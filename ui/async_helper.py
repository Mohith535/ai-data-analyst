"""
async_helper.py — Background Threading Utility for Responsive Tkinter GUI
==========================================================================
Enforces the single-threaded GUI rule:
  1. Long-running tasks (SQL queries, Pandas ingestion, ML training) execute
     on background daemon threads to prevent the UI from freezing.
  2. Completion and error callbacks are scheduled onto Tkinter's main event loop
     using `widget.after(0, ...)`, guaranteeing thread-safe widget updates.
"""

import threading


def run_async(target, args=(), on_success=None, on_error=None, widget=None):
    """
    Run `target(*args)` in a background daemon thread.
    
    Parameters:
        target (callable): The blocking function to execute.
        args (tuple): Positional arguments for target.
        on_success (callable): Callback called with target's return value on the GUI thread.
        on_error (callable): Callback called with any caught Exception on the GUI thread.
        widget (tkinter.Widget): Widget instance whose `.after(0, ...)` is used to dispatch.
    
    Returns:
        threading.Thread: The started background thread.
    """
    def worker():
        try:
            result = target(*args)
            if on_success:
                if widget and hasattr(widget, "after"):
                    widget.after(0, lambda: on_success(result))
                else:
                    on_success(result)
        except Exception as exc:
            if on_error:
                if widget and hasattr(widget, "after"):
                    widget.after(0, lambda: on_error(exc))
                else:
                    on_error(exc)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t
