#!/usr/bin/env python3
"""
AxCrypt v1.0.1 CustomTkinter - Main Entry Point
FIXED: Single window initialization to prevent font errors
"""
import sys, os, logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import LOG_FILE, APP_NAME


def _setup_logging():
    fmt = "%(asctime)s  [%(levelname)-8s] %(name)s: %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


def main():
    _setup_logging()
    log = logging.getLogger(APP_NAME)
    log.info("Starting %s CustomTkinter Edition…", APP_NAME)

    try:
        import customtkinter as ctk
        from ui.splash import SplashScreen
        from ui.app import AxCryptApp
        
        # FIXED: Create main app FIRST (this establishes the Tk root)
        # This prevents "Too early to use font: no default root window" error
        app = AxCryptApp()
        app.withdraw()  # Keep hidden during splash
        
        # Show splash screen as Toplevel window
        def on_splash_complete():
            """Called when splash finishes - show main app"""
            app.deiconify()  # Show main app
            app.show_auth()  # Start at auth screen
        
        # Pass app as root (splash will be Toplevel of app)
        splash = SplashScreen(app, on_splash_complete)
        
        # Start single event loop
        app.mainloop()
        
    except Exception as exc:
        log.critical("Fatal: %s", exc, exc_info=True)
        import customtkinter as ctk
        error_root = ctk.CTk()
        error_root.title("AxCrypt – Fatal Error")
        error_root.geometry("450x180")
        error_root.configure(fg_color="#0a0c0f")
        ctk.CTkLabel(
            error_root, 
            text=f"Fatal error:\n\n{exc}",
            font=("Courier", 10), 
            fg_color="#0a0c0f", 
            text_color="#ff2d95",
            justify="left", 
            wraplength=400
        ).pack(expand=True, padx=20)
        error_root.mainloop()


if __name__ == "__main__":
    main()