"""
SettingsPanelV2 - Futuristic Compact Settings Interface
Features:
- Horizontal tab navigation (no sidebar)
- No scrolling - compact single-view layout
- Neon glow effects and animated borders
- Font selector with live preview in actual typeface
- Merged sections for efficiency
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
from tkinter import font as tkfont
from typing import Dict, Any, Optional, Callable
import copy
import math
import string

from .design_system import (
    COLORS, TYPOGRAPHY, SPACING, ANIMATION, RADIUS,
    FUTURISTIC_THEMES,
    get_font, get_mono_font, blend_colors, lighten, darken,
    get_contrast_color, configure_ttk_styles,
    contrast_ratio, validate_theme_contrast, 
    WCAG_AA_NORMAL, WCAG_AA_LARGE, WCAG_UI_COMPONENTS
)
from .widgets import (
    ModernButton, ToggleSwitch, GlowSlider, ModernCard, HorizontalTabBar, TabItem, Toast,
    FontPreviewCombobox
)
from .widgets.modern_card import SettingsCard
from .widgets.glow_slider import StepperSlider


class NeonBorder(tk.Canvas):
    """Animated neon border effect for futuristic UI"""
    
    def __init__(self, parent, color="#00e5e5", pulse=True, **kwargs):
        self._color = color
        self._pulse = pulse
        self._alpha = 1.0
        self._direction = -1
        self._running = True
        
        super().__init__(parent, highlightthickness=0, **kwargs)
        
        if pulse:
            self._animate()
    
    def _animate(self):
        """Pulse animation for neon effect"""
        if not self._running:
            return
        
        # Oscillate alpha between 0.4 and 1.0
        self._alpha += self._direction * 0.03
        if self._alpha <= 0.4:
            self._alpha = 0.4
            self._direction = 1
        elif self._alpha >= 1.0:
            self._alpha = 1.0
            self._direction = -1
        
        self.after(50, self._animate)
    
    def stop(self):
        self._running = False


class SettingsPanelV2:
    """
    Futuristic settings panel with:
    - Horizontal tabs at top (compact)
    - No scrolling - everything visible
    - Neon/glow effects
    - Merged sections for efficiency
    """
    
    # Navigation items - Compact horizontal tabs
    NAV_ITEMS = [
        TabItem(key="general", label="General", icon="⚙️"),
        TabItem(key="appearance", label="Appearance", icon="🎨"),
        TabItem(key="shortcuts", label="Shortcuts", icon="⌨️"),
        TabItem(key="data", label="Data", icon="📁"),
        TabItem(key="about", label="About", icon="ℹ️"),
    ]
    
    def __init__(self, parent, initial_section: str = "general", show_user_guide_popup: bool = False):
        """Initialize the settings panel."""
        self.parent = parent
        self.settings = copy.deepcopy(parent.settings)
        self._dirty = False
        nav_keys = {item.key for item in self.NAV_ITEMS}
        self._current_section = initial_section if initial_section in nav_keys else "general"
        
        # Create window
        self.window = tk.Toplevel(parent.root)
        self._setup_window()
        
        # Build UI
        self._build_ui()
        
        # Load initial section
        self.focus_section(self._current_section)
        if show_user_guide_popup:
            try:
                self.window.after(120, self.show_user_guide_popup)
            except Exception:
                pass
        
        # Start neon border animation
        self._start_neon_animation()
    
    def _setup_window(self):
        """Configure the settings window - COMPACT SIZE"""
        self.window.title("Neural Control Deck")
        self.window.geometry("860x640")
        self.window.minsize(860, 640)
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)
        
        # Theme colors
        self._bg = self.settings["theme"].get("background", COLORS.BLACK)
        self._fg = self.settings["theme"].get("foreground", COLORS.TEXT_PRIMARY)
        self._accent = self.settings["theme"].get("accent", COLORS.SURFACE_1)
        self._highlight = self.settings["theme"].get("highlight", COLORS.CYAN)
        self._border = self.settings["theme"].get("border", COLORS.BORDER_DEFAULT)
        self._panel_bg = blend_colors(self._bg, self._accent, 0.2)
        
        self.window.configure(bg=self._bg)
        
        # Configure ttk styles
        self._theme_dict = {
            "background": self._bg,
            "foreground": self._fg,
            "accent": self._accent,
            "highlight": self._highlight,
            "border": self._border,
            "button_bg": self.settings["theme"].get("button_bg", COLORS.SURFACE_3),
            "button_hover": self.settings["theme"].get("button_hover", COLORS.SURFACE_4),
            "muted_text": self.settings["theme"].get("muted_text", COLORS.TEXT_SECONDARY),
            "glow_color": f"{self._highlight}40",
            "slider_trough": self.settings["theme"].get("slider_trough", COLORS.SURFACE_2),
        }
        
        configure_ttk_styles(self.window, self._theme_dict)
        
        # Close handler
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Keyboard shortcuts
        self.window.bind("<Escape>", lambda e: self._on_close())
        self.window.bind("<Control-s>", lambda e: self._save_settings())
        
        # Apply icon if available
        try:
            self.parent._apply_window_icon(self.window)
        except Exception:
            pass
        
        # Smooth fade-in
        self._animate_in()
    
    def _animate_in(self):
        """Smooth fade-in animation"""
        try:
            self.window.attributes("-alpha", 0.0)
            
            def step(i):
                if i > 10:
                    self.window.attributes("-alpha", 1.0)
                    return
                alpha = i / 10
                self.window.attributes("-alpha", alpha)
                self.window.after(20, lambda: step(i + 1))
            
            step(0)
        except Exception:
            try:
                self.window.attributes("-alpha", 1.0)
            except Exception:
                pass
    
    def _build_ui(self):
        """Build the main UI structure with neon effects"""
        # Outer frame for neon border effect
        self._outer_frame = tk.Frame(self.window, bg=self._highlight, padx=1, pady=1)
        self._outer_frame.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Main container
        main = tk.Frame(self._outer_frame, bg=self._bg)
        main.pack(fill="both", expand=True)

        # Decorative holographic top strokes
        top_fx = tk.Frame(main, bg=self._bg, height=3)
        top_fx.pack(fill="x")
        top_fx.pack_propagate(False)
        tk.Frame(top_fx, bg=blend_colors(self._highlight, self._bg, 0.3), height=1).pack(fill="x")
        tk.Frame(top_fx, bg=blend_colors(self._highlight, self._bg, 0.55), height=1).pack(fill="x")
        
        # ═══════════════════════════════════════════════════════════════════
        # HEADER with Horizontal Tabs
        # ═══════════════════════════════════════════════════════════════════
        header = tk.Frame(main, bg=self._bg)
        header.pack(fill="x", padx=SPACING.MD, pady=(SPACING.MD, 0))

        # Title with neon glow effect
        title_label = tk.Label(
            header,
            text="NEURAL CONTROL DECK",
            font=get_font(TYPOGRAPHY.SIZE_LG, TYPOGRAPHY.WEIGHT_BOLD),
            bg=self._bg,
            fg=self._highlight
        )
        title_label.pack(anchor="w")

        tabs_row = tk.Frame(main, bg=self._bg)
        tabs_row.pack(fill="x", padx=SPACING.MD, pady=(SPACING.XS, 0))

        # Horizontal Tab Bar directly below title
        self._tab_bar = HorizontalTabBar(
            tabs_row,
            items=self.NAV_ITEMS,
            on_select=self._on_nav_select,
            selected=self._current_section,
            theme=self._theme_dict
        )
        self._tab_bar.pack(fill="x")
        
        # Neon separator line
        sep = tk.Frame(main, bg=self._highlight, height=1)
        sep.pack(fill="x", padx=SPACING.MD, pady=(SPACING.SM, 0))
        
        # ═══════════════════════════════════════════════════════════════════
        # CONTENT AREA (no scrolling)
        # ═══════════════════════════════════════════════════════════════════
        self._content_frame = tk.Frame(main, bg=self._bg)
        self._content_frame.pack(fill="both", expand=True, padx=SPACING.MD, pady=SPACING.MD)
        
        # ═══════════════════════════════════════════════════════════════════
        # FOOTER with action buttons
        # ═══════════════════════════════════════════════════════════════════
        self._build_footer(main)
    
    def _start_neon_animation(self):
        """Animate the neon border"""
        self._neon_alpha = 1.0
        self._neon_direction = -1
        self._animate_neon()
    
    def _animate_neon(self):
        """Pulsing neon border animation (15fps for efficiency)"""
        try:
            if not self.window.winfo_exists():
                return
            
            # Oscillate between dim and bright
            self._neon_alpha += self._neon_direction * 0.03
            if self._neon_alpha <= 0.3:
                self._neon_alpha = 0.3
                self._neon_direction = 1
            elif self._neon_alpha >= 1.0:
                self._neon_alpha = 1.0
                self._neon_direction = -1
            
            # Blend highlight with black for dimming effect
            dimmed = blend_colors(self._highlight, self._bg, 1 - self._neon_alpha)
            self._outer_frame.config(bg=dimmed)
            
            self.window.after(66, self._animate_neon)  # ~15fps, still smooth
        except Exception:
            pass
    
    def _build_footer(self, parent):
        """Build compact footer with action buttons and keyboard hints"""
        footer = tk.Frame(parent, bg=self._bg)
        footer.pack(fill="x", padx=SPACING.MD, pady=(0, SPACING.MD))
        
        # Separator
        sep = tk.Frame(footer, bg=blend_colors(self._border, self._highlight, 0.3), height=1)
        sep.pack(fill="x", pady=(0, SPACING.SM))
        
        # Keyboard hints row
        hints_frame = tk.Frame(footer, bg=self._bg)
        hints_frame.pack(fill="x", pady=(0, SPACING.XS))
        
        for key_text, desc_text in [("Ctrl+S", "Save"), ("Esc", "Close")]:
            hint = tk.Frame(hints_frame, bg=self._bg)
            hint.pack(side="left", padx=(0, SPACING.MD))
            tk.Label(
                hint, text=key_text,
                font=get_font(TYPOGRAPHY.SIZE_XS, TYPOGRAPHY.WEIGHT_BOLD),
                bg=self._theme_dict.get("button_bg", COLORS.SURFACE_3),
                fg=self._highlight, padx=4, pady=1
            ).pack(side="left", padx=(0, 3))
            tk.Label(
                hint, text=desc_text,
                font=get_font(TYPOGRAPHY.SIZE_XS),
                bg=self._bg,
                fg=self._theme_dict.get("muted_text", COLORS.TEXT_LOW)
            ).pack(side="left")
        
        # Button container
        btn_frame = tk.Frame(footer, bg=self._bg)
        btn_frame.pack(fill="x")
        
        # Left - Reset
        self._reset_btn = ModernButton(
            btn_frame,
            text="Reset",
            command=self._reset_defaults,
            variant="secondary",
            theme=self._theme_dict,
            height=28
        )
        self._reset_btn.pack(side="left")
        
        # Right - Cancel and Save
        right = tk.Frame(btn_frame, bg=self._bg)
        right.pack(side="right")
        
        self._cancel_btn = ModernButton(
            right,
            text="Cancel",
            command=self._on_close,
            variant="secondary",
            theme=self._theme_dict,
            height=28
        )
        self._cancel_btn.pack(side="left", padx=(0, SPACING.SM))
        
        self._save_btn = ModernButton(
            right,
            text="⚡ Apply",
            command=self._save_settings,
            variant="primary",
            theme=self._theme_dict,
            height=28
        )
        self._save_btn.pack(side="left")
    
    def _on_nav_select(self, key: str):
        """Handle tab selection"""
        self._load_section(key)

    def focus_section(self, key: str):
        """Programmatically focus a settings section."""
        valid = {item.key for item in self.NAV_ITEMS}
        if key not in valid:
            key = "general"
        try:
            if hasattr(self._tab_bar, "get_selected") and self._tab_bar.get_selected() == key:
                self._load_section(key)
                return
            self._tab_bar.select(key)
            return
        except Exception:
            pass
        self._load_section(key)
    
    def _load_section(self, key: str):
        """Load a settings section"""
        self._current_section = key
        
        # Clear current content
        for widget in self._content_frame.winfo_children():
            widget.destroy()
        
        # Load new section
        loader = getattr(self, f"_build_{key}_section", None)
        if loader:
            loader()
        self._build_tab_action_strip()

    def _save_and_accept(self):
        """Save current settings and close the settings window."""
        ok = self._save_settings()
        if ok:
            self._on_close()

    def _build_tab_action_strip(self):
        """Render per-tab action buttons (Save + Accept) inside the active tab content."""
        strip = tk.Frame(self._content_frame, bg=self._bg)
        strip.pack(side="bottom", fill="x", pady=(SPACING.XS, 0))

        sep = tk.Frame(strip, bg=blend_colors(self._border, self._highlight, 0.35), height=1)
        sep.pack(fill="x", pady=(0, SPACING.XS))

        row = tk.Frame(strip, bg=self._bg)
        row.pack(fill="x")

        section_label = self._current_section.replace("_", " ").title()
        tk.Label(
            row,
            text=f"{section_label} actions",
            font=get_font(TYPOGRAPHY.SIZE_XS),
            bg=self._bg,
            fg=self._theme_dict.get("muted_text", COLORS.TEXT_LOW),
            anchor="w",
        ).pack(side="left")

        btns = tk.Frame(row, bg=self._bg)
        btns.pack(side="right")

        self._tab_save_btn = ModernButton(
            btns,
            text="Save",
            command=self._save_settings,
            variant="primary",
            theme=self._theme_dict,
            height=26,
        )
        self._tab_save_btn.pack(side="left", padx=(0, SPACING.SM))

        self._tab_accept_btn = ModernButton(
            btns,
            text="Accept",
            command=self._save_and_accept,
            variant="secondary",
            theme=self._theme_dict,
            height=26,
        )
        self._tab_accept_btn.pack(side="left")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: General (merged with Behavior)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_general_section(self):
        """Build compact General section with Behavior merged in"""
        container = self._content_frame

        # ─── Quick Access: Formatter + Guide (first card) ───
        self._build_formatter_quick_card(container)
        
        # ─── Icon Settings ───
        icon_frame = self._create_neon_card(container, "🎯 Launcher Icon")
        
        # Icon type row
        type_row = tk.Frame(icon_frame, bg=self._accent)
        type_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(
            type_row, text="Type:", font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent, fg=self._fg
        ).pack(side="left")
        
        self._icon_type_var = tk.StringVar(value=self.settings["icon"]["type"])
        
        for icon_type, label in [("emoji", "Emoji"), ("image", "Image")]:
            rb = tk.Radiobutton(
                type_row, text=label, variable=self._icon_type_var, value=icon_type,
                bg=self._accent, fg=self._fg, selectcolor=self._accent,
                activebackground=self._accent, activeforeground=self._fg,
                highlightthickness=0, command=self._on_icon_type_change,
                font=get_font(TYPOGRAPHY.SIZE_SM)
            )
            rb.pack(side="left", padx=SPACING.SM)
        
        # Emoji selector (inline)
        self._emoji_frame = tk.Frame(icon_frame, bg=self._accent)
        self._emoji_var = tk.StringVar(
            value=self.settings["icon"]["value"] if self.settings["icon"]["type"] == "emoji" else "🧠"
        )
        
        presets = ["🧠", "💡", "⚡", "🔥", "🚀", "💻", "📝", "🎯", "⭐", "🎨", "💎", "🌟"]
        for emoji in presets:
            btn = tk.Label(
                self._emoji_frame, text=emoji, font=get_font(14),
                bg=self._accent, fg=self._fg, cursor="hand2", padx=3
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, em=emoji: self._emoji_var.set(em))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self._theme_dict["button_hover"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self._accent))
        
        # Image selector
        self._image_frame = tk.Frame(icon_frame, bg=self._accent)
        self._image_path_var = tk.StringVar(
            value=self.settings["icon"]["value"] if self.settings["icon"]["type"] == "image" else ""
        )
        
        ModernButton(
            self._image_frame, text="📁 Browse", command=self._choose_icon_image,
            variant="secondary", theme=self._theme_dict, height=24
        ).pack(side="left")
        
        tk.Label(
            self._image_frame, textvariable=self._image_path_var,
            font=get_font(TYPOGRAPHY.SIZE_XS), bg=self._accent,
            fg=self._theme_dict["muted_text"], wraplength=200
        ).pack(side="left", padx=SPACING.SM)
        
        self._on_icon_type_change()
        
        # ─── Behavior Toggles (2-column grid) ───
        behavior_frame = self._create_neon_card(container, "🎮 Behavior")
        
        # Grid container
        grid = tk.Frame(behavior_frame, bg=self._accent)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        
        # Row 1
        self._auto_hide_var = tk.BooleanVar(value=self.settings.get("auto_hide", True))
        self._create_toggle_cell(grid, "Auto-hide", self._auto_hide_var, 0, 0)
        
        self._start_hidden_var = tk.BooleanVar(value=self.settings.get("start_hidden", False))
        self._create_toggle_cell(grid, "Start minimized", self._start_hidden_var, 0, 1)
        
        # Row 2
        self._auto_paste_var = tk.BooleanVar(value=self.settings.get("auto_paste", False))
        self._create_toggle_cell(grid, "Auto-paste", self._auto_paste_var, 1, 0)
        
        self._always_on_top_var = tk.BooleanVar(value=self.settings.get("always_on_top", True))
        self._create_toggle_cell(grid, "Always on top", self._always_on_top_var, 1, 1)
        
        # Row 3 - Spring-loaded auto-close (full width with description)
        spring_row = tk.Frame(behavior_frame, bg=self._accent)
        spring_row.pack(fill="x", pady=(SPACING.XS, 0))
        
        spring_label_frame = tk.Frame(spring_row, bg=self._accent)
        spring_label_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            spring_label_frame, text="Auto-close after copy",
            font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg, anchor="w"
        ).pack(anchor="w")
        tk.Label(
            spring_label_frame, text="Collapse the drawer automatically after copying a prompt",
            font=get_font(TYPOGRAPHY.SIZE_XS), bg=self._accent,
            fg=self._theme_dict["muted_text"], anchor="w"
        ).pack(anchor="w")
        
        self._spring_loaded_var = tk.BooleanVar(value=self.settings.get("spring_loaded_close", True))
        ToggleSwitch(spring_row, variable=self._spring_loaded_var, theme=self._theme_dict, width=36, height=20).pack(side="right", pady=SPACING.XS)
        
        # Paste delay slider (shown when auto-paste is on)
        paste_row = tk.Frame(behavior_frame, bg=self._accent)
        paste_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(
            paste_row, text="Paste delay:", font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent, fg=self._fg
        ).pack(side="left")
        
        self._paste_delay_var = tk.DoubleVar(value=self.settings.get("paste_delay_ms", 500))
        GlowSlider(
            paste_row, variable=self._paste_delay_var, from_=100, to=2000,
            width=120, height=22, show_value=True, value_format="{:.0f}ms",
            theme=self._theme_dict
        ).pack(side="right")
        
        # ─── Advanced ───
        adv_frame = self._create_neon_card(container, "🔧 Advanced")
        
        adv_grid = tk.Frame(adv_frame, bg=self._accent)
        adv_grid.pack(fill="x")
        adv_grid.columnconfigure(0, weight=1)
        adv_grid.columnconfigure(1, weight=1)
        
        self._virtual_scroll_var = tk.BooleanVar(value=self.settings.get("use_virtual_scrolling", False))
        self._create_toggle_cell(
            adv_grid,
            "Virtual scroll",
            self._virtual_scroll_var,
            0,
            0,
            tooltip=(
                "Render only visible prompt rows for smoother performance in large libraries. "
                "Best for big prompt collections."
            ),
        )
        
        self._fuzzy_var = tk.BooleanVar(value=self.settings.get("search_fuzzy", False))
        self._create_toggle_cell(
            adv_grid,
            "Fuzzy search",
            self._fuzzy_var,
            0,
            1,
            tooltip=(
                "Allow approximate matching in search, so close spellings and partial terms still find prompts."
            ),
        )
        
        self._highlight_var = tk.BooleanVar(value=self.settings.get("search_highlight", True))
        self._create_toggle_cell(
            adv_grid,
            "Highlight matches",
            self._highlight_var,
            1,
            0,
            tooltip="Highlight matching text in prompt titles while searching.",
        )
    
    def _create_toggle_cell(self, parent, label: str, var: tk.BooleanVar, row: int, col: int, tooltip: str = ""):
        """Create a compact toggle cell for grid layout"""
        cell = tk.Frame(parent, bg=self._accent)
        cell.grid(row=row, column=col, sticky="ew", padx=SPACING.XS, pady=SPACING.XS)
        
        label_widget = tk.Label(
            cell, text=label, font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent, fg=self._fg, anchor="w", cursor="hand2"
        )
        label_widget.pack(side="left", fill="x", expand=True)
        
        switch = ToggleSwitch(cell, variable=var, theme=self._theme_dict, width=40, height=22)
        switch.pack(side="right")

        def _toggle_from_cell(_event=None):
            if _event is not None and _event.widget not in (cell, label_widget):
                return
            try:
                var.set(not bool(var.get()))
            except Exception:
                pass
            return "break"

        cell.bind("<Button-1>", _toggle_from_cell)
        label_widget.bind("<Button-1>", _toggle_from_cell)
        self._attach_tooltip((cell, label_widget, switch), tooltip)

    def _attach_tooltip(self, widgets, text: str, delay: int = 250):
        """Attach a shared tooltip using the parent application's tooltip helper when available."""
        if not text:
            return
        if not isinstance(widgets, (list, tuple)):
            widgets = [widgets]
        for widget in widgets:
            try:
                if hasattr(self.parent, "_attach_tooltip"):
                    self.parent._attach_tooltip(widget, text, delay=delay)
            except Exception:
                pass

    def _get_formatter_prompt_text(self) -> str:
        """Return the full formatter prompt text from the parent app when available."""
        try:
            if hasattr(self.parent, "get_formatter_prompt_text"):
                text = self.parent.get_formatter_prompt_text()
                if isinstance(text, str) and text.strip():
                    return text
        except Exception:
            pass
        return (
            "PROMPTOIRE - ONE-SHOT FORMATTER (STRICT OUTPUT)\n\n"
            "Convert raw prompt notes into one valid Promptoire JSON object.\n"
            "Output JSON only (no prose, no markdown).\n"
            "Top-level key must be \"categories\"."
        )

    def _build_formatter_quick_card(self, container):
        """Build the front-of-settings formatter quick actions."""
        quick = self._create_neon_card(container, "⚡ Formatter LLM")

        tk.Label(
            quick,
            text="Copy the formatter prompt instantly. Open the full prompt only when needed.",
            font=get_font(TYPOGRAPHY.SIZE_XS),
            bg=self._accent,
            fg=self._theme_dict["muted_text"],
            anchor="w",
            justify="left",
            wraplength=620,
        ).pack(fill="x", pady=(0, SPACING.XS))

        row1 = tk.Frame(quick, bg=self._accent)
        row1.pack(fill="x", pady=(0, SPACING.XS))
        ModernButton(
            row1,
            text="📋 Copy Formatter Prompt",
            command=lambda: self._copy_text(self._get_formatter_prompt_text()),
            variant="primary",
            theme=self._theme_dict,
            height=28,
        ).pack(side="left", padx=(0, SPACING.SM))
        ModernButton(
            row1,
            text="👁 View Full Prompt",
            command=self._show_formatter_prompt_popup,
            variant="secondary",
            theme=self._theme_dict,
            height=28,
        ).pack(side="left")

        row2 = tk.Frame(quick, bg=self._accent)
        row2.pack(fill="x")
        ModernButton(
            row2,
            text="📘 Open User Guide",
            command=self.show_user_guide_popup,
            variant="secondary",
            theme=self._theme_dict,
            height=26,
        ).pack(side="left")

    def _show_formatter_prompt_popup(self):
        """Show the full formatter prompt in a compact popup."""
        try:
            prompt_text = self._get_formatter_prompt_text()
            popup = tk.Toplevel(self.window)
            popup.title("Formatter Prompt")
            popup.geometry("760x560")
            popup.minsize(620, 420)
            popup.attributes("-topmost", True)
            popup.configure(bg=self._bg)
            try:
                self.parent._apply_window_icon(popup)
            except Exception:
                pass

            container = tk.Frame(popup, bg=self._bg, padx=10, pady=10)
            container.pack(fill="both", expand=True)

            tk.Label(
                container,
                text="Full Formatter Prompt",
                font=get_font(TYPOGRAPHY.SIZE_BASE, TYPOGRAPHY.WEIGHT_BOLD),
                bg=self._bg,
                fg=self._fg,
                anchor="w",
            ).pack(fill="x", pady=(0, SPACING.XS))

            text_frame = tk.Frame(container, bg=self._bg)
            text_frame.pack(fill="both", expand=True)

            text = tk.Text(
                text_frame,
                wrap="word",
                font=get_mono_font(TYPOGRAPHY.SIZE_XS),
                bg=self._theme_dict.get("accent", self._accent),
                fg=self._fg,
                relief="flat",
                padx=8,
                pady=8,
                insertbackground=self._fg,
            )
            scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            text.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            text.insert("1.0", prompt_text)
            text.configure(state="disabled")

            actions = tk.Frame(container, bg=self._bg)
            actions.pack(fill="x", pady=(SPACING.SM, 0))
            ModernButton(
                actions,
                text="📋 Copy Formatter Prompt",
                command=lambda: self._copy_text(prompt_text),
                variant="primary",
                theme=self._theme_dict,
                height=28,
            ).pack(side="left")
            ModernButton(
                actions,
                text="Close",
                command=popup.destroy,
                variant="secondary",
                theme=self._theme_dict,
                height=28,
            ).pack(side="right")
            try:
                popup.bind("<Escape>", lambda _e: popup.destroy())
                popup.bind("<Control-w>", lambda _e: popup.destroy())
            except Exception:
                pass
        except Exception:
            pass

    def show_user_guide_popup(self):
        """Show consolidated user guide content from within Settings."""
        try:
            popup = tk.Toplevel(self.window)
            popup.title("Promptoire - User Guide")
            popup.geometry("780x620")
            popup.minsize(640, 460)
            popup.attributes("-topmost", True)
            popup.configure(bg=self._bg)
            try:
                self.parent._apply_window_icon(popup)
            except Exception:
                pass

            frame = tk.Frame(popup, bg=self._bg, padx=10, pady=10)
            frame.pack(fill="both", expand=True)

            teleport_hotkey = (self.settings.get("teleport_hotkey", "") or "").strip() or "Not set"
            guide_text = (
                "Promptoire User Guide\n\n"
                "Overview\n"
                "- Promptoire is a compact launcher for browsing, copying, and reusing prompts quickly.\n"
                "- Open Settings by double-clicking the Prompt Library tab or by right-clicking it and choosing Settings.\n\n"
                "Workflow\n"
                "- Prompt Library tab: open your saved prompts and copy one quickly.\n"
                "- Prompt Editor tab: edit categories/prompts and reorganize with drag-and-drop.\n"
                "- Move tab: drag the launcher anywhere on screen.\n\n"
                "Shortcuts\n"
                f"- Teleport to Cursor: {teleport_hotkey}\n"
                "- Focus Search: Ctrl+F\n"
                "- Prompt Editor: Ctrl+E\n"
                "- Settings: Ctrl+,\n"
                "- Reload Prompts: Ctrl+R\n"
                "- User Guide: F1\n\n"
                "Import / Export\n"
                "- Prompts are stored as JSON.\n"
                "- Use Settings > Data for Import, Export, Backup, and opening the prompts folder.\n"
                "- The formatter prompt converts messy source text into importable Promptoire JSON.\n\n"
                "Formatter Tip\n"
                "- Use 'Copy Formatter Prompt' for daily use.\n"
                "- Use 'View Full Prompt' only when you want to inspect or edit the full instructions."
            )

            text_frame = tk.Frame(frame, bg=self._bg)
            text_frame.pack(fill="both", expand=True)

            text = tk.Text(
                text_frame,
                wrap="word",
                font=get_font(TYPOGRAPHY.SIZE_SM),
                bg=self._theme_dict.get("accent", self._accent),
                fg=self._fg,
                relief="flat",
                padx=10,
                pady=10,
                insertbackground=self._fg,
            )
            scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            text.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            text.insert("1.0", guide_text)
            text.configure(state="disabled")

            buttons = tk.Frame(frame, bg=self._bg)
            buttons.pack(fill="x", pady=(SPACING.SM, 0))
            ModernButton(
                buttons,
                text="📋 Copy Formatter Prompt",
                command=lambda: self._copy_text(self._get_formatter_prompt_text()),
                variant="primary",
                theme=self._theme_dict,
                height=28,
            ).pack(side="left")
            ModernButton(
                buttons,
                text="👁 View Full Prompt",
                command=self._show_formatter_prompt_popup,
                variant="secondary",
                theme=self._theme_dict,
                height=28,
            ).pack(side="left", padx=(SPACING.SM, 0))
            ModernButton(
                buttons,
                text="Close",
                command=popup.destroy,
                variant="secondary",
                theme=self._theme_dict,
                height=28,
            ).pack(side="right")
            try:
                popup.bind("<Escape>", lambda _e: popup.destroy())
                popup.bind("<Control-w>", lambda _e: popup.destroy())
            except Exception:
                pass
        except Exception:
            pass
    
    def _on_icon_type_change(self):
        """Toggle between emoji and image selection"""
        if self._icon_type_var.get() == "emoji":
            self._image_frame.pack_forget()
            self._emoji_frame.pack(fill="x", pady=SPACING.XS)
        else:
            self._emoji_frame.pack_forget()
            self._image_frame.pack(fill="x", pady=SPACING.XS)
    
    def _choose_icon_image(self):
        """Open file dialog for icon image"""
        file_path = filedialog.askopenfilename(
            title="Choose Icon Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")]
        )
        if file_path:
            self._image_path_var.set(file_path)
    
    def _preview_opacity(self, value):
        """Preview opacity change"""
        try:
            self.parent.root.attributes("-alpha", value)
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: Appearance (merged Look & Feel + Typography + Scale)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_appearance_section(self):
        """Build compact Appearance section"""
        container = self._content_frame
        
        # ─── Theme Preset ───
        theme_frame = self._create_neon_card(container, "🎨 Theme")
        
        # Preset selector row
        preset_row = tk.Frame(theme_frame, bg=self._accent)
        preset_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(
            preset_row, text="Preset:", font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent, fg=self._fg
        ).pack(side="left")
        
        # Get all presets - organized by category
        all_presets = {}
        if hasattr(self.parent, "THEME_PRESETS"):
            all_presets.update(self.parent.THEME_PRESETS)
        all_presets.update(FUTURISTIC_THEMES)
        all_presets["Custom"] = None
        
        # Build categorized preset list with separator labels
        self._theme_categories = {
            "── Popular ──": ["Dracula", "Catppuccin Mocha", "Tokyo Night", "One Dark", "Rosé Pine"],
            "── Dark ──": ["Obsidian", "Midnight", "Charcoal"],
            "── Vibrant ──": ["Cyber Neon", "Aurora", "Deep Ocean"],
            "── Accent ──": ["Crimson Night", "Emerald Dusk", "Royal Purple", "Golden Hour"],
            "── Nature ──": ["Sakura", "Frost", "Sunset Gradient", "Mint Fresh", "Everforest Dark"],
            "── Developer ──": ["Synthwave", "Solarized Dark", "Nord", "Monokai", "Gruvbox Dark", "Ayu Dark"],
            "── High Contrast ──": ["Pure Black", "Stark"],
            "── Light ──": ["Daylight", "Paper", "Warm Cream"],
        }
        
        # Build flat list with category headers
        self._preset_names = []
        for category, themes in self._theme_categories.items():
            self._preset_names.append(category)
            for theme_name in themes:
                if theme_name in all_presets:
                    self._preset_names.append(theme_name)
        self._preset_names.append("Custom")
        
        current_preset = self.settings.get("theme_preset", "Obsidian")
        if current_preset not in self._preset_names:
            current_preset = "Obsidian"
        
        self._theme_preset_var = tk.StringVar(value=current_preset)
        
        preset_combo = ttk.Combobox(
            preset_row, textvariable=self._theme_preset_var,
            values=self._preset_names, state="readonly", width=20,
            style="Futuristic.TCombobox"
        )
        preset_combo.pack(side="right")
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)
        
        # Theme preview swatch - enhanced
        self._preview_frame = tk.Frame(theme_frame, bg=self._accent)
        self._preview_frame.pack(fill="x", pady=SPACING.XS)
        self._build_theme_preview()
        
        # ─── Typography ───
        typo_frame = self._create_neon_card(container, "🔤 Typography")
        
        # Get available fonts
        try:
            families = sorted(set(tkfont.families()))
        except Exception:
            families = ["Segoe UI", "Arial", "Helvetica"]
        
        font_settings = self.settings.get("font", {})
        
        # UI Font with preview
        font_row1 = tk.Frame(typo_frame, bg=self._accent)
        font_row1.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(
            font_row1, text="UI Font:", font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent, fg=self._fg
        ).pack(side="left")
        
        self._font_family_var = tk.StringVar(value=font_settings.get("family", "Segoe UI"))
        
        # Custom font selector with preview
        self._ui_font_selector = FontPreviewCombobox(
            font_row1, variable=self._font_family_var,
            command=self._update_font_preview, width=180,
            font_size=10, theme=self._theme_dict, show_preview=False
        )
        self._ui_font_selector.pack(side="right")
        
        # Mono Font
        font_row2 = tk.Frame(typo_frame, bg=self._accent)
        font_row2.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(
            font_row2, text="Mono Font:", font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent, fg=self._fg
        ).pack(side="left")
        
        self._mono_family_var = tk.StringVar(value=font_settings.get("mono_family", "Consolas"))
        
        self._mono_font_selector = FontPreviewCombobox(
            font_row2, variable=self._mono_family_var,
            command=self._update_font_preview, width=180,
            font_size=10, theme=self._theme_dict, show_preview=False
        )
        self._mono_font_selector.pack(side="right")
        
        # Font preview (shows both fonts in action)
        preview_box = tk.Frame(typo_frame, bg=self._bg, highlightbackground=self._border, highlightthickness=1)
        preview_box.pack(fill="x", pady=SPACING.XS)
        
        self._font_preview_ui = tk.Label(
            preview_box, text="The quick brown fox jumps...",
            font=(self._font_family_var.get(), 11), bg=self._bg, fg=self._fg,
            anchor="w", padx=8, pady=4
        )
        self._font_preview_ui.pack(fill="x")
        
        self._font_preview_mono = tk.Label(
            preview_box, text="0123 const fn => {}",
            font=(self._mono_family_var.get(), 11), bg=self._bg, fg=self._highlight,
            anchor="w", padx=8, pady=4
        )
        self._font_preview_mono.pack(fill="x")
        
        # Bold titles toggle
        bold_row = tk.Frame(typo_frame, bg=self._accent)
        bold_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(
            bold_row, text="Bold titles:", font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent, fg=self._fg
        ).pack(side="left")
        
        self._bold_titles_var = tk.BooleanVar(value=font_settings.get("bold_titles", True))
        ToggleSwitch(bold_row, variable=self._bold_titles_var, theme=self._theme_dict, width=36, height=20).pack(side="right")
        
        # ─── Scale & Sizing ───
        scale_frame = self._create_neon_card(container, "📐 Scale & Sizing")
        
        scale_grid = tk.Frame(scale_frame, bg=self._accent)
        scale_grid.pack(fill="x")
        
        # Opacity (moved from General for logical grouping)
        opacity_row = tk.Frame(scale_grid, bg=self._accent)
        opacity_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(opacity_row, text="Opacity:", font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg).pack(side="left")
        
        self._opacity_var = tk.DoubleVar(value=self.settings.get("opacity", 0.95))
        GlowSlider(
            opacity_row, variable=self._opacity_var, from_=0.3, to=1.0,
            width=120, height=22, show_value=True, value_format="{:.0%}",
            command=self._preview_opacity, theme=self._theme_dict
        ).pack(side="right")
        
        # UI Scale (expanded range)
        ui_row = tk.Frame(scale_grid, bg=self._accent)
        ui_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(ui_row, text="UI Scale:", font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg).pack(side="left")
        
        self._ui_scale_var = tk.DoubleVar(value=self.settings.get("ui_scale", 1.0))
        GlowSlider(
            ui_row, variable=self._ui_scale_var, from_=0.7, to=1.5,
            width=120, height=22, show_value=True, value_format="{:.0%}",
            theme=self._theme_dict
        ).pack(side="right")
        
        # Bar Scale (expanded range)
        bar_row = tk.Frame(scale_grid, bg=self._accent)
        bar_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(bar_row, text="Bar Scale:", font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg).pack(side="left")
        
        self._bar_scale_var = tk.DoubleVar(value=self.settings.get("bar_scale", 1.0))
        GlowSlider(
            bar_row, variable=self._bar_scale_var, from_=0.6, to=2.0,
            width=120, height=22, show_value=True, value_format="{:.0%}",
            theme=self._theme_dict
        ).pack(side="right")
        
        # Drawer Width
        drawer_size = self.settings.get("drawer_size", {})
        
        dw_row = tk.Frame(scale_grid, bg=self._accent)
        dw_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(dw_row, text="Drawer Width:", font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg).pack(side="left")
        
        self._drawer_width_var = tk.DoubleVar(value=drawer_size.get("width", 360))
        GlowSlider(
            dw_row, variable=self._drawer_width_var, from_=240, to=800,
            width=120, height=22, show_value=True, value_format="{:.0f}px",
            theme=self._theme_dict
        ).pack(side="right")
        
        # Drawer Height
        dh_row = tk.Frame(scale_grid, bg=self._accent)
        dh_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(dh_row, text="Drawer Height:", font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg).pack(side="left")
        
        self._drawer_height_var = tk.DoubleVar(value=drawer_size.get("height", 500))
        GlowSlider(
            dh_row, variable=self._drawer_height_var, from_=300, to=900,
            width=120, height=22, show_value=True, value_format="{:.0f}px",
            theme=self._theme_dict
        ).pack(side="right")
        
        # Compact mode + Reset row
        compact_row = tk.Frame(scale_grid, bg=self._accent)
        compact_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(compact_row, text="Compact mode:", font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg).pack(side="left")
        
        self._compact_mode_var = tk.BooleanVar(value=self.settings.get("compact_mode", False))
        ToggleSwitch(compact_row, variable=self._compact_mode_var, theme=self._theme_dict, width=36, height=20).pack(side="right")
        
        # Reset size button
        reset_row = tk.Frame(scale_grid, bg=self._accent)
        reset_row.pack(fill="x", pady=SPACING.XS)
        
        ModernButton(
            reset_row, text="↺ Reset Sizes",
            command=self._reset_sizes,
            variant="secondary", theme=self._theme_dict, height=24
        ).pack(side="right")
        
        # ─── Visual Effects ───
        fx_frame = self._create_neon_card(container, "✨ Visual Effects")
        
        fx_grid = tk.Frame(fx_frame, bg=self._accent)
        fx_grid.pack(fill="x")
        fx_grid.columnconfigure(0, weight=1)
        fx_grid.columnconfigure(1, weight=1)
        
        self._glow_enabled_var = tk.BooleanVar(
            value=self.settings.get("visual", {}).get("glow_enabled", True)
        )
        self._create_toggle_cell(fx_grid, "Glow effects", self._glow_enabled_var, 0, 0)
        
        self._animations_enabled_var = tk.BooleanVar(
            value=self.settings.get("animations_enabled", True)
        )
        self._create_toggle_cell(fx_grid, "Animations", self._animations_enabled_var, 0, 1)
        
        # Animation speed
        speed_row = tk.Frame(fx_frame, bg=self._accent)
        speed_row.pack(fill="x", pady=SPACING.XS)
        
        tk.Label(speed_row, text="Animation speed:", font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent, fg=self._fg).pack(side="left")
        
        self._animation_speed_var = tk.DoubleVar(value=self.settings.get("animation_speed", 1.0))
        GlowSlider(
            speed_row, variable=self._animation_speed_var, from_=0.5, to=2.0,
            width=120, height=22, show_value=True, value_format="{:.1f}x",
            theme=self._theme_dict
        ).pack(side="right")
    
    def _update_font_preview(self, font_name: str = None):
        """Update font preview labels"""
        try:
            self._font_preview_ui.config(font=(self._font_family_var.get(), 11))
        except Exception:
            pass
        try:
            self._font_preview_mono.config(font=(self._mono_family_var.get(), 11))
        except Exception:
            pass
    
    def _reset_sizes(self):
        """Reset drawer and scale sizes to defaults"""
        self._ui_scale_var.set(1.0)
        self._bar_scale_var.set(1.0)
        self._drawer_width_var.set(360)
        self._drawer_height_var.set(500)
        self._compact_mode_var.set(False)
        Toast.show(self.window, "Sizes reset to defaults", variant="info", theme=self._theme_dict)
    
    def _build_theme_preview(self):
        """Build enhanced theme preview swatch with realistic mockup"""
        for widget in self._preview_frame.winfo_children():
            widget.destroy()
        
        preset_name = self._theme_preset_var.get()
        
        # Skip category headers
        if preset_name.startswith("──"):
            tk.Label(
                self._preview_frame, text="Select a theme from the dropdown",
                font=get_font(TYPOGRAPHY.SIZE_SM), bg=self._accent,
                fg=self._theme_dict["muted_text"]
            ).pack(pady=SPACING.SM)
            return
        
        # Get colors
        if preset_name == "Custom":
            colors = dict(self.settings["theme"])
        else:
            all_presets = {}
            if hasattr(self.parent, "THEME_PRESETS"):
                all_presets.update(self.parent.THEME_PRESETS)
            all_presets.update(FUTURISTIC_THEMES)
            colors = all_presets.get(preset_name, {})
        
        if not colors:
            return
        
        bg = colors.get("background", COLORS.BLACK)
        fg = colors.get("foreground", COLORS.TEXT_PRIMARY)
        hl = colors.get("highlight", COLORS.CYAN)
        accent = colors.get("accent", COLORS.SURFACE_1)
        muted = colors.get("muted_text", COLORS.TEXT_LOW)
        btn_bg = colors.get("button_bg", COLORS.SURFACE_3)
        border = colors.get("border", COLORS.BORDER_DEFAULT)
        hl_text = colors.get("highlight_text", "#000000")
        
        # Compact preview mockup
        preview = tk.Frame(self._preview_frame, bg=bg, height=68, highlightbackground=hl, highlightthickness=1)
        preview.pack(fill="x")
        preview.pack_propagate(False)
        
        # Top accent bar
        hl_bar = tk.Frame(preview, bg=hl, height=2)
        hl_bar.pack(fill="x")
        
        inner = tk.Frame(preview, bg=bg)
        inner.pack(fill="both", expand=True, padx=8, pady=4)
        
        # Row 1: Title + color dots
        top_row = tk.Frame(inner, bg=bg)
        top_row.pack(fill="x")
        
        tk.Label(top_row, text=preset_name, font=get_font(TYPOGRAPHY.SIZE_SM, TYPOGRAPHY.WEIGHT_BOLD), bg=bg, fg=fg).pack(side="left")
        
        # Color dots on the right
        dots_frame = tk.Frame(top_row, bg=bg)
        dots_frame.pack(side="right")
        for c in [bg, accent, btn_bg, hl, fg]:
            dot = tk.Canvas(dots_frame, width=12, height=12, bg=bg, highlightthickness=0)
            dot.pack(side="left", padx=1)
            dot.create_oval(1, 1, 11, 11, fill=c, outline=border, width=1)
        
        # Row 2: Simulated prompt item
        mock_item = tk.Frame(inner, bg=accent, highlightbackground=border, highlightthickness=1)
        mock_item.pack(fill="x", pady=(3, 2))
        
        mock_inner = tk.Frame(mock_item, bg=accent)
        mock_inner.pack(fill="x", padx=4, pady=2)
        tk.Label(mock_inner, text="Sample prompt title", font=get_font(TYPOGRAPHY.SIZE_XS), bg=accent, fg=fg, anchor="w").pack(side="left")
        tk.Label(mock_inner, text="📋", font=get_font(TYPOGRAPHY.SIZE_XS), bg=accent, fg=muted).pack(side="right")
        
        # Row 3: Mock highlight button
        btn_row = tk.Frame(inner, bg=bg)
        btn_row.pack(fill="x", pady=(1, 0))
        tk.Label(btn_row, text="  Sample Action  ", font=get_font(TYPOGRAPHY.SIZE_XS), bg=hl, fg=hl_text, padx=6, pady=1).pack(side="left")
    
    def _on_preset_change(self, event=None):
        """Handle theme preset change with validation"""
        selected = self._theme_preset_var.get()
        # Reject category headers (lines starting with ──) and revert
        if selected.startswith("──"):
            self._theme_preset_var.set(self._last_valid_preset if hasattr(self, "_last_valid_preset") else self.settings.get("theme_preset", "Obsidian"))
            return
        self._last_valid_preset = selected
        self._build_theme_preview()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: Shortcuts
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_shortcuts_section(self):
        """Build compact Shortcuts section"""
        container = self._content_frame
        
        # ─── Global Hotkey ───
        hotkey_frame = self._create_neon_card(container, "🚀 Global Hotkey")
        
        # Predefined hotkeys
        predefined = ["None", "alt+z", "alt+c", "ctrl+alt+space", "ctrl+shift+space"]
        for ch in string.ascii_lowercase[:6]:
            predefined.append(f"ctrl+alt+{ch}")
        
        saved_hotkey = (self.settings.get("teleport_hotkey", "alt+z") or "").strip() or "alt+z"
        saved_hotkey = self._normalize_hotkey(saved_hotkey)
        
        self._hotkey_var = tk.StringVar(value=saved_hotkey if saved_hotkey in predefined else "")
        self._hotkey_custom_var = tk.StringVar(value=saved_hotkey if saved_hotkey not in predefined else "")
        self._capturing_hotkey = False
        self._hotkey_capture_press_bind = None
        self._hotkey_capture_escape_bind = None
        
        # Quick select row
        quick_row = tk.Frame(hotkey_frame, bg=self._accent)
        quick_row.pack(fill="x", pady=SPACING.XS)
        
        quick_label = tk.Label(
            quick_row,
            text="Quick:",
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent,
            fg=self._fg
        )
        quick_label.pack(side="left")
        
        combo = ttk.Combobox(
            quick_row, textvariable=self._hotkey_var, values=predefined,
            state="readonly", width=16, style="Futuristic.TCombobox"
        )
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", self._on_quick_hotkey_selected)
        self._attach_tooltip(
            (quick_label, combo),
            "Pick a known-good shortcut preset. Choosing one clears the custom field."
        )
        
        # Custom entry row
        custom_row = tk.Frame(hotkey_frame, bg=self._accent)
        custom_row.pack(fill="x", pady=SPACING.XS)
        
        custom_label = tk.Label(
            custom_row,
            text="Custom:",
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent,
            fg=self._fg
        )
        custom_label.pack(side="left")
        
        custom_entry = tk.Entry(
            custom_row, textvariable=self._hotkey_custom_var, width=14,
            font=get_mono_font(TYPOGRAPHY.SIZE_SM), bg=self._bg, fg=self._fg,
            insertbackground=self._fg, relief="flat",
            highlightbackground=self._border, highlightthickness=1
        )
        custom_entry.pack(side="right", padx=(0, SPACING.XS))
        custom_entry.bind("<KeyRelease>", self._on_custom_hotkey_changed)

        self._record_hotkey_btn = ModernButton(
            custom_row,
            text="Record",
            command=self._start_hotkey_capture,
            variant="secondary",
            theme=self._theme_dict,
            height=24,
            font_size=TYPOGRAPHY.SIZE_XS,
            width=70,
        )
        self._record_hotkey_btn.pack(side="right")
        self._attach_tooltip(
            (custom_label, custom_entry, self._record_hotkey_btn),
            "Type a hotkey like alt+z, or click Record and press the combo once."
        )

        self._hotkey_status = tk.StringVar(value="")
        status_lbl = tk.Label(
            hotkey_frame,
            textvariable=self._hotkey_status,
            font=get_font(TYPOGRAPHY.SIZE_XS),
            bg=self._accent,
            fg=self._theme_dict["muted_text"],
            anchor="w",
            justify="left",
        )
        status_lbl.pack(fill="x", pady=(2, 0))
        self._set_hotkey_status()
        
        # Suppress toggle
        suppress_row = tk.Frame(hotkey_frame, bg=self._accent)
        suppress_row.pack(fill="x", pady=SPACING.XS)
        
        suppress_label = tk.Label(
            suppress_row,
            text="Suppress keystroke:",
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent,
            fg=self._fg
        )
        suppress_label.pack(side="left")
        
        self._suppress_var = tk.BooleanVar(value=self.settings.get("teleport_hotkey_suppress", False))
        suppress_toggle = ToggleSwitch(suppress_row, variable=self._suppress_var, theme=self._theme_dict, width=40, height=22)
        suppress_toggle.pack(side="right")
        self._attach_tooltip(
            (suppress_label, suppress_toggle),
            "When enabled, the app blocks the shortcut keypress after activating teleport.",
        )
        
        # ─── Quick Reference ───
        ref_frame = self._create_neon_card(container, "⌨️ Quick Reference")
        
        shortcuts = [
            ("Alt+Z", "Teleport"),
            ("Alt+C", "Teleport Alias"),
            ("Ctrl+F", "Search"),
            ("↑/↓", "Navigate"),
            ("Enter", "Copy"),
            ("Esc", "Close"),
            ("Ctrl+Q", "Quit"),
        ]
        
        ref_grid = tk.Frame(ref_frame, bg=self._accent)
        ref_grid.pack(fill="x")
        
        for i, (key, desc) in enumerate(shortcuts):
            row = i // 3
            col = i % 3
            
            cell = tk.Frame(ref_grid, bg=self._accent)
            cell.grid(row=row, column=col, sticky="ew", padx=SPACING.XS, pady=2)
            ref_grid.columnconfigure(col, weight=1)
            
            key_lbl = tk.Label(
                cell, text=key, font=get_mono_font(TYPOGRAPHY.SIZE_XS),
                bg=self._bg, fg=self._highlight, padx=4, pady=1
            )
            key_lbl.pack(side="left")
            
            tk.Label(
                cell, text=desc, font=get_font(TYPOGRAPHY.SIZE_XS),
                bg=self._accent, fg=self._fg
            ).pack(side="left", padx=4)

    def _normalize_hotkey(self, hotkey: str) -> str:
        """Normalize hotkey text using the parent hotkey service when available."""
        value = (hotkey or "").strip()
        if not value:
            return ""
        try:
            if hasattr(self.parent, "hotkey_service") and hasattr(self.parent.hotkey_service, "normalize_hotkey_string"):
                normalized = self.parent.hotkey_service.normalize_hotkey_string(value)
                if normalized:
                    return normalized
        except Exception:
            pass
        return value.lower().replace(" ", "")

    def _set_hotkey_status(self, text: str = ""):
        """Update helper text below the hotkey editor."""
        if text:
            self._hotkey_status.set(text)
            return
        available = False
        try:
            available = bool(
                hasattr(self.parent, "hotkey_service")
                and hasattr(self.parent.hotkey_service, "is_available")
                and self.parent.hotkey_service.is_available()
            )
        except Exception:
            available = False
        if available:
            self._hotkey_status.set("Global hotkeys available.")
        else:
            self._hotkey_status.set("Global hotkeys unavailable here; shortcut still works while Promptoire is focused.")

    def _on_quick_hotkey_selected(self, _event=None):
        try:
            quick_value = (self._hotkey_var.get() or "").strip()
            if quick_value and quick_value != "None":
                self._hotkey_custom_var.set("")
            self._set_hotkey_status()
        except Exception:
            pass

    def _on_custom_hotkey_changed(self, _event=None):
        try:
            custom_text = (self._hotkey_custom_var.get() or "").strip()
            if custom_text:
                self._hotkey_var.set("")
            self._set_hotkey_status()
        except Exception:
            pass

    def _parse_event_hotkey(self, event) -> str:
        """Convert a Tk keypress event to normalized hotkey format."""
        if not event:
            return ""

        key = (event.keysym or "").lower()
        if key in {"shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r", "meta_l", "meta_r"}:
            return ""

        state = int(getattr(event, "state", 0))
        mods = []
        if state & 0x0004:
            mods.append("ctrl")
        if state & 0x0001:
            mods.append("shift")
        if (state & 0x0008) or (state & 0x20000):
            mods.append("alt")

        key_map = {
            "return": "enter",
            "escape": "esc",
            "space": "space",
            "prior": "page up",
            "next": "page down",
        }
        if len(key) == 1:
            main = key
        else:
            main = key_map.get(key, key)
        return self._normalize_hotkey("+".join(mods + [main]))

    def _stop_hotkey_capture(self):
        """Clear key-capture bindings used by Record."""
        try:
            if self._hotkey_capture_press_bind:
                self.window.unbind("<KeyPress>", self._hotkey_capture_press_bind)
        except Exception:
            pass
        try:
            if self._hotkey_capture_escape_bind:
                self.window.unbind("<Escape>", self._hotkey_capture_escape_bind)
        except Exception:
            pass
        self._hotkey_capture_press_bind = None
        self._hotkey_capture_escape_bind = None
        self._capturing_hotkey = False
        try:
            if hasattr(self, "_record_hotkey_btn") and self._record_hotkey_btn:
                self._record_hotkey_btn.set_text("Record")
        except Exception:
            pass

    def _cancel_hotkey_capture(self, _event=None):
        self._stop_hotkey_capture()
        self._set_hotkey_status("Hotkey capture canceled.")
        return "break"

    def _capture_hotkey_press(self, event):
        if not self._capturing_hotkey:
            return None
        hotkey = self._parse_event_hotkey(event)
        if not hotkey:
            return "break"
        if hotkey == "esc":
            return self._cancel_hotkey_capture(event)
        self._hotkey_custom_var.set(hotkey)
        self._hotkey_var.set("")
        self._stop_hotkey_capture()
        self._set_hotkey_status(f"Captured: {hotkey}")
        return "break"

    def _start_hotkey_capture(self):
        if self._capturing_hotkey:
            self._cancel_hotkey_capture()
            return
        self._capturing_hotkey = True
        try:
            if hasattr(self, "_record_hotkey_btn") and self._record_hotkey_btn:
                self._record_hotkey_btn.set_text("Press keys...")
        except Exception:
            pass
        self._set_hotkey_status("Recording: press your shortcut now (Esc to cancel).")
        try:
            self.window.focus_force()
            self.window.lift()
        except Exception:
            pass
        self._hotkey_capture_press_bind = self.window.bind("<KeyPress>", self._capture_hotkey_press, add="+")
        self._hotkey_capture_escape_bind = self.window.bind("<Escape>", self._cancel_hotkey_capture, add="+")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: Data
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_data_section(self):
        """Build compact Data section"""
        container = self._content_frame
        
        # ─── Prompts Library ───
        lib_frame = self._create_neon_card(container, "📚 Prompts Library")
        
        # Action buttons row
        btn_row = tk.Frame(lib_frame, bg=self._accent)
        btn_row.pack(fill="x", pady=SPACING.XS)
        
        ModernButton(
            btn_row, text="⬆ Import", command=self._do_import,
            variant="secondary", theme=self._theme_dict, height=28
        ).pack(side="left", padx=(0, SPACING.SM))
        
        ModernButton(
            btn_row, text="⬇ Export", command=self._do_export,
            variant="secondary", theme=self._theme_dict, height=28
        ).pack(side="left", padx=(0, SPACING.SM))
        
        ModernButton(
            btn_row, text="🕒 Backup", command=self._do_backup,
            variant="secondary", theme=self._theme_dict, height=28
        ).pack(side="left", padx=(0, SPACING.SM))
        
        ModernButton(
            btn_row, text="📂 Open", command=self._open_prompts_folder,
            variant="secondary", theme=self._theme_dict, height=28
        ).pack(side="left")
        
        # ─── Formatter Helper ───
        format_frame = self._create_neon_card(container, "📋 Formatter Helper")

        tk.Label(
            format_frame,
            text="Use this for converting raw prompt notes into valid Promptoire JSON.",
            font=get_font(TYPOGRAPHY.SIZE_XS),
            bg=self._accent,
            fg=self._theme_dict["muted_text"],
            anchor="w",
            justify="left",
            wraplength=620,
        ).pack(fill="x", pady=(0, SPACING.XS))

        fmt_actions = tk.Frame(format_frame, bg=self._accent)
        fmt_actions.pack(fill="x")
        ModernButton(
            fmt_actions,
            text="📋 Copy Formatter Prompt",
            command=lambda: self._copy_text(self._get_formatter_prompt_text()),
            variant="primary",
            theme=self._theme_dict,
            height=28,
        ).pack(side="left", padx=(0, SPACING.SM))
        ModernButton(
            fmt_actions,
            text="👁 View Full Prompt",
            command=self._show_formatter_prompt_popup,
            variant="secondary",
            theme=self._theme_dict,
            height=28,
        ).pack(side="left")
    
    def _copy_text(self, text: str):
        """Copy text to clipboard"""
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
            self.window.update()
            Toast.show(self.window, "Copied!", variant="success", theme=self._theme_dict)
        except Exception:
            pass
    
    def _do_import(self):
        try:
            if hasattr(self.parent, "import_prompts"):
                self.parent.import_prompts()
        except Exception as e:
            Toast.show(self.window, f"Import failed: {str(e)[:30]}", variant="error", theme=self._theme_dict)
    
    def _do_export(self):
        try:
            if hasattr(self.parent, "export_prompts"):
                self.parent.export_prompts()
        except Exception as e:
            Toast.show(self.window, f"Export failed: {str(e)[:30]}", variant="error", theme=self._theme_dict)
    
    def _do_backup(self):
        try:
            if hasattr(self.parent, "backup_prompts"):
                self.parent.backup_prompts()
                Toast.show(self.window, "Backup created!", variant="success", theme=self._theme_dict)
        except Exception as e:
            Toast.show(self.window, f"Backup failed: {str(e)[:30]}", variant="error", theme=self._theme_dict)
    
    def _open_prompts_folder(self):
        try:
            if hasattr(self.parent, "open_prompts_folder"):
                self.parent.open_prompts_folder()
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: About
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_about_section(self):
        """Build About + Guide section."""
        container = self._content_frame
        
        # ─── App Info ───
        info_frame = self._create_neon_card(container, "ℹ️ Promptoire")
        tk.Label(
            info_frame,
            text="Promptoire is a compact floating prompt library for fast copy and reuse.",
            font=get_font(TYPOGRAPHY.SIZE_SM),
            bg=self._accent,
            fg=self._fg,
            anchor="w",
            justify="left",
            wraplength=620,
        ).pack(fill="x", pady=(0, SPACING.XS))

        meta = tk.Frame(info_frame, bg=self._accent)
        meta.pack(fill="x")
        tk.Label(
            meta,
            text="Version v1.0.0",
            font=get_mono_font(TYPOGRAPHY.SIZE_XS),
            bg=self._highlight,
            fg=get_contrast_color(self._highlight),
            padx=8,
            pady=2,
        ).pack(side="left")

        if hasattr(self.parent, "open_coffee_url"):
            ModernButton(
                meta,
                text="☕ Support",
                command=self.parent.open_coffee_url,
                variant="secondary",
                theme=self._theme_dict,
                height=26,
            ).pack(side="right")

        # ─── Consolidated Guide ───
        guide_frame = self._create_neon_card(container, "📘 User Guide")
        guide_lines = [
            "• Open Settings by double-clicking the Prompt Library tab or right-clicking it.",
            "• Prompt Library: browse and copy prompts quickly.",
            "• Prompt Editor: edit prompts and drag items to reorder.",
            "• Data tab: import, export, backup, and open prompt files.",
            "• Formatter: copy the formatter prompt from the General tab.",
        ]
        for line in guide_lines:
            tk.Label(
                guide_frame,
                text=line,
                font=get_font(TYPOGRAPHY.SIZE_XS),
                bg=self._accent,
                fg=self._fg,
                anchor="w",
                justify="left",
                wraplength=620,
            ).pack(fill="x", pady=(0, 1))

        actions = tk.Frame(guide_frame, bg=self._accent)
        actions.pack(fill="x", pady=(SPACING.XS, 0))
        ModernButton(
            actions,
            text="Open Full Guide",
            command=self.show_user_guide_popup,
            variant="primary",
            theme=self._theme_dict,
            height=28,
        ).pack(side="left", padx=(0, SPACING.SM))
        ModernButton(
            actions,
            text="View Formatter Prompt",
            command=self._show_formatter_prompt_popup,
            variant="secondary",
            theme=self._theme_dict,
            height=28,
        ).pack(side="left")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _create_neon_card(self, parent, title: str, collapsed: bool = False) -> tk.Frame:
        """Create a compact card with neon accent"""
        # Outer container - tight vertical spacing
        outer = tk.Frame(parent, bg=self._bg)
        outer.pack(fill="x", pady=1)
        
        # Card with subtle border
        card = tk.Frame(
            outer, bg=self._accent,
            highlightbackground=self._border, highlightthickness=1
        )
        card.pack(fill="x")
        
        # Header (if title)
        if title:
            header = tk.Frame(card, bg=self._accent)
            header.pack(fill="x", padx=SPACING.XS, pady=(SPACING.XS, 1))
            
            # Neon accent bar
            accent_bar = tk.Frame(header, bg=self._highlight, width=3)
            accent_bar.pack(side="left", fill="y", padx=(0, SPACING.XS))
            
            tk.Label(
                header, text=title, font=get_font(TYPOGRAPHY.SIZE_SM, TYPOGRAPHY.WEIGHT_BOLD),
                bg=self._accent, fg=self._fg
            ).pack(side="left")
            
            # Collapse toggle
            if collapsed:
                card._collapsed = True
                card._toggle_icon = tk.Label(
                    header, text="▸", font=get_font(TYPOGRAPHY.SIZE_XS),
                    bg=self._accent, fg=self._theme_dict["muted_text"], cursor="hand2"
                )
                card._toggle_icon.pack(side="right")
        
        # Content area - tighter padding
        content = tk.Frame(card, bg=self._accent)
        
        if not collapsed:
            content.pack(fill="x", padx=SPACING.XS, pady=(0, SPACING.XS))
        
        # Store content reference
        card._content = content
        
        # Toggle handler
        if title and collapsed:
            def toggle(event=None):
                if card._collapsed:
                    content.pack(fill="x", padx=SPACING.XS, pady=(0, SPACING.XS))
                    card._toggle_icon.config(text="▾")
                    card._collapsed = False
                else:
                    content.pack_forget()
                    card._toggle_icon.config(text="▸")
                    card._collapsed = True
            
            header.bind("<Button-1>", toggle)
            card._toggle_icon.bind("<Button-1>", toggle)
        
        return content
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _reset_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            self.settings = copy.deepcopy(self.parent.default_settings)
            self._load_section(self._current_section)
            Toast.show(self.window, "Reset! Click Save to apply.", variant="info", theme=self._theme_dict)
    
    def _save_settings(self):
        """Save settings"""
        try:
            self._collect_settings()
            self.parent.settings = self.settings
            self.parent.save_settings()
            self._apply_to_parent()
            
            Toast.show(self.window, "✓ Saved!", variant="success", duration=1500, theme=self._theme_dict)
            self._save_btn.set_text("✓ Saved!")
            self.window.after(1500, lambda: self._save_btn.set_text("💾 Save"))
            try:
                if hasattr(self, "_tab_save_btn") and self._tab_save_btn:
                    self._tab_save_btn.set_text("✓ Saved")
                    self.window.after(1200, lambda: self._tab_save_btn.set_text("Save"))
            except Exception:
                pass
            return True
            
        except Exception as e:
            Toast.show(self.window, f"Error: {str(e)[:40]}", variant="error", theme=self._theme_dict)
            return False
    
    def _collect_settings(self):
        """Collect all settings from UI"""
        # Icon
        if hasattr(self, "_icon_type_var"):
            self.settings["icon"]["type"] = self._icon_type_var.get()
            if self._icon_type_var.get() == "emoji":
                self.settings["icon"]["value"] = self._emoji_var.get()
            else:
                self.settings["icon"]["value"] = self._image_path_var.get()
        
        # General - Behavior
        if hasattr(self, "_auto_hide_var"):
            self.settings["auto_hide"] = self._auto_hide_var.get()
        if hasattr(self, "_start_hidden_var"):
            self.settings["start_hidden"] = self._start_hidden_var.get()
        if hasattr(self, "_auto_paste_var"):
            self.settings["auto_paste"] = self._auto_paste_var.get()
        if hasattr(self, "_spring_loaded_var"):
            self.settings["spring_loaded_close"] = self._spring_loaded_var.get()
        if hasattr(self, "_always_on_top_var"):
            self.settings["always_on_top"] = self._always_on_top_var.get()
        if hasattr(self, "_paste_delay_var"):
            self.settings["paste_delay_ms"] = int(self._paste_delay_var.get())
        
        # Appearance - Theme: write actual color values, not just the name
        if hasattr(self, "_theme_preset_var"):
            preset = self._theme_preset_var.get()
            if not preset.startswith("──"):
                self.settings["theme_preset"] = preset
                # Look up the actual theme colors and write them into settings
                if preset != "Custom":
                    all_presets = {}
                    if hasattr(self.parent, "THEME_PRESETS"):
                        all_presets.update(self.parent.THEME_PRESETS)
                    all_presets.update(FUTURISTIC_THEMES)
                    theme_colors = all_presets.get(preset)
                    if theme_colors:
                        # Write every color key from the preset into settings["theme"]
                        for key, value in theme_colors.items():
                            self.settings["theme"][key] = value
        
        # Appearance - Opacity (now in Appearance section)
        if hasattr(self, "_opacity_var"):
            self.settings["opacity"] = self._opacity_var.get()
        
        # Appearance - Scale & Sizing
        if hasattr(self, "_ui_scale_var"):
            self.settings["ui_scale"] = self._ui_scale_var.get()
        if hasattr(self, "_bar_scale_var"):
            self.settings["bar_scale"] = self._bar_scale_var.get()
        if hasattr(self, "_compact_mode_var"):
            self.settings["compact_mode"] = self._compact_mode_var.get()
        if hasattr(self, "_drawer_width_var"):
            self.settings.setdefault("drawer_size", {})
            self.settings["drawer_size"]["width"] = int(self._drawer_width_var.get())
        if hasattr(self, "_drawer_height_var"):
            self.settings.setdefault("drawer_size", {})
            self.settings["drawer_size"]["height"] = int(self._drawer_height_var.get())
        
        # Appearance - Visual Effects
        if hasattr(self, "_glow_enabled_var"):
            self.settings.setdefault("visual", {})
            self.settings["visual"]["glow_enabled"] = self._glow_enabled_var.get()
        if hasattr(self, "_animations_enabled_var"):
            self.settings["animations_enabled"] = self._animations_enabled_var.get()
        if hasattr(self, "_animation_speed_var"):
            self.settings["animation_speed"] = self._animation_speed_var.get()
        
        # Fonts
        if hasattr(self, "_font_family_var"):
            self.settings.setdefault("font", {})
            self.settings["font"]["family"] = self._font_family_var.get()
        if hasattr(self, "_mono_family_var"):
            self.settings["font"]["mono_family"] = self._mono_family_var.get()
        if hasattr(self, "_bold_titles_var"):
            self.settings["font"]["bold_titles"] = self._bold_titles_var.get()
        
        # Hotkeys
        if hasattr(self, "_hotkey_var"):
            hotkey_custom = (self._hotkey_custom_var.get() or "").strip()
            hotkey_quick = (self._hotkey_var.get() or "").strip()
            hotkey_raw = hotkey_custom or hotkey_quick
            hotkey = self._normalize_hotkey(hotkey_raw)
            if hotkey and hotkey != "none":
                self.settings["teleport_hotkey"] = hotkey
            else:
                self.settings["teleport_hotkey"] = ""
        if hasattr(self, "_suppress_var"):
            self.settings["teleport_hotkey_suppress"] = self._suppress_var.get()
        
        # Advanced
        if hasattr(self, "_virtual_scroll_var"):
            self.settings["use_virtual_scrolling"] = self._virtual_scroll_var.get()
        if hasattr(self, "_fuzzy_var"):
            self.settings["search_fuzzy"] = self._fuzzy_var.get()
        if hasattr(self, "_highlight_var"):
            self.settings["search_highlight"] = self._highlight_var.get()
    
    def _apply_to_parent(self):
        """Apply settings to parent application"""
        try:
            from .design_system import set_ui_scale, set_compact_mode, set_bar_scale
            set_ui_scale(self.settings.get("ui_scale", 1.0))
            set_bar_scale(self.settings.get("bar_scale", 1.0))
            set_compact_mode(self.settings.get("compact_mode", False))
        except Exception:
            pass
        
        try:
            self.parent.update_icon()
            self.parent.root.attributes("-alpha", self.settings["opacity"])
            self.parent.root.configure(bg=self.settings["theme"]["background"])
            
            if hasattr(self.parent, "_apply_global_ttk_style"):
                self.parent._apply_global_ttk_style()
            
            if hasattr(self.parent, "setup_window"):
                self.parent.setup_window()
            if hasattr(self.parent, "create_widgets"):
                for child in list(self.parent.root.children.values()):
                    try:
                        child.destroy()
                    except Exception:
                        pass
                self.parent.create_widgets()

            if hasattr(self.parent, "apply_settings_update"):
                self.parent.apply_settings_update()
            
            if hasattr(self.parent, "register_hotkey"):
                self.parent.register_hotkey()
        except Exception as e:
            print(f"Error applying settings: {e}")
    
    def _on_close(self):
        """Handle window close"""
        try:
            self._stop_hotkey_capture()
        except Exception:
            pass

        try:
            self.parent.root.attributes("-alpha", self.parent.settings.get("opacity", 0.95))
        except Exception:
            pass
        
        if hasattr(self.parent, "settings_panel"):
            self.parent.settings_panel = None
        
        self.window.destroy()
