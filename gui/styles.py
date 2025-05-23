"""
Modern UI style system for the diabetes tracking application.
"""
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import font
import time


class ModernStyles:
    """Modern styling system with animations and beautiful components."""
    
    # Modern color palette
    COLORS = {
        'primary': '#6C5CE7',
        'secondary': '#A29BFE', 
        'success': '#00B894',
        'danger': '#E17055',
        'warning': '#FDCB6E',
        'info': '#74B9FF',
        'dark': '#2D3436',
        'light': '#DDD',
        'background': '#F8F9FA',
        'card': '#FFFFFF',
        'gradient_start': '#667EEA',
        'gradient_end': '#764BA2',
        'accent': '#FF6B6B'
    }
    
    @staticmethod
    def configure_modern_theme(root):
        """Configure modern theme for the application."""
        # Configure ttk styles
        style = ttk.Style()
        
        # Modern button styles
        style.configure(
            "Modern.TButton",
            padding=(20, 12),
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            focuscolor="none",
            relief="flat"
        )
        
        style.configure(
            "ModernPrimary.TButton",
            background=ModernStyles.COLORS['primary'],
            foreground="white",
            borderwidth=0,
            focuscolor="none"
        )
        
        style.map(
            "ModernPrimary.TButton",
            background=[
                ("active", ModernStyles.COLORS['secondary']),
                ("pressed", ModernStyles.COLORS['dark'])
            ]
        )
        
        # Modern card frame style
        style.configure(
            "Card.TFrame",
            background=ModernStyles.COLORS['card'],
            relief="flat",
            borderwidth=2
        )
        
        # Modern entry style
        style.configure(
            "Modern.TEntry",
            padding=(12, 8),
            borderwidth=1,
            relief="solid",
            fieldbackground="white"
        )
        
        return style


class AnimatedWidget:
    """Mixin class for adding animations to widgets."""
    
    @staticmethod
    def fade_in(widget, duration=300):
        """Fade in animation."""
        steps = 20
        step_time = duration // steps
        alpha_step = 1.0 / steps
        
        def animate(step=0):
            if step <= steps:
                alpha = step * alpha_step
                try:
                    widget.attributes('-alpha', alpha)
                except:
                    pass
                widget.after(step_time, lambda: animate(step + 1))
        
        animate()
    
    @staticmethod
    def slide_in(widget, direction='left', duration=300):
        """Slide in animation."""
        if not hasattr(widget, 'original_x'):
            widget.update_idletasks()
            widget.original_x = widget.winfo_x()
            widget.original_y = widget.winfo_y()
        
        start_x = widget.original_x - 100 if direction == 'left' else widget.original_x + 100
        widget.place(x=start_x, y=widget.original_y)
        
        steps = 20
        step_time = duration // steps
        x_step = (widget.original_x - start_x) / steps
        
        def animate(step=0):
            if step <= steps:
                current_x = start_x + (x_step * step)
                widget.place(x=current_x, y=widget.original_y)
                widget.after(step_time, lambda: animate(step + 1))
            else:
                widget.place(x=widget.original_x, y=widget.original_y)
        
        animate()


class ModernButton(ttk.Button):
    """Modern button with hover effects and animations."""
    
    def __init__(self, parent, text="", command=None, style_type="primary", icon="", **kwargs):
        # Combine icon and text
        display_text = f"{icon} {text}" if icon else text
        
        # Create appropriate style name
        style_name = f"Modern{style_type.capitalize()}.TButton"
        
        super().__init__(
            parent, 
            text=display_text, 
            command=command,
            **kwargs
        )
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
    
    def _on_enter(self, event):
        """Hover effect."""
        self.configure(cursor="hand2")
    
    def _on_leave(self, event):
        """Remove hover effect."""
        self.configure(cursor="")
    
    def _on_click(self, event):
        """Click animation - simplified for TTK compatibility."""
        # TTK doesn't support relief changes, so we'll just do a simple visual feedback
        self.state(['pressed'])
        self.after(100, lambda: self.state(['!pressed']))


class ModernCard(ttk.Frame):
    """Modern card container with shadow effect."""
    
    def __init__(self, parent, title="", padding=20, **kwargs):
        super().__init__(parent, style="Card.TFrame", padding=padding, **kwargs)
        
        if title:
            title_label = ttk.Label(
                self,
                text=title,
                font=("Segoe UI", 14, "bold"),
                foreground=ModernStyles.COLORS['dark']
            )
            title_label.pack(anchor="w", pady=(0, 15))


class NavigationManager:
    """Manages navigation stack and history."""
    
    def __init__(self):
        self.history = []
        self.current_window = None
    
    def push(self, window_info):
        """Push a window to navigation history."""
        if self.current_window:
            self.history.append(self.current_window)
        self.current_window = window_info
    
    def pop(self):
        """Pop and return to previous window."""
        if self.history:
            previous = self.history.pop()
            self.current_window = previous
            return previous
        return None
    
    def can_go_back(self):
        """Check if can go back."""
        return len(self.history) > 0


# Global navigation manager
nav_manager = NavigationManager()


class ModernDialog(tk.Toplevel):
    """Modern dialog base class with navigation and animations."""
    
    def __init__(self, parent, title="", width=None, height=None, can_navigate_back=True):
        super().__init__(parent)
        
        # Setup responsive dialog
        from gui.utils import setup_responsive_dialog
        self.dialog_width, self.dialog_height = setup_responsive_dialog(
            self, title, width, height
        )
        
        # Modern styling
        self.configure(bg=ModernStyles.COLORS['background'])
        
        # Navigation setup
        self.can_navigate_back = can_navigate_back
        if can_navigate_back:
            nav_manager.push({
                'window': self,
                'title': title,
                'parent': parent
            })
        
        # Main container with modern styling
        self.main_container = ModernCard(self, padding=25)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with navigation
        self._create_header(title)
        
        # Content area
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Footer with modern buttons
        self.footer_frame = ttk.Frame(self.main_container)
        self.footer_frame.pack(fill="x")
        
        # Add fade in animation
        self.after(10, lambda: AnimatedWidget.fade_in(self))
    
    def _create_header(self, title):
        """Create modern header with navigation."""
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Back button if navigation is available
        if self.can_navigate_back and nav_manager.can_go_back():
            back_btn = ModernButton(
                header_frame,
                text="",
                icon="◀",
                command=self._go_back,
                style_type="secondary"
            )
            back_btn.pack(side="left")
        
        # Title
        if title:
            title_label = ttk.Label(
                header_frame,
                text=title,
                font=("Segoe UI", 18, "bold"),
                foreground=ModernStyles.COLORS['dark']
            )
            title_label.pack(side="left", padx=(15, 0) if self.can_navigate_back else (0, 0))
    
    def _go_back(self):
        """Navigate back to previous window."""
        previous = nav_manager.pop()
        if previous:
            self.destroy()
            if hasattr(previous['parent'], 'lift'):
                previous['parent'].lift()
                previous['parent'].focus_force()
    
    def add_action_button(self, text, command, style_type="primary", icon=""):
        """Add a modern action button to footer."""
        btn = ModernButton(
            self.footer_frame,
            text=text,
            command=command,
            style_type=style_type,
            icon=icon
        )
        btn.pack(side="right", padx=(10, 0))
        return btn
    
    def add_cancel_button(self, command=None):
        """Add a modern cancel button."""
        if command is None:
            command = self.destroy
        
        return self.add_action_button("İptal", command, "danger", "✖")


# Icons for modern UI
ICONS = {
    'add': '➕',
    'edit': '✏️',
    'delete': '🗑️',
    'save': '💾',
    'cancel': '✖',
    'back': '◀',
    'forward': '▶',
    'home': '🏠',
    'user': '👤',
    'settings': '⚙️',
    'search': '🔍',
    'chart': '📊',
    'calendar': '📅',
    'heart': '❤️',
    'medicine': '💊',
    'check': '✓',
    'warning': '⚠️',
    'info': 'ℹ️',
    'mail': '📧'
} 