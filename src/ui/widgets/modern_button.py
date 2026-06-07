"""
ModernButton - A sleek, animated button with glow effects
"""

import tkinter as tk
from typing import Callable, Optional
from ..design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION,
    get_font, blend_colors, lighten, darken, get_contrast_color, ensure_contrast,
    WCAG_AA_NORMAL, get_scaled_spacing
)


class ModernButton(tk.Canvas):
    """
    A modern button widget with:
    - Gradient backgrounds
    - Glow effect on hover
    - Press animation (scale down)
    - Icon support
    - Multiple variants (primary, secondary, danger, ghost)
    - WCAG AA compliant text contrast
    """
    
    # Variants use ON_* colors for guaranteed contrast
    VARIANTS = {
        "primary": {
            "bg": COLORS.CYAN,
            "hover_bg": COLORS.CYAN_DIM,
            "pressed_bg": darken(COLORS.CYAN_DIM, 0.1),
            "fg": COLORS.ON_CYAN,  # Guaranteed contrast on cyan
            "glow": COLORS.CYAN_GLOW,
        },
        "secondary": {
            "bg": COLORS.SURFACE_3,
            "hover_bg": COLORS.SURFACE_4,
            "pressed_bg": COLORS.SURFACE_2,
            "fg": COLORS.TEXT_PRIMARY,
            "glow": None,
        },
        "danger": {
            "bg": COLORS.ERROR,
            "hover_bg": lighten(COLORS.ERROR, 0.1),
            "pressed_bg": darken(COLORS.ERROR, 0.1),
            "fg": COLORS.ON_ERROR,  # White on red
            "glow": "#ef444440",
        },
        "success": {
            "bg": COLORS.SUCCESS,
            "hover_bg": COLORS.GREEN_DIM,
            "pressed_bg": darken(COLORS.GREEN_DIM, 0.1),
            "fg": COLORS.ON_SUCCESS,  # Black on green
            "glow": COLORS.GREEN_GLOW,
        },
        "warning": {
            "bg": COLORS.WARNING,
            "hover_bg": COLORS.YELLOW_DIM,
            "pressed_bg": darken(COLORS.YELLOW_DIM, 0.1),
            "fg": COLORS.ON_WARNING,  # Black on yellow
            "glow": COLORS.YELLOW_GLOW,
        },
        "ghost": {
            "bg": "transparent",
            "hover_bg": COLORS.SURFACE_2,
            "pressed_bg": COLORS.SURFACE_3,
            "fg": COLORS.TEXT_PRIMARY,
            "glow": None,
        },
        "purple": {
            "bg": COLORS.PURPLE,
            "hover_bg": COLORS.PURPLE_DIM,
            "pressed_bg": darken(COLORS.PURPLE_DIM, 0.1),
            "fg": COLORS.ON_PURPLE,  # Black on purple
            "glow": COLORS.PURPLE_GLOW,
        },
    }
    
    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable] = None,
        variant: str = "secondary",
        icon: Optional[str] = None,
        width: Optional[int] = None,
        height: int = 32,
        font_size: int = TYPOGRAPHY.SIZE_BASE,
        font_weight: str = TYPOGRAPHY.WEIGHT_NORMAL,
        theme: dict = None,
        disabled: bool = False,
        **kwargs
    ):
        self.parent = parent
        self.text = text
        self.command = command
        self.icon = icon
        self.font_size = font_size
        self.font_weight = font_weight
        self.theme = theme or {}
        self._disabled = disabled
        
        # Get variant colors
        self._setup_variant(variant)
        
        # Calculate dimensions
        self._height = height
        self._padding_x = int(get_scaled_spacing(SPACING.BUTTON_PADDING_X))
        self._padding_y = int(get_scaled_spacing(SPACING.BUTTON_PADDING_Y))
        
        # Create font and calculate text width
        self._font = get_font(font_size, font_weight)
        self._calculate_dimensions(width)
        
        # Animation state
        self._hover = False
        self._pressed = False
        self._animation_id = None
        
        # Initialize canvas
        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            bg=self._get_parent_bg(),
            highlightthickness=0,
            cursor="hand2" if not disabled else "arrow",
            **kwargs
        )
        
        # Draw button
        self._draw()
        
        # Bind events
        if not disabled:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<Button-1>", self._on_press)
            self.bind("<ButtonRelease-1>", self._on_release)
    
    def _setup_variant(self, variant: str):
        """Setup colors based on variant with contrast validation"""
        v = self.VARIANTS.get(variant, self.VARIANTS["secondary"])
        
        # Allow theme override for non-semantic variants
        if self.theme and variant in ("secondary", "ghost"):
            self._bg = self.theme.get("button_bg", v["bg"])
            self._hover_bg = self.theme.get("button_hover", v["hover_bg"])
            # Ensure text contrast on button background
            base_fg = self.theme.get("foreground", v["fg"])
            self._fg = ensure_contrast(base_fg, self._bg, WCAG_AA_NORMAL)
            self._glow = self.theme.get("glow_color", v["glow"])
        elif self.theme and variant == "primary":
            # Primary uses highlight color from theme
            self._bg = self.theme.get("highlight", v["bg"])
            self._hover_bg = darken(self._bg, 0.1)
            # Always get contrast color for primary buttons
            self._fg = get_contrast_color(self._bg)
            self._glow = self.theme.get("glow_color", v["glow"]) or f"{self._bg}40"
        else:
            # Use variant defaults for semantic buttons (danger, success, warning)
            self._bg = v["bg"]
            self._hover_bg = v["hover_bg"]
            self._fg = v["fg"]
            self._glow = v["glow"]
        
        self._pressed_bg = v.get("pressed_bg", darken(self._bg, 0.15))
        self._variant = variant
    
    def _get_parent_bg(self) -> str:
        """Get parent background color"""
        try:
            return self.parent.cget("bg")
        except Exception:
            return self.theme.get("background", COLORS.BLACK)
    
    def _calculate_dimensions(self, width: Optional[int]):
        """Calculate button dimensions based on content"""
        if width:
            self._width = width
        else:
            # Estimate text width (rough calculation)
            text_width = len(self.text) * (self.font_size * 0.6)
            icon_width = 20 if self.icon else 0
            icon_gap = 8 if self.icon and self.text else 0
            self._width = int(text_width + icon_width + icon_gap + (self._padding_x * 2))
            self._width = max(self._width, 60)  # Minimum width
    
    def _draw(self):
        """Draw the button"""
        self.delete("all")
        
        # Get current background color
        if self._pressed:
            bg = self._pressed_bg
        elif self._hover:
            bg = self._hover_bg
        else:
            bg = self._bg
        
        if self._disabled:
            bg = COLORS.SURFACE_2
            self._current_fg = COLORS.TEXT_DISABLED
        else:
            self._current_fg = self._fg
        
        # Handle transparent background
        if bg == "transparent":
            bg = self._get_parent_bg()
        
        # Draw glow effect on hover
        if self._hover and self._glow and not self._disabled:
            self._draw_glow(bg)
        
        # Draw rounded rectangle background
        self._draw_rounded_rect(
            2, 2, self._width - 2, self._height - 2,
            radius=8,
            fill=bg,
            outline=""
        )
        
        # Draw subtle border
        border_color = lighten(bg, 0.15) if self._hover else blend_colors(bg, COLORS.BORDER_DEFAULT, 0.5)
        self._draw_rounded_rect(
            2, 2, self._width - 2, self._height - 2,
            radius=8,
            fill="",
            outline=border_color,
            width=1
        )
        
        # Calculate content position
        content_x = self._width // 2
        content_y = self._height // 2
        
        # Draw icon and text
        if self.icon and self.text:
            # Icon + text
            icon_x = content_x - (len(self.text) * self.font_size * 0.3) - 4
            self.create_text(
                icon_x, content_y,
                text=self.icon,
                font=get_font(self.font_size + 2),
                fill=self._current_fg,
                anchor="center",
                tags="content"
            )
            text_x = icon_x + 16
            self.create_text(
                text_x, content_y,
                text=self.text,
                font=self._font,
                fill=self._current_fg,
                anchor="w",
                tags="content"
            )
        elif self.icon:
            # Icon only
            self.create_text(
                content_x, content_y,
                text=self.icon,
                font=get_font(self.font_size + 2),
                fill=self._current_fg,
                anchor="center",
                tags="content"
            )
        else:
            # Text only
            self.create_text(
                content_x, content_y,
                text=self.text,
                font=self._font,
                fill=self._current_fg,
                anchor="center",
                tags="content"
            )
    
    def _draw_glow(self, bg: str):
        """Draw glow effect behind button"""
        glow_color = self._glow or f"{bg}40"
        # Multiple layers for soft glow
        for i, offset in enumerate([6, 4, 2]):
            alpha = 0.1 - (i * 0.03)
            self._draw_rounded_rect(
                2 - offset, 2 - offset,
                self._width - 2 + offset, self._height - 2 + offset,
                radius=10 + offset,
                fill="",
                outline=blend_colors(bg, COLORS.TEXT_PRIMARY, alpha),
                width=2
            )
    
    def _draw_rounded_rect(self, x1, y1, x2, y2, radius=6, **kwargs):
        """Draw a rounded rectangle"""
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
    
    def _on_enter(self, event=None):
        """Handle mouse enter"""
        self._hover = True
        self._draw()
    
    def _on_leave(self, event=None):
        """Handle mouse leave"""
        self._hover = False
        self._pressed = False
        self._draw()
    
    def _on_press(self, event=None):
        """Handle button press"""
        if self._disabled:
            return
        self._pressed = True
        self._draw()
        # Scale down animation
        self._animate_scale(0.97)
    
    def _on_release(self, event=None):
        """Handle button release"""
        if self._disabled:
            return
        self._pressed = False
        self._draw()
        # Scale back
        self._animate_scale(1.0)
        # Execute command
        if self.command and self._hover:
            self.command()
    
    def _animate_scale(self, target_scale: float):
        """Animate scale (simplified - just visual feedback)"""
        # For tkinter, we simulate scale with a brief visual change
        # Full scale animation would require more complex canvas manipulation
        pass
    
    def configure(self, **kwargs):
        """Configure button properties"""
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._disabled = state == "disabled"
            self.config(cursor="arrow" if self._disabled else "hand2")
        
        super().configure(**kwargs)
        self._draw()
    
    def set_text(self, text: str):
        """Update button text"""
        self.text = text
        self._draw()
    
    def set_disabled(self, disabled: bool):
        """Enable or disable the button"""
        self._disabled = disabled
        self.config(cursor="arrow" if disabled else "hand2")
        self._draw()


class IconButton(ModernButton):
    """A compact circular icon button"""
    
    def __init__(
        self,
        parent,
        icon: str,
        command: Optional[Callable] = None,
        size: int = 32,
        variant: str = "ghost",
        tooltip: str = "",
        theme: dict = None,
        **kwargs
    ):
        self.tooltip_text = tooltip
        self._tooltip_window = None
        
        super().__init__(
            parent,
            text="",
            command=command,
            variant=variant,
            icon=icon,
            width=size,
            height=size,
            theme=theme,
            **kwargs
        )
        
        if tooltip:
            self.bind("<Enter>", self._show_tooltip)
            self.bind("<Leave>", self._hide_tooltip)
    
    def _draw(self):
        """Draw circular icon button"""
        self.delete("all")
        
        # Get current background color
        if self._pressed:
            bg = self._pressed_bg
        elif self._hover:
            bg = self._hover_bg
        else:
            bg = self._bg
        
        if bg == "transparent":
            bg = self._get_parent_bg()
        
        if self._disabled:
            bg = COLORS.SURFACE_2
            fg = COLORS.TEXT_DISABLED
        else:
            fg = self._fg
        
        # Draw circular background
        padding = 2
        self.create_oval(
            padding, padding,
            self._width - padding, self._height - padding,
            fill=bg,
            outline=lighten(bg, 0.1) if self._hover else "",
            width=1
        )
        
        # Draw icon
        self.create_text(
            self._width // 2, self._height // 2,
            text=self.icon,
            font=get_font(self.font_size + 2),
            fill=fg,
            anchor="center"
        )
    
    def _show_tooltip(self, event=None):
        """Show tooltip on hover"""
        if not self.tooltip_text:
            return
        
        super()._on_enter(event)

        self._tooltip_window = tk.Toplevel(self)
        self._tooltip_window.wm_overrideredirect(True)
        
        bg = COLORS.SURFACE_3
        fg = COLORS.TEXT_PRIMARY
        
        label = tk.Label(
            self._tooltip_window,
            text=self.tooltip_text,
            bg=bg,
            fg=fg,
            font=get_font(TYPOGRAPHY.SIZE_SM),
            padx=8,
            pady=4,
            relief="flat",
            highlightbackground=COLORS.BORDER_DEFAULT,
            highlightthickness=1
        )
        label.pack()

        self._tooltip_window.update_idletasks()
        tw_w = self._tooltip_window.winfo_reqwidth()
        tw_h = self._tooltip_window.winfo_reqheight()
        pointer_x = self.winfo_pointerx()
        pointer_y = self.winfo_pointery()

        # Prefer above-left placement so tooltip doesn't spawn under the cursor.
        x = self.winfo_rootx() - 10
        y = self.winfo_rooty() - tw_h - 10
        x = min(x, pointer_x - tw_w - 14)
        y = min(y, pointer_y - tw_h - 14)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if x + tw_w > screen_w:
            x = screen_w - tw_w - 5
        if x < 5:
            x = 5
        if y < 5:
            y = min(screen_h - tw_h - 5, self.winfo_rooty() + self._height + 8)
        if y + tw_h > screen_h:
            y = max(5, self.winfo_rooty() - tw_h - 2)

        self._tooltip_window.wm_geometry(f"+{x}+{y}")
    
    def _hide_tooltip(self, event=None):
        """Hide tooltip"""
        super()._on_leave(event)
        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None
