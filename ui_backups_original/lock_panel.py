"""
axcrypt/ui/lock_panel.py
────────────────────────
Screen shown on session auto-lock or panic-lock.
Requires re-entry of the master password to unlock.
"""

import tkinter as tk
from core.config import C
from ui.widgets  import NeonButton, DarkEntry, CardFrame, PulseLabel


class LockPanel(tk.Frame):

    def __init__(self, app):
        super().__init__(app.content, bg=C["bg_deep"])
        self.app = app

        card = CardFrame(self, border_colour=C["neon_violet"])
        card.place(relx=0.5, rely=0.5, anchor="center", width=608, height=544)

        # Pulsing lock icon
        self._pulse = PulseLabel(card, text="🔒", font=("Courier", 132),
                                 bg=C["bg_card"], fg=C["neon_violet"],
                                 colour_a=C["neon_violet"], colour_b=C["text_dim"])
        self._pulse.pack(pady=(20, 0))

        tk.Label(card, text="SESSION LOCKED", font=("Courier", 38, "bold"),
                 bg=C["bg_card"], fg=C["text_white"]).pack(pady=(4, 2))
        tk.Label(card, text="Enter master password to unlock", font=("Courier", 22),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(pady=(0, 18))

        tk.Label(card, text="MASTER PASSWORD", font=("Courier", 19),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=76)
        self._pwd_entry = DarkEntry(card, placeholder="password", show="•", width=44)
        self._pwd_entry.pack(padx=76, pady=(2, 8))
        self._pwd_entry.bind_key("<Return>", lambda _: self._unlock())

        self._status = tk.Label(card, text="", font=("Courier", 22),
                                bg=C["bg_card"], fg=C["danger"])
        self._status.pack(pady=(0, 8))

        btn_row = tk.Frame(card, bg=C["bg_card"])
        btn_row.pack(pady=(4, 16))
        NeonButton(btn_row, text="UNLOCK", colour=C["neon_violet"],
                   command=self._unlock).pack(side="left", ipadx=32, ipady=8, padx=(0, 8))
        NeonButton(btn_row, text="LOGOUT", colour=C["neon_orange"],
                   command=self._logout).pack(side="left", ipadx=19, ipady=8)

    # ── public ─────────────────────────────────────────────────────────────
    def show(self):
        self.pack(fill="both", expand=True)
        self._pulse.start()
        self._pwd_entry.set("")
        self._status.configure(text="")
        self._pwd_entry.focus()

    def hide(self):
        self._pulse.stop()
        self.pack_forget()

    # ── actions ────────────────────────────────────────────────────────────
    def _unlock(self):
        pwd  = self._pwd_entry.get()
        user = self.app.session.username
        if not user:
            self._logout()
            return
        ok, msg = self.app.user_mgr.authenticate(user, pwd)
        if ok:
            self._status.configure(text="")
            self.app.session.locked = False
            self.app.session.touch()
            self.app.show_main(user)
        else:
            self._status.configure(text=msg, fg=C["danger"])

    def _logout(self):
        self.app.session.logout()
        self.app.show_auth()
