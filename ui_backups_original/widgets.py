"""
axcrypt/ui/widgets.py
─────────────────────
Reusable cyberpunk-themed Tkinter widgets with professional polish.

COMPONENTS:
  NeonButton        – glowing accent button with hover effects
  DarkEntry         – styled text input with placeholder support
  CardFrame         – raised dark panel with neon border (glassmorphism)
  NeonProgressBar   – animated progress bar
  StrengthBar       – live password-strength indicator
  TerminalText      – read-only log widget with typing animation
  PulseLabel        – label that pulses colour for status indication
"""

import tkinter as tk
from core.config import C


# ══════════════════════════════════════════════════════════════════════════════
class NeonButton(tk.Button):
    """Button with neon colour that brightens on hover - enterprise-grade styling."""

    def __init__(self, master, *, colour=None, text="", command=None, width=None, **kw):
        colour = colour or C["neon_cyan"]
        # Darken colour for default state
        dark = self._darken(colour)
        
        super().__init__(
            master,
            text=text,
            font=("Arial", 25, "bold"),
            bg=dark,
            fg="#ffffff",
            activebackground=colour,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=command,
            width=width,
            **kw,
        )
        
        if width:
            self.configure(width=width)
        
        # Enhanced hover effects
        self.bind("<Enter>", lambda _: self.configure(bg=colour))
        self.bind("<Leave>", lambda _: self.configure(bg=dark))
        
        self._colour = colour
        self._dark = dark

    @staticmethod
    def _darken(hex_colour: str) -> str:
        """Return a darker shade (multiply each channel by 0.55)."""
        h = hex_colour.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        return f"#{int(r*0.55):02x}{int(g*0.55):02x}{int(b*0.55):02x}"


# ══════════════════════════════════════════════════════════════════════════════
class DarkEntry(tk.Frame):
    """Styled entry with placeholder support and professional aesthetics."""

    def __init__(self, master, *, placeholder="", show="", width=48, **kw):
        super().__init__(master, bg=C["border"], padx=3, pady=3)
        
        self.entry = tk.Entry(
            self,
            font=("Arial", 27),
            bg=C["bg_input"],
            fg=C["text_hi"],
            insertbackground=C["neon_cyan"],
            relief="flat",
            bd=4,
            highlightthickness=1,
            highlightcolor=C["neon_cyan"],
            highlightbackground=C["border"],
            show=show,
            width=width,
        )
        self.entry.pack(fill="both", expand=True)
        
        self._placeholder = placeholder
        self._show = show
        
        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.configure(fg=C["text_dim"])
            self.entry.bind("<FocusIn>", self._on_focus_in)
            self.entry.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _e=None):
        """Clear placeholder on focus."""
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, "end")
            self.entry.configure(fg=C["text_hi"])

    def _on_focus_out(self, _e=None):
        """Restore placeholder if empty."""
        if not self.entry.get():
            self.entry.insert(0, self._placeholder)
            self.entry.configure(fg=C["text_dim"])

    def get(self) -> str:
        """Get entry value (empty string if placeholder)."""
        val = self.entry.get()
        return "" if val == self._placeholder else val

    def set(self, value: str):
        """Set entry value."""
        self.entry.delete(0, "end")
        if value:
            self.entry.insert(0, value)
            self.entry.configure(fg=C["text_hi"])
        else:
            self._on_focus_out()

    def bind_key(self, seq, func):
        """Bind key event to entry."""
        self.entry.bind(seq, func)

    def focus(self):
        """Set focus to entry."""
        self.entry.focus_set()


# ══════════════════════════════════════════════════════════════════════════════
class CardFrame(tk.Frame):
    """A raised dark-themed card with optional glowing border - glassmorphism effect."""

    def __init__(self, master, *, border_colour=None, **kw):
        super().__init__(
            master,
            bg=C["bg_card"],
            highlightthickness=1,
            highlightbackground=border_colour or C["border"],
            highlightcolor=border_colour or C["border"],
            bd=0,
            **kw,
        )


# ══════════════════════════════════════════════════════════════════════════════
class NeonProgressBar(tk.Frame):
    """Animated neon progress bar with smooth transitions. Call .set(fraction 0-1)."""

    def __init__(self, master, *, width=640, height=9, colour=None, **kw):
        super().__init__(master, bg=C["bg_input"], width=width, height=height, **kw)
        self.pack_propagate(False)
        
        self._colour = colour or C["neon_cyan"]
        self._bar = tk.Frame(self, bg=self._colour, width=0, height=height)
        self._bar.pack(side="left", fill="y")
        
        self._width = width
        self._value = 0.0

    def set(self, fraction: float):
        """Set progress bar fill (0.0 to 1.0)."""
        fraction = max(0.0, min(1.0, fraction))
        self._value = fraction
        px = int(self._width * fraction)
        self._bar.configure(width=max(px, 0))

    def get(self) -> float:
        """Get current progress value."""
        return self._value


# ══════════════════════════════════════════════════════════════════════════════
class StrengthBar(tk.Frame):
    """Visual password-strength indicator: bar + label + difficulty tier."""

    def __init__(self, master, **kw):
        super().__init__(master, bg=C["bg_deep"], **kw)
        
        # Top row: label and tier
        top = tk.Frame(self, bg=C["bg_deep"])
        top.pack(fill="x")
        
        self._label = tk.Label(
            top,
            text="Password Strength",
            font=("Arial", 22),
            bg=C["bg_deep"],
            fg=C["text_dim"],
        )
        self._label.pack(side="left")
        
        self._tier_label = tk.Label(
            top,
            text="",
            font=("Arial", 22, "bold"),
            bg=C["bg_deep"],
            fg=C["text_dim"],
        )
        self._tier_label.pack(side="right")

        # Bar background
        bar_bg = tk.Frame(self, bg=C["bg_input"], height=12)
        bar_bg.pack(fill="x", pady=(4, 0))
        bar_bg.pack_propagate(False)
        
        self._fill = tk.Frame(bar_bg, bg=C["danger"], width=0)
        self._fill.pack(side="left", fill="y")
        
        self._bar_bg = bar_bg

    def update(self, score: int):
        """Update strength display (score 0-100)."""
        from core.crypto import strength_label
        
        label, colour = strength_label(score)

        self._fill.configure(bg=colour)
        self._tier_label.configure(text=label, fg=colour)
        
        # Defer width update after geometry is known
        self._bar_bg.update_idletasks()
        total_w = self._bar_bg.winfo_width() or 300
        px = int(total_w * score / 100)
        self._fill.configure(width=max(px, 0))


# ══════════════════════════════════════════════════════════════════════════════
class TerminalText(tk.Frame):
    """Scrollable read-only text widget styled as a terminal with typing effect.

    METHODS:
        .print(text, tag=None)              – append a line
        .clear()                            – empty the terminal
        .animate_print(text, delay_ms=18)   – character-by-character typing
    """

    TAGS = {
        "default": (C["text_hi"], C["bg_deep"]),
        "dim": (C["text_dim"], C["bg_deep"]),
        "green": (C["neon_green"], C["bg_deep"]),
        "cyan": (C["neon_cyan"], C["bg_deep"]),
        "violet": (C["neon_violet"], C["bg_deep"]),
        "orange": (C["neon_orange"], C["bg_deep"]),
        "danger": (C["danger"], C["bg_deep"]),
        "success": (C["success"], C["bg_deep"]),
    }

    def __init__(self, master, **kw):
        super().__init__(master, bg=C["bg_deep"], **kw)
        
        self.text = tk.Text(
            self,
            font=("Arial", 25),
            bg=C["bg_deep"],
            fg=C["text_hi"],
            insertbackground=C["neon_cyan"],
            relief="flat",
            bd=8,
            wrap="word",
            state="disabled",
            spacing1=2,
            spacing3=2,
        )
        
        scroll = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.text.yview,
            bg=C["bg_panel"],
            troughcolor=C["bg_deep"],
            highlightthickness=0,
        )
        
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Register colour tags
        for name, (fg, bg) in self.TAGS.items():
            self.text.tag_configure(name, foreground=fg, background=bg)

    def print(self, line: str, tag: str = "default"):
        """Print a line to the terminal."""
        self.text.configure(state="normal")
        self.text.insert("end", line + "\n", tag)
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self):
        """Clear all terminal text."""
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.mark_set("insert", "1.0")
        self.text.configure(state="disabled")


    def animate_print(self, line: str, delay_ms: int = 18, tag: str = "default"):
        """Character-by-character typing animation."""
        self.text.configure(state="normal")
        
        idx = 0

        def _tick():
            nonlocal idx
            if idx < len(line):
                self.text.insert("end", line[idx], tag)
                self.text.see("end")
                idx += 1
                self.text.after(delay_ms, _tick)
            else:
                self.text.insert("end", "\n")
                self.text.configure(state="disabled")

        _tick()

# ══════════════════════════════════════════════════════════════════════════════
class PulseLabel(tk.Label):
    """A label that pulses between two colours - perfect for status indicators."""

    def __init__(self, master, *, colour_a=None, colour_b=None, interval_ms=800, **kw):
        super().__init__(master, **kw)
        
        self._ca = colour_a or C["neon_cyan"]
        self._cb = colour_b or C["text_dim"]
        self._interval = interval_ms
        self._state = False
        self._running = False

    def start(self):
        """Start the pulsing animation."""
        if not self._running:
            self._running = True
            self._tick()

    def stop(self):
        """Stop the pulsing animation."""
        self._running = False

    def _tick(self):
        """Internal pulse tick."""
        if not self._running:
            return
        self._state = not self._state
        self.configure(fg=self._ca if self._state else self._cb)
        self.after(self._interval, self._tick)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 1: SCROLLABLE FRAME FOR ALL LONG PANELS
# ══════════════════════════════════════════════════════════════════════════════

class ScrollableFrame(tk.Frame):
    """
    Scrollable frame wrapper with mouse wheel support.
    Solves TASK 1 - makes all buttons reachable.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=C["bg_deep"])
        
        # Create canvas + scrollbar
        self.canvas = tk.Canvas(self, bg=C["bg_deep"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                     bg=C["bg_panel"], troughcolor=C["bg_deep"])
        
        # Scrollable container frame
        self.scrollable_frame = tk.Frame(self.canvas, bg=C["bg_deep"])
        
        # Update scroll region when content changes
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind mouse wheel (cross-platform)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows/Mac
        self.canvas.bind("<Button-4>", self._on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)    # Linux scroll down
        
        # Pack elements
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind canvas width to scrollable frame
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _on_canvas_configure(self, event):
        # Make scrollable frame fill canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Cross-platform mouse wheel scrolling"""
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:  # Windows/Mac
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"  # Prevent event propagation


# ══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION MODE DIALOG - COMPLETELY REWRITTEN WITH FORCED RENDERING
# ══════════════════════════════════════════════════════════════════════════════

class EncryptModeDialog:
    """
    Modal dialog for choosing encryption mode.
    COMPLETELY REWRITTEN - Forces content visibility.
    """
    def __init__(self, parent):
        self.result = None
        
        # Get root window
        root = parent.winfo_toplevel()
        
        # Create dialog
        self.dialog = tk.Toplevel(root)
        self.dialog.title("Encryption Mode")
        self.dialog.configure(bg="#0a0c0f")
        
        # Make modal
        self.dialog.transient(root)
        self.dialog.grab_set()
        self.dialog.focus_set()
        
        # Size and position
        w, h = 650, 680
        self.dialog.geometry(f"{w}x{h}")
        root.update_idletasks()
        px = root.winfo_x()
        py = root.winfo_y()
        pw = root.winfo_width()
        ph = root.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        self.dialog.resizable(False, False)
        
        # Mode variable
        self.mode = tk.StringVar(master=self.dialog, value="new")
        
        # Build UI with forced colors
        self._build_ui()
        
        # Force rendering
        self.dialog.update()
        self.dialog.lift()
        self.dialog.focus_force()
    
    def _build_ui(self):
        """Build dialog UI with explicit colors"""
        
        # Header
        header = tk.Label(
            self.dialog,
            text="🔐  CHOOSE ENCRYPTION MODE",
            font=("Arial", 51, "bold"),
            bg="#0a0c0f",
            fg="#00f0ff"
        )
        header.pack(pady=(30, 10))
        
        subtitle = tk.Label(
            self.dialog,
            text="How do you want to encrypt the file?",
            font=("Arial", 27),
            bg="#0a0c0f",
            fg="#a0aec0"
        )
        subtitle.pack(pady=(0, 30))
        
        # Container
        container = tk.Frame(self.dialog, bg="#0a0c0f")
        container.pack(fill="x", padx=64, pady=(0, 10))
        
        # OPTION 1 - CREATE NEW
        opt1_border = tk.Frame(container, bg="#39ff14", bd=0)
        opt1_border.pack(fill="x", pady=(0, 15))
        
        opt1 = tk.Frame(opt1_border, bg="#1f2530", bd=0)
        opt1.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Radio + Title
        radio_row1 = tk.Frame(opt1, bg="#1f2530")
        radio_row1.pack(fill="x", padx=40, pady=(15, 8))
        
        rb1 = tk.Radiobutton(
            radio_row1,
            variable=self.mode,
            value="new",
            text="",
            bg="#1f2530",
            fg="#39ff14",
            selectcolor="#0a0c0f",
            activebackground="#1f2530",
            font=("Arial", 30)
        )
        rb1.pack(side="left", padx=(0, 15))
        
        title1 = tk.Label(
            radio_row1,
            text="✓ Create New Encrypted Copy (Recommended)",
            font=("Arial", 32, "bold"),
            bg="#1f2530",
            fg="#39ff14"
        )
        title1.pack(side="left")
        
        # Descriptions
        desc_container1 = tk.Frame(opt1, bg="#1f2530")
        desc_container1.pack(fill="x", padx=(70, 25), pady=(5, 15))
        
        for text in [
            "• Original file remains safe and untouched",
            "• Creates: filename.ext.enc (separate file)",
            "• Best for keeping backups"
        ]:
            lbl = tk.Label(
                desc_container1,
                text=text,
                font=("Arial", 27),
                bg="#1f2530",
                fg="#e2e8f0",
                anchor="w"
            )
            lbl.pack(fill="x", pady=4)
        
        # OPTION 2 - REPLACE ORIGINAL
        opt2_border = tk.Frame(container, bg="#ff9f1c", bd=0)
        opt2_border.pack(fill="x", pady=(0, 0))
        
        opt2 = tk.Frame(opt2_border, bg="#1f2530", bd=0)
        opt2.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Radio + Title
        radio_row2 = tk.Frame(opt2, bg="#1f2530")
        radio_row2.pack(fill="x", padx=40, pady=(20, 10))
        
        rb2 = tk.Radiobutton(
            radio_row2,
            variable=self.mode,
            value="replace",
            text="",
            bg="#1f2530",
            fg="#ff9f1c",
            selectcolor="#0a0c0f",
            activebackground="#1f2530",
            font=("Arial", 30)
        )
        rb2.pack(side="left", padx=(0, 15))
        
        title2 = tk.Label(
            radio_row2,
            text="⚠️  Encrypt in Place (Replace Content)",
            font=("Arial", 32, "bold"),
            bg="#1f2530",
            fg="#ff9f1c"
        )
        title2.pack(side="left")
        
        # Descriptions
        desc_container2 = tk.Frame(opt2, bg="#1f2530")
        desc_container2.pack(fill="x", padx=(70, 25), pady=(5, 20))
        
        texts = [
            ("• File stays at same path", "#e2e8f0"),
            ("• Content replaced with encrypted data", "#ff9f1c"),
            ("• Cannot open without decryption first", "#ff2d95")
        ]
        
        for text, color in texts:
            lbl = tk.Label(
                desc_container2,
                text=text,
                font=("Arial", 27),
                bg="#1f2530",
                fg=color,
                anchor="w"
            )
            lbl.pack(fill="x", pady=4)
        
        # Buttons
        btn_container = tk.Frame(self.dialog, bg="#0a0c0f")
        btn_container.pack(pady=(20, 30))
        
        NeonButton(
            btn_container,
            text="CONTINUE",
            colour="#39ff14",
            command=self._ok
        ).pack(side="left", ipadx=64, ipady=19, padx=(0, 15))
        
        NeonButton(
            btn_container,
            text="CANCEL",
            colour="#4a5568",
            command=self._cancel
        ).pack(side="left", ipadx=64, ipady=19)
    
    def _ok(self):
        self.result = self.mode.get()
        self.dialog.destroy()
    
    def _cancel(self):
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return user choice"""
        self.dialog.wait_window()
        return self.result

# ══════════════════════════════════════════════════════════════════════════════
# BACK BUTTON
# ══════════════════════════════════════════════════════════════════════════════

class BackButton(tk.Button):
    """Professional back button - prevents user entrapment"""
    def __init__(self, master, *, command=None, **kw):
        super().__init__(
            master,
            text="←  BACK",
            font=("Arial", 25, "bold"),
            bg=C["bg_card"],
            fg=C["text_mid"],
            activebackground=C["bg_hover"],
            activeforeground=C["neon_cyan"],
            relief="flat",
            bd=0,
            cursor="hand2",
            command=command,
            padx=25,
            pady=12,
            **kw
        )
        self.bind("<Enter>", lambda _: self.configure(bg=C["bg_hover"], fg=C["neon_cyan"]))
        self.bind("<Leave>", lambda _: self.configure(bg=C["bg_card"], fg=C["text_mid"]))