"""
ModernCard - An elevated card container with hover effects
"""

import tkinter as tk
import math
from typing import Optional, Callable
from ..design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION, RADIUS,
    get_font, blend_colors, lighten, darken, ensure_contrast, get_contrast_color,
    WCAG_AA_NORMAL, WCAG_UI_COMPONENTS
)


class RoundedFrame(tk.Canvas):
    """
    A Canvas-based frame with actual rounded corners.
    
    Draws a rounded rectangle background and places an inner frame
    on top where content can be added. Lightweight and reusable.
    """
    
    def __init__(
        self,
        parent,
        radius: int = 8,
        bg_color: str = None,
        border_color: str = None,
        border_width: int = 1,
        theme: dict = None,
        padding: int = 4,
        **kwargs
    ):
        self.theme = theme or {}
        self._radius = radius
        self._bg_color = bg_color or self.theme.get("accent", COLORS.SURFACE_2)
        self._border_color = border_color or self.theme.get("border", COLORS.BORDER_DEFAULT)
        self._border_width = border_width
        self._padding = padding
        
        # Get parent background for canvas bg
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = self.theme.get("background", COLORS.BLACK)
        
        super().__init__(
            parent,
            bg=parent_bg,
            highlightthickness=0,
            **kwargs
        )
        
        # Inner frame for content
        self._inner = tk.Frame(self, bg=self._bg_color)
        self._inner_window = None
        
        # Draw on configure
        self.bind("<Configure>", self._redraw)
    
    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a smooth rounded rectangle"""
        r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _redraw(self, event=None):
        """Redraw the rounded rectangle and reposition the inner frame"""
        self.delete("bg_rect", "border_rect")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        
        pad = self._border_width
        
        # Draw border
        if self._border_color and self._border_width > 0:
            self._draw_rounded_rect(
                0, 0, w, h,
                radius=self._radius,
                fill=self._border_color,
                outline="",
                tags="border_rect"
            )
        
        # Draw background
        self._draw_rounded_rect(
            pad, pad, w - pad, h - pad,
            radius=max(1, self._radius - pad),
            fill=self._bg_color,
            outline="",
            tags="bg_rect"
        )
        
        # Place inner frame
        inner_pad = self._padding + pad
        if self._inner_window:
            self.delete(self._inner_window)
        self._inner_window = self.create_window(
            inner_pad, inner_pad,
            window=self._inner,
            anchor="nw",
            width=max(1, w - inner_pad * 2),
            height=max(1, h - inner_pad * 2),
            tags="inner"
        )
        
        # Ensure ordering: border behind bg behind inner
        self.tag_lower("border_rect")
        self.tag_lower("bg_rect", "inner")
    
    @property
    def inner(self) -> tk.Frame:
        """Get the inner frame for adding content"""
        return self._inner
    
    def set_border_color(self, color: str):
        """Update the border color"""
        self._border_color = color
        self._redraw()


class ModernCard(tk.Frame):
    """
    A modern card container widget with:
    - Elevated appearance with subtle border
    - Hover glow effect
    - Collapsible sections
    - Title and icon support
    """
    
    def __init__(
        self,
        parent,
        title: str = "",
        icon: str = "",
        collapsible: bool = False,
        collapsed: bool = False,
        theme: dict = None,
        padding: int = SPACING.CARD_PADDING,
        border_color: str = None,
        hover_glow: bool = True,
        on_collapse_change: Optional[Callable] = None,
        **kwargs
    ):
        self.theme = theme or {}
        self._title = title
        self._icon = icon
        self._collapsible = collapsible
        self._collapsed = collapsed
        self._padding = padding
        self._hover_glow = hover_glow
        self._on_collapse_change = on_collapse_change
        
        # Colors with contrast validation
        self._bg = self.theme.get("accent", COLORS.SURFACE_2)
        self._border = border_color or self.theme.get("border", COLORS.BORDER_DEFAULT)
        # Ensure text has sufficient contrast on card background
        base_fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        self._fg = ensure_contrast(base_fg, self._bg, WCAG_AA_NORMAL)
        self._highlight = self.theme.get("highlight", COLORS.CYAN)
        # Muted text for secondary content
        base_muted = self.theme.get("muted_text", COLORS.TEXT_LOW)
        self._muted = ensure_contrast(base_muted, self._bg, WCAG_UI_COMPONENTS)
        
        # Get parent background
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = self.theme.get("background", COLORS.BLACK)
        
        # Initialize frame
        super().__init__(
            parent,
            bg=parent_bg,
            **kwargs
        )
        
        # State
        self._hover = False
        
        # Create inner container with border
        self._container = tk.Frame(
            self,
            bg=self._bg,
            highlightbackground=self._border,
            highlightthickness=1,
            highlightcolor=self._border
        )
        self._container.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Create header if title provided
        if title or collapsible:
            self._create_header()
        
        # Create content area
        self._content = tk.Frame(self._container, bg=self._bg)
        if not collapsed:
            self._content.pack(fill="both", expand=True, padx=padding, pady=(0, padding))
        
        # Bind hover events
        if hover_glow:
            self._bind_hover_events()
    
    def _create_header(self):
        """Create the card header with title and collapse toggle"""
        self._header = tk.Frame(self._container, bg=self._bg)
        self._header.pack(fill="x", padx=self._padding, pady=(self._padding, self._padding // 2))
        
        # Icon and title
        title_frame = tk.Frame(self._header, bg=self._bg)
        title_frame.pack(side="left", fill="x", expand=True)
        
        if self._icon:
            icon_label = tk.Label(
                title_frame,
                text=self._icon,
                font=get_font(TYPOGRAPHY.SIZE_MD),
                bg=self._bg,
                fg=self._highlight
            )
            icon_label.pack(side="left", padx=(0, 8))
        
        if self._title:
            self._title_label = tk.Label(
                title_frame,
                text=self._title,
                font=get_font(TYPOGRAPHY.SIZE_MD, TYPOGRAPHY.WEIGHT_BOLD),
                bg=self._bg,
                fg=self._fg
            )
            self._title_label.pack(side="left")
        
        # Collapse toggle
        if self._collapsible:
            self._toggle_icon = tk.Label(
                self._header,
                text="▾" if not self._collapsed else "▸",
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=self._bg,
                fg=self._muted,
                cursor="hand2"
            )
            self._toggle_icon.pack(side="right")
            self._toggle_icon.bind("<Button-1>", self._toggle_collapse)
            
            # Make header clickable
            self._header.bind("<Button-1>", self._toggle_collapse)
            if hasattr(self, "_title_label"):
                self._title_label.bind("<Button-1>", self._toggle_collapse)
                self._title_label.config(cursor="hand2")
    
    def _toggle_collapse(self, event=None):
        """Toggle collapsed state"""
        self._collapsed = not self._collapsed
        
        if self._collapsed:
            self._content.pack_forget()
            self._toggle_icon.config(text="▸")
        else:
            self._content.pack(fill="both", expand=True, padx=self._padding, pady=(0, self._padding))
            self._toggle_icon.config(text="▾")
        
        if self._on_collapse_change:
            self._on_collapse_change(self._collapsed)
    
    def _bind_hover_events(self):
        """Bind hover events to all child widgets"""
        def on_enter(event=None):
            self._hover = True
            self._update_hover_style()
        
        def on_leave(event=None):
            self._hover = False
            self._update_hover_style()
        
        # Bind to container and all children
        widgets = [self, self._container]
        if hasattr(self, "_header"):
            widgets.append(self._header)
        if hasattr(self, "_content"):
            widgets.append(self._content)
        
        for widget in widgets:
            widget.bind("<Enter>", on_enter, add="+")
            widget.bind("<Leave>", on_leave, add="+")
    
    def _update_hover_style(self):
        """Update border color on hover"""
        if self._hover:
            border_color = lighten(self._highlight, 0.3)
            self._container.config(
                highlightbackground=border_color,
                highlightcolor=border_color
            )
        else:
            self._container.config(
                highlightbackground=self._border,
                highlightcolor=self._border
            )
    
    @property
    def content(self) -> tk.Frame:
        """Get the content frame for adding widgets"""
        return self._content
    
    def set_title(self, title: str):
        """Update card title"""
        self._title = title
        if hasattr(self, "_title_label"):
            self._title_label.config(text=title)
    
    def is_collapsed(self) -> bool:
        """Check if card is collapsed"""
        return self._collapsed
    
    def expand(self):
        """Expand the card"""
        if self._collapsed:
            self._toggle_collapse()
    
    def collapse(self):
        """Collapse the card"""
        if not self._collapsed:
            self._toggle_collapse()


class SettingsCard(ModernCard):
    """
    A specialized card for settings sections with:
    - Consistent styling
    - Description support
    - Built-in row layout helper
    """
    
    def __init__(
        self,
        parent,
        title: str = "",
        icon: str = "",
        description: str = "",
        theme: dict = None,
        **kwargs
    ):
        super().__init__(
            parent,
            title=title,
            icon=icon,
            theme=theme,
            collapsible=True,
            **kwargs
        )
        
        self._description = description
        
        # Add description if provided
        if description:
            self._desc_label = tk.Label(
                self._content,
                text=description,
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=self._bg,
                fg=self._muted,
                wraplength=400,
                justify="left",
                anchor="w"
            )
            self._desc_label.pack(fill="x", pady=(0, SPACING.MD))
    
    def add_row(
        self,
        label: str,
        widget: tk.Widget = None,
        description: str = "",
        fill_widget: bool = True
    ) -> tk.Frame:
        """
        Add a settings row with label and optional widget
        Returns the row frame for adding custom widgets
        """
        row = tk.Frame(self._content, bg=self._bg)
        row.pack(fill="x", pady=SPACING.SM)
        
        # Left side - label and description
        left = tk.Frame(row, bg=self._bg)
        left.pack(side="left", fill="y")
        
        label_widget = tk.Label(
            left,
            text=label,
            font=get_font(TYPOGRAPHY.SIZE_BASE),
            bg=self._bg,
            fg=self._fg,
            anchor="w"
        )
        label_widget.pack(anchor="w")
        
        if description:
            desc = tk.Label(
                left,
                text=description,
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=self._bg,
                fg=self._muted,
                anchor="w"
            )
            desc.pack(anchor="w")
        
        # Right side - widget
        if widget:
            if fill_widget:
                widget.pack(side="right", fill="x", expand=True, padx=(SPACING.XL, 0))
            else:
                widget.pack(side="right", padx=(SPACING.XL, 0))
        
        return row
    
    def add_separator(self):
        """Add a horizontal separator line"""
        sep = tk.Frame(
            self._content,
            bg=self._border,
            height=1
        )
        sep.pack(fill="x", pady=SPACING.MD)


class InfoCard(tk.Frame):
    """A simple info/notification card with WCAG-compliant colors"""
    
    VARIANTS = {
        "info": {"bg": COLORS.INFO_BG, "border": COLORS.INFO, "icon": "ℹ️", "fg": COLORS.TEXT_PRIMARY},
        "success": {"bg": COLORS.SUCCESS_BG, "border": COLORS.SUCCESS, "icon": "✓", "fg": COLORS.TEXT_PRIMARY},
        "warning": {"bg": COLORS.WARNING_BG, "border": COLORS.WARNING, "icon": "⚠️", "fg": COLORS.TEXT_PRIMARY},
        "error": {"bg": COLORS.ERROR_BG, "border": COLORS.ERROR, "icon": "✕", "fg": COLORS.TEXT_PRIMARY},
    }
    
    def __init__(
        self,
        parent,
        message: str,
        variant: str = "info",
        dismissible: bool = False,
        on_dismiss: Optional[Callable] = None,
        theme: dict = None,
        **kwargs
    ):
        self.theme = theme or {}
        self._on_dismiss = on_dismiss
        
        v = self.VARIANTS.get(variant, self.VARIANTS["info"])
        bg = v["bg"]
        border = v["border"]
        icon = v["icon"]
        
        # Ensure text contrast on the variant background
        fg = ensure_contrast(v.get("fg", COLORS.TEXT_PRIMARY), bg, WCAG_AA_NORMAL)
        muted_fg = ensure_contrast(COLORS.TEXT_LOW, bg, WCAG_UI_COMPONENTS)
        
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = COLORS.BLACK
        
        super().__init__(parent, bg=parent_bg, **kwargs)
        
        # Container with border
        container = tk.Frame(
            self,
            bg=bg,
            highlightbackground=border,
            highlightthickness=1
        )
        container.pack(fill="x", padx=2, pady=2)
        
        # Content
        content = tk.Frame(container, bg=bg)
        content.pack(fill="x", padx=SPACING.MD, pady=SPACING.SM)
        
        # Icon
        icon_label = tk.Label(
            content,
            text=icon,
            font=get_font(TYPOGRAPHY.SIZE_BASE),
            bg=bg,
            fg=border
        )
        icon_label.pack(side="left", padx=(0, SPACING.SM))
        
        # Message
        msg_label = tk.Label(
            content,
            text=message,
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=bg,
            fg=fg,
            wraplength=400,
            justify="left",
            anchor="w"
        )
        msg_label.pack(side="left", fill="x", expand=True)
        
        # Dismiss button
        if dismissible:
            dismiss_btn = tk.Label(
                content,
                text="✕",
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=bg,
                fg=muted_fg,
                cursor="hand2"
            )
            dismiss_btn.pack(side="right", padx=(SPACING.SM, 0))
            dismiss_btn.bind("<Button-1>", self._dismiss)
    
    def _dismiss(self, event=None):
        """Dismiss the card"""
        if self._on_dismiss:
            self._on_dismiss()
        self.destroy()
