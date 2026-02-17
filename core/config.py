"""
axcrypt/core/config.py
─────────────────────
Central configuration & constants for AxCrypt.
"""

import os

# ─── App Identity ─────────────────────────────────────────────────────────────
APP_NAME        = "AxCrypt"
APP_TAGLINE     = "Master-Level Encryption for Code & Files"
APP_VERSION     = "1.0.1"

# ─── Filesystem Layout ────────────────────────────────────────────────────────
APP_DIR         = os.path.join(os.path.expanduser("~"), ".axcrypt")
DATA_DIR        = os.path.join(APP_DIR, "data")
TEMP_DIR        = os.path.join(APP_DIR, "tmp")
LOG_FILE        = os.path.join(APP_DIR, "axcrypt.log")

USERS_DB        = os.path.join(DATA_DIR, "users.axc")
HISTORY_DB      = os.path.join(DATA_DIR, "history.axc")
SESSION_FILE    = os.path.join(DATA_DIR, "session.axc")

# ─── Assets ────────────────────────────────────────────────────────────────────
_SCRIPT_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR      = os.path.join(_SCRIPT_DIR, "assets")
LOGO_PATH       = os.path.join(ASSETS_DIR, "logo.png")

for _d in (APP_DIR, DATA_DIR, TEMP_DIR):
    os.makedirs(_d, exist_ok=True)

# ─── Cryptographic Constants ─────────────────────────────────────────────────
SALT_SIZE       = 16
IV_SIZE         = 16
KEY_SIZE        = 32
SCRYPT_N        = 2**15
SCRYPT_R        = 8
SCRYPT_P        = 1

# ─── Security Tunables ────────────────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS  = 3
LOCKOUT_SECS        = 120
SESSION_TIMEOUT     = 300
OTP_VALIDITY_SECS   = 300
OTP_LENGTH          = 6

# ─── Secure-Delete ────────────────────────────────────────────────────────────
WIPE_PASSES     = 7

# ─── One-Time Decrypt ─────────────────────────────────────────────────────────
OTD_MARKER      = b"\x4f\x54\x44\x31"

# ─── Steganographic Metadata ──────────────────────────────────────────────────
STEG_MAGIC      = b"\xAC\xCE"

# ─── UI Window Sizes ──────────────────────────────────────────────────────────
WIN_W           = 1200
WIN_H           = 800
MIN_W           = 1024
MIN_H           = 700

# ─── Splash Screen ─────────────────────────────────────────────────────────────
SPLASH_DURATION = 2500


# ─── Modern Fonts (High Readability) ──────────────────────────────────────────
FONT_FAMILY = "Arial"  # Modern, clean, works everywhere
FONT_MONO = "Consolas" if __import__("os").name == "nt" else "Courier"

# ─── Central Font Map (Used Across UI) ────────────────────────────────────────
FONTS = {
    "title":   (FONT_FAMILY, 16, "bold"),
    "header":  (FONT_FAMILY, 13, "bold"),
    "section": (FONT_FAMILY, 11, "bold"),
    "body":    (FONT_FAMILY, 10),
    "small":   (FONT_FAMILY, 9),
    "mono":    (FONT_MONO,   9),
}

# ─── Cyberpunk Colour Palette ─────────────────────────────────────────────────
C = dict(
    bg_deep      = "#0a0c0f",
    bg_panel     = "#111318",
    bg_card      = "#161a22",
    bg_input     = "#0e1014",
    border       = "#1e2530",
    border_glow  = "#2a3545",
    text_dim     = "#4a5568",
    text_mid     = "#a0aec0",
    text_hi      = "#e2e8f0",
    text_white   = "#f7fafc",
    neon_green   = "#39ff14",
    neon_cyan    = "#00f0ff",
    neon_violet  = "#bf5fff",
    neon_pink    = "#ff2d95",
    neon_orange  = "#ff9f1c",
    success      = "#39ff14",
    warning      = "#ff9f1c",
    danger       = "#ff2d95",
    info         = "#00f0ff",
    stage_kdf    = "#bf5fff",
    stage_pad    = "#00f0ff",
    stage_enc    = "#39ff14",
    stage_out    = "#ff9f1c",
    btn_disabled = "#2a2f3a",
    btn_hover    = "#1f2530",
    bg_hover     = "#1a1e28",
)

# ─── Encryption-Difficulty Thresholds ─────────────────────────────────────────
DIFFICULTY_TIERS = [
    (0,  "Casual",           C["danger"],    "⚠️"),
    (40, "Professional",     C["warning"],   "⚡"),
    (70, "Military Grade",   C["success"],   "🛡️"),
]