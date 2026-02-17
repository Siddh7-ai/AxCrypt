import os, tkinter as tk, threading, queue, tempfile, shutil
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
        
        # Thread-safe queue for worker -> main thread communication
        self.ui_queue = queue.Queue()
        self._poll_job = None
        
        self._build_ui()

    def _build_ui(self):
        # TASK 1: Wrap in ScrollableFrame for long content
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        container = scroll.scrollable_frame

        # Back button (top-left)
        back_frame = tk.Frame(container, bg=C["bg_deep"])
        back_frame.pack(fill="x", padx=15, pady=10)
        BackButton(back_frame, command=lambda: self.app._switch_tab("DASHBOARD")).pack(side="left")
        

        # Left column: controls
        left = tk.Frame(container, bg=C["bg_deep"])
        left.pack(side="left", fill="y", padx=(12, 5), pady=15)

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
        self._selected_file = ""

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

        # Options
        opt_card = CardFrame(left, border_colour=C["neon_violet"])
        opt_card.pack(fill="x", pady=(0, 10))
        tk.Label(opt_card, text="⚙️  OPTIONS", font=("Arial", 11, "bold"),
                bg=C["bg_card"], fg=C["neon_violet"]).pack(anchor="w", padx=15, pady=(8, 5))

        # FIX: Pass self as master to BooleanVar
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

        # TASK 6: Enhanced button with state management
        self._encrypt_btn = NeonButton(left, text="⚡  ENCRYPT FILE", colour=C["neon_green"],
                                       command=self._start_encrypt)
        self._encrypt_btn.pack(pady=(6, 0), ipadx=20, ipady=6)

        # Right: visualization (simplified for space)
        right = tk.Frame(container, bg=C["bg_deep"])
        right.pack(side="right", fill="both", expand=True, padx=(0, 12), pady=15)
        viz_card = CardFrame(right, border_colour=C["border_glow"])
        viz_card.pack(fill="both", expand=True)
        tk.Label(viz_card, text="📡  ENCRYPTION VISUALIZATION",
                font=("Arial", 12, "bold"),
                bg=C["bg_card"], fg=C["text_white"]).pack(pady=(8, 5))
        self._viz_log = TerminalText(viz_card)
        self._viz_log.pack(fill="both", expand=True, padx=30, pady=(2, 8))

    def show(self):
        self.pack(fill="both", expand=True)

    def hide(self):
        self.pack_forget()

    def on_show(self):
        pass

    # TASK 2: State reset method
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
        self._viz_log.clear()
        self._encrypt_btn.configure(state="normal", bg=self._encrypt_btn._dark)
        
        # Stop polling if active
        if self._poll_job:
            self.after_cancel(self._poll_job)
            self._poll_job = None

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

    # TASK 3: Encryption with mode choice
    def _start_encrypt(self):
        # Validate
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

        # TASK 3: Show mode selection dialog
        dialog = EncryptModeDialog(self)
        mode = dialog.show()
        
        if mode is None:
            return  # Cancelled
        
        create_new = (mode == "new")

        # TASK 6: Disable button during operation
        self._encrypt_btn.configure(state="disabled", bg=C["btn_disabled"], cursor="watch")
        self._status.configure(text="Encrypting...", fg=C["info"])
        self._viz_log.clear()
        self._viz_log.print("🔐 ENCRYPTION STARTED", tag="info")
        self._viz_log.print(f"File: {os.path.basename(self._selected_file)}", tag="dim")
        self._viz_log.print(f"Mode: {'Create new file' if create_new else 'Replace current file'}", tag="dim")
        
        otd   = self._otd_var.get()
        owner = self._owner_entry.get().strip()
        src   = self._selected_file

        if otd:
            self._viz_log.print("⚠️  One-Time-Decrypt enabled", tag="warning")

        # Start polling queue
        self._start_ui_polling()

        # Run in thread
        t = threading.Thread(target=self._run_encrypt, args=(pwd, create_new, otd, owner, src), daemon=True)
        t.start()

    def _run_encrypt(self, pwd, create_new, otd, owner, src):
        """
        Worker thread - performs encryption.
        NEVER calls Tkinter directly - only puts messages in queue.
        """
        
        # Thread-safe progress callback - NO Tkinter calls
        def _progress(frac):
            # Put progress update in queue for main thread to process
            self.ui_queue.put(("progress", frac))
        
        try:
            if create_new:
                # MODE: Create new encrypted file (original stays untouched)
                ok, out_path, err = encrypt_file(src, pwd, one_time_decrypt=otd,
                                                owner_info=owner, progress_cb=_progress)
                
                if ok:
                    self.app.history.add("ENCRYPT", os.path.basename(src), status="Success",
                                        user=self.app.session.username or "",
                                        extra={"otd": otd, "output": out_path})
                    
                    # Send success message with new file path
                    self.ui_queue.put(("complete", True, out_path))
                else:
                    self.app.history.add("ENCRYPT", os.path.basename(src), status="Failed",
                                        user=self.app.session.username or "")
                    
                    # Send error message to main thread
                    self.ui_queue.put(("complete", False, err))
            else:
                # MODE: Replace original file content (in-place encryption)
                # Uses the new encrypt_file_replace function with atomic file replacement
                ok, out_path, err = encrypt_file_replace(src, pwd, one_time_decrypt=otd,
                                                         owner_info=owner, progress_cb=_progress)
                
                if ok:
                    # Log the in-place encryption
                    self.app.history.add("ENCRYPT_REPLACE", os.path.basename(src),
                                        status="Success", user=self.app.session.username or "",
                                        extra={"otd": otd, "mode": "in-place"})
                    
                    # Report success with original path (file still exists there)
                    self.ui_queue.put(("complete", True, out_path))
                else:
                    self.app.history.add("ENCRYPT_REPLACE", os.path.basename(src),
                                        status="Failed", user=self.app.session.username or "")
                    
                    # Send error message
                    self.ui_queue.put(("complete", False, err))
        
        except Exception as e:
            # Handle unexpected errors
            self.ui_queue.put(("complete", False, str(e)))

    def _start_ui_polling(self):
        """Start polling the queue for UI updates - runs on main thread"""
        self._poll_ui_queue()

    def _poll_ui_queue(self):
        """
        Main thread dispatcher - polls queue and updates UI.
        This runs periodically on the main thread via after().
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
        All Tkinter calls are safe here.
        """
        msg_type = msg[0]
        
        if msg_type == "progress":
            # Update progress bar
            frac = msg[1]
            self._progress.set(frac)
            self._progress_label.configure(text=f"{int(frac*100)}%")
        
        elif msg_type == "complete":
            # Encryption finished
            success = msg[1]
            result = msg[2]
            
            # Stop polling
            if self._poll_job:
                self.after_cancel(self._poll_job)
                self._poll_job = None
            
            # Update UI
            self._finish(success, result)

    def _finish(self, success, msg):
        """
        Finalize encryption - called on main thread only.
        Re-enable button and show results.
        """
        # Re-enable button
        self._encrypt_btn.configure(state="normal", bg=self._encrypt_btn._dark, cursor="hand2")
        
        if success:
            self._progress.set(1.0)
            self._progress_label.configure(text="100% – Complete")
            self._status.configure(text=f"✔ Encrypted → {os.path.basename(msg)}", fg=C["success"])
            self._viz_log.print("\n✔ ENCRYPTION COMPLETE", tag="success")
            self._viz_log.print(f"File: {msg}", tag="dim")
        else:
            self._status.configure(text=f"✘ Error: {msg}", fg=C["danger"])
            self._viz_log.print(f"\n✘ FAILED: {msg}", tag="danger")