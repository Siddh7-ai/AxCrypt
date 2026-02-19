"""
AxCrypt Splash Screen - TASK 4
Professional animated loading screen
"""
import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk

class SplashScreen:
    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        
        # Import here to avoid circular dependency
        from core.config import LOGO_PATH, APP_NAME, APP_TAGLINE, C, SPLASH_DURATION
        
        # Create splash window
        self.splash = tk.Toplevel(root)
        self.splash.title("")
        self.splash.overrideredirect(True)  # Remove window decorations
        
        # Center on screen
        w, h = 500, 400
        sw = self.splash.winfo_screenwidth()
        sh = self.splash.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.splash.geometry(f"{w}x{h}+{x}+{y}")
        self.splash.configure(bg=C["bg_deep"])
        
        # Logo
        try:
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                img = img.resize((120, 120), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                logo_label = tk.Label(self.splash, image=self.logo_img, bg=C["bg_deep"])
                logo_label.pack(pady=(40, 15))
        except Exception:
            # Fallback if PIL not available
            tk.Label(self.splash, text="🛡️", font=("Courier", 48),
                    bg=C["bg_deep"], fg=C["neon_cyan"]).pack(pady=(40, 15))
        
        # App name
        tk.Label(self.splash, text=APP_NAME, font=("Courier", 24, "bold"),
                bg=C["bg_deep"], fg=C["text_white"]).pack()
        
        # Tagline
        tk.Label(self.splash, text=APP_TAGLINE, font=("Courier", 10),
                bg=C["bg_deep"], fg=C["text_dim"]).pack(pady=(5, 20))
        
        # Progress bar
        self.progress = ttk.Progressbar(self.splash, length=350, mode='indeterminate',
                                       style="Splash.Horizontal.TProgressbar")
        self.progress.pack(pady=15)
        
        # Loading text
        self.loading_label = tk.Label(self.splash, text="Loading...", 
                                      font=("Courier", 9),
                                      bg=C["bg_deep"], fg=C["neon_cyan"])
        self.loading_label.pack()
        
        # Style the progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Splash.Horizontal.TProgressbar",
                       troughcolor=C["bg_card"],
                       background=C["neon_cyan"],
                       darkcolor=C["neon_cyan"],
                       lightcolor=C["neon_cyan"],
                       bordercolor=C["border"],
                       thickness=8)
        
        # Start animation
        self.progress.start(10)
        
        # Auto-close after duration
        self.splash.after(SPLASH_DURATION, self.close)
    
    def close(self):
        self.progress.stop()
        self.splash.destroy()
        self.on_complete()