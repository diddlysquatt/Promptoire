"""
ToggleSwitch - An animated iOS-style toggle switch
"""

import math
import tkinter as tk
from typing import Callable, Optional
from ..design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION,
    get_font, blend_colors, lighten, darken, ensure_contrast,
    WCAG_AA_NORMAL
)


class ToggleSwitch(tk.Canvas):
    """
    An animated toggle switch widget with:
    - Smooth sliding animation
    - Glow effect when on
    - Custom colors
    - Optional label
    """
    
    def __init__(
        self,
        parent,
        variable: Optional[tk.BooleanVar] = None,
        command: Optional[Callable] = None,
        label: str = "",
        label_position: str = "right",  # "left" or "right"
        width: int = 44,
        height: int = 24,
        on_color: str = None,
        off_color: str = None,
        theme: dict = None,
        disabled: bool = False,
        **kwargs
    ):
        self.parent = parent
        self.command = command
        self.label = label
        self.label_position = label_position
        self._width = width
        self._height = height
        self.theme = theme or {}
        self._disabled = disabled
        
        # Create variable if not provided
        if variable is None:
            self._variable = tk.BooleanVar(value=False)
        else:
            self._variable = variable
        
        # Colors
        self._on_color = on_color or self.theme.get("highlight", COLORS.CYAN)
        self._off_color = off_color or self.theme.get("accent", COLORS.SURFACE_3)
        self._thumb_color = COLORS.TEXT_PRIMARY
        self._glow_color = self.theme.get("glow_color", COLORS.CYAN_GLOW)
        
        # Animation state
        self._thumb_x = self._get_thumb_x()
        self._target_x = self._thumb_x
        self._animating = False
        
        # Calculate total width with label
        self._label_gap = 10
        if label:
            self._total_width = self._width + self._label_gap + (len(label) * 7)
        else:
            self._total_width = self._width
        
        # Get parent background
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = self.theme.get("background", COLORS.BLACK)
        
        # Initialize canvas
        super().__init__(
            parent,
            width=self._total_width,
            height=self._height,
            bg=parent_bg,
            highlightthickness=0,
            cursor="hand2" if not disabled else "arrow",
            **kwargs
        )

        self._hover = False
        
        # Draw initial state
        self._draw()
        
        # Bind events
        if not disabled:
            self.bind("<Button-1>", self._on_click)
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
        
        # Watch for variable changes
        self._variable.trace_add("write", self._on_variable_change)
    
    def _get_thumb_x(self) -> float:
        """Get thumb X position based on state"""
        padding = 2
        thumb_radius = (self._height - padding * 2) // 2
        if self._variable.get():
            return self._width - thumb_radius - padding - 2
        else:
            return thumb_radius + padding + 2
    
    def _draw(self):
        """Draw the toggle switch"""
        self.delete("all")
        
        # Determine offset for label position
        if self.label and self.label_position == "left":
            label_width = len(self.label) * 7
            offset_x = label_width + self._label_gap
        else:
            offset_x = 0
        
        # Get colors based on state
        is_on = self._variable.get()
        
        if self._disabled:
            track_color = COLORS.SURFACE_2
            thumb_color = COLORS.TEXT_DISABLED
        elif is_on:
            track_color = self._on_color
            thumb_color = self._thumb_color
        else:
            track_color = self._off_color
            thumb_color = COLORS.TEXT_SECONDARY
        
        # Draw glow when on and hovering
        if is_on and self._hover and not self._disabled:
            self._draw_glow(offset_x)
        
        # Draw track (pill shape)
        padding = 2
        self._draw_pill(
            offset_x + padding,
            padding,
            offset_x + self._width - padding,
            self._height - padding,
            fill=track_color,
            outline=lighten(track_color, 0.1) if self._hover else ""
        )
        
        # Draw thumb (circle)
        thumb_radius = (self._height - padding * 2) // 2 - 2
        thumb_y = self._height // 2
        
        # Add subtle shadow to thumb
        if not self._disabled:
            self.create_oval(
                offset_x + self._thumb_x - thumb_radius + 1,
                thumb_y - thumb_radius + 1,
                offset_x + self._thumb_x + thumb_radius + 1,
                thumb_y + thumb_radius + 1,
                fill=COLORS.BLACK,
                outline=""
            )
        
        # Draw thumb
        self.create_oval(
            offset_x + self._thumb_x - thumb_radius,
            thumb_y - thumb_radius,
            offset_x + self._thumb_x + thumb_radius,
            thumb_y + thumb_radius,
            fill=thumb_color,
            outline=""
        )
        
        # Draw label
        if self.label:
            fg = COLORS.TEXT_DISABLED if self._disabled else self.theme.get("foreground", COLORS.TEXT_PRIMARY)
            if self.label_position == "left":
                label_x = 0
                anchor = "w"
            else:
                label_x = self._width + self._label_gap + offset_x
                anchor = "w"
            
            self.create_text(
                label_x, self._height // 2,
                text=self.label,
                font=get_font(TYPOGRAPHY.SIZE_BASE),
                fill=fg,
                anchor=anchor
            )
    
    def _draw_glow(self, offset_x: float):
        """Draw glow effect around track"""
        padding = 2
        glow_size = 4
        
        # Draw multiple layers for soft glow
        for i in range(3):
            expand = glow_size - i
            self._draw_pill(
                offset_x + padding - expand,
                padding - expand,
                offset_x + self._width - padding + expand,
                self._height - padding + expand,
                fill="",
                outline=blend_colors(self._on_color, COLORS.TEXT_PRIMARY, 0.05 * (3 - i))
            )
    
    def _draw_pill(self, x1, y1, x2, y2, **kwargs):
        """Draw a pill/capsule shape"""
        radius = (y2 - y1) // 2
        points = []
        
        # Left semicircle
        for i in range(180, 360, 15):
            x = x1 + radius + radius * math.cos(math.radians(i))
            y = y1 + radius + radius * math.sin(math.radians(i))
            points.extend([x, y])
        
        # Right semicircle
        for i in range(0, 180, 15):
            x = x2 - radius + radius * math.cos(math.radians(i))
            y = y1 + radius + radius * math.sin(math.radians(i))
            points.extend([x, y])
        
        if len(points) >= 6:
            return self.create_polygon(points, smooth=True, **kwargs)
    
    def _on_click(self, event=None):
        """Handle click to toggle"""
        if self._disabled:
            return
        
        # Toggle value
        new_value = not self._variable.get()
        self._variable.set(new_value)
        
        # Animate
        self._animate_toggle()
        
        # Call command
        if self.command:
            self.command()
    
    def _on_variable_change(self, *args):
        """Handle variable change"""
        self._target_x = self._get_thumb_x()
        if not self._animating:
            self._animate_toggle()
    
    def _animate_toggle(self):
        """Animate the thumb sliding"""
        self._target_x = self._get_thumb_x()
        self._animating = True
        self._animate_step()
    
    def _animate_step(self):
        """Single animation step"""
        if not self._animating:
            return
        
        # Calculate new position (ease-out)
        diff = self._target_x - self._thumb_x
        if abs(diff) < 0.5:
            self._thumb_x = self._target_x
            self._animating = False
            self._draw()
            return
        
        # Move towards target with easing
        self._thumb_x += diff * 0.3
        self._draw()
        
        # Schedule next step
        self.after(16, self._animate_step)  # ~60fps
    
    def _on_enter(self, event=None):
        """Handle mouse enter"""
        self._hover = True
        self._draw()
    
    def _on_leave(self, event=None):
        """Handle mouse leave"""
        self._hover = False
        self._draw()
    
    def get(self) -> bool:
        """Get current value"""
        return self._variable.get()
    
    def set(self, value: bool):
        """Set value"""
        self._variable.set(value)
    
    def configure(self, **kwargs):
        """Configure switch properties"""
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._disabled = state == "disabled"
            self.config(cursor="arrow" if self._disabled else "hand2")
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        
        super().configure(**kwargs)
        self._draw()
    
    def set_disabled(self, disabled: bool):
        """Enable or disable the switch"""
        self._disabled = disabled
        self.config(cursor="arrow" if disabled else "hand2")
        self._draw()
