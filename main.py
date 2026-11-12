"""
main.py — Entry Point for AI Data Analyst
============================================
This is the file you run to start the app: python main.py

WHY a separate main.py?
  Convention. Most Python projects have a thin main.py that just:
  1. Does any one-time setup (like creating the database)
  2. Creates and runs the application

  This keeps the actual app logic in the ui/ and other modules.
"""

import sys
from tkinter import messagebox
import db
from ui.app import App


def main():
    """
    Initialize the database and launch the GUI.
    
    Steps:
        1. Try to connect to MySQL and create the database
        2. If MySQL isn't running, show a helpful error and exit
        3. If all good, create and run the App
    """
    print("=" * 50)
    print("  AI Data Analyst — Starting up...")
    print("=" * 50)
    
    # --- Step 1: Initialize the database ---
    # WHY do this before creating the GUI?
    #   If MySQL isn't running, we want to tell the user immediately,
    #   not after they've loaded a CSV and tried to save.
    print("[STARTUP] Connecting to MySQL...")
    
    db_ok = db.initialize_database()
    
    if not db_ok:
        # Show a GUI error popup even though the main app hasn't started
        # WHY? Because a console error message might not be visible to the user
        import customtkinter as ctk
        # Create a temporary hidden root window for the messagebox
        temp = ctk.CTk()
        temp.withdraw()  # Hide it
        messagebox.showerror(
            "MySQL Connection Failed",
            "Could not connect to MySQL!\n\n"
            "Please check:\n"
            "1. Is MySQL Server installed and running?\n"
            "2. Is the password in .env correct?\n"
            "3. Is the MySQL service started?\n\n"
            "The app will now exit."
        )
        temp.destroy()
        sys.exit(1)
    
    print("[STARTUP] Database ready! Launching GUI...")
    
    # --- Step 2: Create and run the app ---
    app = App()
    
    # mainloop() starts Tkinter's event loop.
    # WHY? Tkinter is event-driven. mainloop() listens for button clicks,
    # key presses, window resizes, etc. and dispatches them to handlers.
    # Without it, the window would appear and immediately close.
    app.mainloop()


# WHY this if-block?
#   It means main() only runs when you execute this file directly
#   (python main.py), NOT when someone imports it (import main).
#   This is a Python best practice.
if __name__ == "__main__":
    main()

