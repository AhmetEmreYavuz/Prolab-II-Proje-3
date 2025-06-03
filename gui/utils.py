
import tkinter as tk
import ttkbootstrap as ttk


def setup_responsive_dialog(dialog, title, width=None, height=None, min_width=400, min_height=300):

    dialog.title(title)


    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()

    if width is None:
        width = min(int(screen_width * 0.7), 800)
    if height is None:
        height = min(int(screen_height * 0.7), 600)

    width = max(width, min_width)
    height = max(height, min_height)

    x_pos = (screen_width - width) // 2
    y_pos = (screen_height - height) // 2

    dialog.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

    dialog.resizable(True, True)

    dialog.minsize(min_width, min_height)

    dialog.configure(bg="#2b3e50")

    dialog.transient(dialog.master)
    dialog.grab_set()
    dialog.lift()
    dialog.focus_force()

    dialog.after(10, lambda: dialog.focus_force())
    dialog.after(10, lambda: dialog.lift())

    return width, height 