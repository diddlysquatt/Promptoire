"""
FontPreviewCombobox - A font selector that displays each font in its own typeface
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional, List
from ..design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION,
    get_font, blend_colors, lighten, darken, ensure_contrast, get_contrast_color,
    WCAG_AA_NORMAL, WCAG_UI_COMPONENTS
)


class FontPreviewCombobox(tk.Frame):
    """
    A custom font selector dropdown that:
    - Shows each font name rendered in its OWN typeface
    - Does NOT change font on hover (only on selection)
    - Includes search/filter capability
    - Shows a live preview of the selected font
    """
    
    def __init__(
        self,
        parent,
        variable: Optional[tk.StringVar] = None,
        command: Optional[Callable[[str], None]] = None,
        width: int = 200,
        max_dropdown_height: int = 250,
        font_size: int = 11,
        theme: dict = None,
        show_preview: bool = True,
        preview_text: str = "AaBbCc 123",
        **kwargs
    ):
        self.theme = theme or {}
        self._command = command
        self._width = width
        self._max_dropdown_height = max_dropdown_height
        self._font_size = font_size
        self._show_preview = show_preview
        self._preview_text = preview_text
        
        # Colors
        self._bg = self.theme.get("background", COLORS.SURFACE_0)
        self._accent = self.theme.get("accent", COLORS.SURFACE_2)
        self._fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        self._highlight = self.theme.get("highlight", COLORS.CYAN)
        self._border = self.theme.get("border", COLORS.BORDER_DEFAULT)
        self._muted = self.theme.get("muted_text", COLORS.TEXT_LOW)
        self._hover_bg = self.theme.get("button_hover", COLORS.SURFACE_3)
        
        # Get parent background
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = self._bg
        
        super().__init__(parent, bg=parent_bg, **kwargs)
        
        # Variable
        self._variable = variable or tk.StringVar(value="Segoe UI")
        
        # Get available fonts
        self._all_fonts = self._get_available_fonts()
        self._filtered_fonts = self._all_fonts.copy()
        
        # State
        self._dropdown_open = False
        self._dropdown_window = None
        self._hover_index = -1
        
        # Build UI
        self._build_ui()
        
        # Bind global click to close dropdown
        self.bind_all("<Button-1>", self._on_global_click, add="+")
    
    def _get_available_fonts(self) -> List[str]:
        """Get list of available font families, filtered for usability"""
        try:
            all_fonts = set(tkfont.families())
            # Filter out problematic fonts (starting with @ for vertical, etc.)
            fonts = [f for f in all_fonts if not f.startswith("@") and not f.startswith(".")]
            return sorted(fonts, key=str.lower)
        except Exception:
            return ["Segoe UI", "Arial", "Helvetica", "Consolas", "Courier New"]
    
    def _build_ui(self):
        """Build the main UI components"""
        # Main container frame with border
        self._container = tk.Frame(
            self,
            bg=self._accent,
            highlightbackground=self._border,
            highlightthickness=1,
            highlightcolor=self._highlight
        )
        self._container.pack(fill="x", expand=True)
        
        # Inner frame for content
        inner = tk.Frame(self._container, bg=self._accent)
        inner.pack(fill="x", padx=2, pady=2)
        
        # Selected font display (shows current font in its own face)
        self._display_frame = tk.Frame(inner, bg=self._accent, cursor="hand2")
        self._display_frame.pack(fill="x")
        
        # Font name label (rendered in the selected font)
        self._font_label = tk.Label(
            self._display_frame,
            text=self._variable.get(),
            font=(self._variable.get(), self._font_size),
            bg=self._accent,
            fg=self._fg,
            anchor="w",
            padx=8,
            pady=6
        )
        self._font_label.pack(side="left", fill="x", expand=True)
        
        # Dropdown arrow
        self._arrow = tk.Label(
            self._display_frame,
            text="▼",
            font=get_font(TYPOGRAPHY.SIZE_XS),
            bg=self._accent,
            fg=self._muted,
            padx=8
        )
        self._arrow.pack(side="right")
        
        # Bind click events
        for widget in [self._display_frame, self._font_label, self._arrow]:
            widget.bind("<Button-1>", self._toggle_dropdown)
            widget.bind("<Enter>", self._on_hover_enter)
            widget.bind("<Leave>", self._on_hover_leave)
        
        # Preview area (optional)
        if self._show_preview:
            self._preview_frame = tk.Frame(self._container, bg=self._bg)
            self._preview_frame.pack(fill="x", padx=2, pady=(0, 2))
            
            self._preview_label = tk.Label(
                self._preview_frame,
                text=self._preview_text,
                font=(self._variable.get(), self._font_size + 2),
                bg=self._bg,
                fg=self._highlight,
                anchor="w",
                padx=8,
                pady=4
            )
            self._preview_label.pack(fill="x")
        
        # Watch variable changes
        self._variable.trace_add("write", self._on_variable_change)
    
    def _on_hover_enter(self, event=None):
        """Handle hover on main display"""
        self._container.config(highlightbackground=self._highlight)
    
    def _on_hover_leave(self, event=None):
        """Handle hover leave"""
        if not self._dropdown_open:
            self._container.config(highlightbackground=self._border)
    
    def _toggle_dropdown(self, event=None):
        """Toggle the dropdown open/closed"""
        if self._dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()
    
    def _open_dropdown(self):
        """Open the font dropdown"""
        if self._dropdown_open:
            return
        
        self._dropdown_open = True
        self._container.config(highlightbackground=self._highlight)
        self._arrow.config(text="▲")
        
        # Create toplevel dropdown window
        self._dropdown_window = tk.Toplevel(self)
        self._dropdown_window.wm_overrideredirect(True)
        self._dropdown_window.wm_attributes("-topmost", True)
        
        # Position below the main widget
        x = self._container.winfo_rootx()
        y = self._container.winfo_rooty() + self._container.winfo_height()
        
        self._dropdown_window.wm_geometry(f"{self._width}x{self._max_dropdown_height}+{x}+{y}")
        
        # Dropdown container with border and glow
        dropdown_frame = tk.Frame(
            self._dropdown_window,
            bg=self._accent,
            highlightbackground=self._highlight,
            highlightthickness=2,
            highlightcolor=self._highlight
        )
        dropdown_frame.pack(fill="both", expand=True)
        
        # Search entry
        search_frame = tk.Frame(dropdown_frame, bg=self._accent)
        search_frame.pack(fill="x", padx=4, pady=4)
        
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self._search_var,
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._bg,
            fg=self._fg,
            insertbackground=self._fg,
            relief="flat",
            highlightbackground=self._border,
            highlightthickness=1
        )
        search_entry.pack(fill="x", padx=2, pady=2)
        search_entry.insert(0, "")
        search_entry.focus_set()
        
        # Placeholder
        search_entry.bind("<FocusIn>", lambda e: search_entry.config(fg=self._fg))
        
        # Font list with scrollbar
        list_frame = tk.Frame(dropdown_frame, bg=self._accent)
        list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        # Canvas for scrollable list
        self._list_canvas = tk.Canvas(
            list_frame,
            bg=self._accent,
            highlightthickness=0,
            width=self._width - 20
        )
        
        scrollbar = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self._list_canvas.yview,
            bg=self._accent,
            troughcolor=self._bg,
            width=8
        )
        
        self._list_inner = tk.Frame(self._list_canvas, bg=self._accent)
        
        self._list_canvas.create_window((0, 0), window=self._list_inner, anchor="nw")
        self._list_canvas.configure(yscrollcommand=scrollbar.set)
        
        self._list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate font list
        self._populate_font_list()
        
        # Update scroll region
        self._list_inner.update_idletasks()
        self._list_canvas.configure(scrollregion=self._list_canvas.bbox("all"))
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            self._list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self._dropdown_window.bind_all("<MouseWheel>", on_mousewheel)
        
        # Scroll to currently selected font
        self._scroll_to_selected()
    
    def _populate_font_list(self):
        """Populate the dropdown with font items"""
        # Clear existing
        for widget in self._list_inner.winfo_children():
            widget.destroy()
        
        current_font = self._variable.get()
        
        for idx, font_name in enumerate(self._filtered_fonts):
            is_selected = font_name == current_font
            
            # Create font item row
            item_bg = self._highlight if is_selected else self._accent
            item_fg = get_contrast_color(item_bg) if is_selected else self._fg
            
            item = tk.Frame(self._list_inner, bg=item_bg, cursor="hand2")
            item.pack(fill="x", pady=1)
            
            # Font name label - RENDERED IN ITS OWN TYPEFACE
            try:
                display_font = (font_name, self._font_size)
            except Exception:
                display_font = get_font(self._font_size)
            
            label = tk.Label(
                item,
                text=font_name,
                font=display_font,
                bg=item_bg,
                fg=item_fg,
                anchor="w",
                padx=8,
                pady=4
            )
            label.pack(fill="x")
            
            # Bind events (selection only on click, NOT on hover)
            def make_select_handler(fn):
                return lambda e: self._select_font(fn)
            
            def make_hover_handler(frame, lbl, fn):
                def enter(e):
                    if fn != current_font:
                        frame.config(bg=self._hover_bg)
                        lbl.config(bg=self._hover_bg)
                return enter
            
            def make_leave_handler(frame, lbl, fn):
                def leave(e):
                    if fn != current_font:
                        frame.config(bg=self._accent)
                        lbl.config(bg=self._accent)
                return leave
            
            for w in [item, label]:
                w.bind("<Button-1>", make_select_handler(font_name))
                w.bind("<Enter>", make_hover_handler(item, label, font_name))
                w.bind("<Leave>", make_leave_handler(item, label, font_name))
    
    def _scroll_to_selected(self):
        """Scroll the list to show the currently selected font"""
        current_font = self._variable.get()
        if current_font in self._filtered_fonts:
            idx = self._filtered_fonts.index(current_font)
            # Calculate scroll position
            total_items = len(self._filtered_fonts)
            if total_items > 0:
                fraction = idx / total_items
                self._list_canvas.yview_moveto(max(0, fraction - 0.2))
    
    def _select_font(self, font_name: str):
        """Select a font and close dropdown"""
        self._variable.set(font_name)
        self._close_dropdown()
        
        if self._command:
            self._command(font_name)
    
    def _close_dropdown(self):
        """Close the dropdown"""
        if self._dropdown_window:
            try:
                self._dropdown_window.destroy()
            except Exception:
                pass
            self._dropdown_window = None
        
        self._dropdown_open = False
        self._container.config(highlightbackground=self._border)
        self._arrow.config(text="▼")
    
    def _on_search_change(self, *args):
        """Filter fonts based on search input"""
        search_text = self._search_var.get().lower()
        
        if search_text:
            self._filtered_fonts = [
                f for f in self._all_fonts 
                if search_text in f.lower()
            ]
        else:
            self._filtered_fonts = self._all_fonts.copy()
        
        # Repopulate list
        self._populate_font_list()
        
        # Update scroll region
        self._list_inner.update_idletasks()
        self._list_canvas.configure(scrollregion=self._list_canvas.bbox("all"))
    
    def _on_variable_change(self, *args):
        """Handle variable change (from outside)"""
        font_name = self._variable.get()
        
        # Update display label
        try:
            self._font_label.config(
                text=font_name,
                font=(font_name, self._font_size)
            )
        except Exception:
            self._font_label.config(text=font_name)
        
        # Update preview if enabled
        if self._show_preview:
            try:
                self._preview_label.config(
                    font=(font_name, self._font_size + 2)
                )
            except Exception:
                pass
    
    def _on_global_click(self, event):
        """Close dropdown when clicking outside"""
        if self._dropdown_open and self._dropdown_window:
            # Check if click is outside dropdown
            try:
                widget = event.widget
                if widget not in [self._dropdown_window] and \
                   not str(widget).startswith(str(self._dropdown_window)):
                    # Check if click is on main widget
                    if widget not in [self._display_frame, self._font_label, self._arrow, self._container]:
                        self._close_dropdown()
            except Exception:
                pass
    
    def get(self) -> str:
        """Get current font value"""
        return self._variable.get()
    
    def set(self, value: str):
        """Set font value"""
        self._variable.set(value)
    
    def configure(self, **kwargs):
        """Configure widget"""
        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        super().configure(**kwargs)
    
    def destroy(self):
        """Clean up on destroy"""
        self._close_dropdown()
        super().destroy()


class CompactFontSelector(tk.Frame):
    """
    A more compact font selector with inline preview
    Used for settings panels where space is limited
    """
    
    def __init__(
        self,
        parent,
        label: str = "Font",
        variable: Optional[tk.StringVar] = None,
        command: Optional[Callable[[str], None]] = None,
        theme: dict = None,
        **kwargs
    ):
        self.theme = theme or {}
        self._label_text = label
        self._command = command
        
        # Colors
        self._bg = self.theme.get("accent", COLORS.SURFACE_2)
        self._fg = self.theme.get("foreground", COLORS.TEXT_PRIMARY)
        self._muted = self.theme.get("muted_text", COLORS.TEXT_LOW)
        
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = self._bg
        
        super().__init__(parent, bg=parent_bg, **kwargs)
        
        self._variable = variable or tk.StringVar(value="Segoe UI")
        
        # Label
        if label:
            lbl = tk.Label(
                self,
                text=label,
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=parent_bg,
                fg=self._muted
            )
            lbl.pack(anchor="w")
        
        # Font selector
        self._selector = FontPreviewCombobox(
            self,
            variable=self._variable,
            command=self._on_change,
            width=180,
            max_dropdown_height=200,
            font_size=10,
            theme=theme,
            show_preview=False
        )
        self._selector.pack(fill="x", pady=(2, 0))
    
    def _on_change(self, font_name: str):
        """Handle font change"""
        if self._command:
            self._command(font_name)
    
    def get(self) -> str:
        return self._variable.get()
    
    def set(self, value: str):
        self._variable.set(value)
