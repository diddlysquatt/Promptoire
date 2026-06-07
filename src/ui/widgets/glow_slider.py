"""
GlowSlider - A modern slider with neon glow effects
"""

import tkinter as tk
from typing import Callable, Optional, Union
from ..design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION,
    get_font, blend_colors, lighten, darken, ensure_contrast,
    WCAG_AA_NORMAL
)


class GlowSlider(tk.Canvas):
    """
    A modern slider widget with:
    - Neon glowing track
    - Animated thumb with glow
    - Value display
    - Step support
    - Custom colors
    """
    
    def __init__(
        self,
        parent,
        variable: Optional[tk.DoubleVar] = None,
        from_: float = 0.0,
        to: float = 100.0,
        step: float = 1.0,
        command: Optional[Callable] = None,
        width: int = 200,
        height: int = 32,
        show_value: bool = True,
        value_format: str = "{:.0f}",
        suffix: str = "",
        track_color: str = None,
        active_color: str = None,
        theme: dict = None,
        disabled: bool = False,
        **kwargs
    ):
        self.parent = parent
        self.from_ = from_
        self.to = to
        self.step = step
        self.command = command
        self._width = width
        self._height = height
        self.show_value = show_value
        self.value_format = value_format
        self.suffix = suffix
        self.theme = theme or {}
        self._disabled = disabled
        
        # Create variable if not provided
        if variable is None:
            self._variable = tk.DoubleVar(value=from_)
        else:
            self._variable = variable
        
        # Colors
        self._track_color = track_color or self.theme.get("accent", COLORS.SURFACE_2)
        self._active_color = active_color or self.theme.get("highlight", COLORS.CYAN)
        self._thumb_color = COLORS.TEXT_PRIMARY
        self._glow_color = self.theme.get("glow_color", COLORS.CYAN_GLOW)
        
        # Geometry
        self._track_height = 6
        self._thumb_radius = 7
        self._padding = self._thumb_radius + 4
        
        # State
        self._hover = False
        self._dragging = False
        self._last_draw_time = 0  # Throttle redraws during drag
        
        # Get parent background
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = self.theme.get("background", COLORS.BLACK)
        
        # Initialize canvas
        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            bg=parent_bg,
            highlightthickness=0,
            cursor="hand2" if not disabled else "arrow",
            **kwargs
        )
        
        # Draw initial state
        self._draw()
        
        # Bind events
        if not disabled:
            self.bind("<Button-1>", self._on_click)
            self.bind("<B1-Motion>", self._on_drag)
            self.bind("<ButtonRelease-1>", self._on_release)
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<MouseWheel>", self._on_scroll)
        
        # Watch for variable changes
        self._variable.trace_add("write", self._on_variable_change)
    
    def _value_to_x(self, value: float) -> float:
        """Convert value to X position"""
        range_val = self.to - self.from_
        if range_val == 0:
            return self._padding
        ratio = (value - self.from_) / range_val
        track_width = self._width - (self._padding * 2)
        return self._padding + (ratio * track_width)
    
    def _x_to_value(self, x: float) -> float:
        """Convert X position to value"""
        track_width = self._width - (self._padding * 2)
        ratio = max(0, min(1, (x - self._padding) / track_width))
        raw_value = self.from_ + (ratio * (self.to - self.from_))
        
        # Snap to step
        if self.step > 0:
            steps = round((raw_value - self.from_) / self.step)
            raw_value = self.from_ + (steps * self.step)
        
        return max(self.from_, min(self.to, raw_value))
    
    def _draw(self):
        """Draw the slider"""
        self.delete("all")
        
        value = self._variable.get()
        thumb_x = self._value_to_x(value)
        track_y = self._height // 2
        
        # Colors
        if self._disabled:
            track_color = COLORS.SURFACE_2
            active_color = COLORS.TEXT_DISABLED
            thumb_color = COLORS.TEXT_DISABLED
        else:
            track_color = self._track_color
            active_color = self._active_color
            thumb_color = self._thumb_color
        
        # Draw track background
        self._draw_rounded_rect(
            self._padding, track_y - self._track_height // 2,
            self._width - self._padding, track_y + self._track_height // 2,
            radius=self._track_height // 2,
            fill=track_color,
            outline=""
        )
        
        # Draw active track with glow
        if not self._disabled and (self._hover or self._dragging):
            # Glow effect
            for i in range(3):
                expand = 3 - i
                glow_alpha = 0.1 * (3 - i)
                self._draw_rounded_rect(
                    self._padding - expand, track_y - self._track_height // 2 - expand,
                    thumb_x + expand, track_y + self._track_height // 2 + expand,
                    radius=(self._track_height // 2) + expand,
                    fill="",
                    outline=blend_colors(active_color, COLORS.TEXT_PRIMARY, glow_alpha)
                )
        
        # Draw active portion of track
        if thumb_x > self._padding:
            self._draw_rounded_rect(
                self._padding, track_y - self._track_height // 2,
                thumb_x, track_y + self._track_height // 2,
                radius=self._track_height // 2,
                fill=active_color,
                outline=""
            )
        
        # Draw thumb glow
        if not self._disabled and (self._hover or self._dragging):
            glow_radius = self._thumb_radius + 6
            self.create_oval(
                thumb_x - glow_radius, track_y - glow_radius,
                thumb_x + glow_radius, track_y + glow_radius,
                fill="",
                outline=blend_colors(active_color, COLORS.TEXT_PRIMARY, 0.15),
                width=2
            )
        
        # Draw thumb shadow
        if not self._disabled:
            self.create_oval(
                thumb_x - self._thumb_radius + 1, track_y - self._thumb_radius + 1,
                thumb_x + self._thumb_radius + 1, track_y + self._thumb_radius + 1,
                fill=COLORS.BLACK,
                outline=""
            )
        
        # Draw thumb
        self.create_oval(
            thumb_x - self._thumb_radius, track_y - self._thumb_radius,
            thumb_x + self._thumb_radius, track_y + self._thumb_radius,
            fill=thumb_color,
            outline=active_color if (self._hover or self._dragging) and not self._disabled else "",
            width=2
        )
        
        # Draw value label with contrast validation
        if self.show_value:
            formatted_value = self.value_format.format(value) + self.suffix
            # Get parent background for contrast check
            try:
                parent_bg = self.parent.cget("bg")
            except Exception:
                parent_bg = self.theme.get("background", COLORS.SURFACE_0)
            
            if self._disabled:
                fg = COLORS.TEXT_DISABLED
            else:
                base_fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
                fg = ensure_contrast(base_fg, parent_bg, WCAG_AA_NORMAL)
            
            self.create_text(
                self._width - 5, track_y,
                text=formatted_value,
                font=get_font(TYPOGRAPHY.SIZE_SM),
                fill=fg,
                anchor="e"
            )
    
    def _draw_rounded_rect(self, x1, y1, x2, y2, radius=3, **kwargs):
        """Draw a rounded rectangle"""
        if x2 <= x1 or y2 <= y1:
            return
        
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _on_click(self, event):
        """Handle click on track"""
        if self._disabled:
            return
        
        value = self._x_to_value(event.x)
        self._variable.set(value)
        self._dragging = True
        self._draw()
        
        if self.command:
            self.command(value)
    
    def _on_drag(self, event):
        """Handle drag with 16ms throttle for performance"""
        if self._disabled or not self._dragging:
            return
        
        import time
        now = time.monotonic()
        if now - self._last_draw_time < 0.016:  # 16ms throttle (~60fps)
            return
        self._last_draw_time = now
        
        value = self._x_to_value(event.x)
        self._variable.set(value)
        self._draw()
        
        if self.command:
            self.command(value)
    
    def _on_release(self, event):
        """Handle release"""
        self._dragging = False
        self._draw()
    
    def _on_enter(self, event):
        """Handle mouse enter"""
        self._hover = True
        self._draw()
    
    def _on_leave(self, event):
        """Handle mouse leave"""
        self._hover = False
        if not self._dragging:
            self._draw()
    
    def _on_scroll(self, event):
        """Handle mouse wheel"""
        if self._disabled:
            return "break"
        
        # Determine scroll direction
        delta = 1 if event.delta > 0 else -1
        current = self._variable.get()
        new_value = current + (delta * self.step)
        new_value = max(self.from_, min(self.to, new_value))
        
        self._variable.set(new_value)
        self._draw()
        
        if self.command:
            self.command(new_value)
        
        return "break"  # Prevent parent scroll
    
    def _on_variable_change(self, *args):
        """Handle variable change from outside"""
        self._draw()
    
    def get(self) -> float:
        """Get current value"""
        return self._variable.get()
    
    def set(self, value: float):
        """Set value"""
        value = max(self.from_, min(self.to, value))
        self._variable.set(value)
    
    def configure(self, **kwargs):
        """Configure slider properties"""
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._disabled = state == "disabled"
            self.config(cursor="arrow" if self._disabled else "hand2")
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "from_" in kwargs:
            self.from_ = kwargs.pop("from_")
        if "to" in kwargs:
            self.to = kwargs.pop("to")
        
        super().configure(**kwargs)
        self._draw()
    
    def set_disabled(self, disabled: bool):
        """Enable or disable the slider"""
        self._disabled = disabled
        self.config(cursor="arrow" if disabled else "hand2")
        self._draw()


class StepperSlider(tk.Frame):
    """A slider with +/- buttons for fine control"""
    
    def __init__(
        self,
        parent,
        variable: Optional[tk.DoubleVar] = None,
        from_: float = 0.0,
        to: float = 100.0,
        step: float = 1.0,
        command: Optional[Callable] = None,
        width: int = 180,
        show_value: bool = True,
        value_format: str = "{:.0f}",
        suffix: str = "",
        theme: dict = None,
        disabled: bool = False,
        **kwargs
    ):
        self.theme = theme or {}
        bg = self.theme.get("background", COLORS.BLACK)
        
        super().__init__(parent, bg=bg, **kwargs)
        
        self._variable = variable or tk.DoubleVar(value=from_)
        self.from_ = from_
        self.to = to
        self.step = step
        self.command = command
        self._disabled = disabled
        
        # Button colors with contrast validation
        btn_bg = self.theme.get("accent", COLORS.SURFACE_3)
        base_fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        btn_fg = ensure_contrast(base_fg, btn_bg, WCAG_AA_NORMAL)
        btn_hover = self.theme.get("button_hover", COLORS.SURFACE_4)
        
        # Minus button
        self._minus_btn = tk.Button(
            self,
            text="−",
            font=get_font(TYPOGRAPHY.SIZE_LG, TYPOGRAPHY.WEIGHT_BOLD),
            bg=btn_bg,
            fg=btn_fg,
            activebackground=btn_hover,
            activeforeground=btn_fg,
            relief="flat",
            width=2,
            cursor="hand2",
            command=self._decrement
        )
        self._minus_btn.pack(side="left", padx=(0, 4))
        
        # Slider
        self._slider = GlowSlider(
            self,
            variable=self._variable,
            from_=from_,
            to=to,
            step=step,
            command=self._on_slider_change,
            width=width,
            show_value=show_value,
            value_format=value_format,
            suffix=suffix,
            theme=theme,
            disabled=disabled
        )
        self._slider.pack(side="left", fill="x", expand=True)
        
        # Plus button
        self._plus_btn = tk.Button(
            self,
            text="+",
            font=get_font(TYPOGRAPHY.SIZE_LG, TYPOGRAPHY.WEIGHT_BOLD),
            bg=btn_bg,
            fg=btn_fg,
            activebackground=btn_hover,
            activeforeground=btn_fg,
            relief="flat",
            width=2,
            cursor="hand2",
            command=self._increment
        )
        self._plus_btn.pack(side="left", padx=(4, 0))
        
        # Bind hover effects
        for btn in [self._minus_btn, self._plus_btn]:
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=btn_hover))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=btn_bg))
    
    def _increment(self):
        """Increase value by step"""
        if self._disabled:
            return
        current = self._variable.get()
        new_value = min(self.to, current + self.step)
        self._variable.set(new_value)
        if self.command:
            self.command(new_value)
    
    def _decrement(self):
        """Decrease value by step"""
        if self._disabled:
            return
        current = self._variable.get()
        new_value = max(self.from_, current - self.step)
        self._variable.set(new_value)
        if self.command:
            self.command(new_value)
    
    def _on_slider_change(self, value):
        """Handle slider change"""
        if self.command:
            self.command(value)
    
    def get(self) -> float:
        """Get current value"""
        return self._variable.get()
    
    def set(self, value: float):
        """Set value"""
        self._slider.set(value)
    
    def set_disabled(self, disabled: bool):
        """Enable or disable"""
        self._disabled = disabled
        self._slider.set_disabled(disabled)
        state = "disabled" if disabled else "normal"
        self._minus_btn.config(state=state)
        self._plus_btn.config(state=state)
