"""
axcrypt/core/history.py
───────────────────────
Tamper-resistant encryption-activity log.

Each entry is HMAC-chained: the HMAC of entry N includes the HMAC of entry N-1.
Any modification / deletion / reorder of an entry breaks the chain and is
detected on load.

The full chain is stored AES-encrypted on disk (reuses the same db-wrap
mechanism as the users store).
"""

import os, json, time, hmac, hashlib, logging, secrets
from datetime import datetime
from core.config import HISTORY_DB

log = logging.getLogger("axcrypt.history")

# ─── Reuse the encrypted-blob helpers from user_manager ──────────────────────
from core.user_manager import _encrypt_blob, _decrypt_blob

# HMAC key for the chain – derived at import time from a per-install secret
_CHAIN_KEY_FILE = os.path.join(os.path.dirname(HISTORY_DB), "chain.key")


def _chain_key() -> bytes:
    if os.path.exists(_CHAIN_KEY_FILE):
        with open(_CHAIN_KEY_FILE, "rb") as f:
            return f.read()
    key = secrets.token_bytes(32)
    with open(_CHAIN_KEY_FILE, "wb") as f:
        f.write(key)
    return key


def _entry_hash(entry: dict, prev_hash: str) -> str:
    """Compute HMAC-SHA256 for an entry, chained to prev_hash."""
    payload = json.dumps({"entry": entry, "prev": prev_hash}, sort_keys=True)
    return hmac.new(_chain_key(), payload.encode(), hashlib.sha256).hexdigest()


class HistoryManager:
    """Load / save / append / verify the HMAC-chained history."""

    MAX_ENTRIES = 200

    def __init__(self):
        self.entries: list[dict] = []
        self._load()

    # ── persistence ────────────────────────────────────────────────────────
    def _load(self):
        if not os.path.exists(HISTORY_DB):
            self.entries = []
            return
        try:
            raw  = open(HISTORY_DB, "rb").read()
            data = json.loads(_decrypt_blob(raw).decode("utf-8"))
            self.entries = data.get("entries", [])
        except Exception as exc:
            log.warning("History load failed (%s) – starting fresh.", exc)
            self.entries = []

    def _save(self):
        data = json.dumps({"entries": self.entries}).encode("utf-8")
        with open(HISTORY_DB, "wb") as f:
            f.write(_encrypt_blob(data))

    # ── append ─────────────────────────────────────────────────────────────
    def add(self, action: str, filename: str, status: str = "Success",
            algorithm: str = "AES-256-CBC", user: str = "", extra: dict | None = None):
        """Append one entry and re-save."""
        prev_hash = self.entries[-1]["_hash"] if self.entries else "GENESIS"

        entry = {
            "action":    action,           # ENCRYPT | DECRYPT | SECURE_DELETE | …
            "filename":  filename,
            "algorithm": algorithm,
            "status":    status,           # Success | Failed
            "user":      user,
            "timestamp": datetime.now().isoformat(),
            "display_time": datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
        }
        if extra:
            entry.update(extra)

        entry["_hash"] = _entry_hash(
            {k: v for k, v in entry.items() if k != "_hash"},
            prev_hash,
        )
        self.entries.append(entry)

        # Trim oldest if over limit
        if len(self.entries) > self.MAX_ENTRIES:
            # Re-chain after trim
            self.entries = self.entries[-self.MAX_ENTRIES:]
            self._rechain()

        self._save()

    # ── verification ───────────────────────────────────────────────────────
    def verify_chain(self) -> tuple[bool, str]:
        """Walk the chain and verify every HMAC.

        Returns (intact, message).
        """
        prev = "GENESIS"
        for i, entry in enumerate(self.entries):
            stored_hash = entry.get("_hash", "")
            computed    = _entry_hash(
                {k: v for k, v in entry.items() if k != "_hash"},
                prev,
            )
            if stored_hash != computed:
                return False, f"Chain broken at entry #{i} ({entry.get('display_time','?')})"
            prev = stored_hash
        return True, f"Chain intact – {len(self.entries)} entries verified."

    # ── helpers ────────────────────────────────────────────────────────────
    def _rechain(self):
        """Re-compute HMACs for the entire list (after trim)."""
        prev = "GENESIS"
        for entry in self.entries:
            entry["_hash"] = _entry_hash(
                {k: v for k, v in entry.items() if k != "_hash"},
                prev,
            )
            prev = entry["_hash"]

    def clear(self):
        self.entries = []
        self._save()

    def get_all(self) -> list[dict]:
        return list(reversed(self.entries))   # newest-first for display
