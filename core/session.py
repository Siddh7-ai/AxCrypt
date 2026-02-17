"""
axcrypt/core/session.py
───────────────────────
Session & Panic management.

  • Tracks the currently logged-in user.
  • Inactivity auto-lock after SESSION_TIMEOUT seconds.
  • PANIC LOCK: instantly locks the app, wipes all temp files.

CRITICAL FIX: Auto-lock now uses a polling mechanism instead of threading.Timer
to avoid "RuntimeError: main thread is not in main loop" when calling Tkinter
methods from background threads.

Why the original failed:
- threading.Timer runs callbacks in a background thread
- The callback attempted to call self.after() and UI methods
- Tkinter is NOT thread-safe and requires all UI calls from main thread
- after() and after_idle() still require main-thread execution

Correct approach:
- No threading.Timer for UI callbacks
- Session manager only tracks state (thread-safe)
- UI layer polls session state using Tkinter's native event loop
- All Tkinter calls happen only on the main thread
"""

import os, time, logging
from core.config import SESSION_TIMEOUT, TEMP_DIR
from core.crypto  import secure_delete_dir

log = logging.getLogger("axcrypt.session")


class SessionManager:
    """
    Singleton-style session tracker.
    
    This class is now UI-agnostic and thread-safe.
    It only manages session state without making any UI calls.
    """

    def __init__(self):
        self.username: str | None  = None
        self.locked:   bool        = True
        self._last_activity: float = 0.0
        self._lock_requested: bool = False  # Flag for UI to poll

    # ── public API ─────────────────────────────────────────────────────────
    def login(self, username: str):
        """Start a new session for the given user."""
        self.username = username
        self.locked   = False
        self._lock_requested = False
        self._last_activity = time.time()
        log.info("Session started for %s", username)

    def logout(self):
        """End the current session."""
        self.username = None
        self.locked   = True
        self._lock_requested = False
        log.info("Session ended.")

    def touch(self):
        """
        Call on any user interaction to reset the inactivity clock.
        This is thread-safe and can be called from any thread.
        """
        if not self.locked:
            self._last_activity = time.time()
            self._lock_requested = False  # Cancel any pending lock

    def is_locked(self) -> bool:
        """Check if the session is currently locked."""
        return self.locked

    def check_timeout(self) -> bool:
        """
        Check if the session has timed out due to inactivity.
        
        This method is designed to be called periodically by the UI layer
        using Tkinter's after() method (main thread only).
        
        Returns True if auto-lock should trigger, False otherwise.
        """
        if self.locked:
            return False
        
        # Check if enough time has passed since last activity
        inactive_time = time.time() - self._last_activity
        
        if inactive_time >= SESSION_TIMEOUT and not self._lock_requested:
            log.info("Auto-lock: session inactive for %ds.", SESSION_TIMEOUT)
            self.locked = True
            self._lock_requested = True
            return True
        
        return False

    def is_lock_requested(self) -> bool:
        """
        Check if a lock has been requested (either auto-lock or panic).
        UI should poll this flag and trigger lock screen when True.
        """
        return self._lock_requested

    def clear_lock_request(self):
        """Clear the lock request flag after UI has processed it."""
        self._lock_requested = False

    # ── panic lock ─────────────────────────────────────────────────────────
    def panic_lock(self):
        """
        Emergency lock: wipe all temp files and request immediate lock.
        
        This method is thread-safe and can be called from any thread.
        It only sets flags - actual UI locking must be done by the UI layer.
        """
        self.locked = True
        self._lock_requested = True

        # Wipe temp directory (this is safe to do from any thread)
        try:
            secure_delete_dir(TEMP_DIR)
            os.makedirs(TEMP_DIR, exist_ok=True)
            log.warning("⚠️  PANIC LOCK triggered – temp files wiped.")
        except Exception as e:
            log.error("Error during panic lock cleanup: %s", e)