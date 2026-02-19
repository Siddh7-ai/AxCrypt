"""
axcrypt/ui/decrypt_panel.py
───────────────────────────
DECRYPT tab.
  • File selector (only .enc files)
  • Password input (supports normal + time-locked tokens)
  • Steganographic metadata reader (shows hidden owner info)
  • OTD awareness – auto re-encrypt after first decrypt
  • Live decryption visualization (mirrored 4-stage)

CRITICAL FIX: Thread-safe UI updates using queue-based dispatcher
- Worker thread emits events to queue
- Main thread polls queue and updates UI
- NO Tkinter calls from background threads
"""

import os, tkinter as tk, threading, time, random, queue
from core.config import C
from core.crypto import (
    decrypt_file, encrypt_file, secure_delete,
    validate_time_locked_password, read_steg_metadata,
)
from ui.widgets import (
    BackButton,
    NeonButton, DarkEntry, CardFrame, NeonProgressBar, TerminalText
)


class DecryptPanel(tk.Frame):

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
        # Back button (top-left)
        back_frame = tk.Frame(self, bg=C["bg_deep"])
        back_frame.pack(fill="x", padx=15, pady=10)
        BackButton(back_frame, command=lambda: self.app._switch_tab("DASHBOARD")).pack(side="left")
        
        # ── LEFT: controls ────────────────────────────────────────────────
        left = tk.Frame(self, bg=C["bg_deep"], width=420)
        left.pack(side="left", fill="y", padx=(12, 5), pady=15)
        left.pack_propagate(False)

        # File selector
        file_card = CardFrame(left, border_colour=C["neon_cyan"])
        file_card.pack(fill="x", pady=(0, 10))
        tk.Label(file_card, text="📂  SELECT ENCRYPTED FILE",
                 font=("Arial", 11, "bold"),
                 bg=C["bg_card"], fg=C["neon_cyan"]).pack(anchor="w", padx=15, pady=(8, 4))
        btn_row = tk.Frame(file_card, bg=C["bg_card"])
        btn_row.pack(fill="x", padx=15, pady=(0, 3))
        NeonButton(btn_row, text="BROWSE", colour=C["neon_cyan"],
                   command=self._browse_file).pack(side="left", ipadx=10, ipady=4)
        self._file_label = tk.Label(btn_row, text="No file selected",
                                    font=("Arial", 10), bg=C["bg_card"], fg=C["text_dim"])
        self._file_label.pack(side="left", padx=(10, 0))

        # Steg-meta card (hidden until file is selected)
        self._steg_card = CardFrame(left, border_colour=C["neon_violet"])
        # not packed until needed
        tk.Label(self._steg_card, text="🕵️  STEGANOGRAPHIC METADATA",
                 font=("Arial", 11, "bold"),
                 bg=C["bg_card"], fg=C["neon_violet"]).pack(anchor="w", padx=15, pady=(6, 3))
        self._steg_label = tk.Label(self._steg_card, text="No hidden data found.",
                                    font=("Arial", 10), bg=C["bg_card"], fg=C["text_dim"],
                                    justify="left", wraplength=400)
        self._steg_label.pack(anchor="w", padx=15, pady=(0, 3))

        # Password
        pwd_card = CardFrame(left, border_colour=C["neon_green"])
        pwd_card.pack(fill="x", pady=(0, 10))
        tk.Label(pwd_card, text="🔑  PASSWORD", font=("Arial", 11, "bold"),
                 bg=C["bg_card"], fg=C["neon_green"]).pack(anchor="w", padx=15, pady=(8, 4))
        tk.Label(pwd_card, text="DECRYPTION PASSWORD (or time-locked token)",
                 font=("Arial", 9), bg=C["bg_card"], fg=C["text_dim"]).pack(anchor="w", padx=15)
        self._pwd_entry = DarkEntry(pwd_card, placeholder="password / token", width=35)
        self._pwd_entry.pack(padx=15, pady=(2, 3))

        # Token validator
        self._token_status = tk.Label(pwd_card, text="", font=("Arial", 9),
                                      bg=C["bg_card"], fg=C["text_dim"])
        self._token_status.pack(padx=15, pady=(0, 3))
        self._pwd_entry.bind_key("<KeyRelease>", self._check_token)

        # OTD warning
        self._otd_warning = tk.Label(left, text="", font=("Arial", 10, "bold"),
                                     bg=C["bg_deep"], fg=C["neon_pink"])
        self._otd_warning.pack(pady=(2, 3))

        # Secure delete decrypted after view?
        # FIX: Pass self as master to BooleanVar
        self._del_after_var = tk.BooleanVar(master=self, value=False)
        del_row = tk.Frame(left, bg=C["bg_deep"])
        del_row.pack(fill="x", pady=(0, 3))
        tk.Checkbutton(del_row, variable=self._del_after_var, text="",
                       bg=C["bg_deep"], activebackground=C["bg_deep"],
                       fg=C["neon_orange"], selectcolor=C["bg_input"],
                       ).pack(side="left")
        tk.Label(del_row, text="🗑️ Secure-delete decrypted file after viewing",
                 font=("Arial", 10), bg=C["bg_deep"], fg=C["neon_orange"]).pack(side="left")

        # Status + progress
        self._status = tk.Label(left, text="", font=("Arial", 10),
                                bg=C["bg_deep"], fg=C["danger"])
        self._status.pack(pady=(4, 4))
        self._progress = NeonProgressBar(left, width=90, colour=C["neon_cyan"])
        self._progress.pack(pady=(0, 3))
        self._progress_label = tk.Label(left, text="", font=("Arial", 9),
                                        bg=C["bg_deep"], fg=C["text_dim"])
        self._progress_label.pack()

        self._decrypt_btn = NeonButton(left, text="⚡  DECRYPT FILE", colour=C["neon_green"],
                   command=self._start_decrypt)
        self._decrypt_btn.pack(pady=(6, 0), ipadx=20, ipady=6)

        # ── RIGHT: live viz ───────────────────────────────────────────────
        right = tk.Frame(self, bg=C["bg_deep"])
        right.pack(side="right", fill="both", expand=True, padx=(0, 12), pady=15)

        viz_card = CardFrame(right, border_colour=C["border_glow"])
        viz_card.pack(fill="both", expand=True)
        tk.Label(viz_card, text="📡  LIVE DECRYPTION VISUALIZATION",
                 font=("Arial", 12, "bold"),
                 bg=C["bg_card"], fg=C["text_white"]).pack(pady=(8, 5), padx=15)

        # 4-stage row
        stages_frame = tk.Frame(viz_card, bg=C["bg_card"])
        stages_frame.pack(fill="x", padx=15, pady=(0, 5))
        self._stage_labels = {}
        self._stage_bars   = {}
        stages = [
            ("KEY DERIVATION", C["stage_kdf"], "Scrypt  n=2¹⁵"),
            ("HEADER PARSE",   C["stage_pad"], "Read salt + IV"),
            ("DECRYPTION",     C["stage_enc"], "AES-256-CBC"),
            ("OUTPUT",         C["stage_out"], "Write plain file"),
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
            self._stage_bars[i]   = (bar_bg, bar_fill)

        tk.Frame(viz_card, bg=C["border"], height=1).pack(fill="x", padx=15, pady=19)
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
        self._steg_card.pack_forget()
        self._pwd_entry.set("")
        self._token_status.configure(text="")
        self._otd_warning.configure(text="")
        self._del_after_var.set(False)
        self._status.configure(text="")
        self._progress.set(0.0)
        self._progress_label.configure(text="")
        self._reset_viz()
        self._decrypt_btn.configure(state="normal", bg=self._decrypt_btn._dark)
        self._is_processing = False
        
        # Stop polling if active
        if self._poll_job:
            self.after_cancel(self._poll_job)
            self._poll_job = None

    # ══════════════════════════════════════════════════════════════════════
    # FILE / TOKEN
    # ══════════════════════════════════════════════════════════════════════
    def _browse_file(self):
        import tkinter.filedialog as fd
        path = fd.askopenfilename(title="Select encrypted file",
                                  filetypes=[("All files", "*.*"), ("Encrypted files", "*.enc")])
        if path:
            self._selected_file = path
            self._file_label.configure(text=os.path.basename(path), fg=C["neon_cyan"])

            # Try read steganographic metadata
            meta = read_steg_metadata(path)
            if meta and "owner" in meta:
                import time as _t
                ts = meta.get("ts", 19)
                when = _t.strftime("%Y-%m-%d %H:%M", _t.localtime(ts)) if ts else "unknown"
                txt = f"Owner: {meta['owner']}  (Encrypted: {when})"
                self._steg_label.configure(text=txt, fg=C["neon_violet"])
                self._steg_card.pack(fill="x", pady=(0, 10), after=self._file_label.master.master)
            else:
                self._steg_card.pack_forget()

    def _check_token(self, _e=None):
        val = self._pwd_entry.get().strip()
        if "." in val and len(val) > 50:
            try:
                ok, _pwd, err = validate_time_locked_password(val)
                if ok:
                    self._token_status.configure(text="✔ Valid time-locked token", fg=C["success"])
                else:
                    self._token_status.configure(text=f"⚠ {err}", fg=C["danger"])
            except Exception:
                self._token_status.configure(text="⚠ Invalid token format", fg=C["danger"])
        else:
            self._token_status.configure(text="")

    # ══════════════════════════════════════════════════════════════════════
    # DECRYPT WORKFLOW (THREAD-SAFE)
    # ══════════════════════════════════════════════════════════════════════
    def _start_decrypt(self):
        if self._is_processing:
            return  # Already processing
            
        if not self._selected_file or not os.path.exists(self._selected_file):
            self._status.configure(text="⚠ Select an encrypted file.", fg=C["danger"])
            return
        pwd = self._pwd_entry.get().strip()
        if not pwd:
            self._status.configure(text="⚠ Enter password or token.", fg=C["danger"])
            return

        # If time-locked token, extract base password
        if "." in pwd and len(pwd) > 50:
            try:
                ok, base_pwd, err = validate_time_locked_password(pwd)
                if not ok:
                    self._status.configure(text=f"⚠ Token error: {err}", fg=C["danger"])
                    return
                pwd = base_pwd
            except Exception as e:
                self._status.configure(text=f"⚠ Token error: {str(e)}", fg=C["danger"])
                return

        self._status.configure(text="", fg=C["danger"])
        self._reset_viz()
        self._is_processing = True
        self._decrypt_btn.configure(state="disabled", bg=C["btn_disabled"], cursor="watch")
        
        # Start UI polling
        self._start_ui_polling()
        
        # Start worker thread
        t = threading.Thread(target=self._run_decrypt, args=(pwd,), daemon=True)
        t.start()

    def _run_decrypt(self, password: str):
        """
        Worker thread - performs decryption.
        
        CRITICAL FIX: This method NEVER calls Tkinter directly.
        All UI updates are sent as messages to the queue for the main thread to process.
        
        Why the original crashed:
        - Background thread called self.after() directly
        - self.after() is NOT thread-safe - it requires main thread execution
        - widget.configure() from background threads causes "main thread not in main loop"
        - Even with after(0, ...), the thread still attempts to schedule on wrong thread
        
        Correct approach:
        - Worker emits events: ("stage", idx, msg), ("progress", frac), ("complete", ...)
        - Main thread polls queue using root.after() and updates UI
        - Zero direct Tkinter calls from this thread
        """
        src = self._selected_file

        try:
            # Stage 0: Key derivation
            self.ui_queue.put(("stage", 0, "Deriving key …"))
            time.sleep(0.5)

            # Stage 1: Header parse
            self.ui_queue.put(("stage", 1, "Parsing file header …"))
            time.sleep(0.3)

            # Stage 2: Decryption
            self.ui_queue.put(("stage", 2, "Decrypting …"))

            # Thread-safe progress callback - NO Tkinter calls
            def _progress(frac):
                self.ui_queue.put(("progress", frac))

            # Perform actual decryption
            # Perform actual decryption (in-place: replaces encrypted file)
            # Determine output path: remove .enc extension or use original name
            if src.endswith(".enc"):
                output_path = src[:-4]  # Remove .enc extension
            else:
                output_path = src  # Use same path (will overwrite)

            ok, out_path, err, was_otd = decrypt_file(src, password, 
                                                    progress_cb=_progress, 
                                                    output_path=output_path)

            # If successful, delete the encrypted file (clean up)
            if ok and os.path.exists(src) and output_path != src:
                try:
                    os.remove(src)  # Delete the .enc file
                except Exception:
                    pass  # Ignore cleanup errors

            # Stage 3: Output
            self.ui_queue.put(("stage", 3, "Writing output …"))
            time.sleep(0.3)

            # Send completion event to main thread
            if ok:
                self.app.history.add("DECRYPT", os.path.basename(src),
                                     status="Success", user=self.app.session.username or "",
                                     extra={"otd": was_otd, "output": out_path})
                self.ui_queue.put(("complete", True, out_path, was_otd))
            else:
                self.app.history.add("DECRYPT", os.path.basename(src),
                                     status="Failed", user=self.app.session.username or "")
                self.ui_queue.put(("complete", False, err, None))
                
        except Exception as e:
            self.ui_queue.put(("complete", False, f"Unexpected error: {str(e)}", None))
        finally:
            self._is_processing = False
            self.ui_queue.put(("enable_button",))

    def _start_ui_polling(self):
        """Start polling the queue for UI updates - runs on main thread"""
        self._poll_ui_queue()

    def _poll_ui_queue(self):
        """
        Main thread dispatcher - polls queue and updates UI.
        
        This method runs on the main thread via after() scheduling.
        All Tkinter calls are safe here.
        """
        try:
            # Process all pending messages in queue
            while True:
                try:
                    msg = self.ui_queue.get_nowait()
                    self._handle_ui_message(msg)
                except queue.Empty:
                    break
            
            # Schedule next poll (50ms intervals for smooth updates)
            self._poll_job = self.after(50, self._poll_ui_queue)
            
        except tk.TclError:
            # Widget destroyed, stop polling
            self._poll_job = None

    def _handle_ui_message(self, msg):
        """
        Handle messages from worker thread - runs on main thread.
        
        All Tkinter calls are safe here because this method is only called
        from _poll_ui_queue, which runs on the main thread.
        """
        msg_type = msg[0]
        
        if msg_type == "stage":
            # Animate a decryption stage
            idx = msg[1]
            stage_msg = msg[2]
            self._animate_stage(idx, stage_msg)
        
        elif msg_type == "progress":
            # Update progress bar
            frac = msg[1]
            self._update_progress(frac)
        
        elif msg_type == "complete":
            # Decryption finished
            success = msg[1]
            result = msg[2]
            was_otd = msg[3]
            
            # Stop polling
            if self._poll_job:
                self.after_cancel(self._poll_job)
                self._poll_job = None
            
            # Update UI based on result
            if success:
                self._finish_ok(result, was_otd)
            else:
                self._finish_fail(result)
        
        elif msg_type == "enable_button":
            # Re-enable decrypt button
            self._decrypt_btn.configure(
                state="normal", 
                bg=self._decrypt_btn._dark, 
                cursor="hand2"
            )

    def _finish_ok(self, out_path: str, was_otd: bool):
        """
        Handle successful decryption - called on main thread only.
        """
        self._progress.set(1.0)
        self._progress_label.configure(text="100% – Complete")
        self._status.configure(text=f"✔ Decrypted → {os.path.basename(out_path)}", fg=C["success"])
        self._byte_stream.print("\n  ✔ DECRYPTION COMPLETE", tag="success")

        if was_otd:
            self._otd_warning.configure(
                text="⚡ ONE-TIME DECRYPT: file will be re-encrypted automatically.",
                fg=C["neon_pink"]
            )
            self._byte_stream.print("  ⚡ OTD – Re-encrypting original …", tag="violet")
            # Re-encrypt the decrypted file back, then secure-delete the plaintext
            # (In real use, show the file content first; here we just note it)
            self.app.after(3000, lambda: self._otd_reencrypt(out_path))
        else:
            if self._del_after_var.get():
                try:
                    secure_delete(out_path)
                    self.app.history.add("SECURE_DELETE", os.path.basename(out_path),
                                         status="Success", user=self.app.session.username or "")
                    self._byte_stream.print("  🗑️ Plaintext securely deleted.", tag="orange")
                except Exception as e:
                    self._byte_stream.print(f"  ⚠ Delete failed: {str(e)}", tag="danger")

    def _otd_reencrypt(self, plain_path: str):
        """Re-encrypt after OTD view, then secure-delete the plaintext."""
        try:
            # Use a generic password for the re-encrypt (locks it back)
            import secrets as _s
            tmp_pwd = _s.token_hex(16)
            ok, _, _ = encrypt_file(plain_path, tmp_pwd, one_time_decrypt=True)
            if ok:
                secure_delete(plain_path)
                self._byte_stream.print("  ✔ OTD: file re-encrypted & plaintext wiped.", tag="success")
            else:
                self._byte_stream.print("  ⚠ OTD re-encrypt failed.", tag="danger")
        except Exception as e:
            self._byte_stream.print(f"  ⚠ OTD re-encrypt error: {str(e)}", tag="danger")

    def _finish_fail(self, err: str):
        """
        Handle decryption failure - called on main thread only.
        """
        self._status.configure(text=f"✘ {err}", fg=C["danger"])
        self._byte_stream.print(f"\n  ✘ FAILED: {err}", tag="danger")

    # ══════════════════════════════════════════════════════════════════════
    # VIZ (MAIN THREAD ONLY)
    # ══════════════════════════════════════════════════════════════════════
    def _reset_viz(self):
        """Reset visualization - safe to call from main thread"""
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
        """
        Animate a decryption stage - safe to call from main thread.
        
        This method is only called from _handle_ui_message, which runs
        on the main thread, so all Tkinter operations are safe.
        """
        circle, lbl, sub, colour = self._stage_labels[idx]
        circle.configure(fg=colour)
        lbl.configure(fg=colour)
        sub.configure(fg=colour)
        _, bar_fill = self._stage_bars[idx]

        # Animate progress bar
        def _fill(pct=0):
            if pct <= 100:
                bar_fill.configure(width=int(120 * pct / 100))
                self.after(25, lambda: _fill(pct + 12))
        _fill()

        # Print stage info
        tags  = ["violet", "cyan", "green", "orange"]
        names = ["▶ KEY DERIVATION", "▶ HEADER PARSE", "▶ DECRYPTION", "▶ OUTPUT"]
        self._print_bytes(names[idx], msg, tags[idx])

    def _print_bytes(self, stage_name, msg, tag):
        """Print stage information - safe to call from main thread"""
        self._byte_stream.print(f"\n  {stage_name}", tag=tag)
        self._byte_stream.print(f"  {msg}", tag="dim")
        for _ in range(2):
            line = "  " + " ".join(f"{random.randint(0,255):02x}" for _ in range(24))
            self._byte_stream.print(line, tag=tag)

    def _update_progress(self, frac):
        """Update progress bar - safe to call from main thread"""
        self._progress.set(frac)
        self._progress_label.configure(text=f"{int(frac*100)}%")