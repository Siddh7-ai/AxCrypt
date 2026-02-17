"""
axcrypt/core/crypto.py
──────────────────────
All cryptographic primitives for AxCrypt.
  • Password hashing + verification (scrypt)
  • AES-256-CBC file encrypt / decrypt with progress callbacks
  • Secure multi-pass file wipe
  • Password-strength scorer
  • One-Time-Decrypt (OTD) header flag
  • Steganographic owner-metadata embedding
"""

import os, hmac, hashlib, logging, secrets, struct, json, time, tempfile
from cryptography.hazmat.primitives.ciphers  import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.padding  import PKCS7
from cryptography.hazmat.backends           import default_backend

from core.config import (
    SALT_SIZE, IV_SIZE, KEY_SIZE,
    SCRYPT_N, SCRYPT_R, SCRYPT_P,
    WIPE_PASSES, OTD_MARKER, STEG_MAGIC,
)

log = logging.getLogger("axcrypt.crypto")

# ─── HMAC key for time-locked tokens (per-install, not rotated here) ──────────
_HMAC_KEY = b"AxCrypt_TimeLock_2025_SecretKey!"


# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key via scrypt."""
    kdf = Scrypt(salt=salt, length=KEY_SIZE,
                 n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P,
                 backend=default_backend())
    return kdf.derive(password.encode("utf-8"))


def hash_password(password: str, salt: bytes | None = None) -> bytes:
    """Return salt + derived-key blob for credential storage."""
    if salt is None:
        salt = secrets.token_bytes(SALT_SIZE)
    return salt + derive_key(password, salt)


def verify_password(password: str, blob: bytes) -> bool:
    """Constant-time password verification."""
    try:
        salt   = blob[:SALT_SIZE]
        stored = blob[SALT_SIZE:]
        return hmac.compare_digest(derive_key(password, salt), stored)
    except Exception as exc:
        log.error("verify_password: %s", exc)
        return False


def password_strength(pwd: str) -> int:
    """Return 0-100 score.

    Breakdown:
      length ≥8  → +20   length ≥12 → +15   length ≥16 → +10
      upper      → +15   lower      → +10   digit       → +10
      special    → +15   mix (≥3 categories) → +5
    """
    s = 0
    if len(pwd) >= 8:  s += 20
    if len(pwd) >= 12: s += 15
    if len(pwd) >= 16: s += 10

    has_upper   = any(c.isupper()   for c in pwd)
    has_lower   = any(c.islower()   for c in pwd)
    has_digit   = any(c.isdigit()   for c in pwd)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:',.<>?/~`" for c in pwd)

    cats = sum((has_upper, has_lower, has_digit, has_special))
    if has_upper:   s += 15
    if has_lower:   s += 10
    if has_digit:   s += 10
    if has_special: s += 15
    if cats >= 3:   s += 5

    return min(s, 100)


def strength_label(score: int):
    """Return (label, hex-colour) for the score."""
    from core.config import DIFFICULTY_TIERS, C
    label, colour = "Casual", C["danger"]
    for threshold, lbl, clr, _ in DIFFICULTY_TIERS:
        if score >= threshold:
            label, colour = lbl, clr
    return label, colour


# ══════════════════════════════════════════════════════════════════════════════
# FILE ENCRYPTION / DECRYPTION
# ══════════════════════════════════════════════════════════════════════════════
# On-disk layout (per encrypted file):
#   [salt 16 B][iv 16 B][OTD-flag 1 B][steg-len 2 B][steg-payload N B][ciphertext …]
#   OTD-flag: 0x00 = normal, 0x01 = one-time-decrypt
#   steg-len: big-endian uint16 – length of steganographic JSON payload

def _build_header(otd: bool, steg_meta: bytes) -> bytes:
    """Assemble the post-IV header bytes."""
    flag  = b"\x01" if otd else b"\x00"
    slen  = struct.pack(">H", len(steg_meta))
    return flag + slen + steg_meta


def _parse_header(raw: bytes):
    """Parse header after salt+iv.  Returns (otd_flag, steg_bytes, payload_offset)."""
    otd_flag  = raw[0] == 0x01
    slen      = struct.unpack(">H", raw[1:3])[0]
    steg_meta = raw[3:3 + slen]
    payload_offset = 3 + slen          # relative to end of salt+iv
    return otd_flag, steg_meta, payload_offset


def encrypt_file(
    src_path: str,
    password: str,
    *,
    one_time_decrypt: bool = False,
    owner_info: str = "",
    progress_cb=None,
) -> tuple[bool, str | None, str | None]:
    """Encrypt *src_path* → *src_path*.enc

    Returns (success, output_path, error_message).
    progress_cb(float 0.0-1.0) called during work.
    """
    try:
        if not os.path.exists(src_path):
            return False, None, "Source file not found."

        salt = secrets.token_bytes(SALT_SIZE)
        iv   = secrets.token_bytes(IV_SIZE)
        key  = derive_key(password, salt)

        # Build steganographic payload
        steg_payload = b""
        if owner_info:
            meta_json = json.dumps({"owner": owner_info, "ts": time.time()})
            steg_payload = STEG_MAGIC + meta_json.encode("utf-8")

        header = _build_header(one_time_decrypt, steg_payload)

        cipher   = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder    = PKCS7(128).padder()

        file_size = os.path.getsize(src_path) or 1
        out_path  = src_path + ".enc"
        processed = 0

        with open(src_path, "rb") as fin, open(out_path, "wb") as fout:
            fout.write(salt + iv + header)          # unencrypted framing

            while True:
                chunk = fin.read(8192)
                if not chunk:
                    break
                processed += len(chunk)
                fout.write(encryptor.update(padder.update(chunk)))
                if progress_cb:
                    progress_cb(min(processed / file_size, 0.95))

            fout.write(encryptor.update(padder.finalize()) + encryptor.finalize())

        if progress_cb:
            progress_cb(1.0)

        log.info("Encrypted %s → %s  otd=%s", src_path, out_path, one_time_decrypt)
        return True, out_path, None

    except Exception as exc:
        log.error("encrypt_file: %s", exc, exc_info=True)
        return False, None, str(exc)


def encrypt_file_replace(
    src_path: str,
    password: str,
    *,
    one_time_decrypt: bool = False,
    owner_info: str = "",
    progress_cb=None,
) -> tuple[bool, str | None, str | None]:
    """
    Encrypt file and replace original with encrypted content atomically.
    
    This is the CORRECT implementation that fixes [Errno 9] Bad file descriptor.
    
    Why the original failed:
    - The code attempted to use os.replace() on a file that was still open
    - File descriptors were invalid because files weren't properly closed
    - Violated OS file-handling rules on all platforms
    
    Correct strategy:
    1. Read the entire original file content (then CLOSE it)
    2. Encrypt the data in memory
    3. Write encrypted data to a TEMPORARY file in the same directory
    4. Flush and fsync the temp file to ensure data is on disk
    5. Use os.replace(temp_file, original_file) to atomically swap
    6. Original path remains unchanged, only content is replaced
    
    Benefits:
    - Crash-safe: If power fails, either old or new file exists (no corruption)
    - Atomic: Operation completes fully or not at all
    - Cross-platform: Works on Windows, Linux, macOS
    - Reversible: Can decrypt using same path
    
    Returns (success, original_path, error_message).
    """
    try:
        if not os.path.exists(src_path):
            return False, None, "Source file not found."

        # STEP 1: Read original file content completely
        with open(src_path, "rb") as fin:
            plaintext = fin.read()
        # File is now CLOSED - no file descriptor issues
        
        file_size = len(plaintext) or 1

        # STEP 2: Generate encryption parameters
        salt = secrets.token_bytes(SALT_SIZE)
        iv   = secrets.token_bytes(IV_SIZE)
        key  = derive_key(password, salt)

        # Build steganographic payload
        steg_payload = b""
        if owner_info:
            meta_json = json.dumps({"owner": owner_info, "ts": time.time()})
            steg_payload = STEG_MAGIC + meta_json.encode("utf-8")

        header = _build_header(one_time_decrypt, steg_payload)

        # STEP 3: Encrypt data in memory
        cipher   = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder    = PKCS7(128).padder()

        # Encrypt in chunks for progress reporting
        encrypted_chunks = []
        chunk_size = 8192
        processed = 0
        
        for i in range(0, len(plaintext), chunk_size):
            chunk = plaintext[i:i + chunk_size]
            encrypted_chunks.append(encryptor.update(padder.update(chunk)))
            processed += len(chunk)
            if progress_cb:
                progress_cb(min(processed / file_size, 0.95))
        
        # Finalize encryption
        encrypted_chunks.append(encryptor.update(padder.finalize()) + encryptor.finalize())
        ciphertext = b"".join(encrypted_chunks)

        # STEP 4: Write to temporary file in SAME DIRECTORY
        # (same filesystem ensures atomic os.replace())
        src_dir = os.path.dirname(src_path) or "."
        fd, temp_path = tempfile.mkstemp(dir=src_dir, prefix=".axcrypt_tmp_", suffix=".enc")
        
        try:
            # Write encrypted data to temp file
            with os.fdopen(fd, 'wb') as fout:
                fout.write(salt + iv + header)
                fout.write(ciphertext)
                fout.flush()
                os.fsync(fout.fileno())
            # Temp file is now CLOSED and synced to disk
            
            # STEP 5: Atomically replace original with encrypted content
            # This is atomic on POSIX and Windows (Python 3.3+)
            # The original file path is preserved, only content changes
            os.replace(temp_path, src_path)
            
            if progress_cb:
                progress_cb(1.0)
            
            log.info("Encrypted and replaced %s (in-place)  otd=%s", src_path, one_time_decrypt)
            return True, src_path, None
            
        except Exception as replace_err:
            # Clean up temp file on error
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            raise replace_err

    except Exception as exc:
        log.error("encrypt_file_replace: %s", exc, exc_info=True)
        return False, None, str(exc)


def decrypt_file(
    enc_path: str,
    password: str,
    *,
    progress_cb=None,
    output_path: str | None = None,
) -> tuple[bool, str | None, str | None, bool]:
    """Decrypt *enc_path*.

    Returns (success, decrypted_path, error, was_otd).
    If the file was OTD-flagged *was_otd* is True – caller must handle
    re-encrypt / delete after the user is done.
    """
    try:
        if not os.path.exists(enc_path):
            return False, None, "Encrypted file not found.", False

        with open(enc_path, "rb") as f:
            salt = f.read(SALT_SIZE)
            iv   = f.read(IV_SIZE)
            # Read enough bytes for the fixed + variable header
            peek = f.read(3)                  # flag(1) + slen(2)
            slen = struct.unpack(">H", peek[1:3])[0]
            steg_meta = f.read(slen)          # may be empty
            ciphertext = f.read()             # rest is ciphertext

        otd_flag = peek[0] == 0x01

        key = derive_key(password, salt)
        cipher    = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        unpadder  = PKCS7(128).unpadder()

        plaintext = unpadder.update(decryptor.update(ciphertext)) + \
                    unpadder.update(decryptor.finalize()) + unpadder.finalize()

        # Determine output path
        if output_path is None:
            output_path = enc_path[:-4] if enc_path.endswith(".enc") else enc_path + ".dec"

        with open(output_path, "wb") as fout:
            fout.write(plaintext)

        if progress_cb:
            progress_cb(1.0)

        log.info("Decrypted %s → %s  otd=%s", enc_path, output_path, otd_flag)
        return True, output_path, None, otd_flag

    except Exception as exc:
        log.error("decrypt_file: %s", exc, exc_info=True)
        return False, None, "Decryption failed – wrong password or corrupted file.", False


def read_steg_metadata(enc_path: str) -> dict | None:
    """Read steganographic owner metadata without decrypting."""
    try:
        with open(enc_path, "rb") as f:
            f.read(SALT_SIZE + IV_SIZE)
            peek = f.read(3)
            slen = struct.unpack(">H", peek[1:3])[0]
            raw  = f.read(slen)
        if raw[:2] == STEG_MAGIC:
            return json.loads(raw[2:].decode("utf-8"))
        return None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SECURE DELETE
# ══════════════════════════════════════════════════════════════════════════════

def secure_delete(path: str, passes: int = WIPE_PASSES) -> bool:
    """Multi-pass overwrite then unlink."""
    try:
        if not os.path.exists(path):
            return True
        size = os.path.getsize(path)
        if size == 0:
            os.remove(path)
            return True

        patterns = [
            lambda _: b"\x00" * size,                   # all-zeros
            lambda _: b"\xff" * size,                   # all-ones
            lambda _: secrets.token_bytes(size),        # random
        ]

        with open(path, "r+b") as fh:
            for i in range(passes):
                fh.seek(0)
                fh.write(patterns[i % len(patterns)](i))
                fh.flush()
                os.fsync(fh.fileno())
        os.remove(path)
        log.info("Secure-deleted %s (%d passes)", path, passes)
        return True
    except Exception as exc:
        log.error("secure_delete %s: %s", path, exc)
        try:
            os.remove(path)
        except OSError:
            pass
        return False


def secure_delete_dir(dir_path: str) -> None:
    """Recursively secure-delete every file in *dir_path*, then rmdir."""
    import shutil
    if not os.path.isdir(dir_path):
        return
    for root, _dirs, files in os.walk(dir_path):
        for fname in files:
            secure_delete(os.path.join(root, fname))
    shutil.rmtree(dir_path, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════════════
# TIME-LOCKED PASSWORD  (carry-over, improved)
# ══════════════════════════════════════════════════════════════════════════════
import base64

def generate_time_locked_password(base_password: str, duration_secs: int) -> tuple[str, int]:
    """Create an HMAC-signed, base64 time-locked password token.

    Returns (token_string, expiry_unix_timestamp).
    """
    expiry = int(time.time()) + duration_secs
    payload = json.dumps({"p": base_password, "e": expiry}, separators=(",", ":"))
    b64_payload = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(_HMAC_KEY, b64_payload.encode(), hashlib.sha256).digest()
    b64_sig = base64.urlsafe_b64encode(sig).decode()
    return f"{b64_payload}.{b64_sig}", expiry

def validate_time_locked_password(token: str) -> tuple[bool, str | None, str | None]:
    """Validate token.  Returns (valid, base_password, error_msg)."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False, None, "Malformed token."
        b64_payload, b64_sig = parts
        expected_sig = hmac.new(_HMAC_KEY, b64_payload.encode(), hashlib.sha256).digest()
        provided_sig = base64.urlsafe_b64decode(b64_sig)
        if not hmac.compare_digest(expected_sig, provided_sig):
            return False, None, "Signature mismatch – token tampered."
        payload = json.loads(base64.urlsafe_b64decode(b64_payload).decode())
        if time.time() > payload["e"]:
            return False, None, "Token expired."
        return True, payload["p"], None
    except Exception as exc:
        return False, None, str(exc)