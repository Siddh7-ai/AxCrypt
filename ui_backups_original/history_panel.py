"""
axcrypt/ui/history_panel.py
───────────────────────────
HISTORY tab – tamper-resistant encryption log viewer.
  • Table of all past operations
  • Colour-coded by action & status
  • Chain-integrity verification button
  • Search / filter by action type
  • Clear history (with confirmation)
"""

import tkinter as tk
from core.config import C
from ui.widgets  import CardFrame, NeonButton


class HistoryPanel(tk.Frame):

    def __init__(self, app):
        super().__init__(app.content, bg=C["bg_deep"])
        self.app = app
        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # ── top bar ────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=C["bg_panel"])
        top.pack(fill="x")
        tk.Label(top, text="📜  ENCRYPTION HISTORY",
                 font=("Courier", 32, "bold"),
                 bg=C["bg_panel"], fg=C["text_white"]).pack(side="left", padx=(18, 0), pady=19)

        # Right-side buttons
        btn_row = tk.Frame(top, bg=C["bg_panel"])
        btn_row.pack(side="right", padx=(0, 18))

        NeonButton(btn_row, text="🔍 VERIFY CHAIN", colour=C["neon_violet"],
                   command=self._verify_chain).pack(side="left", ipadx=19, ipady=6, padx=(0, 8))
        NeonButton(btn_row, text="🗑️ CLEAR", colour=C["danger"],
                   command=self._clear_history).pack(side="left", ipadx=19, ipady=6)

        # Filter row
        filter_row = tk.Frame(self, bg=C["bg_panel"])
        filter_row.pack(fill="x", padx=28, pady=(8, 4))
        tk.Label(filter_row, text="FILTER:", font=("Courier", 22),
                 bg=C["bg_panel"], fg=C["text_dim"]).pack(side="left")
        for label, value in [("ALL", ""), ("ENCRYPT", "ENCRYPT"),
                             ("DECRYPT", "DECRYPT"), ("DELETE", "SECURE_DELETE")]:
            colours = {
                "":              (C["text_mid"],   C["bg_card"]),
                "ENCRYPT":       (C["neon_green"], C["bg_card"]),
                "DECRYPT":       (C["neon_cyan"],  C["bg_card"]),
                "SECURE_DELETE": (C["neon_violet"],C["bg_card"]),
            }
            fg, bg = colours.get(value, (C["text_mid"], C["bg_card"]))
            btn = tk.Button(filter_row, text=label, font=("Courier", 19, "bold"),
                            bg=bg, fg=fg, activebackground=C["border"],
                            activeforeground=C["text_hi"],
                            relief="flat", bd=0, cursor="hand2",
                            command=lambda v=value: self._apply_filter(v))
            btn.pack(side="left", padx=(6, 0), pady=6, ipadx=12, ipady=3)

        # Chain-integrity status
        self._chain_status = tk.Label(self, text="", font=("Courier", 22, "bold"),
                                      bg=C["bg_deep"], fg=C["text_dim"])
        self._chain_status.pack(pady=(2, 4))

        # ── table header ───────────────────────────────────────────────────
        self._table_frame = tk.Frame(self, bg=C["bg_deep"])
        self._table_frame.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        # Scrollable canvas
        self._canvas = tk.Canvas(self._table_frame, bg=C["bg_deep"],
                                 highlightthickness=0)
        scrollbar = tk.Scrollbar(self._table_frame, orient="vertical",
                                 command=self._canvas.yview,
                                 bg=C["bg_panel"], troughcolor=C["bg_deep"],
                                 highlightthickness=0)
        self._scroll_frame = tk.Frame(self._canvas, bg=C["bg_deep"])
        self._scroll_frame.bind("<Configure>",
                                lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Header row
        self._header_row()
        self._filter_value = ""

    def _header_row(self):
        cols = [("No.", 64), ("#  TIME", 288), ("ACTION", 160),
                ("FILE", 448), ("STATUS", 144), ("USER", 192)]
        row = tk.Frame(self._scroll_frame, bg=C["bg_panel"])
        row.pack(fill="x", pady=(0, 2))
        for txt, w in cols:
            tk.Label(row, text=txt, font=("Courier", 19, "bold"),
                     bg=C["bg_panel"], fg=C["neon_cyan"],
                     width=w // 7, anchor="w").pack(side="left", padx=(8, 0))

    # ══════════════════════════════════════════════════════════════════════
    # PUBLIC
    # ══════════════════════════════════════════════════════════════════════
    def show(self):
        self.pack(fill="both", expand=True)

    def hide(self):
        self.pack_forget()

    def on_show(self):
        self._populate(self._filter_value)

    # ══════════════════════════════════════════════════════════════════════
    # POPULATE TABLE
    # ══════════════════════════════════════════════════════════════════════
    def _populate(self, filter_action: str = ""):
        # Remove all body rows (keep header)
        children = self._scroll_frame.winfo_children()
        for w in children[1:]:        # skip header
            w.destroy()

        entries = self.app.history.get_all()   # newest first
        if filter_action:
            entries = [e for e in entries if e.get("action") == filter_action]

        if not entries:
            tk.Label(self._scroll_frame, text="  No history entries.",
                     font=("Courier", 25), bg=C["bg_deep"], fg=C["text_dim"]
                     ).pack(pady=32, anchor="w")
            return

        action_colours = {
            "ENCRYPT":       C["neon_green"],
            "DECRYPT":       C["neon_cyan"],
            "SECURE_DELETE": C["neon_violet"],
        }

        for i, entry in enumerate(entries):
            action  = entry.get("action",       "?")
            fname   = entry.get("filename",     "?")
            status  = entry.get("status",       "?")
            user    = entry.get("user",         "")
            ts      = entry.get("display_time", "?")
            a_colour = action_colours.get(action, C["text_mid"])
            s_colour = C["success"] if status == "Success" else C["danger"]

            row_bg = C["bg_card"] if i % 2 == 0 else C["bg_panel"]
            row = tk.Frame(self._scroll_frame, bg=row_bg)
            row.pack(fill="x", pady=(1, 0))

            tk.Label(row, text=str(i + 1), font=("Courier", 22),
                     bg=row_bg, fg=C["text_dim"], width=6, anchor="w"
                     ).pack(side="left", padx=(8, 0))
            tk.Label(row, text=ts, font=("Courier", 22),
                     bg=row_bg, fg=C["text_mid"], width=38, anchor="w"
                     ).pack(side="left", padx=(4, 0))
            tk.Label(row, text=action, font=("Courier", 22, "bold"),
                     bg=row_bg, fg=a_colour, width=20, anchor="w"
                     ).pack(side="left", padx=(4, 0))
            tk.Label(row, text=fname, font=("Courier", 22),
                     bg=row_bg, fg=C["text_hi"], width=60, anchor="w"
                     ).pack(side="left", padx=(4, 0))
            tk.Label(row, text=status, font=("Courier", 22, "bold"),
                     bg=row_bg, fg=s_colour, width=19, anchor="w"
                     ).pack(side="left", padx=(4, 0))
            tk.Label(row, text=user, font=("Courier", 22),
                     bg=row_bg, fg=C["text_dim"], width=25, anchor="w"
                     ).pack(side="left", padx=(4, 0))

        # Scroll to top
        self._canvas.yview_moveto(0)

    # ══════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════════════════════════════════
    def _apply_filter(self, value: str):
        self._filter_value = value
        self._populate(value)

    def _verify_chain(self):
        intact, msg = self.app.history.verify_chain()
        colour = C["success"] if intact else C["danger"]
        self._chain_status.configure(text=f"  🔍 {msg}", fg=colour)

    def _clear_history(self):
        # Simple confirmation via messagebox
        import tkinter.messagebox as mb
        if mb.askyesno("Confirm", "Clear all history entries?"):
            self.app.history.clear()
            self._populate(self._filter_value)
            self._chain_status.configure(text="  History cleared.", fg=C["text_dim"])
