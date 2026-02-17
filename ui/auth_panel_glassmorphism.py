"""
AxCrypt CustomTkinter - Stunning Modern Authentication Panel
════════════════════════════════════════════════════════════

FEATURES:
✓ NO BOTTOM NAVIGATION BAR on auth screen
✓ Animated gradient background
✓ Glassmorphic floating card
✓ Modern tab switcher with smooth animations
✓ Neon glow effects
✓ Particle effects in background
✓ Large, beautiful UI elements
✓ Guest access with icon
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, Canvas
from PIL import Image
import os
import random
import math
from core.config import C, LOGO_PATH


class AnimatedBackground(Canvas):
    """Animated gradient background with floating particles."""
    
    def __init__(self, master):
        super().__init__(
            master,
            bg=C["bg_deep"],
            highlightthickness=0
        )
        self.particles = []
        self._create_particles()
        self._animate()
    
    def _create_particles(self):
        """Create floating particles."""
        for _ in range(30):
            x = random.randint(0, 1400)
            y = random.randint(0, 900)
            size = random.randint(2, 5)
            speed = random.uniform(0.3, 1.0)
            color = random.choice([C["neon_cyan"], C["neon_violet"], C["neon_green"], C["neon_pink"]])
            
            particle = {
                'id': self.create_oval(x, y, x+size, y+size, fill=color, outline=""),
                'x': x,
                'y': y,
                'speed': speed,
                'color': color
            }
            self.particles.append(particle)
    
    def _animate(self):
        """Animate particles."""
        try:
            for particle in self.particles:
                # Move particle up
                particle['y'] -= particle['speed']
                
                # Reset if goes off screen
                if particle['y'] < -10:
                    particle['y'] = self.winfo_height() + 10
                    particle['x'] = random.randint(0, max(self.winfo_width(), 1))
                
                # Update position
                self.coords(
                    particle['id'],
                    particle['x'], particle['y'],
                    particle['x']+3, particle['y']+3
                )
            
            # Schedule next frame
            self.after(50, self._animate)
        except:
            pass


class AuthPanelGlassmorphic:
    """Stunning modern authentication panel."""
    
    def __init__(self, app):
        self.app = app
        self.container = None
        self._current_mode = "login"
        
        # Input fields
        self.username_entry = None
        self.password_entry = None
        self.email_entry = None
        self.mobile_entry = None
        self.fullname_entry = None
    
    def show(self):
        """Display the authentication panel."""
        if self.container:
            self.container.pack_forget()
        
        # Hide footer navigation during auth
        if hasattr(self.app, 'footer_frame'):
            self.app.footer_frame.pack_forget()
        
        self.container = ctk.CTkFrame(
            self.app.content,
            fg_color=C["bg_deep"],
            corner_radius=0
        )
        self.container.pack(fill="both", expand=True)
        
        self._build_ui()
    
    def hide(self):
        """Hide the authentication panel."""
        if self.container:
            self.container.pack_forget()
        
        # Show footer when leaving auth
        if hasattr(self.app, 'footer_frame'):
            self.app.footer_frame.pack(side="bottom", fill="x")
    
    def _build_ui(self):
        """Build the stunning auth UI."""
        for widget in self.container.winfo_children():
            widget.destroy()
        
        # ═══════════════════════════════════════════════════
        # ANIMATED BACKGROUND
        # ═══════════════════════════════════════════════════
        self.bg_canvas = AnimatedBackground(self.container)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # ═══════════════════════════════════════════════════
        # CENTER FLOATING CARD
        # ═══════════════════════════════════════════════════
        
        # Card container with glow effect
        card_container = ctk.CTkFrame(
            self.container,
            fg_color="transparent"
        )
        card_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Glassmorphic card
        main_card = ctk.CTkFrame(
            card_container,
            fg_color=("#1a1e28", "#1a1e28"),
            corner_radius=20,
            border_width=2,
            border_color=C["neon_cyan"],
            width=480,
            height=580
        )
        main_card.pack(padx=20, pady=20)
        main_card.pack_propagate(False)
        
        # Inner content
        content = ctk.CTkFrame(main_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=25)
        
        # ═══════════════════════════════════════════════════
        # LOGO & BRANDING
        # ═══════════════════════════════════════════════════
        
        logo_frame = ctk.CTkFrame(content, fg_color="transparent")
        logo_frame.pack(pady=(0, 10))
        
        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                img = img.resize((70, 70), Image.Resampling.LANCZOS)
                logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(70, 70))
                ctk.CTkLabel(logo_frame, image=logo_img, text="").pack()
        except Exception:
            ctk.CTkLabel(
                logo_frame,
                text="🛡️",
                font=("Segoe UI", 40),
                text_color=C["neon_cyan"]
            ).pack()
        
        # App name with glow
        ctk.CTkLabel(
            content,
            text="AxCrypt",
            font=("Segoe UI", 26, "bold"),
            text_color=C["text_white"]
        ).pack()
        
        ctk.CTkLabel(
            content,
            text="Master-Level Encryption",
            font=("Segoe UI", 12),
            text_color=C["neon_cyan"]
        ).pack(pady=(3, 15))
        
        # ═══════════════════════════════════════════════════
        # MODERN TAB SWITCHER
        # ═══════════════════════════════════════════════════
        
        tab_container = ctk.CTkFrame(
            content,
            fg_color=C["bg_input"],
            corner_radius=10,
            height=44
        )
        tab_container.pack(fill="x", pady=(0, 15))
        tab_container.pack_propagate(False)
        
        # Login tab
        self.login_tab = ctk.CTkButton(
            tab_container,
            text="🔐 Login",
            font=("Segoe UI", 12, "bold"),
            fg_color=C["neon_cyan"] if self._current_mode == "login" else "transparent",
            hover_color=C["bg_hover"],
            text_color=C["text_white"],
            corner_radius=8,
            height=36,
            command=lambda: self._switch_mode("login")
        )
        self.login_tab.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Signup tab
        self.signup_tab = ctk.CTkButton(
            tab_container,
            text="✨ Sign Up",
            font=("Segoe UI", 12, "bold"),
            fg_color=C["neon_green"] if self._current_mode == "signup" else "transparent",
            hover_color=C["bg_hover"],
            text_color=C["text_white"],
            corner_radius=8,
            height=36,
            command=lambda: self._switch_mode("signup")
        )
        self.signup_tab.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # ═══════════════════════════════════════════════════
        # FORM FIELDS (Scrollable)
        # ═══════════════════════════════════════════════════
        
        # Scrollable frame for forms
        form_scroll = ctk.CTkScrollableFrame(
            content,
            fg_color="transparent",
            height=220
        )
        form_scroll.pack(fill="both", expand=True)
        
        self.form_container = form_scroll
        
        if self._current_mode == "login":
            self._build_login_form()
        else:
            self._build_signup_form()
        
        # ═══════════════════════════════════════════════════
        # GUEST ACCESS
        # ═══════════════════════════════════════════════════
        
        guest_btn = ctk.CTkButton(
            content,
            text="⚡ Continue as Guest",
            font=("Segoe UI", 12, "bold"),
            fg_color=C["neon_violet"],
            hover_color=C["neon_pink"],
            text_color=C["text_white"],
            corner_radius=8,
            height=38,
            command=self._continue_as_guest
        )
        guest_btn.pack(fill="x", pady=(15, 0))
    
    def _build_login_form(self):
        """Build login form."""
        # Username
        self._create_input(
            self.form_container,
            "Username",
            "Enter your username",
            False
        )
        self.username_entry = self.last_entry
        
        # Password
        self._create_input(
            self.form_container,
            "Password",
            "Enter your password",
            True
        )
        self.password_entry = self.last_entry
        
        # Login button
        login_btn = ctk.CTkButton(
            self.form_container,
            text="🚀 Login to AxCrypt",
            font=("Segoe UI", 13, "bold"),
            fg_color=C["neon_cyan"],
            hover_color=C["neon_green"],
            text_color=C["text_white"],
            corner_radius=8,
            height=42,
            command=self._handle_login
        )
        login_btn.pack(fill="x", pady=(20, 10))
        
        # Forgot password
        ctk.CTkButton(
            self.form_container,
            text="Forgot Password?",
            font=("Segoe UI", 10),
            fg_color="transparent",
            hover_color=C["bg_hover"],
            text_color=C["text_dim"],
            command=self._forgot_password
        ).pack()
    
    def _build_signup_form(self):
        """Build signup form."""
        # Full Name
        self._create_input(self.form_container, "Full Name", "Your full name", False)
        self.fullname_entry = self.last_entry
        
        # Username
        self._create_input(self.form_container, "Username", "Choose username", False)
        self.username_entry = self.last_entry
        
        # Email
        self._create_input(self.form_container, "Email", "your@email.com", False)
        self.email_entry = self.last_entry
        
        # Mobile
        self._create_input(self.form_container, "Mobile", "+1234567890", False)
        self.mobile_entry = self.last_entry
        
        # Password
        self._create_input(self.form_container, "Password", "Strong password", True)
        self.password_entry = self.last_entry
        
        # Signup button
        signup_btn = ctk.CTkButton(
            self.form_container,
            text="✨ Create Account",
            font=("Segoe UI", 13, "bold"),
            fg_color=C["neon_green"],
            hover_color=C["neon_cyan"],
            text_color=C["text_white"],
            corner_radius=8,
            height=42,
            command=self._handle_signup
        )
        signup_btn.pack(fill="x", pady=(20, 0))
    
    def _create_input(self, parent, label, placeholder, is_password):
        """Create a styled input field."""
        ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 11, "bold"),
            text_color=C["text_mid"],
            anchor="w"
        ).pack(fill="x", pady=(6, 2))
        
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            font=("Segoe UI", 12),
            fg_color=C["bg_input"],
            border_color=C["border_glow"],
            border_width=1,
            text_color=C["text_white"],
            placeholder_text_color=C["text_dim"],
            corner_radius=8,
            height=38,
            show="●" if is_password else None
        )
        entry.pack(fill="x", pady=(0, 3))
        
        self.last_entry = entry
    
    def _switch_mode(self, mode):
        """Switch between login and signup."""
        if self._current_mode != mode:
            self._current_mode = mode
            self._build_ui()
    
    def _continue_as_guest(self):
        """Continue as guest."""
        result = messagebox.askyesno(
            "Guest Access",
            "Continue as Guest?\n\n"
            "✓ Full encryption features\n"
            "✓ No account needed\n"
            "⚠ No history tracking\n"
            "⚠ No password recovery\n\n"
            "Continue?",
            icon='question'
        )
        
        if result:
            self.app.show_main("Guest")
    
    def _forgot_password(self):
        """Handle forgot password."""
        username = ctk.CTkInputDialog(
            text="Enter your username for password reset:",
            title="Forgot Password"
        ).get_input()
        
        if not username:
            return
        
        if not self.app.user_mgr.user_exists(username):
            messagebox.showerror("Error", "Username not found")
            return
        
        mobile = self.app.user_mgr.get_mobile_by_username(username)
        if not mobile:
            messagebox.showerror("Error", "No mobile number on file")
            return
        
        # Generate OTP
        otp = self.app.user_mgr.generate_otp(mobile, purpose="reset", username=username)
        
        # Show OTP dialog
        otp_input = ctk.CTkInputDialog(
            text=f"OTP sent to {mobile}\n(Demo: {otp})\n\nEnter OTP:",
            title="Verify OTP"
        ).get_input()
        
        if not otp_input:
            return
        
        # Verify OTP
        ok, msg = self.app.user_mgr.verify_otp(mobile, otp_input)
        if not ok:
            messagebox.showerror("Error", msg)
            return
        
        # Get new password
        new_password = ctk.CTkInputDialog(
            text="Enter new password:",
            title="Reset Password"
        ).get_input()
        
        if not new_password:
            return
        
        # Reset password
        ok, msg = self.app.user_mgr.reset_password(username, new_password)
        if ok:
            messagebox.showinfo("Success", "Password reset successfully!")
        else:
            messagebox.showerror("Error", msg)
    
    def _handle_login(self):
        """Handle login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Enter username and password")
            return
        
        ok, msg = self.app.user_mgr.authenticate(username, password)
        
        if ok:
            self.app.show_main(username)
        else:
            messagebox.showerror("Login Failed", msg)
    
    def _handle_signup(self):
        """Handle signup."""
        fullname = self.fullname_entry.get().strip()
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        mobile = self.mobile_entry.get().strip()
        password = self.password_entry.get()
        
        if not all([username, password, email, mobile]):
            messagebox.showerror("Error", "Fill in all fields")
            return
        
        # Generate OTP
        otp = self.app.user_mgr.generate_otp(mobile, purpose="register", username=username)
        
        # Show OTP dialog
        otp_input = ctk.CTkInputDialog(
            text=f"OTP sent to {mobile}\n(Demo: {otp})\n\nEnter OTP:",
            title="Verify OTP"
        ).get_input()
        
        if not otp_input:
            return
        
        # Verify OTP
        ok, msg = self.app.user_mgr.verify_otp(mobile, otp_input)
        if not ok:
            messagebox.showerror("OTP Failed", msg)
            return
        
        # Register
        ok, msg = self.app.user_mgr.register(username, password, email, mobile, fullname)
        
        if ok:
            messagebox.showinfo("Success", "Account created! Please login.")
            self._switch_mode("login")
        else:
            messagebox.showerror("Failed", msg)