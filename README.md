# 🛡️AxCrypt — CustomTkinter Edition
### Complete Project Documentation

> **Version:** 1.0.1 | **Python:** 3.11+ | **UI Framework:** CustomTkinter + Tkinter

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Directory Structure](#2-architecture--directory-structure)
3. [Core Modules](#3-core-modules)
   - [config.py](#31-configpy)
   - [crypto.py](#32-cryptopy)
   - [session.py](#33-sessionpy)
   - [user_manager.py](#34-user_managerpy)
   - [history.py](#35-historypy)
4. [UI Modules](#4-ui-modules)
   - [main.py & app.py](#41-mainpy--apppy)
   - [splash.py](#42-splashpy)
   - [auth_panel_glassmorphism.py](#43-auth_panel_glassmorphismpy)
   - [lock_panel.py](#44-lock_panelpy)
   - [dashboard.py](#45-dashboardpy)
   - [encrypt_panel.py](#46-encrypt_panelpy)
   - [decrypt_panel.py](#47-decrypt_panelpy)
   - [history_panel.py](#48-history_panelpy)
   - [settings_panel.py](#49-settings_panelpy)
   - [widgets.py](#410-widgetspy)
5. [Cryptography Deep Dive](#5-cryptography-deep-dive)
6. [Security Architecture](#6-security-architecture)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Installation & Setup](#8-installation--setup)
9. [Configuration Reference](#9-configuration-reference)
10. [Known Issues & Bug Fixes](#10-known-issues--bug-fixes)
11. [Enhancements & Roadmap](#11-enhancements--roadmap)

---

## 1. Project Overview

**AxCrypt** is a desktop file encryption application with a cyberpunk aesthetic built in Python using `CustomTkinter` and standard `Tkinter`. It provides AES-256-CBC encryption/decryption for files, a tamper-resistant activity log, multi-user authentication with brute-force lockout, OTP-based password reset, time-locked passwords, steganographic metadata embedding, and one-time decrypt (OTD) mode.

### Key Features

| Feature | Description |
|---|---|
| AES-256-CBC Encryption | File encryption using scrypt-derived keys |
| One-Time Decrypt (OTD) | File auto-destroys after first decryption |
| Steganographic Metadata | Hidden owner info embedded in encrypted files |
| HMAC-Chained History | Tamper-evident activity log |
| Multi-User Auth | Username/password with brute-force lockout |
| OTP Password Reset | 6-digit, time-limited OTP via mobile |
| Time-Locked Passwords | HMAC-signed expiring password tokens |
| Secure Delete | 7-pass DoD-style file wipe |
| Session Auto-Lock | Inactivity timeout with panic lock |
| Glassmorphic UI | Cyberpunk neon-on-dark design system |

---

## 2. Architecture & Directory Structure

```
AxCrypt_CustomTkinter/
│
├── main.py                        # Entry point — bootstraps app + splash
│
├── core/                          # Business logic (no UI dependencies)
│   ├── __init__.py
│   ├── config.py                  # All constants, paths, palette, font map
│   ├── crypto.py                  # AES-256-CBC, scrypt, secure delete, OTD
│   ├── history.py                 # HMAC-chained encrypted activity log
│   ├── session.py                 # Session state, inactivity, panic lock
│   └── user_manager.py            # User DB (encrypted), auth, OTP
│
├── ui/                            # All UI panels and widgets
│   ├── __init__.py
│   ├── app.py                     # Root CTk window, navigation, auto-lock
│   ├── splash.py                  # Animated loading splash screen
│   ├── auth_panel_glassmorphism.py # Login / Register / OTP / Forgot-password
│   ├── lock_panel.py              # Inactivity lock screen
│   ├── dashboard.py               # Stats overview and quick actions
│   ├── encrypt_panel.py           # File encrypt workflow
│   ├── decrypt_panel.py           # File decrypt workflow
│   ├── history_panel.py           # Activity log viewer with chain verify
│   ├── settings_panel.py          # Session settings, time-lock generator
│   └── widgets.py                 # Reusable cyberpunk widget library
│
├── ui_backups_original/           # Original pre-CTk widget backups
│
├── assets/
│   └── logo.png                   # Application logo
│
├── requirements.txt               # Python dependencies
├── resize_all_ui.py               # Utility: batch-resize UI elements
├── ENHANCEMENTS.md                # UX enhancement guide with code snippets
├── IMPLEMENTATION_SUMMARY.md      # Summary of completed fixes
└── UPGRADE_NOTES.txt              # Migration notes (Tkinter → CustomTkinter)
```

### Layer Separation

```
┌────────────────────────────────────────┐
│              UI Layer (ui/)             │  CustomTkinter / Tkinter widgets
│   app ─ panels ─ widgets               │  No crypto logic here
├────────────────────────────────────────┤
│            Core Layer (core/)           │  Pure Python, no UI imports
│   crypto ─ user_manager ─ history      │
│   session ─ config                     │
├────────────────────────────────────────┤
│          Storage Layer (~/.axcrypt/)    │  Encrypted AES blobs on disk
│   users.axc ─ history.axc ─ session   │
└────────────────────────────────────────┘
```

---

## 3. Core Modules

### 3.1 `config.py`

Central constants and configuration. All other modules import from here.

**App Identity**

| Constant | Value | Purpose |
|---|---|---|
| `APP_NAME` | `"AxCrypt"` | Window title, logging |
| `APP_VERSION` | `"1.0.1"` | Displayed in header |
| `APP_TAGLINE` | `"Master-Level Encryption..."` | Header subtitle |

**File System Layout** — All data is stored under `~/.axcrypt/`:

| Path | Purpose |
|---|---|
| `~/.axcrypt/data/users.axc` | Encrypted user database |
| `~/.axcrypt/data/history.axc` | Encrypted HMAC-chained history |
| `~/.axcrypt/data/session.axc` | Session state (reserved) |
| `~/.axcrypt/tmp/` | Temporary files wiped on panic lock |
| `~/.axcrypt/axcrypt.log` | Application log file |

**Cryptographic Constants**

| Constant | Value | Meaning |
|---|---|---|
| `SALT_SIZE` | 16 bytes | Random salt per encryption |
| `IV_SIZE` | 16 bytes | Random IV per encryption |
| `KEY_SIZE` | 32 bytes | AES-256 key length |
| `SCRYPT_N` | 2¹⁵ = 32768 | CPU/memory cost factor |
| `SCRYPT_R` | 8 | Block size |
| `SCRYPT_P` | 1 | Parallelization |
| `WIPE_PASSES` | 7 | Secure-delete overwrite count |

**Security Tunables**

| Constant | Default | Description |
|---|---|---|
| `MAX_LOGIN_ATTEMPTS` | 3 | Failed logins before lockout |
| `LOCKOUT_SECS` | 120 | Account lockout duration |
| `SESSION_TIMEOUT` | 300 | Inactivity seconds before auto-lock |
| `OTP_VALIDITY_SECS` | 300 | OTP time-to-live |
| `OTP_LENGTH` | 6 | OTP digit count |

**Colour Palette** — The cyberpunk colour scheme is defined as a dictionary `C`:

| Key | Hex | Use |
|---|---|---|
| `bg_deep` | `#0a0c0f` | Window background |
| `bg_panel` | `#111318` | Header/footer |
| `bg_card` | `#161a22` | Card backgrounds |
| `neon_green` | `#39ff14` | Encrypt actions, success |
| `neon_cyan` | `#00f0ff` | Decrypt, info |
| `neon_violet` | `#bf5fff` | History, OTP |
| `neon_pink` | `#ff2d95` | Danger, panic |
| `neon_orange` | `#ff9f1c` | Warnings, settings |

---

### 3.2 `crypto.py`

All cryptographic operations. No UI code.

#### Key Derivation

```
password + random_salt ──scrypt(N=32768, r=8, p=1)──► 256-bit AES key
```

`derive_key(password, salt)` — Returns 32-byte key using `cryptography` library's `Scrypt` KDF.

#### Password Hashing

`hash_password(password, salt=None)` — Returns `salt (16B) + derived_key (32B)` blob for storage.

`verify_password(password, blob)` — Constant-time comparison using `hmac.compare_digest`.

#### Password Strength Scorer

`password_strength(pwd)` → 0–100 integer score:

| Criterion | Points |
|---|---|
| Length ≥ 8 | +20 |
| Length ≥ 12 | +15 |
| Length ≥ 16 | +10 |
| Uppercase | +15 |
| Lowercase | +10 |
| Digits | +10 |
| Special chars | +15 |
| 3+ categories | +5 |

Tiers: **Casual** (0–39), **Professional** (40–69), **Military Grade** (70+).

#### File Encryption — On-Disk Format

```
┌────────────────────────────────────────────────────────────────┐
│  salt (16B) │ iv (16B) │ otd_flag (1B) │ steg_len (2B big-end) │
│  steg_payload (N bytes) │ AES-256-CBC ciphertext (PKCS7 padded) │
└────────────────────────────────────────────────────────────────┘
```

`encrypt_file(src, password, ...)` — Encrypts to `src.enc`, leaving the original intact.

`encrypt_file_replace(src, password, ...)` — **Atomic in-place encryption.** Reads entire file, encrypts in memory, writes to temp file in same directory, then calls `os.replace()`. Crash-safe: either old or new file exists at all times.

`decrypt_file(enc_path, password, ...)` — Returns `(success, output_path, error, was_otd)`. The `was_otd` flag tells the caller to re-encrypt or delete after viewing.

#### Steganographic Metadata

An optional JSON payload can be hidden inside the encrypted file's unencrypted header area:

```
steg_payload = STEG_MAGIC (2B: 0xACCE) + JSON bytes
JSON: {"owner": "...", "ts": unix_timestamp}
```

`read_steg_metadata(enc_path)` reads owner info without decrypting the body.

#### Secure Delete

`secure_delete(path, passes=7)` — Multi-pass overwrite: zeros → ones → random, cycling until `passes` iterations. Uses `os.fsync()` after each pass to force disk write.

`secure_delete_dir(dir_path)` — Recursively wipes all files then removes directory tree.

#### Time-Locked Passwords

`generate_time_locked_password(base_password, duration_secs)` → `(token, expiry_timestamp)`

Token format: `base64url(JSON_payload) . base64url(HMAC-SHA256_signature)`

`validate_time_locked_password(token)` → `(valid, base_password, error)` — Checks HMAC integrity then expiry.

---

### 3.3 `session.py`

Session state tracker. Deliberately **UI-agnostic** to avoid threading issues with Tkinter.

#### Design Decision

The original implementation used `threading.Timer` to call UI methods from a background thread — which crashes Tkinter (not thread-safe). The fixed version uses a **polling pattern**: `SessionManager` only flips boolean flags; the UI layer polls every 1 second via `root.after(1000, ...)`.

#### API

| Method | Description |
|---|---|
| `login(username)` | Start session, record activity time |
| `logout()` | Clear session state |
| `touch()` | Reset inactivity clock (call on any user action) |
| `check_timeout()` | Returns `True` if inactive ≥ `SESSION_TIMEOUT` |
| `is_lock_requested()` | Polls lock flag (UI calls this every second) |
| `panic_lock()` | Set lock flag + wipe `TEMP_DIR` |

---

### 3.4 `user_manager.py`

Manages the encrypted user database (`users.axc`).

#### Database Encryption

The user database is AES-256-CBC encrypted using a **per-install salt** stored in `~/.axcrypt/data/db.salt`. The wrapping key is derived from the fixed string `"axcrypt_internal_db_wrap"` + the install salt. This prevents reading the DB on a different machine without copying the salt file.

```
users.axc = AES-CBC( JSON(user_records), key=scrypt("axcrypt_internal_db_wrap", db.salt) )
```

#### User Record Schema

```json
{
  "username": {
    "password_hash": "hex(salt + scrypt_key)",
    "email": "user@example.com",
    "mobile": "+91xxxxxxxxxx",
    "fullname": "Full Name",
    "created_at": "ISO-8601",
    "last_login": "ISO-8601 or null"
  }
}
```

#### Authentication Flow

1. Check `lockout_until[username]` — reject if still locked
2. Look up username — fail silently with generic message
3. `verify_password(entered, stored_hash)` — constant-time compare
4. On failure: increment `login_attempts`; lock account after `MAX_LOGIN_ATTEMPTS`

#### OTP System

OTPs are **in-memory only** (not stored to disk). The `_pending_otps` dict maps `mobile → {otp, expiry, purpose, username, attempts}`.

In the current (demo) build, the OTP is logged to console. In production, this would be the SMS gateway integration point.

`verify_otp(mobile, otp)` enforces a 3-attempt limit before invalidating the OTP.

---

### 3.5 `history.py`

Tamper-evident activity log using HMAC-SHA256 chaining.

#### Chain Structure

```
Entry 0: hash = HMAC(entry_data, prev="GENESIS")
Entry 1: hash = HMAC(entry_data, prev=entry_0_hash)
Entry N: hash = HMAC(entry_data, prev=entry_N-1_hash)
```

Any insertion, deletion, modification, or reordering of entries breaks the chain. `verify_chain()` walks every entry and recomputes HMACs.

The chain key is stored in `~/.axcrypt/data/chain.key` (32 random bytes generated on first run).

#### History Storage

The entire entries list is serialised as JSON, then encrypted with the same AES-CBC blob mechanism used by `user_manager.py`.

#### Entry Schema

```json
{
  "action": "ENCRYPT | DECRYPT | SECURE_DELETE",
  "filename": "example.txt",
  "algorithm": "AES-256-CBC",
  "status": "Success | Failed",
  "user": "username",
  "timestamp": "ISO-8601",
  "display_time": "YYYY-MM-DD  HH:MM:SS",
  "_hash": "hmac-sha256-hex"
}
```

Maximum of 200 entries are retained. When trimmed, the chain is re-computed from the new genesis.

---

## 4. UI Modules

### 4.1 `main.py` & `app.py`

#### `main.py` — Entry Point

1. Sets up file + stdout logging
2. Creates `AxCryptApp` (the root `ctk.CTk` window) first — this establishes the Tk root and prevents the "Too early to use font: no default root window" error
3. Hides the main window (`app.withdraw()`)
4. Creates `SplashScreen` as a `Toplevel` of the main app
5. On splash complete: `app.deiconify()` then `app.show_auth()`
6. Runs `app.mainloop()` — a single event loop for the entire app

#### `app.py` — `AxCryptApp(ctk.CTk)`

The root window owns all shared state and manages panel switching.

**Shared state objects** (created in `__init__`):
- `self.session` — `SessionManager`
- `self.user_mgr` — `UserManager`
- `self.history` — `HistoryManager`

**Layout structure:**
```
AxCryptApp
├── Header (CTkFrame, height=60)      ← Logo, app name, tagline, user label
├── Content (CTkFrame, expand=True)   ← All panels are packed here
└── Footer (CTkFrame, height=52)      ← Persistent navigation bar
```

**Panel management:**
- Pre-loaded panels (always exist): `auth_panel`, `lock_panel`, `dashboard_panel`, `history_panel`, `settings_panel`
- Lazy-loaded panels (created on first visit): `_encrypt_panel`, `_decrypt_panel`
- `_switch_tab(tab_name)` hides all, shows target, calls `on_show()` hook

**Auto-lock polling:**
`_check_auto_lock()` runs every 1000ms via `self.after()` on the main thread. It calls `session.check_timeout()` and triggers `_do_lock_screen()` if needed.

---

### 4.2 `splash.py`

Animated splash screen shown as a `Toplevel` window during app startup. Displays logo, app name, and an animated progress bar/loading text. After `SPLASH_DURATION` ms, it calls the provided `on_complete` callback.

---

### 4.3 `auth_panel_glassmorphism.py`

Glassmorphic authentication panel with four sub-views:

| View | Trigger | Purpose |
|---|---|---|
| Login | Default | Username + password → `app.show_main()` |
| Register | "Sign Up" tab | Name, email, mobile, password; requires OTP first |
| OTP Verify | After signup | 6-digit code entry with TTL display |
| Forgot Password | "Forgot?" link | Mobile lookup → OTP → new password |

The glassmorphism effect uses layered semi-transparent frames with neon border highlights to create depth.

---

### 4.4 `lock_panel.py`

Shown on inactivity timeout or panic lock. Displays only the logged-in username and a password re-entry field. On correct password, resumes session via `app.show_main()`.

---

### 4.5 `dashboard.py`

First screen after login. Three sections:

**Top row:**
- Welcome card with `TerminalText` animated greeting
- Stats column: count of ENCRYPT / DECRYPT / SECURE_DELETE actions from history

**Middle row:**
- Encryption Difficulty indicator (driven by last password strength score)
- Quick Action buttons: ENCRYPT, DECRYPT, HISTORY

**Bottom:**
- Recent Activity feed showing the last 5 history entries

`on_show()` hook refreshes stats and activity every time the dashboard becomes visible.

---

### 4.6 `encrypt_panel.py`

Full encrypt workflow in a scrollable layout:

**Left column (controls):**
- File browser → stores `_selected_file`
- Password + confirm fields with live `StrengthBar`
- Options card: One-Time Decrypt toggle, Time-Lock Password generator, owner info, shred original toggle
- Encrypt Mode dialog for selecting `encrypt_file` vs `encrypt_file_replace`

**Right column (visualization):**
- 4-stage animated process display: KDF → PAD → ENC → OUT
- `NeonProgressBar` animated progress
- `TerminalText` log output

Encryption runs in a background `threading.Thread`. Communication back to the main thread uses a `queue.Queue` polled by `root.after()` — no Tkinter calls from the worker thread.

---

### 4.7 `decrypt_panel.py`

Mirror of encrypt panel for decryption:

- File browser filters for `.enc` files
- Steganographic metadata card: auto-reads and displays hidden owner info on file selection
- Password field with time-locked token support (validated before passing to `decrypt_file`)
- OTD awareness: if `was_otd=True` returned, the panel offers to re-encrypt or secure-delete

Same thread-safe queue pattern as encrypt panel.

---

### 4.8 `history_panel.py`

Displays the encrypted HMAC-chained history:

- Scrollable table of all entries (newest first)
- Colour-coded rows: green for Success, pink for Failed
- **Verify Chain** button: calls `history.verify_chain()` and displays result
- **Clear History** button: with confirmation dialog

---

### 4.9 `settings_panel.py`

Two-column layout:

**Left column:**
- Session auto-lock timeout (editable, applied to `core.config.SESSION_TIMEOUT`)
- Secure-delete pass count (editable, applied to `core.config.WIPE_PASSES`)
- Time-Lock Password Generator: base password + duration → token with copy button

**Right column:**
- Change Password: current + new + confirm, calls `user_mgr.reset_password()`
- About card: version, tagline, algorithm info

Includes a Back button for navigation consistency (added as an enhancement).

---

### 4.10 `widgets.py`

Reusable cyberpunk widget library.

| Widget | Base | Description |
|---|---|---|
| `NeonButton` | `tk.Button` | Neon-coloured button; darkened at rest, full colour on hover |
| `DarkEntry` | `tk.Frame` | Text entry with placeholder text and dark styling |
| `CardFrame` | `tk.Frame` | Dark raised card with coloured neon border |
| `NeonProgressBar` | `tk.Canvas` | Animated horizontal progress bar with glow |
| `StrengthBar` | `tk.Frame` | Password strength colour bar (red → orange → green) |
| `TerminalText` | `tk.Text` | Read-only log widget with colour tags for success/error/info |
| `PulseLabel` | `tk.Label` | Label that pulses between two colours for status indication |
| `ScrollableFrame` | `tk.Frame` | Scrollable canvas container for long content |
| `BackButton` | `NeonButton` | Pre-styled "← BACK" navigation button |
| `EncryptModeDialog` | `tk.Toplevel` | Modal dialog for choosing encrypt-and-keep vs encrypt-in-place |

`NeonButton._darken(hex)` computes a 55%-brightness variant of any hex colour for the default state.

---

## 5. Cryptography Deep Dive

### Encryption Process (step by step)

```
1.  salt = secrets.token_bytes(16)        # Fresh random salt
2.  iv   = secrets.token_bytes(16)        # Fresh random IV
3.  key  = scrypt(password, salt, N=32768, r=8, p=1) → 32B
4.  header = otd_flag(1B) + steg_len(2B) + steg_payload(NB)
5.  Write to output:  salt | iv | header  (unencrypted framing)
6.  AES-256-CBC encrypt plaintext with PKCS7 padding
7.  Append ciphertext to output file
```

### Why scrypt?

scrypt is deliberately expensive in both CPU and memory, making brute-force dictionary attacks impractical even with GPU clusters. The chosen parameters (`N=2¹⁵, r=8, p=1`) balance security with responsiveness on consumer hardware (~0.3–1 second per derivation).

### Why AES-256-CBC?

- CBC mode is well-understood and widely audited
- PKCS7 padding handles arbitrary file sizes
- 256-bit key provides quantum-resistant security margin (128-bit effective after Grover's algorithm)

### Atomic In-Place Encryption

The `encrypt_file_replace` function solves a classic concurrency bug:

1. Read entire file into memory → close file descriptor
2. Encrypt in memory
3. Write to `tempfile.mkstemp()` in **same directory** (ensures same filesystem for atomic rename)
4. `os.fsync()` the temp file
5. `os.replace(temp, original)` — atomic on POSIX and Windows

If power fails between steps 4 and 5, the original file is intact. If it fails after step 5, the encrypted file is complete. No partial or corrupted state is possible.

### Time-Locked Password Tokens

```
payload = JSON({"p": password, "e": expiry_unix})
token   = base64url(payload) + "." + base64url(HMAC-SHA256(payload, secret_key))
```

The secret key (`_HMAC_KEY`) is a hardcoded per-application constant. In production, this should be a per-install random key stored securely (e.g., OS keychain).

---

## 6. Security Architecture

### Threat Model

| Threat | Mitigation |
|---|---|
| Offline disk access | AES-256-CBC + scrypt KDF; user DB also encrypted |
| Brute-force login | 3-attempt lockout for 120 seconds |
| Session hijacking | Inactivity auto-lock after 300 seconds |
| Emergency exposure | Panic lock wipes temp dir, locks immediately |
| History tampering | HMAC-chained entries detect any modification |
| Weak passwords | Strength scorer with visual feedback |
| File metadata leaks | Optional steganographic owner embedding |
| Post-decrypt exposure | One-Time Decrypt mode re-encrypts/deletes |

### Limitations & Notes

- The user database encryption key is derived from a fixed string + per-install salt. If the `db.salt` file is compromised along with `users.axc`, the database can be decrypted with moderate effort. For higher security, derive the key from a master password entered at startup.
- The `_HMAC_KEY` for time-locked tokens is hardcoded. Tokens generated on one installation of AxCrypt can be validated on any other installation with the same source code.
- OTP is in-memory only and logged to console in demo mode. A production build must integrate an SMS gateway and remove console logging.
- The history chain key is per-install. Moving `history.axc` to another machine (without `chain.key`) will fail chain verification.

---

## 7. Data Flow Diagrams

### Login Flow

```
User enters credentials
        │
        ▼
UserManager.authenticate()
        │
   ┌────┴────┐
  OK?      FAIL
   │          │
   ▼          ▼
session.login()    increment attempts
app.show_main()    (lockout if ≥3)
```

### Encrypt Flow

```
User selects file + enters password
        │
        ▼
[Background Thread]
  derive_key(password, salt)
  AES-256-CBC encrypt
  write to .enc file
  queue.put(progress/result)
        │
[Main Thread polling queue.Queue]
        ▼
  Update ProgressBar + TerminalText
        │
        ▼
history.add("ENCRYPT", filename, "Success")
```

### Session Auto-Lock Flow

```
app._check_auto_lock()  [runs every 1000ms via after()]
        │
session.check_timeout()
        │
   ┌────┴────────┐
  No           Timed out
   │                │
   ▼                ▼
reschedule    session.locked = True
              app.show_lock()
```

---

## 8. Installation & Setup

### Prerequisites

- Python 3.11 or higher (uses `str | None` union syntax)
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
cryptography>=41.0
pillow>=10.0
customtkinter>=5.2.0
```

### Run

```bash
python main.py
```

On first run, AxCrypt creates `~/.axcrypt/` with all required subdirectories and key files automatically.

### First Use

1. Click **SIGN UP** on the auth screen
2. Enter username, full name, email, mobile number, and password
3. An OTP is generated — in demo mode it is printed to the console
4. Enter the OTP to complete registration
5. Log in with your credentials

---

## 9. Configuration Reference

All runtime-tunable constants are in `core/config.py`. Key ones:

```python
SESSION_TIMEOUT = 300      # Seconds before auto-lock (modify in Settings UI)
WIPE_PASSES = 7            # Secure-delete overwrite passes (modify in Settings UI)
MAX_LOGIN_ATTEMPTS = 3     # Failed logins before lockout
LOCKOUT_SECS = 120         # Account lockout duration in seconds
SCRYPT_N = 2**15           # KDF cost (increase for stronger security, slower UX)
WIN_W, WIN_H = 1200, 800   # Default window size
SPLASH_DURATION = 2500     # Splash screen duration in ms
```

---

## 10. Known Issues & Bug Fixes

### Fix 1: `RuntimeError: main thread is not in main loop`

**Root Cause:** `threading.Timer` callbacks attempted to call `self.after()` and Tkinter widget methods from a background thread. Tkinter is single-threaded.

**Fix:** Replaced all `threading.Timer` usage for UI callbacks with a polling mechanism. `SessionManager` only sets boolean flags; `AxCryptApp._check_auto_lock()` polls every 1 second via `self.after(1000, ...)` — executing only on the main thread.

### Fix 2: `[Errno 9] Bad file descriptor`

**Root Cause:** The original in-place encrypt function called `os.replace()` while file handles were still open, violating OS file-descriptor rules on all platforms.

**Fix:** `encrypt_file_replace` now reads the entire file to memory first (closing all handles), encrypts in memory, writes to a temp file via `os.fdopen(fd, 'wb')` with explicit `fsync`, then calls `os.replace()` after all handles are closed.

### Fix 3: Font Error on Startup

**Root Cause:** `SplashScreen` was being created as a standalone `ctk.CTk()` root before `AxCryptApp`, so when `AxCryptApp` tried to register fonts there was no established root window.

**Fix:** `main.py` now creates `AxCryptApp` first (establishing the root), hides it with `app.withdraw()`, then creates `SplashScreen` as a `Toplevel`. A single `app.mainloop()` drives everything.

### Fix 4: `BooleanVar` / `StringVar` Without Master

**Root Cause:** Several panels created `tk.BooleanVar()` or `tk.StringVar()` without passing `master=`, which can raise errors in later Tkinter/Python versions.

**Fix:** All variable constructors now pass the containing frame as `master`, e.g. `tk.BooleanVar(master=self)`.

---

## 11. Enhancements & Roadmap

### Completed Enhancements (v1.0.1)

- Settings panel back button for navigation consistency
- Persistent footer navigation bar across all main panels
- CustomTkinter migration for all major panels (`app.py`, `splash.py`, `auth_panel`)
- Thread-safe queue-based worker communication for encrypt/decrypt
- Atomic in-place file replacement
- Main-thread-safe auto-lock via polling

### Planned Enhancements

- **Animated cyber-grid background** on auth screen using a `tk.Canvas` with periodic `after()` redraws
- **Count-up animations** for dashboard stat counters (0 → actual value over 800ms)
- **OTP countdown timer** with visible MM:SS display and resend button
- **Input focus glow** on `DarkEntry` using border color transitions
- **Error shake animation** on failed login (horizontal offset sequence)
- **SMS gateway integration** for real OTP delivery (Twilio, AWS SNS, etc.)
- **Master password** for user DB encryption instead of fixed-string KDF
- **Per-install `_HMAC_KEY`** stored in OS keychain for time-lock tokens
- **Drag-and-drop** file selection
- **Folder encryption** (recursive, zip-then-encrypt)
- **Key file support** (two-factor: password + key file)
- **Cloud backup** of encrypted files

---

## Appendix: Widget API Quick Reference

```python
# NeonButton
NeonButton(parent, text="ENCRYPT", colour=C["neon_green"], command=fn)

# DarkEntry
entry = DarkEntry(parent, placeholder="enter password", show="•", width=35)
entry.get()         # Returns current value
entry.bind_key(event, callback)

# CardFrame
card = CardFrame(parent, border_colour=C["neon_cyan"])
# Use card as any tk.Frame

# NeonProgressBar
bar = NeonProgressBar(parent, colour=C["neon_green"])
bar.set(0.75)       # Set to 75%
bar.start()         # Start indeterminate animation
bar.stop()

# StrengthBar
sb = StrengthBar(parent)
sb.set_strength(72) # Score 0-100; updates colour + label

# TerminalText
term = TerminalText(parent)
term.print("message", tag="success")  # tags: success, danger, info, warning
term.clear()

# ScrollableFrame
sf = ScrollableFrame(parent)
# Add children to sf.scrollable_frame, not sf directly
```

---

---

## Author

**Raulji Siddharthsinh**

- 🐙 GitHub: [Siddh7-ai](https://github.com/Siddh7-ai)
- 💼 LinkedIn: [siddharthsinhraulji](https://www.linkedin.com/in/siddharthsinhraulji)

*Documentation generated for AxCrypt v1.0.1 — CustomTkinter Edition*