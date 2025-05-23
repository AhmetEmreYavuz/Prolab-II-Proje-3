"""
Utility functions for GUI components.
"""
import tkinter as tk
import ttkbootstrap as ttk


def setup_responsive_dialog(dialog, title, width=None, height=None, min_width=400, min_height=300):
    """
    Configure a dialog window to be responsive and properly positioned.
    
    Args:
        dialog: The Toplevel dialog instance
        title: Window title
        width: Preferred width (will be adjusted based on screen size)
        height: Preferred height (will be adjusted based on screen size)
        min_width: Minimum width
        min_height: Minimum height
    """
    # Set window title
    dialog.title(title)
    
    # Get screen dimensions
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    
    # Use defaults if dimensions not provided
    if width is None:
        width = min(int(screen_width * 0.7), 800)
    if height is None:
        height = min(int(screen_height * 0.7), 600)
    
    # Ensure minimum dimensions
    width = max(width, min_width)
    height = max(height, min_height)
    
    # Calculate position
    x_pos = (screen_width - width) // 2
    y_pos = (screen_height - height) // 2
    
    # Set geometry with position
    dialog.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
    
    # Make the dialog resizable
    dialog.resizable(True, True)
    
    # Set minimum size
    dialog.minsize(min_width, min_height)
    
    # Set theme-specific background 
    dialog.configure(bg="#2b3e50")  # Default for the superhero theme
    
    # Bring dialog to front and keep it on top
    dialog.transient(dialog.master)  # Make it a transient window
    dialog.grab_set()  # Make it modal
    dialog.lift()  # Bring to front
    dialog.focus_force()  # Force focus
    
    # Schedule additional focusing to ensure it stays on top
    dialog.after(10, lambda: dialog.focus_force())
    dialog.after(10, lambda: dialog.lift())
    
    # Return configured width and height for further layout adjustments
    return width, height 