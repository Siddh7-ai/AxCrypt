"""
AxCrypt Enhanced - Main Application Window (CustomTkinter Version)
═══════════════════════════════════════════════════════════════════

CUSTOMTKINTER TRANSFORMATION:
✓ Modern CustomTkinter widgets throughout
✓ Same design and functionality as original
✓ Enhanced visual consistency
✓ Better cross-platform appearance
✓ Main-thread-safe auto-lock using event loop
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image
import os

from core.config import APP_NAME, APP_TAGLINE, APP_VERSION, WIN_W, WIN_H, MIN_W, MIN_H, C, LOGO_PATH, FONTS
from core.session import SessionManager
from core.user_manager import UserManager
from core.history import HistoryManager

from ui.auth_panel_glassmorphism import AuthPanelGlassmorphic as AuthPanel
from ui.lock_panel import LockPanel
from ui.dashboard import DashboardPanel
from ui.history_panel import HistoryPanel
from ui.settings_panel import SettingsPanel

# Set CustomTkinter appearance mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AxCryptApp(ctk.CTk):
    """
    Root application window with CustomTkinter:
    - Modern CTk widgets
    - Enhanced typography
    - Smooth panel transitions  
    - Proper state management
    - Logo integration
    - Main-thread-safe auto-lock mechanism
    """

    def __init__(self):
        super().__init__()

        # ═══ Shared State ═══
        self.session = SessionManager()
        self.user_mgr = UserManager()
        self.history = HistoryManager()

        # ═══ Window Configuration ═══
        self.title(APP_NAME)
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.minsize(MIN_W, MIN_H)
        self._fg_color = C["bg_deep"]
        self.configure(fg_color=C["bg_deep"])
        self.resizable(True, True)

        # Set window icon
        self._set_window_icon()

        # ═══ Professional Fonts ═══
        self._setup_fonts()

        # ═══ Layout Layers ═══
        self._build_header()
        
        # Footer navigation bar (persistent)
        self.footer_frame = ctk.CTkFrame(self, fg_color=C["bg_panel"], height=52, corner_radius=0)
        self.footer_frame.pack(side="bottom", fill="x")
        self.footer_frame.pack_propagate(False)
        self._build_footer()
        
        self.content = ctk.CTkFrame(self, fg_color=C["bg_deep"], corner_radius=0)
        self.content.pack(fill="both", expand=True)

        # ═══ Panel Registry ═══
        # Pre-loaded panels
        self.auth_panel = AuthPanel(self)
        self.lock_panel = LockPanel(self)
        self.dashboard_panel = DashboardPanel(self)
        self.history_panel = HistoryPanel(self)
        self.settings_panel = SettingsPanel(self)

        # Lazy-loaded heavy panels (for performance)
        self._encrypt_panel = None
        self._decrypt_panel = None

        self._active_panel = None
        self._active_tab = None

        # ═══ Auto-Lock Polling ═══
        self._auto_lock_job = None
        self._start_auto_lock_polling()

    # ═══════════════════════════════════════════════════════════════
    # INITIALIZATION HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _set_window_icon(self):
        """Set application icon from logo"""
        try:
            if os.path.exists(LOGO_PATH):
                # For CustomTkinter, we need to use tk.PhotoImage or PIL
                from PIL import ImageTk
                logo_img = Image.open(LOGO_PATH)
                logo_img = logo_img.resize((64, 64), Image.Resampling.LANCZOS)
                self.logo_icon = ImageTk.PhotoImage(logo_img)
                self.iconphoto(True, self.logo_icon)
        except Exception:
            pass  # Fallback to system default

    def _setup_fonts(self):
        """Configure professional font stack"""
        try:
            available_fonts = tkfont.families()
            
            if "Segoe UI" in available_fonts:
                primary_family = "Segoe UI"
            elif "Helvetica Neue" in available_fonts:
                primary_family = "Helvetica Neue"
            else:
                primary_family = "Helvetica"

            mono_family = "Consolas" if "Consolas" in available_fonts else "Courier New"

        except Exception:
            primary_family = "Helvetica"
            mono_family = "Courier"

        # Global font tuples (family, size, weight)
        self.font_heading    = (primary_family, 16, "bold")
        self.font_subheading = (primary_family, 13, "bold")
        self.font_body       = (primary_family, 11)
        self.font_body_bold  = (primary_family, 11, "bold")
        self.font_small      = (primary_family, 10)
        self.font_tiny       = (primary_family, 9)
        self.font_mono       = (mono_family,    10)
        self.font_button     = (primary_family, 10, "bold")
        self.font_tab        = (primary_family, 10, "bold")

    # ═══════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════

    def _build_header(self):
        """Build application header with logo and status"""
        hdr = ctk.CTkFrame(self, fg_color=C["bg_panel"], height=60, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Left: Logo + Branding
        logo_frame = ctk.CTkFrame(hdr, fg_color=C["bg_panel"], corner_radius=0)
        logo_frame.pack(side="left", padx=(20, 0))

        # Logo image
        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                self.header_logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(48, 48))
                ctk.CTkLabel(
                    logo_frame, 
                    image=self.header_logo_img,
                    text="",
                    fg_color=C["bg_panel"]
                ).pack(side="left", padx=(0, 10))
        except Exception:
            # Fallback emoji
            ctk.CTkLabel(
                logo_frame,
                text="🛡️",
                font=("Segoe UI", 22),
                fg_color=C["bg_panel"],
                text_color=C["neon_cyan"]
            ).pack(side="left", padx=(0, 8))

        # App name
        ctk.CTkLabel(
            logo_frame,
            text=APP_NAME,
            font=("Segoe UI", 20, "bold"),
            fg_color=C["bg_panel"],
            text_color=C["text_white"]
        ).pack(side="left", padx=(0, 0))

        # Tagline
        ctk.CTkLabel(
            logo_frame,
            text=APP_TAGLINE,
            font=("Segoe UI", 11),
            fg_color=C["bg_panel"],
            text_color=C["text_mid"]
        ).pack(side="left", padx=(12, 0))


        # Right: Version + User
        self.header_right = ctk.CTkFrame(hdr, fg_color=C["bg_panel"], corner_radius=0)
        self.header_right.pack(side="right", padx=(0, 20))

        ctk.CTkLabel(
            self.header_right,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 10),
            fg_color=C["bg_panel"],
            text_color=C["text_mid"]
        ).pack(side="right", padx=(0, 10))


        self.user_label = ctk.CTkLabel(
            self.header_right,
            text="",
            font=("Segoe UI", 12, "bold"),
            fg_color=C["bg_panel"],
            text_color=C["neon_green"]
        )
        self.user_label.pack(side="right", padx=(10, 0))

        # Border
        ctk.CTkFrame(self, fg_color=C["border"], height=1, corner_radius=0).pack(fill="x")

    def _build_footer(self):
        """Build persistent footer navigation bar"""
        # Clear existing widgets
        for w in self.footer_frame.winfo_children():
            w.destroy()
        
        # Add top border separator
        ctk.CTkFrame(self.footer_frame, fg_color=C["border"], height=1, corner_radius=0).pack(side="top", fill="x")
        
        # Define footer tabs
        tabs = [
            ("📊", "DASHBOARD", C["neon_cyan"]),
            ("🔐", "ENCRYPT", C["neon_green"]),
            ("🔓", "DECRYPT", C["neon_cyan"]),
            ("📜", "HISTORY", C["neon_violet"]),
            ("⚙️", "SETTINGS", C["neon_orange"]),
        ]
        
        # Store footer buttons for later updates
        if not hasattr(self, 'footer_buttons'):
            self.footer_buttons = {}
        
        # Create footer tab buttons
        for icon, name, color in tabs:
            btn_frame = ctk.CTkFrame(self.footer_frame, fg_color=C["bg_panel"], corner_radius=0)
            btn_frame.pack(side="left", fill="both", expand=True)
            
            btn = ctk.CTkButton(
                btn_frame,
                text=f"{icon} {name}",
                font=self.font_small,
                fg_color="transparent",
                hover_color=C["bg_card"],
                text_color=C["text_mid"],
                corner_radius=8,
                border_width=0,
                command=lambda n=name: self._switch_tab(n)
            )
            btn.pack(fill="both", expand=True, padx=9, pady=14)
            self.footer_buttons[name] = (btn, color)

    def _update_footer_highlight(self):
        """Update footer button highlights based on active tab"""
        for name, (btn, color) in self.footer_buttons.items():
            if name == self._active_tab:
                btn.configure(fg_color=C["bg_card"], text_color=color)
            else:
                btn.configure(fg_color="transparent", text_color=C["text_mid"])

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════

    _TABS = [
        ("DASHBOARD", "📊"),
        ("ENCRYPT", "🔐"),
        ("DECRYPT", "🔓"),
        ("HISTORY", "📜"),
        ("SETTINGS", "⚙️"),
    ]

    def _build_nav(self):
        """Build top navigation bar (shown after login)"""
        # Clear existing nav
        for w in self.nav_frame.winfo_children():
            w.destroy()

        # Import NeonButton from widgets
        from ui.widgets import NeonButton

        # Action buttons on right
        panic_btn = NeonButton(
            self.nav_frame,
            text="⚡ PANIC",
            colour=C["danger"],
            command=self._panic_lock
        )
        panic_btn.pack(side="right", padx=(10, 18), pady=8, ipadx=10, ipady=4)

        logout_btn = NeonButton(
            self.nav_frame,
            text="LOGOUT",
            colour=C["bg_card"],
            command=self._logout
        )
        logout_btn.pack(side="right", padx=(4, 0), pady=8, ipadx=8, ipady=4)

        # Tab buttons
        self.tab_buttons = {}
        for tab_name, icon in self._TABS:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=f" {icon}  {tab_name} ",
                font=self.font_tab,
                fg_color=C["bg_panel"],
                hover_color=C["bg_card"],
                text_color=C["text_mid"],
                corner_radius=8,
                border_width=0,
                command=lambda t=tab_name: self._switch_tab(t),
            )
            btn.pack(side="left", padx=(3, 3), pady=(5, 5), ipadx=8, ipady=4)
            self.tab_buttons[tab_name] = btn

    # ═══════════════════════════════════════════════════════════════
    # PANEL SWITCHING
    # ═══════════════════════════════════════════════════════════════

    def _switch_tab(self, tab_name: str):
        """Switch to a specific tab with proper state management."""
        self.session.touch()
        self._hide_all_panels()

        self._active_tab = tab_name

        # Get panel (lazy-load encrypt/decrypt for performance)
        panel_map = {
            "DASHBOARD": self.dashboard_panel,
            "HISTORY": self.history_panel,
            "SETTINGS": self.settings_panel,
        }

        if tab_name == "ENCRYPT":
            if self._encrypt_panel is None:
                from ui.encrypt_panel import EncryptPanel
                self._encrypt_panel = EncryptPanel(self)
            panel = self._encrypt_panel

        elif tab_name == "DECRYPT":
            if self._decrypt_panel is None:
                from ui.decrypt_panel import DecryptPanel
                self._decrypt_panel = DecryptPanel(self)
            panel = self._decrypt_panel

        else:
            panel = panel_map[tab_name]

        # Reset panel state before showing
        if hasattr(panel, "reset_state"):
            panel.reset_state()

        # Show panel
        panel.show()
        self._active_panel = panel

        # Call on_show hook if available
        if hasattr(panel, "on_show"):
            panel.on_show()
        
        # Update footer highlight
        self._update_footer_highlight()

    def _hide_all_panels(self):
        """Hide all panels"""
        panels = []
        if hasattr(self, 'auth_panel'):
            panels.append(self.auth_panel)
        if hasattr(self, 'lock_panel'):
            panels.append(self.lock_panel)
        if hasattr(self, 'dashboard_panel'):
            panels.append(self.dashboard_panel)
        if hasattr(self, 'history_panel'):
            panels.append(self.history_panel)
        if hasattr(self, 'settings_panel'):
            panels.append(self.settings_panel)
        
        for p in panels:
            p.hide()

        if hasattr(self, '_encrypt_panel') and self._encrypt_panel:
            self._encrypt_panel.hide()
        if hasattr(self, '_decrypt_panel') and self._decrypt_panel:
            self._decrypt_panel.hide()

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC NAVIGATION METHODS
    # ═══════════════════════════════════════════════════════════════

    def show_auth(self):
        self._hide_all_panels()

        if hasattr(self, "nav_frame"):
            self.nav_frame.pack_forget()

        self.auth_panel.show()


    def show_lock(self):
        self._hide_all_panels()

        if hasattr(self, "nav_frame"):
            self.nav_frame.pack_forget()

        self.lock_panel.show()


    def show_main(self, username: str):
        self.session.login(username)
        self.user_label.configure(text=f"👤 {username}")
        self._hide_all_panels()

        # DO NOT call _build_nav()

        self._switch_tab("DASHBOARD")


    # ═══════════════════════════════════════════════════════════════
    # AUTO-LOCK MECHANISM (MAIN THREAD SAFE)
    # ═══════════════════════════════════════════════════════════════

    def _start_auto_lock_polling(self):
        """Start polling for auto-lock condition using CTk's event loop."""
        self._check_auto_lock()

    def _check_auto_lock(self):
        """Periodic check for auto-lock condition."""
        try:
            if self.session.check_timeout():
                self._do_lock_screen()
            
            elif self.session.is_lock_requested() and not self.session.is_locked():
                self.session.locked = True
                self._do_lock_screen()
            
            # Schedule next check (1 second intervals)
            self._auto_lock_job = self.after(1000, self._check_auto_lock)
            
        except Exception:
            if self._auto_lock_job:
                self.after_cancel(self._auto_lock_job)
                self._auto_lock_job = None

    def _do_lock_screen(self):
        """Execute lock screen transition."""
        self._hide_all_panels()
        self.nav_frame.pack_forget()
        self.user_label.configure(text="")
        self.lock_panel.show()
        self.session.clear_lock_request()

    # ═══════════════════════════════════════════════════════════════
    # PANIC & LOGOUT
    # ═══════════════════════════════════════════════════════════════

    def _panic_lock(self):
        """Emergency panic lock."""
        self.session.panic_lock()

    def _logout(self):
        """Logout and return to auth screen"""
        self.session.logout()
        
        # Clean up heavy panels
        self._encrypt_panel = None
        self._decrypt_panel = None
        
        self.show_auth()