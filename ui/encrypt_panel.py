import os, tkinter as tk, threading, queue, random, time
from core.config import C
from core.crypto import (
    password_strength, encrypt_file, encrypt_file_replace, secure_delete, generate_time_locked_password
)
from ui.widgets import (
    BackButton,
    NeonButton, DarkEntry, CardFrame, NeonProgressBar, StrengthBar, TerminalText,
    ScrollableFrame, EncryptModeDialog
)


class EncryptPanel(tk.Frame):

    def __init__(self, app):
        super().__init__(app.content, bg=C["bg_deep"])
        self.app = app
        self._selected_file = ""
        self._is_processing = False

        # Thread-safe queue for worker -> main thread communication
        self.ui_queue = queue.Queue()
        self._poll_job = None

        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        container = scroll.scrollable_frame

        # Back button
        back_frame = tk.Frame(container, bg=C["bg_deep"])
        back_frame.pack(fill="x", padx=15, pady=10)
        BackButton(back_frame, command=lambda: self.app._switch_tab("DASHBOARD")).pack(side="left")

        # ── LEFT: controls ────────────────────────────────────────────────
        left = tk.Frame(container, bg=C["bg_deep"], width=420)
        left.pack(side="left", fill="y", padx=(12, 5), pady=15)
        left.pack_propagate(False)

        # File selector
        file_card = CardFrame(left, border_colour=C["neon_green"])
        file_card.pack(fill="x", pady=(0, 10))
        tk.Label(file_card, text="📂  SELECT FILE", font=("Arial", 11, "bold"),
                 bg=C["bg_card"], fg=C["neon_green"]).pack(anchor="w", padx=15, pady=(8, 4))
        btn_row = tk.Frame(file_card, bg=C["bg_card"])
        btn_row.pack(fill="x", padx=15, pady=(0, 4))
        NeonButton(btn_row, text="BROWSE", colour=C["neon_green"],
                   command=self._browse_file).pack(side="left", ipadx=10, ipady=4)
        self._file_label = tk.Label(btn_row, text="No file selected",
                                    font=("Arial", 10), bg=C["bg_card"], fg=C["text_dim"])
        self._file_label.pack(side="left", padx=(10, 0))

        # Password card
        pwd_card = CardFrame(left, border_colour=C["neon_cyan"])
        pwd_card.pack(fill="x", pady=(0, 10))
        tk.Label(pwd_card, text="🔐  PASSWORD", font=("Arial", 11, "bold"),
                 bg=C["bg_card"], fg=C["neon_cyan"]).pack(anchor="w", padx=15, pady=(8, 4))
        tk.Label(pwd_card, text="PASSWORD", font=("Arial", 9),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=15)
        self._pwd_entry = DarkEntry(pwd_card, placeholder="encryption password", show="•", width=35)
        self._pwd_entry.pack(padx=15, pady=(2, 4))
        self._pwd_entry.bind_key("<KeyRelease>", self._on_pwd_change)

        tk.Label(pwd_card, text="CONFIRM PASSWORD", font=("Arial", 9),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=15)
        self._pwd_confirm = DarkEntry(pwd_card, placeholder="confirm password", show="•", width=35)
        self._pwd_confirm.pack(padx=15, pady=(2, 3))

        self._strength = StrengthBar(pwd_card)
        self._strength.pack(padx=15, pady=(2, 6), fill="x")

        # Options card
        opt_card = CardFrame(left, border_colour=C["neon_violet"])
        opt_card.pack(fill="x", pady=(0, 10))
        tk.Label(opt_card, text="⚙️  OPTIONS", font=("Arial", 11, "bold"),
                 bg=C["bg_card"], fg=C["neon_violet"]).pack(anchor="w", padx=15, pady=(8, 5))

        self._otd_var = tk.BooleanVar(master=self, value=False)
        otd_row = tk.Frame(opt_card, bg=C["bg_card"])
        otd_row.pack(fill="x", padx=15, pady=(0, 4))
        tk.Checkbutton(otd_row, variable=self._otd_var, text="",
                       bg=C["bg_card"], activebackground=C["bg_card"],
                       fg=C["neon_pink"], selectcolor=C["bg_input"]).pack(side="left")
        tk.Label(otd_row, text="🔥 One-Time Decrypt", font=("Arial", 10, "bold"),
                 bg=C["bg_card"], fg=C["neon_pink"]).pack(side="left")

        tk.Label(opt_card, text="OWNER INFO (hidden)", font=("Arial", 9),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=15)
        self._owner_entry = DarkEntry(opt_card, placeholder="your name", width=35)
        self._owner_entry.pack(padx=15, pady=(2, 8))

        # Status + progress
        self._status = tk.Label(left, text="", font=("Arial", 10),
                                bg=C["bg_deep"], fg=C["danger"])
        self._status.pack(pady=(4, 4))
        self._progress = NeonProgressBar(left, width=90, colour=C["neon_green"])
        self._progress.pack(pady=(0, 5))
        self._progress_label = tk.Label(left, text="", font=("Arial", 9),
                                        bg=C["bg_deep"], fg=C["text_dim"])
        self._progress_label.pack()

        self._encrypt_btn = NeonButton(left, text="⚡  ENCRYPT FILE", colour=C["neon_green"],
                                       command=self._start_encrypt)
        self._encrypt_btn.pack(pady=(6, 0), ipadx=20, ipady=6)

        # ── RIGHT: live visualization (mirrors decrypt panel exactly) ─────
        right = tk.Frame(container, bg=C["bg_deep"])
        right.pack(side="right", fill="both", expand=True, padx=(0, 12), pady=15)

        viz_card = CardFrame(right, border_colour=C["border_glow"])
        viz_card.pack(fill="both", expand=True)
        tk.Label(viz_card, text="📡  LIVE ENCRYPTION VISUALIZATION",
                 font=("Arial", 12, "bold"),
                 bg=C["bg_card"], fg=C["text_white"]).pack(pady=(8, 5), padx=15)

        # 4-stage indicators
        stages_frame = tk.Frame(viz_card, bg=C["bg_card"])
        stages_frame.pack(fill="x", padx=15, pady=(0, 5))

        self._stage_labels = {}
        self._stage_bars = {}

        stages = [
            ("KEY DERIVATION",  C["stage_kdf"], "Scrypt  n=2¹⁵"),
            ("PADDING",         C["stage_pad"], "PKCS7  128-bit"),
            ("ENCRYPTION",      C["stage_enc"], "AES-256-CBC"),
            ("OUTPUT",          C["stage_out"], "Write .enc file"),
        ]

        for i, (name, colour, desc) in enumerate(stages):
            row = tk.Frame(stages_frame, bg=C["bg_card"])
            row.pack(fill="x", pady=(6, 0))

            circle = tk.Label(row, text="●", font=("Arial", 12),
                              bg=C["bg_card"], fg=C["text_dim"])
            circle.pack(side="left", padx=(4, 8))

            lbl = tk.Label(row, text=name, font=("Arial", 11, "bold"),
                           bg=C["bg_card"], fg=C["text_dim"])
            lbl.pack(side="left")

            sub = tk.Label(row, text=f"  [{desc}]", font=("Arial", 9),
                           bg=C["bg_card"], fg=C["text_dim"])
            sub.pack(side="left")

            bar_bg = tk.Frame(row, bg=C["bg_input"], width=100, height=5)
            bar_bg.pack(side="right", fill="y")
            bar_bg.pack_propagate(False)
            bar_fill = tk.Frame(bar_bg, bg=colour, width=0)
            bar_fill.pack(side="left", fill="y")

            self._stage_labels[i] = (circle, lbl, sub, colour)
            self._stage_bars[i] = (bar_bg, bar_fill)

        tk.Frame(viz_card, bg=C["border"], height=1).pack(fill="x", padx=15, pady=10)
        tk.Label(viz_card, text="BYTE STREAM", font=("Arial", 9),
                 bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=15)
        self._byte_stream = TerminalText(viz_card)
        self._byte_stream.pack(fill="both", expand=True, padx=10, pady=(2, 8))

    # ══════════════════════════════════════════════════════════════════════
    # PUBLIC
    # ══════════════════════════════════════════════════════════════════════

    def show(self):
        self.pack(fill="both", expand=True)

    def hide(self):
        self.pack_forget()

    def on_show(self):
        pass

    def reset_state(self):
        """Reset all UI state - called when switching tabs"""
        self._selected_file = ""
        self._file_label.configure(text="No file selected", fg=C["text_dim"])
        self._pwd_entry.set("")
        self._pwd_confirm.set("")
        self._owner_entry.set("")
        self._otd_var.set(False)
        self._status.configure(text="")
        self._progress.set(0.0)
        self._progress_label.configure(text="")
        self._reset_viz()
        self._encrypt_btn.configure(state="normal", bg=self._encrypt_btn._dark)
        self._is_processing = False

        if self._poll_job:
            self.after_cancel(self._poll_job)
            self._poll_job = None

    # ══════════════════════════════════════════════════════════════════════
    # FILE / PASSWORD
    # ══════════════════════════════════════════════════════════════════════

    def _browse_file(self):
        import tkinter.filedialog as fd
        path = fd.askopenfilename(title="Select file to encrypt")
        if path:
            self._selected_file = path
            self._file_label.configure(text=os.path.basename(path), fg=C["neon_green"])

    def _on_pwd_change(self, _e=None):
        pwd = self._pwd_entry.get()
        score = password_strength(pwd)
        self._strength.update(score)
        # Live dashboard difficulty update
        if hasattr(self.app, "dashboard_panel"):
            self.app.dashboard_panel.update_difficulty(score)

    # ══════════════════════════════════════════════════════════════════════
    # ENCRYPT WORKFLOW (THREAD-SAFE)
    # ══════════════════════════════════════════════════════════════════════

    def _start_encrypt(self):
        if self._is_processing:
            return

        if not self._selected_file or not os.path.exists(self._selected_file):
            self._status.configure(text="⚠ Select a file first.", fg=C["danger"])
            return
        pwd = self._pwd_entry.get()
        if not pwd or len(pwd) < 8:
            self._status.configure(text="⚠ Password must be ≥ 8 chars.", fg=C["danger"])
            return
        if pwd != self._pwd_confirm.get():
            self._status.configure(text="⚠ Passwords don't match.", fg=C["danger"])
            return

        dialog = EncryptModeDialog(self)
        mode = dialog.show()
        if mode is None:
            return

        create_new = (mode == "new")

        self._is_processing = True
        self._encrypt_btn.configure(state="disabled", bg=C["btn_disabled"], cursor="watch")
        self._status.configure(text="Encrypting...", fg=C["info"])
        self._reset_viz()

        otd   = self._otd_var.get()
        owner = self._owner_entry.get().strip()
        src   = self._selected_file

        self._start_ui_polling()
        t = threading.Thread(
            target=self._run_encrypt,
            args=(pwd, create_new, otd, owner, src),
            daemon=True,
        )
        t.start()

    def _run_encrypt(self, pwd, create_new, otd, owner, src):
        """
        Worker thread — performs encryption.
        NEVER calls Tkinter directly; all UI updates go through the queue.
        """
        def _progress(frac):
            self.ui_queue.put(("progress", frac))

        try:
            # Stage 0 — Key derivation
            self.ui_queue.put(("stage", 0, "Deriving key from password …"))
            time.sleep(0.5)

            # Stage 1 — Padding
            self.ui_queue.put(("stage", 1, "Applying PKCS7 padding …"))
            time.sleep(0.3)

            # Stage 2 — Encryption (actual crypto work)
            self.ui_queue.put(("stage", 2, "Encrypting with AES-256-CBC …"))

            if create_new:
                ok, out_path, err = encrypt_file(
                    src, pwd,
                    one_time_decrypt=otd,
                    owner_info=owner,
                    progress_cb=_progress,
                )
            else:
                ok, out_path, err = encrypt_file_replace(
                    src, pwd,
                    one_time_decrypt=otd,
                    owner_info=owner,
                    progress_cb=_progress,
                )

            # Stage 3 — Output
            self.ui_queue.put(("stage", 3, "Writing encrypted file to disk …"))
            time.sleep(0.3)

            if ok:
                action = "ENCRYPT" if create_new else "ENCRYPT_REPLACE"
                extra = {"otd": otd, "output": out_path}
                if not create_new:
                    extra["mode"] = "in-place"
                self.app.history.add(
                    action, os.path.basename(src),
                    status="Success",
                    user=self.app.session.username or "",
                    extra=extra,
                )
                self.ui_queue.put(("complete", True, out_path))
            else:
                action = "ENCRYPT" if create_new else "ENCRYPT_REPLACE"
                self.app.history.add(
                    action, os.path.basename(src),
                    status="Failed",
                    user=self.app.session.username or "",
                )
                self.ui_queue.put(("complete", False, err))

        except Exception as e:
            self.ui_queue.put(("complete", False, str(e)))
        finally:
            self._is_processing = False
            self.ui_queue.put(("enable_button",))

    # ══════════════════════════════════════════════════════════════════════
    # QUEUE POLLING (MAIN THREAD)
    # ══════════════════════════════════════════════════════════════════════

    def _start_ui_polling(self):
        self._poll_ui_queue()

    def _poll_ui_queue(self):
        try:
            while True:
                try:
                    msg = self.ui_queue.get_nowait()
                    self._handle_ui_message(msg)
                except queue.Empty:
                    break
            self._poll_job = self.after(50, self._poll_ui_queue)
        except tk.TclError:
            self._poll_job = None

    def _handle_ui_message(self, msg):
        msg_type = msg[0]

        if msg_type == "stage":
            self._animate_stage(msg[1], msg[2])

        elif msg_type == "progress":
            self._update_progress(msg[1])

        elif msg_type == "complete":
            success, result = msg[1], msg[2]
            if self._poll_job:
                self.after_cancel(self._poll_job)
                self._poll_job = None
            if success:
                self._finish_ok(result)
            else:
                self._finish_fail(result)

        elif msg_type == "enable_button":
            self._encrypt_btn.configure(
                state="normal", bg=self._encrypt_btn._dark, cursor="hand2"
            )

    # ══════════════════════════════════════════════════════════════════════
    # FINISH HANDLERS (MAIN THREAD)
    # ══════════════════════════════════════════════════════════════════════

    def _finish_ok(self, out_path: str):
        self._progress.set(1.0)
        self._progress_label.configure(text="100% – Complete")
        self._status.configure(text=f"✔ Encrypted → {os.path.basename(out_path)}", fg=C["success"])
        self._byte_stream.print("\n  ✔ ENCRYPTION COMPLETE", tag="success")
        self._byte_stream.print(f"  Output: {out_path}", tag="dim")

    def _finish_fail(self, err: str):
        self._status.configure(text=f"✘ Error: {err}", fg=C["danger"])
        self._byte_stream.print(f"\n  ✘ FAILED: {err}", tag="danger")

    # ══════════════════════════════════════════════════════════════════════
    # VISUALIZATION (MAIN THREAD ONLY)
    # ══════════════════════════════════════════════════════════════════════

    def _reset_viz(self):
        self._byte_stream.clear()
        self._progress.set(0.0)
        self._progress_label.configure(text="")
        for i in range(4):
            circle, lbl, sub, colour = self._stage_labels[i]
            circle.configure(fg=C["text_dim"])
            lbl.configure(fg=C["text_dim"])
            sub.configure(fg=C["text_dim"])
            _, bar_fill = self._stage_bars[i]
            bar_fill.configure(width=0)

    def _animate_stage(self, idx: int, msg: str):
        """Light up a stage indicator and emit hex bytes — main thread only."""
        circle, lbl, sub, colour = self._stage_labels[idx]
        circle.configure(fg=colour)
        lbl.configure(fg=colour)
        sub.configure(fg=colour)
        _, bar_fill = self._stage_bars[idx]

        def _fill(pct=0):
            if pct <= 100:
                bar_fill.configure(width=int(120 * pct / 100))
                self.after(25, lambda: _fill(pct + 12))
        _fill()

        tags  = ["violet", "cyan", "green", "orange"]
        names = ["▶ KEY DERIVATION", "▶ PADDING", "▶ ENCRYPTION", "▶ OUTPUT"]
        self._print_bytes(names[idx], msg, tags[idx])

    def _print_bytes(self, stage_name: str, msg: str, tag: str):
        self._byte_stream.print(f"\n  {stage_name}", tag=tag)
        self._byte_stream.print(f"  {msg}", tag="dim")
        for _ in range(2):
            line = "  " + " ".join(f"{random.randint(0, 255):02x}" for _ in range(24))
            self._byte_stream.print(line, tag=tag)

    def _update_progress(self, frac: float):
        self._progress.set(frac)
        self._progress_label.configure(text=f"{int(frac * 100)}%")