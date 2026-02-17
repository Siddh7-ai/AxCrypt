"""
axcrypt/ui/settings_panel.py
────────────────────────────
SETTINGS tab.
  • Session auto-lock timeout control
  • Secure-delete pass count
  • Time-Lock Password Generator (create + copy)
  • About / version info
  • Change password (for logged-in user)
  
ENHANCEMENTS:
  • Added Back button for navigation consistency
  • Improved layout and visual hierarchy
"""

import tkinter as tk
from core.config import C, APP_NAME, APP_VERSION, APP_TAGLINE
from core.crypto import generate_time_locked_password
from ui.widgets  import CardFrame, NeonButton, DarkEntry, TerminalText, BackButton


class SettingsPanel(tk.Frame):

    def __init__(self, app):
        super().__init__(app.content, bg=C["bg_deep"])
        self.app = app
        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════════
    def _build_ui(self):

        back_frame = tk.Frame(self, bg=C["bg_deep"])
        back_frame.pack(fill="x", padx=28, pady=19)

        BackButton(
            back_frame,
            command=lambda: self.app._switch_tab("DASHBOARD")
        ).pack(side="left")
        
        # ── two-column layout ─────────────────────────────────────────────
        left  = tk.Frame(self, bg=C["bg_deep"])
        left.pack(side="left", fill="both", expand=True, padx=(18, 8), pady=(0, 18))
        right = tk.Frame(self, bg=C["bg_deep"])
        right.pack(side="right", fill="both", expand=True, padx=(0, 18), pady=(0, 18))

        # ────────────── LEFT COLUMN ──────────────────────────────────────
        # Session settings
        sess_card = CardFrame(left, border_colour=C["neon_cyan"])
        sess_card.pack(fill="x", pady=(0, 12))
        tk.Label(sess_card, text="⏱️  SESSION SETTINGS",
                 font=("Courier", 27, "bold"),
                 bg=C["bg_card"], fg=C["neon_cyan"]).pack(anchor="w", padx=25, pady=(12, 8))

        # Auto-lock timeout
        tk.Label(sess_card, text="AUTO-LOCK TIMEOUT (seconds)",
                 font=("Courier", 19), bg=C["bg_card"], fg=C["text_dim"]
                 ).pack(anchor="w", padx=25)
        self._timeout_var = tk.StringVar(master=sess_card, value="300")
        timeout_entry = tk.Entry(sess_card, textvariable=self._timeout_var,
                                 font=("Courier", 27), bg=C["bg_input"],
                                 fg=C["text_hi"], insertbackground=C["neon_cyan"],
                                 relief="flat", bd=4, highlightthickness=1,
                                 highlightcolor=C["neon_cyan"],
                                 highlightbackground=C["border"], width=16)
        timeout_entry.pack(anchor="w", padx=25, pady=(2, 4))

        tk.Label(sess_card, text="Current: 300s (5 min)  – restart required to take effect",
                 font=("Courier", 19), bg=C["bg_card"], fg=C["text_dim"]
                 ).pack(anchor="w", padx=25, pady=(0, 12))

        # Secure-delete settings
        del_card = CardFrame(left, border_colour=C["neon_violet"])
        del_card.pack(fill="x", pady=(0, 12))
        tk.Label(del_card, text="🗑️  SECURE DELETE",
                 font=("Courier", 27, "bold"),
                 bg=C["bg_card"], fg=C["neon_violet"]).pack(anchor="w", padx=25, pady=(12, 8))
        tk.Label(del_card, text="WIPE PASSES (1-35, default 7)",
                 font=("Courier", 19), bg=C["bg_card"], fg=C["text_dim"]
                 ).pack(anchor="w", padx=25)
        self._wipe_var = tk.StringVar(master=del_card, value="7")
        tk.Entry(del_card, textvariable=self._wipe_var,
                 font=("Courier", 27), bg=C["bg_input"],
                 fg=C["text_hi"], insertbackground=C["neon_violet"],
                 relief="flat", bd=4, highlightthickness=1,
                 highlightcolor=C["neon_violet"],
                 highlightbackground=C["border"], width=9
                 ).pack(anchor="w", padx=25, pady=(2, 4))
        tk.Label(del_card, text="7 passes = Schneier standard.  More passes = slower.",
                 font=("Courier", 19), bg=C["bg_card"], fg=C["text_dim"]
                 ).pack(anchor="w", padx=25, pady=(0, 12))

        # Change password
        chg_card = CardFrame(left, border_colour=C["neon_orange"])
        chg_card.pack(fill="x", pady=(0, 12))
        tk.Label(chg_card, text="🔐  CHANGE PASSWORD",
                 font=("Courier", 27, "bold"),
                 bg=C["bg_card"], fg=C["neon_orange"]).pack(anchor="w", padx=25, pady=(12, 8))
        tk.Label(chg_card, text="CURRENT PASSWORD", font=("Courier", 19),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=25)
        self._chg_old = DarkEntry(chg_card, placeholder="current", show="•", width=60)
        self._chg_old.pack(padx=25, pady=(2, 6))
        tk.Label(chg_card, text="NEW PASSWORD", font=("Courier", 19),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=25)
        self._chg_new = DarkEntry(chg_card, placeholder="new password", show="•", width=60)
        self._chg_new.pack(padx=25, pady=(2, 6))
        tk.Label(chg_card, text="CONFIRM NEW", font=("Courier", 19),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=25)
        self._chg_confirm = DarkEntry(chg_card, placeholder="confirm", show="•", width=60)
        self._chg_confirm.pack(padx=25, pady=(2, 6))
        self._chg_status = tk.Label(chg_card, text="", font=("Courier", 22),
                                    bg=C["bg_card"], fg=C["danger"])
        self._chg_status.pack(pady=(2, 4))
        NeonButton(chg_card, text="CHANGE PASSWORD", colour=C["neon_orange"],
                   command=self._do_change_pwd).pack(pady=(2, 12), ipadx=25, ipady=6)

        # ────────────── RIGHT COLUMN ─────────────────────────────────────
        # Time-Lock Password Generator
        tl_card = CardFrame(right, border_colour=C["neon_green"])
        tl_card.pack(fill="x", pady=(0, 12))
        tk.Label(tl_card, text="⏰  TIME-LOCK PASSWORD GENERATOR",
                 font=("Courier", 27, "bold"),
                 bg=C["bg_card"], fg=C["neon_green"]).pack(anchor="w", padx=25, pady=(12, 8))

        tk.Label(tl_card, text="BASE PASSWORD", font=("Courier", 19),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=25)
        self._tl_pwd = DarkEntry(tl_card, placeholder="password to wrap", show="•", width=60)
        self._tl_pwd.pack(padx=25, pady=(2, 6))

        tk.Label(tl_card, text="DURATION", font=("Courier", 19),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=25)
        dur_row = tk.Frame(tl_card, bg=C["bg_card"])
        dur_row.pack(fill="x", padx=25, pady=(2, 8))
        self._dur_var = tk.StringVar(master=tl_card, value="60")
        dur_options = [("1 min", "60"), ("5 min", "300"), ("30 min", "1800"),
                       ("1 hr", "3600"), ("24 hr", "86400")]
        for label, val in dur_options:
            tk.Radiobutton(dur_row, text=label, variable=self._dur_var, value=val,
                           bg=C["bg_card"], fg=C["text_mid"], activebackground=C["bg_card"],
                           selectcolor=C["bg_input"], font=("Courier", 19)
                           ).pack(side="left", padx=(0, 4))

        self._tl_output = tk.Label(tl_card, text="", font=("Courier", 19),
                                   bg=C["bg_card"], fg=C["neon_green"],
                                   justify="left", wraplength=380)
        self._tl_output.pack(anchor="w", padx=25, pady=(4, 4))

        btn_row = tk.Frame(tl_card, bg=C["bg_card"])
        btn_row.pack(pady=(2, 12))
        NeonButton(btn_row, text="GENERATE", colour=C["neon_green"],
                   command=self._gen_time_lock).pack(side="left", ipadx=22, ipady=6, padx=(0, 8))
        self._copy_btn = NeonButton(btn_row, text="COPY", colour=C["neon_cyan"],
                                    command=self._copy_token)
        self._copy_btn.pack(side="left", ipadx=22, ipady=6)
        self._generated_token = ""

        # About card
        about_card = CardFrame(right, border_colour=C["border_glow"])
        about_card.pack(fill="both", expand=True, pady=(0, 0))
        tk.Label(about_card, text="ℹ️  ABOUT AxCrypt",
                 font=("Courier", 27, "bold"),
                 bg=C["bg_card"], fg=C["text_white"]).pack(pady=(14, 8), padx=25)

        self._about_text = TerminalText(about_card)
        self._about_text.pack(fill="both", expand=True, padx=19, pady=(0, 12))

    # ══════════════════════════════════════════════════════════════════════
    # PUBLIC
    # ══════════════════════════════════════════════════════════════════════
    def show(self):
        self.pack(fill="both", expand=True)

    def hide(self):
        self.pack_forget()
    
    def reset_state(self):
        """Reset state when switching tabs"""
        pass

    def on_show(self):
        self._about_text.clear()
        self._about_text.print(f"  {APP_NAME}  v{APP_VERSION}", tag="cyan")
        self._about_text.print(f"  {APP_TAGLINE}", tag="dim")
        self._about_text.print("", tag="dim")
        self._about_text.print("  Security Features:", tag="green")
        self._about_text.print("    • AES-256-CBC encryption", tag="dim")
        self._about_text.print("    • Scrypt key derivation (n=2¹⁵)", tag="dim")
        self._about_text.print("    • 7-pass secure file deletion", tag="dim")
        self._about_text.print("    • HMAC-chained history log", tag="dim")
        self._about_text.print("    • One-Time Decrypt mode", tag="dim")
        self._about_text.print("    • Steganographic metadata", tag="dim")
        self._about_text.print("    • Panic Lock + auto-lock", tag="dim")
        self._about_text.print("    • Time-locked passwords", tag="dim")
        self._about_text.print("", tag="dim")
        self._about_text.print("  Built with Python + Tkinter", tag="violet")

    # ══════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════════════════════════════════
    def _do_change_pwd(self):
        user = self.app.session.username
        if not user:
            self._chg_status.configure(text="Not logged in.", fg=C["danger"])
            return
        old = self._chg_old.get()
        new = self._chg_new.get()
        con = self._chg_confirm.get()
        if not old or not new:
            self._chg_status.configure(text="Fill in all fields.", fg=C["danger"])
            return
        if new != con:
            self._chg_status.configure(text="New passwords don't match.", fg=C["danger"])
            return
        if len(new) < 8:
            self._chg_status.configure(text="New password must be ≥ 8 chars.", fg=C["danger"])
            return
        # Verify old
        ok, _ = self.app.user_mgr.authenticate(user, old)
        if not ok:
            self._chg_status.configure(text="Current password is wrong.", fg=C["danger"])
            return
        ok2, msg = self.app.user_mgr.reset_password(user, new)
        if ok2:
            self._chg_status.configure(text="✔ Password changed!", fg=C["success"])
            self._chg_old.set("")
            self._chg_new.set("")
            self._chg_confirm.set("")
        else:
            self._chg_status.configure(text=msg, fg=C["danger"])

    def _gen_time_lock(self):
        pwd = self._tl_pwd.get()
        if not pwd:
            self._tl_output.configure(text="Enter a base password first.", fg=C["danger"])
            return
        dur = int(self._dur_var.get())
        token, expiry = generate_time_locked_password(pwd, dur)
        self._generated_token = token
        from datetime import datetime
        exp_str = datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
        self._tl_output.configure(
            text=f"Token generated!\nExpires: {exp_str}\n\n{token[:60]}…",
            fg=C["neon_green"]
        )

    def _copy_token(self):
        if not self._generated_token:
            self._tl_output.configure(text="Generate a token first.", fg=C["danger"])
            return
        self.clipboard_clear()
        self.clipboard_append(self._generated_token)
        self.update()
        self._tl_output.configure(text="✔ Token copied to clipboard!", fg=C["success"])
        self.after(1500, lambda: self._tl_output.configure(
            text=f"{self._generated_token[:60]}…", fg=C["neon_green"]))