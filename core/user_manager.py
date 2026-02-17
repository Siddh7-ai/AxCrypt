"""
axcrypt/core/user_manager.py
────────────────────────────
Full authentication system:
  • Sign-up  (name, email, mobile)
  • Login    (brute-force lockout)
  • OTP generation & verification (mock – no external API)
  • Forgot-password reset via OTP
  • All credentials stored encrypted on disk with AES-256
"""

import os, json, time, secrets, logging, hashlib
from datetime import datetime
from core.config import (
    USERS_DB, MAX_LOGIN_ATTEMPTS, LOCKOUT_SECS,
    OTP_VALIDITY_SECS, OTP_LENGTH,
    SALT_SIZE, KEY_SIZE,
)
from core.crypto import (
    hash_password, verify_password, derive_key,
    secure_delete,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends             import default_backend

log = logging.getLogger("axcrypt.user")

# ─── A fixed salt for the *database-level* encryption (not per-user passwords)
_DB_SALT_FILE = os.path.join(os.path.dirname(USERS_DB), "db.salt")


def _get_db_salt() -> bytes:
    """Return (or create) the per-install salt used to wrap the users DB."""
    if os.path.exists(_DB_SALT_FILE):
        with open(_DB_SALT_FILE, "rb") as f:
            return f.read()
    salt = secrets.token_bytes(SALT_SIZE)
    with open(_DB_SALT_FILE, "wb") as f:
        f.write(salt)
    return salt


def _db_key() -> bytes:
    """Derive the AES key that encrypts the on-disk users blob.
    Key is derived from the app-name string + per-install salt (no user secret).
    """
    return derive_key("axcrypt_internal_db_wrap", _get_db_salt())


def _encrypt_blob(data: bytes) -> bytes:
    iv  = secrets.token_bytes(16)
    key = _db_key()
    from cryptography.hazmat.primitives.padding import PKCS7
    padder = PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    enc = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).encryptor()
    return iv + enc.update(padded) + enc.finalize()


def _decrypt_blob(raw: bytes) -> bytes:
    iv         = raw[:16]
    ciphertext = raw[16:]
    key        = _db_key()
    dec = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).decryptor()
    from cryptography.hazmat.primitives.padding import PKCS7
    unpadder = PKCS7(128).unpadder()
    padded = dec.update(ciphertext) + dec.finalize()
    return unpadder.update(padded) + unpadder.finalize()


class UserManager:
    """In-memory cache of the encrypted users DB + auth helpers."""

    def __init__(self):
        self.users: dict = {}                   # username → record
        self.login_attempts: dict[str, int]  = {}
        self.lockout_until:  dict[str, float] = {}
        self._pending_otps: dict[str, dict]  = {}   # mobile → {otp, expiry, purpose, username}
        self._load()

    # ── persistence ────────────────────────────────────────────────────────
    def _load(self):
        if not os.path.exists(USERS_DB):
            self.users = {}
            return
        try:
            with open(USERS_DB, "rb") as f:
                self.users = json.loads(_decrypt_blob(f.read()).decode("utf-8"))
        except Exception as exc:
            log.warning("Could not load users DB (first run?): %s", exc)
            self.users = {}

    def _save(self):
        raw = json.dumps(self.users).encode("utf-8")
        with open(USERS_DB, "wb") as f:
            f.write(_encrypt_blob(raw))

    # ── registration ───────────────────────────────────────────────────────
    def register(self, username: str, password: str, email: str, mobile: str, fullname: str = ""):
        """Register a new user.  Returns (ok, message).

        Does NOT require OTP first – caller should have already verified OTP
        via verify_otp() before calling this.
        """
        if username in self.users:
            return False, "Username already taken."
        if len(username) < 3:
            return False, "Username must be ≥ 3 characters."
        if len(password) < 8:
            return False, "Password must be ≥ 8 characters."
        if not email or "@" not in email:
            return False, "Enter a valid email."
        if not mobile or len(mobile) < 7:
            return False, "Enter a valid mobile number."

        self.users[username] = {
            "password_hash": hash_password(password).hex(),
            "email":         email,
            "mobile":        mobile,
            "fullname":      fullname,
            "created_at":    datetime.now().isoformat(),
            "last_login":    None,
        }
        self._save()
        log.info("Registered user: %s", username)
        return True, "Registration successful."

    # ── login ──────────────────────────────────────────────────────────────
    def authenticate(self, username: str, password: str):
        """Returns (ok, message)."""
        # lockout check
        if username in self.lockout_until:
            if time.time() < self.lockout_until[username]:
                rem = int(self.lockout_until[username] - time.time())
                return False, f"Account locked. Try again in {rem}s."
            else:
                del self.lockout_until[username]
                self.login_attempts[username] = 0

        if username not in self.users:
            return False, "Invalid username or password."

        blob = bytes.fromhex(self.users[username]["password_hash"])
        if verify_password(password, blob):
            self.login_attempts[username] = 0
            self.users[username]["last_login"] = datetime.now().isoformat()
            self._save()
            return True, "Login successful."

        self.login_attempts[username] = self.login_attempts.get(username, 0) + 1
        if self.login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
            self.lockout_until[username] = time.time() + LOCKOUT_SECS
            return False, f"Too many failed attempts. Locked for {LOCKOUT_SECS}s."
        rem = MAX_LOGIN_ATTEMPTS - self.login_attempts[username]
        return False, f"Invalid credentials. {rem} attempt(s) left."

    # ── OTP helpers ────────────────────────────────────────────────────────
    def generate_otp(self, mobile: str, purpose: str = "register", username: str = ""):
        """Generate a 6-digit OTP, store in memory with TTL.

        purpose: 'register' | 'reset'
        Returns the OTP string (mock – in production send via SMS gateway).
        """
        otp = str(secrets.randbelow(10 ** OTP_LENGTH)).zfill(OTP_LENGTH)
        self._pending_otps[mobile] = {
            "otp":      otp,
            "expiry":   time.time() + OTP_VALIDITY_SECS,
            "purpose":  purpose,
            "username": username,
            "attempts": 0,
        }
        log.info("OTP generated for %s (purpose=%s): %s", mobile, purpose, otp)
        # In production you would send SMS here.
        # For demo the OTP is displayed directly in the UI.
        return otp

    def verify_otp(self, mobile: str, otp_entered: str) -> tuple[bool, str]:
        """Verify user-entered OTP.  Returns (ok, message)."""
        record = self._pending_otps.get(mobile)
        if record is None:
            return False, "No pending OTP. Request a new one."
        if time.time() > record["expiry"]:
            del self._pending_otps[mobile]
            return False, "OTP expired. Request a new one."
        record["attempts"] += 1
        if record["attempts"] > 3:
            del self._pending_otps[mobile]
            return False, "Too many wrong attempts. Request a new OTP."
        if otp_entered.strip() != record["otp"]:
            return False, "Incorrect OTP."
        # valid – leave record so caller can read purpose/username
        return True, "OTP verified."

    def get_otp_record(self, mobile: str) -> dict | None:
        return self._pending_otps.get(mobile)

    def clear_otp(self, mobile: str):
        self._pending_otps.pop(mobile, None)

    # ── password reset ─────────────────────────────────────────────────────
    def reset_password(self, username: str, new_password: str):
        """Forcefully set a new password (call only after OTP verified)."""
        if username not in self.users:
            return False, "User not found."
        if len(new_password) < 8:
            return False, "Password must be ≥ 8 characters."
        self.users[username]["password_hash"] = hash_password(new_password).hex()
        self._save()
        # reset lockout
        self.login_attempts.pop(username, None)
        self.lockout_until.pop(username, None)
        return True, "Password reset successfully."

    # ── misc ───────────────────────────────────────────────────────────────
    def user_exists(self, username: str) -> bool:
        return username in self.users

    def get_mobile_by_username(self, username: str) -> str | None:
        rec = self.users.get(username)
        return rec["mobile"] if rec else None

    def get_username_by_mobile(self, mobile: str) -> str | None:
        for uname, rec in self.users.items():
            if rec.get("mobile") == mobile:
                return uname
        return None
