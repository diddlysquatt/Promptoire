"""
Drawer Styles - Modern styling utilities for the main prompt drawer
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable

from .design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION, RADIUS,
    get_font, get_mono_font, blend_colors, lighten, darken,
    get_contrast_color, ensure_contrast, WCAG_AA_NORMAL, WCAG_UI_COMPONENTS
)


class DrawerStyles:
    """
    Provides modern styling utilities for the main drawer UI.
    Apply these styles to transform the drawer appearance.
    """
    
    def __init__(self, theme: dict = None):
        """Initialize with theme colors"""
        self.theme = theme or {}
        self._setup_colors()
    
    def _setup_colors(self):
        """Setup color variables from theme with contrast validation"""
        self.bg = self.theme.get("background", COLORS.SURFACE_0)
        self.accent = self.theme.get("accent", COLORS.SURFACE_1)
        self.highlight = self.theme.get("highlight", COLORS.CYAN)
        self.border = self.theme.get("border", COLORS.BORDER_DEFAULT)
        self.button_bg = self.theme.get("button_bg", COLORS.SURFACE_3)
        self.button_hover = self.theme.get("button_hover", COLORS.SURFACE_4)
        
        # Ensure text colors meet contrast requirements
        base_fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        self.fg = ensure_contrast(base_fg, self.bg, WCAG_AA_NORMAL)
        
        base_muted = self.theme.get("muted_text", COLORS.TEXT_LOW)
        self.muted = ensure_contrast(base_muted, self.bg, WCAG_UI_COMPONENTS)
        
        # Text on highlight backgrounds
        self.highlight_text = get_contrast_color(self.highlight)
        
        # Computed colors
        self.card_bg = blend_colors(self.bg, self.accent, 0.15)
        self.header_bg = blend_colors(self.bg, self.accent, 0.08)
        self.search_bg = blend_colors(self.bg, self.accent, 0.20)
        self.glow = f"{self.highlight}30"
        
        # Ensure text is readable on computed backgrounds
        self.card_fg = ensure_contrast(self.fg, self.card_bg, WCAG_AA_NORMAL)
        self.search_fg = ensure_contrast(self.fg, self.search_bg, WCAG_AA_NORMAL)
    
    def style_drawer(self, drawer: tk.Toplevel):
        """Apply base styling to drawer window"""
        drawer.configure(bg=self.bg)
        
        # Remove window decorations for sleek look
        try:
            drawer.overrideredirect(True)
        except Exception:
            pass
    
    def create_header(self, parent: tk.Widget, title: str = "Promptoire",
                      on_close: Callable = None) -> tk.Frame:
        """
        Create a modern styled header for the drawer.
        
        Returns the header frame.
        """
        header = tk.Frame(parent, bg=self.header_bg)
        header.pack(fill="x", pady=(0, 1))
        
        # Inner container with padding
        inner = tk.Frame(header, bg=self.header_bg)
        inner.pack(fill="x", padx=SPACING.MD, pady=SPACING.SM)
        
        # Title with glow effect
        title_frame = tk.Frame(inner, bg=self.header_bg)
        title_frame.pack(side="left")
        
        # Accent bar
        accent_bar = tk.Frame(title_frame, bg=self.highlight, width=3)
        accent_bar.pack(side="left", fill="y", padx=(0, SPACING.SM))
        
        title_label = tk.Label(
            title_frame,
            text=title,
            font=get_font(TYPOGRAPHY.SIZE_MD, TYPOGRAPHY.WEIGHT_BOLD),
            bg=self.header_bg,
            fg=self.fg
        )
        title_label.pack(side="left")
        
        # Close button (if callback provided)
        if on_close:
            close_btn = tk.Label(
                inner,
                text="✕",
                font=get_font(TYPOGRAPHY.SIZE_BASE),
                bg=self.header_bg,
                fg=self.muted,
                cursor="hand2"
            )
            close_btn.pack(side="right")
            close_btn.bind("<Button-1>", lambda e: on_close())
            close_btn.bind("<Enter>", lambda e: close_btn.config(fg=COLORS.ERROR))
            close_btn.bind("<Leave>", lambda e: close_btn.config(fg=self.muted))
        
        # Bottom border with gradient effect
        border = tk.Frame(header, bg=self.border, height=1)
        border.pack(fill="x", side="bottom")
        
        return header
    
    def create_search_bar(self, parent: tk.Widget, search_var: tk.StringVar,
                          on_search: Callable = None,
                          placeholder: str = "Search prompts...") -> tk.Frame:
        """
        Create a modern search bar with icon and clear button.
        
        Returns the search frame.
        """
        container = tk.Frame(parent, bg=self.bg)
        container.pack(fill="x", padx=SPACING.SM, pady=SPACING.XS)
        
        # Search box container with border
        search_frame = tk.Frame(
            container,
            bg=self.search_bg,
            highlightbackground=self.border,
            highlightthickness=1,
            highlightcolor=self.highlight
        )
        search_frame.pack(fill="x")
        
        inner = tk.Frame(search_frame, bg=self.search_bg)
        inner.pack(fill="x", padx=SPACING.SM, pady=SPACING.XS)
        
        # Search icon
        search_icon = tk.Label(
            inner,
            text="🔍",
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self.search_bg,
            fg=self.muted
        )
        search_icon.pack(side="left", padx=(SPACING.XS, SPACING.SM))
        
        # Entry
        entry = tk.Entry(
            inner,
            textvariable=search_var,
            font=get_font(TYPOGRAPHY.SIZE_BASE),
            bg=self.search_bg,
            fg=self.fg,
            insertbackground=self.fg,
            relief="flat",
            highlightthickness=0,
            border=0
        )
        entry.pack(side="left", fill="x", expand=True, pady=SPACING.XS)
        
        # Placeholder handling
        is_placeholder = [True]
        
        def show_placeholder():
            if not search_var.get():
                entry.delete(0, tk.END)
                entry.insert(0, placeholder)
                entry.config(fg=self.muted)
                is_placeholder[0] = True
        
        def hide_placeholder():
            if is_placeholder[0]:
                entry.delete(0, tk.END)
                entry.config(fg=self.fg)
                is_placeholder[0] = False
        
        entry.bind("<FocusIn>", lambda e: hide_placeholder())
        entry.bind("<FocusOut>", lambda e: show_placeholder() if not search_var.get() else None)
        
        show_placeholder()
        
        # Clear button
        clear_btn = tk.Label(
            inner,
            text="✕",
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self.search_bg,
            fg=self.muted,
            cursor="hand2"
        )
        
        def clear_search():
            search_var.set("")
            hide_placeholder()
            entry.focus_set()
            if on_search:
                on_search("")
        
        clear_btn.bind("<Button-1>", lambda e: clear_search())
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg=self.fg))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg=self.muted))
        
        # Show/hide clear button based on content
        def update_clear_btn(*args):
            if search_var.get() and not is_placeholder[0]:
                clear_btn.pack(side="right", padx=SPACING.XS)
            else:
                clear_btn.pack_forget()
        
        search_var.trace_add("write", update_clear_btn)
        
        # Search on key release
        if on_search:
            entry.bind("<KeyRelease>", lambda e: on_search(search_var.get()) if not is_placeholder[0] else None)
        
        # Focus border effect
        def on_focus_in(e):
            search_frame.config(highlightbackground=self.highlight)
        
        def on_focus_out(e):
            search_frame.config(highlightbackground=self.border)
        
        entry.bind("<FocusIn>", on_focus_in, add="+")
        entry.bind("<FocusOut>", on_focus_out, add="+")
        
        return container
    
    def create_category_header(self, parent: tk.Widget, title: str,
                               color: str = None, collapsed: bool = False,
                               on_toggle: Callable = None) -> tk.Frame:
        """
        Create a styled category header.
        
        Returns the header frame.
        """
        color = color or self.highlight
        
        frame = tk.Frame(
            parent,
            bg=self.card_bg,
            highlightbackground=blend_colors(self.border, color, 0.3),
            highlightthickness=1
        )
        
        inner = tk.Frame(frame, bg=self.card_bg)
        inner.pack(fill="x", padx=SPACING.XS, pady=SPACING.XS)
        
        # Color strip
        strip = tk.Frame(inner, bg=color, width=3)
        strip.pack(side="left", fill="y", padx=(0, SPACING.XS))
        
        # Expand/collapse icon
        icon_text = "▸" if collapsed else "▾"
        icon = tk.Label(
            inner,
            text=icon_text,
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self.card_bg,
            fg=self.muted,
            cursor="hand2" if on_toggle else "arrow"
        )
        icon.pack(side="left", padx=(0, SPACING.XS))
        
        # Folder icon
        folder = tk.Label(
            inner,
            text="📁" if collapsed else "📂",
            font=get_font(TYPOGRAPHY.SIZE_BASE),
            bg=self.card_bg,
            fg=color
        )
        folder.pack(side="left", padx=(0, SPACING.SM))
        
        # Title
        title_label = tk.Label(
            inner,
            text=title,
            font=get_font(TYPOGRAPHY.SIZE_BASE, TYPOGRAPHY.WEIGHT_BOLD),
            bg=self.card_bg,
            fg=self.fg
        )
        title_label.pack(side="left")
        
        # Hover effect with smooth transition feel
        default_border = blend_colors(self.border, color, 0.3)
        hover_border = color
        hover_bg = blend_colors(self.card_bg, color, 0.06)
        
        def on_enter(e):
            frame.config(highlightbackground=hover_border)
            inner.config(bg=hover_bg)
            for w in [icon, folder, title_label]:
                try:
                    w.config(bg=hover_bg)
                except Exception:
                    pass
        
        def on_leave(e):
            frame.config(highlightbackground=default_border)
            inner.config(bg=self.card_bg)
            for w in [icon, folder, title_label]:
                try:
                    w.config(bg=self.card_bg)
                except Exception:
                    pass
        
        for widget in [frame, inner, icon, folder, title_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            if on_toggle:
                widget.bind("<Button-1>", lambda e: on_toggle())
                widget.config(cursor="hand2")
        
        # Store reference to icon for updates
        frame._toggle_icon = icon
        frame._folder_icon = folder
        
        return frame
    
    def create_prompt_item(self, parent: tk.Widget, title: str,
                           preview: str = "", is_favorite: bool = False,
                           on_click: Callable = None,
                           on_copy: Callable = None,
                           on_favorite: Callable = None) -> tk.Frame:
        """
        Create a styled prompt item.
        
        Returns the item frame.
        """
        frame = tk.Frame(
            parent,
            bg=self.card_bg,
            highlightbackground=self.border,
            highlightthickness=1
        )
        
        inner = tk.Frame(frame, bg=self.card_bg)
        inner.pack(fill="x", padx=SPACING.XS, pady=SPACING.XS)
        
        # Main content area
        content = tk.Frame(inner, bg=self.card_bg)
        content.pack(side="left", fill="x", expand=True)
        
        # Title row
        title_row = tk.Frame(content, bg=self.card_bg)
        title_row.pack(fill="x")
        
        title_label = tk.Label(
            title_row,
            text=title,
            font=get_font(TYPOGRAPHY.SIZE_BASE),
            bg=self.card_bg,
            fg=self.fg,
            anchor="w"
        )
        title_label.pack(side="left")
        
        # Preview text
        if preview:
            preview_text = preview[:60] + "..." if len(preview) > 60 else preview
            preview_label = tk.Label(
                content,
                text=preview_text,
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=self.card_bg,
                fg=self.muted,
                anchor="w"
            )
            preview_label.pack(fill="x")
        
        # Action buttons
        actions = tk.Frame(inner, bg=self.card_bg)
        actions.pack(side="right")
        
        # Favorite button
        fav_text = "★" if is_favorite else "☆"
        fav_color = COLORS.WARNING if is_favorite else self.muted
        fav_btn = tk.Label(
            actions,
            text=fav_text,
            font=get_font(TYPOGRAPHY.SIZE_MD),
            bg=self.card_bg,
            fg=fav_color,
            cursor="hand2"
        )
        fav_btn.pack(side="left", padx=SPACING.XS)
        
        if on_favorite:
            fav_btn.bind("<Button-1>", lambda e: on_favorite())
        
        # Copy button
        copy_btn = tk.Label(
            actions,
            text="📋",
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self.card_bg,
            fg=self.muted,
            cursor="hand2"
        )
        copy_btn.pack(side="left", padx=SPACING.XS)
        
        if on_copy:
            copy_btn.bind("<Button-1>", lambda e: on_copy())
            copy_btn.bind("<Enter>", lambda e: copy_btn.config(fg=self.highlight))
            copy_btn.bind("<Leave>", lambda e: copy_btn.config(fg=self.muted))
        
        # Hover effects with smooth visual feedback
        hover_bg = blend_colors(self.card_bg, self.highlight, 0.06)
        
        def on_enter(e):
            frame.config(highlightbackground=self.highlight)
            for w in [inner, content, title_label]:
                try:
                    w.config(bg=hover_bg)
                except Exception:
                    pass
            actions.pack(side="right")
        
        def on_leave(e):
            frame.config(highlightbackground=self.border)
            for w in [inner, content, title_label]:
                try:
                    w.config(bg=self.card_bg)
                except Exception:
                    pass
        
        for widget in [frame, inner, content, title_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            if on_click:
                widget.bind("<Button-1>", lambda e: on_click())
                widget.config(cursor="hand2")
        
        return frame
    
    def create_footer(self, parent: tk.Widget,
                      on_exit: Callable = None) -> tk.Frame:
        """
        Create a minimal styled footer.
        
        Returns the footer frame.
        """
        frame = tk.Frame(parent, bg=self.header_bg)
        frame.pack(fill="x", side="bottom")
        
        # Top border
        border = tk.Frame(frame, bg=self.border, height=1)
        border.pack(fill="x")
        
        inner = tk.Frame(frame, bg=self.header_bg)
        inner.pack(fill="x", padx=SPACING.MD, pady=SPACING.SM)
        
        # Keyboard hints
        hints = tk.Label(
            inner,
            text="↑↓ Navigate  •  Enter Copy  •  F1 Help",
            font=get_font(TYPOGRAPHY.SIZE_XS),
            bg=self.header_bg,
            fg=self.muted
        )
        hints.pack(side="left")
        
        # Exit button
        if on_exit:
            exit_btn = tk.Label(
                inner,
                text="Exit",
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=self.header_bg,
                fg=COLORS.ERROR,
                cursor="hand2"
            )
            exit_btn.pack(side="right")
            exit_btn.bind("<Button-1>", lambda e: on_exit())
            exit_btn.bind("<Enter>", lambda e: exit_btn.config(fg=lighten(COLORS.ERROR, 0.2)))
            exit_btn.bind("<Leave>", lambda e: exit_btn.config(fg=COLORS.ERROR))
        
        return frame
    
    def create_stats_bar(self, parent: tk.Widget,
                         stats_var: tk.StringVar) -> tk.Frame:
        """
        Create a stats display bar.
        
        Returns the stats frame.
        """
        frame = tk.Frame(parent, bg=self.bg)
        frame.pack(fill="x", padx=SPACING.MD, pady=(0, SPACING.SM))
        
        stats_label = tk.Label(
            frame,
            textvariable=stats_var,
            font=get_font(TYPOGRAPHY.SIZE_XS),
            bg=self.bg,
            fg=self.muted
        )
        stats_label.pack(side="left")
        
        return frame
    
    def configure_scrollbar(self, scrollbar: ttk.Scrollbar, style: ttk.Style = None):
        """Configure scrollbar with modern styling"""
        if style is None:
            return
        
        style.configure(
            "Modern.Vertical.TScrollbar",
            background=self.accent,
            troughcolor=self.bg,
            borderwidth=0,
            arrowsize=0,
            width=8
        )
        style.map(
            "Modern.Vertical.TScrollbar",
            background=[("active", self.button_hover), ("pressed", self.highlight)]
        )


def apply_futuristic_drawer_style(drawer_instance, theme: dict = None):
    """
    Apply futuristic styling to an existing drawer instance.
    
    This is a helper function to retrofit styling to the existing drawer
    without major code changes.
    """
    styles = DrawerStyles(theme)
    
    # This function would hook into the existing drawer and apply styles
    # Implementation depends on the specific drawer structure
    
    return styles


class ModernScrollableFrame(tk.Frame):
    """
    A modern scrollable frame with custom scrollbar styling.
    Use this for the main prompt list.
    """
    
    def __init__(self, parent, theme: dict = None, **kwargs):
        self.theme = theme or {}
        bg = self.theme.get("background", COLORS.BLACK)
        
        super().__init__(parent, bg=bg, **kwargs)
        
        # Canvas
        self._canvas = tk.Canvas(
            self,
            bg=bg,
            highlightthickness=0,
            border=0
        )
        
        # Scrollbar
        accent = self.theme.get("accent", COLORS.SURFACE_2)
        highlight = self.theme.get("highlight", COLORS.CYAN)
        
        self._scrollbar = tk.Canvas(
            self,
            width=8,
            bg=bg,
            highlightthickness=0
        )
        
        # Inner frame
        self._inner = tk.Frame(self._canvas, bg=bg)
        
        # Canvas window
        self._window_id = self._canvas.create_window(
            (0, 0),
            window=self._inner,
            anchor="nw"
        )
        
        # Configure scrolling
        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Pack
        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")
        
        # Custom scrollbar drawing
        self._thumb_id = None
        self._draw_scrollbar()
        
        # Bind scroll events
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._inner.bind("<MouseWheel>", self._on_mousewheel)
        self._scrollbar.bind("<Button-1>", self._on_scrollbar_click)
        self._scrollbar.bind("<B1-Motion>", self._on_scrollbar_drag)
    
    def _on_inner_configure(self, event):
        """Update scroll region"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._draw_scrollbar()
    
    def _on_canvas_configure(self, event):
        """Resize inner frame to canvas width"""
        self._canvas.itemconfigure(self._window_id, width=event.width)
        self._draw_scrollbar()
    
    def _draw_scrollbar(self):
        """Draw custom scrollbar thumb"""
        self._scrollbar.delete("thumb")
        
        canvas_height = self._canvas.winfo_height()
        scroll_region = self._canvas.bbox("all")
        
        if not scroll_region or scroll_region[3] <= canvas_height:
            return
        
        total_height = scroll_region[3]
        visible_ratio = canvas_height / total_height
        
        # Get current scroll position
        y0, y1 = self._canvas.yview()
        
        # Calculate thumb position and size
        thumb_height = max(30, canvas_height * visible_ratio)
        thumb_y = y0 * canvas_height
        
        # Draw thumb
        accent = self.theme.get("accent", COLORS.SURFACE_3)
        highlight = self.theme.get("highlight", COLORS.CYAN)
        
        self._thumb_id = self._scrollbar.create_rectangle(
            2, thumb_y + 2,
            6, thumb_y + thumb_height - 2,
            fill=accent,
            outline="",
            tags="thumb"
        )
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._draw_scrollbar()
    
    def _on_scrollbar_click(self, event):
        """Handle scrollbar click"""
        canvas_height = self._canvas.winfo_height()
        ratio = event.y / canvas_height
        self._canvas.yview_moveto(ratio)
        self._draw_scrollbar()
    
    def _on_scrollbar_drag(self, event):
        """Handle scrollbar drag"""
        self._on_scrollbar_click(event)
    
    @property
    def inner(self) -> tk.Frame:
        """Get the inner scrollable frame"""
        return self._inner
    
    def scroll_to_top(self):
        """Scroll to top"""
        self._canvas.yview_moveto(0)
        self._draw_scrollbar()
    
    def scroll_to_bottom(self):
        """Scroll to bottom"""
        self._canvas.yview_moveto(1)
        self._draw_scrollbar()
