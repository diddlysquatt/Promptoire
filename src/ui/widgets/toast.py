"""
Toast - Elegant notification widget with fade animation
"""

import tkinter as tk
from typing import Optional, Callable
from ..design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION,
    get_font, blend_colors, lighten
)


class Toast(tk.Toplevel):
    """
    A modern toast notification widget with:
    - Bottom-right positioning relative to parent window
    - Smooth fade-in/fade-out animation
    - Success/error/info variants with icons
    - Auto-dismiss with configurable duration
    """
    
    VARIANTS = {
        "success": {
            "bg": "#0a1f0a",
            "border": COLORS.GREEN,
            "icon": "✓",
            "icon_color": COLORS.GREEN,
        },
        "error": {
            "bg": "#1f0a0a",
            "border": COLORS.ERROR,
            "icon": "✕",
            "icon_color": COLORS.ERROR,
        },
        "info": {
            "bg": COLORS.SURFACE_2,
            "border": COLORS.CYAN,
            "icon": "ℹ",
            "icon_color": COLORS.CYAN,
        },
        "warning": {
            "bg": "#1f1a0a",
            "border": COLORS.WARNING,
            "icon": "⚠",
            "icon_color": COLORS.WARNING,
        },
    }
    
    # Track active toasts to stack them
    _active_toasts = []
    
    def __init__(
        self,
        parent: tk.Tk,
        message: str,
        variant: str = "success",
        duration: int = 2500,
        theme: dict = None,
        on_dismiss: Optional[Callable] = None,
    ):
        super().__init__(parent)
        
        self.parent = parent
        self.message = message
        self.duration = duration
        self.theme = theme or {}
        self._on_dismiss = on_dismiss
        self._dismissed = False
        
        # Get variant styling
        v = self.VARIANTS.get(variant, self.VARIANTS["info"])
        self._bg = v["bg"]
        self._border = v["border"]
        self._icon = v["icon"]
        self._icon_color = v["icon_color"]
        self._fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        
        # Configure window
        self.overrideredirect(True)  # No window decorations
        self.attributes("-topmost", True)
        self.configure(bg=self._bg)
        
        # Start fully transparent
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass
        
        # Build content
        self._build_content()
        
        # Position the toast
        self._position_toast()
        
        # Track this toast
        Toast._active_toasts.append(self)
        
        # Start fade-in animation
        self.after(10, self._fade_in)
        
        # Schedule auto-dismiss
        if duration > 0:
            self._dismiss_job = self.after(duration, self._start_dismiss)
        else:
            self._dismiss_job = None
    
    def _build_content(self):
        """Build the toast content"""
        # Main container with border
        self._container = tk.Frame(
            self,
            bg=self._bg,
            highlightbackground=self._border,
            highlightthickness=2,
            highlightcolor=self._border,
        )
        self._container.pack(fill="both", expand=True)
        
        # Inner content with padding
        content = tk.Frame(self._container, bg=self._bg)
        content.pack(fill="both", expand=True, padx=SPACING.MD, pady=SPACING.SM)
        
        # Icon
        icon_label = tk.Label(
            content,
            text=self._icon,
            font=get_font(TYPOGRAPHY.SIZE_MD, TYPOGRAPHY.WEIGHT_BOLD),
            bg=self._bg,
            fg=self._icon_color,
        )
        icon_label.pack(side="left", padx=(0, SPACING.SM))
        
        # Message
        msg_label = tk.Label(
            content,
            text=self.message,
            font=get_font(TYPOGRAPHY.SIZE_BASE),
            bg=self._bg,
            fg=self._fg,
            anchor="w",
        )
        msg_label.pack(side="left", fill="x", expand=True)
        
        # Bind click to dismiss
        for widget in [self, self._container, content, icon_label, msg_label]:
            widget.bind("<Button-1>", lambda e: self._start_dismiss())
            widget.configure(cursor="hand2")
    
    def _position_toast(self):
        """Position toast at bottom-right of parent window"""
        self.update_idletasks()
        
        # Get toast dimensions
        toast_width = self.winfo_reqwidth()
        toast_height = self.winfo_reqheight()
        
        # Ensure minimum size
        toast_width = max(toast_width, 200)
        toast_height = max(toast_height, 40)
        
        # Get parent window position and size
        try:
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
        except Exception:
            # Fallback to screen dimensions
            parent_x = 0
            parent_y = 0
            parent_width = self.winfo_screenwidth()
            parent_height = self.winfo_screenheight()
        
        # Calculate position (bottom-right with margin)
        margin = 16
        
        # Stack toasts if multiple are active
        stack_offset = 0
        for toast in Toast._active_toasts:
            if toast is not self and not toast._dismissed:
                try:
                    stack_offset += toast.winfo_reqheight() + 8
                except Exception:
                    stack_offset += 50
        
        x = parent_x + parent_width - toast_width - margin
        y = parent_y + parent_height - toast_height - margin - stack_offset - 60  # 60 for footer
        
        # Ensure on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, min(x, screen_width - toast_width))
        y = max(0, min(y, screen_height - toast_height))
        
        self.geometry(f"{toast_width}x{toast_height}+{x}+{y}")
    
    def _fade_in(self, step: int = 0):
        """Animate fade-in"""
        steps = ANIMATION.STEPS_FAST
        
        if step > steps:
            try:
                self.attributes("-alpha", 1.0)
            except Exception:
                pass
            return
        
        try:
            # Ease-out for smooth deceleration
            progress = step / steps
            alpha = 1 - pow(1 - progress, 3)  # Cubic ease-out
            self.attributes("-alpha", alpha)
        except Exception:
            return
        
        self.after(ANIMATION.FAST // steps, lambda: self._fade_in(step + 1))
    
    def _start_dismiss(self):
        """Start the dismiss animation"""
        if self._dismissed:
            return
        self._dismissed = True
        
        # Cancel any pending dismiss job
        if self._dismiss_job:
            try:
                self.after_cancel(self._dismiss_job)
            except Exception:
                pass
        
        self._fade_out()
    
    def _fade_out(self, step: int = 0):
        """Animate fade-out and destroy"""
        steps = ANIMATION.STEPS_FAST
        
        if step > steps:
            self._cleanup()
            return
        
        try:
            # Ease-in for smooth acceleration
            progress = step / steps
            alpha = 1 - pow(progress, 2)  # Quadratic ease-in
            self.attributes("-alpha", alpha)
        except Exception:
            self._cleanup()
            return
        
        self.after(ANIMATION.FAST // steps, lambda: self._fade_out(step + 1))
    
    def _cleanup(self):
        """Clean up and destroy the toast"""
        # Remove from active toasts
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)
        
        # Callback
        if self._on_dismiss:
            try:
                self._on_dismiss()
            except Exception:
                pass
        
        # Destroy
        try:
            self.destroy()
        except Exception:
            pass
    
    @classmethod
    def show(
        cls,
        parent: tk.Tk,
        message: str,
        variant: str = "success",
        duration: int = 2500,
        theme: dict = None,
        on_dismiss: Optional[Callable] = None,
    ) -> "Toast":
        """
        Convenience method to show a toast notification.
        
        Args:
            parent: Parent window
            message: Message to display
            variant: "success", "error", "info", or "warning"
            duration: Auto-dismiss duration in ms (0 to disable)
            theme: Optional theme dict for colors
            on_dismiss: Optional callback when dismissed
            
        Returns:
            Toast instance
        """
        return cls(
            parent=parent,
            message=message,
            variant=variant,
            duration=duration,
            theme=theme,
            on_dismiss=on_dismiss,
        )
    
    @classmethod
    def dismiss_all(cls):
        """Dismiss all active toasts"""
        for toast in list(cls._active_toasts):
            try:
                toast._start_dismiss()
            except Exception:
                pass
