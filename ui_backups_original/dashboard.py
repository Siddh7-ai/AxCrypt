"""
axcrypt/ui/dashboard.py
───────────────────────
Dashboard – first screen after login.
  • Welcome greeting with animated typing
  • Stats: total encryptions, decryptions, secure deletes
  • Encryption Difficulty Indicator (live)
  • Recent activity feed (last 5 entries)
"""

import tkinter as tk
from core.config import C
from ui.widgets  import CardFrame, TerminalText, NeonButton


class DashboardPanel(tk.Frame):

    def __init__(self, app):
        super().__init__(app.content, bg=C["bg_deep"])
        self.app = app

        # ── top row: welcome + stats cards ────────────────────────────────
        top = tk.Frame(self, bg=C["bg_deep"])
        top.pack(fill="x", padx=32, pady=(20, 12))

        # Welcome card (wider)
        self._welcome_card = CardFrame(top, border_colour=C["neon_cyan"])
        self._welcome_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self._welcome_text = TerminalText(self._welcome_card)
        self._welcome_text.pack(fill="both", expand=True, ipady=16)

        # Stats column
        stats_col = tk.Frame(top, bg=C["bg_deep"], width=320)
        stats_col.pack(side="right", fill="y")
        stats_col.pack_propagate(False)

        self._stat_labels = {}
        for label, key, colour in [
            ("ENCRYPTIONS",   "enc",  C["neon_green"]),
            ("DECRYPTIONS",   "dec",  C["neon_cyan"]),
            ("SECURE DELETES","del",  C["neon_violet"]),
        ]:
            card = CardFrame(stats_col, border_colour=colour)
            card.pack(fill="x", pady=(0, 8))
            tk.Label(card, text=label, font=("Arial", 19),
                     bg=C["bg_card"], fg=C["text_dim"]).pack(pady=(10, 0))
            lbl = tk.Label(card, text="0", font=("Arial", 65, "bold"),
                           bg=C["bg_card"], fg=colour)
            lbl.pack(pady=(0, 10))
            self._stat_labels[key] = lbl

        # ── middle row: difficulty indicator + quick actions ──────────────
        mid = tk.Frame(self, bg=C["bg_deep"])
        mid.pack(fill="x", padx=32, pady=(0, 12))

        # Difficulty card
        diff_card = CardFrame(mid, border_colour=C["neon_orange"])
        diff_card.pack(side="left", fill="both", expand=True, padx=(0, 12), ipady=12)
        tk.Label(diff_card, text="⚡ ENCRYPTION DIFFICULTY", font=("Arial", 27, "bold"),
                 bg=C["bg_card"], fg=C["neon_orange"]).pack(pady=(14, 6))
        self._diff_label = tk.Label(diff_card, text="─", font=("Arial", 51, "bold"),
                                    bg=C["bg_card"], fg=C["text_dim"])
        self._diff_label.pack()
        self._diff_sub = tk.Label(diff_card, text="Set a password to see difficulty",
                                  font=("Arial", 22), bg=C["bg_card"], fg=C["text_dim"])
        self._diff_sub.pack(pady=(2, 14))

        # Quick-action buttons
        qa_card = CardFrame(mid, border_colour=C["border_glow"])
        qa_card.pack(side="right", fill="y")
        tk.Label(qa_card, text="QUICK ACTIONS", font=("Arial", 25, "bold"),
                 bg=C["bg_card"], fg=C["text_mid"]).pack(pady=(14, 8), padx=28)
        NeonButton(qa_card, text="ENCRYPT", colour=C["neon_green"],
                   command=lambda: self.app._switch_tab("ENCRYPT")
                   ).pack(pady=6, padx=28, ipadx=28, ipady=6)
        NeonButton(qa_card, text="DECRYPT", colour=C["neon_cyan"],
                   command=lambda: self.app._switch_tab("DECRYPT")
                   ).pack(pady=6, padx=28, ipadx=28, ipady=6)
        NeonButton(qa_card, text="HISTORY", colour=C["neon_violet"],
                   command=lambda: self.app._switch_tab("HISTORY")
                   ).pack(pady=(4, 14), padx=28, ipadx=28, ipady=6)

        # ── bottom: recent activity feed ──────────────────────────────────
        bot = tk.Frame(self, bg=C["bg_deep"])
        bot.pack(fill="both", expand=True, padx=32, pady=(0, 16))
        recent_card = CardFrame(bot, border_colour=C["border_glow"])
        recent_card.pack(fill="both", expand=True)
        tk.Label(recent_card, text="📋  RECENT ACTIVITY", font=("Arial", 27, "bold"),
                 bg=C["bg_card"], fg=C["text_mid"]).pack(anchor="w", padx=25, pady=(12, 6))
        self._activity = TerminalText(recent_card)
        self._activity.pack(fill="both", expand=True, padx=(0, 0))

    # ── public ─────────────────────────────────────────────────────────────
    def show(self):
        self.pack(fill="both", expand=True)

    def hide(self):
        self.pack_forget()

    def on_show(self):
        """Refresh data every time dashboard is surfaced."""
        user = self.app.session.username or "User"
        self._welcome_text.clear()
        
        # Use animate_print for first line only, then regular print for rest
        self._welcome_text.animate_print(f"Welcome back, {user}.", tag="cyan")
        
        # Wait for animation to complete before adding other lines
        self.after(len(user) * 18 + 500, self._add_welcome_lines)

    def _add_welcome_lines(self):
        """Add remaining welcome text after animation completes"""
        self._welcome_text.print("AxCrypt – Master-Level Encryption", tag="green")
        self._welcome_text.print("for Code & Files", tag="green")
        self._welcome_text.print("", tag="dim")
        self._welcome_text.print("Use the tabs above to encrypt,", tag="dim")
        self._welcome_text.print("decrypt, or manage your files.", tag="dim")
        
        # Now update stats and activity
        self._update_stats_and_activity()

    def _update_stats_and_activity(self):
        """Update stats and recent activity"""
        # Stats from history
        entries = self.app.history.entries
        enc_count = sum(1 for e in entries if e.get("action") == "ENCRYPT")
        dec_count = sum(1 for e in entries if e.get("action") == "DECRYPT")
        del_count = sum(1 for e in entries if e.get("action") == "SECURE_DELETE")
        self._stat_labels["enc"].configure(text=str(enc_count))
        self._stat_labels["dec"].configure(text=str(dec_count))
        self._stat_labels["del"].configure(text=str(del_count))

        # Recent activity
        self._activity.clear()
        recent = self.app.history.get_all()[:6]
        if not recent:
            self._activity.print("  No activity yet – start encrypting!", tag="dim")
        else:
            for entry in recent:
                action = entry.get("action", "?")
                fname  = entry.get("filename", "?")
                status = entry.get("status", "?")
                ts     = entry.get("display_time", "?")
                tag    = "success" if status == "Success" else "danger"
                self._activity.print(f"  [{ts}]  {action:16s} {fname:40s} [{status}]", tag=tag)

    def update_difficulty(self, score: int):
        """Called from encrypt panel as the user types a password."""
        from core.config import DIFFICULTY_TIERS
        label, colour, icon = "Casual", C["danger"], "⚠️"
        for threshold, lbl, clr, icn in DIFFICULTY_TIERS:
            if score >= threshold:
                label, colour, icon = lbl, clr, icn
        self._diff_label.configure(text=f"{icon}  {label}", fg=colour)
        self._diff_sub.configure(text=f"Strength score: {score}/100", fg=colour)