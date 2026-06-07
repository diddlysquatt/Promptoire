#!/usr/bin/env python3
"""
Promptoire - A floating prompt library for Windows 11
Minimal, always-accessible launcher for your best LLM prompts
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, colorchooser
from tkinter import font as tkfont
import json
import os
from pathlib import Path
import sys
import base64
from io import BytesIO
import shutil
import subprocess
import re
import time
import threading
from datetime import datetime
from collections import OrderedDict
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import uuid

# Import types and constants
try:
    from src.types.PromptTypes import Prompt, Category, PromptLibrary, PromptType
    from src.types.SettingsTypes import Settings, ThemeColors, IconSettings, Position, Size, TraySettings, IconType, ThemePreset
    from src.types.EventTypes import Event, EventType, EventSeverity, EventData, UserAction, EventLog
    from src.core.ConfigManager import ConfigManager
    from src.core.StateManager import StateManager
    from src.constants import *
except ImportError:
    # Fallback if modules are not available
    pass

# Import security utilities
try:
    from src.utils.security import safe_open_file_location, validate_input, sanitize_filename, secure_file_operation
except ImportError:
    # Fallback implementations if security module is not available
    import platform
    import subprocess

# Import optimized UI components
try:
    from src.ui.components.VirtualScrolledList import VirtualScrolledList
    from src.ui.performance.UIOptimizer import UIOptimizer
    VIRTUAL_SCROLLING_AVAILABLE = True
except ImportError:
    VIRTUAL_SCROLLING_AVAILABLE = False

# Import modern UI components
try:
    from src.ui.settings_panel_v2 import SettingsPanelV2
    from src.ui.design_system import (
        COLORS, FUTURISTIC_THEMES, configure_ttk_styles,
        # Animation system
        Easing, AnimationController, create_smooth_animation,
        # Scaling system
        set_ui_scale, get_ui_scale, set_bar_scale, get_bar_scale,
        get_scaled, get_scaled_spacing, set_compact_mode, is_compact_mode,
        get_bar_scaled, get_fully_scaled, get_responsive_size,
        calculate_responsive_dimensions
    )
    from src.ui.drawer_styles import DrawerStyles
    MODERN_UI_AVAILABLE = True
except ImportError:
    MODERN_UI_AVAILABLE = False
    SettingsPanelV2 = None
    # Fallback stubs for animation/scaling if design system not available
    class Easing:
        @staticmethod
        def ease_out_cubic(t): return 1 - (1 - t) ** 3
        @staticmethod
        def ease_out_quart(t): return 1 - (1 - t) ** 4
    AnimationController = None
    def get_scaled(v): return v
    def get_bar_scaled(v): return v
    def set_bar_scale(s): pass
    def get_bar_scale(): return 1.0

# Import error handling and logging utilities
try:
    from src.utils.logger import get_logger, setup_logging, LogOperation
    from src.utils.error_handlers import (
        ErrorHandler, handle_exceptions, safe_execute, safe_file_operation,
        ErrorContext, PromptoireError, ConfigurationError, FileOperationError,
        DataValidationError, UIError
    )
except ImportError:
    # Fallback implementations if error handling modules are not available
    import logging
    from logging.handlers import RotatingFileHandler

# Import service layer
try:
    from src.services.FileService import FileService
    from src.services.ClipboardService import ClipboardService
    from src.services.HotkeyService import HotkeyService
    from src.services.SearchService import SearchService
    from src.services.PromptService import PromptService
    from src.services.AnalyticsService import AnalyticsService
    from src.core.ProfileService import ProfileService
    from src.ui.settings.ProfileManager import ProfileManager
    from src.utils.cache import get_cache
except ImportError:
    # Fallback implementations if service modules are not available
    class FileService:
        def __init__(self):
            pass
    class ClipboardService:
        def __init__(self, root=None):
            self.root = root
    class HotkeyService:
        def __init__(self):
            pass
    class SearchService:
        def __init__(self, cache_service=None, **kwargs):
            pass
        def build_search_index(self, data):
            pass
        def search(self, query, callback, **kwargs):
            # Fallback immediate callback
            callback([], None)
        def destroy(self):
            pass
    class ProfileService:
        def __init__(self):
            pass
    class ProfileManager:
        def __init__(self, parent, config_manager, on_profile_change=None):
            pass

    def get_cache(cache_type="memory", **kwargs):
        return None

    def get_logger(name="Promptoire"):
        return logging.getLogger(name)

    def setup_logging(name="Promptoire", log_dir=None):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        return logger

    class LogOperation:
        def __init__(self, name, logger):
            self.name = name
            self.logger = logger
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    class PromptoireError(Exception):
        pass

    class ConfigurationError(PromptoireError):
        pass

    class FileOperationError(PromptoireError):
        pass

    class DataValidationError(PromptoireError):
        pass

    class UIError(PromptoireError):
        pass

    def handle_exceptions(exception_types=Exception, return_value=None, log_errors=True, show_user_message=False, context=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exception_types:
                    return return_value
            return wrapper
        return decorator

    def safe_execute(func, args=(), kwargs=None, default_return=None, exception_types=Exception, context=None):
        kwargs = kwargs or {}
        try:
            return func(*args, **kwargs)
        except exception_types:
            return default_return

    def safe_file_operation(operation, file_path, **kwargs):
        path = Path(file_path)
        try:
            if operation == 'exists':
                return path.exists()
            elif operation == 'read':
                return path.read_text(encoding='utf-8') if path.exists() else ""
            elif operation == 'write':
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(kwargs.get('content', ''), encoding='utf-8')
                return True
            elif operation == 'delete':
                if path.exists():
                    path.unlink()
                    return True
                return False
        except Exception:
            return False

    class ErrorContext:
        def __init__(self, operation_name, exception_types=Exception, return_value=None, log_errors=True, context=None):
            self.operation_name = operation_name
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    def safe_open_file_location(file_path):
        """Fallback implementation"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            parent_dir = path.parent
            if platform.system() == "Windows":
                os.startfile(parent_dir)
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(parent_dir)], check=True, timeout=10)
            else:
                subprocess.run(["xdg-open", str(parent_dir)], check=True, timeout=10)
            return True
        except:
            return False

    def validate_input(input_str, max_length=1000, allowed_chars=None):
        """Fallback implementation"""
        if not isinstance(input_str, str):
            return False
        if len(input_str) > max_length or len(input_str) == 0:
            return False
        return True

    def sanitize_filename(filename):
        """Fallback implementation"""
        if not isinstance(filename, str):
            return "invalid"
        import re
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        sanitized = sanitized.strip(' .')
        if not sanitized:
            sanitized = "unnamed"
        return sanitized

    def secure_file_operation(file_path, operation, **kwargs):
        """Fallback implementation"""
        try:
            path = Path(file_path)
            if operation == 'exists':
                return path.exists()
            elif operation == 'mkdir':
                path.mkdir(parents=True, exist_ok=True)
                return True
            return False
        except:
            return False
try:
    import msvcrt
    MSVCRT_AVAILABLE = True
except Exception:
    MSVCRT_AVAILABLE = False
import ctypes
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

import copy
import traceback

# Optional system-tray support
try:
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# CRITICAL: Set DPI awareness at module level before any Tk windows are created
# This ensures proper window styling on Windows, especially for borderless windows
if sys.platform == "win32":
    try:
        # Windows 10 version 1703+ (SetProcessDpiAwarenessContext is best, but not always available)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    except Exception:
        pass


class Promptoire:
    def _init_theme_presets(self):
        """
        Initialize theme presets using FUTURISTIC_THEMES from design_system.py
        as the single source of truth.
        
        All themes are pre-validated for WCAG AA contrast compliance in design_system.py.
        This method applies additional runtime validation and auto-fixes if needed.
        """
        try:
            # Import contrast utilities from design_system
            from src.ui.design_system import (
                FUTURISTIC_THEMES, auto_fix_theme_contrast, validate_theme_contrast,
                get_contrast_color, ensure_contrast, WCAG_AA_NORMAL, WCAG_UI_COMPONENTS
            )
            
            # Use FUTURISTIC_THEMES as the primary source (curated, WCAG-compliant themes)
            presets = copy.deepcopy(FUTURISTIC_THEMES)
            
            # Add "Custom" option for user-defined themes
            presets["Custom"] = None
            
            # Apply runtime contrast validation to ensure all themes are safe
            for name, theme in list(presets.items()):
                if theme is not None:
                    # Auto-fix any contrast issues (should be none since themes are pre-validated)
                    validation = validate_theme_contrast(theme)
                    if not validation["valid"]:
                        self.logger.warning(f"Theme '{name}' has contrast issues: {validation['issues']}")
                        presets[name] = auto_fix_theme_contrast(theme)
                    
                    # Ensure glow_color exists
                    if "glow_color" not in presets[name]:
                        highlight = presets[name].get("highlight", "#00e5e5")
                        presets[name]["glow_color"] = f"{highlight}40"
            
            return presets
            
        except ImportError as e:
            # Fallback if design_system imports fail - provide minimal default
            self.logger.warning(f"Could not import from design_system: {e}")
            return {
                "Obsidian": {
                    "background": "#0a0a0a", "foreground": "#f5f5f5", "accent": "#1a1a1a",
                    "button_bg": "#262626", "button_hover": "#333333", "border": "#3a3a3a",
                    "highlight": "#00e5e5", "highlight_text": "#000000", "slider_trough": "#1a1a1a",
                    "category_bar": "#00e5e5", "muted_text": "#a3a3a3", "category_text": "#000000",
                    "glow_color": "#00e5e540"
                },
                "Custom": None
            }
        except Exception as e:
            self.logger.error(f"Error initializing theme presets: {e}")
            return {
                "Obsidian": {
                    "background": "#0a0a0a", "foreground": "#f5f5f5", "accent": "#1a1a1a",
                    "button_bg": "#262626", "button_hover": "#333333", "border": "#3a3a3a",
                    "highlight": "#00e5e5", "highlight_text": "#000000", "slider_trough": "#1a1a1a",
                    "category_bar": "#00e5e5", "muted_text": "#a3a3a3", "category_text": "#000000",
                    "glow_color": "#00e5e540"
                },
                "Custom": None
            }
    def __init__(self):
        # Setup centralized logging
        self.logger = get_logger("Promptoire")
        self.logger.info("Initializing Promptoire application")
        # Ensure Windows sees us as a distinct app (taskbar grouping, notifications)
        try:
            if sys.platform == "win32":
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Promptoire.App")
        except Exception:
            pass
        self.root = tk.Tk()

        # IMPORTANT: Withdraw window immediately to prevent flickering during setup
        self.root.withdraw()

        # Initialize data + defaults early so settings paths exist
        self.setup_data()
        # Centralized theme presets (no gradients/patterns)
        self.THEME_PRESETS = self._init_theme_presets()
        # Ensure settings exist before any dependent services initialize
        self.settings = copy.deepcopy(self.default_settings)

        # Initialize configuration and state managers
        self.config_manager = ConfigManager(self.settings_file)
        self.state_manager = StateManager()

        # Initialize profile service
        self.profile_service = ProfileService()
        self.profile_manager = None

        # Load settings before services that depend on them
        self.load_settings()
        # Feature flags
        self.use_virtual_scrolling = bool(self.settings.get("use_virtual_scrolling", False)) and VIRTUAL_SCROLLING_AVAILABLE

        # Initialize service layer
        self.file_service = FileService()
        self.clipboard_service = ClipboardService(self.root)
        self.hotkey_service = HotkeyService()

        # Initialize enhanced prompt services
        self.prompt_service = PromptService()
        self.analytics_service = AnalyticsService()

        # Initialize search and caching services
        self.cache_service = get_cache("persistent", cache_dir="cache", max_memory_size=500)
        self.search_service = SearchService(
            cache_service=self.cache_service,
            fuzzy_threshold=self.settings.get("search_fuzzy_threshold", 0.6),
            search_delay_ms=self.settings.get("search_delay_ms", 300),
            enable_fuzzy=self.settings.get("search_fuzzy", False)  # Disabled by default for performance
        )

        self.expanded = False
        self.drawer = None
        # Keep single instances of secondary windows
        self.settings_panel = None
        self.prompt_editor = None
        self.collapsed_categories = set()  # Track collapsed categories
        # Session-only matrix state
        self._last_copied_category_path = ""
        # Runtime cache for prompt search blobs (keyed by prompt id/signature).
        self._prompt_search_cache = {}

        # Initialize optimized UI components
        if VIRTUAL_SCROLLING_AVAILABLE:
            self._init_optimized_ui()
        self.setup_window()
        # Immediately enforce borderless after window setup
        self._enforce_borderless()
        self.create_widgets()
        self.load_prompts()
        # Ensure stable IDs exist for categories and prompts (backward compatible)
        try:
            self._ensure_stable_ids()
            # Persist once if any IDs were added
            self.save_prompts()
        except Exception:
            pass
        # Register optional system-wide hotkey (Teleport only)
        self.register_hotkey()
        
        # Setup tray icon (if available)
        self.setup_tray_icon()
        
        # Override close behaviour to minimise to tray instead of exiting
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Optionally start hidden in system tray
        try:
            if self.settings.get("start_hidden", False) and getattr(self, "tray_icon", None):
                # Delay to allow window to initialize before withdrawing
                self.root.after(200, self.minimize_to_tray)
            else:
                # Show window after everything is initialized (prevents title bar flash)
                # Increased delay to ensure borderless style is fully applied
                self.root.after(150, self._show_window_after_init)
        except Exception:
            # Fallback: show window immediately if there's an error
            self.root.after(150, self._show_window_after_init)
        

    def _apply_borderless_style(self, window):
        """Ensure a Tk window stays chrome-free on Windows."""
        if sys.platform != "win32":
            return
        try:
            # NOTE: Must be called AFTER overrideredirect(True) and while window is withdrawn
            # Defer until Tk has created the native window handle
            window.update_idletasks()
            hwnd = window.winfo_id()
            if not hwnd:
                return
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            try:
                get_window_long = user32.GetWindowLongPtrW
                set_window_long = user32.SetWindowLongPtrW
            except AttributeError:
                get_window_long = user32.GetWindowLongW
                set_window_long = user32.SetWindowLongW

            GWL_STYLE = -16
            GWL_EXSTYLE = -20
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            WS_MAXIMIZEBOX = 0x00010000
            WS_MINIMIZEBOX = 0x00020000
            WS_SYSMENU = 0x00080000

            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080

            style = get_window_long(ctypes.c_void_p(hwnd), GWL_STYLE)
            if not style:
                return
            new_style = style & ~(WS_CAPTION | WS_THICKFRAME | WS_MAXIMIZEBOX | WS_MINIMIZEBOX | WS_SYSMENU)
            if new_style != style:
                set_window_long(ctypes.c_void_p(hwnd), GWL_STYLE, new_style)

            ex_style = get_window_long(ctypes.c_void_p(hwnd), GWL_EXSTYLE)
            if ex_style:
                desired_ex = (ex_style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
                if desired_ex != ex_style:
                    set_window_long(ctypes.c_void_p(hwnd), GWL_EXSTYLE, desired_ex)

            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            SWP_FRAMECHANGED = 0x0020
            user32.SetWindowPos(ctypes.c_void_p(hwnd), None, 0, 0, 0, 0,
                                SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)
        except Exception:
            # Best effort only; fall back to Tk's overrideredirect handling
            pass

    def _enforce_borderless(self):
        """Best-effort to keep the main window chrome-free."""
        try:
            if getattr(self, "root", None) and self.root.winfo_exists():
                try:
                    self.root.overrideredirect(True)
                except Exception:
                    pass
                self._apply_borderless_style(self.root)
        except Exception:
            pass
    
    def _show_window_after_init(self):
        """Show the window after complete initialization to prevent title bar flashing."""
        try:
            # Ensure borderless is applied before showing
            self.root.update_idletasks()
            self._enforce_borderless()
            # Additional enforcement after a brief delay to ensure it takes effect
            self.root.after(10, self._enforce_borderless)
            self.root.deiconify()
            # Ensure window is on screen
            self.ensure_window_on_screen()
            # Final enforcement after window is shown (belt and suspenders approach)
            self.root.after(100, self._enforce_borderless)
            self.root.after(250, self._enforce_borderless)
        except Exception:
            # Fallback: just show the window
            try:
                self.root.deiconify()
            except Exception:
                pass

    def load_settings(self):
        """Load settings using ConfigManager and ProfileService"""
        try:
            # Initialize state manager
            self.state_manager.load_state()

            # Initialize profile system and migrate existing settings if needed
            self._initialize_profile_system()

            # Load current profile settings first
            current_profile = self.profile_service.get_current_profile()
            if current_profile and current_profile.settings:
                # Use profile settings
                profile_settings = current_profile.settings
                # Merge with defaults to ensure all required settings exist
                self.settings = self.config_manager._merge_settings(self.default_settings, profile_settings)
            else:
                # Fall back to regular settings loading
                self.settings = self.config_manager.load_settings(self.default_settings)

            # Hydrate persisted UI state from state manager
            try:
                collapsed = self.state_manager.get_ui_state("collapsed_categories", set())
                self.collapsed_categories = set(collapsed) if isinstance(collapsed, (list, set)) else set()
            except Exception:
                self.collapsed_categories = set()

        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = copy.deepcopy(self.default_settings)
            self.collapsed_categories = set()
        
        # Apply UI scale and compact mode from settings
        self._apply_ui_scale_settings()

    def _apply_ui_scale_settings(self):
        """Apply UI scale, bar scale, and compact mode settings to the design system"""
        try:
            from src.ui.design_system import set_ui_scale, set_compact_mode, set_bar_scale
            ui_scale = self.settings.get("ui_scale", 1.0)
            bar_scale = self.settings.get("bar_scale", 1.0)
            compact_mode = self.settings.get("compact_mode", False)
            set_ui_scale(ui_scale)
            set_bar_scale(bar_scale)
            set_compact_mode(compact_mode)
        except ImportError:
            # Design system not available, skip
            pass
        except Exception as e:
            print(f"Error applying UI scale settings: {e}")

    def _initialize_profile_system(self):
        """Initialize the profile system and migrate existing settings if needed"""
        try:
            # Check if this is the first run (no profiles exist)
            profiles = self.profile_service.load_all_profiles()

            if len(profiles) == 1 and "Default" in profiles:
                # Only default profile exists, check if we need to migrate existing settings
                default_profile = profiles["Default"]

                if not default_profile.settings or len(default_profile.settings) < 50:
                    # Profile has minimal or no settings, migrate from existing settings.json
                    if Path(self.settings_file).exists():
                        try:
                            existing_settings = self.config_manager.load_settings(self.default_settings)

                            # Update default profile with existing settings
                            if self.profile_service.update_profile("Default", existing_settings):
                                print("Migrated existing settings to Default profile")
                            else:
                                print("Failed to migrate existing settings to profile")
                        except Exception as e:
                            print(f"Error migrating settings to profile: {e}")
                    else:
                        # No existing settings file, use defaults
                        if self.profile_service.update_profile("Default", self.default_settings):
                            print("Initialized Default profile with default settings")

            # Ensure we have a current profile set
            current_profile = self.profile_service.get_current_profile()
            if not current_profile:
                # Set Default as current profile
                self.profile_service.switch_profile("Default")
                print("Set Default profile as current profile")

        except Exception as e:
            print(f"Error initializing profile system: {e}")
            traceback.print_exc()

    def _ensure_visual_defaults(self):
        """Ensure decorative visual settings exist with sensible defaults."""
        try:
            theme = self.settings.get("theme", {})
            visual = self.settings.setdefault("visual", {})
            changed = False

            def _ensure(key, value, allow_empty=False):
                nonlocal changed
                existing = visual.get(key)
                if key not in visual or (not allow_empty and existing in ("", None)):
                    visual[key] = value
                    changed = True

            background = theme.get("background", "#0f0f23")
            accent = theme.get("accent", "#1a1a2e")
            highlight = theme.get("highlight", accent)
            border = theme.get("border", "#533483")

            _ensure("frame_style", "Luminous Glass")
            try:
                outline_default = self._blend_colors(border, highlight, 0.35)
            except Exception:
                outline_default = border
            _ensure("outline_color", outline_default)

            _ensure("glow_enabled", True, allow_empty=True)
            try:
                glow_default = self._blend_colors(highlight, "#ffffff", 0.25)
            except Exception:
                glow_default = highlight
            _ensure("glow_color", glow_default)

            _ensure("shadow_enabled", True, allow_empty=True)
            try:
                shadow_default = self._blend_colors(background, "#000000", 0.45)
            except Exception:
                shadow_default = "#000000"
            _ensure("shadow_color", shadow_default)

            _ensure("gradient_enabled", True, allow_empty=True)
            try:
                gradient_start = self._blend_colors(background, accent, 0.28)
                gradient_end = self._blend_colors(background, "#000000", 0.3)
            except Exception:
                gradient_start = background
                gradient_end = border
            _ensure("gradient_start", gradient_start)
            _ensure("gradient_end", gradient_end)

            _ensure("texture_intensity", 0.25, allow_empty=True)
            try:
                mountain_default = self._blend_colors(background, highlight, 0.35)
                stone_default = self._blend_colors(background, border, 0.45)
                stone_outline_default = self._blend_colors(border, "#ffffff", 0.2)
            except Exception:
                mountain_default = accent
                stone_default = border
                stone_outline_default = border
            _ensure("mountain_fill", mountain_default)
            _ensure("stone_fill", stone_default)
            _ensure("stone_outline", stone_outline_default)

            if changed:
                self.settings["visual"] = visual
                try:
                    self.save_settings()
                except Exception:
                    pass
        except Exception:
            pass

    def save_settings(self):
        """Save settings using ConfigManager, StateManager, and ProfileService"""
        try:
            # Save UI state to StateManager
            try:
                if hasattr(self, 'collapsed_categories') and isinstance(self.collapsed_categories, set):
                    self.state_manager.set_ui_state("collapsed_categories", self.collapsed_categories)
            except Exception:
                pass

            # Save to current profile
            current_profile = self.profile_service.get_current_profile()
            if current_profile:
                # Update current profile with new settings
                if self.profile_service.update_profile(current_profile.name, self.settings):
                    print(f"Settings saved to profile '{current_profile.name}'")
                else:
                    print(f"Failed to save settings to profile '{current_profile.name}'")
                    # Fallback to regular config manager
                    self.config_manager.save_settings(self.settings)
            else:
                # Fallback to regular settings saving
                if not self.config_manager.save_settings(self.settings):
                    raise Exception("Failed to save settings")

            # Save state if it's dirty
            if self.state_manager.is_dirty():
                self.state_manager.save_state()

        except Exception as e:
            print(f"Error saving settings: {e}")
            traceback.print_exc()
    
    def setup_window(self):
        """Configure the main window properties"""
        self.root.title("Promptoire")
        
        # CRITICAL: Set overrideredirect BEFORE any other window operations to prevent title bar
        self.root.overrideredirect(True)
        
        # Apply app icon if available (Windows .ico preferred; falls back if PIL is available)
        try:
            self._apply_window_icon(self.root)
        except Exception:
            pass
        
        # Use saved position
        x = self.settings["position"]["x"]
        y = self.settings["position"]["y"]
        
        # Modern compact design with buttons (adjustable size via bar_scale)
        try:
            bar_scale = float(self.settings.get("bar_scale", 1.0))
        except Exception:
            bar_scale = 1.0
        bar_scale = max(0.8, min(2.0, bar_scale))
        w, h = self._compute_main_bar_size(bar_scale)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self.root.attributes("-topmost", self.settings.get("always_on_top", True))
        # Hide from taskbar (keeps it unobtrusive); tray icon provides access
        try:
            self.root.attributes("-toolwindow", True)
        except Exception:
            pass
        
        # Apply opacity setting
        opacity = self.settings.get("opacity", 0.95)
        self.root.attributes("-alpha", opacity)
        
        # Apply borderless style (after overrideredirect but while window is still withdrawn)
        self._apply_borderless_style(self.root)

        # Gradients/patterns removed
        
        # Use theme colors
        bg_color = self.settings["theme"]["background"]
        self.root.configure(bg=bg_color)
        
        # Modern styling with subtle border
        self.root.configure(highlightbackground=self.settings["theme"].get("border", "#555555"), highlightthickness=1)
        
        # Make window draggable
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag_window)
        # Global shortcuts
        try:
            # Removed auto-close bindings so the drawer stays open unless explicitly minimized/hidden via hotkey
            pass
        except Exception:
            pass

    def _compute_main_bar_size(self, bar_scale=None):
        """Calculate a non-clipping launcher size for current bar controls."""
        try:
            if bar_scale is None:
                bar_scale = float(self.settings.get("bar_scale", 1.0))
        except Exception:
            bar_scale = 1.0
        bar_scale = max(0.8, min(2.0, float(bar_scale)))

        btn_px = max(20, int(round(24 * bar_scale)))
        gap = max(1, int(round(2 * bar_scale)))
        outer_pad = max(1, int(2 * bar_scale))

        # 3 buttons + separator + grid paddings from create_widgets.
        controls_w = (btn_px * 3) + 1 + (gap * 4)
        controls_h = btn_px + (gap * 2)

        # Include shell/halo/content chrome and root border.
        chrome = (outer_pad * 2) + 8
        width = controls_w + chrome
        height = controls_h + chrome

        return max(86, int(width)), max(36, int(height))

    def _fit_main_bar_window(self):
        """Resize root window to fit the launcher controls without clipping."""
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
        except Exception:
            x = int(self.settings.get("position", {}).get("x", 100))
            y = int(self.settings.get("position", {}).get("y", 100))

        min_w, min_h = self._compute_main_bar_size(getattr(self, "current_bar_scale", None))
        try:
            self.root.update_idletasks()
            req_w = int(self.root.winfo_reqwidth())
            req_h = int(self.root.winfo_reqheight())
        except Exception:
            req_w, req_h = min_w, min_h

        new_w = max(min_w, req_w)
        new_h = max(min_h, req_h)
        try:
            self.root.geometry(f"{new_w}x{new_h}+{x}+{y}")
        except Exception:
            pass

        try:
            self.settings["position"]["x"] = x
            self.settings["position"]["y"] = y
        except Exception:
            pass

    def duplicate_selected(self):
        try:
            self._push_undo()
            sels = list(self.tree.selection())
            if not sels:
                return
            for item in sels:
                vals = self.tree.item(item, "values")
                if not vals:
                    continue
                if vals[0] == "prompt":
                    path = vals[1]
                    idx = int(vals[2])
                    cat = self._get_category_by_path(path)
                    src = cat.get("prompts", [])[idx]
                    cat.setdefault("prompts", []).insert(idx + 1, copy.deepcopy(src))
                elif vals[0] == "category":
                    path = vals[1]
                    parts = path.split("/")
                    name = parts[-1]
                    parent_path = "/".join(parts[:-1])
                    container = self.prompts["categories"] if not parent_path else self._get_category_by_path(parent_path).setdefault("subcategories", {})
                    src_obj = self._get_category_by_path(path)
                    new_name = name + " (Copy)"
                    i = 2
                    while new_name in container:
                        new_name = f"{name} (Copy {i})"
                        i += 1
                    container[new_name] = copy.deepcopy(src_obj)
            self.populate_tree()
        except Exception:
            pass

    def sort_siblings_alpha(self):
        try:
            self._push_undo()
            sels = list(self.tree.selection())
            if not sels:
                return
            vals = self.tree.item(sels[0], "values")
            if not vals:
                return
            if vals[0] == "category":
                path = vals[1]
                is_top, container, parent, name, parent_path = self._get_category_container_info(path)
                order = sorted(container.keys(), key=lambda s: s.lower())
                new_container = {n: container[n] for n in order}
                if is_top:
                    self.prompts["categories"] = new_container
                else:
                    parent["subcategories"] = new_container
            else:
                path = vals[1]
                cat = self._get_category_by_path(path)
                lst = cat.get("prompts", [])
                lst.sort(key=lambda p: str(p.get("title", "")).lower())
            self.populate_tree()
        except Exception:
            pass

    def bulk_edit_tags(self):
        try:
            sels = list(self.tree.selection())
            if not sels:
                return
            targets = []
            for item in sels:
                vals = self.tree.item(item, "values")
                if vals and vals[0] == "prompt":
                    targets.append((vals[1], int(vals[2])))
            if not targets:
                return
            self._push_undo()
            add = self.parent._ask_string_modal(self.window, "Bulk Tags", "Add tags (comma-separated), or leave blank:", initial_value="")
            rem = self.parent._ask_string_modal(self.window, "Bulk Tags", "Remove tags (comma-separated), or leave blank:", initial_value="")
            add_tags = [t.strip() for t in (add or "").split(",") if t.strip()]
            rem_tags = set([t.strip().lower() for t in (rem or "").split(",") if t.strip()])
            for path, idx in targets:
                cat = self._get_category_by_path(path)
                p = cat.get("prompts", [])[idx]
                tags = p.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                tags = [t for t in tags if t.lower() not in rem_tags]
                tags.extend(add_tags)
                seen = set()
                tags = [t for t in tags if not (t.lower() in seen or seen.add(t.lower()))]
                p["tags"] = tags
            self.populate_tree()
        except Exception:
            pass

    def bulk_find_replace_titles(self):
        try:
            sels = list(self.tree.selection())
            if not sels:
                return
            targets = []
            for item in sels:
                vals = self.tree.item(item, "values")
                if vals and vals[0] == "prompt":
                    targets.append((vals[1], int(vals[2])))
            if not targets:
                return
            self._push_undo()
            find = self.parent._ask_string_modal(self.window, "Find/Replace", "Find in titles:", initial_value="")
            if find is None:
                return
            repl = self.parent._ask_string_modal(self.window, "Find/Replace", "Replace with:", initial_value="")
            if repl is None:
                return
            for path, idx in targets:
                cat = self._get_category_by_path(path)
                p = cat.get("prompts", [])[idx]
                p["title"] = str(p.get("title", "")).replace(find, repl)
            self.populate_tree()
        except Exception:
            pass
        # Apply accessibility font scale
        try:
            self._apply_font_scale()
        except Exception:
            pass
        
        # Apply global compact visual styles (scrollbars, etc.)
        try:
            self._apply_global_ttk_style()
        except Exception:
            pass
        
        # Handy app-wide keyboard shortcuts
        try:
            self.root.bind_all("<Control-e>", lambda e: self.open_prompt_editor())
            self.root.bind_all("<Control-comma>", lambda e: self.open_settings())
            self.root.bind_all("<Control-Shift-P>", lambda e: self.open_profile_manager())
            self.root.bind_all("<Control-t>", lambda e: self.open_template_manager())
            self.root.bind_all("<Control-a>", lambda e: self.open_analytics_dashboard())
            self.root.bind_all("<Control-r>", lambda e: self.reload_prompts())
            self.root.bind_all("<Control-o>", lambda e: self.open_prompts_folder())
            self.root.bind_all("<Control-q>", lambda e: self.exit_app())
            self.root.bind_all("<Control-f>", lambda e: self._focus_search())
            self.root.bind_all("<F1>", lambda e: self.show_help_about())
        except Exception:
            pass
        
    def setup_data(self):
        """Initialize data storage"""
        # Use constants if available, otherwise fallback to hardcoded values
        if 'DEFAULT_DATA_FILE' in globals():
            self.data_file = DEFAULT_DATA_FILE
            self.settings_file = DEFAULT_SETTINGS_FILE
            self.icons_dir = DEFAULT_ICONS_DIR
        else:
            self.data_file = Path("prompts.json")
            self.settings_file = Path("settings.json")
            self.icons_dir = Path("icons")
        self.icons_dir.mkdir(exist_ok=True)
        
        # Use constants for default settings if available
        if 'DEFAULT_WINDOW_POSITION' in globals():
            default_position = DEFAULT_WINDOW_POSITION
        else:
            default_position = {"x": 100, "y": 100}

        self.default_settings = {
            "position": default_position,
            "icon": {"type": "emoji", "value": "🧠"},
            "theme": {
                "background": "#060a12",
                "foreground": "#f2f7ff",
                "accent": "#0f1828",
                "button_bg": "#17253a",
                "button_hover": "#213452",
                "border": "#294564",
                "highlight": "#2ee6ff",
                "highlight_text": "#000000",
                "slider_trough": "#0f1828",
                "category_bar": "#2ee6ff",
                "muted_text": "#9eb9d8",
                "category_text": "#000000",
                "glow_color": "#2ee6ff40",
                "background_image": "",
                "background_image_fit": "cover",
                "background_image_enabled": False
            },
            "visual": {
                "frame_style": "Luminous Glass",
                "outline_color": "",
                "glow_enabled": True,
                "glow_color": "",
                "shadow_enabled": True,
                "shadow_color": "",
                "gradient_enabled": True,
                "gradient_start": "",
                "gradient_end": "",
                "texture_intensity": 0.25,
                "mountain_fill": "",
                "stone_fill": "",
                "stone_outline": ""
            },
            "theme_preset": "Nebula Flux",
            # Default color scheme preset (users can switch in Settings)
            "opacity": 0.97,
            # Teleport hotkeys (global)
            "teleport_hotkey": "alt+z",
            "teleport_hotkey_aliases": ["alt+c"],
            "teleport_hotkey_suppress": False,
            "auto_hide": True,
            "drawer_size": {"width": 360, "height": 500},
            # Scale of the floating main bar (size of the tiny launcher bar)
            "bar_scale": 1.0,
            # Optional support link – customize in Settings
            "coffee_url": "https://buy.stripe.com/cNiaEW3c0bsxcTL9gV3ZK00",
            # Start minimized to tray (hide the bar); can be changed in Settings
            "start_hidden": True,
            # New features
            "auto_paste": False,
            "spring_loaded_close": True,  # Auto-close drawer after copying a prompt
            "paste_delay_ms": 500,
            "always_on_top": True,
            "search_fuzzy": True,
            "search_highlight": True,
            "font_scale": 1.0,
            "ui_scale": 1.0,
            "compact_mode": False,
            # Animation & visual effects
            "animations_enabled": True,
            "animation_speed": 1.0,
            # Font customization
            "font": {
                "family": "Bahnschrift",
                "mono_family": "Cascadia Code",
                "emoji_family": "Segoe UI Emoji",
                "bold_titles": True
            },
            "favorites": [],
            "recent_prompts": [],
            # Persist UI state
            "collapsed_categories": [],
            "tray": {"show_recents": True, "show_favorites": True, "recents_count": 5},
            "gist": {"token": "", "gist_id": ""},
            # Performance
            "use_virtual_scrolling": False
        }
        
        self.default_prompts = {
            "categories": {
                "Writing": {
                    "prompts": [
                        {
                            "title": "Email Draft",
                            "prompt": "Draft a professional email about {subject} with a {tone} tone."
                        }
                    ],
                    "subcategories": {
                        "Content Creation": {
                            "prompts": [
                                {
                                    "title": "Blog Post Outline", 
                                    "prompt": "Write a detailed outline for a blog post about {topic} in a {tone} tone."
                                }
                            ]
                        },
                        "Creative Writing": {
                            "prompts": [
                                {
                                    "title": "Creative Story",
                                    "prompt": "Write a creative short story about {theme} in {genre} style."
                                }
                            ]
                        }
                    }
                },
                "Coding": {
                    "prompts": [
                        {
                            "title": "Algorithm Explanation",
                            "prompt": "Explain the {algorithm_name} algorithm in simple terms."
                        }
                    ],
                    "subcategories": {
                        "Python": {
                            "prompts": [
                                {
                                    "title": "Python Docstring",
                                    "prompt": "Write a Google-style docstring for this Python function:\n\n{code}"
                                }
                            ]
                        },
                        "General": {
                            "prompts": [
                                {
                                    "title": "Code Review",
                                    "prompt": "Review this code for best practices, bugs, and improvements:\n\n{code}"
                                }
                            ]
                        }
                    }
                },
                "AI Tools": {
                    "prompts": [
                        {
                            "title": "System Prompt",
                            "prompt": "You are a helpful AI assistant specialized in {domain}. Your responses should be {tone} and focus on {objective}."
                        },
                        {
                            "title": "Explain Concept",
                            "prompt": "Explain {concept} in simple terms for someone who is {background}. Use {format} format."
                        }
                    ]
                }
            }
        }

    def create_widgets(self):
        """Create a compact glass-like launcher bar with neon accents."""
        theme = self.settings.get("theme", {})
        bg_color = theme.get("background", "#060a12")
        self.root.configure(bg=bg_color)

        # Clean up old widgets if they exist
        try:
            for widget in self.root.winfo_children():
                widget.destroy()
        except Exception:
            pass

        try:
            bar_scale = float(self.settings.get("bar_scale", 1.0))
        except Exception:
            bar_scale = 1.0
        bar_scale = max(0.8, min(2.0, bar_scale))
        self.current_bar_scale = bar_scale

        accent = theme.get("accent", bg_color)
        highlight = theme.get("highlight", accent)
        border = theme.get("border", "#3a3a3a")
        base_fg = theme.get("foreground", "#ffffff")

        bar_shadow = self._blend_colors(bg_color, "#000000", 0.68)
        bar_surface = self._blend_colors(bg_color, accent, 0.30)
        bar_surface = self._blend_colors(bar_surface, highlight, 0.06)
        bar_border = self._blend_colors(border, highlight, 0.42)
        glass_top = self._blend_colors(bar_surface, highlight, 0.24)
        glass_bottom = self._blend_colors(bar_surface, "#000000", 0.22)

        button_bg = self._blend_colors(bar_surface, accent, 0.28)
        button_hover = self._blend_colors(button_bg, highlight, 0.28)
        button_active = self._blend_colors(button_hover, "#000000", 0.22)
        fg_color = self._text_on(button_bg, base_fg)

        self.root.configure(bg=bar_shadow)

        shell = tk.Frame(self.root, bg=bar_shadow, bd=0, highlightthickness=0)
        shell.pack(fill="both", expand=True)

        outer_pad = max(1, int(2 * bar_scale))
        halo = tk.Frame(shell, bg=bar_shadow, highlightbackground=bar_border, highlightthickness=1)
        halo.pack(fill="both", expand=True, padx=outer_pad, pady=outer_pad)

        inner = tk.Frame(halo, bg=bar_surface, bd=0, highlightthickness=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Subtle holographic edge treatment
        tk.Frame(inner, bg=glass_top, height=1).pack(fill="x", side="top")
        tk.Frame(inner, bg=glass_bottom, height=1).pack(fill="x", side="bottom")

        content = tk.Frame(inner, bg=bar_surface)
        content.pack(fill="both", expand=True, padx=1, pady=1)

        button_frame = tk.Frame(content, bg=bar_surface)
        button_frame.pack(fill="both", expand=True)

        # Keep icon glyphs slightly smaller than the hitbox so scaling stays centered/clean.
        btn_px = max(20, int(round(24 * bar_scale)))
        icon_font = max(10, int(round(11 * bar_scale)))
        btn_font = max(8, int(round(9 * bar_scale)))
        gap = max(1, int(round(2 * bar_scale)))

        # Keep reference (used by overflow checks / live resize)
        self.button_frame = button_frame

        for col in range(4):
            button_frame.grid_columnconfigure(col, weight=0)

        shared_btn_kwargs = {
            "bg_color": button_bg,
            "fg_color": fg_color,
            "hover_color": button_hover,
            "active_color": button_active,
            "fixed_size": btn_px,
            "border_color": self._blend_colors(bar_border, button_bg, 0.55),
            "glow_color": self._blend_colors(highlight, "#ffffff", 0.18),
        }

        # Main icon (brain) button
        self.icon_wrap = self._create_bar_button(
            button_frame,
            "🧠",
            self.toggle_drawer,
            font_size=icon_font,
            **shared_btn_kwargs
        )
        self.icon_wrap.grid(row=0, column=0, sticky="nsew", padx=(gap, max(1, gap // 2)), pady=gap)
        self.icon_btn = self.icon_wrap.icon_label
        self.update_icon()
        try:
            self._attach_tooltip(self.icon_wrap, "Toggle prompt drawer (double-click for Settings)", delay=260)
        except Exception:
            pass

        try:
            rc_handler = self.show_context_menu
        except Exception:
            rc_handler = lambda e: None
        self.icon_btn.bind("<Button-3>", rc_handler)
        try:
            self.icon_btn.bind("<Double-Button-1>", lambda e: self.open_settings())
        except Exception:
            pass

        # Prompt editor button
        self.prompts_btn = self._create_bar_button(
            button_frame,
            "📝",
            self.open_prompt_editor,
            font_size=btn_font,
            **shared_btn_kwargs
        )
        self.prompts_btn.grid(row=0, column=1, sticky="nsew", padx=(0, max(1, gap // 2)), pady=gap)
        try:
            self._attach_tooltip(self.prompts_btn, "Open Prompt Matrix / Editor (Ctrl+E)", delay=260)
        except Exception:
            pass
        try:
            self.prompts_btn.bind("<Enter>", lambda e: self.root.title("Edit Prompts (Ctrl+E)"))
            self.prompts_btn.bind("<Leave>", lambda e: self.root.title("Promptoire"))
        except Exception:
            pass

        # Separator between action buttons and drag handle
        sep_color = self._blend_colors(bar_surface, highlight, 0.30)
        separator = tk.Frame(button_frame, bg=sep_color, width=1)
        separator.grid(row=0, column=2, sticky="ns", padx=0, pady=max(2, int(3 * bar_scale)))

        # Drag handle (no click command)
        handle_bg = self._blend_colors(button_bg, accent, 0.48)
        handle_hover = self._blend_colors(handle_bg, highlight, 0.38)
        handle_fg = self._text_on(handle_bg, fg_color)
        self.drag_handle = self._create_bar_button(
            button_frame,
            "⋮⋮",
            None,
            bg_color=handle_bg,
            fg_color=handle_fg,
            hover_color=handle_hover,
            active_color=handle_hover,
            font_size=btn_font,
            fixed_size=btn_px,
            border_color=self._blend_colors(bar_border, handle_bg, 0.52),
            glow_color=self._blend_colors(highlight, "#ffffff", 0.14),
        )
        self.drag_handle.grid(row=0, column=3, sticky="nsew", padx=(gap, gap), pady=gap)
        try:
            self._attach_tooltip(self.drag_handle, "Drag to move launcher bar", delay=260)
        except Exception:
            pass
        self.drag_handle.configure(cursor="fleur")
        if getattr(self.drag_handle, "icon_label", None):
            self.drag_handle.icon_label.configure(cursor="fleur")
        self.drag_handle.bind("<Button-1>", self.start_drag)
        self.drag_handle.bind("<B1-Motion>", self.drag_window)
        try:
            for _child in self.drag_handle.winfo_children():
                _child.bind("<Button-1>", self.start_drag)
                _child.bind("<B1-Motion>", self.drag_window)
        except Exception:
            pass

        # Enhanced keyboard shortcuts for accessibility
        self.root.bind("<Control-comma>", lambda e: self.open_settings())
        self.root.bind("<Control-e>", lambda e: self.open_prompt_editor())
        self.root.bind("<F1>", lambda e: self.show_help_about())
        self.root.bind("<Escape>", lambda e: self.root.withdraw())  # Hide window on Escape

        # Tab order for keyboard navigation
        self.icon_btn.takefocus = 1
        if getattr(self.prompts_btn, "icon_label", None):
            self.prompts_btn.icon_label.takefocus = 1

        # Set initial focus to main icon
        self.icon_btn.focus_set()

        # Make container and button frame draggable
        for widget in (shell, halo, inner, button_frame):
            try:
                widget.bind("<Button-1>", self.start_drag)
                widget.bind("<B1-Motion>", self.drag_window)
            except Exception:
                pass
        try:
            self._fit_main_bar_window()
        except Exception:
            pass



    # Canvas rendering methods removed - using simple frame layout now

    # Decoration rendering removed - using clean, simple design

    def _show_import_hover(self, event):
        """Show a tiny pop-over above the import icon on hover."""
        try:
            if getattr(self, "_import_hover", None):
                return
            widget = event.widget
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()

            tip = tk.Toplevel(self.root)
            try:
                tip.overrideredirect(True)
            except Exception:
                pass
            try:
                tip.attributes("-topmost", True)
            except Exception:
                pass

            bg = self.settings["theme"].get("button_bg", "#2a2a2a")
            fg = self._text_on(bg, self.settings["theme"].get("foreground", "#dddddd"))

            frame = tk.Frame(tip, bg=bg, bd=1, relief="solid")
            frame.pack()
            btn = tk.Button(
                frame,
                text="📥 Import",
                command=self.import_prompts,
                bg=bg,
                fg=fg,
                relief="flat",
                padx=6,
                pady=2,
                cursor="hand2"
            )
            btn.pack()

            tip.update_idletasks()
            tip.geometry(f"+{x}+{y - tip.winfo_height() - 6}")
            self._import_hover = tip

            def on_leave(_e=None):
                self._hide_import_hover()
            tip.bind("<Leave>", on_leave)
        except Exception:
            pass

    def _hide_import_hover(self, event=None):
        """Hide the import hover pop-over if shown."""
        try:
            if getattr(self, "_import_hover", None):
                try:
                    self._import_hover.destroy()
                except Exception:
                    pass
                self._import_hover = None
        except Exception:
            self._import_hover = None

    def _resolve_shortcut_target(self):
        """Determine the best executable entry point and arguments for shortcuts."""
        base_dir = Path(__file__).parent.resolve()
        exe_direct = base_dir / 'dist' / 'Promptoire.exe'
        exe_onedir = base_dir / 'dist' / 'Promptoire' / 'Promptoire.exe'
        bat_runner = base_dir / 'run.bat'
        script_path = base_dir / 'promptoire.py'

        if bat_runner.exists():
            return bat_runner, '', base_dir
        if exe_direct.exists():
            return exe_direct, '', exe_direct.parent
        if exe_onedir.exists():
            return exe_onedir, '', exe_onedir.parent

        pythonw = shutil.which('pythonw') if sys.platform == 'win32' else None
        interpreter = pythonw or sys.executable
        arguments = f'"{script_path}"' if script_path.exists() else ''
        return Path(interpreter), arguments, base_dir

    def _get_desktop_directory(self):
        """Best-effort detection of the user's Desktop folder across OneDrive/local setups."""
        candidates = []
        if sys.platform == 'win32':
            try:
                from ctypes import windll, wintypes, create_unicode_buffer
                CSIDL_DESKTOPDIRECTORY = 0x0010
                SHGFP_TYPE_CURRENT = 0
                buf = create_unicode_buffer(wintypes.MAX_PATH)
                if windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, SHGFP_TYPE_CURRENT, buf) == 0:
                    resolved = Path(buf.value)
                    if resolved:
                        candidates.append(resolved)
            except Exception:
                pass

            env_roots = [
                os.environ.get('USERPROFILE'),
                os.environ.get('PUBLIC'),
                os.environ.get('OneDrive'),
                os.environ.get('OneDriveConsumer'),
                os.environ.get('OneDriveCommercial'),
            ]
            for root in env_roots:
                if not root:
                    continue
                root_path = Path(root)
                candidates.append(root_path / 'Desktop')
                candidates.append(root_path / 'OneDrive' / 'Desktop')
        else:
            candidates.append(Path.home() / 'Desktop')

        candidates.append(Path.home() / 'Desktop')
        candidates.append(Path.home() / 'OneDrive' / 'Desktop')

        seen = set()
        for candidate in candidates:
            try:
                if not candidate:
                    continue
                path_str = str(candidate.expanduser())
                if path_str.lower() in seen:
                    continue
                seen.add(path_str.lower())
                if Path(path_str).exists():
                    return Path(path_str)
            except Exception:
                continue
        return None

    def _create_windows_shortcut_via_powershell(self, lnk_path, target, arguments, working_dir, icon_path):
        """Use the built-in Windows scripting host via PowerShell to create a .lnk."""
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        if not powershell:
            raise RuntimeError('PowerShell not available on PATH')

        lnk_path = Path(lnk_path)
        lnk_path.parent.mkdir(parents=True, exist_ok=True)

        def _ps_escape(value):
            if value is None:
                return ''
            return str(value).replace("'", "''")

        lnk_str = _ps_escape(str(lnk_path.resolve()))
        target_str = _ps_escape(target)
        args_str = _ps_escape(arguments or '')
        workdir_str = _ps_escape(str(working_dir) if working_dir else '')
        icon_str = _ps_escape(icon_path or '')

        script_lines = [
            "$ErrorActionPreference = 'Stop'",
            f"$lnk = '{lnk_str}'",
            f"$target = '{target_str}'",
            f"$arguments = '{args_str}'",
            f"$workdir = '{workdir_str}'",
            f"$icon = '{icon_str}'",
            "$shell = New-Object -ComObject WScript.Shell",
            "$shortcut = $shell.CreateShortcut($lnk)",
            "$shortcut.TargetPath = $target",
            "if ($arguments.Trim().Length -gt 0) { $shortcut.Arguments = $arguments }",
            "if ($workdir.Trim().Length -gt 0) { $shortcut.WorkingDirectory = $workdir }",
            "if ($icon.Trim().Length -gt 0) { $shortcut.IconLocation = $icon }",
            "$shortcut.Save()"
        ]
        command = '; '.join(script_lines)

        result = subprocess.run(
            [powershell, '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or 'Unable to create shortcut')

    def _write_windows_launcher_batch(self, desktop_dir, target, arguments, working_dir):
        """Fallback: create a small launcher .bat on the desktop."""
        launcher_path = Path(desktop_dir) / 'Promptoire Launcher.bat'
        cmd_args = f' {arguments.strip()}' if arguments and arguments.strip() else ''
        content = (
            "@echo off\n"
            "setlocal\n"
            f'cd /d "{working_dir}"\n'
            f'start "Promptoire" "{target}"{cmd_args}\n'
            "exit /b 0\n"
        )
        launcher_path.write_text(content, encoding='utf-8')
        return launcher_path

    def create_desktop_shortcut(self):
        """Create a desktop entry point without requiring external packages."""
        try:
            base_dir = Path(__file__).parent.resolve()
            target, arguments, working_dir = self._resolve_shortcut_target()
            icon_candidate = base_dir / 'icons' / 'replicate-prediction-2j5y20xssnrmc0crx40tp1mzjc.ico'
            icon_path = str(icon_candidate.resolve()) if icon_candidate.exists() else str((base_dir / 'promptoire.py').resolve())

            desktop = self._get_desktop_directory()
            if not desktop:
                self.show_notification('Desktop folder not found')
                return

            if sys.platform == 'win32':
                lnk_path = desktop / 'Promptoire.lnk'
                try:
                    self._create_windows_shortcut_via_powershell(
                        lnk_path=lnk_path,
                        target=str(target),
                        arguments=arguments,
                        working_dir=working_dir,
                        icon_path=icon_path
                    )
                    self.show_notification('Desktop shortcut ready')
                    return
                except Exception as exc:
                    try:
                        if self.logger:
                            self.logger.warning('PowerShell shortcut creation failed: %s', exc)
                    except Exception:
                        pass
                    fallback = self._write_windows_launcher_batch(desktop, str(target), arguments, working_dir)
                    self.show_notification(f'Launcher script ready: {fallback.name}')
                    return

            # Non-Windows or final fallback: create launcher shell script
            script_path = desktop / 'Promptoire.sh'
            launcher = f'#!/bin/bash\ncd "{base_dir}"\npython3 promptoire.py\n'
            script_path.write_text(launcher, encoding='utf-8')
            try:
                os.chmod(script_path, 0o755)
            except Exception:
                pass
            self.show_notification('Desktop script created!')
        except Exception as e:
            message = f'Error creating shortcut: {e}'
            try:
                if self.logger:
                    self.logger.error(message)
            except Exception:
                pass
            self.show_notification(message[:60] + ('...' if len(message) > 60 else ''))

    def update_icon(self):
        """Update the main icon based on settings"""
        icon_settings = self.settings["icon"]
        
        if icon_settings["type"] == "emoji":
            self.icon_btn.configure(text=icon_settings["value"], image="")
        elif icon_settings["type"] == "image" and PIL_AVAILABLE:
            try:
                # Load custom image
                if icon_settings["value"].startswith("data:"):
                    # Base64 encoded image
                    image_data = icon_settings["value"].split(",")[1]
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(BytesIO(image_bytes))
                else:
                    # File path
                    image = Image.open(icon_settings["value"])
                
                # Resize relative to the real icon button hitbox so scaling stays centered.
                button_size = None
                try:
                    if hasattr(self, "icon_wrap") and self.icon_wrap:
                        button_size = int(getattr(self.icon_wrap, "_fixed_size", 0) or self.icon_wrap.winfo_width())
                except Exception:
                    button_size = None
                if not button_size or button_size <= 1:
                    try:
                        scale = float(getattr(self, "current_bar_scale", 1.0))
                    except Exception:
                        scale = 1.0
                    button_size = max(20, int(round(24 * scale)))
                size = max(14, int(round(button_size * 0.62)))
                image = image.convert("RGBA")
                image.thumbnail((size, size), Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                offset = ((size - image.width) // 2, (size - image.height) // 2)
                canvas.paste(image, offset, image if image.mode == "RGBA" else None)
                self.icon_photo = ImageTk.PhotoImage(canvas)
                self.icon_btn.configure(text="", image=self.icon_photo)
            except Exception as e:
                print(f"Error loading custom icon: {e}")
                # Fallback to emoji
                self.icon_btn.configure(text="🧠", image="")
        else:
            # Fallback to default emoji
            self.icon_btn.configure(text="🧠", image="")
    
    def _apply_window_icon(self, window):
        """Apply window icon from settings or default icons/app.ico.
        - On Windows, .ico is preferred via iconbitmap.
        - Else, if Pillow is available, use iconphoto with any raster format.
        """
        try:
            icon_settings = (self.settings or {}).get("icon", {})
            icon_path = None
            # If settings point to a file path, use it (skip base64 data URIs here)
            if icon_settings.get("type") == "image" and icon_settings.get("value") and not str(icon_settings["value"]).startswith("data:"):
                icon_path = icon_settings["value"]
            # Fallback to icons/app.ico if it exists
            if not icon_path:
                default_ico = self.icons_dir / "app.ico"
                if default_ico.exists():
                    icon_path = str(default_ico)

            if not icon_path:
                return

            if sys.platform == "win32" and icon_path.lower().endswith(".ico"):
                window.iconbitmap(icon_path)  # Best on Windows
            elif PIL_AVAILABLE:
                img = Image.open(icon_path)
                # Keep a ref to avoid GC
                if not hasattr(self, "_tk_icon_photo"):
                    self._tk_icon_photo = None
                self._tk_icon_photo = ImageTk.PhotoImage(img)
                try:
                    window.iconphoto(True, self._tk_icon_photo)
                except Exception:
                    pass
        except Exception:
            # Ignore icon errors to avoid breaking app startup
            pass
        
    def _apply_font_scale(self):
        """Apply font scaling based on settings['font_scale']."""
        try:
            scale = float(self.settings.get("font_scale", 1.0))
            # Hard cap between 80% and 130%
            scale = max(0.8, min(1.3, scale))
            # Tk scaling: pixels per point
            self.root.tk.call('tk', 'scaling', scale)
        except Exception:
            pass

    # ─────────────────────────────── Font helpers ───────────────────────────────
    def _get_font_family(self):
        try:
            return (self.settings or {}).get("font", {}).get("family", "Segoe UI")
        except Exception:
            return "Segoe UI"

    def _get_mono_family(self):
        try:
            return (self.settings or {}).get("font", {}).get("mono_family", "Consolas")
        except Exception:
            return "Consolas"

    def _get_emoji_family(self):
        try:
            return (self.settings or {}).get("font", {}).get("emoji_family", "Segoe UI Emoji")
        except Exception:
            return "Segoe UI Emoji"

    def title_weight(self):
        try:
            return "bold" if (self.settings or {}).get("font", {}).get("bold_titles", True) else "normal"
        except Exception:
            return "bold"

    def ui_font(self, size, weight=None):
        try:
            family = self._get_font_family()
            if weight and weight != "normal":
                return (family, int(size), weight)
            return (family, int(size))
        except Exception:
            return ("Segoe UI", int(size), weight or "normal")

    def mono_font(self, size, weight=None):
        try:
            family = self._get_mono_family()
            if weight and weight != "normal":
                return (family, int(size), weight)
            return (family, int(size))
        except Exception:
            return ("Consolas", int(size), weight or "normal")

    def emoji_font(self, size, weight=None):
        try:
            family = self._get_emoji_family()
            if weight and weight != "normal":
                return (family, int(size), weight)
            return (family, int(size))
        except Exception:
            return ("Segoe UI Emoji", int(size), weight or "normal")

    def reapply_fonts_main_bar(self):
        try:
            try:
                bar_scale = float(self.settings.get("bar_scale", 1.0))
            except Exception:
                bar_scale = 1.0
            bar_scale = max(0.8, min(2.0, bar_scale))
            btn_font = max(8, int(round(9 * bar_scale)))
            icon_font = max(10, int(round(11 * bar_scale)))

            if hasattr(self, 'import_btn') and getattr(self.import_btn, "icon_label", None):
                self.import_btn.icon_label.configure(font=self.emoji_font(btn_font))
            if hasattr(self, 'prompts_btn') and getattr(self.prompts_btn, "icon_label", None):
                self.prompts_btn.icon_label.configure(font=self.emoji_font(btn_font))
            if hasattr(self, 'drag_handle') and getattr(self.drag_handle, "icon_label", None):
                self.drag_handle.icon_label.configure(font=self.emoji_font(btn_font))
            if hasattr(self, 'icon_btn') and self.icon_btn:
                self.icon_btn.configure(font=self.emoji_font(icon_font))
            self._fit_main_bar_window()
        except Exception:
            pass

    def start_drag(self, event):
        """Begin drag action from the drag handle (or its child)."""
        try:
            if not hasattr(self, "drag_handle"):
                return
            w = event.widget
            allowed = False
            while w is not None:
                if w == self.drag_handle:
                    allowed = True
                    break
                try:
                    w = w.master
                except Exception:
                    w = None
            if not allowed:
                return
            # Use screen-relative coordinates for stability
            self._drag_offset_x = event.x_root - self.root.winfo_x()
            self._drag_offset_y = event.y_root - self.root.winfo_y()
        except Exception:
            pass

    def drag_window(self, event):
        """Drag the main window; keep dropdown aligned if open."""
        try:
            if not hasattr(self.root, "start_x") or not hasattr(self.root, "start_y"):
                return
            x = self.root.winfo_x() + event.x - self.root.start_x
            y = self.root.winfo_y() + event.y - self.root.start_y
            self.root.geometry(f"+{x}+{y}")
            if getattr(self, "expanded", False) and getattr(self, "drawer", None):
                self._apply_drawer_geometry()
            self.settings["position"]["x"] = x
            self.settings["position"]["y"] = y
        except Exception:
            pass

    def _on_icon_click(self, event=None):
        """Fallback click handler if toggle_drawer isn't available."""
        try:
            # Prefer real toggle if present
            if hasattr(self, "toggle_drawer") and callable(getattr(self, "toggle_drawer")):
                return self.toggle_drawer(event)
            # Otherwise, no-op to avoid crashes
        except Exception:
            pass

    # ─────────────────────────────── Prompt identification & utils ───────────────────────────────
    def _compute_prompt_content_id(self, prompt_obj):
        """Create a stable content-based ID for a prompt (sha1 of title + prompt)."""
        try:
            base = (prompt_obj.get("title", "") + "\n" + prompt_obj.get("prompt", "")).encode("utf-8")
            return hashlib.sha1(base).hexdigest()
        except Exception:
            return hashlib.sha1(repr(prompt_obj).encode("utf-8")).hexdigest()

    def _get_prompt_search_blob(self, prompt_obj):
        """Return cached lowercase search text for a prompt."""
        if not isinstance(prompt_obj, dict):
            return ""

        try:
            prompt_id = prompt_obj.get("id")
            if not isinstance(prompt_id, str) or not prompt_id:
                prompt_id = self._compute_prompt_content_id(prompt_obj)
        except Exception:
            prompt_id = self._compute_prompt_content_id(prompt_obj)

        tags_raw = prompt_obj.get("tags", [])
        if isinstance(tags_raw, list):
            tags_tuple = tuple(str(tag) for tag in tags_raw)
        elif tags_raw:
            tags_tuple = (str(tags_raw),)
        else:
            tags_tuple = tuple()

        signature = (
            str(prompt_obj.get("title", "")),
            str(prompt_obj.get("prompt", "")),
            tags_tuple,
        )

        cache = getattr(self, "_prompt_search_cache", None)
        if not isinstance(cache, dict):
            self._prompt_search_cache = {}
            cache = self._prompt_search_cache

        cached = cache.get(prompt_id)
        if cached and cached[0] == signature:
            return cached[1]

        tags_text = ", ".join(tags_tuple)
        blob = f"{signature[0]}\n{signature[1]}\n{tags_text}".lower()
        cache[prompt_id] = (signature, blob)
        return blob

    def _iter_prompts(self):
        """Yield tuples of (category_path, index, prompt_obj)."""
        def recurse(cat_dict, path_prefix=""):
            for cat_name, cat_data in cat_dict.items():
                current_path = f"{path_prefix}/{cat_name}" if path_prefix else cat_name
                prompts_list = cat_data.get("prompts", [])
                for idx, p in enumerate(prompts_list):
                    yield (current_path, idx, p)
                sub = cat_data.get("subcategories", {})
                if isinstance(sub, dict):
                    for x in recurse(sub, current_path):
                        yield x
        try:
            for t in recurse(self.prompts.get("categories", {})):
                yield t
        except Exception:
            return

    def _find_prompt_by_id(self, content_id):
        """Return (category_path, index, prompt_obj) for a given content-based ID, or (None, None, None)."""
        try:
            for cat_path, idx, p in self._iter_prompts():
                if self._compute_prompt_content_id(p) == content_id:
                    return cat_path, idx, p
        except Exception:
            pass
        return None, None, None

    def _ensure_stable_ids(self):
        """Ensure each category and prompt has a stable UUID-based id. Adds ids in-place.
        Returns True if any ids were added.
        """
        changed = False

        def ensure_prompt_id(prompt_obj):
            nonlocal changed
            try:
                if not isinstance(prompt_obj, dict):
                    return
                pid = prompt_obj.get("id")
                if not pid or not isinstance(pid, str) or len(pid) < 6:
                    prompt_obj["id"] = f"prm_{uuid.uuid4().hex[:12]}"
                    changed = True
            except Exception:
                pass

        def walk_categories(cat_dict):
            nonlocal changed
            if not isinstance(cat_dict, dict):
                return
            for cat_name, cat_data in cat_dict.items():
                try:
                    if not isinstance(cat_data, dict):
                        continue
                    # Category id
                    cid = cat_data.get("id")
                    if not cid or not isinstance(cid, str) or len(cid) < 6:
                        cat_data["id"] = f"cat_{uuid.uuid4().hex[:12]}"
                        changed = True
                    # Prompts
                    lst = cat_data.get("prompts", [])
                    if isinstance(lst, list):
                        for p in lst:
                            ensure_prompt_id(p)
                    # Subcategories
                    sub = cat_data.get("subcategories", {})
                    if isinstance(sub, dict):
                        walk_categories(sub)
                except Exception:
                    pass

        try:
            cats = self.prompts.setdefault("categories", {})
            walk_categories(cats)
        except Exception:
            pass
        return changed

    def _is_favorite(self, prompt_obj):
        content_id = self._compute_prompt_content_id(prompt_obj)
        return content_id in self.settings.get("favorites", [])

    def _toggle_favorite(self, prompt_obj):
        content_id = self._compute_prompt_content_id(prompt_obj)
        favs = self.settings.get("favorites", [])
        if content_id in favs:
            favs.remove(content_id)
            self.show_notification("Removed from Favorites")
        else:
            favs.insert(0, content_id)
            # De-duplicate
            favs = list(dict.fromkeys(favs))
            self.show_notification("Added to Favorites")
        self.settings["favorites"] = favs
        self.save_settings()
        # Repaint list if open & rebuild tray
        if self.expanded:
            self.populate_prompts(self.search_var.get() if hasattr(self, "search_var") else "")
        self._rebuild_tray_menu()

    def _register_recent(self, prompt_obj):
        try:
            rid = self._compute_prompt_content_id(prompt_obj)
            recents = self.settings.get("recent_prompts", [])
            recents = [r for r in recents if r != rid]
            recents.insert(0, rid)
            # Keep last 20
            recents = recents[:20]
            self.settings["recent_prompts"] = recents
            self.save_settings()
            self._rebuild_tray_menu()
        except Exception:
            pass

    def _iter_prompt_category_nodes(self, categories=None, level=0, path_prefix=""):
        """Yield (name, data, level, real_path) for all categories in the prompt tree."""
        if categories is None:
            categories = self.prompts.get("categories", {})
        if not isinstance(categories, dict):
            return
        for name, data in categories.items():
            if not isinstance(data, dict):
                continue
            real_path = f"{path_prefix}/{name}" if path_prefix else name
            yield name, data, level, real_path
            sub = data.get("subcategories", {})
            if isinstance(sub, dict):
                yield from self._iter_prompt_category_nodes(sub, level + 1, real_path)

    def _all_prompt_matrix_category_keys(self):
        """Return collapse keys for all categories (including special sections)."""
        keys = set()
        try:
            for name, _data, level, _path in self._iter_prompt_category_nodes():
                keys.add(f"{name}_level_{level}")
        except Exception:
            pass
        keys.add("__favorites__")
        keys.add("⭐ Favorites_level_0")
        return keys

    def _keys_for_real_category_path(self, real_path: str):
        """Map real path (A/B/C) to renderer category keys."""
        keys = set()
        if not isinstance(real_path, str):
            return keys
        if real_path.startswith("__favorites__"):
            keys.add("__favorites__")
            keys.add("⭐ Favorites_level_0")
            return keys
        parts = [part for part in real_path.split("/") if part]
        for level, name in enumerate(parts):
            keys.add(f"{name}_level_{level}")
        return keys

    def _resolve_prompt_category_path(self, prompt_obj):
        """Best-effort resolve category path for a prompt object."""
        try:
            rid = self._compute_prompt_content_id(prompt_obj)
            cat_path, _idx, found = self._find_prompt_by_id(rid)
            if found and cat_path:
                return str(cat_path)
        except Exception:
            pass
        try:
            category = prompt_obj.get("category", "")
            if isinstance(category, str):
                cleaned = category.strip()
                if cleaned and cleaned != "Unknown":
                    return cleaned.replace(" > ", "/")
        except Exception:
            pass
        return ""

    def _apply_prompt_matrix_session_state(self):
        """Collapse all categories and expand only the last copied category path."""
        all_keys = self._all_prompt_matrix_category_keys()
        if not all_keys:
            return
        last_path = (self._last_copied_category_path or "").strip()
        if not last_path:
            self.collapsed_categories = set(all_keys)
        else:
            expanded = self._keys_for_real_category_path(last_path)
            self.collapsed_categories = set(k for k in all_keys if k not in expanded)
        self._initialized_collapse_state = True

    # Gradients/patterns removed
            
    def _interpolate_color(self, color1, color2, ratio):
        """Interpolate between two hex colors"""
        try:
            # Convert hex to RGB
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Convert RGB to hex
            def rgb_to_hex(rgb):
                return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            
            # Interpolate each component
            r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
            g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
            b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
            
            return rgb_to_hex((r, g, b))
        except Exception:
            return color1
            
    def _blend_colors(self, bg_color, fg_color, opacity):
        """Blend two colors with given opacity"""
        try:
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            def rgb_to_hex(rgb):
                return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            
            bg_rgb = hex_to_rgb(bg_color)
            fg_rgb = hex_to_rgb(fg_color)
            
            # Blend each component
            r = int(bg_rgb[0] * (1 - opacity) + fg_rgb[0] * opacity)
            g = int(bg_rgb[1] * (1 - opacity) + fg_rgb[1] * opacity)
            b = int(bg_rgb[2] * (1 - opacity) + fg_rgb[2] * opacity)
            
            return rgb_to_hex((r, g, b))
        except Exception:
            return bg_color

    def _lighten_color(self, hex_color, factor=0.15):
        """Lighten a hex color by a given factor"""
        try:
            factor = max(0.0, min(1.0, float(factor)))
            c = hex_color.lstrip('#')
            r = int(c[0:2], 16); g = int(c[2:4], 16); b = int(c[4:6], 16)
            r = min(255, int(round(r + (255 - r) * factor)))
            g = min(255, int(round(g + (255 - g) * factor)))
            b = min(255, int(round(b + (255 - b) * factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _animate_color(self, widget, start_color, end_color, steps=6, delay=15, attr="bg"):
        """Animate a widget color for subtle UI motion."""
        try:
            token = getattr(widget, "_color_anim_token", 0) + 1
            widget._color_anim_token = token

            def step(i):
                if getattr(widget, "_color_anim_token", None) != token:
                    return
                ratio = min(1.0, max(0.0, i / max(1, steps)))
                color = self._interpolate_color(start_color, end_color, ratio)
                try:
                    widget.configure(**{attr: color})
                except Exception:
                    return
                if i < steps:
                    widget.after(delay, lambda: step(i + 1))

            step(0)
        except Exception:
            try:
                widget.configure(**{attr: end_color})
            except Exception:
                pass
    
    def _attach_tooltip(self, widget, text, delay=300):
        """Attach a hover tooltip to a widget showing preview text."""
        if not text or len(text.strip()) == 0:
            return
        
        # Truncate long text
        preview = text[:150] + "..." if len(text) > 150 else text
        
        tooltip_win = [None]  # Use list to allow mutation in closures
        show_job = [None]
        
        bg = self.settings["theme"].get("accent", "#1a1a1a")
        fg = self._text_on(bg, self.settings["theme"].get("foreground", "#ffffff"))
        border = self.settings["theme"].get("highlight", "#00e5e5")
        
        def schedule_show(event=None):
            cancel_show()
            show_job[0] = widget.after(delay, show_tooltip)
        
        def cancel_show():
            if show_job[0]:
                try:
                    widget.after_cancel(show_job[0])
                except Exception:
                    pass
                show_job[0] = None
        
        def show_tooltip(event=None):
            if tooltip_win[0]:
                return
            try:
                tw = tk.Toplevel(widget)
                tw.overrideredirect(True)
                tw.attributes("-topmost", True)
                try:
                    tw.attributes("-alpha", 0.95)
                except Exception:
                    pass
                
                frame = tk.Frame(tw, bg=bg, highlightbackground=border, highlightthickness=1)
                frame.pack(fill="both", expand=True)
                
                label = tk.Label(
                    frame,
                    text=preview,
                    font=self.ui_font(8),
                    bg=bg,
                    fg=fg,
                    wraplength=240,
                    justify="left",
                    padx=6,
                    pady=4,
                )
                label.pack()
                
                tw.update_idletasks()
                tw_w = tw.winfo_reqwidth()
                tw_h = tw.winfo_reqheight()
                pointer_x = widget.winfo_pointerx()
                pointer_y = widget.winfo_pointery()

                # Default to above-left so the tooltip does not appear under the cursor.
                x = widget.winfo_rootx() - 12
                y = widget.winfo_rooty() - tw_h - 10

                # Push further away from the pointer hotspot to reduce hover flicker.
                x = min(x, pointer_x - tw_w - 14)
                y = min(y, pointer_y - tw_h - 14)
                
                # Keep on screen
                screen_w = tw.winfo_screenwidth()
                screen_h = tw.winfo_screenheight()
                
                if x + tw_w > screen_w:
                    x = screen_w - tw_w - 5
                if x < 5:
                    x = 5
                if y < 5:
                    y = min(screen_h - tw_h - 5, widget.winfo_rooty() + widget.winfo_height() + 8)
                if y + tw_h > screen_h:
                    y = widget.winfo_rooty() - tw_h - 2
                
                tw.geometry(f"+{x}+{y}")
                tooltip_win[0] = tw
            except Exception:
                pass
        
        def hide_tooltip(event=None):
            cancel_show()
            if tooltip_win[0]:
                try:
                    tooltip_win[0].destroy()
                except Exception:
                    pass
                tooltip_win[0] = None
        
        widget.bind("<Enter>", schedule_show, add="+")
        widget.bind("<Leave>", hide_tooltip, add="+")
        widget.bind("<Button-1>", hide_tooltip, add="+")
    
    def _apply_gradient_background(self, window, theme):
        """No-op placeholder; gradient support removed to simplify theming."""
        try:
            # Keep method to avoid attribute errors from older callers
            return
        except Exception:
            return
    
    def _apply_pattern_background(self, window, theme):
        """No-op placeholder; pattern overlays removed."""
        try:
            return
        except Exception:
            return

    def _install_drawer_background_image(self):
        """If settings specify a background image, prepare it for the drawer (Toplevel) window.
        Supports file paths and base64 data URIs when Pillow is available. Rendering occurs in _draw_drawer_background.
        """
        # Reset any previous image objects
        try:
            self._drawer_bg_pil = None
            self._drawer_bg_image = None
        except Exception:
            pass
        try:
            theme = self.settings.get("theme", {})
            if not bool(theme.get("background_image_enabled", False)):
                return
            img_val = str(theme.get("background_image", "")).strip()
            if not img_val:
                return
            if not PIL_AVAILABLE:
                return
            # Load via file path or data URI
            if img_val.startswith("data:"):
                try:
                    b64 = img_val.split(",", 1)[1]
                    data = base64.b64decode(b64)
                    from io import BytesIO as _BIO
                    self._drawer_bg_pil = Image.open(_BIO(data)).convert("RGBA")
                except Exception:
                    self._drawer_bg_pil = None
            else:
                try:
                    self._drawer_bg_pil = Image.open(img_val).convert("RGBA")
                except Exception:
                    self._drawer_bg_pil = None
            if self._drawer_bg_pil is None:
                return
            # Keep fit mode
            self._drawer_bg_fit = theme.get("background_image_fit", "cover")
            # Create initial PhotoImage sized to drawer; resized on draw
            w, h = self._get_drawer_dimensions()
            try:
                self._drawer_bg_image = ImageTk.PhotoImage(self._drawer_bg_pil.resize((max(1, int(w)), max(1, int(h))), Image.Resampling.LANCZOS))
            except Exception:
                self._drawer_bg_image = None
        except Exception:
            # Do not crash on theme/image errors
            self._drawer_bg_pil = None
            self._drawer_bg_image = None

    def _draw_drawer_background(self, canvas):
        """Draw or update the drawer background image onto the given Canvas respecting fit mode."""
        try:
            if not getattr(self, "_drawer_bg_pil", None) or not PIL_AVAILABLE:
                return
            cw = max(1, int(canvas.winfo_width()))
            ch = max(1, int(canvas.winfo_height()))
            fit = getattr(self, "_drawer_bg_fit", "cover")

            img = self._drawer_bg_pil
            iw, ih = img.size
            if iw <= 0 or ih <= 0:
                return
            # Compute scale based on fit
            if fit == "contain":
                scale = min(cw / iw, ch / ih)
            else:  # cover
                scale = max(cw / iw, ch / ih)
            nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
            try:
                resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            except Exception:
                resized = img
            self._drawer_bg_image = ImageTk.PhotoImage(resized)
            # Center image
            x = (cw - nw) // 2
            y = (ch - nh) // 2
            # Use a dedicated canvas tag for background
            try:
                canvas.delete("__bg__")
            except Exception:
                pass
            canvas.create_image(x, y, anchor="nw", image=self._drawer_bg_image, tags="__bg__")
            # Ensure scrollable frame stays above background
            try:
                if hasattr(self, "_canvas_window"):
                    canvas.tag_raise(self._canvas_window)
            except Exception:
                pass
        except Exception:
            pass

    def _create_enhanced_button(self, parent, text, command, bg_color=None, fg_color=None, hover_color=None, **kwargs):
        """Create an enhanced button with professional styling and accessibility"""
        if bg_color is None:
            bg_color = self.settings["theme"]["button_bg"]
        if fg_color is None:
            fg_color = self.settings["theme"]["foreground"]
        if hover_color is None:
            hover_color = self.settings["theme"]["button_hover"]

        # Create a frame to act as the button container
        button_frame = tk.Frame(parent, bg=bg_color, relief="flat", bd=0)

        # Create the actual button label with enhanced styling
        button = tk.Label(
            button_frame,
            text=text,
            font=self.ui_font(kwargs.get("font_size", 9), kwargs.get("font_weight", "normal")),
            bg=bg_color,
            fg=fg_color,
            cursor="hand2",
            relief="flat",
            bd=0,
            padx=kwargs.get("padx", 8),
            pady=kwargs.get("pady", 4),
            takefocus=1  # Enable focus for keyboard navigation
        )
        button.pack(fill="both", expand=True)

        # Enhanced click event with visual feedback
        def on_click(event):
            # Visual feedback
            original_bg = button.cget("bg")
            button.configure(bg=self._blend_colors(original_bg, "#000000", 0.2))
            button_frame.configure(bg=self._blend_colors(original_bg, "#000000", 0.2))
            command()
            # Restore color after a short delay
            button.after(100, lambda: button.configure(bg=original_bg))
            button.after(100, lambda: button_frame.configure(bg=original_bg))

        # Bind click event
        button.bind("<Button-1>", on_click)
        button_frame.bind("<Button-1>", on_click)

        # Enhanced hover effects with smooth transitions
        def on_enter(event):
            button.configure(bg=hover_color)
            button_frame.configure(bg=hover_color)
            # Add subtle border effect
            button.configure(relief="solid", bd=1)

        def on_leave(event):
            button.configure(bg=bg_color)
            button_frame.configure(bg=bg_color)
            button.configure(relief="flat", bd=0)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button_frame.bind("<Enter>", on_enter)
        button_frame.bind("<Leave>", on_leave)

        # Keyboard navigation support
        def on_key_press(event):
            if event.keysym == "Return" or event.keysym == "space":
                on_click(event)
            elif event.keysym == "Tab":
                # Move to next widget
                button.tk_focusNext().focus_set()
                return "break"

        button.bind("<Key>", on_key_press)
        button_frame.bind("<Key>", on_key_press)

        # High contrast mode support
        if self.settings.get("high_contrast", False):
            high_contrast_fg = self._get_high_contrast_color(bg_color)
            button.configure(fg=high_contrast_fg)

        return button_frame

    def _create_bar_button(self, parent, text, command=None, bg_color=None, fg_color=None,
                           hover_color=None, active_color=None, font_size=9, padx=4, pady=2,
                           fixed_size=None, border_color=None, glow_color=None):
        """Create a compact icon button optimized for the main bar with polished styling."""
        if bg_color is None:
            bg_color = self.settings["theme"].get("button_bg", "#2a2a2a")
        if fg_color is None:
            fg_color = self.settings["theme"].get("foreground", "#ffffff")
        if hover_color is None:
            hover_color = self.settings["theme"].get("button_hover", bg_color)
        if active_color is None:
            active_color = self._blend_colors(hover_color, "#000000", 0.2)
        fg_color = self._text_on(bg_color, fg_color)

        # Subtle border that blends with the background (less harsh than solid border)
        border_color = border_color or self._blend_colors(
            self.settings["theme"].get("border", "#444444"),
            bg_color, 0.5
        )
        glow_color = glow_color or self._blend_colors(
            self.settings["theme"].get("highlight", "#00e5e5"),
            "#ffffff",
            0.12
        )
        hover_fg = self._text_on(hover_color, fg_color, min_ratio=3.0)
        frame = tk.Frame(parent, bg=bg_color, highlightthickness=1,
                         highlightbackground=border_color)
        if fixed_size:
            try:
                frame._fixed_size = int(fixed_size)
                frame.configure(width=int(fixed_size), height=int(fixed_size))
                frame.pack_propagate(False)
                frame.grid_propagate(False)
            except Exception:
                pass
        label = tk.Label(
            frame,
            text=text,
            font=self.emoji_font(font_size),
            bg=bg_color,
            fg=fg_color,
            padx=0 if fixed_size else padx,
            pady=0 if fixed_size else pady,
            cursor="hand2",
            takefocus=1
        )
        if fixed_size:
            # Center the glyph inside a fixed square hitbox (prevents DPI rounding glitches)
            label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            label.pack(fill="both", expand=True)

        # Highlight color for hover border accent
        highlight = self.settings["theme"].get("highlight", "#00e5e5")

        def apply_colors(color):
            frame.configure(bg=color)
            label.configure(bg=color)

        def on_enter(_e=None):
            start = frame.cget("bg")
            # Smoother hover with more animation steps
            self._animate_color(frame, start, hover_color, steps=6, delay=10)
            self._animate_color(label, label.cget("bg"), hover_color, steps=6, delay=10)
            # Subtle highlight border on hover
            try:
                hover_border = self._blend_colors(border_color, highlight, 0.45)
                frame.configure(highlightbackground=hover_border)
                label.configure(fg=hover_fg)
            except Exception:
                pass

        def on_leave(_e=None):
            start = frame.cget("bg")
            self._animate_color(frame, start, bg_color, steps=6, delay=10)
            self._animate_color(label, label.cget("bg"), bg_color, steps=6, delay=10)
            try:
                frame.configure(highlightbackground=border_color)
                label.configure(fg=fg_color)
            except Exception:
                pass

        def on_click(_e=None):
            if not command:
                return "break"
            self._animate_color(frame, frame.cget("bg"), active_color, steps=3, delay=12)
            self._animate_color(label, label.cget("bg"), active_color, steps=3, delay=12)
            try:
                frame.configure(highlightbackground=glow_color)
            except Exception:
                pass
            frame.after(80, lambda: apply_colors(bg_color))
            def restore_border():
                try:
                    frame.configure(highlightbackground=border_color)
                except Exception:
                    pass
            frame.after(120, restore_border)
            command()
            return "break"

        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        label.bind("<Button-1>", on_click)
        frame.bind("<Button-1>", on_click)
        label.bind("<Return>", on_click)
        frame.bind("<Return>", on_click)

        frame.icon_label = label
        frame._icon_label = label
        return frame

    def _create_modern_button(self, parent, text, command, bg_color=None, fg_color=None, hover_color=None, **kwargs):
        """Create a compact, high-contrast action button with subtle hover/press states."""
        if bg_color is None:
            bg_color = self.settings["theme"]["button_bg"]
        if fg_color is None:
            fg_color = self.settings["theme"]["foreground"]
        if hover_color is None:
            hover_color = self.settings["theme"]["button_hover"]
        fg_color = self._text_on(bg_color, fg_color)
        hover_fg = self._text_on(hover_color, fg_color, min_ratio=3.0)
        active_color = kwargs.get("active_color", self._blend_colors(hover_color, "#000000", 0.18))
        border_color = kwargs.get(
            "border_color",
            self._blend_colors(self.settings["theme"].get("border", "#3a3a3a"), bg_color, 0.45)
        )
        hover_border = self._blend_colors(border_color, self.settings["theme"].get("highlight", "#00e5e5"), 0.40)
        active_border = self._blend_colors(hover_border, "#ffffff", 0.12)

        # Create a frame to act as the button container
        button_frame = tk.Frame(
            parent,
            bg=bg_color,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=border_color,
        )

        # Create the actual button label
        pad_x = int(kwargs.get("padx", 8))
        pad_y = int(kwargs.get("pady", 4))
        button = tk.Label(
            button_frame,
            text=text,
            font=self.ui_font(kwargs.get("font_size", 9), kwargs.get("font_weight", "normal")),
            bg=bg_color,
            fg=fg_color,
            cursor="hand2",
            relief="flat",
            bd=0,
            padx=pad_x,
            pady=pad_y
        )
        button.pack(fill="both", expand=True)

        def _apply(bg, border, fg):
            try:
                button.configure(bg=bg, fg=fg)
                button_frame.configure(bg=bg, highlightbackground=border)
            except Exception:
                pass

        # Modern hover effects
        def on_enter(_event=None):
            _apply(hover_color, hover_border, hover_fg)

        def on_leave(_event=None):
            _apply(bg_color, border_color, fg_color)

        def on_click(_event=None):
            _apply(active_color, active_border, hover_fg)
            try:
                button_frame.after(95, on_leave)
            except Exception:
                pass
            try:
                command()
            except Exception:
                pass
            return "break"

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button_frame.bind("<Enter>", on_enter)
        button_frame.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_click)
        button_frame.bind("<Button-1>", on_click)
        button.bind("<Return>", on_click)
        button_frame.bind("<Return>", on_click)
        button.bind("<space>", on_click)
        button_frame.bind("<space>", on_click)

        return button_frame

    def _get_high_contrast_color(self, bg_color):
        """Calculate high contrast foreground color for accessibility"""
        try:
            # Convert hex to RGB
            bg_color = bg_color.lstrip('#')
            r, g, b = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))

            # Calculate luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

            # Return high contrast color based on luminance
            return "#FFFFFF" if luminance < 0.5 else "#000000"
        except Exception:
            return "#FFFFFF"  # Default to white on error

    def _contrast_ratio(self, color1, color2):
        """Return WCAG contrast ratio between two hex colors."""
        try:
            def _luminance(hex_color):
                hex_color = hex_color.lstrip("#")
                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                def _channel(c):
                    c = c / 255.0
                    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                r_l = _channel(r)
                g_l = _channel(g)
                b_l = _channel(b)
                return 0.2126 * r_l + 0.7152 * g_l + 0.0722 * b_l
            l1 = _luminance(color1)
            l2 = _luminance(color2)
            lighter = max(l1, l2)
            darker = min(l1, l2)
            return (lighter + 0.05) / (darker + 0.05)
        except Exception:
            return 1.0

    def _ensure_contrast(self, bg_color, fg_color, min_ratio=4.5):
        """Return a readable foreground color for a given background."""
        try:
            if self.settings.get("high_contrast", False):
                return self._get_high_contrast_color(bg_color)
        except Exception:
            pass
        if not fg_color:
            return self._get_high_contrast_color(bg_color)
        try:
            if self._contrast_ratio(bg_color, fg_color) >= float(min_ratio):
                return fg_color
        except Exception:
            pass
        return self._get_high_contrast_color(bg_color)

    def _text_on(self, bg_color, preferred=None, min_ratio=4.5):
        """Pick a legible text color for a given background."""
        base = preferred or self.settings.get("theme", {}).get("foreground", "#ffffff")
        return self._ensure_contrast(bg_color, base, min_ratio=min_ratio)

    def _check_overflow_and_adjust(self):
        """Check if buttons overflow container and adjust if needed"""
        try:
            if hasattr(self, 'button_frame') and self.button_frame.winfo_exists():
                # Get total required width and available width
                buttons = []
                for attr in ("icon_wrap", "prompts_btn", "drag_handle", "import_btn"):
                    btn = getattr(self, attr, None)
                    try:
                        if btn is not None and btn.winfo_exists():
                            buttons.append(btn)
                    except Exception:
                        pass
                total_width = sum(btn.winfo_width() for btn in buttons)
                available_width = self.button_frame.winfo_width()

                # If overflow detected, reduce padding
                if total_width > available_width and hasattr(self, 'current_bar_scale'):
                    reduction_factor = available_width / total_width
                    new_padx = max(1, int(2 * self.current_bar_scale * reduction_factor))

                    # Apply reduced padding to all buttons
                    for btn in buttons:
                        try:
                            if btn.winfo_exists():
                                for child in btn.winfo_children():
                                    try:
                                        child.configure(padx=new_padx)
                                    except Exception:
                                        pass
                        except Exception:
                            pass
        except Exception:
            pass  # Silently handle overflow detection errors

    # ─────────────────────────────── Clipboard & placeholders ───────────────────────────────
    def _fill_placeholders(self, text):
        """If {placeholders} exist, prompt user to fill; return filled text or None if cancelled.
        Rules:
        - Only treat tokens of the form {name} where name matches [A-Za-z_][A-Za-z0-9_]{0,31}
          (must start with a letter/underscore; purely numeric braces like {4} are ignored).
        - Ignore JSON/object braces, regex quantifiers (e.g., {2}, {1,3}), and anything inside
          inline or block code spans delimited by backticks.
        - Users can escape literal braces with double braces: {{ and }}
        """
        try:
            # Temporarily mask escaped literal braces ({{, }}) to avoid false positives
            MASK_L = "\uFFF0"; MASK_R = "\uFFF1"
            masked = text.replace("{{", MASK_L).replace("}}", MASK_R)

            # Mask regex quantifiers like {2} or {1,3}
            def _mask_regex_quantifiers(m):
                s = m.group(0)
                return s.replace("{", MASK_L).replace("}", MASK_R)

            masked = re.sub(r"\{\d+(?:,\d+)?\}", _mask_regex_quantifiers, masked)

            # Mask braces that appear inside inline `code` or triple ```code``` blocks
            def _mask_braces_in_code(m):
                s = m.group(0)
                return s.replace("{", MASK_L).replace("}", MASK_R)

            masked = re.sub(r"```[\s\S]*?```", _mask_braces_in_code, masked)
            masked = re.sub(r"`[^`]*`", _mask_braces_in_code, masked)

            # Extract only simple placeholder variables (letter/underscore first)
            raw = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]{0,31})\}", masked)
            # Preserve order while deduping
            seen = set(); placeholders = []
            for p in raw:
                if p not in seen:
                    seen.add(p)
                    placeholders.append(p)
        except Exception:
            placeholders = []
        if not placeholders:
            return text
        # If exactly one placeholder, show a tiny one-field popup
        if len(placeholders) == 1:
            value = self._ask_string_modal(self.root, "Fill", f"{placeholders[0]}:")
            if value is None:
                return None
            out = masked.replace("{" + placeholders[0] + "}", value)
            # Unmask escaped braces back to literals
            return out.replace(MASK_L, "{").replace(MASK_R, "}")
        # Multiple placeholders: small form
        popup = tk.Toplevel(self.root)
        popup.title("Fill Variables")
        try:
            self._apply_window_icon(popup)
        except Exception:
            pass
        try:
            popup.transient(self.root)
        except Exception:
            pass
        popup.attributes("-topmost", True)
        bg = self.settings["theme"]["background"]
        fg = self._text_on(bg, self.settings["theme"].get("foreground", "#ffffff"))
        accent = self.settings["theme"].get("accent", bg)
        accent_fg = self._text_on(accent, fg)
        popup.configure(bg=bg)
        try:
            popup.lift()
            popup.focus_force()
        except Exception:
            pass
        self._center_window(popup, self.root)
        frm = tk.Frame(popup, bg=bg)
        frm.pack(padx=10, pady=10)
        entries = {}
        for ph in placeholders:
            tk.Label(frm, text=ph+":", bg=bg, fg=fg).pack(anchor="w")
            e = tk.Entry(frm, bg=accent, fg=accent_fg, relief="flat", insertbackground=accent_fg)
            e.pack(fill="x", pady=(0,6))
            entries[ph] = e
        out = {"cancelled": False}
        def on_ok():
            popup.destroy()
        def on_cancel():
            out["cancelled"] = True
            popup.destroy()
        btns = tk.Frame(frm, bg=bg) 
        btns.pack(fill="x", pady=(6,0))
        tk.Button(btns, text="OK", command=on_ok, bg="#4CAF50", fg="white", relief="flat").pack(side="right")
        tk.Button(btns, text="Cancel", command=on_cancel, bg="#ff4444", fg="white", relief="flat").pack(side="right", padx=(0,6))
        # Focus first entry
        try:
            next(iter(entries.values())).focus_set()
        except Exception:
            pass
        try:
            popup.grab_set()
        except Exception:
            pass
        popup.wait_window()
        if out["cancelled"]:
            return None
        # Apply replacements on masked text
        filled = masked
        for ph, e in entries.items():
            filled = filled.replace("{"+ph+"}", e.get())
        # Restore masked literals
        return filled.replace(MASK_L, "{").replace(MASK_R, "}")

    def _auto_paste_if_enabled(self):
        try:
            if sys.platform != 'win32':
                return
            if not self.settings.get("auto_paste", False):
                return
            delay = max(0, int(self.settings.get("paste_delay_ms", 500)))
            def do_paste():
                # Use hotkey service for paste simulation
                self.hotkey_service.simulate_key_press("ctrl+v")
            # Keep drawer open; just paste after a short delay
            self.root.after(delay, do_paste)
        except Exception:
            pass

    def start_drag(self, event):
        """Start dragging the window (from drag handle area)"""
        # Allow dragging if the click originated from the drag handle or its children
        try:
            if not hasattr(self, "drag_handle"):
                return
            w = event.widget
            allowed = False
            # Walk up the widget hierarchy to see if drag_handle is an ancestor
            while w is not None:
                if w == self.drag_handle:
                    allowed = True
                    break
                try:
                    w = w.master
                except Exception:
                    w = None
            if not allowed:
                return
            # Use screen-relative coordinates for stable dragging
            self._drag_offset_x = event.x_root - self.root.winfo_x()
            self._drag_offset_y = event.y_root - self.root.winfo_y()
        except Exception:
            pass
        
    def drag_window(self, event):
        """Drag the window and update dropdown position if open"""
        try:
            if not hasattr(self, "_drag_offset_x") or not hasattr(self, "_drag_offset_y"):
                return
            x = int(event.x_root - self._drag_offset_x)
            y = int(event.y_root - self._drag_offset_y)
            self.root.geometry(f"+{x}+{y}")
            
            # Update dropdown position if it's open
            if getattr(self, "expanded", False) and getattr(self, "drawer", None):
                self._apply_drawer_geometry()
            
            # Save position to settings
            self.settings["position"]["x"] = x
            self.settings["position"]["y"] = y
        except Exception:
            pass
        
    def on_closing(self):
        """Handle application closing"""
        # Save final position and settings
        self.settings["position"]["x"] = self.root.winfo_x()
        self.settings["position"]["y"] = self.root.winfo_y()
        self.save_settings()
        # Unregister global hotkeys if any
        try:
            self._clear_local_hotkey_binding()
        except Exception:
            pass
        try:
            if getattr(self, 'hotkey_registered', False):
                self.hotkey_service.unregister_all_hotkeys()
        except Exception:
            pass
        # Stop tray icon loop safely
        try:
            if getattr(self, 'tray_icon', None):
                self.tray_icon.visible = False
                self.tray_icon.stop()
        except Exception:
            pass
        # Cleanup search and cache services
        try:
            if hasattr(self, 'search_service'):
                self.search_service.destroy()
            if hasattr(self, 'cache_service'):
                self.cache_service.clear()
        except Exception:
            pass
        self.root.destroy()
        
    def toggle_drawer(self, event=None):
        """Toggle the expanded drawer"""
        if not self.expanded:
            self.show_drawer()
        else:
            self.hide_drawer()

    def _get_bar_scale(self):
        try:
            scale = float(self.settings.get("bar_scale", 1.0))
        except Exception:
            scale = 1.0
        return max(0.8, min(2.0, scale))

    def _compute_drawer_width(self):
        # Use persisted drawer_size, but clamp to a compact cap tied to launcher size.
        scale = self._get_bar_scale()
        try:
            screen_w = max(1, int(self.root.winfo_screenwidth()))
        except Exception:
            screen_w = 1920

        try:
            bar_w, _bar_h = self._compute_main_bar_size(scale)
        except Exception:
            bar_w = 140

        min_width = max(280, int(round(240 * min(scale, 1.3))))
        max_by_bar = max(340, int(round(bar_w * 3.2)))
        max_width = min(int(screen_w * 0.85), max_by_bar)

        drawer_size = self.settings.get("drawer_size", {})
        saved_width = int(drawer_size.get("width", 0) or 0)
        if saved_width >= min_width:
            return max(min_width, min(saved_width, max_width))

        base_width = int(round(bar_w * 2.75))
        return max(min_width, min(base_width, max_width))

    def _compute_drawer_base_height(self):
        # Use persisted drawer_size from settings if available
        drawer_size = self.settings.get("drawer_size", {})
        saved_height = drawer_size.get("height", 0)
        if saved_height and saved_height >= 300:
            try:
                screen_h = max(1, int(self.root.winfo_screenheight()))
            except Exception:
                screen_h = 1080
            return max(300, min(int(saved_height), int(screen_h * 0.75)))

        scale = self._get_bar_scale()
        base_height = 460
        height = int(round(base_height * scale))
        min_height = int(round(260 * scale))
        try:
            screen_h = max(1, int(self.root.winfo_screenheight()))
        except Exception:
            screen_h = height
        height = max(min_height, min(height, int(screen_h * 0.75)))
        return height

    def _get_drawer_dimensions(self):
        width = int(getattr(self, "_drawer_width", 0) or 0)
        height = int(getattr(self, "_drawer_height", 0) or 0)
        if width <= 0:
            width = self._compute_drawer_width()
        if height <= 0:
            height = self._compute_drawer_base_height()
        return width, height

    def _apply_drawer_geometry(self, width=None, height=None):
        if not getattr(self, "drawer", None):
            return
        if width is None or height is None:
            width, height = self._get_drawer_dimensions()
        self._drawer_width = int(width)
        self._drawer_height = int(height)
        try:
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_height = self.root.winfo_height()
        except Exception:
            main_x = 0
            main_y = 0
            main_height = 0
        dropdown_x = main_x
        dropdown_y = main_y + main_height
        self.drawer.geometry(f"{int(width)}x{int(height)}+{dropdown_x}+{dropdown_y}")
        
        # Update decoration canvas to match new width
        self._update_decoration_width(int(width))

    def _compute_drawer_content_height(self):
        try:
            if getattr(self, "use_virtual_scrolling", False) and getattr(self, "virtual_list", None):
                item_height = int(getattr(self.virtual_list, "item_height", 42))
                item_count = len(getattr(self, "optimized_items", []) or [])
                return max(0, item_height * item_count)
            if getattr(self, "scrollable_frame", None):
                return int(self.scrollable_frame.winfo_reqheight())
        except Exception:
            pass
        return 0

    def _resize_drawer_to_content(self):
        """Auto-fit the drawer to the current prompt list."""
        if not getattr(self, "drawer", None):
            return
        try:
            self.drawer.update_idletasks()
        except Exception:
            pass

        scale = self._get_bar_scale()
        try:
            screen_h = max(1, int(self.root.winfo_screenheight()))
        except Exception:
            screen_h = 800

        chrome = int(getattr(self, "_drawer_chrome_height", 140))
        content_height = self._compute_drawer_content_height()
        min_height = int(round(260 * scale))
        max_height = min(int(round(560 * scale)), int(screen_h * 0.75))

        desired = chrome + content_height
        desired = max(min_height, min(desired, max_height))
        width = self._compute_drawer_width()
        self._apply_drawer_geometry(width=width, height=desired)
            
    def show_drawer(self):
        """Show the expanded prompt drawer as a dropdown attached to the main bar"""
        self.expanded = True

        # Reuse existing drawer instance when possible (faster + prevents open-time jump).
        try:
            if self.drawer and self.drawer.winfo_exists():
                self.drawer.attributes("-topmost", bool(self.settings.get("always_on_top", True)))
                self._drawer_initializing = True
                self._apply_drawer_geometry()
                self.drawer.deiconify()
                self.drawer.lift()
                try:
                    self.populate_prompts(self._get_search_query())
                    self.update_stats()
                    self._resize_drawer_to_content()
                except Exception:
                    pass
                finally:
                    self._drawer_initializing = False
                self.drawer.attributes("-alpha", 0.0)
                self.animate_dropdown_in()
                return
        except Exception:
            pass

        self.drawer = None
        self._drawer_initializing = True
        
        # Create drawer as a borderless window positioned below the main bar
        self.drawer = tk.Toplevel(self.root)
        self.drawer.overrideredirect(True)  # Remove window decorations for dropdown effect
        self._apply_borderless_style(self.drawer)
        self.drawer.attributes("-topmost", bool(self.settings.get("always_on_top", True)))
        try:
            self._apply_window_icon(self.drawer)
        except Exception:
            pass
        # Removed drawer-specific auto-close shortcuts (Esc/Ctrl+W) to keep the drawer open
        
        # Initial drawer size (auto-fit later based on content)
        w, h = self._get_drawer_dimensions()

        # Use theme colors
        bg_color = self.settings["theme"]["background"]
        self.drawer.configure(bg=bg_color)
        
        # Optional background image for drawer
        try:
            self._install_drawer_background_image()
        except Exception:
            pass
        
        # Position drawer directly below the main window to create dropdown effect
        self._apply_drawer_geometry(width=w, height=h)
        
        # Add subtle border to make it look attached
        drawer_border = self._blend_colors(
            self.settings["theme"].get("border", "#555555"),
            self.settings["theme"].get("highlight", "#00e5e5"),
            0.35
        )
        self.drawer.configure(highlightbackground=drawer_border, highlightthickness=1)
        
        # Add futuristic decorative elements
        self._add_futuristic_decorations()
        
        # Create drawer content
        try:
            self.create_drawer_content()
            # Resolve final geometry before fade-in to avoid visual "jump".
            self._resize_drawer_to_content()
        finally:
            self._drawer_initializing = False

        # Add edge-drag resize handles (bottom and right edges)
        self._install_drawer_resize_handles()
        
        # Add subtle fade-in animation
        self.drawer.attributes("-alpha", 0.0)
        self.animate_dropdown_in()
        
        # Removed focus-out and click-outside handlers so the drawer only closes via minimize/hotkey

    def _install_drawer_resize_handles(self):
        """Add edge-drag resize handles on the bottom and right edges of the drawer."""
        if not getattr(self, "drawer", None):
            return

        highlight = self.settings["theme"].get("highlight", "#00e5e5")
        border = self.settings["theme"].get("border", "#3a3a3a")
        handle_color = self._blend_colors(border, highlight, 0.20)
        handle_hover = self._blend_colors(border, highlight, 0.50)

        # Bottom resize handle (full width, 4px tall)
        bottom_handle = tk.Frame(self.drawer, bg=handle_color, height=4, cursor="sb_v_double_arrow")
        bottom_handle.pack(side="bottom", fill="x")

        # Right resize handle (full height, 4px wide)
        right_handle = tk.Frame(self.drawer, bg=handle_color, width=4, cursor="sb_h_double_arrow")
        right_handle.pack(side="right", fill="y")

        # Corner resize handle (bottom-right, 8x8)
        corner_handle = tk.Frame(self.drawer, bg=handle_hover, width=8, height=8,
                                 cursor="size_nw_se")
        corner_handle.place(relx=1.0, rely=1.0, anchor="se")

        # Resize state
        self._resize_start = {}

        def start_resize_bottom(event):
            self._resize_start = {"y": event.y_root, "h": self.drawer.winfo_height()}

        # Scale-aware resize limits
        try:
            scale = float(self.settings.get("bar_scale", 1.0))
        except Exception:
            scale = 1.0
        min_w = int(220 * scale)
        max_w = int(900 * scale)
        min_h = int(280 * scale)
        max_h = int(1000 * scale)

        def _reflow_after_resize():
            """Update internal layout after resize"""
            try:
                # Update canvas inner frame width to match new drawer width
                canvas = getattr(self, "_drawer_scroll_canvas", None)
                if canvas and hasattr(self, "_canvas_window"):
                    canvas.itemconfigure(self._canvas_window, width=canvas.winfo_width())
                # Update decorations
                w = self.drawer.winfo_width()
                self._update_decoration_width(w)
            except Exception:
                pass

        def do_resize_bottom(event):
            if "h" not in self._resize_start:
                return
            delta = event.y_root - self._resize_start["y"]
            new_h = max(min_h, min(max_h, self._resize_start["h"] + delta))
            w = self.drawer.winfo_width()
            x = self.drawer.winfo_x()
            y = self.drawer.winfo_y()
            self.drawer.geometry(f"{w}x{new_h}+{x}+{y}")

        def start_resize_right(event):
            self._resize_start = {"x": event.x_root, "w": self.drawer.winfo_width()}

        def do_resize_right(event):
            if "w" not in self._resize_start:
                return
            delta = event.x_root - self._resize_start["x"]
            new_w = max(min_w, min(max_w, self._resize_start["w"] + delta))
            h = self.drawer.winfo_height()
            x = self.drawer.winfo_x()
            y = self.drawer.winfo_y()
            self.drawer.geometry(f"{new_w}x{h}+{x}+{y}")
            _reflow_after_resize()

        def start_resize_corner(event):
            self._resize_start = {
                "x": event.x_root, "y": event.y_root,
                "w": self.drawer.winfo_width(), "h": self.drawer.winfo_height()
            }

        def do_resize_corner(event):
            if "w" not in self._resize_start:
                return
            dx = event.x_root - self._resize_start["x"]
            dy = event.y_root - self._resize_start["y"]
            new_w = max(min_w, min(max_w, self._resize_start["w"] + dx))
            new_h = max(min_h, min(max_h, self._resize_start["h"] + dy))
            x = self.drawer.winfo_x()
            y = self.drawer.winfo_y()
            self.drawer.geometry(f"{new_w}x{new_h}+{x}+{y}")
            _reflow_after_resize()

        def end_resize(event):
            """Persist the new drawer size to settings and reflow content."""
            try:
                w = self.drawer.winfo_width()
                h = self.drawer.winfo_height()
                self._drawer_width = w
                self._drawer_height = h
                self.settings.setdefault("drawer_size", {})
                self.settings["drawer_size"]["width"] = w
                self.settings["drawer_size"]["height"] = h
                _reflow_after_resize()
                self.save_settings()
            except Exception:
                pass

        # Hover feedback
        def on_handle_enter(handle, event):
            handle.configure(bg=handle_hover)

        def on_handle_leave(handle, event):
            handle.configure(bg=handle_color)

        for handle, start_fn, drag_fn in [
            (bottom_handle, start_resize_bottom, do_resize_bottom),
            (right_handle, start_resize_right, do_resize_right),
            (corner_handle, start_resize_corner, do_resize_corner),
        ]:
            handle.bind("<Button-1>", start_fn)
            handle.bind("<B1-Motion>", drag_fn)
            handle.bind("<ButtonRelease-1>", end_resize)
            handle.bind("<Enter>", lambda e, h=handle: on_handle_enter(h, e))
            handle.bind("<Leave>", lambda e, h=handle: on_handle_leave(h, e))

    def animate_dropdown_in(self):
        """Animate the dropdown appearing with a smooth butter-like fade-in effect"""
        if not self.drawer:
            return
        
        # Use the new animation system if available
        if MODERN_UI_AVAILABLE and AnimationController is not None:
            try:
                self._drawer_animator = AnimationController(self.drawer, duration_ms=180, fps=60)
                self._drawer_animator.animate_alpha(
                    start=0.0, 
                    end=1.0, 
                    easing=Easing.ease_out_quart
                )
                return
            except Exception:
                pass
        
        # Fallback to basic animation
        total_steps = 12
        step_delay = 15  # 15ms per step = ~60fps
        
        def ease_out_quart(t):
            return 1 - pow(1 - t, 4)
        
        def fade_step(step):
            if not self.drawer:
                return
            try:
                if not self.drawer.winfo_exists():
                    return
            except Exception:
                return
            
            if step <= total_steps:
                progress = step / total_steps
                alpha = ease_out_quart(progress)
                try:
                    self.drawer.attributes("-alpha", alpha)
                except Exception:
                    return
                self.root.after(step_delay, lambda: fade_step(step + 1))
            else:
                try:
                    self.drawer.attributes("-alpha", 1.0)
                except Exception:
                    pass
        
        fade_step(1)
    
    def _add_futuristic_decorations(self):
        """Add futuristic visual decorations to the drawer"""
        if not self.drawer:
            return
        
        bg = self.settings["theme"]["background"]
        highlight = self.settings["theme"].get("highlight", "#00e5e5")
        accent = self.settings["theme"].get("accent", bg)
        
        # Create a decorative frame at the top with layered glow lines
        deco_frame = tk.Frame(self.drawer, bg=bg, height=6)
        deco_frame.pack(fill="x", side="top")
        deco_frame.pack_propagate(False)
        
        # Create canvas for decorative elements
        deco_canvas = tk.Canvas(
            deco_frame,
            bg=bg,
            highlightthickness=0,
            height=6
        )
        deco_canvas.pack(fill="both", expand=True)
        
        # Draw top-line glow and corner callouts
        try:
            w = self._get_drawer_dimensions()[0]
            
            glow_far = self._blend_colors(highlight, bg, 0.88)
            glow_mid = self._blend_colors(highlight, bg, 0.62)
            glow_color = self._blend_colors(highlight, bg, 0.38)
            
            deco_canvas.create_line(0, 5, w, 5, fill=glow_far, width=1, tags="glow_far")
            deco_canvas.create_line(0, 3, w, 3, fill=glow_mid, width=1, tags="glow_line")
            deco_canvas.create_line(0, 2, w, 2, fill=highlight, width=1, tags="bright_line")
            
            # Corner accents
            deco_canvas.create_arc(0, -1, 14, 10, start=180, extent=95,
                                   outline=highlight, style="arc", width=1, tags="left_arc")
            deco_canvas.create_arc(w - 14, -1, w, 10, start=265, extent=95,
                                   outline=highlight, style="arc", width=1, tags="right_arc")
            
            # Store reference for updating after geometry changes
            self._deco_canvas = deco_canvas
            self._deco_highlight = highlight
            self._deco_glow_color = glow_color
        except Exception:
            pass
        
        # Add side "pipe" decorations
        self._add_side_decorations()
    
    def _add_side_decorations(self):
        """Add subtle side decorations that look like futuristic pipes/circuits"""
        if not self.drawer:
            return
        
        bg = self.settings["theme"]["background"]
        highlight = self.settings["theme"].get("highlight", "#00e5e5")
        dim_highlight = self._blend_colors(highlight, bg, 0.68)
        
        # Left side decoration frame
        left_deco = tk.Frame(self.drawer, bg=bg, width=4)
        left_deco.place(x=0, y=10, relheight=0.32)
        
        left_canvas = tk.Canvas(left_deco, bg=bg, highlightthickness=0, width=4)
        left_canvas.pack(fill="both", expand=True)
        
        # Draw vertical accent line and nodes
        try:
            left_canvas.create_line(2, 0, 2, 180, fill=dim_highlight, width=1, tags="spine")
            left_canvas.create_oval(0, 10, 4, 14, fill=highlight, outline="", tags="pulse_node")
            left_canvas.create_oval(0, 56, 4, 60, fill=dim_highlight, outline="", tags="dim_node")
        except Exception:
            pass
        
        # Right side decoration (mirror)
        right_deco = tk.Frame(self.drawer, bg=bg, width=4)
        right_deco.place(relx=1.0, x=-4, y=10, relheight=0.32)
        
        right_canvas = tk.Canvas(right_deco, bg=bg, highlightthickness=0, width=4)
        right_canvas.pack(fill="both", expand=True)
        
        try:
            right_canvas.create_line(2, 0, 2, 180, fill=dim_highlight, width=1, tags="spine")
            right_canvas.create_oval(0, 10, 4, 14, fill=highlight, outline="", tags="pulse_node")
            right_canvas.create_oval(0, 56, 4, 60, fill=dim_highlight, outline="", tags="dim_node")
        except Exception:
            pass
        
        # Start subtle glow animation
        self._animate_glow_decorations(left_canvas, right_canvas, highlight, dim_highlight)
    
    def _update_decoration_width(self, width):
        """Update decoration canvas elements to match new drawer width"""
        if not hasattr(self, '_deco_canvas') or not self._deco_canvas:
            return
        try:
            canvas = self._deco_canvas
            
            # Update all gradient glow lines
            try:
                canvas.coords("glow_far", 0, 5, width, 5)
            except Exception:
                pass
            canvas.coords("glow_line", 0, 3, width, 3)
            canvas.coords("bright_line", 0, 2, width, 2)
            canvas.coords("left_arc", 0, -1, 14, 10)
            canvas.coords("right_arc", width - 14, -1, width, 10)
        except Exception:
            pass
    
    def _animate_glow_decorations(self, left_canvas, right_canvas, bright, dim):
        """Animate subtle glow pulse on decorations"""
        pulse_state = [0]  # 0 = dimming, 1 = brightening
        pulse_step = [0]
        max_steps = 30
        
        def pulse():
            # Stop animation if drawer is closed or doesn't exist
            if not self.drawer or not getattr(self, 'expanded', False):
                return
            try:
                if not self.drawer.winfo_exists():
                    return
            except Exception:
                return
            
            # Calculate current brightness
            step = pulse_step[0]
            if pulse_state[0] == 0:
                ratio = 1 - (step / max_steps) * 0.3  # Dim to 70%
            else:
                ratio = 0.7 + (step / max_steps) * 0.3  # Brighten to 100%
            
            current = self._blend_colors(bright, dim, 1 - ratio)
            
            try:
                left_canvas.itemconfig("pulse_node", fill=current)
                right_canvas.itemconfig("pulse_node", fill=current)
            except Exception:
                pass
            
            pulse_step[0] += 1
            if pulse_step[0] > max_steps:
                pulse_step[0] = 0
                pulse_state[0] = 1 - pulse_state[0]  # Toggle direction
            
            # Continue animation slowly
            try:
                self.drawer.after(100, pulse)
            except Exception:
                pass
        
        # Start pulse after a delay
        try:
            self.drawer.after(500, pulse)
        except Exception:
            pass
    
    def setup_click_outside_handler(self):
        """Setup handler to close dropdown when clicking outside"""
        def check_click_outside(event):
            if not self.expanded or not self.drawer:
                return
                
            # Get the widget that was clicked
            clicked_widget = event.widget
            
            # Check if click was in the main window or dropdown
            clicked_toplevel = clicked_widget.winfo_toplevel()
            
            if clicked_toplevel == self.root or clicked_toplevel == self.drawer:
                # Click was inside our application windows, don't close
                return
            
            # Click was outside - close the dropdown
            self.hide_drawer()
        
        # Bind to root window for global click detection
        self.root.bind_all("<Button-1>", check_click_outside, add="+")
        
    def create_drawer_content(self):
        """Create the content for the expanded drawer"""
        bg = self.settings["theme"]["background"]
        accent = self.settings["theme"].get("accent", bg)
        highlight = self.settings["theme"].get("highlight", accent)
        border = self.settings["theme"].get("border", "#444444")
        base_fg = self._text_on(bg, self.settings["theme"].get("foreground", "#ffffff"))
        muted_fg = self._text_on(bg, self.settings["theme"].get("muted_text", base_fg), min_ratio=3.0)
        header_bg = self._blend_colors(bg, accent, 0.22)
        header_bg = self._blend_colors(header_bg, highlight, 0.06)
        header_edge = self._blend_colors(border, highlight, 0.45)
        header_fg = self._text_on(header_bg, base_fg)

        # Top accent line
        accent_strip_top = tk.Frame(self.drawer, bg=self._blend_colors(highlight, bg, 0.2), height=1)
        accent_strip_top.pack(fill="x", side="top")

        # Futuristic header strip
        header = tk.Frame(self.drawer, bg=header_bg, height=30,
                          highlightbackground=header_edge, highlightthickness=0)
        header.pack(fill="x", padx=4, pady=(0, 0))
        header.pack_propagate(False)

        # Title with styling that matches the main bar
        title_label = tk.Label(
            header,
            text="PROMPT MATRIX",
            font=self.ui_font(10, self.title_weight()),
            bg=header_bg,
            fg=header_fg
        )
        title_label.pack(side="left", padx=8, pady=4)

        # Fold up button (instead of close) - Modern style
        fold_btn = self._create_bar_button(
            header,
            "⤴",
            self.hide_drawer,
            bg_color=header_bg,
            fg_color=header_fg,
            hover_color=self._blend_colors(header_bg, highlight, 0.25),
            active_color=self._blend_colors(header_bg, "#000000", 0.2),
            font_size=8,
            padx=2,
            pady=1
        )
        fold_btn.pack(side="right", padx=4, pady=3)

        # Subtle accent gradient line below header
        header_accent_line = tk.Frame(self.drawer, bg=self._blend_colors(highlight, bg, 0.48), height=1)
        header_accent_line.pack(fill="x", padx=6)

        # Modern search bar with placeholder effect
        search_frame = tk.Frame(self.drawer, bg=bg)
        search_frame.pack(fill="x", padx=8, pady=(4, 6))

        # Search container with border
        search_bg = self._blend_colors(bg, accent, 0.26)
        search_bg = self._blend_colors(search_bg, highlight, 0.04)
        search_border = self._blend_colors(border, highlight, 0.34)
        search_fg = self._text_on(search_bg, base_fg)
        search_muted = self._text_on(search_bg, muted_fg, min_ratio=3.0)
        search_container = tk.Frame(search_frame, bg=search_bg, relief="flat",
                                    highlightbackground=search_border, highlightthickness=1)
        search_container.pack(fill="x", ipady=2, ipadx=3)

        search_icon = tk.Label(search_container, text="⌕", bg=search_bg,
                               fg=search_muted, font=self.ui_font(8))
        search_icon.pack(side="left", padx=(5, 3))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_container,
            textvariable=self.search_var,
            bg=search_bg,
            fg=search_fg,
            insertbackground=search_fg,
            relief="flat",
            font=self.ui_font(9),
            bd=0
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(2, 4), pady=3)
        search_entry.bind("<KeyRelease>", self.filter_prompts)
        # Remember for Ctrl+F focus
        self._search_entry_widget = search_entry

        # Clear button for quick reset - compact
        clear_btn = tk.Label(search_container, text="✕", bg=search_bg,
                             fg=search_muted,
                             font=self.ui_font(8), cursor="hand2", padx=4, pady=1)
        clear_btn.pack(side="right", padx=(0, 4))
        clear_btn.bind("<Button-1>", lambda e: (self.search_var.set(""), self.filter_prompts()))

        # Add placeholder text functionality
        self._search_placeholder_text = "Search the prompt matrix..."
        self._search_placeholder_active = True
        search_entry.insert(0, self._search_placeholder_text)
        search_entry.configure(fg=search_muted)
        
        # Focus glow color for search bar
        search_glow_border = self._blend_colors(highlight, search_border, 0.6)

        def on_search_focus_in(event):
            if search_entry.get() == self._search_placeholder_text:
                search_entry.delete(0, tk.END)
                search_entry.configure(fg=search_fg) 
                self._search_placeholder_active = False
            # Add subtle glow border on focus
            try:
                search_container.configure(highlightbackground=search_glow_border)
            except Exception:
                pass
        
        def on_search_focus_out(event):
            if search_entry.get() == "":
                search_entry.insert(0, self._search_placeholder_text)
                search_entry.configure(fg=search_muted)
                self._search_placeholder_active = True
            # Remove glow border
            try:
                search_container.configure(highlightbackground=search_border)
            except Exception:
                pass
                
        search_entry.bind("<FocusIn>", on_search_focus_in)
        search_entry.bind("<FocusOut>", on_search_focus_out)
        
        # Stats bar showing count
        stats_bg = self._blend_colors(bg, accent, 0.14)
        stats_edge = self._blend_colors(border, highlight, 0.3)
        stats_frame = tk.Frame(self.drawer, bg=stats_bg, highlightbackground=stats_edge, highlightthickness=1)
        stats_frame.pack(fill="x", padx=8, pady=(0, 6))

        self.stats_label = tk.Label(stats_frame, text="", font=self.ui_font(8),
            bg=stats_bg, fg=muted_fg)
        self.stats_label.pack(side="left", padx=(6, 0), pady=3)
        try:
            # small hint on toggle search highlight
            hint_bg = self._blend_colors(stats_bg, highlight, 0.22)
            hint_fg = self._text_on(hint_bg, base_fg)
            hint_label = "Highlight ON" if bool(self.settings.get("search_highlight", True)) else "Highlight OFF"
            hint = tk.Label(stats_frame, text=hint_label, font=self.ui_font(8),
                            bg=hint_bg, fg=hint_fg, cursor="hand2",
                            padx=8, pady=2)
            hint.pack(side="right", padx=4, pady=2)
            def toggle_highlight(event=None):
                self.settings["search_highlight"] = not bool(self.settings.get("search_highlight", True))
                self.save_settings()
                hint.config(
                    text="Highlight ON" if bool(self.settings.get("search_highlight", True)) else "Highlight OFF"
                )
                self.populate_prompts(self._get_search_query())
            hint.bind("<Button-1>", toggle_highlight)
        except Exception:
            pass
        
        # Container for the scrollable list
        list_bg = self._blend_colors(bg, accent, 0.08)
        list_edge = self._blend_colors(border, highlight, 0.22)
        list_container = tk.Frame(
            self.drawer,
            bg=list_bg,
            highlightbackground=list_edge,
            highlightthickness=1,
        )
        list_container.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 6))
        self.list_container = list_container

        # Decide which list implementation to use
        use_virtual = bool(getattr(self, "use_virtual_scrolling", False)) and VIRTUAL_SCROLLING_AVAILABLE
        self._drawer_scroll_canvas = None
        self._drawer_scrollbar = None
        self._drawer_list_host = list_container
        self.scrollable_frame = None

        if not use_virtual:
            # Scrollable content with modern styling
            # If background image is enabled, use a neutral canvas background; image will be drawn separately
            canvas_bg = list_bg
            canvas = tk.Canvas(list_container, bg=canvas_bg, highlightthickness=0, bd=0)

            # Custom scrollbar styling (limited in tkinter, but we can try)
            scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)

            # Scrollbar uses global ttk style (configured in _apply_global_ttk_style)
            # Scroll content frame uses solid theme background for readability
            self.scrollable_frame = tk.Frame(canvas, bg=list_bg)

            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            self._canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Track canvas width changes to keep inner frame fitting
            def _on_canvas_resize(event):
                canvas.itemconfigure(self._canvas_window, width=event.width)
            canvas.bind("<Configure>", _on_canvas_resize, add="+")

            canvas.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=5)

            # Draw background image on resize/scroll if enabled
            try:
                if getattr(self, "_drawer_bg_image", None):
                    def _redraw_bg(event=None):
                        try:
                            self._draw_drawer_background(canvas)
                        except Exception:
                            pass
                    canvas.bind("<Configure>", _redraw_bg)
            except Exception:
                pass
            scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

            self._drawer_scroll_canvas = canvas
            self._drawer_scrollbar = scrollbar
            self._drawer_list_host = self.scrollable_frame

        # Bottom accent line before footer
        footer_accent = tk.Frame(self.drawer, bg=self._blend_colors(highlight, bg, 0.52), height=1)
        footer_accent.pack(side="bottom", fill="x", padx=8, pady=0)

        # Footer with exit button and keyboard hints - polished styling
        footer_bg = self._blend_colors(bg, accent, 0.18)
        footer_fg = self._text_on(footer_bg, muted_fg, min_ratio=3.0)
        footer = tk.Frame(self.drawer, bg=footer_bg, highlightbackground=header_edge, highlightthickness=1)
        footer.pack(side="bottom", fill="x", padx=8, pady=(3, 8))

        # Exit button uses theme highlight color for more cohesive look
        exit_bg = self._blend_colors(highlight, "#000000", 0.35)
        exit_hover = self._blend_colors(highlight, "#000000", 0.15)
        exit_fg_color = self._text_on(exit_bg, "#ffffff")
        exit_btn = self._create_bar_button(
            footer,
            "Shutdown",
            self.exit_app,
            bg_color=exit_bg,
            fg_color=exit_fg_color,
            hover_color=exit_hover,
            active_color=self._blend_colors(exit_hover, "#000000", 0.2),
            font_size=9,
            padx=6,
            pady=2,
            border_color=self._blend_colors(border, highlight, 0.5),
            glow_color=self._blend_colors(highlight, "#ffffff", 0.16),
        )
        exit_btn.pack(side="right", padx=6, pady=4)
        # Keyboard hints - styled as pill badges
        try:
            hint_frame = tk.Frame(footer, bg=footer_bg)
            hint_frame.pack(side="left", padx=6, pady=3)
            hint_key_bg = self._blend_colors(footer_bg, accent, 0.35)
            for key_text, desc_text in [("F1", "Guide"), ("Ctrl+F", "Search"), ("Esc", "Clear")]:
                pill = tk.Frame(hint_frame, bg=footer_bg)
                pill.pack(side="left", padx=(0, 6))
                tk.Label(pill, text=key_text, bg=hint_key_bg,
                         fg=highlight, font=self.ui_font(7),
                         padx=3, pady=0).pack(side="left")
                tk.Label(pill, text=desc_text, bg=footer_bg,
                         fg=footer_fg, font=self.ui_font(7),
                         padx=2).pack(side="left")
        except Exception:
            pass

        # Cache chrome height for auto-fit calculations
        try:
            self.drawer.update_idletasks()
            chrome = (
                header.winfo_reqheight()
                + search_frame.winfo_reqheight()
                + stats_frame.winfo_reqheight()
                + footer.winfo_reqheight()
                + 28
            )
            self._drawer_chrome_height = chrome
        except Exception:
            pass
        
        # Enhanced mouse wheel scrolling
        def _drawer_scroll_target():
            if getattr(self, "_drawer_scroll_canvas", None):
                return self._drawer_scroll_canvas
            if getattr(self, "virtual_list", None) and getattr(self.virtual_list, "canvas", None):
                return self.virtual_list.canvas
            return None

        def on_mousewheel(event):
            target = _drawer_scroll_target()
            if not target:
                return
            target.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_mousewheel(event):
            target = _drawer_scroll_target()
            if not target:
                return
            target.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel(event):
            target = _drawer_scroll_target()
            if not target:
                return
            target.unbind_all("<MouseWheel>")

        # Bind scroll wheel when mouse enters the drawer
        self.drawer.bind('<Enter>', bind_mousewheel)
        self.drawer.bind('<Leave>', unbind_mousewheel)
        if getattr(self, "_drawer_scroll_canvas", None):
            self._drawer_scroll_canvas.bind('<Enter>', bind_mousewheel)
            self._drawer_scroll_canvas.bind('<Leave>', unbind_mousewheel)
        
        # Enable keyboard-first navigation
        try:
            self.drawer.bind_all("<Control-f>", lambda e: self._focus_search())
            self.drawer.bind_all("<Up>", self._nav_up)
            self.drawer.bind_all("<Down>", self._nav_down)
            self.drawer.bind_all("<Return>", self._nav_enter)
            self.drawer.bind_all("<Control-q>", lambda e: self.exit_app())
            self.drawer.bind_all("<F1>", lambda e: self.show_help_about())
            # Clear search quickly
            try:
                search_entry.bind("<Escape>", lambda e: (self.search_var.set(""), self.filter_prompts()))
            except Exception:
                pass
        except Exception:
            pass

        # Session behavior: first open starts collapsed; later opens keep last-copied category expanded
        try:
            self._apply_prompt_matrix_session_state()
        except Exception:
            pass

        # Populate with prompts
        self.populate_prompts()
        self.update_stats()

    # ─────────────────────────────── Prompt helpers ───────────────────────────────
    def preview_prompt(self, prompt):
        """Show a lightweight preview window for a prompt"""
        try:
            preview = tk.Toplevel(self.root)
            preview.title(prompt.get("title", "Preview"))
            bg = self.settings["theme"]["background"]
            fg = self._text_on(bg, self.settings["theme"].get("foreground", "#ffffff"))
            button_bg = self.settings["theme"].get("button_bg", self.settings["theme"].get("accent", bg))
            button_fg = self._text_on(button_bg, fg)
            preview.configure(bg=bg) 
            preview.attributes("-topmost", True)
            try:
                preview.bind("<Escape>", lambda e: preview.destroy())
            except Exception:
                pass

            frame = tk.Frame(preview, bg=bg) 
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            label = tk.Label(frame, text=prompt.get("title", ""), font=self.ui_font(11, self.title_weight()),
                             bg=bg, fg=fg) 
            label.pack(anchor="w", pady=(0, 6))

            text = tk.Text(frame, height=12, wrap="word", bg=button_bg, fg=button_fg, relief="flat", font=self.mono_font(10)) 
            text.insert("1.0", prompt.get("prompt", ""))
            text.configure(state="disabled")
            text.pack(fill="both", expand=True)

            btns = tk.Frame(frame, bg=bg) 
            btns.pack(fill="x", pady=(8, 0))

            tk.Button(btns, text="📋 Copy", command=lambda: self.copy_prompt(prompt),
                      bg="#4CAF50", fg="white", relief="flat").pack(side="left")
            tk.Button(btns, text="Close", command=preview.destroy, bg="#444444", fg="white", relief="flat").pack(side="right")
        except Exception:
            # Fallback
            try:
                messagebox.showinfo(prompt.get("title", "Preview"), prompt.get("prompt", ""))
            except Exception:
                pass

    def edit_prompt(self, prompt):
        """Open the editor (single-instance); user can edit the item from there"""
        self.open_prompt_editor()
        
    def _init_optimized_ui(self):
        """Initialize optimized UI components"""
        if not VIRTUAL_SCROLLING_AVAILABLE:
            return

        # Initialize UI optimizer
        self.ui_optimizer = UIOptimizer(performance_threshold=0.1)

        # Track virtual scrolling component
        self.virtual_list = None
        self.optimized_items = []

        # Performance tracking
        self.last_populate_time = 0
        self.populate_count = 0

    def _prepare_optimized_items(self, filter_text: str = ""):
        """
        Prepare flattened list of items for virtual scrolling
        Returns items with hierarchical information preserved
        """
        start_time = time.time()
        items = []

        # Add favorites section if enabled
        if not filter_text.strip() and self.settings.get("favorites"):
            try:
                fav_prompts = []
                for fid in self.settings.get("favorites", [])[:20]:
                    cat_path, idx, p = self._find_prompt_by_id(fid)
                    if p:
                        fav_prompts.append(p)

                if fav_prompts:
                    favorites_collapsed = '__favorites__' in getattr(self, 'collapsed_categories', set())
                    # Add favorites as a special category
                    items.append({
                        'type': 'category',
                        'title': '⭐ Favorites',
                        'level': 0,
                        'category_path': '__favorites__',
                        'is_collapsed': favorites_collapsed,
                        'data': {'prompts': fav_prompts, 'subcategories': {}}
                    })

                    # Add favorite prompts
                    if not favorites_collapsed:
                        for prompt in fav_prompts:
                            if self._prompt_matches_filter(prompt, filter_text):
                                items.append({
                                    'type': 'prompt',
                                    'prompt': prompt,
                                    'level': 1,
                                    'category_path': '__favorites__',
                                    'data': prompt
                                })
            except Exception:
                pass

        # Process all categories
        for category_name, category_data in self.prompts["categories"].items():
            if self._category_matches_filter(category_name, category_data, filter_text):
                self._add_category_items_optimized(
                    items, category_name, category_data, filter_text, 0
                )

        preparation_time = time.time() - start_time
        try:
            self.logger.debug("Prepared %s virtual items in %.3fs", len(items), preparation_time)
        except Exception:
            pass

        return items

    def _add_category_items_optimized(self, items, category_name: str, category_data, filter_text: str, level: int, path_prefix: str = ""):
        """Add category and its contents to the flattened items list"""

        real_path = f"{path_prefix}/{category_name}" if path_prefix else category_name
        category_path = f"{category_name}_level_{level}"
        is_collapsed = category_path in getattr(self, 'collapsed_categories', set())

        # Add category header
        items.append({
            'type': 'category',
            'title': category_name,
            'level': level,
            'category_path': category_path,
            'real_path': real_path,
            'is_collapsed': is_collapsed,
            'data': category_data,
            'color': category_data.get("color") or self.settings["theme"].get("category_bar", "#222222")
        })

        # Add contents if not collapsed
        if not is_collapsed:
            # Add direct prompts
            if "prompts" in category_data:
                for prompt in category_data["prompts"]:
                    if self._prompt_matches_filter(prompt, filter_text):
                        items.append({
                            'type': 'prompt',
                            'prompt': prompt,
                            'level': level + 1,
                            'category_path': real_path,
                            'data': prompt,
                            'is_favorite': self._is_favorite(prompt)
                        })

            # Add subcategories
            if "subcategories" in category_data:
                for sub_name, sub_data in category_data["subcategories"].items():
                    if self._category_matches_filter(sub_name, sub_data, filter_text):
                        self._add_category_items_optimized(
                            items, sub_name, sub_data, filter_text,
                            level + 1, real_path
                        )

    def _create_virtual_item_widget(self, parent, item, index: int):
        """
        Create a widget for a virtual list item
        This is the render callback for the virtual scrolling list
        """
        try:
            if item['type'] == 'category':
                return self._create_virtual_category_widget(parent, item, index)
            elif item['type'] == 'prompt':
                return self._create_virtual_prompt_widget(parent, item, index)
            else:
                # Fallback
                return tk.Label(parent, text="Unknown item type", bg="red")
        except Exception as e:
            try:
                self.logger.warning("Error creating widget for item %s: %s", index, e)
            except Exception:
                pass
            return tk.Label(parent, text="Error loading item", bg="gray")

    def _create_virtual_category_widget(self, parent, item, index: int):
        """Create a category widget for virtual scrolling."""
        indent = "  " * item['level']
        expand_icon = "▸" if item['is_collapsed'] else "▾"
        folder_icon = "◉" if not item['is_collapsed'] else "○"

        base_bg = self.settings["theme"].get("background", "#060a12")
        accent = self.settings["theme"].get("accent", base_bg)
        highlight = self.settings["theme"].get("highlight", accent)
        border = self.settings["theme"].get("border", "#3a3a3a")
        card_bg = self._blend_colors(base_bg, accent, 0.24)
        card_edge = self._blend_colors(border, highlight, 0.38)
        cat_fg = self._text_on(card_bg, self.settings["theme"].get("foreground", "#ffffff"))
        cat_color = item.get('color') or self.settings["theme"].get("category_bar", "#222222")

        cat_frame = tk.Frame(
            parent,
            bg=card_bg,
            relief="flat",
            highlightbackground=card_edge,
            highlightthickness=1,
            height=40
        )
        cat_frame.pack(fill="x", pady=2, padx=6)

        cat_container = tk.Frame(cat_frame, bg=card_bg)
        cat_container.pack(fill="x", padx=6, pady=4)

        strip = tk.Frame(cat_container, bg=cat_color, width=3)
        strip.pack(side="left", fill="y", padx=(0, 6))

        cat_label = tk.Label(
            cat_container,
            text=f"{indent}{expand_icon} {folder_icon} {item['title']}",
            font=self.ui_font(10, self.title_weight()),
            bg=card_bg,
            fg=cat_fg,
            anchor="w",
            cursor="hand2",
            padx=4,
            pady=2
        )
        cat_label.pack(side="left", fill="x", expand=True)

        cat_label.bind("<Button-1>", lambda e: self._toggle_virtual_category(item))

        hover_color = self._blend_colors(card_bg, highlight, 0.2)
        cat_label.bind("<Enter>", lambda e: self._animate_color(cat_label, card_bg, hover_color))
        cat_label.bind("<Leave>", lambda e: self._animate_color(cat_label, cat_label.cget("bg"), card_bg))
        cat_frame.bind("<Enter>", lambda e: self._animate_color(cat_frame, card_bg, hover_color))
        cat_frame.bind("<Leave>", lambda e: self._animate_color(cat_frame, cat_frame.cget("bg"), card_bg))

        cat_frame.item_data = item
        return cat_frame

    def _create_virtual_prompt_widget(self, parent, item, index: int):
        """Create a compact prompt widget for virtual scrolling."""
        prompt = item['prompt']
        star = "★ " if item.get('is_favorite', False) else ""
        title_text = prompt.get('title', '')
        display_text = f"{star}{title_text}"

        base_bg = self.settings["theme"].get("background", "#1a1a1a")
        accent = self.settings["theme"].get("accent", base_bg)
        highlight = self.settings["theme"].get("highlight", accent)
        border = self.settings["theme"].get("border", "#3a3a3a")
        row_bg = self._blend_colors(base_bg, accent, 0.16)
        row_edge = self._blend_colors(border, highlight, 0.3)
        row_hover = self._blend_colors(row_bg, highlight, 0.2)
        button_bg = self.settings["theme"].get("button_bg", "#333333")
        button_bg = self._blend_colors(button_bg, accent, 0.15)
        button_fg = self._text_on(button_bg, self.settings["theme"].get("foreground", "#ffffff"))

        prompt_frame = tk.Frame(
            parent,
            bg=row_bg,
            relief="flat",
            highlightbackground=row_edge,
            highlightthickness=1,
            height=30
        )
        prompt_frame.pack(fill="x", pady=1, padx=4)

        prompt_container = tk.Frame(prompt_frame, bg=button_bg, relief="flat", bd=0)
        prompt_container.pack(fill="x", padx=1, pady=1)

        accent_strip = tk.Frame(prompt_container, bg=highlight, width=3)
        accent_strip.pack(side="left", fill="y", padx=(0, 4))

        prompt_btn = tk.Label(
            prompt_container,
            text=display_text,
            font=self.ui_font(9, self.title_weight()),
            bg=button_bg,
            fg=button_fg,
            anchor="w",
            cursor="hand2",
            padx=6 + (item['level'] * 6),
            pady=3
        )
        prompt_btn.pack(fill="x")

        prompt_btn.bind("<Button-1>", lambda e: self.copy_prompt(prompt, item.get('category_path')))

        prompt_text = prompt.get('prompt', '')
        if prompt_text:
            self._attach_tooltip(prompt_btn, prompt_text, delay=350)

        def on_enter(_e=None):
            self._animate_color(prompt_frame, prompt_frame.cget("bg"), row_hover)
            self._animate_color(prompt_container, prompt_container.cget("bg"), row_hover)
            self._animate_color(prompt_btn, prompt_btn.cget("bg"), row_hover)

        def on_leave(_e=None):
            self._animate_color(prompt_frame, prompt_frame.cget("bg"), row_bg)
            self._animate_color(prompt_container, prompt_container.cget("bg"), button_bg)
            self._animate_color(prompt_btn, prompt_btn.cget("bg"), button_bg)

        prompt_btn.bind("<Enter>", on_enter, add="+")
        prompt_btn.bind("<Leave>", on_leave, add="+")

        prompt_frame.prompt_data = prompt
        return prompt_frame

    def _toggle_virtual_category(self, item):
        """Toggle category collapse state in virtual scrolling"""
        category_path = item['category_path']

        if category_path in getattr(self, 'collapsed_categories', set()):
            self.collapsed_categories.remove(category_path)
            item['is_collapsed'] = False
        else:
            self.collapsed_categories.add(category_path)
            item['is_collapsed'] = True

        # Refresh the virtual list
        if hasattr(self, 'virtual_list') and self.virtual_list:
            self._debounced_populate_prompts()

    def populate_prompts_optimized(self, filter_text: str = ""):
        """
        Optimized version of populate_prompts using virtual scrolling
        Provides 10x+ performance improvement
        """
        if not VIRTUAL_SCROLLING_AVAILABLE:
            # Fallback to original method
            return self.populate_prompts_original(filter_text)

        start_time = time.time()

        # Use UI optimizer to track performance
        def populate_operation():
            # Clear existing virtual list if it exists
            if hasattr(self, 'virtual_list') and self.virtual_list:
                self.virtual_list.destroy()

            # Get the list container
            scrollable_parent = getattr(self, "_drawer_list_host", None)
            if not scrollable_parent:
                return

            # Clear any residual children (canvas-based list, empty state, etc.)
            try:
                for child in scrollable_parent.winfo_children():
                    child.destroy()
            except Exception:
                pass

            # Prepare optimized items
            self.optimized_items = self._prepare_optimized_items(filter_text)

            if not self.optimized_items:
                # Show empty state
                empty_label = tk.Label(
                    scrollable_parent,
                    text="No prompts found matching your search.",
                    font=self.ui_font(12),
                    fg=self.settings["theme"].get("muted_text", "#a0aec0"),
                    bg=self.settings["theme"].get("background", "#1a1a1a")
                )
                empty_label.pack(expand=True)
                return

            # Create virtual scrolling list
            self.virtual_list = VirtualScrolledList(
                scrollable_parent,
                item_height=42,  # Based on our widget heights
                buffer_size=5
            )

            # Set render callback
            self.virtual_list.set_render_callback(self._create_virtual_item_widget)

            # Set item click callback
            self.virtual_list.set_item_click_callback(self._on_virtual_item_click)

            # Set items
            self.virtual_list.set_items(self.optimized_items)

            # Pack the virtual list
            self.virtual_list.pack(fill="both", expand=True)

            # Update stats
            self._update_stats_optimized(filter_text)

        # Execute with performance tracking
        self.ui_optimizer.optimize_render_operation(populate_operation, widget_count=len(self.optimized_items) if hasattr(self, 'optimized_items') else 0)

        # Track performance
        populate_time = time.time() - start_time
        self.last_populate_time = populate_time
        self.populate_count += 1

        try:
            self.logger.debug(
                "Optimized populate completed in %.3fs (%s calls)",
                populate_time,
                self.populate_count,
            )
        except Exception:
            pass

    def _on_virtual_item_click(self, item):
        """Handle clicks on virtual list items"""
        if item['type'] == 'prompt':
            self.copy_prompt(item['prompt'], item.get('category_path'))
        elif item['type'] == 'category':
            self._toggle_virtual_category(item)

    def _update_stats_optimized(self, filter_text: str):
        """Update statistics with optimized performance"""
        try:
            if not hasattr(self, "stats_label"):
                return

            # Count items efficiently
            total_prompts = sum(1 for item in self.optimized_items if item['type'] == 'prompt')
            total_categories = sum(1 for item in self.optimized_items if item['type'] == 'category')

            if filter_text:
                text = f"{total_prompts} results in {total_categories} categories"
            else:
                text = f"{total_prompts} prompts across {total_categories} categories"

            self.stats_label.configure(text=text)
        except Exception:
            pass

    def _debounced_populate_prompts(self):
        """Debounced version of populate_prompts to prevent excessive updates"""
        filter_text = self.search_var.get().strip() if hasattr(self, 'search_var') else ""

        # Use UI optimizer's debouncer
        try:
            if getattr(self, "use_virtual_scrolling", False) and hasattr(self, "ui_optimizer"):
                self.ui_optimizer.debounce_filter(
                    lambda ft, data: self.populate_prompts_optimized(ft),
                    filter_text,
                    None
                )
            else:
                self.populate_prompts_original(filter_text)
        except Exception:
            self.populate_prompts_original(filter_text)

    def populate_prompts(self, filter_text=""):
        """Populate the drawer with prompt categories and items in hierarchical tree structure"""
        # Use optimized version if available
        if getattr(self, "use_virtual_scrolling", False) and VIRTUAL_SCROLLING_AVAILABLE and hasattr(self, 'ui_optimizer'):
            result = self.populate_prompts_optimized(filter_text)
        else:
            # Fallback to original implementation
            result = self.populate_prompts_original(filter_text)

        # Auto-fit drawer height to content
        try:
            if (
                getattr(self, "drawer", None)
                and not getattr(self, "_drawer_initializing", False)
                and self.drawer.winfo_exists()
            ):
                self.drawer.after(50, self._resize_drawer_to_content)
        except Exception:
            pass

        return result

    def populate_prompts_original(self, filter_text=""):
        # Safety check: ensure scrollable_frame exists and is valid
        if not hasattr(self, 'scrollable_frame') or not self.scrollable_frame.winfo_exists():
            return
        
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Initialize collapse state once (session rules may set this before first render)
        if not hasattr(self, '_initialized_collapse_state'):
            try:
                if not self.collapsed_categories:
                    self.collapsed_categories = self._all_prompt_matrix_category_keys()
            except Exception:
                self.collapsed_categories = set()
            self._initialized_collapse_state = True
        
        # Reset keyboard navigation list
        self._nav_widgets = []
        self._nav_index = 0

        # Optional pinned Favorites section at top
        try:
            if not filter_text.strip() and self.settings.get("favorites"):
                fav_prompts = []
                for fid in self.settings.get("favorites", [])[:20]:
                    cat_path, idx, p = self._find_prompt_by_id(fid)
                    if p:
                        fav_prompts.append(p)
                if fav_prompts:
                    fake_cat = {"prompts": fav_prompts}
                    self._render_category("⭐ Favorites", fake_cat, filter_text, level=0, path_prefix="__favorites__")
        except Exception:
            pass

        # Render each top-level category
        for category_name, category_data in self.prompts["categories"].items():
            if self._category_matches_filter(category_name, category_data, filter_text):
                self._render_category(category_name, category_data, filter_text, level=0)

    def update_stats(self):
        """Update the stats label with simple counts of visible prompts/categories"""
        try:
            if not hasattr(self, "stats_label") or not hasattr(self, "search_var"):
                return
            filter_text = self.search_var.get().strip() if self.search_var else ""

            def count_prompts_in(category_data):
                total = 0
                # Count direct prompts
                if "prompts" in category_data:
                    for p in category_data["prompts"]:
                        if self._prompt_matches_filter(p, filter_text):
                            total += 1
                # Recurse into subcategories
                if "subcategories" in category_data:
                    for sub_data in category_data["subcategories"].values():
                        total += count_prompts_in(sub_data)
                return total

            total_prompts = 0
            matching_categories = 0
            for cat_name, cat_data in self.prompts.get("categories", {}).items():
                if self._category_matches_filter(cat_name, cat_data, filter_text):
                    matching_categories += 1
                    total_prompts += count_prompts_in(cat_data)

            if filter_text:
                text = f"{total_prompts} results in {matching_categories} categories"
            else:
                text = f"{total_prompts} prompts across {matching_categories} categories"
            self.stats_label.configure(text=text)
        except Exception:
            try:
                self.stats_label.configure(text="")
            except Exception:
                pass
    
    def _text_matches(self, hay, needle):
        if not needle:
            return True
        hay_l = hay.lower(); needle_l = needle.lower()
        if hay_l.find(needle_l) != -1:
            return True
        if self.settings.get("search_fuzzy", True):
            try:
                from difflib import SequenceMatcher
                ratio = SequenceMatcher(None, hay_l, needle_l).ratio()
                return ratio >= 0.6
            except Exception:
                return False
        return False

    def _category_matches_filter(self, category_name, category_data, filter_text):
        """Check if a category or any of its contents match the filter"""
        if not filter_text:
            return True
            
        # Check category name
        if self._text_matches(category_name, filter_text):
            return True
            
        # Check direct prompts
        if "prompts" in category_data:
            for prompt in category_data["prompts"]:
                blob = self._get_prompt_search_blob(prompt)
                if self._text_matches(blob, filter_text):
                    return True
        
        # Check subcategories recursively
        if "subcategories" in category_data:
            for sub_name, sub_data in category_data["subcategories"].items():
                if self._category_matches_filter(sub_name, sub_data, filter_text):
                    return True
                    
        return False
    
    def _render_category(self, category_name, category_data, filter_text, level=0, path_prefix=""):
        """Render a category and its contents recursively - compact styling"""
        real_path = f"{path_prefix}/{category_name}" if path_prefix else category_name
        category_path = f"{category_name}_level_{level}"
        is_collapsed = category_path in self.collapsed_categories

        base_bg = self.settings["theme"].get("background", "#0f0f23")
        accent = self.settings["theme"].get("accent", base_bg)
        highlight = self.settings["theme"].get("highlight", accent)
        border = self.settings["theme"].get("border", "#3a3a3a")
        card_bg = self._blend_colors(base_bg, accent, 0.22)
        card_bg = self._blend_colors(card_bg, highlight, 0.04)
        card_edge = self._blend_colors(border, highlight, 0.38)
        cat_fg = self._text_on(
            card_bg,
            self.settings["theme"].get("category_text", self.settings["theme"].get("foreground", "#ffffff"))
        )

        # Futuristic category header
        cat_color = category_data.get("color") or self.settings["theme"].get("category_bar", "#222222")
        cat_frame = tk.Frame(self.scrollable_frame, bg=card_bg, relief="flat",
                             highlightbackground=card_edge, highlightthickness=1)
        cat_frame.pack(fill="x", pady=2, padx=6)

        cat_container = tk.Frame(cat_frame, bg=card_bg)
        cat_container.pack(fill="x", padx=6, pady=3)

        strip = tk.Frame(cat_container, bg=cat_color, width=3)
        strip.pack(side="left", fill="y", padx=(0, 6))

        # Collapse/expand icon and category name
        expand_icon = "▸" if is_collapsed else "▾"
        cat_label = tk.Label(
            cat_container,
            text=f"{expand_icon} {category_name}",
            font=self.ui_font(10, self.title_weight()),
            bg=card_bg,
            fg=cat_fg,
            anchor="w",
            cursor="hand2",
            padx=4 + (level * 6),
            pady=2
        )
        cat_label.pack(side="left", fill="x", expand=True)
        cat_label.bind("<Button-1>", lambda e: self._toggle_category(category_path, cat_label))

        hover_color = self._blend_colors(card_bg, highlight, 0.2)
        cat_label.bind("<Enter>", lambda e: self._animate_color(cat_label, card_bg, hover_color))
        cat_label.bind("<Leave>", lambda e: self._animate_color(cat_label, cat_label.cget("bg"), card_bg))
        cat_frame.bind("<Enter>", lambda e: self._animate_color(cat_frame, card_bg, hover_color))
        cat_frame.bind("<Leave>", lambda e: self._animate_color(cat_frame, cat_frame.cget("bg"), card_bg))
        
        # Only show contents if not collapsed
        if not is_collapsed:
            # Render direct prompts in this category
            if "prompts" in category_data:
                for prompt in category_data["prompts"]:
                    if self._prompt_matches_filter(prompt, filter_text):
                        self._render_prompt(prompt, filter_text, level + 1, real_path)
            
            # Render subcategories
            if "subcategories" in category_data:
                for sub_name, sub_data in category_data["subcategories"].items():
                    if self._category_matches_filter(sub_name, sub_data, filter_text):
                        self._render_category(sub_name, sub_data, filter_text, level + 1, real_path)
    
    def _prompt_matches_filter(self, prompt, filter_text):
        """Check if a prompt matches the filter"""
        if not filter_text:
            return True
        blob = self._get_prompt_search_blob(prompt)
        return self._text_matches(blob, filter_text)
    
    def _render_prompt(self, prompt, filter_text, level, category_path):
        """Render a single prompt with compact styling"""
        base_bg = self.settings["theme"].get("background", "#1a1a1a")
        accent = self.settings["theme"].get("accent", base_bg)
        highlight = self.settings["theme"].get("highlight", accent)
        border = self.settings["theme"].get("border", "#3a3a3a")
        row_bg = self._blend_colors(base_bg, accent, 0.16)
        row_edge = self._blend_colors(border, highlight, 0.32)
        row_hover = self._blend_colors(row_bg, highlight, 0.2)
        button_bg = self.settings["theme"].get("button_bg", accent)
        button_bg = self._blend_colors(button_bg, accent, 0.16)
        button_fg = self._text_on(button_bg, self.settings["theme"].get("foreground", "#ffffff"))

        indent_pad = 6 + (level * 6)

        # Prompt container
        prompt_frame = tk.Frame(self.scrollable_frame, bg=row_bg, relief="flat",
                                highlightbackground=row_edge, highlightthickness=1)
        prompt_frame.pack(fill="x", pady=1, padx=6)

        prompt_container = tk.Frame(prompt_frame, bg=button_bg, relief="flat", bd=0)
        prompt_container.pack(fill="x", padx=1, pady=1)

        accent_strip = tk.Frame(prompt_container, bg=highlight, width=3)
        accent_strip.pack(side="left", fill="y", padx=(0, 4))

        # Prompt button with compact styling
        star = "★ " if self._is_favorite(prompt) else ""
        title_text = prompt.get('title', '')
        display_text = f"{star}{title_text}"
        prompt_btn = tk.Label(
            prompt_container,
            text=display_text,
            font=self.ui_font(9, self.title_weight()),
            bg=button_bg,
            fg=button_fg,
            anchor="w",
            cursor="hand2",
            padx=indent_pad,
            pady=3,
            takefocus=1
        )
        prompt_btn.pack(fill="x")
        prompt_btn.bind("<Button-1>", lambda e, p=prompt, cp=category_path: self.copy_prompt(p, cp))
        
        # Attach tooltip showing prompt preview
        prompt_text = prompt.get('prompt', '')
        if prompt_text:
            self._attach_tooltip(prompt_btn, prompt_text, delay=350)

        # Enhanced hover effects using theme + subtle animation
        def on_enter(event):
            self._animate_color(prompt_frame, prompt_frame.cget("bg"), row_hover)
            self._animate_color(prompt_container, prompt_container.cget("bg"), row_hover)
            self._animate_color(prompt_btn, prompt_btn.cget("bg"), row_hover)

        def on_leave(event):
            self._animate_color(prompt_frame, prompt_frame.cget("bg"), row_bg)
            self._animate_color(prompt_container, prompt_container.cget("bg"), button_bg)
            self._animate_color(prompt_btn, prompt_btn.cget("bg"), button_bg)

        prompt_btn.bind("<Enter>", on_enter, add="+")
        prompt_btn.bind("<Leave>", on_leave, add="+")
        # Keyboard navigation hooks
        if not hasattr(self, "_nav_widgets"):
            self._nav_widgets = []
        self._nav_widgets.append(prompt_btn)
        def on_activate(event=None, p=prompt, cp=category_path):
            self.copy_prompt(p, cp)
        prompt_btn.bind("<Return>", on_activate)
        
        # Optional search highlighting of query in title
        try:
            q = (filter_text or "").strip()
            if q and self.settings.get("search_highlight", True):
                # naive case-insensitive highlight in label text
                text_val = prompt_btn.cget("text")
                start = text_val.lower().find(q.lower())
                if start != -1:
                    end = start + len(q)
                    # Split into three labels for colored highlight (compact)
                    prompt_btn.pack_forget()
                    row = tk.Frame(prompt_container, bg=button_bg, padx=4, pady=2)
                    row.pack(fill="x")
                    pre = tk.Label(row, text=text_val[:start], font=self.ui_font(9),
                                   bg=button_bg, fg=button_fg, anchor="w")
                    hit_bg = self.settings["theme"].get("highlight", self._lighten_color(self.settings["theme"].get("accent", "#333333"), 0.35))
                    hit_fg = self._text_on(hit_bg, self.settings["theme"].get("highlight_text", button_fg))
                    hit = tk.Label(row, text=text_val[start:end], font=self.ui_font(9, "bold"),
                                   bg=hit_bg,
                                   fg=hit_fg)
                    post = tk.Label(row, text=text_val[end:], font=self.ui_font(9),
                                    bg=button_bg, fg=button_fg)
                    for w in (pre, hit, post):
                        w.pack(side="left", anchor="w")
                        w.bind("<Button-1>", lambda e, p=prompt, cp=category_path: self.copy_prompt(p, cp))
                    # Re-attach hover and focus to row
                    def on_enter_row(event):
                        hover_bg = self.settings["theme"].get("button_hover", button_bg)
                        row.configure(bg=hover_bg)
                        prompt_container.configure(bg=hover_bg)
                        prompt_frame.configure(bg=row_hover)
                    def on_leave_row(event):
                        row.configure(bg=button_bg)
                        prompt_container.configure(bg=button_bg)
                        prompt_frame.configure(bg=row_bg)
                    row.bind("<Enter>", on_enter_row); row.bind("<Leave>", on_leave_row)
                    # Focus ring support by proxy
                    row.bind("<Return>", lambda e, p=prompt, cp=category_path: self.copy_prompt(p, cp))
        except Exception:
            pass

        # Add right-click context menu for individual prompts
        def show_prompt_context_menu(event):
            prompt_menu = tk.Menu(self.root, tearoff=0, bg=button_bg, fg=button_fg) 
            prompt_menu.add_command(label="📋 Copy", command=lambda: self.copy_prompt(prompt, category_path))
            prompt_menu.add_command(label="✏️ Edit", command=lambda: self.edit_prompt(prompt))
            prompt_menu.add_command(label="👁️ Preview", command=lambda: self.preview_prompt(prompt))
            fav_label = "⭐ Unfavorite" if self._is_favorite(prompt) else "⭐ Favorite"
            prompt_menu.add_command(label=fav_label, command=lambda: self._toggle_favorite(prompt))
            
            try:
                prompt_menu.tk_popup(event.x_root, event.y_root)
            finally:
                prompt_menu.grab_release()
                
        prompt_btn.bind("<Button-3>", show_prompt_context_menu)
    
    def _toggle_category(self, category_path, label_widget):
        """Toggle collapse/expand state of a category"""
        if category_path in self.collapsed_categories:
            self.collapsed_categories.remove(category_path)
        else:
            self.collapsed_categories.add(category_path)
        # Persist collapse state
        try:
            self.save_settings()
        except Exception:
            pass
        
        # Refresh the display
        self.populate_prompts()
                
    def filter_prompts(self, event=None):
        """Filter prompts based on search text using optimized search service"""
        filter_text = self.search_var.get()

        # If no search text, use the original method
        if not filter_text.strip():
            self.populate_prompts("")
            self.update_stats()
            return

        # For virtual scrolling, use the unified populate path to avoid mixed renderers
        if getattr(self, "use_virtual_scrolling", False):
            self.populate_prompts(filter_text)
            self.update_stats()
            return

        # Expand all categories when filtering to show results
        self.collapsed_categories.clear()

        # Use the new search service for better performance
        def on_search_results(results, stats):
            """Callback for search results"""
            if stats and stats.search_time_ms > 100:
                self.logger.debug(f"Search took {stats.search_time_ms:.2f}ms for {stats.matching_prompts} results")

            # Record search analytics
            try:
                results_count = len(results) if results else 0
                self.analytics_service.record_search(filter_text, results_count)
            except Exception as e:
                self.logger.warning(f"Failed to record search analytics: {e}")

            # Convert search results to the format expected by populate_prompts
            self._populate_with_search_results(results, filter_text)
            self.update_stats()

        try:
            self.search_service.search(filter_text, on_search_results)
        except Exception as e:
            # Fallback to original method if search service fails
            self.logger.warning(f"Search service failed, falling back: {e}")
            self.populate_prompts(filter_text)
            self.update_stats()

    def _populate_with_search_results(self, search_results, filter_text):
        """Populate UI with search results from SearchService"""
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not search_results:
            # Show no results message
            try:
                empty_label = tk.Label(
                    self.scrollable_frame,
                    text="No prompts found matching your search.",
                    font=self.ui_font(12),
                    fg=self.settings["theme"].get("muted_text", "#a0aec0"),
                    bg=self.settings["theme"].get("background", "#1a1a1a")
                )
                empty_label.pack(expand=True)
            except Exception:
                pass
            return

        # Group results by category path
        categories = {}
        for result in search_results:
            category_path = result.category_path
            if category_path not in categories:
                categories[category_path] = []
            categories[category_path].append(result)

        base_bg = self.settings["theme"].get("background", "#0f0f23")
        accent = self.settings["theme"].get("accent", base_bg)
        highlight = self.settings["theme"].get("highlight", accent)
        border = self.settings["theme"].get("border", "#3a3a3a")
        card_bg = self._blend_colors(base_bg, accent, 0.18)
        card_edge = self._blend_colors(border, highlight, 0.3)

        # Render categories with search results
        for category_path, results in categories.items():
            # Render category header
            category_parts = category_path.split('/')
            category_name = category_parts[-1] if category_parts else "Uncategorized"

            category_frame = tk.Frame(self.scrollable_frame, bg=card_bg,
                                      highlightbackground=card_edge, highlightthickness=1)
            category_frame.pack(fill="x", pady=(8, 4), padx=8)

            strip = tk.Frame(category_frame, bg=self.settings["theme"].get("category_bar", accent), width=4)
            strip.pack(side="left", fill="y", padx=(0, 6))

            # Category label
            try:
                category_label = tk.Label(
                    category_frame,
                    text=f"📁 {category_name}",
                    font=self.ui_font(11, "bold"),
                    fg=cat_fg,
                    bg=card_bg,
                    anchor="w",
                    padx=6,
                    pady=4
                )
                category_label.pack(fill="x")
            except Exception:
                pass

            # Render search results in this category
            for result in results:
                self._render_search_result(result.prompt, filter_text, 1, category_path)

    def _render_search_result(self, prompt, filter_text, level, category_path):
        """Render a single search result with highlighting"""
        indent = "  " * level

        base_bg = self.settings["theme"].get("background", "#1a1a1a")
        accent = self.settings["theme"].get("accent", base_bg)
        highlight = self.settings["theme"].get("highlight", accent)
        border = self.settings["theme"].get("border", "#3a3a3a")
        row_bg = self._blend_colors(base_bg, accent, 0.14)
        row_edge = self._blend_colors(border, highlight, 0.25)
        row_hover = self._blend_colors(row_bg, highlight, 0.18)

        # Modern prompt container
        prompt_frame = tk.Frame(self.scrollable_frame, bg=row_bg, relief="flat",
                                highlightbackground=row_edge, highlightthickness=1)
        prompt_frame.pack(fill="x", pady=2, padx=8)

        # Prompt content container
        content_frame = tk.Frame(prompt_frame, bg=self.settings["theme"].get("button_bg", accent))
        content_frame.pack(fill="x", padx=2, pady=2)

        accent_strip = tk.Frame(content_frame, bg=highlight, width=3)
        accent_strip.pack(side="left", fill="y", padx=(0, 6))

        # Prompt button with highlighting
        try:
            title = prompt.get('title', 'Untitled')
            # Apply search highlighting if available
            display_title = title
            if filter_text and self.settings.get("search_highlight", True):
                try:
                    q = (filter_text or "").strip()
                    if q and q.lower() in title.lower():
                        # Simple highlighting by wrapping in brackets
                        start = title.lower().find(q.lower())
                        if start != -1:
                            end = start + len(q)
                            display_title = f"{title[:start]}[{title[start:end]}]{title[end:]}"
                except Exception:
                    pass

            prompt_btn = tk.Button(
                content_frame,
                text=f"{indent}📄 {display_title}",
                font=self.ui_font(10),
                fg=self._text_on(self.settings["theme"].get("button_bg", "#16213e"), self.settings["theme"].get("foreground", "#ffffff")),
                bg=self.settings["theme"].get("button_bg", "#16213e"),
                activebackground=row_hover,
                activeforeground=self._text_on(self.settings["theme"].get("button_bg", "#16213e"), self.settings["theme"].get("foreground", "#ffffff")),
                relief="flat",
                anchor="w",
                cursor="hand2",
                command=lambda p=prompt, cp=category_path: self.copy_prompt(p, cp)
            )
            prompt_btn.pack(fill="x", pady=1, padx=6)
            prompt_btn.bind("<Enter>", lambda e: self._animate_color(prompt_btn, prompt_btn.cget("bg"), row_hover))
            prompt_btn.bind("<Leave>", lambda e: self._animate_color(prompt_btn, prompt_btn.cget("bg"),
                                                                     self.settings["theme"].get("button_bg", "#16213e")))

            # Bind keyboard navigation
            def on_activate(event, p=prompt, cp=category_path):
                self.copy_prompt(p, cp)
            prompt_btn.bind("<Return>", on_activate)
        except Exception:
            pass

    def _focus_search(self):
        try:
            if not self.expanded:
                self.show_drawer()
            if hasattr(self, "_search_entry_widget") and self._search_entry_widget:
                self._search_entry_widget.focus_set()
                self._search_entry_widget.select_range(0, tk.END)
        except Exception:
            pass

    def _nav_up(self, event=None):
        try:
            if not hasattr(self, "_nav_widgets") or not self._nav_widgets:
                return
            idx = getattr(self, "_nav_index", 0)
            idx = max(0, idx - 1)
            self._nav_index = idx
            self._nav_widgets[idx].focus_set()
        except Exception:
            pass

    def _nav_down(self, event=None):
        try:
            if not hasattr(self, "_nav_widgets") or not self._nav_widgets:
                return
            idx = getattr(self, "_nav_index", -1)
            idx = min(len(self._nav_widgets) - 1, idx + 1)
            self._nav_index = idx
            self._nav_widgets[idx].focus_set()
        except Exception:
            pass

    def _nav_enter(self, event=None):
        try:
            if hasattr(self, "_nav_widgets") and self._nav_widgets and hasattr(self, "_nav_index"):
                w = self._nav_widgets[self._nav_index]
                w.event_generate("<Button-1>")
        except Exception:
            pass
        
    def copy_prompt(self, prompt, category_path=None):
        """Copy prompt to clipboard"""
        text = ""
        text_filled = None
        try:
            text = prompt.get("prompt", "")
            # Handle {placeholders}
            text_filled = self._fill_placeholders(text)
            if text_filled is None:
                return
            copied = False
            if hasattr(self, "clipboard_service") and self.clipboard_service:
                copied = bool(self.clipboard_service.copy_to_clipboard(text_filled, show_confirmation=False))
            elif CLIPBOARD_AVAILABLE:
                pyperclip.copy(text_filled)
                copied = True

            if not copied:
                self.show_notification("Clipboard unavailable")
                return
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to copy prompt: {e}")
            return

        # Session memory for matrix expansion state
        try:
            resolved_path = category_path or self._resolve_prompt_category_path(prompt)
            if isinstance(resolved_path, str) and resolved_path.strip():
                self._last_copied_category_path = resolved_path.strip()
        except Exception:
            pass

        # Best-effort extras: never block copying on analytics/service issues
        try:
            self._register_recent(prompt)
        except Exception:
            pass

        # Track usage with enhanced services (avoid relative imports; this file is not a package)
        try:
            if hasattr(self, 'prompt_service'):
                try:
                    from src.types.PromptTypes import Prompt as PromptModel  # type: ignore
                except Exception:
                    PromptModel = None

                if PromptModel is not None:
                    prompt_obj = PromptModel(
                        id=prompt.get("id", ""),
                        title=prompt.get("title", ""),
                        prompt=text,
                        category=prompt.get("category", "Unknown"),
                        tags=prompt.get("tags", []),
                        usage_count=prompt.get("usage_count", 0)
                    )
                    self.prompt_service.use_prompt(prompt_obj, text_filled)
        except Exception:
            pass

        try:
            if hasattr(self, 'analytics_service'):
                self.analytics_service.record_prompt_usage({
                    "id": prompt.get("id", ""),
                    "title": prompt.get("title", ""),
                    "category": prompt.get("category", "Unknown"),
                    "tags": prompt.get("tags", []),
                    "prompt": text
                })
                self.analytics_service.record_copy()
        except Exception:
            pass

        try:
            self.show_notification(f"Copied: {prompt.get('title', 'Prompt')}")
        except Exception:
            pass
        try:
            self._auto_paste_if_enabled()
        except Exception:
            pass
        
        # Spring-loaded behavior: auto-hide drawer after copy with short delay
        # (only if spring_loaded_close setting is enabled)
        try:
            if self.settings.get("spring_loaded_close", True):
                if getattr(self, "drawer", None) and self.expanded:
                    self.root.after(200, self.hide_drawer)
        except Exception:
            pass
            
    def show_notification(self, message):
        """Show a modern notification popup"""
        notification = tk.Toplevel(self.root)
        notification.title("")
        notification.configure(bg=self.settings["theme"]["background"]) 
        notification.overrideredirect(True)
        notification.attributes("-topmost", True)
        notification.attributes("-alpha", min(1.0, float(self.settings.get("opacity", 0.95))))
        
        # Position to the right of the launcher bar so it never covers controls.
        try:
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_w = max(1, self.root.winfo_width())
            screen_w = max(1, self.root.winfo_screenwidth())
            screen_h = max(1, self.root.winfo_screenheight())
            x = root_x + root_w + 14
            y = max(0, root_y + 4)
            x = max(0, min(x, screen_w - 220))
            y = max(0, min(y, screen_h - 80))
        except Exception:
            x, y = 80, 40
        
        # Create modern notification frame
        notif_bg = self.settings["theme"].get("accent", self.settings["theme"].get("background", "#1a1a1a"))
        notif_fg = self._text_on(notif_bg, self.settings["theme"].get("foreground", "#ffffff"))
        notif_frame = tk.Frame(notification, bg=notif_bg, relief="flat", bd=1, highlightthickness=1, highlightbackground=self.settings["theme"].get("border", "#444444")) 
        notif_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Icon and message
        content_frame = tk.Frame(notif_frame, bg=notif_bg) 
        content_frame.pack(fill="both", expand=True, padx=7, pady=5)
        
        # Success icon
        icon_label = tk.Label(content_frame, text="✓", font=self.ui_font(10, "bold"), 
                             bg=notif_bg, fg="#4CAF50") 
        icon_label.pack(side="left", padx=(0, 5))
        
        # Message text
        message_label = tk.Label(content_frame, text=message, bg=notif_bg,
            fg=notif_fg, font=self.ui_font(8), wraplength=135, justify="left") 
        message_label.pack(side="left", fill="both", expand=True)
        
        # Auto-size the notification
        notification.update_idletasks()
        width = max(120, min(notif_frame.winfo_reqwidth(), 190))
        height = max(28, min(notif_frame.winfo_reqheight(), 56))
        notification.geometry(f"{width}x{height}+{x}+{y}")
        
        # Fade in effect (simple version)
        notification.attributes("-alpha", 0.0)
        notification.after(50, lambda: notification.attributes("-alpha", 0.3))
        notification.after(100, lambda: notification.attributes("-alpha", 0.6))
        notification.after(150, lambda: notification.attributes("-alpha", 0.95))
        
        # Auto-close with fade out
        def fade_out():
            notification.after(50, lambda: notification.attributes("-alpha", 0.6))
            notification.after(100, lambda: notification.attributes("-alpha", 0.3))
            notification.after(150, lambda: notification.attributes("-alpha", 0.0))
            notification.after(200, notification.destroy)
            
        notification.after(1800, fade_out)
        
        # Allow click to close
        def close_notification(event):
            notification.destroy()
            
        notification.bind("<Button-1>", close_notification)
        notif_frame.bind("<Button-1>", close_notification)
        icon_label.bind("<Button-1>", close_notification)
        message_label.bind("<Button-1>", close_notification)
        
    def hide_drawer(self):
        """Hide the expanded drawer with smooth fade-out animation"""
        if not self.drawer:
            self.expanded = False
            return
        
        # Remove the click-outside handler
        try:
            self.root.unbind_all("<Button-1>")
        except Exception:
            pass
        
        # Cancel any running drawer animation
        if hasattr(self, '_drawer_animator') and self._drawer_animator:
            try:
                self._drawer_animator.stop()
            except Exception:
                pass
        
        drawer_to_hide = self.drawer
        self.expanded = False
        
        # Animate fade-out if modern UI is available
        if MODERN_UI_AVAILABLE and AnimationController is not None:
            try:
                animator = AnimationController(drawer_to_hide, duration_ms=120, fps=60)
                animator.animate_alpha(
                    start=1.0,
                    end=0.0,
                    easing=Easing.ease_out_cubic,
                    on_complete=lambda: self._safe_withdraw_drawer(drawer_to_hide)
                )
                return
            except Exception:
                pass
        
        # Fallback: quick fade-out
        try:
            def fade_out_step(step):
                if step >= 6:
                    self._safe_withdraw_drawer(drawer_to_hide)
                    return
                try:
                    if drawer_to_hide.winfo_exists():
                        alpha = 1.0 - (step / 6)
                        drawer_to_hide.attributes("-alpha", max(0, alpha))
                        self.root.after(20, lambda: fade_out_step(step + 1))
                except Exception:
                    self._safe_withdraw_drawer(drawer_to_hide)
            
            fade_out_step(1)
        except Exception:
            self._safe_withdraw_drawer(drawer_to_hide)

    def _safe_withdraw_drawer(self, drawer):
        """Safely hide a drawer window without destroying it."""
        try:
            if drawer and drawer.winfo_exists():
                drawer.attributes("-alpha", 1.0)
                drawer.withdraw()
        except Exception:
            pass

    def _safe_destroy_drawer(self, drawer):
        """Safely destroy a drawer window."""
        try:
            if drawer and drawer.winfo_exists():
                drawer.destroy()
        except Exception:
            pass
        
    def on_drawer_focus_out(self, event):
        """Handle drawer losing focus"""
        # Don't hide if focus went to a child widget
        if event.widget == self.drawer:
            self.root.after(100, self.check_focus_and_hide)
            
    def check_focus_and_hide(self):
        """Check focus and hide drawer if appropriate"""
        try:
            focused = self.root.focus_get()
            if focused is None or focused.winfo_toplevel() != self.drawer:
                self.hide_drawer()
        except:
            self.hide_drawer()
            
    def show_context_menu(self, event):
        """Show right-click context menu"""
        bg_color = self.settings["theme"]["background"]
        fg_color = self._text_on(bg_color, self.settings["theme"].get("foreground", "#ffffff"))
        
        menu = tk.Menu(self.root, tearoff=0, bg=bg_color, fg=fg_color)
        # Show accelerators so users discover shortcuts
        menu.add_command(label="📝 Edit Prompts", command=self.open_prompt_editor, accelerator="Ctrl+E")
        menu.add_command(label="⚙️ Settings", command=self.open_settings, accelerator="Ctrl+,")
        menu.add_command(label="👤 Profiles", command=self.open_profile_manager, accelerator="Ctrl+Shift+P")
        menu.add_separator()
        menu.add_command(label="🎯 Template Manager", command=self.open_template_manager, accelerator="Ctrl+T")
        menu.add_command(label="📊 Analytics Dashboard", command=self.open_analytics_dashboard, accelerator="Ctrl+A")
        menu.add_separator()
        menu.add_command(label="📁 Open Prompts Folder", command=self.open_prompts_folder, accelerator="Ctrl+O")
        menu.add_command(label="🔄 Reload Prompts", command=self.reload_prompts, accelerator="Ctrl+R")
        menu.add_separator()
        menu.add_command(label="⬇ Export JSON", command=self.export_prompts)
        menu.add_command(label="⬆ Import JSON", command=self.import_prompts)
        menu.add_command(label="🕒 Backup Now", command=self.backup_prompts)
        menu.add_separator()
        
        # Auto-start toggle
        if self.is_autostart_enabled():
            menu.add_command(label="🚫 Disable Auto-Start", command=self.disable_autostart)
        else:
            menu.add_command(label="🚀 Enable Auto-Start", command=self.enable_autostart)
        
        # Support link (non-invasive, if configured)
        coffee_url = self.get_coffee_url()
        if coffee_url:
            menu.add_separator()
            menu.add_command(label="💰 Buy Me a Coffee", command=self.open_coffee_url)

        menu.add_separator()
        menu.add_command(label="📘 User Guide", command=self.show_help_about, accelerator="F1")
        menu.add_separator()
        menu.add_command(label="❌ Exit", command=self.exit_app, accelerator="Ctrl+Q")
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _apply_global_ttk_style(self):
        """Apply compact, modern styles to ttk widgets (scrollbars, etc.)."""
        style = ttk.Style()
        try:
            # Stable, themeable base
            style.theme_use("clam")
        except Exception:
            pass
        try:
            accent = self.settings["theme"].get("accent", "#333333")
            bg = self.settings["theme"].get("background", "#1a1a1a")
            border = self.settings["theme"].get("border", "#444444")
            fg = self.settings["theme"].get("foreground", "#dddddd")
            highlight = self.settings["theme"].get("highlight", accent)
            highlight_text = self.settings["theme"].get("highlight_text", fg)
            field_bg = self._blend_colors(bg, accent, 0.22)
            scroll_bg = self._blend_colors(accent, highlight, 0.2)
            scroll_hover = self._blend_colors(scroll_bg, highlight, 0.3)
            for s in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
                style.configure(
                    s,
                    background=scroll_bg,
                    troughcolor=bg,
                    bordercolor=border,
                    arrowcolor=fg,
                    darkcolor=scroll_bg,
                    lightcolor=scroll_bg,
                    gripcount=0,
                    width=8
                )
                style.map(
                    s,
                    background=[("active", scroll_hover), ("pressed", highlight)],
                )
            style.configure(
                "Promptoire.TCombobox",
                fieldbackground=field_bg,
                background=bg,
                foreground=fg,
                arrowcolor=fg,
                bordercolor=border
            )
            style.map(
                "Promptoire.TCombobox",
                fieldbackground=[("readonly", field_bg)],
                foreground=[("readonly", fg)],
                background=[("readonly", bg)]
            )
            style.configure(
                "Promptoire.TScale",
                background=bg,
                troughcolor=self.settings["theme"].get("slider_trough", "#3a3a3a")
            )
            style.configure("Promptoire.TCheckbutton", background=bg, foreground=fg)
            style.configure("Promptoire.TRadiobutton", background=bg, foreground=fg)
            style.configure("Promptoire.TNotebook", background=bg, borderwidth=0)
            style.configure("Promptoire.TNotebook.Tab", background=accent, foreground=fg, padding=(10, 4))
            style.map(
                "Promptoire.TNotebook.Tab",
                background=[("selected", highlight)],
                foreground=[("selected", highlight_text)]
            )
        except Exception:
            pass

    def _center_window(self, child, parent):
        """Center a toplevel window over its parent window."""
        try:
            parent.update_idletasks()
            child.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            cw = child.winfo_reqwidth()
            ch = child.winfo_reqheight()
            x = px + max(0, (pw - cw) // 2)
            y = py + max(0, (ph - ch) // 2)
            child.geometry(f"+{x}+{y}")
        except Exception:
            try:
                child.geometry("+200+200")
            except Exception:
                pass

    def _ask_string_modal(self, parent, title, prompt_label, initial_value=""):
        """Open a compact, styled, topmost modal dialog prompting for a single string.

        Returns the entered string, or None if cancelled.
        """
        dlg = tk.Toplevel(parent)
        try:
            self._apply_window_icon(dlg)
        except Exception:
            pass
        try:
            dlg.transient(parent)
        except Exception:
            pass
        try:
            dlg.attributes("-topmost", True)
        except Exception:
            pass
        dlg.title(title)
        bg = self.settings["theme"].get("background", "#1a1a1a")
        fg = self.settings["theme"].get("foreground", "#ffffff")
        accent = self.settings["theme"].get("accent", "#333333")
        border = self.settings["theme"].get("border", "#444444")
        try:
            dlg.configure(bg=bg, highlightbackground=border, highlightthickness=1)
        except Exception:
            dlg.configure(bg=bg)

        frame = tk.Frame(dlg, bg=bg)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        label = tk.Label(frame, text=prompt_label, bg=bg, fg=fg, font=self.ui_font(10, "bold"))
        label.pack(anchor="w", pady=(0, 6))

        var = tk.StringVar(value=initial_value)
        entry = tk.Entry(frame, textvariable=var, bg=accent, fg=fg, relief="flat", insertbackground=fg)
        entry.pack(fill="x", pady=(0, 10))

        btn_row = tk.Frame(frame, bg=bg)
        btn_row.pack(fill="x")

        result = {"value": None}

        def do_ok(event=None):
            v = var.get().strip()
            if v == "":
                dlg.destroy()
                return
            result["value"] = v
            dlg.destroy()

        def do_cancel(event=None):
            dlg.destroy()

        ok_btn = tk.Button(btn_row, text="OK", command=do_ok, bg="#2563eb", fg="white", relief="flat", width=10, font=self.ui_font(9, "bold"))
        ok_btn.pack(side="right")
        cancel_btn = tk.Button(btn_row, text="Cancel", command=do_cancel, bg=self.settings["theme"]["button_bg"], fg=fg, relief="flat", width=10, font=self.ui_font(9))
        cancel_btn.pack(side="right", padx=(0, 8))

        try:
            dlg.bind("<Return>", do_ok)
            dlg.bind("<Escape>", do_cancel)
            dlg.bind("<Control-w>", do_cancel)
        except Exception:
            pass

        try:
            entry.focus_set()
        except Exception:
            pass

        try:
            dlg.lift()
            dlg.focus_force()
        except Exception:
            pass
        self._center_window(dlg, parent)
        try:
            dlg.grab_set()
        except Exception:
            pass
        dlg.wait_window()
        return result["value"]

    def get_formatter_prompt_text(self):
        """Return the full formatter prompt used for raw-text -> Promptoire JSON conversion."""
        return (
            "PROMPTOIRE - ONE-SHOT FORMATTER (STRICT OUTPUT)\n\n"
            "ROLE\n"
            "You are a data formatter. Convert the raw text I paste into a SINGLE valid JSON object for Promptoire import. Do not invent or rewrite content; only structure and lightly normalize whitespace.\n\n"
            "OUTPUT REQUIREMENTS (NO EXCEPTIONS)\n"
            "- Output EXACTLY one JSON object and nothing else. No markdown fences, no comments, no prose.\n"
            "- Must be valid JSON (double quotes, no trailing commas).\n"
            "- Preserve original text inside fields verbatim (trim leading/trailing whitespace only).\n"
            "- Do NOT hallucinate tags or notes. Include \"tags\" and \"note\" ONLY if provided.\n"
            "- Keep input order for prompts as encountered.\n\n"
            "TARGET SHAPE (DESCRIBED, NOT AN EXAMPLE)\n"
            "Top-level object:\n"
            "{\n"
            "  \"categories\": {\n"
            "    \"<CategoryName>\": {\n"
            "      \"prompts\": [\n"
            "        { \"title\": \"string\", \"prompt\": \"string\", \"tags\": [\"string\"], \"note\": \"string\" }\n"
            "      ],\n"
            "      \"subcategories\": {\n"
            "        \"<SubcategoryName>\": {\n"
            "          \"prompts\": [ ... ],\n"
            "          \"subcategories\": { ... }\n"
            "        }\n"
            "      },\n"
            "      \"color\": \"#RRGGBB\"\n"
            "    }\n"
            "  }\n"
            "}\n\n"
            "RULES\n"
            "1) Categories & subcategories\n"
            "   - Preserve category paths EXACTLY as provided.\n"
            "   - If I provide a path like:  Category > Subcategory > Sub-Sub\n"
            "     -> Nest under \"subcategories\" accordingly.\n"
            "   - If no category is detectable, use \"Uncategorized\".\n"
            "   - Only include \"subcategories\" and \"color\" if explicitly provided.\n"
            "   - If a category line contains a hex color (e.g., \"Art #A12BFF\"), set \"color\" for that category.\n\n"
            "2) Prompt objects\n"
            "   - Each prompt requires:\n"
            "     - \"title\": string\n"
            "     - \"prompt\": string (may be multi-line; keep \\n in JSON strings)\n"
            "   - Optional fields:\n"
            "     - \"tags\": array of strings (include ONLY if provided; split on commas or semicolons; trim)\n"
            "     - \"note\": string (ONLY if provided)\n"
            "   - DO NOT create empty \"tags\" or empty \"note\". Omit them when absent.\n\n"
            "3) Parsing heuristics (be robust to messy input)\n"
            "   - Blocks: Treat a blank line or a delimiter line (e.g., \"---\", \"-----\") as a new prompt boundary.\n"
            "   - Category lines:\n"
            "       - Accept any of:\n"
            "         \"Category: A > B > C\"\n"
            "         \"A > B > C\"\n"
            "         \"[Category] A > B > C\"\n"
            "         \"# A > B > C\" (on its own line)\n"
            "       - When you see a category line, it sets the active category path for the prompts that follow until a new category line appears.\n"
            "   - Title detection (priority order):\n"
            "       1) A line starting with \"Title:\" -> title is the remainder of that line.\n"
            "       2) Otherwise, the first non-empty line of the block up to the first \":\" or \"-\" dash; if none, use the full line (max 200 chars).\n"
            "   - Prompt body detection:\n"
            "       - If a \"Prompt:\" line exists, the prompt body is everything after \"Prompt:\" up to the next delimiter/new block.\n"
            "       - Otherwise, the prompt body is all remaining lines in the block after the title line.\n"
            "   - Tags detection:\n"
            "       - Look for a line starting with \"Tags:\" or \"Tag:\" -> split by comma/semicolon, trim.\n"
            "       - Also accept bracketed formats like \"[tags: a, b, c]\".\n"
            "   - Note detection:\n"
            "       - Look for a line starting with \"Note:\" or \"[note: ...]\".\n"
            "   - Ignore lines like \"Example:\", \"Sample:\", or obvious commentary unless they match the above keys.\n\n"
            "4) Normalization\n"
            "   - Trim trailing spaces on each line inside \"prompt\".\n"
            "   - Preserve internal newlines using \"\\n\".\n"
            "   - Do not change capitalization or wording.\n"
            "   - Deduplicate exact duplicate prompts within the SAME category by keeping the first occurrence.\n\n"
            "5) Ordering\n"
            "   - Preserve the order prompts appear in within each category.\n"
            "   - Preserve the order categories are first encountered.\n\n"
            "6) Validation before output\n"
            "   - Ensure top-level key is \"categories\" (an object).\n"
            "   - Each category has a \"prompts\" array (can be empty).\n"
            "   - All strings use valid JSON escaping.\n\n"
            "INPUT WILL BE PASTED BELOW. RETURN ONLY THE JSON.\n\n"
            "<<<BEGIN RAW PROMPTS>>>\n"
            "[PASTE YOUR UNFORMATTED PROMPTS HERE]\n"
            "<<<END RAW PROMPTS>>>"
        )

    def show_help_about(self):
        """Route legacy help triggers into Settings guide content."""
        self.open_settings(section="about", show_user_guide_popup=True)
            
    def open_prompt_editor(self):
        """Open the comprehensive prompt editor (single-instance)"""
        if self.prompt_editor and self.prompt_editor.window and self.prompt_editor.window.winfo_exists():
            try:
                self.prompt_editor.window.deiconify()
                self.prompt_editor.window.lift()
                self.prompt_editor.window.focus_force()
            except Exception:
                pass
            return
        self.prompt_editor = PromptEditor(self)
        # Auto-select first prompt if available so the editor shows content immediately
        try:
            tree = self.prompt_editor.tree
            for top in tree.get_children():
                # Find the first prompt child under the first category
                for child in tree.get_children(top):
                    vals = tree.item(child, "values")
                    if vals and vals[0] == "prompt":
                        tree.selection_set(child)
                        self.prompt_editor.on_tree_select(None)
                        raise StopIteration
            # If none found, do nothing
        except StopIteration:
            pass
        except Exception:
            pass
        
    def open_settings(self, section="general", show_user_guide_popup=False):
        """Open the settings panel (single-instance), optionally focused to a section."""
        if self.settings_panel and hasattr(self.settings_panel, 'window') and self.settings_panel.window.winfo_exists():
            try:
                self.settings_panel.window.deiconify()
                self.settings_panel.window.lift()
                self.settings_panel.window.focus_force()
                if hasattr(self.settings_panel, "focus_section"):
                    self.settings_panel.focus_section(section)
                if show_user_guide_popup and hasattr(self.settings_panel, "show_user_guide_popup"):
                    self.settings_panel.show_user_guide_popup()
            except Exception:
                pass
            return
        
        # Use modern settings panel
        from src.ui.settings_panel_v2 import SettingsPanelV2
        self.settings_panel = SettingsPanelV2(
            self,
            initial_section=section,
            show_user_guide_popup=show_user_guide_popup
        )

    def open_profile_manager(self):
        """Open the profile manager (single-instance)"""
        if self.profile_manager and hasattr(self.profile_manager, 'window') and self.profile_manager.window.winfo_exists():
            try:
                self.profile_manager.window.deiconify()
                self.profile_manager.window.lift()
                self.profile_manager.window.focus_force()
            except Exception:
                pass
            return
        self.profile_manager = ProfileManager(self, self.config_manager, self.on_profile_change)

    def on_profile_change(self, profile_settings):
        """Handle profile change events"""
        try:
            # Update current settings with profile settings
            self.settings = self.config_manager._merge_settings(self.default_settings, profile_settings)

            # Apply the new settings immediately
            self.apply_settings_update()

            # Save the new settings to the current profile
            current_profile = self.profile_service.get_current_profile()
            if current_profile:
                self.profile_service.update_profile(current_profile.name, self.settings)

        except Exception as e:
            print(f"Error handling profile change: {e}")
            traceback.print_exc()

    def apply_settings_update(self):
        """Apply settings updates without restarting"""
        try:
            # Apply UI scale and compact mode first (affects font/spacing calculations)
            self._apply_ui_scale_settings()
            
            # Update window position
            if "position" in self.settings:
                pos = self.settings["position"]
                self.root.geometry(f"+{pos.get('x', 100)}+{pos.get('y', 100)}")

            # Update opacity
            if "opacity" in self.settings:
                self.root.attributes('-alpha', self.settings["opacity"])

            # Update theme colors
            if "theme" in self.settings:
                self.update_theme_colors()

            # Update fonts
            if "font_scale" in self.settings:
                self.update_fonts()

            # Update search settings
            if hasattr(self, 'search_service'):
                self.search_service.fuzzy_threshold = self.settings.get("search_fuzzy_threshold", 0.6)
                self.search_service.enable_fuzzy = self.settings.get("search_fuzzy", False)

            # Apply virtual scrolling mode immediately (no restart required).
            self.use_virtual_scrolling = bool(self.settings.get("use_virtual_scrolling", False)) and VIRTUAL_SCROLLING_AVAILABLE

            # Keep bar icons and fonts aligned with current scale.
            try:
                self.reapply_fonts_main_bar()
                self.update_icon()
                self._check_overflow_and_adjust()
            except Exception:
                pass

            # Refresh prompt list if drawer is already open so search/virtual mode applies now.
            try:
                if getattr(self, "expanded", False) and getattr(self, "drawer", None):
                    query = self.search_var.get() if hasattr(self, "search_var") else ""
                    self.populate_prompts(query)
            except Exception:
                pass

        except Exception as e:
            print(f"Error applying settings update: {e}")
            traceback.print_exc()
        
    def open_prompts_folder(self):
        """Open the folder containing prompts.json"""
        try:
            # Use secure file operation to open folder
            if not safe_open_file_location(self.data_file):
                messagebox.showerror("Error", "Could not open folder: Invalid path or security check failed")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
            
    def reload_prompts(self):
        """Reload prompts from file"""
        self.load_prompts()
        messagebox.showinfo("Reload", "Prompts reloaded successfully!")
        
    def get_startup_folder(self):
        """Get the Windows startup folder path"""
        try:
            if sys.platform == "win32":
                # Resolve via environment to avoid spawning a console window
                appdata = os.environ.get("APPDATA")
                if appdata:
                    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                return None
            else:
                return None
        except Exception as e:
            print(f"Error getting startup folder: {e}")
            return None
            
    def get_startup_script_path(self):
        """Get the path where the startup script would be placed"""
        startup_folder = self.get_startup_folder()
        if startup_folder:
            return startup_folder / "Promptoire.bat"
        return None
        
    def is_autostart_enabled(self):
        """Check if auto-start is currently enabled"""
        script_path = self.get_startup_script_path()
        return script_path and script_path.exists()

    # ─────────────────────────────── Support helpers ───────────────────────────────
    def get_coffee_url(self):
        try:
            return (self.settings or {}).get("coffee_url", "").strip()
        except Exception:
            return ""

    def open_coffee_url(self):
        url = self.get_coffee_url()
        if not url:
            messagebox.showinfo("Support", "Set your Buy Me a Coffee link in Settings → Support.")
            return
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open link: {e}")
        
    def enable_autostart(self):
        """Enable auto-start with Windows"""
        try:
            startup_folder = self.get_startup_folder()
            if not startup_folder:
                messagebox.showerror("Error", "Could not access Windows startup folder.")
                return
                
            # Create startup script content
            current_dir = Path(__file__).parent.absolute()
            script_content = f'''@echo off
cd /d "{current_dir}"
python promptoire.py
exit'''
            
            # Write the startup script
            script_path = startup_folder / "Promptoire.bat"
            with open(script_path, 'w') as f:
                f.write(script_content)
                
            messagebox.showinfo(
                "Auto-Start Enabled",
                "Promptoire will now start automatically with Windows!\n\n"
                f"Startup script created at:\n{script_path}"
            )
                               
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable auto-start: {e}")
            
    def disable_autostart(self):
        """Disable auto-start with Windows"""
        try:
            script_path = self.get_startup_script_path()
            if script_path and script_path.exists():
                script_path.unlink()
                messagebox.showinfo(
                    "Auto-Start Disabled",
                    "Promptoire will no longer start automatically with Windows."
                )
            else:
                messagebox.showinfo("Auto-Start", "Auto-start was not enabled.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disable auto-start: {e}")
        
    def _is_legacy_prompts_format(self, data):
        """Legacy format: categories contain prompts/subcategories trees."""
        try:
            if not isinstance(data, dict):
                return False
            cats = data.get("categories")
            if not isinstance(cats, dict):
                return False
            for cat in cats.values():
                if isinstance(cat, dict) and ("prompts" in cat or "subcategories" in cat):
                    return True
            return False
        except Exception:
            return False

    def _is_v2_prompts_format(self, data):
        """V2 format: top-level prompts/category metadata tables."""
        try:
            return (
                isinstance(data, dict)
                and isinstance(data.get("categories"), dict)
                and isinstance(data.get("prompts"), dict)
            )
        except Exception:
            return False

    def _convert_v2_prompts_to_legacy(self, data):
        """Convert V2 prompt library format into legacy tree format."""
        legacy = {"categories": {}}
        try:
            categories = data.get("categories", {}) if isinstance(data, dict) else {}
            prompts_by_category = data.get("prompts", {}) if isinstance(data, dict) else {}
            # Build categories from metadata
            for cat_name, cat_meta in categories.items():
                cat_obj = {"prompts": []}
                if isinstance(cat_meta, dict) and cat_meta.get("color"):
                    cat_obj["color"] = cat_meta.get("color")
                legacy["categories"][cat_name] = cat_obj
            # Attach prompts by category name
            for cat_name, prompt_list in prompts_by_category.items():
                if cat_name not in legacy["categories"]:
                    legacy["categories"][cat_name] = {"prompts": []}
                if isinstance(prompt_list, list):
                    legacy["categories"][cat_name]["prompts"] = prompt_list
            return legacy
        except Exception:
            return legacy

    def _count_prompts_in_data(self, data):
        """Count total prompts in a legacy tree dict."""
        try:
            total = 0
            for cat in data.get("categories", {}).values():
                total += self._count_prompts_in_tree(cat)
            return total
        except Exception:
            return 0

    def _load_latest_prompt_backup(self):
        """Load the newest backup that contains prompts."""
        try:
            backup_dir = self.data_file.parent / "backups"
            if not backup_dir.exists():
                return None
            backups = sorted(
                [p for p in backup_dir.glob("prompts-*.json") if p.is_file()],
                key=lambda p: p.name,
                reverse=True,
            )
            for path in backups:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if self._is_legacy_prompts_format(data) and self._count_prompts_in_data(data) > 0:
                        return data
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def _build_search_index_now(self):
        """Build the search index in a safe, non-blocking callback context."""
        try:
            self.search_service.build_search_index(self.prompts)
        except Exception as e:
            self.logger.warning(f"Failed to build search index: {e}")

    def _schedule_search_index_build(self):
        """Schedule search indexing after UI initialization to keep startup snappy."""
        try:
            if getattr(self, "root", None) and self.root.winfo_exists():
                self.root.after_idle(self._build_search_index_now)
            else:
                self._build_search_index_now()
        except Exception:
            self._build_search_index_now()

    def load_prompts(self):
        """Load prompts from JSON file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if self._is_legacy_prompts_format(data):
                    self.prompts = data
                elif self._is_v2_prompts_format(data):
                    converted = self._convert_v2_prompts_to_legacy(data)
                    if self._count_prompts_in_data(converted) > 0:
                        self.prompts = converted
                    else:
                        recovered = self._load_latest_prompt_backup()
                        if recovered:
                            self.prompts = recovered
                            self.save_prompts()
                        else:
                            self.prompts = copy.deepcopy(self.default_prompts)
                else:
                    self.prompts = copy.deepcopy(self.default_prompts)
            else:
                self.prompts = copy.deepcopy(self.default_prompts)
                self.save_prompts()
        except Exception as e:
            print(f"Error loading prompts: {e}")
            self.prompts = copy.deepcopy(self.default_prompts)
        # Backward-compat: install stable IDs in-memory
        try:
            self._ensure_stable_ids()
        except Exception:
            pass
        # Refresh runtime search cache after reload.
        self._prompt_search_cache = {}

        # Build search index asynchronously to avoid blocking app startup.
        self._schedule_search_index_build()
            
    def save_prompts(self):
        """Save prompts to JSON file atomically"""
        try:
            tmp_file = self.data_file.with_suffix('.tmp')
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
            tmp_file.replace(self.data_file)
        except Exception as e:
            print(f"Error saving prompts: {e}")
            traceback.print_exc()

    def autosave_prompts_with_backup(self):
        """Save prompts and maintain a rolling backup of the last 5 versions."""
        try:
            self.save_prompts()
            backup_dir = self.data_file.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = backup_dir / f"prompts-{stamp}.json"
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
            # Prune to last 5
            try:
                backups = sorted([p for p in backup_dir.glob("prompts-*.json") if p.is_file()], key=lambda p: p.name, reverse=True)
                for old in backups[5:]:
                    try:
                        old.unlink()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    # ─────────────────────────────── Import merge helpers ───────────────────────────────
    def _count_prompts_in_tree(self, category_obj):
        """Count prompts recursively in a category tree node."""
        try:
            total = 0
            if isinstance(category_obj, dict):
                total += len(category_obj.get("prompts", []) or [])
                sub = category_obj.get("subcategories", {})
                if isinstance(sub, dict):
                    for _n, subcat in sub.items():
                        total += self._count_prompts_in_tree(subcat)
            return total
        except Exception:
            return 0

    def _merge_category_nodes(self, dest_cat, src_cat):
        """Merge src category node into dest in-place. Returns (prompts_added, categories_added)."""
        prompts_added = 0
        categories_added = 0
        try:
            # Merge prompts with de-dup by content id
            dest_prompts = dest_cat.setdefault("prompts", [])
            existing_ids = set()
            for p in dest_prompts:
                try:
                    existing_ids.add(self._compute_prompt_content_id(p))
                except Exception:
                    pass
            for p in src_cat.get("prompts", []) or []:
                try:
                    pid = self._compute_prompt_content_id(p)
                except Exception:
                    pid = None
                if pid is None or pid not in existing_ids:
                    dest_prompts.append(p)
                    prompts_added += 1
                    if pid:
                        existing_ids.add(pid)

            # Optionally merge visual props if missing
            if "color" in src_cat and "color" not in dest_cat:
                dest_cat["color"] = src_cat["color"]

            # Merge subcategories recursively
            src_sub = src_cat.get("subcategories", {})
            if isinstance(src_sub, dict):
                dest_sub = dest_cat.setdefault("subcategories", {})
                for name, subcat in src_sub.items():
                    if name not in dest_sub or not isinstance(dest_sub.get(name), dict):
                        dest_sub[name] = copy.deepcopy(subcat)
                        categories_added += 1
                        prompts_added += self._count_prompts_in_tree(subcat)
                    else:
                        p_add, c_add = self._merge_category_nodes(dest_sub[name], subcat)
                        prompts_added += p_add
                        categories_added += c_add
        except Exception:
            pass
        return prompts_added, categories_added

    def _merge_prompts_into(self, base_data, imported_data):
        """Merge imported_data into base_data in-place. Returns (prompts_added, categories_added)."""
        prompts_added = 0
        categories_added = 0
        try:
            base_cats = base_data.setdefault("categories", {})
            src_cats = (imported_data or {}).get("categories", {})
            if not isinstance(src_cats, dict):
                return 0, 0
            for name, cat in src_cats.items():
                if name not in base_cats or not isinstance(base_cats.get(name), dict):
                    base_cats[name] = copy.deepcopy(cat)
                    categories_added += 1
                    prompts_added += self._count_prompts_in_tree(cat)
                else:
                    p_add, c_add = self._merge_category_nodes(base_cats[name], cat)
                    prompts_added += p_add
                    categories_added += c_add
        except Exception:
            pass
        return prompts_added, categories_added
            
    def exit_app(self):
        """Exit the application"""
        self.on_closing()

    def open_template_manager(self):
        """Open the template manager dialog"""
        try:
            from .ui.dialogs.TemplateManager import TemplateManagerDialog
            dialog = TemplateManagerDialog(self.root, self.prompt_service, self.settings, self.ui_font)
            dialog.show()
        except ImportError:
            # Fallback to simple template manager if the dialog module doesn't exist
            self._fallback_template_manager()
        except Exception as e:
            self.logger.error(f"Failed to open template manager: {e}")
            messagebox.showerror("Error", "Failed to open template manager")

    def open_analytics_dashboard(self):
        """Open the analytics dashboard dialog"""
        try:
            from .ui.dialogs.AnalyticsDashboard import AnalyticsDashboardDialog
            dialog = AnalyticsDashboardDialog(self.root, self.analytics_service, self.prompt_service, self.settings, self.ui_font)
            dialog.show()
        except ImportError:
            # Fallback to simple analytics display if the dialog module doesn't exist
            self._fallback_analytics_display()
        except Exception as e:
            self.logger.error(f"Failed to open analytics dashboard: {e}")
            messagebox.showerror("Error", "Failed to open analytics dashboard")

    def _fallback_template_manager(self):
        """Fallback template manager implementation"""
        try:
            dlg = tk.Toplevel(self.root)
            dlg.title("Template Manager")
            dlg.geometry("800x600")
            dlg.transient(self.root)
            dlg.grab_set()

            # Apply theming
            bg_color = self.settings["theme"].get("background", "#1a1a1a")
            fg_color = self.settings["theme"].get("foreground", "#ffffff")
            dlg.configure(bg=bg_color)

            # Main frame
            main_frame = tk.Frame(dlg, bg=bg_color)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title_label = tk.Label(main_frame, text="🎯 Template Manager",
                                 font=self.ui_font(16, "bold"),
                                 fg=fg_color, bg=bg_color)
            title_label.pack(pady=(0, 20))

            # Templates list
            templates_frame = tk.Frame(main_frame, bg=bg_color)
            templates_frame.pack(fill="both", expand=True)

            # Get templates
            templates = self.prompt_service.get_all_templates()

            if not templates:
                tk.Label(templates_frame, text="No templates found. Create your first template!",
                        font=self.ui_font(12), fg=self.settings["theme"].get("muted_text", "#a0aec0"),
                        bg=bg_color).pack(expand=True)
            else:
                # Create scrollable frame
                canvas = tk.Canvas(templates_frame, bg=bg_color, highlightthickness=0)
                scrollbar = tk.Scrollbar(templates_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg=bg_color)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                for template in templates:
                    template_frame = tk.Frame(scrollable_frame, bg=self.settings["theme"].get("card_bg", "#2a2a2a"),
                                           relief="raised", bd=1)
                    template_frame.pack(fill="x", pady=5, padx=5)

                    # Template name
                    name_label = tk.Label(template_frame, text=template.name,
                                       font=self.ui_font(12, "bold"),
                                       fg=fg_color, bg=self.settings["theme"].get("card_bg", "#2a2a2a"))
                    name_label.pack(anchor="w", padx=10, pady=(10, 5))

                    # Template content preview
                    content_preview = template.content[:100] + "..." if len(template.content) > 100 else template.content
                    content_label = tk.Label(template_frame, text=content_preview,
                                          font=self.ui_font(10),
                                          fg=self.settings["theme"].get("muted_text", "#a0aec0"),
                                          bg=self.settings["theme"].get("card_bg", "#2a2a2a"),
                                          justify="left", wraplength=700)
                    content_label.pack(anchor="w", padx=10, pady=(0, 10))

                    # Variables
                    if template.variables:
                        vars_text = f"Variables: {', '.join(template.variables)}"
                        vars_label = tk.Label(template_frame, text=vars_text,
                                           font=self.ui_font(9, "italic"),
                                           fg=self.settings["theme"].get("accent", "#4a9eff"),
                                           bg=self.settings["theme"].get("card_bg", "#2a2a2a"))
                        vars_label.pack(anchor="w", padx=10, pady=(0, 10))

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

            # Close button
            close_btn = tk.Button(main_frame, text="Close", command=dlg.destroy,
                                bg=self.settings["theme"].get("button_bg", "#007acc"),
                                fg=fg_color, font=self.ui_font(10, "bold"),
                                relief="flat", cursor="hand2")
            close_btn.pack(pady=(20, 0))

            # Center dialog
            self._center_window(dlg, self.root)

        except Exception as e:
            self.logger.error(f"Fallback template manager failed: {e}")

    def _fallback_analytics_display(self):
        """Fallback analytics display implementation"""
        try:
            dlg = tk.Toplevel(self.root)
            dlg.title("Analytics Dashboard")
            dlg.geometry("800x600")
            dlg.transient(self.root)
            dlg.grab_set()

            # Apply theming
            bg_color = self.settings["theme"].get("background", "#1a1a1a")
            fg_color = self.settings["theme"].get("foreground", "#ffffff")
            dlg.configure(bg=bg_color)

            # Main frame
            main_frame = tk.Frame(dlg, bg=bg_color)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title_label = tk.Label(main_frame, text="📊 Analytics Dashboard",
                                 font=self.ui_font(16, "bold"),
                                 fg=fg_color, bg=bg_color)
            title_label.pack(pady=(0, 20))

            # Get analytics data
            usage_summary = self.analytics_service.get_usage_summary("all")
            category_analytics = self.analytics_service.get_category_analytics()
            time_analytics = self.analytics_service.get_time_analytics()
            productivity_metrics = self.analytics_service.get_productivity_metrics()

            # Create notebook for tabs
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill="both", expand=True)

            # Overview tab
            overview_frame = tk.Frame(notebook, bg=bg_color)
            notebook.add(overview_frame, text="Overview")

            # Usage stats
            stats_frame = tk.Frame(overview_frame, bg=bg_color)
            stats_frame.pack(fill="x", pady=10)

            tk.Label(stats_frame, text=f"Total Prompts Used: {usage_summary.get('total_prompts_used', 0)}",
                    font=self.ui_font(12), fg=fg_color, bg=bg_color).pack(anchor="w", pady=2)
            tk.Label(stats_frame, text=f"Total Sessions: {usage_summary.get('total_sessions', 0)}",
                    font=self.ui_font(12), fg=fg_color, bg=bg_color).pack(anchor="w", pady=2)
            tk.Label(stats_frame, text=f"Avg Session Duration: {usage_summary.get('average_session_duration', 0):.1f}s",
                    font=self.ui_font(12), fg=fg_color, bg=bg_color).pack(anchor="w", pady=2)

            # Categories tab
            categories_frame = tk.Frame(notebook, bg=bg_color)
            notebook.add(categories_frame, text="Categories")

            most_used = category_analytics.get("most_used", [])
            if most_used:
                for category, count in most_used[:10]:
                    tk.Label(categories_frame, text=f"{category}: {count} uses",
                           font=self.ui_font(11), fg=fg_color, bg=bg_color).pack(anchor="w", pady=2)

            # Productivity tab
            productivity_frame = tk.Frame(notebook, bg=bg_color)
            notebook.add(productivity_frame, text="Productivity")

            tk.Label(productivity_frame, text=f"Current Session: {productivity_metrics.get('current_session_duration', 0):.1f}s",
                    font=self.ui_font(11), fg=fg_color, bg=bg_color).pack(anchor="w", pady=2)
            tk.Label(productivity_frame, text=f"Prompts/Hour: {productivity_metrics.get('prompts_per_hour', 0):.1f}",
                    font=self.ui_font(11), fg=fg_color, bg=bg_color).pack(anchor="w", pady=2)
            tk.Label(productivity_frame, text=f"Efficiency Score: {productivity_metrics.get('efficiency_score', 0)}/100",
                    font=self.ui_font(11), fg=fg_color, bg=bg_color).pack(anchor="w", pady=2)

            # Close button
            close_btn = tk.Button(main_frame, text="Close", command=dlg.destroy,
                                bg=self.settings["theme"].get("button_bg", "#007acc"),
                                fg=fg_color, font=self.ui_font(10, "bold"),
                                relief="flat", cursor="hand2")
            close_btn.pack(pady=(20, 0))

            # Center dialog
            self._center_window(dlg, self.root)

        except Exception as e:
            self.logger.error(f"Fallback analytics display failed: {e}")

    def run(self):
        """Start the application"""
        self.root.mainloop()

    def _clear_local_hotkey_binding(self):
        """Remove in-app Tk hotkey fallback binding if present."""
        sequences = list(getattr(self, "_local_hotkey_bindings", []) or [])
        legacy_seq = getattr(self, "_local_hotkey_sequence", None)
        if legacy_seq and legacy_seq not in sequences:
            sequences.append(legacy_seq)
        for seq in sequences:
            try:
                self.root.unbind_all(seq)
            except Exception:
                pass
        self._local_hotkey_bindings = []
        self._local_hotkey_sequence = None
        self._local_hotkey_handler = None

    def _normalize_hotkey_value(self, raw_hotkey):
        """Normalize a configured hotkey string into service format."""
        hotkey = (raw_hotkey or "").strip()
        if not hotkey or hotkey.lower() == "none":
            return ""
        try:
            if hasattr(self, "hotkey_service") and hasattr(self.hotkey_service, "normalize_hotkey_string"):
                normalized = self.hotkey_service.normalize_hotkey_string(hotkey)
                if normalized:
                    return normalized
        except Exception:
            pass
        return hotkey.lower().replace(" ", "")

    def _hotkey_to_tk_sequence(self, hotkey):
        """Convert normalized hotkey format (ctrl+alt+x) to Tk bind sequence."""
        normalized = self._normalize_hotkey_value(hotkey)
        if not normalized:
            return None

        mod_map = {
            "ctrl": "Control",
            "control": "Control",
            "alt": "Alt",
            "shift": "Shift",
            "windows": "Win",
            "win": "Win",
            "command": "Command",
            "cmd": "Command",
        }
        key_map = {
            "space": "space",
            "enter": "Return",
            "esc": "Escape",
            "tab": "Tab",
            "backspace": "BackSpace",
            "delete": "Delete",
            "insert": "Insert",
            "home": "Home",
            "end": "End",
            "page up": "Prior",
            "page down": "Next",
            "up": "Up",
            "down": "Down",
            "left": "Left",
            "right": "Right",
        }

        mods = []
        main = None
        for part in normalized.split("+"):
            piece = (part or "").strip().lower()
            if not piece:
                continue
            if piece in mod_map:
                mapped = mod_map[piece]
                if mapped not in mods:
                    mods.append(mapped)
            else:
                if len(piece) == 1:
                    main = piece
                else:
                    main = key_map.get(piece, piece)

        if not main:
            return None
        return "<" + "-".join(mods + [main]) + ">"

    def _bind_local_hotkey_fallback(self, hotkey):
        """Bind an in-app hotkey fallback via Tk for environments without global hooks."""
        seq = self._hotkey_to_tk_sequence(hotkey)
        if not seq:
            return False

        suppress = bool((self.settings or {}).get("teleport_hotkey_suppress", False))
        if not hasattr(self, "_local_hotkey_bindings") or self._local_hotkey_bindings is None:
            self._local_hotkey_bindings = []
        if seq in self._local_hotkey_bindings:
            return True

        def _on_hotkey(_event=None):
            try:
                trigger = getattr(self, "_trigger_teleport_from_hotkey", None)
                if callable(trigger):
                    trigger()
                else:
                    self.teleport_toggle()
            except Exception:
                pass
            return "break" if suppress else None

        try:
            self.root.bind_all(seq, _on_hotkey, add="+")
            self._local_hotkey_bindings.append(seq)
            self._local_hotkey_sequence = seq
            self._local_hotkey_handler = _on_hotkey
            return True
        except Exception:
            return False

    def _get_teleport_hotkeys(self):
        """Return deduplicated normalized hotkeys for teleport activation."""
        normalize_fn = getattr(self, "_normalize_hotkey_value", None)
        if not callable(normalize_fn):
            normalize_fn = lambda v: str(v or "").strip().lower().replace(" ", "")

        selected = []
        try:
            primary = normalize_fn((self.settings or {}).get("teleport_hotkey", ""))
            if primary and primary not in selected:
                selected.append(primary)
        except Exception:
            pass

        # Aliases are only active when a primary hotkey is configured.
        if not selected:
            return selected

        aliases = []
        try:
            aliases_raw = (self.settings or {}).get("teleport_hotkey_aliases", [])
            if isinstance(aliases_raw, str):
                aliases = [aliases_raw]
            elif isinstance(aliases_raw, (list, tuple, set)):
                aliases = list(aliases_raw)
        except Exception:
            aliases = []

        for raw in aliases:
            try:
                candidate = normalize_fn(raw)
            except Exception:
                candidate = ""
            if candidate and candidate != "none" and candidate not in selected:
                selected.append(candidate)

        return selected

    def _trigger_teleport_from_hotkey(self):
        """Marshal hotkey callbacks onto Tk's UI thread for safe window operations."""
        try:
            if getattr(self, "root", None) and self.root.winfo_exists():
                self.root.after(0, self.teleport_toggle)
            else:
                self.teleport_toggle()
        except Exception:
            pass

    def register_hotkey(self):
        """Register a single global hotkey for Teleport."""
        try:
            clear_local = getattr(self, "_clear_local_hotkey_binding", None)
            if callable(clear_local):
                clear_local()

            # Unhook previous hotkeys
            try:
                if hasattr(self, "hotkey_service") and hasattr(self.hotkey_service, "unregister_all_hotkeys"):
                    self.hotkey_service.unregister_all_hotkeys()
            except Exception:
                pass

            # Register selected hotkeys (primary + aliases)
            selected_hotkeys = self._get_teleport_hotkeys()
            suppress = bool((self.settings or {}).get('teleport_hotkey_suppress', False))

            if not selected_hotkeys:
                self.hotkey_registered = False
                return

            global_available = bool(
                hasattr(self, "hotkey_service")
                and hasattr(self.hotkey_service, "is_available")
                and self.hotkey_service.is_available()
            )

            global_registered = False
            local_registered = False
            failed_hotkeys = []

            for hotkey in selected_hotkeys:
                registered_here = False

                if global_available:
                    try:
                        registered_here = bool(
                            self.hotkey_service.register_hotkey(
                                hotkey,
                                self._trigger_teleport_from_hotkey,
                                name="Teleport",
                                suppress=suppress,
                                overwrite=True,
                            )
                        )
                    except Exception:
                        registered_here = False

                if registered_here:
                    global_registered = True
                    continue

                bind_local = getattr(self, "_bind_local_hotkey_fallback", None)
                if callable(bind_local) and bind_local(hotkey):
                    local_registered = True
                    continue

                failed_hotkeys.append(hotkey)

            if failed_hotkeys and not (global_registered or local_registered):
                try:
                    self.show_notification(f"Hotkey failed: {failed_hotkeys[0]}")
                except Exception:
                    pass

            self.hotkey_registered = bool(global_registered or local_registered)

        except Exception as e:
            print(f"Error registering global hotkey: {e}")
            traceback.print_exc()
            self.hotkey_registered = False

    def teleport_toggle(self):
        """If hidden, show at mouse; if visible and focused, hide; else focus."""
        try:
            # If not visible, show at cursor
            if not self.root.winfo_viewable():
                self.teleport_to_cursor()
                return
            # If drawer open, hide drawer first to reduce clutter
            if getattr(self, 'expanded', False):
                self.hide_drawer()
            # If visible: toggle hide/show behavior
            # If currently on screen, hide (withdraw)
            if self.root.winfo_viewable():
                self.root.withdraw()
                return
        except Exception:
            pass
        # Fallback: show at cursor
        self.teleport_to_cursor()

    # ───────────────────────────────────────── Tray icon helpers ─────────────────────────────────────────

    def setup_tray_icon(self):
        """Create system-tray icon if pystray is available (Windows only)"""
        if not (sys.platform == "win32" and TRAY_AVAILABLE and PIL_AVAILABLE):
            self.tray_icon = None
            return

        # Prepare image for tray (use custom icon if possible, else blank)
        try:
            icon_settings = self.settings["icon"]
            if icon_settings["type"] == "image" and icon_settings["value"]:
                if icon_settings["value"].startswith("data:"):
                    image_data = icon_settings["value"].split(",", 1)[1]
                    img_bytes = base64.b64decode(image_data)
                    tray_img = Image.open(BytesIO(img_bytes)).resize((32, 32), Image.Resampling.LANCZOS)
                else:
                    tray_img = Image.open(icon_settings["value"]).resize((32, 32), Image.Resampling.LANCZOS)
            else:
                # Fallback: simple transparent square
                tray_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        except Exception:
            # Visible fallback icon (teal square with 'A')
            tray_img = Image.new("RGBA", (32, 32), (46, 196, 182, 255))
            try:
                from PIL import ImageDraw
                draw = ImageDraw.Draw(tray_img)
                draw.text((9, 6), "A", fill=(255, 255, 255, 255))
            except Exception:
                pass

        # Initial menu
        self.tray_icon = pystray.Icon(
            "Promptoire",
            tray_img,
            "Promptoire",
            menu=pystray.Menu(pystray.MenuItem("Show / Hide", lambda icon, item: self._tray_action(self.toggle_tray_visibility)))
        )

        # Left-click toggles visibility
        def on_clicked(icon, item):
            self._tray_action(self.toggle_tray_visibility)

        # Use correct callback attribute
        self.tray_icon.on_click = on_clicked

        # Run tray icon in detached thread
        self.tray_icon.run_detached()
        # Build full dynamic menu
        self._rebuild_tray_menu()

    def _rebuild_tray_menu(self):
        try:
            if not getattr(self, 'tray_icon', None):
                return
            items = [pystray.MenuItem("Show / Hide", lambda icon, item: self._tray_action(self.toggle_tray_visibility))]
            # Recents
            if self.settings.get("tray", {}).get("show_recents", True):
                recents = self.settings.get("recent_prompts", [])[: int(self.settings.get("tray", {}).get("recents_count", 5))]
                rec_items = []
                for rid in recents:
                    cat_path, idx, p = self._find_prompt_by_id(rid)
                    if p:
                        title = p.get('title', 'Untitled')
                        rec_items.append(pystray.MenuItem(title[:40], lambda icon, item, pid=rid: self._tray_action(self._tray_copy_by_id, pid)))
                if rec_items:
                    items.append(pystray.Menu.SEPARATOR)
                    items.append(pystray.MenuItem("Recent", pystray.Menu(*rec_items)))
            # Favorites
            if self.settings.get("tray", {}).get("show_favorites", True):
                favs = self.settings.get("favorites", [])[:10]
                fav_items = []
                for fid in favs:
                    cat_path, idx, p = self._find_prompt_by_id(fid)
                    if p:
                        title = p.get('title', 'Untitled')
                        fav_items.append(pystray.MenuItem("⭐ " + title[:38], lambda icon, item, pid=fid: self._tray_action(self._tray_copy_by_id, pid)))
                if fav_items:
                    items.append(pystray.Menu.SEPARATOR)
                    items.append(pystray.MenuItem("Favorites", pystray.Menu(*fav_items)))
            # Coffee link
            if self.get_coffee_url():
                items.append(pystray.Menu.SEPARATOR)
                items.append(pystray.MenuItem("Buy Me a Coffee", lambda icon, item: self._tray_action(self.open_coffee_url_from_tray)))
            # Utilities
            items.append(pystray.Menu.SEPARATOR)
            items.append(pystray.MenuItem("Reload Prompts", lambda icon, item: self._tray_action(self._tray_reload)))
            items.append(pystray.MenuItem("Create Desktop Shortcut", lambda icon, item: self._tray_action(self.create_desktop_shortcut)))
            items.append(pystray.MenuItem("Reset Position", lambda icon, item: self._tray_action(self._tray_reset_position)))
            items.append(pystray.MenuItem("Exit", lambda icon, item: self._tray_action(self.exit_from_tray)))
            self.tray_icon.menu = pystray.Menu(*items)
            try:
                self.tray_icon.update_menu()
            except Exception:
                pass
        except Exception:
            pass

    def _tray_action(self, fn, *args, **kwargs):
        try:
            self.root.after(0, lambda: fn(*args, **kwargs))
        except Exception:
            pass

    def _tray_copy_by_id(self, pid):
        try:
            cat_path, idx, p = self._find_prompt_by_id(pid)
            if p:
                self.copy_prompt(p)
        except Exception:
            pass

    def _tray_reload(self, icon=None, item=None):
        try:
            self.reload_prompts()
        except Exception:
            pass

    def open_coffee_url_from_tray(self, icon=None, item=None):
        self.open_coffee_url()

    def minimize_to_tray(self, *args):
        """Hide the main window and keep running in system tray"""
        if getattr(self, "tray_icon", None):
            self.hide_drawer()
            self.root.withdraw()
        else:
            # Tray not available – just close
            self.on_closing()

    def restore_window(self):
        """Restore the main window from tray"""
        if not self.root.winfo_viewable():
            self.root.deiconify()
        try:
            self.ensure_window_on_screen()
            self.root.lift()
            self.root.focus_force()
            self.root.attributes("-topmost", True)
        except Exception:
            pass

    def toggle_tray_visibility(self, icon=None, item=None):
        """Toggle between hidden and visible states from tray"""
        if self.root.winfo_viewable():
            self.minimize_to_tray()
        else:
            self.restore_window()

    def exit_from_tray(self, icon=None, item=None):
        """Exit application via tray menu"""
        # Ensure tray icon stops first
        if getattr(self, "tray_icon", None):
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        # Now proceed with normal shutdown
        self.on_closing()

    def _tray_reset_position(self, icon=None, item=None):
        try:
            self.root.deiconify()
            self.root.geometry("+100+100")
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def ensure_window_on_screen(self):
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = max(1, self.root.winfo_width())
            h = max(1, self.root.winfo_height())
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            if x + w < 0 or y + h < 0 or x > sw or y > sh:
                nx = max(0, min(sw - w, 100))
                ny = max(0, min(sh - h, 100))
                self.root.geometry(f"+{nx}+{ny}")
        except Exception:
            pass

    def _hotkey_toggle(self):
        try:
            if not self.root.winfo_viewable():
                self.restore_window()
            else:
                self.toggle_drawer()
        except Exception:
            pass

    def teleport_to_cursor(self):
        """Move the main window to the current mouse cursor position immediately and show it."""
        try:
            # Ensure window is visible
            if not self.root.winfo_viewable():
                try:
                    self.root.deiconify()
                except Exception:
                    pass
            # Get pointer position in screen coords
            px = max(0, int(self.root.winfo_pointerx()))
            py = max(0, int(self.root.winfo_pointery()))
            # Keep fully on screen
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = max(1, self.root.winfo_width())
            h = max(1, self.root.winfo_height())
            tx = max(0, min(sw - w, px))
            ty = max(0, min(sh - h, py))
            self.root.geometry(f"+{tx}+{ty}")
            # Save position
            try:
                self.settings["position"]["x"] = tx
                self.settings["position"]["y"] = ty
                self.save_settings()
            except Exception:
                pass
            # Bring to front
            try:
                self.root.lift()
                self.root.focus_force()
                self.root.attributes("-topmost", True)
            except Exception:
                pass
        except Exception:
            pass

    # ───────────────────────────────────────── Data reload ─────────────────────────────────────────
    def reload_prompts(self):
        try:
            self.load_prompts()
            if self.expanded:
                self.populate_prompts(self.search_var.get() if hasattr(self, 'search_var') else "")
                self.update_stats()
            self.show_notification("Prompts reloaded")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload prompts: {e}")

    def export_prompts(self):
        try:
            file_path = self.file_service.save_file_dialog(
                title="Export Prompts JSON",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                initialfile="prompts.json"
            )
            if not file_path:
                return

            # Use the FileService atomic writer (handles Windows paths correctly)
            if hasattr(self, "file_service") and hasattr(self.file_service, "write_json_file"):
                ok = self.file_service.write_json_file(file_path, self.prompts)
            else:
                # Fallback to a direct write
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.prompts, f, indent=2, ensure_ascii=False)
                ok = True
            if not ok:
                raise Exception("Failed to write file")

            self.show_notification("Exported prompts.json")
        except Exception as e:
            messagebox.showerror("Export", f"Failed to export: {e}")

    def import_prompts(self):
        try:
            file_path = self.file_service.open_file_dialog(
                title="Import Prompts JSON (will MERGE with existing)",
                filetypes=[("JSON files", "*.json")]
            )
            if not file_path:
                return

            # Read JSON safely (handles Windows paths correctly)
            if hasattr(self, "file_service") and hasattr(self.file_service, "read_json_file"):
                data = self.file_service.read_json_file(file_path)
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            if not isinstance(data, dict) or "categories" not in data:
                raise ValueError("Invalid prompts file")
            # Merge into existing instead of replacing
            added_prompts, added_categories = self._merge_prompts_into(self.prompts, data)
            self.save_prompts()
            
            # Defer UI updates to after the file dialog fully closes
            # This prevents "bad window path name" errors from stale widget references
            def _deferred_ui_update():
                try:
                    if self.expanded:
                        # Check that scrollable_frame exists before updating
                        if hasattr(self, 'scrollable_frame') and self.scrollable_frame.winfo_exists():
                            self.populate_prompts(self.search_var.get() if hasattr(self, "search_var") else "")
                            self.update_stats()
                    self._rebuild_tray_menu()
                    self.show_notification(f"Imported and merged ({added_prompts} prompts, {added_categories} categories)")
                except tk.TclError:
                    # Widget was destroyed during update, just show notification
                    self._rebuild_tray_menu()
                    self.show_notification(f"Imported and merged ({added_prompts} prompts, {added_categories} categories)")
            
            # Schedule update after current event processing completes
            self.root.after_idle(_deferred_ui_update)
        except Exception as e:
            messagebox.showerror("Import", f"Failed to import: {e}")

    def backup_prompts(self):
        try:
            backup_dir = self.data_file.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = backup_dir / f"prompts-{stamp}.json"
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
            self.show_notification(f"Backup saved: {backup_path.name}")
        except Exception as e:
            messagebox.showerror("Backup", f"Failed to backup: {e}")

    def gist_push(self):
        try:
            import requests
            token = self.settings.get("gist", {}).get("token", "").strip()
            gid = self.settings.get("gist", {}).get("gist_id", "").strip()
            if not token:
                messagebox.showerror("Gist", "Set a GitHub token in Settings → Sync.")
                return
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
            files = {"prompts.json": {"content": json.dumps(self.prompts, indent=2, ensure_ascii=False)}}
            if gid:
                resp = requests.patch(f"https://api.github.com/gists/{gid}", json={"files": files}, headers=headers, timeout=20)
            else:
                resp = requests.post("https://api.github.com/gists", json={"files": files, "public": False, "description": "Promptoire prompts"}, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if not gid:
                self.settings.setdefault("gist", {})["gist_id"] = data.get("id", "")
                self.save_settings()
            self.show_notification("Pushed to Gist")
        except Exception as e:
            messagebox.showerror("Gist", f"Failed to push: {e}")

    def gist_pull(self):
        try:
            import requests
            token = self.settings.get("gist", {}).get("token", "").strip()
            gid = self.settings.get("gist", {}).get("gist_id", "").strip()
            if not token or not gid:
                messagebox.showerror("Gist", "Set GitHub token and Gist ID in Settings → Sync.")
                return
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
            resp = requests.get(f"https://api.github.com/gists/{gid}", headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            files = data.get("files", {})
            file_meta = files.get("prompts.json")
            if not file_meta:
                raise ValueError("Gist does not contain prompts.json")
            # Raw URL might be provided
            raw_url = file_meta.get("raw_url")
            if raw_url:
                raw = requests.get(raw_url, timeout=20)
                raw.raise_for_status()
                content = raw.text
            else:
                content = file_meta.get("content", "{}")
            data = json.loads(content)
            if not isinstance(data, dict) or "categories" not in data:
                raise ValueError("Invalid prompts content")
            self.prompts = data
            self.save_prompts()
            if self.expanded:
                self.populate_prompts(self.search_var.get() if hasattr(self, "search_var") else "")
                self.update_stats()
            self._rebuild_tray_menu()
            self.show_notification("Pulled from Gist")
        except Exception as e:
            messagebox.showerror("Gist", f"Failed to pull: {e}")

    def ping_bar(self):
        """Brief visual 'radar ping' on the main bar to help locate it."""
        try:
            bg = self.settings["theme"].get("background", "#1a1a1a")
            hi = self.settings["theme"].get("highlight", "#0ea5e9")
            # Flash border and background a few times
            def flash(i=0):
                try:
                    if i >= 6:
                        self.root.configure(bg=bg, highlightbackground="#555555")
                        return
                    if i % 2 == 0:
                        self.root.configure(bg=hi, highlightbackground=hi)
                    else:
                        self.root.configure(bg=bg, highlightbackground="#555555")
                    self.root.after(100, lambda: flash(i+1))
                except Exception:
                    pass
            # Bring to front and ping
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass
            flash(0)
        except Exception:
            pass


class PromptEditor:
    """Comprehensive prompt editor window"""
    PLACEHOLDER_TITLE = "New Prompt"
    PLACEHOLDER_PROMPT = "Enter your prompt here..."
    
    def __init__(self, parent):
        self.parent = parent
        # Deep copy to avoid mutating parent's prompts until save
        self.prompts = copy.deepcopy(parent.prompts)
        # Undo/Redo stacks
        self._undo_stack = []
        self._redo_stack = []
        self.window = tk.Toplevel(parent.root)
        # Clear parent's ref on close so it can be reopened later
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self.setup_window()
        self.create_widgets()
        # Populate immediately and once more after the UI is realized to ensure visibility
        self.populate_tree()
        try:
            self.window.after_idle(self._refresh_from_parent_and_populate)
        except Exception:
            pass

    def _refresh_from_parent_and_populate(self):
        try:
            # Re-sync in case parent prompts were updated after editor init
            self.prompts = copy.deepcopy(self.parent.prompts)
            self.populate_tree()
            try:
                self.tree.update_idletasks()
            except Exception:
                pass
        except Exception:
            pass
        
    def setup_window(self):
        """Setup the editor window"""
        self.window.title("Promptoire - Prompt Editor")
        self.window.geometry("820x600")
        try:
            self.window.minsize(780, 560)
        except Exception:
            pass
        self.window.attributes("-topmost", True)
        try:
            self.window.bind("<Escape>", lambda e: self._on_close())
            self.window.bind("<Control-w>", lambda e: self._on_close())
        except Exception:
            pass
        
        # Theme colors
        bg_color = self.parent.settings["theme"]["background"]
        fg_color = self.parent.settings["theme"]["foreground"]
        self.window.configure(bg=bg_color)
        # Subtle 1px border to match dark theme
        try:
            self.window.configure(highlightbackground=self.parent.settings["theme"].get("border", "#3a3a3a"), highlightthickness=1)
            self.parent._apply_window_icon(self.window)
        except Exception:
            pass
        
    def create_widgets(self):
        """Create the editor interface"""
        bg_color = self.parent.settings["theme"]["background"]
        fg_color = self.parent.settings["theme"]["foreground"]
        accent_color = self.parent.settings["theme"]["accent"]
        highlight = self.parent.settings["theme"].get("highlight", accent_color)
        accent_fg = self.parent._text_on(accent_color, fg_color)
        muted_fg = self.parent._text_on(bg_color, self.parent.settings["theme"].get("muted_text", fg_color), min_ratio=3.0)
        visual_settings = self.parent.settings.get("visual", {})
        
        # Bottom buttons (pinned footer placed first so it always remains visible)
        bottom_frame = tk.Frame(
            self.window,
            bg=bg_color,
            highlightbackground=self.parent.settings["theme"].get("border", "#3a3a3a"),
            highlightthickness=1,
        )
        bottom_frame.pack(side="bottom", fill="x", padx=8, pady=4)

        # Main frame
        main_frame = tk.Frame(self.window, bg=bg_color)
        main_frame.pack(fill="both", expand=True, padx=8, pady=6)
        
        # Left panel - Tree view
        left_shell = tk.Frame(
            main_frame,
            bg=self.parent.settings["theme"].get("border", "#3a3a3a"),
            padx=1,
            pady=1
        )
        left_shell.pack(side="left", fill="both", expand=True)
        left_frame = tk.Frame(left_shell, bg=bg_color)
        left_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Tree view label with drag and drop hint
        tree_label = tk.Label(left_frame, text="📚 Prompt Library",
                             font=self.parent.ui_font(12, self.parent.title_weight()), bg=bg_color, fg=fg_color)
        tree_label.pack(pady=(0, 5))

        # Hint about drag and drop functionality
        hint_label = tk.Label(left_frame, text="💡 Drag items to reorder live. Rows will jump into place as you move.",
                             font=self.parent.ui_font(9), bg=bg_color, fg=muted_fg)
        hint_label.pack(pady=(0, 5))
        
        # Search bar (debounced filter)
        search_row = tk.Frame(left_frame, bg=bg_color)
        search_row.pack(fill="x", pady=(0, 6))
        self.search_var = tk.StringVar()
        self._search_after = None
        search_entry = tk.Entry(search_row, textvariable=self.search_var, bg=accent_color, fg=accent_fg, relief="flat", font=self.parent.ui_font(10), insertbackground=accent_fg)
        search_entry.pack(side="left", fill="x", expand=True)
        def on_key(_e=None):
            try:
                if self._search_after:
                    self.window.after_cancel(self._search_after)
            except Exception:
                pass
            self._search_after = self.window.after(200, self.apply_tree_filter)
        search_entry.bind("<KeyRelease>", on_key)
        # Ctrl+F focuses search
        try:
            self.window.bind("<Control-f>", lambda e: (search_entry.focus_set(), search_entry.select_range(0, tk.END)))
        except Exception:
            pass

        # Quick toolbar (top): ensure Add Category is always visible - Modern style
        tree_btn_frame = tk.Frame(left_frame, bg=bg_color)
        tree_btn_frame.pack(fill="x", pady=(4, 6))

        toolbar_layout = [
            [
                {
                    "text": "➕ Add Category",
                    "command": self.add_category_top_level,
                    "bg": "#2563eb",
                    "fg": "white",
                    "hover": "#1d4ed8",
                },
                {
                    "text": "➕ Add Prompt",
                    "command": self.add_prompt,
                },
                {
                    "text": "✏️ Edit",
                    "command": self.edit_selected,
                },
                {
                    "text": "🗑️ Delete",
                    "command": self.delete_selected,
                    "bg": "#ff4444",
                    "fg": "white",
                    "hover": "#ff6666",
                },
            ],
            [
                {
                    "text": "↩️ Undo",
                    "command": self.undo,
                    "bg": self.parent.settings["theme"]["button_bg"],
                    "fg": fg_color,
                    "hover": self.parent.settings["theme"]["button_hover"],
                },
                {
                    "text": "↪️ Redo",
                    "command": self.redo,
                    "bg": self.parent.settings["theme"]["button_bg"],
                    "fg": fg_color,
                    "hover": self.parent.settings["theme"]["button_hover"],
                },
                {
                    "text": "📦 Move To...",
                    "command": self.move_selected_to,
                },
                {
                    "text": "⬆ Move Up",
                    "command": self.move_selected_up,
                },
                {
                    "text": "⬇ Move Down",
                    "command": self.move_selected_down,
                },
            ],
        ]

        def _build_toolbar_button(parent_frame, cfg):
            return self.parent._create_modern_button(
                parent_frame,
                cfg["text"],
                cfg["command"],
                bg_color=cfg.get("bg", accent_color),
                fg_color=cfg.get("fg", fg_color),
                hover_color=cfg.get("hover", self.parent.settings["theme"]["button_hover"]),
                font_size=9,
                font_weight="bold"
            )

        for row_cfg in toolbar_layout:
            row_frame = tk.Frame(tree_btn_frame, bg=bg_color)
            row_frame.pack(fill="x", pady=(0, 2))
            for btn_cfg in row_cfg:
                btn = _build_toolbar_button(row_frame, btn_cfg)
                btn.pack(side="left", padx=1, pady=1)

        # Tree view with scrollbar
        tree_frame = tk.Frame(left_frame, bg=bg_color)
        tree_frame.pack(fill="both", expand=True)
        
        # Improve tree visibility and readability
        try:
            style = ttk.Style(self.window)
            scale = float(self.parent.settings.get("font_scale", 1.0))
            scale = max(0.85, min(1.6, scale))
            # Ensure readable foreground/background on dark themes
            tree_bg = self.parent._blend_colors(bg_color, accent_color, 0.35)
            tree_fg = self.parent._text_on(tree_bg, fg_color)
            select_bg = self.parent.settings["theme"].get("highlight", accent_color)
            select_fg = self.parent._text_on(select_bg, self.parent.settings["theme"].get("highlight_text", tree_fg))
            style.configure(
                "Treeview",
                font=self.parent.ui_font(10),
                rowheight=int(24 * scale),
                foreground=tree_fg,
                background=tree_bg,
                fieldbackground=tree_bg
            )
            style.configure("Treeview.Heading", font=self.parent.ui_font(10, "bold"))
            # Accent selection color
            try:
                style.map("Treeview", background=[('selected', select_bg)], foreground=[('selected', select_fg)])
            except Exception:
                pass
        except Exception:
            pass
        
        # Use a Canvas wrapper to allow overlay widgets to clip nicely
        self.tree = ttk.Treeview(tree_frame, height=20)
        try:
            self.tree.configure(selectmode="extended")
        except Exception:
            pass
        # Ensure the tree column is shown even without headings
        try:
            self.tree.configure(show="tree")
        except Exception:
            pass
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Increase indentation to make hierarchy clearer
        try:
            cur_indent = int(self.tree.cget("indent")) if "indent" in self.tree.keys() else 19
        except Exception:
            cur_indent = 19
        try:
            self.tree.configure(indent=max(cur_indent, 32))
        except Exception:
            pass

        # Enhanced tree styling for better visual hierarchy
        try:
            # Add padding for better spacing
            self.tree.configure(padx=4, pady=2)
        except Exception:
            pass
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        # Tree view bindings
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.edit_selected)
        # Context menu + shortcuts
        self.tree.bind("<Button-3>", self._show_tree_context_menu)
        self.tree.bind("<F2>", lambda e: self.rename_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<Return>", self.edit_selected)
        # Keyboard reordering shortcuts
        try:
            self.tree.bind("<Alt-Up>", lambda e: (self.move_selected_up(), "break"))
            self.tree.bind("<Alt-Down>", lambda e: (self.move_selected_down(), "break"))
            self.tree.bind("<Control-Shift-M>", lambda e: (self.move_selected_to(), "break"))
        except Exception:
            pass
        # Multi-selection enhancements: anchor-based Shift selection and Shift+Arrow range extend
        try:
            self._selection_anchor = None
            # Set anchor on plain click
            def _on_plain_click(event):
                try:
                    # Ignore if Shift/Ctrl pressed
                    if (event.state & 0x0001) or (event.state & 0x0004):
                        return
                    item = self.tree.identify_row(event.y)
                    if item:
                        self._selection_anchor = item
                except Exception:
                    pass
            # Shift+Click to select range between anchor and clicked item (across visible items)
            def _on_shift_click(event):
                try:
                    item = self.tree.identify_row(event.y)
                    if not item:
                        return "break"
                    anchor = self._selection_anchor or item
                    self._select_range_between(anchor, item)
                    # Keep focus on clicked item
                    try:
                        self.tree.focus(item)
                        self.tree.see(item)
                    except Exception:
                        pass
                    return "break"
                except Exception:
                    return "break"
            # Shift+Arrow to extend selection
            def _on_shift_up(event):
                try:
                    focus = self.tree.focus() or (self.tree.selection()[0] if self.tree.selection() else None)
                    if not focus:
                        return "break"
                    anchor = self._selection_anchor or focus
                    prev_item = self._get_prev_visible_item(focus)
                    if not prev_item:
                        return "break"
                    self._select_range_between(anchor, prev_item)
                    try:
                        self.tree.focus(prev_item)
                        self.tree.see(prev_item)
                    except Exception:
                        pass
                    return "break"
                except Exception:
                    return "break"
            def _on_shift_down(event):
                try:
                    focus = self.tree.focus() or (self.tree.selection()[0] if self.tree.selection() else None)
                    if not focus:
                        return "break"
                    anchor = self._selection_anchor or focus
                    next_item = self._get_next_visible_item(focus)
                    if not next_item:
                        return "break"
                    self._select_range_between(anchor, next_item)
                    try:
                        self.tree.focus(next_item)
                        self.tree.see(next_item)
                    except Exception:
                        pass
                    return "break"
                except Exception:
                    return "break"
            self.tree.bind("<Button-1>", _on_plain_click, add=True)
            self.tree.bind("<Shift-Button-1>", _on_shift_click, add=True)
            self.tree.bind("<Shift-Up>", _on_shift_up, add=True)
            self.tree.bind("<Shift-Down>", _on_shift_down, add=True)
            # Ctrl+Click to toggle additive selection without clearing
            def _on_ctrl_click(event):
                try:
                    item = self.tree.identify_row(event.y)
                    if not item:
                        return "break"
                    current = set(self.tree.selection())
                    if item in current:
                        try:
                            self.tree.selection_remove(item)
                        except Exception:
                            pass
                    else:
                        try:
                            self.tree.selection_add(item)
                        except Exception:
                            pass
                    try:
                        self.tree.focus(item)
                        self.tree.see(item)
                    except Exception:
                        pass
                    # Do not change anchor on Ctrl toggles unless it is not set yet
                    if not getattr(self, "_selection_anchor", None):
                        self._selection_anchor = item
                    return "break"
                except Exception:
                    return "break"
            self.tree.bind("<Control-Button-1>", _on_ctrl_click, add=True)
        except Exception:
            pass
        # Mouse-wheel scrolling for tree
        try:
            def _on_tree_mousewheel(event):
                try:
                    self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except Exception:
                    pass
                return "break"
            self.tree.bind("<MouseWheel>", _on_tree_mousewheel)
        except Exception:
            pass
        try:
            self.window.bind("<Control-s>", lambda e: self.save_current())
            self.window.bind("<Control-z>", lambda e: (self.undo(), "break"))
            self.window.bind("<Control-y>", lambda e: (self.redo(), "break"))
        except Exception:
            pass
        # Persist expansion state
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_open)
        self.tree.bind("<<TreeviewClose>>", self._on_tree_close)
        # Track expanded paths
        self.expanded_paths = set(self.parent.settings.get("editor_expanded_paths", []))
        

        # Live drag-and-drop state (items move out of each other's way while dragging)
        self._dnd_state = {
            "drag_item": None,
            "drag_values": None,
            "drag_start_x": 0,
            "drag_start_y": 0,
            "drag_threshold": 8,
            "is_dragging": False,
            "drop_indicator": None,
            "highlighted_item": None,
            "undo_pushed": False,
            "last_drop_signature": None,
            "last_drop_timestamp": 0.0,
            "hover_signature": None,
            "hover_signature_since": 0.0,
            "last_motion_y": 0,
            "last_motion_time": 0.0,
        }
        # Hover-to-expand timer id
        self._hover_expand_after_id = None
        self._hover_expand_target = None
        # Legacy placeholders kept for backward compatibility with optional helpers
        self._drop_line = None
        self._drop_label = None
        self._drag_ghost = None
        self._drag_ghost_label = None
        
        def _on_tree_button_press(event):
            try:
                iid = self.tree.identify_row(event.y)
                self._dnd_state["drag_item"] = iid
                self._dnd_state["drag_values"] = self.tree.item(iid, "values") if iid else None
                self._dnd_state["drag_start_x"] = event.x
                self._dnd_state["drag_start_y"] = event.y
                self._dnd_state["is_dragging"] = False
                self._dnd_state["undo_pushed"] = False
                self._dnd_state["last_drop_signature"] = None
                self._dnd_state["last_drop_timestamp"] = 0.0
                self._dnd_state["hover_signature"] = None
                self._dnd_state["hover_signature_since"] = 0.0
                self._dnd_state["last_motion_y"] = event.y
                self._dnd_state["last_motion_time"] = time.time()
                # Clear any previous visual feedback
                self._clear_drag_visual_feedback()
                # Visually mark the source as picked up
                try:
                    if iid:
                        self.tree.item(iid, tags=("drag_source",))
                        self.tree.tag_configure("drag_source", background="#0ea5e9", foreground="white")
                except Exception:
                    pass
            except Exception:
                pass
                
        def _on_tree_b1_motion(event):
            try:
                if not self._dnd_state["drag_item"] or not self._dnd_state["drag_values"]:
                    return
                    
                # Check if we've moved enough to start dragging
                if not self._dnd_state["is_dragging"]:
                    dx = abs(event.x - self._dnd_state["drag_start_x"])
                    dy = abs(event.y - self._dnd_state["drag_start_y"])
                    if dx > self._dnd_state["drag_threshold"] or dy > self._dnd_state["drag_threshold"]:
                        self._dnd_state["is_dragging"] = True
                        # Change cursor to indicate dragging
                        try:
                            self.tree.configure(cursor="fleur")
                        except Exception:
                            pass
                    else:
                        return

                # Auto-scroll tree when near edges while dragging
                try:
                    h = int(self.tree.winfo_height())
                    margin = max(16, h // 12)
                    if event.y < margin:
                        self.tree.yview_scroll(-1, "units")
                    elif event.y > h - margin:
                        self.tree.yview_scroll(1, "units")
                except Exception:
                    pass

                # Find the item under the cursor
                dst_iid = self.tree.identify_row(event.y)
                if dst_iid:
                    dst_vals = self.tree.item(dst_iid, "values")
                    if dst_vals:
                        self._update_drag_visual_feedback(dst_iid, dst_vals, event.y)
                        self._perform_live_drag_reorder(dst_iid, dst_vals, event.y)
            except Exception:
                pass
                
        def _on_tree_button_release(event):
            try:
                if not self._dnd_state["is_dragging"]:
                    # If we weren't dragging, just clear state
                    self._clear_drag_visual_feedback()
                    self._reset_dnd_state()
                    return
                    
                src_iid = self._dnd_state.get("drag_item")
                src_vals = self._dnd_state.get("drag_values")

                if not src_iid or not src_vals:
                    self._clear_drag_visual_feedback()
                    self._reset_dnd_state()
                    return
                    
                dst_iid = self.tree.identify_row(event.y)
                if not dst_iid:
                    self._clear_drag_visual_feedback()
                    self._reset_dnd_state()
                    return
                    
                dst_vals = self.tree.item(dst_iid, "values")
                if not dst_vals:
                    self._clear_drag_visual_feedback()
                    self._reset_dnd_state()
                    return

                drop_position = self._get_drop_position(dst_iid, event.y)
                if not self._is_valid_drop_target(src_vals, dst_vals, drop_position):
                    self._clear_drag_visual_feedback()
                    self._reset_dnd_state()
                    return

                final_signature = (
                    src_vals[0],
                    src_vals[1] if len(src_vals) > 1 else "",
                    str(src_vals[2]) if len(src_vals) > 2 else "",
                    dst_vals[0],
                    dst_vals[1] if len(dst_vals) > 1 else "",
                    str(dst_vals[2]) if len(dst_vals) > 2 else "",
                    drop_position,
                )
                if final_signature == self._dnd_state.get("last_drop_signature"):
                    self._clear_drag_visual_feedback()
                    self._reset_dnd_state()
                    return

                # Final placement pass for the release position.
                self._handle_drag_drop(
                    src_iid,
                    src_vals,
                    dst_iid,
                    dst_vals,
                    event.y,
                    record_undo=not bool(self._dnd_state.get("undo_pushed")),
                )
                self._clear_drag_visual_feedback()
                self._reset_dnd_state()
                
            except Exception:
                pass
            finally:
                # Always reset cursor
                try:
                    self.tree.configure(cursor="")
                except Exception:
                    pass
        try:
            self.tree.bind("<ButtonPress-1>", _on_tree_button_press, add=True)
            self.tree.bind("<B1-Motion>", _on_tree_b1_motion, add=True)
            self.tree.bind("<ButtonRelease-1>", _on_tree_button_release, add=True)
        except Exception:
            pass
        
        # Right panel - Editor
        right_shell = tk.Frame(
            main_frame,
            bg=self.parent.settings["theme"].get("border", "#3a3a3a"),
            width=350,
            padx=1,
            pady=1
        )
        right_shell.pack(side="right", fill="both", padx=(8, 0))
        right_shell.pack_propagate(False)
        right_frame = tk.Frame(right_shell, bg=bg_color, width=348)
        right_frame.pack(fill="both", expand=True, padx=5, pady=5)
        right_frame.pack_propagate(False)

        field_label_font = self.parent.ui_font(9, "bold")
        entry_font = self.parent.ui_font(9)
        mono_entry_font = self.parent.mono_font(9)
        field_gap = 8
        
        # Editor label
        editor_label = tk.Label(right_frame, text="🛠 Prompt Details", 
                               font=self.parent.ui_font(11, self.parent.title_weight()), bg=bg_color, fg=fg_color)
        editor_label.pack(pady=(0, 4))
        
        # Title field
        tk.Label(right_frame, text="Title", font=field_label_font, bg=bg_color, fg=fg_color).pack(anchor="w")
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(right_frame, textvariable=self.title_var, 
                                   bg=accent_color, fg=accent_fg, relief="flat", font=entry_font, insertbackground=accent_fg)
        self.title_entry.pack(fill="x", pady=(0, field_gap))

        # Highlight placeholder title text on focus
        
        # Prompt field
        tk.Label(right_frame, text="Prompt", font=field_label_font, bg=bg_color, fg=fg_color).pack(anchor="w")
        prompt_container = tk.Frame(right_frame, bg=bg_color)
        prompt_container.pack(fill="both", expand=True, pady=(0, field_gap))
        self.prompt_text = tk.Text(prompt_container, height=12, wrap="word",
                                   bg=accent_color, fg=accent_fg, relief="flat", font=mono_entry_font, insertbackground=accent_fg)
        prompt_scroll = ttk.Scrollbar(prompt_container, orient="vertical", command=self.prompt_text.yview)
        try:
            self.prompt_text.configure(yscrollcommand=prompt_scroll.set)
        except Exception:
            pass
        self.prompt_text.pack(side="left", fill="both", expand=True)
        prompt_scroll.pack(side="right", fill="y")
        # Mouse-wheel scrolling for prompt text
        try:
            def _on_text_mousewheel(event):
                try:
                    self.prompt_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except Exception:
                    pass
                return "break"
            self.prompt_text.bind("<MouseWheel>", _on_text_mousewheel)
        except Exception:
            pass

        # Tags field
        tk.Label(
            right_frame,
            text="Tags (comma-separated)",
            font=field_label_font,
            bg=bg_color,
            fg=fg_color,
        ).pack(anchor="w")
        self.tags_var = tk.StringVar()
        self.tags_entry = tk.Entry(right_frame, textvariable=self.tags_var, 
                                   bg=accent_color, fg=accent_fg, relief="flat", font=entry_font, insertbackground=accent_fg)
        self.tags_entry.pack(fill="x", pady=(0, field_gap))

        # Note field
        tk.Label(
            right_frame,
            text="Note (short description)",
            font=field_label_font,
            bg=bg_color,
            fg=fg_color,
        ).pack(anchor="w")
        self.note_var = tk.StringVar()
        self.note_entry = tk.Entry(right_frame, textvariable=self.note_var, 
                                   bg=accent_color, fg=accent_fg, relief="flat", font=entry_font, insertbackground=accent_fg)
        self.note_entry.pack(fill="x", pady=(0, field_gap))

        # Category color controls (visible when a category is selected)
        self.cat_color_section = tk.Frame(right_frame, bg=bg_color)
        tk.Label(self.cat_color_section, text="Category Header Color", font=field_label_font, bg=bg_color, fg=fg_color).pack(anchor="w")
        self.cat_color_var = tk.StringVar(value="#222222")
        tk.Button(self.cat_color_section, textvariable=self.cat_color_var,
                  command=self.apply_category_color, bg=accent_color, fg=accent_fg, relief="flat").pack(anchor="w", pady=(0, 10))
        # hidden by default; shown on category select

        # Highlight placeholder prompt text on focus
        def on_prompt_focus_in(event):
            content = self.prompt_text.get("1.0", tk.END).strip()
            if content == self.PLACEHOLDER_PROMPT:
                self.prompt_text.tag_add(tk.SEL, "1.0", "end")
                self.prompt_text.mark_set(tk.INSERT, "1.0")
        self.prompt_text.bind("<FocusIn>", on_prompt_focus_in)
        
        # Auto-save when focus leaves the edit widgets
        self.title_entry.bind("<FocusOut>", lambda e: self.save_current())
        self.prompt_text.bind("<FocusOut>", lambda e: self.save_current())
        
        # Editor buttons - Modern style
        editor_btn_frame = tk.Frame(right_frame, bg=bg_color)
        editor_btn_frame.pack(fill="x", pady=(2, 0))
        
        # Save button with feedback - Modern style
        self.save_btn = self.parent._create_modern_button(
            editor_btn_frame, 
            "Save", 
            self.save_current,
            bg_color="#16a34a",
            fg_color="white",
            hover_color="#22c55e",
            font_size=9,
            font_weight="bold",
            padx=10,
            pady=3
        )
        self.save_btn.pack(side="left", padx=(0, 4))
        
        revert_btn = self.parent._create_modern_button(
            editor_btn_frame, 
            "Revert", 
            self.revert_current,
            bg_color=self.parent._blend_colors(bg_color, accent_color, 0.35),
            fg_color="white",
            hover_color=self.parent._blend_colors(bg_color, highlight, 0.25),
            font_size=9,
            font_weight="bold",
            padx=10,
            pady=3
        )
        revert_btn.pack(side="left")
        
        # Bottom buttons
        save_all_btn = self.parent._create_modern_button(
            bottom_frame, 
            "Accept", 
            self.save_and_close,
            bg_color=highlight,
            fg_color="white",
            hover_color=self.parent._blend_colors(highlight, "#ffffff", 0.20),
            font_size=10,
            font_weight="bold",
            padx=12,
            pady=4
        )
        save_all_btn.pack(side="right", padx=(4, 0), pady=3)
        
        cancel_btn = self.parent._create_modern_button(
            bottom_frame, 
            "Cancel", 
            self._on_close,
            bg_color="#dc2626",
            fg_color="white",
            hover_color="#ef4444",
            font_size=10,
            font_weight="bold",
            padx=12,
            pady=4
        )
        cancel_btn.pack(side="right", padx=(0, 4), pady=3)
    
    def _reset_dnd_state(self):
        """Reset drag-and-drop state"""
        self._dnd_state.update({
            "drag_item": None,
            "drag_values": None,
            "drag_start_x": 0,
            "drag_start_y": 0,
            "is_dragging": False,
            "drop_indicator": None,
            "highlighted_item": None,
            "undo_pushed": False,
            "last_drop_signature": None,
            "last_drop_timestamp": 0.0,
            "hover_signature": None,
            "hover_signature_since": 0.0,
            "last_motion_y": 0,
            "last_motion_time": 0.0,
        })
        self._hover_expand_target = None
    
    def _clear_drag_visual_feedback(self):
        """Clear all visual feedback from drag operations"""
        try:
            # Cancel any pending hover-expand
            try:
                if self._hover_expand_after_id is not None:
                    self.window.after_cancel(self._hover_expand_after_id)
            except Exception:
                pass
            self._hover_expand_after_id = None
            self._hover_expand_target = None
            # Remove any highlighting
            if self._dnd_state.get("highlighted_item"):
                try:
                    self.tree.item(self._dnd_state["highlighted_item"], tags=())
                except Exception:
                    pass
            self._dnd_state["highlighted_item"] = None
            self._dnd_state["drop_indicator"] = None
            # Clear drag source tag if set
            try:
                for it in self.tree.get_children(""):
                    self._clear_tag_recursive(it, "drag_source")
                    self._clear_tag_recursive(it, "drag_target_valid")
                    self._clear_tag_recursive(it, "drag_target_invalid")
            except Exception:
                pass
            
        except Exception:
            pass

    def _clear_tag_recursive(self, item_id, tag):
        try:
            cur_tags = self.tree.item(item_id, "tags") or ()
            if tag in cur_tags:
                try:
                    self.tree.item(item_id, tags=tuple(t for t in cur_tags if t != tag))
                except Exception:
                    pass
            for child in self.tree.get_children(item_id):
                self._clear_tag_recursive(child, tag)
        except Exception:
            pass
    
    def _update_drag_visual_feedback(self, dst_iid, dst_vals, y_pos):
        """Update compact drag visual feedback while items live-reorder."""
        try:
            # Clear previous highlighting
            if self._dnd_state.get("highlighted_item") and self._dnd_state["highlighted_item"] != dst_iid:
                try:
                    self.tree.item(self._dnd_state["highlighted_item"], tags=())
                except Exception:
                    pass
            
            # Determine drop position and style accordingly
            drop_position = self._get_drop_position(dst_iid, y_pos)
            src_vals = self._dnd_state.get("drag_values")
            
            if not src_vals:
                return
            
            # Determine if this is a valid drop target
            is_valid_drop = self._is_valid_drop_target(src_vals, dst_vals, drop_position)
            
            # Highlight the target item with appropriate style
            self._dnd_state["highlighted_item"] = dst_iid

            try:
                theme = {}
                try:
                    if hasattr(self, 'parent') and getattr(self.parent, 'settings', None):
                        theme = self.parent.settings.get('theme', {}) or {}
                    elif hasattr(self, 'settings') and getattr(self, 'settings', None):
                        theme = self.settings.get('theme', {}) or {}
                except Exception:
                    theme = {}

                accent_color = theme.get('accent', '#2196F3')
                highlight_color = theme.get('highlight', accent_color)
                highlight_text = theme.get('highlight_text', theme.get('foreground', '#ffffff'))
                invalid_bg = theme.get('danger', '#f44336')
                invalid_text = theme.get('danger_text', '#ffffff')

                if is_valid_drop:
                    self.tree.item(dst_iid, tags=('drag_target_valid',))
                    self.tree.tag_configure('drag_target_valid', background=highlight_color, foreground=highlight_text)
                else:
                    self.tree.item(dst_iid, tags=('drag_target_invalid',))
                    self.tree.tag_configure('drag_target_invalid', background=invalid_bg, foreground=invalid_text)

                # Auto-expand categories when hovering over middle band to drop inside.
                # Guard with a stable target id so moving across rows does not queue runaway timers.
                try:
                    should_expand = (
                        is_valid_drop
                        and drop_position == "inside"
                        and dst_vals
                        and dst_vals[0] == "category"
                    )
                    src_path = src_vals[1] if len(src_vals) > 1 else ""
                    dst_path = dst_vals[1] if len(dst_vals) > 1 else ""
                    if should_expand and src_path and src_path == dst_path:
                        should_expand = False

                    if should_expand:
                        is_open = bool(self.tree.item(dst_iid, "open"))
                        if not is_open:
                            if self._hover_expand_target != dst_iid:
                                if self._hover_expand_after_id is not None:
                                    try:
                                        self.window.after_cancel(self._hover_expand_after_id)
                                    except Exception:
                                        pass
                                    self._hover_expand_after_id = None
                                self._hover_expand_target = dst_iid

                                def _expand(target_id=dst_iid):
                                    try:
                                        # Expand only if still hovering the same target.
                                        if self._hover_expand_target == target_id:
                                            self.tree.item(target_id, open=True)
                                    except Exception:
                                        pass
                                    self._hover_expand_after_id = None

                                self._hover_expand_after_id = self.window.after(350, _expand)
                        else:
                            # Already open: no pending timer needed.
                            if self._hover_expand_after_id is not None:
                                try:
                                    self.window.after_cancel(self._hover_expand_after_id)
                                except Exception:
                                    pass
                                self._hover_expand_after_id = None
                            self._hover_expand_target = None
                    else:
                        # Not hovering inside a category: cancel pending expansion
                        if self._hover_expand_after_id is not None:
                            try:
                                self.window.after_cancel(self._hover_expand_after_id)
                            except Exception:
                                pass
                            self._hover_expand_after_id = None
                        self._hover_expand_target = None
                except Exception:
                    pass
                
            except Exception:
                pass
                
        except Exception:
            pass

    def _perform_live_drag_reorder(self, dst_iid, dst_vals, y_pos):
        """Apply live reorder while dragging so items visibly jump into place."""
        try:
            src_iid = self._dnd_state.get("drag_item")
            src_vals = self._dnd_state.get("drag_values")
            if not src_iid or not src_vals or not dst_iid or not dst_vals:
                return
            if dst_iid == src_iid:
                return

            drop_position = self._get_drop_position(dst_iid, y_pos)
            if not self._is_valid_drop_target(src_vals, dst_vals, drop_position):
                return

            # Keep live reordering conservative: only reorder prompts within the same category while hovering
            # stably. Other moves still apply on drop-release, which is less jittery.
            src_type = src_vals[0] if src_vals else ""
            dst_type = dst_vals[0] if dst_vals else ""
            same_category = (
                len(src_vals) > 1 and len(dst_vals) > 1 and str(src_vals[1]) == str(dst_vals[1])
            )
            if not (src_type == "prompt" and dst_type == "prompt" and same_category):
                return

            signature = (
                src_vals[0],
                src_vals[1] if len(src_vals) > 1 else "",
                str(src_vals[2]) if len(src_vals) > 2 else "",
                dst_vals[0],
                dst_vals[1] if len(dst_vals) > 1 else "",
                str(dst_vals[2]) if len(dst_vals) > 2 else "",
                drop_position,
            )
            if signature == self._dnd_state.get("last_drop_signature"):
                return

            now = time.time()
            hover_signature = (
                dst_vals[1] if len(dst_vals) > 1 else "",
                str(dst_vals[2]) if len(dst_vals) > 2 else "",
                drop_position,
            )
            if hover_signature != self._dnd_state.get("hover_signature"):
                self._dnd_state["hover_signature"] = hover_signature
                self._dnd_state["hover_signature_since"] = now
                return

            if now - float(self._dnd_state.get("hover_signature_since", 0.0) or 0.0) < 0.09:
                return

            last_motion_y = int(self._dnd_state.get("last_motion_y", y_pos) or y_pos)
            last_motion_time = float(self._dnd_state.get("last_motion_time", 0.0) or 0.0)
            if abs(int(y_pos) - last_motion_y) < 2 and (now - last_motion_time) < 0.06:
                return

            last_ts = float(self._dnd_state.get("last_drop_timestamp", 0.0) or 0.0)
            if now - last_ts < 0.12:
                return

            self._handle_drag_drop(
                src_iid,
                src_vals,
                dst_iid,
                dst_vals,
                y_pos,
                record_undo=not bool(self._dnd_state.get("undo_pushed")),
            )
            self._dnd_state["undo_pushed"] = True
            self._dnd_state["last_drop_signature"] = signature
            self._dnd_state["last_drop_timestamp"] = now
            self._dnd_state["last_motion_y"] = int(y_pos)
            self._dnd_state["last_motion_time"] = now
            self._dnd_state["hover_signature_since"] = now
            self._sync_drag_state_to_current_selection()
        except Exception:
            pass

    def _sync_drag_state_to_current_selection(self):
        """Keep drag state aligned with the moved item after live reorder refreshes."""
        try:
            iid = None
            sel = self.tree.selection()
            if sel:
                iid = sel[0]
            if not iid:
                iid = self.tree.focus()
            if not iid:
                return
            vals = self.tree.item(iid, "values")
            if not vals:
                return
            self._dnd_state["drag_item"] = iid
            self._dnd_state["drag_values"] = vals
        except Exception:
            pass
    
    def _is_valid_drop_target(self, src_vals, dst_vals, drop_position):
        """Check if the drop target is valid for the source item"""
        try:
            src_type = src_vals[0]
            dst_type = dst_vals[0]
            
            # Prompts can be dropped on prompts (reordering) or categories (moving)
            if src_type == "prompt":
                return True  # Prompts can be moved anywhere
            
            # Categories can be dropped on categories or prompts (to become siblings)
            elif src_type == "category":
                src_path = src_vals[1]
                dst_path = dst_vals[1]
                
                # Can't drop category on itself or its descendants
                if src_path == dst_path or dst_path.startswith(src_path + "/"):
                    return False
                
                # Can't drop category inside itself
                if drop_position == "inside" and src_path == dst_path:
                    return False
                
                return True
            
            return False
        except Exception:
            return False
    
    def _show_drop_position_indicator(self, dst_iid, drop_position, is_valid):
        """Show enhanced visual indicator for drop position with improved styling."""
        try:
            if self._dnd_state.get("drop_indicator"):
                try:
                    self.tree.delete(self._dnd_state["drop_indicator"])
                except Exception:
                    pass
                self._dnd_state["drop_indicator"] = None

            bbox = self.tree.bbox(dst_iid)
            if not bbox:
                return
            x, y, width, height = bbox

            theme = {}
            try:
                if hasattr(self, "parent") and getattr(self.parent, "settings", None):
                    theme = self.parent.settings.get("theme", {}) or {}
                elif hasattr(self, "settings") and getattr(self, "settings", None):
                    theme = self.settings.get("theme", {}) or {}
            except Exception:
                theme = {}

            accent_color = theme.get("accent", "#3b82f6")
            highlight_color = theme.get("highlight", accent_color)
            highlight_text = theme.get("highlight_text", theme.get("foreground", "#ffffff"))
            invalid_bg = theme.get("danger", "#ef4444")
            invalid_text = theme.get("danger_text", "#ffffff")

            if drop_position == "inside":
                dst_vals = self.tree.item(dst_iid, "values")
                dst_type = dst_vals[0] if dst_vals else None

                base_bg = highlight_color if dst_type == "category" else accent_color
                bg_color = base_bg if is_valid else invalid_bg
                text_color = highlight_text if is_valid else invalid_text

                try:
                    if self._drop_line is not None:
                        self._drop_line.destroy()
                except Exception:
                    pass
                self._drop_line = None

                try:
                    text_label = self.tree.item(dst_iid, "text") or ""
                    icon = "📁" if dst_type == "category" else "📄"
                    base_text = "Drop inside"
                    if text_label:
                        label_text = f"{icon} {base_text} '{text_label}'"
                    else:
                        label_text = f"{icon} {base_text}"

                    if self._drop_label is None:
                        self._drop_label = tk.Label(
                            self.tree,
                            text=label_text,
                            bg=bg_color,
                            fg=text_color,
                            font=self.parent.ui_font(9, "bold"),
                            relief="solid",
                            bd=1
                        )
                    else:
                        self._drop_label.configure(
                            text=label_text,
                            bg=bg_color,
                            fg=text_color,
                            font=self.parent.ui_font(9, "bold")
                        )

                    try:
                        w = max(0, int(self.tree.winfo_width()))
                    except Exception:
                        w = width

                    label_x = max(4, (width - len(label_text) * 8) // 2)
                    self._drop_label.place(x=label_x, y=y + (height // 2) - 8, width=min(w - 8, len(label_text) * 8 + 16))
                except Exception:
                    pass
                return

            indicator_y = y if drop_position == "above" else y + height
            base_line_color = highlight_color if drop_position == "above" else accent_color
            line_color = base_line_color if is_valid else invalid_bg
            label_bg = line_color
            label_fg = highlight_text if is_valid else invalid_text

            try:
                if self._drop_line is None:
                    self._drop_line = tk.Frame(
                        self.tree,
                        height=4,
                        bg=line_color,
                        highlightthickness=0,
                        bd=0
                    )
                else:
                    try:
                        self._drop_line.configure(bg=line_color)
                    except Exception:
                        pass

                try:
                    w = max(0, int(self.tree.winfo_width()))
                except Exception:
                    w = width

                self._drop_line.place(x=0, y=max(0, indicator_y - 2), width=w)

                try:
                    text_label = self.tree.item(dst_iid, "text") or ""
                    arrow = "⬆" if drop_position == "above" else "⬇"
                    position_text = "above" if drop_position == "above" else "below"
                    label_text = f"{arrow} Drop {position_text} '{text_label}'" if text_label else f"{arrow} Drop {position_text}"

                    if self._drop_label is None:
                        self._drop_label = tk.Label(
                            self.tree,
                            text=label_text,
                            bg=label_bg,
                            fg=label_fg,
                            font=self.parent.ui_font(8, "bold"),
                            relief="solid",
                            bd=1
                        )
                    else:
                        self._drop_label.configure(
                            text=label_text,
                            bg=label_bg,
                            fg=label_fg,
                            font=self.parent.ui_font(8, "bold")
                        )

                    label_y = indicator_y - 18 if drop_position == "above" else indicator_y + 2
                    self._drop_label.place(x=4, y=max(0, label_y))
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

    def _create_drag_ghost(self, text):
        try:
            if self._drag_ghost is not None:
                return
            self._drag_ghost = tk.Toplevel(self.window)
            try:
                self._drag_ghost.overrideredirect(True)
            except Exception:
                pass
            try:
                self._drag_ghost.attributes("-topmost", True)
            except Exception:
                pass
            try:
                # More visible ghost with slight transparency
                self._drag_ghost.attributes("-alpha", 0.85)
            except Exception:
                pass

            # Enhanced colors for drag ghost
            bg = self.parent.settings["theme"]["highlight"] if "highlight" in self.parent.settings["theme"] else "#0ea5e9"
            fg = self.parent.settings["theme"].get("highlight_text", "#ffffff")

            # Create enhanced ghost with better styling
            frame = tk.Frame(
                self._drag_ghost,
                bg=bg,
                bd=2,
                highlightthickness=1,
                highlightbackground="#ffffff"
            )
            frame.pack(fill="both", expand=True, padx=1, pady=1)

            # Add icon based on item type if possible
            dst_vals = self._dnd_state.get("drag_values")
            if dst_vals and dst_vals[0] == "category":
                icon = "📁"
            elif dst_vals and dst_vals[0] == "prompt":
                icon = "📄"
            else:
                icon = "📋"

            self._drag_ghost_label = tk.Label(
                frame,
                text=f"{icon} {text}",
                bg=bg,
                fg=fg,
                font=self.parent.ui_font(10, "bold"),
                padx=12,
                pady=6
            )
            self._drag_ghost_label.pack()

        except Exception:
            pass

    def _move_drag_ghost(self, x, y):
        try:
            if self._drag_ghost is None:
                return
            self._drag_ghost.geometry(f"+{int(x)}+{int(y)}")
        except Exception:
            pass

    def _destroy_drag_ghost(self):
        try:
            if self._drag_ghost is not None:
                try:
                    self._drag_ghost.destroy()
                except Exception:
                    pass
            self._drag_ghost = None
            self._drag_ghost_label = None
        except Exception:
            pass
    
    def _handle_drag_drop(self, src_iid, src_vals, dst_iid, dst_vals, y_pos, record_undo=True):
        """Handle the actual drag-and-drop operation"""
        try:
            if record_undo:
                self._push_undo()
            
            # Determine drop position within the target item
            drop_position = self._get_drop_position(dst_iid, y_pos)
            # Validate drop
            if not self._is_valid_drop_target(src_vals, dst_vals, drop_position):
                return
            
            # Handle different drag-and-drop scenarios
            if src_vals[0] == "prompt" and dst_vals[0] == "prompt":
                # Moving prompt to another prompt (reordering within same category)
                if src_vals[1] == dst_vals[1]:
                    self._reorder_prompts_same_category(src_vals, dst_vals, drop_position)
                else:
                    # Moving prompt to different category
                    self._move_prompt_to_category(src_vals, dst_vals, drop_position)
                    
            elif src_vals[0] == "prompt" and dst_vals[0] == "category":
                # Moving prompt into a category
                self._move_prompt_to_category(src_vals, dst_vals, drop_position)
                
            elif src_vals[0] == "category" and dst_vals[0] == "category":
                # Moving category
                self._move_category(src_vals, dst_vals, drop_position)
                
            elif src_vals[0] == "category" and dst_vals[0] == "prompt":
                # Moving category to be sibling of prompt's category
                self._move_category_to_sibling_of_prompt(src_vals, dst_vals, drop_position)
                
        except Exception as e:
            print(f"Drag-drop error: {e}")
    
    def _get_drop_position(self, dst_iid, y_pos):
        """Determine if we're dropping above, below, or inside the target item.
        Middle band over a category counts as inside; for prompts, only above/below.
        """
        try:
            bbox = self.tree.bbox(dst_iid)
            if not bbox:
                return "inside"
            item_x, item_y, item_w, item_h = bbox
            top_band = item_y + int(item_h * 0.25)
            bottom_band = item_y + int(item_h * 0.75)
            # Identify destination item type
            dst_vals = self.tree.item(dst_iid, "values")
            dst_type = dst_vals[0] if dst_vals else None

            if y_pos < top_band:
                return "above"
            if y_pos > bottom_band:
                return "below"
            # Middle band
            if dst_type == "category":
                return "inside"
            # For prompts, bias to nearest side
            mid = item_y + (item_h // 2)
            return "below" if y_pos >= mid else "above"
        except Exception:
            return "inside"
    
    def _reorder_prompts_same_category(self, src_vals, dst_vals, drop_position):
        """Reorder prompts within the same category"""
        try:
            src_path = src_vals[1]
            src_idx = int(src_vals[2])
            dst_idx = int(dst_vals[2])
            
            cat = self._get_category_by_path(src_path)
            lst = cat.get("prompts", [])
            
            if 0 <= src_idx < len(lst) and 0 <= dst_idx < len(lst):
                # Remove source prompt
                prompt = lst.pop(src_idx)
                
                # Adjust destination index based on drop position
                if drop_position == "above" and src_idx > dst_idx:
                    new_idx = dst_idx
                elif drop_position == "below" and src_idx < dst_idx:
                    new_idx = dst_idx + 1
                else:
                    new_idx = dst_idx
                
                # Ensure valid index
                new_idx = max(0, min(new_idx, len(lst)))
                
                # Insert at new position
                lst.insert(new_idx, prompt)
                
                self.populate_tree()
                self._restore_selection_by_prompt_keys([(src_path, new_idx)])
                self._autosave()
                
        except Exception as e:
            print(f"Reorder prompts error: {e}")
    
    def _move_prompt_to_category(self, src_vals, dst_vals, drop_position):
        """Move a prompt to a different category"""
        try:
            src_path = src_vals[1]
            src_idx = int(src_vals[2])
            
            # Get source prompt
            src_cat = self._get_category_by_path(src_path)
            src_prompts = src_cat.get("prompts", [])
            if not (0 <= src_idx < len(src_prompts)):
                return
                
            prompt = src_prompts[src_idx]
            
            # Determine destination category
            if dst_vals[0] == "category":
                dst_path = dst_vals[1]
                dst_cat = self._get_category_by_path(dst_path)
                dst_prompts = dst_cat.get("prompts", [])
                insert_idx = len(dst_prompts)  # Default to end
            else:  # dst_vals[0] == "prompt"
                dst_path = dst_vals[1]
                dst_idx = int(dst_vals[2])
                dst_cat = self._get_category_by_path(dst_path)
                dst_prompts = dst_cat.get("prompts", [])
                
                # Calculate insert position
                if drop_position == "above":
                    insert_idx = dst_idx
                else:  # below
                    insert_idx = dst_idx + 1
                insert_idx = max(0, min(insert_idx, len(dst_prompts)))
            
            # Remove from source
            src_prompts.pop(src_idx)
            
            # Add to destination
            dst_prompts.insert(insert_idx, prompt)
            
            self.populate_tree()
            self._restore_selection_by_prompt_keys([(dst_path, insert_idx)])
            self._autosave()
            
        except Exception as e:
            print(f"Move prompt to category error: {e}")
    
    def _move_category(self, src_vals, dst_vals, drop_position):
        """Move a category to a new position"""
        try:
            src_path = src_vals[1]
            dst_path = dst_vals[1]
            
            # Get source category info
            src_is_top, src_container, src_parent, src_name, src_parent_path = self._get_category_container_info(src_path)
            src_data = src_container[src_name]
            
            # Determine destination parent
            if drop_position == "inside":
                # Moving category as subcategory
                dst_is_top, dst_container, dst_parent, dst_name, dst_parent_path = self._get_category_container_info(dst_path)
                new_parent_path = dst_path
                new_name = src_name
            else:
                # Moving as sibling
                dst_parent_path = "/".join(dst_path.split("/")[:-1])
                if dst_parent_path:
                    dst_parent = self._get_category_by_path(dst_parent_path)
                    dst_container = dst_parent.setdefault("subcategories", {})
                    dst_is_top = False
                else:
                    dst_container = self.prompts.setdefault("categories", {})
                    dst_is_top = True
                new_parent_path = dst_parent_path
                new_name = src_name
            
            # Remove from source
            del src_container[src_name]
            
            # Add to destination with ordering rules
            if drop_position == "inside":
                # As subcategory at end
                dst_parent = self._get_category_by_path(new_parent_path)
                sub = dst_parent.setdefault("subcategories", {})
                # Insert at end by rebuilding dict to keep order deterministic
                order = list(sub.keys()) + [new_name]
                new_container = {name: (sub[name] if name in sub else src_data) for name in order}
                dst_parent["subcategories"] = new_container
                new_path = f"{new_parent_path}/{new_name}"
            else:
                # As sibling: insert above/below destination category
                dst_name = dst_path.split("/")[-1]
                order = list(dst_container.keys())
                # Determine insert index relative to destination
                try:
                    dst_index = order.index(dst_name)
                except ValueError:
                    dst_index = len(order)
                insert_idx = dst_index if drop_position == "above" else min(dst_index + 1, len(order))
                # Remove any existing occurrence (in case moving within same container and still present)
                try:
                    if new_name in order:
                        order.remove(new_name)
                except Exception:
                    pass
                # Recompute destination index if needed
                if dst_name in order:
                    dst_index = order.index(dst_name)
                    insert_idx = dst_index if drop_position == "above" else min(dst_index + 1, len(order))
                # Build new order with inserted item
                new_order = order[:insert_idx] + [new_name] + order[insert_idx:]
                new_container = {name: (dst_container[name] if name in dst_container else src_data) for name in new_order}
                if new_parent_path:
                    # Subcategories container of some parent
                    parent_obj = self._get_category_by_path(new_parent_path)
                    parent_obj["subcategories"] = new_container
                else:
                    # Top-level categories
                    self.prompts["categories"] = new_container
                new_path = f"{new_parent_path}/{new_name}" if new_parent_path else new_name
            
            self.populate_tree()
            self._restore_selection_by_category_paths([new_path])
            self._autosave()
            
        except Exception as e:
            print(f"Move category error: {e}")
    
    def _move_category_to_sibling_of_prompt(self, src_vals, dst_vals, drop_position):
        """Move a category to be a sibling of a prompt's category"""
        try:
            src_path = src_vals[1]
            dst_path = dst_vals[1]  # This is the prompt's category path
            
            # Get source category
            src_is_top, src_container, src_parent, src_name, src_parent_path = self._get_category_container_info(src_path)
            src_data = src_container[src_name]
            
            # Determine destination parent (same as prompt's category parent)
            dst_parent_path = "/".join(dst_path.split("/")[:-1])
            if dst_parent_path:
                dst_parent = self._get_category_by_path(dst_parent_path)
                dst_container = dst_parent.setdefault("subcategories", {})
            else:
                dst_container = self.prompts.setdefault("categories", {})
            
            # Remove from source
            del src_container[src_name]
            
            # Insert relative to the prompt's category (above/below)
            dst_category_name = dst_path.split("/")[-1]
            order = list(dst_container.keys())
            # Remove if already exists in this container
            if src_name in order:
                try:
                    order.remove(src_name)
                except Exception:
                    pass
            try:
                dst_index = order.index(dst_category_name)
            except ValueError:
                dst_index = len(order)
            insert_idx = dst_index if drop_position == "above" else min(dst_index + 1, len(order))
            new_order = order[:insert_idx] + [src_name] + order[insert_idx:]
            new_container = {name: (dst_container[name] if name in dst_container else src_data) for name in new_order}
            if dst_parent_path:
                dst_parent["subcategories"] = new_container
            else:
                self.prompts["categories"] = new_container
            new_path = f"{dst_parent_path}/{src_name}" if dst_parent_path else src_name
            
            self.populate_tree()
            self._restore_selection_by_category_paths([new_path])
            self._autosave()
            
        except Exception as e:
            print(f"Move category to sibling error: {e}")
    
    def _autosave(self):
        """Autosave changes"""
        try:
            self.parent.prompts = self.prompts
            # Ensure stable IDs exist for new/edited items before persisting
            try:
                if hasattr(self.parent, "_ensure_stable_ids"):
                    self.parent._ensure_stable_ids()
            except Exception:
                pass
            self.parent.autosave_prompts_with_backup()
        except Exception:
            pass
        
    def populate_tree(self):
        """Populate the tree view with categories and prompts in hierarchical structure"""
        # Preserve vertical scroll position
        try:
            yview = self.tree.yview()
        except Exception:
            yview = None
        self.tree.delete(*self.tree.get_children())
        
        data = getattr(self, "_filtered_data", None)
        src = data if isinstance(data, dict) else self.prompts
        for category_name, category_data in src.get("categories", {}).items():
            self._add_category_to_tree("", category_name, category_data)
        # Restore scroll
        try:
            if yview and isinstance(yview, tuple):
                self.tree.yview_moveto(yview[0])
        except Exception:
            pass
        # Ensure at least the first top-level category is visible and selected for context
        try:
            top_children = self.tree.get_children("")
            if top_children:
                first = top_children[0]
                # Expand the first node
                try:
                    self.tree.item(first, open=True)
                except Exception:
                    pass
                # Select the first prompt under it if available, else select the category
                prompt_child = None
                for child in self.tree.get_children(first):
                    vals = self.tree.item(child, "values")
                    if vals and vals[0] == "prompt":
                        prompt_child = child
                        break
                target = prompt_child or first
                self.tree.selection_set(target)
                try:
                    self.tree.focus(target)
                    self.tree.see(target)
                except Exception:
                    pass
                # Trigger the selection handler so the right pane shows content
                try:
                    self.on_tree_select(None)
                except Exception:
                    pass
            # Force UI refresh
            self.tree.update_idletasks()
        except Exception:
            pass
    
    def _add_category_to_tree(self, parent_id, category_name, category_data, parent_path=""):
        """Recursively add categories and their contents to the tree"""
        current_path = f"{parent_path}/{category_name}" if parent_path else category_name
        
        # Add category node
        # Auto-open when filtered view is active
        is_open = current_path in getattr(self, "expanded_paths", set()) or hasattr(self, "_filtered_data") and isinstance(getattr(self, "_filtered_data"), dict)
        cat_id = self.tree.insert(parent_id, "end", text=f"📁 {category_name}", 
                                 values=("category", current_path), open=is_open)
        
        # Add direct prompts in this category
        if "prompts" in category_data:
            for i, prompt in enumerate(category_data["prompts"]):
                # Add slight extra left padding to prompts for clarity
                self.tree.insert(cat_id, "end", text=f"  💡 {prompt['title']}", 
                               values=("prompt", current_path, i))
        
        # Add subcategories
        if "subcategories" in category_data:
            for sub_name, sub_data in category_data["subcategories"].items():
                self._add_category_to_tree(cat_id, sub_name, sub_data, current_path)

    def _show_tree_context_menu(self, event):
        try:
            clicked_item = self.tree.identify_row(event.y)
            clicked_vals = None
            if clicked_item:
                try:
                    self.tree.selection_set(clicked_item)
                    self.tree.focus(clicked_item)
                except Exception:
                    pass
                try:
                    clicked_vals = self.tree.item(clicked_item, "values")
                except Exception:
                    clicked_vals = None
                try:
                    self.on_tree_select(None)
                except Exception:
                    pass

            delete_label = "🗑️ Delete"
            if clicked_vals and clicked_vals[0] == "category":
                delete_label = "🗑️ Delete Category..."
            elif clicked_vals and clicked_vals[0] == "prompt":
                delete_label = "🗑️ Delete Prompt..."

            menu = tk.Menu(self.window, tearoff=0)
            menu.add_command(label="➕ Add Top-Level Category", command=self.add_category_top_level)
            menu.add_command(label="➕ Add Subcategory", command=self.add_category)
            menu.add_command(label="➕ Add Prompt", command=self.add_prompt)
            menu.add_separator()
            menu.add_command(label="✏️ Rename", command=self.rename_selected)
            menu.add_command(label=delete_label, command=self.delete_selected)
            menu.add_separator()
            menu.add_command(label="📦 Move To...", command=self.move_selected_to)
            # Reorder actions for both prompts and categories
            menu.add_command(label="⬆ Move Up", command=self.move_selected_up)
            menu.add_command(label="⬇ Move Down", command=self.move_selected_down)
            menu.add_separator()
            menu.add_command(label="🖱️ Drag & Drop", command=self._show_drag_drop_help)
            menu.add_separator()
            menu.add_command(label="📄 Duplicate", command=self.duplicate_selected)
            menu.add_command(label="↕ Sort Siblings A→Z", command=self.sort_siblings_alpha)
            menu.add_separator()
            menu.add_command(label="✎ Bulk: Add/Remove Tags", command=self.bulk_edit_tags)
            menu.add_command(label="✎ Bulk: Find/Replace in Titles", command=self.bulk_find_replace_titles)
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def _show_drag_drop_help(self):
        """Show help message about drag and drop functionality"""
        try:
            messagebox.showinfo(
                "Drag & Drop Guide",
                "💡 Drag & Drop Instructions:\n\n"
                "• Click and drag any item to move it\n"
                "• Items will jump live while you drag so order is clear\n"
                "• Drop on categories to move inside them\n"
                "• Drop above/below items to reorder\n"
                "• Hold and drag to start moving\n\n"
                "Alternative: Use keyboard shortcuts\n"
                "• Alt+Up/Down to move items\n"
                "• Ctrl+Shift+M to move to different category",
                parent=self.window
            )
        except Exception:
            pass

    def _on_tree_open(self, event=None):
        try:
            item = self.tree.focus()
            vals = self.tree.item(item, "values")
            if vals and vals[0] == "category":
                self.expanded_paths.add(vals[1])
                self._persist_expanded_paths()
        except Exception:
            pass

    def _on_tree_close(self, event=None):
        try:
            item = self.tree.focus()
            vals = self.tree.item(item, "values")
            if vals and vals[0] == "category":
                self.expanded_paths.discard(vals[1])
                self._persist_expanded_paths()
        except Exception:
            pass

    def _persist_expanded_paths(self):
        try:
            self.parent.settings["editor_expanded_paths"] = sorted(list(self.expanded_paths))
            self.parent.save_settings()
        except Exception:
            pass

    def rename_selected(self):
        try:
            selection = self.tree.selection()
            if not selection:
                return
            self._push_undo()
            item = selection[0]
            vals = self.tree.item(item, "values")
            if not vals:
                return
            if vals[0] == "category":
                path = vals[1]
                old_name = path.split("/")[-1]
                new_name = self.parent._ask_string_modal(self.window, "Rename Category", "New category name:", initial_value=old_name)
                if not new_name or new_name == old_name:
                    return
                self._rename_category_by_path(path, new_name)
                self.populate_tree()
            elif vals[0] == "prompt":
                path = vals[1]
                idx = int(vals[2])
                prompt = self._get_prompt_by_path(path, idx)
                old_title = prompt.get("title", "")
                new_title = self.parent._ask_string_modal(self.window, "Rename Prompt", "New prompt title:", initial_value=old_title)
                if not new_title or new_title == old_title:
                    return
                cat = self._get_category_by_path(path)
                cat["prompts"][idx]["title"] = new_title
                self.populate_tree()
        except Exception:
            pass

    def _rename_category_by_path(self, category_path, new_name):
        parts = category_path.split("/")
        if len(parts) == 1:
            cats = self.prompts.setdefault("categories", {})
            if new_name in cats:
                messagebox.showerror("Rename", "A category with that name already exists.")
                return
            cats[new_name] = cats.pop(parts[0])
            # Update expanded paths
            self.expanded_paths = {new_name if p == parts[0] else (p.replace(parts[0] + "/", new_name + "/") if p.startswith(parts[0] + "/") else p) for p in self.expanded_paths}
        else:
            parent_path = "/".join(parts[:-1])
            parent = self._get_category_by_path(parent_path)
            sub = parent.setdefault("subcategories", {})
            if new_name in sub:
                messagebox.showerror("Rename", "A subcategory with that name already exists.")
                return
            sub[new_name] = sub.pop(parts[-1])
            # Update expanded paths
            old_prefix = category_path
            new_prefix = parent_path + "/" + new_name
            updated = set()
            for p in self.expanded_paths:
                if p == old_prefix:
                    updated.add(new_prefix)
                elif p.startswith(old_prefix + "/"):
                    updated.add(p.replace(old_prefix + "/", new_prefix + "/", 1))
                else:
                    updated.add(p)
            self.expanded_paths = updated
        self._persist_expanded_paths()

    def apply_tree_filter(self):
        try:
            q = (self.search_var.get() or "").strip().lower()
            if not q:
                self._filtered_data = None
                self.populate_tree()
                return
            self._filtered_data = {"categories": {}}
            for name, data in self.prompts.get("categories", {}).items():
                filtered = self._filter_category_recursive(name, data, q)
                if filtered:
                    self._filtered_data["categories"][name] = filtered
            self.populate_tree()
        except Exception:
            pass

    def _filter_category_recursive(self, name, data, q):
        try:
            name_match = name.lower().find(q) != -1
            result = {}
            # Filter prompts
            prompts = []
            for p in data.get("prompts", []) if isinstance(data, dict) else []:
                title = str(p.get("title", ""))
                note = str(p.get("note", ""))
                if q in title.lower() or q in note.lower():
                    prompts.append(p)
            # Filter subcategories
            subs_result = {}
            subs = data.get("subcategories", {}) if isinstance(data, dict) else {}
            for sub_name, sub_data in subs.items():
                sub_filtered = self._filter_category_recursive(sub_name, sub_data, q)
                if sub_filtered:
                    subs_result[sub_name] = sub_filtered
            if name_match or prompts or subs_result:
                if prompts:
                    result["prompts"] = prompts
                if subs_result:
                    result["subcategories"] = subs_result
                if not prompts and not subs_result:
                    # Only name matched; include as-is
                    result = data
                return result
            return None
        except Exception:
            return None
                               
    def on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item, "values")
        
        if values[0] == "prompt":
            # Load prompt for editing
            category_path = values[1]
            prompt_index = int(values[2])
            prompt = self._get_prompt_by_path(category_path, prompt_index)
            
            self.current_item = item
            self.current_category_path = category_path
            self.current_index = prompt_index
            
            self.title_var.set(prompt["title"])
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", prompt["prompt"])
            tags_val = ", ".join(prompt.get("tags", [])) if isinstance(prompt.get("tags"), list) else str(prompt.get("tags", ""))
            self.tags_var.set(tags_val)
            self.note_var.set(str(prompt.get("note", "")))
            try:
                self.cat_color_section.pack_forget()
            except Exception:
                pass
        else:
            # Category selected
            self.current_item = None
            self.title_var.set("")
            self.prompt_text.delete("1.0", tk.END)
            self.tags_var.set("")
            self.note_var.set("")
            # Show category color controls
            try:
                # Determine category path
                cat_path = values[1]
                cat_obj = self._get_category_by_path(cat_path)
                self.cat_color_var.set(cat_obj.get("color", "#222222"))
                self.cat_color_section.pack(fill="x")
            except Exception:
                pass

        # Initialize selection anchor if not set
        try:
            if not getattr(self, "_selection_anchor", None):
                self._selection_anchor = self.tree.selection()[0]
        except Exception:
            pass
    
    def _get_prompt_by_path(self, category_path, prompt_index):
        """Get a prompt by its category path and index"""
        path_parts = category_path.split("/")
        current = self.prompts["categories"]
        
        # Navigate to the correct category
        for i, part in enumerate(path_parts):
            if i == 0:
                current = current[part]
            else:
                current = current["subcategories"][part]
        
        return current["prompts"][prompt_index]
    
    def _get_category_by_path(self, category_path):
        """Get a category object by its path"""
        path_parts = category_path.split("/")
        current = self.prompts["categories"]
        
        # Navigate to the correct category
        for i, part in enumerate(path_parts):
            if i == 0:
                current = current[part]
            else:
                current = current["subcategories"][part]
        
        return current

    def _ensure_category_path_exists(self, category_path):
        """Ensure a category path like 'Root/Sub/Sub2' exists; create as needed."""
        if not category_path:
            return
        parts = [p for p in category_path.split("/") if p]
        if not parts:
            return
        current = self.prompts.setdefault("categories", {})
        for i, part in enumerate(parts):
            if i == 0:
                if part not in current or not isinstance(current.get(part), dict):
                    current[part] = {"prompts": []}
                current = current[part]
            else:
                if "subcategories" not in current or not isinstance(current.get("subcategories"), dict):
                    current["subcategories"] = {}
                if part not in current["subcategories"] or not isinstance(current["subcategories"].get(part), dict):
                    current["subcategories"][part] = {"prompts": []}
                current = current["subcategories"][part]

    def _list_all_category_paths(self):
        """Return a flat list of all category paths like 'Root', 'Root/Sub', ... preserving order."""
        paths = []
        def recurse(cat_dict, prefix=None):
            if not isinstance(cat_dict, dict):
                return
            for name, data in cat_dict.items():
                current = name if not prefix else f"{prefix}/{name}"
                paths.append(current)
                sub = data.get("subcategories", {}) if isinstance(data, dict) else {}
                recurse(sub, current)
        try:
            recurse(self.prompts.get("categories", {}))
        except Exception:
            return list(self.prompts.get("categories", {}).keys())
        return paths
        
    def add_category_top_level(self):
        """Add a new top-level category regardless of current selection."""
        self._push_undo()
        name = self.parent._ask_string_modal(self.window, "New Category", "Enter category name:")
        if not name:
            return
        if name in self.prompts.get("categories", {}):
            messagebox.showerror("Error", "Category already exists!")
            return
        try:
            self.prompts.setdefault("categories", {})[name] = {"prompts": []}
            self.populate_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add category: {e}")
            
    def add_category(self):
        """Add a new category with enhanced nesting support"""
        self._push_undo()
        # Get selected item to determine where to add
        selection = self.tree.selection()
        parent_path = ""
        parent_name = "root"
        
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            if values[0] == "category":
                parent_path = values[1]
                parent_name = values[1].split("/")[-1] if "/" in values[1] else values[1]
            elif values[0] == "prompt":
                parent_path = values[1]  # Get category path from prompt
                parent_name = values[1].split("/")[-1] if "/" in values[1] else values[1]
        
        # Enhanced dialog for category creation
        dlg = tk.Toplevel(self.window)
        dlg.title("Add Category")
        dlg.geometry("400x200")
        dlg.resizable(False, False)
        
        try:
            self.parent._apply_window_icon(dlg)
            dlg.transient(self.window)
            dlg.attributes("-topmost", True)
            self.parent._center_window(dlg, self.window)
        except Exception:
            pass
        
        bg = self.parent.settings["theme"]["background"]
        fg = self.parent.settings["theme"]["foreground"]
        accent = self.parent.settings["theme"]["accent"]
        dlg.configure(bg=bg)
        
        # Main frame
        main_frame = tk.Frame(dlg, bg=bg)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Parent info
        parent_label = tk.Label(main_frame, text=f"Adding to: {parent_name}", 
                               bg=bg, fg=fg, font=("Segoe UI", 9))
        parent_label.pack(pady=(0, 10))
        
        # Category name input
        tk.Label(main_frame, text="Category Name:", bg=bg, fg=fg, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        name_var = tk.StringVar()
        name_entry = tk.Entry(main_frame, textvariable=name_var, bg=accent, fg=fg, 
                             font=("Segoe UI", 10), relief="flat")
        name_entry.pack(fill="x", pady=(5, 15))
        name_entry.focus()
        
        # Location options
        location_frame = tk.Frame(main_frame, bg=bg)
        location_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(location_frame, text="Location:", bg=bg, fg=fg, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        location_var = tk.StringVar(value="subcategory")
        if not parent_path:
            location_var.set("top")
            tk.Radiobutton(location_frame, text="Top Level Category", value="top", 
                          variable=location_var, bg=bg, fg=fg, selectcolor=accent).pack(anchor="w", pady=2)
        else:
            tk.Radiobutton(location_frame, text=f"Subcategory of '{parent_name}'", value="subcategory", 
                          variable=location_var, bg=bg, fg=fg, selectcolor=accent).pack(anchor="w", pady=2)
            tk.Radiobutton(location_frame, text="Top Level Category", value="top", 
                          variable=location_var, bg=bg, fg=fg, selectcolor=accent).pack(anchor="w", pady=2)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=bg)
        button_frame.pack(fill="x", pady=(10, 0))
        
        def create_category():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a category name!")
                return

            # Validate category name
            if not validate_input(name, max_length=100):
                messagebox.showerror("Error", "Invalid category name! Contains invalid characters or is too long.")
                return

            # Sanitize category name
            clean_name = sanitize_filename(name)
            if clean_name == "unnamed" or clean_name != name:
                messagebox.showerror("Error", "Category name contains invalid characters!")
                return
            
            try:
                if location_var.get() == "top":
                    # Add to root level
                    if clean_name in self.prompts.get("categories", {}):
                        messagebox.showerror("Error", "Category already exists!")
                        return
                    self.prompts.setdefault("categories", {})[clean_name] = {"prompts": []}
                else:
                    # Add as subcategory
                    if not parent_path:
                        messagebox.showerror("Error", "No parent category selected!")
                        return
                    parent_category = self._get_category_by_path(parent_path)
                    if "subcategories" not in parent_category:
                        parent_category["subcategories"] = {}
                    
                    if name in parent_category["subcategories"]:
                        messagebox.showerror("Error", "Subcategory already exists!")
                        return
                    parent_category["subcategories"][name] = {"prompts": []}
                    
                self.populate_tree()
                dlg.destroy()
                self._autosave()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add category: {e}")
        
        def cancel():
            dlg.destroy()
        
        tk.Button(button_frame, text="Cancel", command=cancel, bg="#666666", fg="white", 
                 relief="flat", width=10).pack(side="right", padx=(5, 0))
        tk.Button(button_frame, text="Create", command=create_category, bg="#4CAF50", fg="white", 
                 relief="flat", width=10).pack(side="right")
        
        # Bind Enter key
        name_entry.bind("<Return>", lambda e: create_category())
        dlg.bind("<Escape>", lambda e: cancel())
            
    def add_prompt(self):
        """Add a new prompt"""
        self._push_undo()
        # Get selected category or ask for one
        selection = self.tree.selection()
        category_path = None
        
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            if values[0] == "category":
                category_path = values[1]
            elif values[0] == "prompt":
                category_path = values[1]
                
        if not category_path:
            categories = list(self.prompts["categories"].keys())
            if not categories:
                messagebox.showerror("Error", "Please create a category first!")
                return
            category_path = categories[0]  # Default to first category
            
        # Create new prompt
        new_prompt = {"title": "New Prompt", "prompt": "Enter your prompt here...", "tags": [], "note": ""}
        category = self._get_category_by_path(category_path)
        if "prompts" not in category:
            category["prompts"] = []
        category["prompts"].append(new_prompt)
        self.populate_tree()
        
        # Find and select the new prompt
        self._select_newest_prompt(category_path)
    
    def _select_newest_prompt(self, category_path):
        """Find and select the newest prompt in the given category"""
        def search_tree(item, path):
            values = self.tree.item(item, "values")
            if values[0] == "category" and values[1] == path:
                children = self.tree.get_children(item)
                prompt_children = [child for child in children 
                                 if self.tree.item(child, "values")[0] == "prompt"]
                if prompt_children:
                    self.tree.selection_set(prompt_children[-1])
                    self.on_tree_select(None)
                    return True
            
            for child in self.tree.get_children(item):
                if search_tree(child, path):
                    return True
            return False
        
        # Search through all top-level items
        for item in self.tree.get_children():
            if search_tree(item, category_path):
                break
                
    def edit_selected(self, event=None):
        """Edit the selected item"""
        if self.current_item:
            self.title_entry.focus()
            # Auto-highlight the title text
            self.title_entry.select_range(0, tk.END)
            self.title_entry.icursor(tk.END)
            
    def _count_prompts_in_category(self, category_obj):
        """Return number of prompts in a category, including nested subcategories."""
        if not isinstance(category_obj, dict):
            return 0
        count = len(category_obj.get("prompts", []) or [])
        sub = category_obj.get("subcategories", {})
        if isinstance(sub, dict):
            for sub_obj in sub.values():
                count += self._count_prompts_in_category(sub_obj)
        return count

    def delete_selected(self, confirm=True):
        """Delete selected items and keep an Undo snapshot."""
        selection = self.tree.selection()
        if not selection:
            return
        # Partition into categories and prompts
        categories = []
        prompts = {}
        for item in selection:
            values = self.tree.item(item, "values")
            if not values:
                continue
            if values[0] == "category":
                categories.append(values[1])
            elif values[0] == "prompt":
                prompts.setdefault(values[1], []).append(int(values[2]))

        if not categories and not prompts:
            return

        # If a category is selected, ignore explicit prompt selections inside it.
        if categories and prompts:
            kept = {}
            for cat_path, idxs in prompts.items():
                covered = False
                for selected_cat in categories:
                    if cat_path == selected_cat or cat_path.startswith(selected_cat + "/"):
                        covered = True
                        break
                if not covered:
                    kept[cat_path] = idxs
            prompts = kept

        prompt_count = sum(len(set(idxs)) for idxs in prompts.values())
        category_count = len(categories)
        category_prompt_count = 0
        for cat_path in categories:
            try:
                category_prompt_count += self._count_prompts_in_category(self._get_category_by_path(cat_path))
            except Exception:
                pass

        if confirm:
            msg = "Delete selected items?"
            if category_count and prompt_count:
                msg = (
                    f"Delete {category_count} categor{'y' if category_count == 1 else 'ies'} and "
                    f"{prompt_count} prompt{'s' if prompt_count != 1 else ''}?\n\n"
                    f"This will also delete {category_prompt_count} prompt"
                    f"{'' if category_prompt_count == 1 else 's'} inside the selected categor"
                    f"{'y' if category_count == 1 else 'ies'}."
                )
            elif category_count:
                msg = (
                    f"Delete {category_count} categor{'y' if category_count == 1 else 'ies'}?\n\n"
                    f"This will permanently delete {category_prompt_count} prompt"
                    f"{'' if category_prompt_count == 1 else 's'} in those categor"
                    f"{'y' if category_count == 1 else 'ies'}."
                )
            elif prompt_count:
                msg = f"Delete {prompt_count} prompt{'s' if prompt_count != 1 else ''}?"

            if not messagebox.askyesno("Confirm Delete", msg, icon="warning", parent=self.window):
                return

        self._push_undo()

        # Capture snapshot for Undo
        last_deleted = {"prompts": [], "categories": []}
        try:
            # Capture prompts to be deleted
            for cat_path, idxs in prompts.items():
                cat = self._get_category_by_path(cat_path)
                for idx in sorted(idxs):
                    try:
                        p = cat.get("prompts", [])[idx]
                        last_deleted["prompts"].append((cat_path, idx, copy.deepcopy(p)))
                    except Exception:
                        pass
            # Capture full category objects (deep copy)
            for cat_path in categories:
                try:
                    cat_obj = copy.deepcopy(self._get_category_by_path(cat_path))
                    last_deleted["categories"].append((cat_path, cat_obj))
                except Exception:
                    pass
        except Exception:
            pass

        # Perform deletion: prompts first (reverse index order per category), then categories
        for cat_path, idxs in prompts.items():
            cat = self._get_category_by_path(cat_path)
            for idx in sorted(idxs, reverse=True):
                try:
                    if 0 <= idx < len(cat.get("prompts", [])):
                        del cat["prompts"][idx]
                except Exception:
                    pass
        for cat_path in sorted(categories, key=lambda p: p.count('/'), reverse=True):
            try:
                self._delete_category_by_path(cat_path)
            except Exception:
                pass
        self.populate_tree()
        # Store snapshot and show toast with Undo
        self._last_deleted = last_deleted
        try:
            self.show_toast("Deleted. Undo?", kind="warning", undo_callback=self.undo_last_delete, duration=5000)
        except Exception:
            pass
    
    def _delete_category_by_path(self, category_path):
        """Delete a category by its path"""
        path_parts = category_path.split("/")
        
        if len(path_parts) == 1:
            # Delete root category
            del self.prompts["categories"][path_parts[0]]
        else:
            # Delete subcategory
            parent_path = "/".join(path_parts[:-1])
            parent_category = self._get_category_by_path(parent_path)
            del parent_category["subcategories"][path_parts[-1]]

    def undo_last_delete(self):
        try:
            data = getattr(self, "_last_deleted", None)
            if not data:
                return
            # Restore categories first
            for cat_path, cat_obj in data.get("categories", []):
                self._restore_category_object_at_path(cat_path, cat_obj)
            # Then restore prompts
            for cat_path, idx, prompt_obj in data.get("prompts", []):
                try:
                    cat = self._get_category_by_path(cat_path)
                    lst = cat.setdefault("prompts", [])
                    insert_at = idx if 0 <= idx <= len(lst) else len(lst)
                    lst.insert(insert_at, prompt_obj)
                except Exception:
                    pass
            self.populate_tree()
            self._last_deleted = None
            self.show_toast("Restored", kind="success", duration=2000)
        except Exception:
            pass

    def _restore_category_object_at_path(self, category_path, category_obj):
        try:
            parts = category_path.split("/")
            if len(parts) == 1:
                self.prompts.setdefault("categories", {})[parts[0]] = category_obj
                return
            parent_path = "/".join(parts[:-1])
            parent = self._get_category_by_path(parent_path)
            parent.setdefault("subcategories", {})[parts[-1]] = category_obj
        except Exception:
            # If parent path missing, create chain
            try:
                parent_path = "/".join(category_path.split("/")[:-1])
                self._ensure_category_path_exists(parent_path)
                parent = self._get_category_by_path(parent_path)
                parent.setdefault("subcategories", {})[category_path.split("/")[-1]] = category_obj
            except Exception:
                pass

    # Toast notifications
    def show_toast(self, message, kind="info", undo_callback=None, duration=3000):
        try:
            # Destroy existing toast
            try:
                self._destroy_toast()
            except Exception:
                pass
            colors = {
                "success": ("#16a34a", "white"),
                "warning": ("#f59e0b", "#111111"),
                "error": ("#ef4444", "white"),
                "info": (self.parent.settings["theme"].get("accent", "#333333"), self.parent.settings["theme"].get("foreground", "#ffffff"))
            }
            bg, fg = colors.get(kind, colors["info"])
            frame = tk.Frame(self.window, bg=bg)
            label = tk.Label(frame, text=message, bg=bg, fg=fg, font=("Segoe UI", 9))
            label.pack(side="left", padx=(10, 8), pady=8)
            if undo_callback:
                undo = tk.Label(frame, text="Undo", bg=bg, fg=fg, font=("Segoe UI", 9, "bold"), cursor="hand2")
                undo.pack(side="right", padx=(0, 10))
                undo.bind("<Button-1>", lambda e: (undo_callback(), self._destroy_toast()))
            # Border
            try:
                frame.configure(highlightbackground=self.parent.settings["theme"].get("border", "#3a3a3a"), highlightthickness=1)
            except Exception:
                pass
            frame.update_idletasks()
            self._toast = frame
            # Place bottom-right, lifted above status area and away from Save button
            # Slightly higher and more right margin to avoid overlap with footer save area
            frame.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-80)
            # Auto-hide faster for delete undo prompts
            if undo_callback and kind == "warning" and duration > 2000:
                duration = 2000
            self._toast_after = self.window.after(max(1200, duration), self._destroy_toast)
        except Exception:
            pass

    def _destroy_toast(self):
        try:
            if hasattr(self, "_toast_after") and self._toast_after:
                self.window.after_cancel(self._toast_after)
        except Exception:
            pass
        try:
            if hasattr(self, "_toast") and self._toast is not None:
                self._toast.destroy()
        except Exception:
            pass
        self._toast = None
        self._toast_after = None
                
    def save_current(self):
        """Save the currently edited prompt"""
        if not self.current_item:
            return
        # Capture undo snapshot before applying changes
        self._push_undo()
            
        title = self.title_var.get().strip()
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        tags_raw = self.tags_var.get().strip()
        note = self.note_var.get().strip()

        # Validate input data (keep this permissive; prompts/tags/notes are free-form text)
        try:
            if "\x00" in title or "\x00" in prompt or "\x00" in tags_raw or "\x00" in note:
                messagebox.showerror("Error", "Invalid text (contains null bytes).")
                return
        except Exception:
            pass

        if len(title) > 200:
            messagebox.showerror("Error", "Title is too long (max 200 characters).")
            return
        if len(prompt) > 50000:
            messagebox.showerror("Error", "Prompt is too long (max 50,000 characters).")
            return
        if tags_raw and len(tags_raw) > 500:
            messagebox.showerror("Error", "Tags are too long (max 500 characters).")
            return
        if note and len(note) > 2000:
            messagebox.showerror("Error", "Note is too long (max 2,000 characters).")
            return

        # Sanitize tags
        tags = []
        if tags_raw:
            for t in tags_raw.split(","):
                clean_tag = sanitize_filename(t.strip())
                if clean_tag and clean_tag != "unnamed":
                    tags.append(clean_tag)

        if not title or not prompt:
            messagebox.showerror("Error", "Title and prompt cannot be empty!")
            return
        
        # Update the prompt using the path-based access (preserve existing metadata like id/usage_count)
        category = self._get_category_by_path(self.current_category_path)
        try:
            existing = category["prompts"][self.current_index]
        except Exception:
            existing = None
        if isinstance(existing, dict):
            existing.update({
                "title": title,
                "prompt": prompt,
                "tags": tags,
                "note": note
            })
            category["prompts"][self.current_index] = existing
        else:
            category["prompts"][self.current_index] = {
                "title": title,
                "prompt": prompt,
                "tags": tags,
                "note": note
            }
        
        # Persist immediately
        try:
            self._autosave_now()
        except Exception:
            pass

        # Update tree display
        self.tree.item(self.current_item, text=f"💡 {title}")

        # Visual feedback on the save button instead of dialog boxes
        if hasattr(self, "save_btn"):
            original_bg = self.save_btn.cget("bg")
            original_text = self.save_btn.cget("text")
            self.save_btn.configure(bg="#66bb6a", text="✔ Saved")
            # Revert after 1 second
            self.save_btn.after(1000, lambda: self.save_btn.configure(bg=original_bg, text=original_text))
        # Non-blocking toast
        try:
            self.show_toast("Saved", kind="success", duration=2000)
        except Exception:
            pass

    def _autosave_now(self):
        try:
            self.parent.prompts = self.prompts
            # Ensure stable IDs exist for new/edited items before persisting
            try:
                if hasattr(self.parent, "_ensure_stable_ids"):
                    self.parent._ensure_stable_ids()
            except Exception:
                pass
            if hasattr(self.parent, "autosave_prompts_with_backup"):
                self.parent.autosave_prompts_with_backup()
            else:
                self.parent.save_prompts()
        except Exception:
            pass

    def _push_undo(self):
        try:
            self._undo_stack.append(copy.deepcopy(self.prompts))
            if len(self._undo_stack) > 20:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
        except Exception:
            pass

    def undo(self):
        try:
            if not self._undo_stack:
                return
            self._redo_stack.append(copy.deepcopy(self.prompts))
            self.prompts = self._undo_stack.pop()
            self.populate_tree()
        except Exception:
            pass

    def redo(self):
        try:
            if not self._redo_stack:
                return
            self._undo_stack.append(copy.deepcopy(self.prompts))
            self.prompts = self._redo_stack.pop()
            self.populate_tree()
        except Exception:
            pass
        
    def revert_current(self):
        """Revert current changes"""
        if self.current_item:
            self.on_tree_select(None)
            
    def save_and_close(self):
        """Save all changes and close"""
        # Save current prompt if editing
        if self.current_item:
            try:
                self.save_current()
            except:
                pass  # Continue even if current save fails
                
        # Save to parent and file
        self.parent.prompts = self.prompts
        try:
            if hasattr(self.parent, "_ensure_stable_ids"):
                self.parent._ensure_stable_ids()
        except Exception:
            pass
        self.parent.save_prompts()
        
        messagebox.showinfo("Success", "All prompts saved successfully!")
        self._on_close()

    def _on_close(self):
        """Close the prompt editor and clear parent reference"""
        try:
            if hasattr(self.parent, "prompt_editor"):
                self.parent.prompt_editor = None
        except Exception:
            pass
        try:
            self.window.destroy()
        except Exception:
            pass

    def apply_category_color(self):
        try:
            if not self.tree.selection():
                return
            item = self.tree.selection()[0]
            values = self.tree.item(item, "values")
            if values[0] != "category":
                return
            cat_path = values[1]
            cat_obj = self._get_category_by_path(cat_path)
            color = colorchooser.askcolor(color=self.cat_color_var.get())
            if color[1]:
                cat_obj["color"] = color[1]
                self.cat_color_var.set(color[1])
                # Reflect to parent UI immediately
                self.parent.prompts = self.prompts
                self.parent.save_prompts()
                try:
                    # If drawer is open, repopulate to reflect colors
                    if self.parent.expanded:
                        self.parent.populate_prompts(self.parent.search_var.get() if hasattr(self.parent, "search_var") else "")
                except Exception:
                    pass
        except Exception:
            pass

    def move_selected_to(self):
        """Open a themed dropdown dialog to move selected items to a category path.
        Supports both prompts and categories with enhanced nesting capabilities.
        """
        try:
            self._push_undo()
            sels = self.tree.selection()
            if not sels:
                return
            
            # Collect selected items (both prompts and categories)
            selected_prompts = []
            selected_categories = []
            
            for item in sels:
                vals = self.tree.item(item, "values")
                if vals and vals[0] == "prompt":
                    src_path = vals[1]
                    try:
                        idx = int(vals[2])
                        selected_prompts.append((src_path, idx))
                    except Exception:
                        continue
                elif vals and vals[0] == "category":
                    src_path = vals[1]
                    selected_categories.append(src_path)
            
            if not selected_prompts and not selected_categories:
                messagebox.showinfo("Move", "Please select prompts or categories to move.")
                return

            # Build list of categories for dropdown (toggle top-level vs full paths)
            top_level = list(self.prompts.get("categories", {}).keys())
            full_paths = self._list_all_category_paths()
            all_paths = top_level[:]
            
            # Filter out source categories if moving categories
            if selected_categories:
                # Remove source categories and their descendants from target list
                filtered_paths = []
                for path in full_paths:
                    is_valid_target = True
                    for src_cat in selected_categories:
                        if path == src_cat or path.startswith(src_cat + "/"):
                            is_valid_target = False
                            break
                    if is_valid_target:
                        filtered_paths.append(path)
                full_paths = filtered_paths
                all_paths = [p for p in top_level if p not in selected_categories]
            
            if not all_paths:
                messagebox.showerror("Move", "No valid target categories available.")
                return

            # Dialog UI
            item_type = "Categories" if selected_categories else "Prompts"
            dlg = tk.Toplevel(self.window)
            dlg.title(f"Move {item_type}")
            try:
                self.parent._apply_window_icon(dlg)
            except Exception:
                pass
            try:
                dlg.transient(self.window)
            except Exception:
                pass
            dlg.attributes("-topmost", True)
            try:
                dlg.lift()
                dlg.focus_force()
            except Exception:
                pass
            try:
                self.parent._center_window(dlg, self.window)
            except Exception:
                pass
            bg = self.parent.settings["theme"]["background"]
            fg = self.parent.settings["theme"]["foreground"]
            accent = self.parent.settings["theme"]["accent"]
            border = self.parent.settings["theme"].get("border", "#3a3a3a")
            dlg.configure(bg=bg)
            try:
                dlg.configure(highlightbackground=border, highlightthickness=1)
            except Exception:
                pass

            frm = tk.Frame(dlg, bg=bg)
            frm.pack(fill="both", expand=True, padx=12, pady=12)

            # Toggle row for nested or top-level
            toggle_row = tk.Frame(frm, bg=bg)
            toggle_row.pack(fill="x", pady=(0, 6))
            tk.Label(toggle_row, text="Target category:", bg=bg, fg=fg, font=("Segoe UI", 10, "bold")).pack(side="left")
            mode_var = tk.StringVar(value="nested" if selected_categories else "top")
            def refresh_combo():
                values = top_level if mode_var.get() == "top" else full_paths
                combo.configure(values=values)
                if values:
                    combo_var.set(values[0])
            ttk.Radiobutton(toggle_row, text="Top Level", value="top", variable=mode_var, command=refresh_combo).pack(side="right")
            ttk.Radiobutton(toggle_row, text="Nested", value="nested", variable=mode_var, command=refresh_combo).pack(side="right", padx=(0,6))

            # Combobox with category paths
            combo_var = tk.StringVar(value=all_paths[0])
            combo = ttk.Combobox(frm, textvariable=combo_var, values=all_paths, state="readonly", width=42)
            combo.pack(fill="x", pady=(6, 6))

            # Inline new category creation
            new_row = tk.Frame(frm, bg=bg)
            new_row.pack(fill="x", pady=(0, 10))
            tk.Label(new_row, text="or create:", bg=bg, fg=fg).pack(side="left")
            new_var = tk.StringVar()
            new_entry = tk.Entry(new_row, textvariable=new_var, bg=accent, fg=fg, relief="flat")
            new_entry.pack(side="left", fill="x", expand=True, padx=(6,6))
            def create_path():
                path = new_var.get().strip()
                if not path:
                    return
                # Accept either simple names (uses selection as parent) or full Parent/Sub path
                parent = combo_var.get().strip()
                full = path if ("/" in path or mode_var.get() == "nested" and not parent) else (f"{parent}/{path}" if parent else path)
                self._ensure_category_path_exists(full)
                # Refresh choices
                nonlocal full_paths, top_level
                top_level = list(self.prompts.get("categories", {}).keys())
                full_paths = self._list_all_category_paths()
                refresh_combo()
                combo_var.set(full)
                new_var.set("")
            tk.Button(new_row, text="Add", command=create_path, bg="#4CAF50", fg="white", relief="flat", width=8).pack(side="right")

            # Buttons row
            btn_row = tk.Frame(frm, bg=bg)
            btn_row.pack(fill="x")

            def do_ok(event=None):
                try:
                    target = combo_var.get().strip()
                    if not target:
                        return
                    
                    # Handle moving prompts
                    if selected_prompts:
                        # Collect prompt objects first, grouped by source to avoid index drift
                        moves = []
                        for src_path, idx in selected_prompts:
                            try:
                                src_cat = self._get_category_by_path(src_path)
                                p = src_cat["prompts"][idx]
                                moves.append((src_path, idx, p))
                            except Exception:
                                continue
                        # Remove from sources in reverse-index order per source path
                        by_src = {}
                        for sp, idx, p in moves:
                            by_src.setdefault(sp, []).append((idx, p))
                        for sp, lst in by_src.items():
                            lst.sort(key=lambda t: t[0], reverse=True)
                            src_cat = self._get_category_by_path(sp)
                            for i, _p in lst:
                                try:
                                    src_cat["prompts"].pop(i)
                                except Exception:
                                    pass
                        # Append to destination
                        # Ensure target exists (in case user typed a new path)
                        self._ensure_category_path_exists(target)
                        dst_cat = self._get_category_by_path(target)
                        if "prompts" not in dst_cat:
                            dst_cat["prompts"] = []
                        for _sp, _i, p in moves:
                            dst_cat["prompts"].append(p)
                    
                    # Handle moving categories
                    if selected_categories:
                        for src_cat_path in selected_categories:
                            try:
                                # Get source category info
                                src_is_top, src_container, src_parent, src_name, src_parent_path = self._get_category_container_info(src_cat_path)
                                src_data = src_container[src_name]
                                
                                # Determine destination
                                if mode_var.get() == "top":
                                    # Move to top level
                                    dst_container = self.prompts.setdefault("categories", {})
                                    new_path = src_name
                                else:
                                    # Move as subcategory
                                    self._ensure_category_path_exists(target)
                                    dst_parent = self._get_category_by_path(target)
                                    dst_container = dst_parent.setdefault("subcategories", {})
                                    new_path = f"{target}/{src_name}"
                                
                                # Remove from source
                                del src_container[src_name]
                                
                                # Add to destination
                                dst_container[src_name] = src_data
                                
                            except Exception as e:
                                print(f"Error moving category {src_cat_path}: {e}")
                    
                    self.populate_tree()
                    dlg.destroy()
                    self._autosave()
                    
                except Exception as e:
                    messagebox.showerror("Move", f"Failed to move: {e}")

            def do_cancel(event=None):
                try:
                    dlg.destroy()
                except Exception:
                    pass

            ok_btn = tk.Button(btn_row, text="Move", command=do_ok, bg="#2563eb", fg="white", relief="flat", width=10)
            ok_btn.pack(side="right")
            cancel_btn = tk.Button(btn_row, text="Cancel", command=do_cancel, bg=self.parent.settings["theme"]["button_bg"], fg=fg, relief="flat", width=10)
            cancel_btn.pack(side="right", padx=(0, 8))

            # Keyboard shortcuts
            try:
                dlg.bind("<Return>", do_ok)
                dlg.bind("<Escape>", do_cancel)
                dlg.bind("<Control-w>", do_cancel)
            except Exception:
                pass
            try:
                combo.focus_set()
            except Exception:
                pass
            try:
                dlg.grab_set()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Move", f"Failed to move: {e}")

    def move_selected_up(self):
        try:
            self._push_undo()
            sels = list(self.tree.selection())
            if not sels:
                return
            # Separate selections into prompts and categories
            prompts_by_path = {}
            selected_category_paths = []
            for item in sels:
                vals = self.tree.item(item, "values")
                if not vals:
                    continue
                if vals[0] == "prompt":
                    path = vals[1]
                    try:
                        idx = int(vals[2])
                    except Exception:
                        continue
                    cat = self._get_category_by_path(path)
                    try:
                        p_obj = cat.get("prompts", [])[idx]
                    except Exception:
                        continue
                    prompts_by_path.setdefault(path, []).append((idx, p_obj))
                elif vals[0] == "category":
                    selected_category_paths.append(vals[1])

            prompt_keys_after_move = []

            # Move prompt blocks up within each category
            if prompts_by_path:
                for path, idx_obj_list in prompts_by_path.items():
                    idx_obj_list.sort(key=lambda t: t[0])
                    cat = self._get_category_by_path(path)
                    prompts = cat.get("prompts", [])
                    # Build consecutive blocks of indices
                    blocks = []
                    cur_start = None
                    prev = None
                    for idx, _ in idx_obj_list:
                        if cur_start is None:
                            cur_start = idx
                            prev = idx
                        elif idx == prev + 1:
                            prev = idx
                        else:
                            blocks.append((cur_start, prev))
                            cur_start = idx
                            prev = idx
                    if cur_start is not None:
                        blocks.append((cur_start, prev))
                    # Shift each block up by one
                    for start, end in blocks:
                        if start <= 0:
                            continue
                        try:
                            before = prompts[start - 1]
                            block = prompts[start:end + 1]
                            prompts[start - 1:end + 1] = block + [before]
                        except Exception:
                            pass
                # Build keys to restore prompt selection after repopulating
                for path, idx_obj_list in prompts_by_path.items():
                    cat = self._get_category_by_path(path)
                    prompts = cat.get("prompts", [])
                    for _old_idx, p_obj in idx_obj_list:
                        try:
                            new_idx = next((i for i, pp in enumerate(prompts) if pp is p_obj), None)
                            if new_idx is not None:
                                prompt_keys_after_move.append((path, new_idx))
                        except Exception:
                            pass

            # Move selected categories up among their siblings
            if selected_category_paths:
                self._move_categories_by_one(selected_category_paths, direction=-1)

            # Refresh tree and restore both prompt and category selections
            self.populate_tree()
            if prompt_keys_after_move:
                self._restore_selection_by_prompt_keys(prompt_keys_after_move)
            if selected_category_paths:
                self._restore_selection_by_category_paths(selected_category_paths)
        except Exception:
            pass

    def move_selected_down(self):
        try:
            self._push_undo()
            sels = list(self.tree.selection())
            if not sels:
                return
            # Separate selections into prompts and categories
            prompts_by_path = {}
            selected_category_paths = []
            for item in sels:
                vals = self.tree.item(item, "values")
                if not vals:
                    continue
                if vals[0] == "prompt":
                    path = vals[1]
                    try:
                        idx = int(vals[2])
                    except Exception:
                        continue
                    cat = self._get_category_by_path(path)
                    try:
                        p_obj = cat.get("prompts", [])[idx]
                    except Exception:
                        continue
                    prompts_by_path.setdefault(path, []).append((idx, p_obj))
                elif vals[0] == "category":
                    selected_category_paths.append(vals[1])

            prompt_keys_after_move = []

            # Move prompt blocks down within each category
            if prompts_by_path:
                for path, idx_obj_list in prompts_by_path.items():
                    idx_obj_list.sort(key=lambda t: t[0])
                    cat = self._get_category_by_path(path)
                    prompts = cat.get("prompts", [])
                    last_index = len(prompts) - 1
                    # Build consecutive blocks
                    blocks = []
                    cur_start = None
                    prev = None
                    for idx, _ in idx_obj_list:
                        if cur_start is None:
                            cur_start = idx
                            prev = idx
                        elif idx == prev + 1:
                            prev = idx
                        else:
                            blocks.append((cur_start, prev))
                            cur_start = idx
                            prev = idx
                    if cur_start is not None:
                        blocks.append((cur_start, prev))
                    # Shift each block down by one (process in descending order)
                    for start, end in sorted(blocks, key=lambda b: b[0], reverse=True):
                        if end >= last_index:
                            continue
                        try:
                            after = prompts[end + 1]
                            block = prompts[start:end + 1]
                            prompts[start:end + 2] = [after] + block
                        except Exception:
                            pass
                # Build keys to restore prompt selection after repopulating
                for path, idx_obj_list in prompts_by_path.items():
                    cat = self._get_category_by_path(path)
                    prompts = cat.get("prompts", [])
                    for _old_idx, p_obj in idx_obj_list:
                        try:
                            new_idx = next((i for i, pp in enumerate(prompts) if pp is p_obj), None)
                            if new_idx is not None:
                                prompt_keys_after_move.append((path, new_idx))
                        except Exception:
                            pass

            # Move selected categories down among their siblings
            if selected_category_paths:
                self._move_categories_by_one(selected_category_paths, direction=1)

            # Refresh tree and restore both prompt and category selections
            self.populate_tree()
            if prompt_keys_after_move:
                self._restore_selection_by_prompt_keys(prompt_keys_after_move)
            if selected_category_paths:
                self._restore_selection_by_category_paths(selected_category_paths)
        except Exception:
            pass

    def _get_category_container_info(self, category_path):
        """Return tuple (is_top_level, container_dict, parent_obj_or_None, name, parent_path_or_empty)."""
        parts = category_path.split("/")
        if len(parts) == 1:
            container = self.prompts.setdefault("categories", {})
            return True, container, None, parts[0], ""
        parent_path = "/".join(parts[:-1])
        parent = self._get_category_by_path(parent_path)
        container = parent.setdefault("subcategories", {})
        return False, container, parent, parts[-1], parent_path

    def _move_categories_by_one(self, selected_paths, direction):
        """Move categories identified by their full paths up (direction=-1) or down (direction=1) among siblings.
        Preserves relative order of selected consecutive blocks.
        """
        try:
            # Group selections by their sibling container
            groups = {}
            for path in selected_paths:
                try:
                    is_top, container, parent, name, parent_path = self._get_category_container_info(path)
                except Exception:
                    continue
                key = id(container)
                g = groups.setdefault(key, {
                    "is_top": is_top,
                    "container": container,
                    "parent": parent,
                    "parent_path": parent_path,
                    "selected_names": set(),
                })
                g["selected_names"].add(name)

            for _k, g in groups.items():
                container = g["container"]
                order = list(container.keys())
                selected_idxs = [i for i, n in enumerate(order) if n in g["selected_names"]]
                if not selected_idxs:
                    continue
                selected_idxs.sort()
                # Build consecutive blocks
                blocks = []
                cur_start = None
                prev = None
                for idx in selected_idxs:
                    if cur_start is None:
                        cur_start = idx
                        prev = idx
                    elif idx == prev + 1:
                        prev = idx
                    else:
                        blocks.append((cur_start, prev))
                        cur_start = idx
                        prev = idx
                if cur_start is not None:
                    blocks.append((cur_start, prev))

                if direction < 0:
                    # Move up: process blocks in ascending order
                    for start, end in blocks:
                        if start <= 0:
                            continue
                        before = order[start - 1]
                        block = order[start:end + 1]
                        order[start - 1:end + 1] = block + [before]
                else:
                    # Move down: process blocks in descending order
                    for start, end in sorted(blocks, key=lambda b: b[0], reverse=True):
                        if end >= len(order) - 1:
                            continue
                        after = order[end + 1]
                        block = order[start:end + 1]
                        order[start:end + 2] = [after] + block

                # Rebuild the container dict to reflect new order
                old = container
                new_container = {name: old[name] for name in order}
                if g["is_top"]:
                    self.prompts["categories"] = new_container
                else:
                    try:
                        g["parent"]["subcategories"] = new_container
                    except Exception:
                        # Fallback in case parent lost subcategories key
                        g["parent"]["subcategories"] = new_container
        except Exception:
            pass

    def _restore_selection_by_category_paths(self, category_paths):
        """Restore selection by category paths after repopulating the tree."""
        try:
            wanted = set(category_paths)
            items_to_select = []
            stack = list(self.tree.get_children(""))
            while stack:
                it = stack.pop()
                try:
                    vals = self.tree.item(it, "values")
                    if vals and vals[0] == "category" and vals[1] in wanted:
                        items_to_select.append(it)
                    for child in self.tree.get_children(it):
                        stack.append(child)
                except Exception:
                    pass
            if items_to_select:
                try:
                    self.tree.selection_remove(self.tree.selection())
                except Exception:
                    pass
                try:
                    self.tree.selection_set(items_to_select)
                    self.tree.focus(items_to_select[0])
                    self.tree.see(items_to_select[0])
                except Exception:
                    pass
        except Exception:
            pass

    def _restore_selection_by_prompt_keys(self, keys):
        """Restore selection by (category_path, prompt_index) keys after repopulating the tree."""
        try:
            # Find tree items matching the given keys
            items_to_select = []
            key_set = {(path, int(idx)) for path, idx in keys}
            stack = list(self.tree.get_children(""))
            while stack:
                it = stack.pop()
                try:
                    vals = self.tree.item(it, "values")
                    if vals and vals[0] == "prompt":
                        path = vals[1]
                        idx = int(vals[2])
                        if (path, idx) in key_set:
                            items_to_select.append(it)
                    # traverse children
                    for child in self.tree.get_children(it):
                        stack.append(child)
                except Exception:
                    pass
            if items_to_select:
                try:
                    # Clear any existing selection first
                    self.tree.selection_remove(self.tree.selection())
                    # Set the new selection
                    self.tree.selection_set(items_to_select)
                    # Focus and ensure visibility
                    self.tree.focus(items_to_select[0])
                    self.tree.see(items_to_select[0])
                except Exception:
                    pass
        except Exception:
            pass

    def _select_range_between(self, anchor_item, target_item):
        """Select a contiguous range between two visible items, filtering to prompts only."""
        try:
            if not anchor_item or not target_item:
                return
            visible = self._get_visible_items_order()
            try:
                i_a = visible.index(anchor_item)
                i_b = visible.index(target_item)
            except ValueError:
                return
            start = min(i_a, i_b)
            end = max(i_a, i_b)
            to_select = []
            for it in visible[start:end + 1]:
                vals = self.tree.item(it, "values")
                if vals and vals[0] == "prompt":
                    to_select.append(it)
            if to_select:
                self.tree.selection_set(to_select)
        except Exception:
            pass

    def _get_visible_items_order(self):
        """Return a flat list of tree item ids in the order they are currently visible (expanded)."""
        order = []
        try:
            def walk(parent=""):
                try:
                    for it in self.tree.get_children(parent):
                        order.append(it)
                        try:
                            opened = bool(self.tree.item(it, "open"))
                        except Exception:
                            opened = False
                        if opened:
                            walk(it)
                except Exception:
                    pass
            walk("")
        except Exception:
            pass
        return order

    def _get_prev_visible_item(self, item_id):
        try:
            order = self._get_visible_items_order()
            idx = order.index(item_id)
            if idx > 0:
                return order[idx - 1]
            return None
        except Exception:
            return None

    def _get_next_visible_item(self, item_id):
        try:
            order = self._get_visible_items_order()
            idx = order.index(item_id)
            if idx < len(order) - 1:
                return order[idx + 1]
            return None
        except Exception:
            return None


if __name__ == "__main__":
    # Make the app crisp and single-instanced; avoid hanging consoles
    # Local inline definitions in case helpers were stripped
    try:
        set_dpi_awareness
    except NameError:
        def set_dpi_awareness():
            try:
                if sys.platform == "win32":
                    try:
                        ctypes.windll.shcore.SetProcessDpiAwareness(2)
                    except Exception:
                        try:
                            ctypes.windll.user32.SetProcessDPIAware()
                        except Exception:
                            pass
            except Exception:
                pass
    try:
        setup_logging
    except NameError:
        def setup_logging():
            try:
                logs_dir = Path("logs"); logs_dir.mkdir(exist_ok=True)
                log_path = logs_dir / "promptoire.log"
                logger = logging.getLogger("Promptoire"); logger.setLevel(logging.INFO)
                handler = RotatingFileHandler(log_path, maxBytes=524288, backupCount=3, encoding="utf-8")
                formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
                handler.setFormatter(formatter)
                if not logger.handlers:
                    logger.addHandler(handler)
                return logger
            except Exception:
                return logging.getLogger("Promptoire")
    try:
        acquire_single_instance_lock()
    except NameError:
        def acquire_single_instance_lock():
            if sys.platform == "win32":
                try:
                    import win32event, win32api, winerror
                    handle = win32event.CreateMutex(None, True, "Promptoire_Singleton_Mutex")
                    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                        return None
                    return ("mutex", handle)
                except Exception:
                    pass
            try:
                lock_path = Path("Promptoire.lock")
                f = open(lock_path, "w")
                if MSVCRT_AVAILABLE:
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                        return ("file", f)
                    except OSError:
                        try:
                            f.close()
                        except Exception:
                            pass
                        return None
                else:
                    return ("file", f)
            except Exception:
                return None

    set_dpi_awareness()
    logger = setup_logging()
    lock_handle = acquire_single_instance_lock()
    if lock_handle is None:
        # Already running – bring to front if possible via message box
        try:
            messagebox.showinfo("Promptoire", "Promptoire is already running.")
        except Exception:
            pass
        sys.exit(0)
    try:
        logger.info("Starting Promptoire")
        app = Promptoire()
        app.run()
    except KeyboardInterrupt:
        logger.info("Promptoire closed via KeyboardInterrupt")
    except Exception as e:
        try:
            logger.exception("Unhandled exception running Promptoire")
        except Exception:
            pass
    finally:
        # Release instance lock
        try:
            if lock_handle:
                kind, handle = lock_handle
                if kind == "file":
                    try:
                        handle.close()
                    except Exception:
                        pass
                elif kind == "mutex":
                    try:
                        import win32api
                        win32api.CloseHandle(handle)
                    except Exception:
                        pass
        except Exception:
            pass











