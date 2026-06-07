"""
TabBar - A modern sidebar navigation component
"""

import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Optional, List
from ..design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION,
    get_font, blend_colors, lighten, darken, get_contrast_color, ensure_contrast,
    WCAG_AA_NORMAL, WCAG_UI_COMPONENTS
)


@dataclass
class TabItem:
    """Represents a navigation tab item"""
    key: str
    label: str
    icon: str = ""
    badge: str = ""


class TabBar(tk.Frame):
    """
    A modern vertical sidebar navigation with:
    - Animated selection indicator
    - Hover effects
    - Icon and text support
    - Badge support
    - Keyboard navigation
    """
    
    def __init__(
        self,
        parent,
        items: List[TabItem],
        on_select: Optional[Callable[[str], None]] = None,
        selected: str = None,
        width: int = SPACING.SIDEBAR_WIDTH,
        theme: dict = None,
        **kwargs
    ):
        self.theme = theme or {}
        self._items = items
        self._on_select = on_select
        self._width = width
        
        # Colors with contrast validation
        self._bg = self.theme.get("background", COLORS.SURFACE_0)
        self._item_bg = self.theme.get("accent", COLORS.SURFACE_1)
        self._item_hover = self.theme.get("button_hover", COLORS.SURFACE_2)
        self._highlight = self.theme.get("highlight", COLORS.CYAN)
        self._border = self.theme.get("border", COLORS.BORDER_DEFAULT)
        
        # Ensure text colors have proper contrast
        base_fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        self._fg = ensure_contrast(base_fg, self._bg, WCAG_AA_NORMAL)
        base_muted = self.theme.get("muted_text", COLORS.TEXT_LOW)
        self._fg_muted = ensure_contrast(base_muted, self._bg, WCAG_UI_COMPONENTS)
        # Selected text must contrast with highlight
        self._fg_selected = get_contrast_color(self._highlight)
        
        super().__init__(parent, bg=self._bg, width=width, **kwargs)
        
        # State
        self._selected = selected or (items[0].key if items else None)
        self._tab_widgets = {}
        self._hover_key = None
        
        # Build tabs
        self._build_tabs()
        
        # Bind keyboard
        self.bind("<Up>", self._nav_prev)
        self.bind("<Down>", self._nav_next)
        self.bind("<Return>", self._nav_select)
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", self._on_blur)
        
        self.focus_set()
    
    def _build_tabs(self):
        """Build tab widgets"""
        # Clear existing
        for widget in self.winfo_children():
            widget.destroy()
        self._tab_widgets = {}
        
        # Header area (optional app title/logo)
        header = tk.Frame(self, bg=self._bg, height=SPACING.XXL)
        header.pack(fill="x", pady=(SPACING.MD, SPACING.LG))
        header.pack_propagate(False)
        
        # Tabs container
        tabs_container = tk.Frame(self, bg=self._bg)
        tabs_container.pack(fill="both", expand=True, padx=SPACING.SM)
        
        for item in self._items:
            tab = self._create_tab(tabs_container, item)
            self._tab_widgets[item.key] = tab
    
    def _create_tab(self, parent, item: TabItem) -> tk.Frame:
        """Create a single tab widget"""
        is_selected = item.key == self._selected
        
        # Tab container
        tab = tk.Frame(
            parent,
            bg=self._highlight if is_selected else self._bg,
            cursor="hand2"
        )
        tab.pack(fill="x", pady=2)
        
        # Inner content with padding
        inner = tk.Frame(tab, bg=tab.cget("bg"))
        inner.pack(fill="x", padx=3, pady=3)
        
        # Content frame (icon + text)
        content = tk.Frame(inner, bg=inner.cget("bg"))
        content.pack(fill="x", padx=SPACING.MD, pady=SPACING.SM)
        
        # Icon
        if item.icon:
            icon_fg = self._fg_selected if is_selected else self._fg_muted
            icon_label = tk.Label(
                content,
                text=item.icon,
                font=get_font(TYPOGRAPHY.SIZE_MD),
                bg=content.cget("bg"),
                fg=icon_fg
            )
            icon_label.pack(side="left", padx=(0, SPACING.SM))
            icon_label.bind("<Button-1>", lambda e, k=item.key: self._select_tab(k))
            icon_label.bind("<Enter>", lambda e, k=item.key: self._on_tab_enter(k))
            icon_label.bind("<Leave>", lambda e, k=item.key: self._on_tab_leave(k))
        
        # Label
        label_fg = self._fg_selected if is_selected else self._fg
        label = tk.Label(
            content,
            text=item.label,
            font=get_font(TYPOGRAPHY.SIZE_BASE, TYPOGRAPHY.WEIGHT_BOLD if is_selected else TYPOGRAPHY.WEIGHT_NORMAL),
            bg=content.cget("bg"),
            fg=label_fg,
            anchor="w"
        )
        label.pack(side="left", fill="x", expand=True)
        label.bind("<Button-1>", lambda e, k=item.key: self._select_tab(k))
        label.bind("<Enter>", lambda e, k=item.key: self._on_tab_enter(k))
        label.bind("<Leave>", lambda e, k=item.key: self._on_tab_leave(k))
        
        # Badge with contrast-safe text
        if item.badge:
            badge_bg = COLORS.ERROR if item.badge.isdigit() else self._highlight
            badge_fg = get_contrast_color(badge_bg)
            badge = tk.Label(
                content,
                text=item.badge,
                font=get_font(TYPOGRAPHY.SIZE_XS),
                bg=badge_bg,
                fg=badge_fg,
                padx=6,
                pady=1
            )
            badge.pack(side="right")
        
        # Bind events to tab frame
        for widget in [tab, inner, content]:
            widget.bind("<Button-1>", lambda e, k=item.key: self._select_tab(k))
            widget.bind("<Enter>", lambda e, k=item.key: self._on_tab_enter(k))
            widget.bind("<Leave>", lambda e, k=item.key: self._on_tab_leave(k))
        
        # Store references for updates
        tab._label = label
        tab._icon = icon_label if item.icon else None
        tab._inner = inner
        tab._content = content
        tab._item = item
        
        return tab
    
    def _select_tab(self, key: str):
        """Select a tab by key"""
        if key == self._selected:
            return
        
        old_selected = self._selected
        self._selected = key
        
        # Update visual state
        self._update_tab_style(old_selected)
        self._update_tab_style(key)
        
        # Callback
        if self._on_select:
            self._on_select(key)
    
    def _update_tab_style(self, key: str):
        """Update a tab's visual style"""
        if key not in self._tab_widgets:
            return
        
        tab = self._tab_widgets[key]
        is_selected = key == self._selected
        is_hover = key == self._hover_key
        
        # Determine colors with proper contrast
        if is_selected:
            bg = self._highlight
            fg = self._fg_selected  # Use pre-calculated contrast color
            icon_fg = self._fg_selected
        elif is_hover:
            bg = self._item_hover
            fg = self._fg
            icon_fg = self._highlight
        else:
            bg = self._bg
            fg = self._fg
            icon_fg = self._fg_muted
        
        # Apply to all sub-widgets
        tab.config(bg=bg)
        tab._inner.config(bg=bg)
        tab._content.config(bg=bg)
        tab._label.config(
            bg=bg,
            fg=fg,
            font=get_font(TYPOGRAPHY.SIZE_BASE, TYPOGRAPHY.WEIGHT_BOLD if is_selected else TYPOGRAPHY.WEIGHT_NORMAL)
        )
        if tab._icon:
            tab._icon.config(bg=bg, fg=icon_fg)
    
    def _on_tab_enter(self, key: str):
        """Handle mouse enter on tab"""
        self._hover_key = key
        self._update_tab_style(key)
    
    def _on_tab_leave(self, key: str):
        """Handle mouse leave from tab"""
        if self._hover_key == key:
            self._hover_key = None
            self._update_tab_style(key)
    
    def _nav_prev(self, event=None):
        """Navigate to previous tab"""
        if not self._items:
            return
        
        keys = [item.key for item in self._items]
        current_idx = keys.index(self._selected) if self._selected in keys else 0
        new_idx = (current_idx - 1) % len(keys)
        self._select_tab(keys[new_idx])
    
    def _nav_next(self, event=None):
        """Navigate to next tab"""
        if not self._items:
            return
        
        keys = [item.key for item in self._items]
        current_idx = keys.index(self._selected) if self._selected in keys else 0
        new_idx = (current_idx + 1) % len(keys)
        self._select_tab(keys[new_idx])
    
    def _nav_select(self, event=None):
        """Select current tab (for keyboard nav)"""
        # Already selected, just trigger callback
        if self._on_select:
            self._on_select(self._selected)
    
    def _on_focus(self, event=None):
        """Handle focus"""
        # Could add visual focus indicator
        pass
    
    def _on_blur(self, event=None):
        """Handle blur"""
        pass
    
    def get_selected(self) -> str:
        """Get currently selected tab key"""
        return self._selected
    
    def select(self, key: str):
        """Programmatically select a tab"""
        if key in [item.key for item in self._items]:
            self._select_tab(key)
    
    def set_items(self, items: List[TabItem]):
        """Update tab items"""
        self._items = items
        if self._selected not in [item.key for item in items]:
            self._selected = items[0].key if items else None
        self._build_tabs()
    
    def set_badge(self, key: str, badge: str):
        """Update badge for a tab"""
        for item in self._items:
            if item.key == key:
                item.badge = badge
                break
        self._build_tabs()


class HorizontalTabBar(tk.Frame):
    """
    A horizontal tab bar for inline navigation
    (pill-style tabs)
    """
    
    def __init__(
        self,
        parent,
        items: List[TabItem],
        on_select: Optional[Callable[[str], None]] = None,
        selected: str = None,
        theme: dict = None,
        **kwargs
    ):
        self.theme = theme or {}
        self._items = items
        self._on_select = on_select
        
        # Colors with contrast validation
        self._bg = self.theme.get("background", COLORS.SURFACE_0)
        self._item_bg = self.theme.get("accent", COLORS.SURFACE_2)
        self._item_hover = self.theme.get("button_hover", COLORS.SURFACE_3)
        self._highlight = self.theme.get("highlight", COLORS.CYAN)
        self._border = self.theme.get("border", COLORS.BORDER_DEFAULT)
        
        # Ensure text colors have proper contrast
        base_fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        self._fg = ensure_contrast(base_fg, self._item_bg, WCAG_AA_NORMAL)
        base_muted = self.theme.get("muted_text", COLORS.TEXT_LOW)
        self._fg_muted = ensure_contrast(base_muted, self._item_bg, WCAG_UI_COMPONENTS)
        # Selected text must contrast with highlight
        self._fg_selected = get_contrast_color(self._highlight)
        
        super().__init__(parent, bg=self._bg, **kwargs)
        
        # State
        self._selected = selected or (items[0].key if items else None)
        self._tab_widgets = {}
        
        # Container with glass border
        self._shell = tk.Frame(
            self,
            bg=self._item_bg,
            highlightbackground=blend_colors(self._border, self._highlight, 0.35),
            highlightthickness=1
        )
        self._shell.pack(fill="x", padx=2, pady=2)

        self._container = tk.Frame(self._shell, bg=self._item_bg)
        self._container.pack(fill="x", padx=2, pady=2)
        
        # Build tabs
        self._build_tabs()
    
    def _build_tabs(self):
        """Build horizontal tab pills"""
        for widget in self._container.winfo_children():
            widget.destroy()
        self._tab_widgets = {}
        
        for item in self._items:
            is_selected = item.key == self._selected
            
            # Tab button with contrast-safe colors
            bg = self._highlight if is_selected else self._item_bg
            fg = self._fg_selected if is_selected else self._fg_muted
            
            tab = tk.Label(
                self._container,
                text=f"{item.icon} {item.label}".strip() if item.icon else item.label,
                font=get_font(TYPOGRAPHY.SIZE_SM, TYPOGRAPHY.WEIGHT_BOLD if is_selected else TYPOGRAPHY.WEIGHT_NORMAL),
                bg=bg,
                fg=fg,
                padx=SPACING.MD + 1,
                pady=SPACING.SM,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=blend_colors(self._border, self._highlight, 0.45 if is_selected else 0.18)
            )
            tab.pack(side="left", padx=2, pady=2)
            
            tab.bind("<Button-1>", lambda e, k=item.key: self._select_tab(k))
            tab.bind("<Enter>", lambda e, t=tab, k=item.key: self._on_enter(t, k))
            tab.bind("<Leave>", lambda e, t=tab, k=item.key: self._on_leave(t, k))
            
            self._tab_widgets[item.key] = tab
    
    def _select_tab(self, key: str):
        """Select a tab"""
        if key == self._selected:
            return
        
        self._selected = key
        self._build_tabs()
        
        if self._on_select:
            self._on_select(key)
    
    def _on_enter(self, tab: tk.Label, key: str):
        """Handle hover"""
        if key != self._selected:
            tab.config(
                bg=self._item_hover,
                fg=self._fg,
                highlightbackground=blend_colors(self._border, self._highlight, 0.35),
            )
    
    def _on_leave(self, tab: tk.Label, key: str):
        """Handle leave"""
        if key != self._selected:
            tab.config(
                bg=self._item_bg,
                fg=self._fg_muted,
                highlightbackground=blend_colors(self._border, self._highlight, 0.18),
            )
    
    def get_selected(self) -> str:
        """Get selected tab key"""
        return self._selected
    
    def select(self, key: str):
        """Select a tab programmatically"""
        if key in [item.key for item in self._items]:
            self._select_tab(key)
