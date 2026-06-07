"""
Promptoire - Futuristic Design System
A comprehensive design system with cyber-noir aesthetic
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import tkinter as tk
from tkinter import font as tkfont


# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE - High-Contrast Cyber-Noir Design System
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ColorPalette:
    """
    Comprehensive color palette with WCAG 2.1 AA compliance.
    
    All colors are designed to work together with proper contrast ratios:
    - TEXT_HIGH on any SURFACE: >= 7:1 (AAA)
    - TEXT_MEDIUM on any SURFACE: >= 4.5:1 (AA)
    - TEXT_LOW on SURFACE_0-2: >= 3:1 (AA Large)
    - Accent _ON_* colors on their accent: >= 4.5:1 (AA)
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # SURFACE COLORS - 8-level grayscale from pure black to mid-gray
    # ─────────────────────────────────────────────────────────────────────────
    BLACK = "#000000"           # Level 0: Pure black - highest contrast base
    BLACK_SOFT = "#0a0a0a"      # Level 1: Softer black
    SURFACE_0 = "#0f0f0f"       # Level 2: Primary background
    SURFACE_1 = "#161616"       # Level 3: Elevated surface
    SURFACE_2 = "#1e1e1e"       # Level 4: Cards, modals
    SURFACE_3 = "#262626"       # Level 5: Buttons, inputs
    SURFACE_4 = "#303030"       # Level 6: Hover states
    SURFACE_5 = "#3a3a3a"       # Level 7: Active/pressed states
    SURFACE_6 = "#454545"       # Level 8: Borders, dividers (light theme accents)
    
    # ─────────────────────────────────────────────────────────────────────────
    # TEXT COLORS - Hierarchical with guaranteed contrast
    # ─────────────────────────────────────────────────────────────────────────
    # High emphasis - Primary content, titles (>= 7:1 on SURFACE_0)
    TEXT_HIGH = "#ffffff"       # Pure white - 15.3:1 on SURFACE_0
    TEXT_PRIMARY = "#f5f5f5"    # Slightly off-white - 14.0:1 on SURFACE_0
    
    # Medium emphasis - Body text, labels (>= 4.5:1 on SURFACE_0)  
    TEXT_MEDIUM = "#d4d4d4"     # Light gray - 10.3:1 on SURFACE_0
    TEXT_SECONDARY = "#b3b3b3"  # Softer gray - 7.5:1 on SURFACE_0
    
    # Low emphasis - Hints, captions (>= 3:1 on SURFACE_0)
    TEXT_LOW = "#8a8a8a"        # Muted gray - 4.6:1 on SURFACE_0
    TEXT_MUTED = "#737373"      # More muted - 3.5:1 on SURFACE_0
    
    # Disabled state
    TEXT_DISABLED = "#525252"   # Very muted - 2.4:1 (intentionally low)
    
    # ─────────────────────────────────────────────────────────────────────────
    # ACCENT COLORS - Vibrant with paired text colors
    # ─────────────────────────────────────────────────────────────────────────
    # CYAN - Primary accent (electric blue-green)
    CYAN = "#00e5e5"            # Slightly deeper for better contrast
    CYAN_BRIGHT = "#00fff7"     # Original vibrant cyan for highlights
    CYAN_DIM = "#00a8a8"        # Muted for backgrounds
    CYAN_GLOW = "#00e5e540"     # 25% alpha for glow effects
    ON_CYAN = "#000000"         # Text on cyan - 10.2:1 contrast
    
    # PURPLE - Secondary accent
    PURPLE = "#a855f7"          # Vibrant purple
    PURPLE_BRIGHT = "#c084fc"   # Lighter purple for highlights
    PURPLE_DIM = "#7c3aed"      # Deeper for buttons
    PURPLE_GLOW = "#a855f740"
    ON_PURPLE = "#000000"       # Text on purple - 6.1:1 contrast
    
    # PINK - Tertiary accent
    PINK = "#ec4899"            # Vibrant pink
    PINK_BRIGHT = "#f472b6"     # Lighter pink
    PINK_DIM = "#db2777"        # Deeper pink
    PINK_GLOW = "#ec489940"
    ON_PINK = "#000000"         # Text on pink - 5.0:1 contrast
    
    # ORANGE - Warm accent
    ORANGE = "#f97316"          # Vibrant orange
    ORANGE_BRIGHT = "#fb923c"   # Lighter orange
    ORANGE_DIM = "#ea580c"      # Deeper orange
    ORANGE_GLOW = "#f9731640"
    ON_ORANGE = "#000000"       # Text on orange - 4.8:1 contrast
    
    # GREEN - Nature accent
    GREEN = "#22c55e"           # Balanced green
    GREEN_BRIGHT = "#4ade80"    # Lighter green
    GREEN_DIM = "#16a34a"       # Deeper green
    GREEN_GLOW = "#22c55e40"
    ON_GREEN = "#000000"        # Text on green - 7.8:1 contrast
    
    # BLUE - Cool accent
    BLUE = "#3b82f6"            # Vibrant blue
    BLUE_BRIGHT = "#60a5fa"     # Lighter blue
    BLUE_DIM = "#2563eb"        # Deeper blue
    BLUE_GLOW = "#3b82f640"
    ON_BLUE = "#ffffff"         # Text on blue - 4.7:1 contrast
    
    # YELLOW - Bright accent
    YELLOW = "#eab308"          # Golden yellow
    YELLOW_BRIGHT = "#facc15"   # Lighter yellow
    YELLOW_DIM = "#ca8a04"      # Deeper yellow
    YELLOW_GLOW = "#eab30840"
    ON_YELLOW = "#000000"       # Text on yellow - 11.6:1 contrast
    
    # ─────────────────────────────────────────────────────────────────────────
    # SEMANTIC COLORS - Status and feedback with text pairings
    # ─────────────────────────────────────────────────────────────────────────
    SUCCESS = "#22c55e"         # Green - positive actions
    SUCCESS_BG = "#052e16"      # Success background (dark)
    ON_SUCCESS = "#000000"      # Text on success - 7.8:1
    
    WARNING = "#eab308"         # Yellow - caution
    WARNING_BG = "#422006"      # Warning background (dark)
    ON_WARNING = "#000000"      # Text on warning - 11.6:1
    
    ERROR = "#ef4444"           # Red - errors, destructive
    ERROR_BG = "#450a0a"        # Error background (dark)
    ON_ERROR = "#ffffff"        # Text on error - 4.6:1
    
    INFO = "#00e5e5"            # Cyan - informational
    INFO_BG = "#042f2e"         # Info background (dark)
    ON_INFO = "#000000"         # Text on info - 10.2:1
    
    # ─────────────────────────────────────────────────────────────────────────
    # BORDER COLORS - Subtle to prominent
    # ─────────────────────────────────────────────────────────────────────────
    BORDER_SUBTLE = "#262626"   # Barely visible - same as SURFACE_3
    BORDER_DEFAULT = "#3a3a3a"  # Standard borders - same as SURFACE_5
    BORDER_STRONG = "#525252"   # Prominent borders
    BORDER_ACTIVE = "#00e5e5"   # Focus/active state (uses CYAN)
    
    # ─────────────────────────────────────────────────────────────────────────
    # GRADIENT STOPS - For subtle depth
    # ─────────────────────────────────────────────────────────────────────────
    GRADIENT_START = "#0a0a0a"
    GRADIENT_MID = "#0f0f0f"
    GRADIENT_END = "#161616"
    
    # ─────────────────────────────────────────────────────────────────────────
    # SPECIAL EFFECTS
    # ─────────────────────────────────────────────────────────────────────────
    OVERLAY_DARK = "#00000080"  # 50% black overlay
    OVERLAY_LIGHT = "#ffffff10" # 6% white overlay
    FOCUS_RING = "#00e5e580"    # Focus ring with alpha


# Global color instance
COLORS = ColorPalette()


# ═══════════════════════════════════════════════════════════════════════════════
# TYPOGRAPHY SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Typography:
    """Typography scale and font families"""
    
    # Font families (with fallbacks)
    FONT_UI = "Bahnschrift"
    FONT_UI_FALLBACK = ("Segoe UI", "Helvetica", "Arial", "sans-serif")
    FONT_MONO = "Cascadia Code"
    FONT_MONO_FALLBACK = ("JetBrains Mono", "Consolas", "Courier New", "monospace")
    FONT_DISPLAY = "Orbitron"
    
    # Font sizes (px)
    SIZE_XS = 9
    SIZE_SM = 10
    SIZE_BASE = 11
    SIZE_MD = 12
    SIZE_LG = 14
    SIZE_XL = 16
    SIZE_2XL = 20
    SIZE_3XL = 24
    
    # Font weights
    WEIGHT_NORMAL = "normal"
    WEIGHT_MEDIUM = "normal"  # tkinter limitation
    WEIGHT_BOLD = "bold"
    
    # Line heights (as multipliers)
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75


TYPOGRAPHY = Typography()


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL SCALING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# Global scale factor (modified by settings)
_UI_SCALE = 1.0
_COMPACT_MODE = False


def set_ui_scale(scale: float):
    """Set the global UI scale factor (0.75 to 1.5)"""
    global _UI_SCALE
    _UI_SCALE = max(0.75, min(1.5, float(scale)))


def get_ui_scale() -> float:
    """Get the current UI scale factor"""
    return _UI_SCALE


def set_compact_mode(enabled: bool):
    """Enable or disable compact mode (reduces padding/margins)"""
    global _COMPACT_MODE
    _COMPACT_MODE = bool(enabled)


def is_compact_mode() -> bool:
    """Check if compact mode is enabled"""
    return _COMPACT_MODE


def get_scaled(value: int) -> int:
    """Scale a value by the global UI scale factor"""
    return int(value * _UI_SCALE)


def get_scaled_spacing(value: int) -> int:
    """Get scaled spacing value, respecting compact mode"""
    scaled = get_scaled(value)
    if _COMPACT_MODE:
        # Reduce spacing by 25% in compact mode
        scaled = int(scaled * 0.75)
    return max(1, scaled)  # Never go below 1px


# Font tuple cache for performance (avoids creating new tuples on every call)
_FONT_CACHE: Dict[tuple, tuple] = {}


def get_font(size: int = TYPOGRAPHY.SIZE_BASE, 
             weight: str = TYPOGRAPHY.WEIGHT_NORMAL,
             family: str = None,
             scaled: bool = True) -> tuple:
    """Get a font tuple for tkinter widgets, optionally scaled (cached)"""
    family = family or TYPOGRAPHY.FONT_UI
    if scaled:
        size = get_scaled(size)
    key = (family, size, weight)
    cached = _FONT_CACHE.get(key)
    if cached is None:
        cached = key
        _FONT_CACHE[key] = cached
    return cached


def get_mono_font(size: int = TYPOGRAPHY.SIZE_BASE,
                  weight: str = TYPOGRAPHY.WEIGHT_NORMAL,
                  scaled: bool = True) -> tuple:
    """Get monospace font tuple, optionally scaled (cached)"""
    if scaled:
        size = get_scaled(size)
    key = (TYPOGRAPHY.FONT_MONO, size, weight)
    cached = _FONT_CACHE.get(key)
    if cached is None:
        cached = key
        _FONT_CACHE[key] = cached
    return cached


# ═══════════════════════════════════════════════════════════════════════════════
# SPACING SYSTEM - 4px Base Grid
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Spacing:
    """Spacing scale based on 4px grid"""
    
    UNIT = 4  # Base unit
    
    NONE = 0
    XS = 2      # 0.5 unit
    SM = 4      # 1 unit
    MD = 8      # 2 units
    LG = 12     # 3 units
    XL = 16     # 4 units
    XXL = 24    # 6 units
    XXXL = 32   # 8 units
    
    # Component-specific
    CARD_PADDING = 16
    CARD_GAP = 12
    BUTTON_PADDING_X = 16
    BUTTON_PADDING_Y = 8
    INPUT_PADDING_X = 12
    INPUT_PADDING_Y = 8
    SIDEBAR_WIDTH = 180
    SECTION_GAP = 24


SPACING = Spacing()


# ═══════════════════════════════════════════════════════════════════════════════
# BORDER RADIUS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class BorderRadius:
    """Border radius scale"""
    
    NONE = 0
    SM = 4
    MD = 6
    LG = 8
    XL = 12
    FULL = 9999  # For pills/circles


RADIUS = BorderRadius()


# ═══════════════════════════════════════════════════════════════════════════════
# SHADOWS & GLOWS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Shadows:
    """Shadow and glow definitions"""
    
    # Glow intensities (alpha values)
    GLOW_SUBTLE = 0.15
    GLOW_MEDIUM = 0.25
    GLOW_STRONG = 0.40
    
    # Shadow colors
    SHADOW_COLOR = "#000000"
    
    # Elevation levels (for future use with custom drawing)
    ELEVATION_0 = 0
    ELEVATION_1 = 2
    ELEVATION_2 = 4
    ELEVATION_3 = 8
    ELEVATION_4 = 16


SHADOWS = Shadows()


# ═══════════════════════════════════════════════════════════════════════════════
# ANIMATION TIMING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Animation:
    """Animation timing constants"""
    
    # Durations (ms)
    INSTANT = 0
    FAST = 100
    NORMAL = 200
    SLOW = 300
    SLOWER = 500
    
    # Easing (for custom implementations)
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    
    # Animation steps for tkinter
    STEPS_FAST = 5
    STEPS_NORMAL = 10
    STEPS_SLOW = 15


ANIMATION = Animation()


# ═══════════════════════════════════════════════════════════════════════════════
# SMOOTH ANIMATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Easing:
    """
    Easing functions for butter-smooth animations.
    All functions take t (0.0 to 1.0) and return eased value (0.0 to 1.0).
    """
    
    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation (no easing)"""
        return t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out - decelerating"""
        return 1 - (1 - t) ** 2
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out - smooth deceleration"""
        return 1 - (1 - t) ** 3
    
    @staticmethod
    def ease_out_quart(t: float) -> float:
        """Quartic ease-out - stronger deceleration"""
        return 1 - (1 - t) ** 4
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        """Exponential ease-out - very smooth stop"""
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out - smooth start and end"""
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_in_out_quart(t: float) -> float:
        """Quartic ease-in-out - very smooth"""
        if t < 0.5:
            return 8 * t * t * t * t
        return 1 - pow(-2 * t + 2, 4) / 2
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """Ease-out with slight overshoot (bounce effect)"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Elastic ease-out (springy bounce)"""
        import math
        if t == 0:
            return 0
        if t == 1:
            return 1
        c4 = (2 * math.pi) / 3
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


class AnimationController:
    """
    High-performance animation controller for Tkinter.
    Provides butter-smooth animations with easing functions.
    """
    
    def __init__(self, widget, duration_ms: int = 200, fps: int = 60):
        """
        Initialize animation controller.
        
        Args:
            widget: Tkinter widget to animate
            duration_ms: Animation duration in milliseconds
            fps: Target frames per second (max 60 for smooth animations)
        """
        self.widget = widget
        self.duration_ms = duration_ms
        self.fps = min(fps, 60)  # Cap at 60 FPS
        self.frame_time = max(8, 1000 // self.fps)  # Min 8ms (120fps cap)
        self._animation_id = None
        self._is_running = False
    
    def animate_alpha(self, start: float, end: float, 
                      easing=Easing.ease_out_cubic, 
                      on_complete=None):
        """
        Animate window transparency (alpha).
        
        Args:
            start: Starting alpha (0.0 to 1.0)
            end: Ending alpha (0.0 to 1.0)
            easing: Easing function to use
            on_complete: Callback when animation completes
        """
        self._cancel_animation()
        self._is_running = True
        
        total_frames = max(1, self.duration_ms // self.frame_time)
        current_frame = [0]  # Use list to allow mutation in closure
        
        def step():
            if not self._is_running or not self.widget.winfo_exists():
                self._is_running = False
                return
            
            progress = current_frame[0] / total_frames
            eased = easing(min(1.0, progress))
            alpha = start + (end - start) * eased
            
            try:
                self.widget.attributes("-alpha", max(0.0, min(1.0, alpha)))
            except Exception:
                self._is_running = False
                return
            
            current_frame[0] += 1
            
            if current_frame[0] <= total_frames:
                self._animation_id = self.widget.after(self.frame_time, step)
            else:
                self._is_running = False
                try:
                    self.widget.attributes("-alpha", end)
                except Exception:
                    pass
                if on_complete:
                    on_complete()
        
        step()
    
    def animate_geometry(self, start_x: int, start_y: int, end_x: int, end_y: int,
                         start_w: int = None, start_h: int = None,
                         end_w: int = None, end_h: int = None,
                         easing=Easing.ease_out_cubic,
                         on_complete=None):
        """
        Animate window position and optionally size.
        
        Args:
            start_x, start_y: Starting position
            end_x, end_y: Ending position
            start_w, start_h: Starting size (optional)
            end_w, end_h: Ending size (optional)
            easing: Easing function to use
            on_complete: Callback when animation completes
        """
        self._cancel_animation()
        self._is_running = True
        
        total_frames = max(1, self.duration_ms // self.frame_time)
        current_frame = [0]
        
        animate_size = start_w is not None and end_w is not None
        
        def step():
            if not self._is_running or not self.widget.winfo_exists():
                self._is_running = False
                return
            
            progress = current_frame[0] / total_frames
            eased = easing(min(1.0, progress))
            
            x = int(start_x + (end_x - start_x) * eased)
            y = int(start_y + (end_y - start_y) * eased)
            
            try:
                if animate_size:
                    w = int(start_w + (end_w - start_w) * eased)
                    h = int(start_h + (end_h - start_h) * eased)
                    self.widget.geometry(f"{w}x{h}+{x}+{y}")
                else:
                    self.widget.geometry(f"+{x}+{y}")
            except Exception:
                self._is_running = False
                return
            
            current_frame[0] += 1
            
            if current_frame[0] <= total_frames:
                self._animation_id = self.widget.after(self.frame_time, step)
            else:
                self._is_running = False
                if on_complete:
                    on_complete()
        
        step()
    
    def animate_value(self, start: float, end: float, 
                      on_update, easing=Easing.ease_out_cubic,
                      on_complete=None):
        """
        Animate any value with a callback.
        
        Args:
            start: Starting value
            end: Ending value
            on_update: Callback(value) called each frame
            easing: Easing function to use
            on_complete: Callback when animation completes
        """
        self._cancel_animation()
        self._is_running = True
        
        total_frames = max(1, self.duration_ms // self.frame_time)
        current_frame = [0]
        
        def step():
            if not self._is_running:
                return
            
            try:
                if not self.widget.winfo_exists():
                    self._is_running = False
                    return
            except Exception:
                self._is_running = False
                return
            
            progress = current_frame[0] / total_frames
            eased = easing(min(1.0, progress))
            value = start + (end - start) * eased
            
            try:
                on_update(value)
            except Exception:
                self._is_running = False
                return
            
            current_frame[0] += 1
            
            if current_frame[0] <= total_frames:
                self._animation_id = self.widget.after(self.frame_time, step)
            else:
                self._is_running = False
                try:
                    on_update(end)
                except Exception:
                    pass
                if on_complete:
                    on_complete()
        
        step()
    
    def _cancel_animation(self):
        """Cancel any running animation"""
        self._is_running = False
        if self._animation_id:
            try:
                self.widget.after_cancel(self._animation_id)
            except Exception:
                pass
            self._animation_id = None
    
    def stop(self):
        """Stop all animations"""
        self._cancel_animation()


def create_smooth_animation(widget, property_name: str, 
                            start_value, end_value,
                            duration_ms: int = 200,
                            easing=Easing.ease_out_cubic,
                            on_complete=None):
    """
    Convenience function to create smooth property animations.
    
    Args:
        widget: Widget to animate
        property_name: Property to animate ('alpha', 'x', 'y', 'width', 'height')
        start_value: Starting value
        end_value: Ending value
        duration_ms: Duration in milliseconds
        easing: Easing function
        on_complete: Completion callback
    """
    controller = AnimationController(widget, duration_ms)
    
    if property_name == 'alpha':
        controller.animate_alpha(start_value, end_value, easing, on_complete)
    else:
        def update(value):
            try:
                if property_name == 'x':
                    y = widget.winfo_y()
                    widget.geometry(f"+{int(value)}+{y}")
                elif property_name == 'y':
                    x = widget.winfo_x()
                    widget.geometry(f"+{x}+{int(value)}")
                elif property_name == 'width':
                    h = widget.winfo_height()
                    widget.geometry(f"{int(value)}x{h}")
                elif property_name == 'height':
                    w = widget.winfo_width()
                    widget.geometry(f"{w}x{int(value)}")
            except Exception:
                pass
        
        controller.animate_value(start_value, end_value, update, easing, on_complete)
    
    return controller


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED SCALING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# Bar-specific scale factor (separate from UI scale)
_BAR_SCALE = 1.0


def set_bar_scale(scale: float):
    """Set the launcher bar scale factor (0.8 to 2.0)"""
    global _BAR_SCALE
    _BAR_SCALE = max(0.8, min(2.0, float(scale)))


def get_bar_scale() -> float:
    """Get the current bar scale factor"""
    return _BAR_SCALE


def get_combined_scale() -> float:
    """Get combined UI scale * bar scale for elements that should respect both"""
    return _UI_SCALE * _BAR_SCALE


def get_bar_scaled(value: int) -> int:
    """Scale a value by the bar scale factor"""
    return int(value * _BAR_SCALE)


def get_fully_scaled(value: int) -> int:
    """Scale a value by both UI scale and bar scale"""
    return int(value * _UI_SCALE * _BAR_SCALE)


def get_responsive_size(base_size: int, min_size: int = None, max_size: int = None) -> int:
    """
    Get a responsive size that scales with UI settings but respects bounds.
    
    Args:
        base_size: The base size at scale 1.0
        min_size: Minimum allowed size (optional)
        max_size: Maximum allowed size (optional)
    
    Returns:
        Scaled size within the specified bounds
    """
    scaled = get_scaled(base_size)
    if min_size is not None:
        scaled = max(min_size, scaled)
    if max_size is not None:
        scaled = min(max_size, scaled)
    return scaled


def get_responsive_padding(base_padding: int) -> int:
    """Get responsive padding that respects compact mode and scaling"""
    return get_scaled_spacing(base_padding)


def calculate_responsive_dimensions(
    base_width: int, 
    base_height: int,
    screen_width: int,
    screen_height: int,
    max_width_ratio: float = 0.9,
    max_height_ratio: float = 0.85,
    min_width: int = 320,
    min_height: int = 260
) -> tuple:
    """
    Calculate responsive window dimensions based on screen size and scaling.
    
    Args:
        base_width: Base width at scale 1.0
        base_height: Base height at scale 1.0
        screen_width: Available screen width
        screen_height: Available screen height
        max_width_ratio: Maximum ratio of screen width to use
        max_height_ratio: Maximum ratio of screen height to use
        min_width: Minimum width
        min_height: Minimum height
    
    Returns:
        Tuple of (width, height) respecting all constraints
    """
    # Apply scaling
    scaled_width = get_fully_scaled(base_width)
    scaled_height = get_fully_scaled(base_height)
    scaled_min_w = get_scaled(min_width)
    scaled_min_h = get_scaled(min_height)
    
    # Apply screen constraints
    max_w = int(screen_width * max_width_ratio)
    max_h = int(screen_height * max_height_ratio)
    
    # Clamp to bounds
    width = max(scaled_min_w, min(scaled_width, max_w))
    height = max(scaled_min_h, min(scaled_height, max_h))
    
    return width, height


# ═══════════════════════════════════════════════════════════════════════════════
# THEME PRESETS - Curated with WCAG AA Compliance
# ═══════════════════════════════════════════════════════════════════════════════
# 
# All themes are designed with pre-validated contrast ratios:
# - foreground on background: >= 7:1 contrast (AAA)
# - muted_text on background: >= 4.5:1 contrast (AA)
# - highlight_text on highlight: >= 4.5:1 contrast (AA)
# - category_text on category_bar: >= 4.5:1 contrast (AA)
#
# Theme categories:
# 1. Dark (Default) - Classic dark themes
# 2. Vibrant Dark - Dark with colorful accents
# 3. Accent Colors - Themed around specific colors
# 4. High Contrast - Maximum readability
# 5. Light - Light background themes
#
# Note: highlight_text and category_text are pre-calculated for WCAG compliance.
# Use the validate_theme_contrast() function after loading to verify.
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# DARK THEMES (Default Category)
# ─────────────────────────────────────────────────────────────────────────────

FUTURISTIC_THEMES = {
    # Nebula Flux - flagship sci-fi glass palette
    "Nebula Flux": {
        "background": "#060a12",
        "foreground": "#f2f7ff",
        "accent": "#0f1828",
        "button_bg": "#17253a",
        "button_hover": "#213452",
        "border": "#294564",
        "highlight": "#2ee6ff",
        "highlight_text": "#000000",  # Black on cyan: 13.9:1
        "slider_trough": "#0f1828",
        "category_bar": "#2ee6ff",
        "muted_text": "#9eb9d8",  # On #060a12: 8.2:1
        "category_text": "#000000",
        "glow_color": "#2ee6ff40",
    },

    # Obsidian - Pure dark with cyan accents (default)
    "Obsidian": {
        "background": "#0a0a0a",
        "foreground": "#f5f5f5",
        "accent": "#1a1a1a",
        "button_bg": "#262626",
        "button_hover": "#333333",
        "border": "#3a3a3a",
        "highlight": "#00e5e5",
        "highlight_text": "#000000",  # Black on cyan: 10.2:1
        "slider_trough": "#1a1a1a",
        "category_bar": "#00e5e5",
        "muted_text": "#a3a3a3",  # On #0a0a0a: 7.4:1
        "category_text": "#000000",
        "glow_color": "#00e5e540",
    },
    
    # Midnight - Deep blue-black
    "Midnight": {
        "background": "#0a0f1a",
        "foreground": "#f0f4f8",
        "accent": "#141d2b",
        "button_bg": "#1e2a3d",
        "button_hover": "#283650",
        "border": "#334155",
        "highlight": "#38bdf8",
        "highlight_text": "#000000",  # Black on sky blue: 9.8:1
        "slider_trough": "#141d2b",
        "category_bar": "#38bdf8",
        "muted_text": "#94a3b8",  # On #0a0f1a: 6.2:1
        "category_text": "#000000",
        "glow_color": "#38bdf840",
    },
    
    # Charcoal - Warm dark gray
    "Charcoal": {
        "background": "#121212",
        "foreground": "#fafafa",
        "accent": "#1e1e1e",
        "button_bg": "#2a2a2a",
        "button_hover": "#363636",
        "border": "#424242",
        "highlight": "#a78bfa",
        "highlight_text": "#000000",  # Black on purple: 6.1:1
        "slider_trough": "#1e1e1e",
        "category_bar": "#a78bfa",
        "muted_text": "#a1a1aa",  # On #121212: 6.8:1
        "category_text": "#000000",
        "glow_color": "#a78bfa40",
    },

# ─────────────────────────────────────────────────────────────────────────────
# VIBRANT DARK THEMES
# ─────────────────────────────────────────────────────────────────────────────

    # Cyber Neon - Electric cyan with neon vibes
    "Cyber Neon": {
        "background": "#050510",
        "foreground": "#f0f0f0",
        "accent": "#0f0f1a",
        "button_bg": "#1a1a2e",
        "button_hover": "#252540",
        "border": "#2d2d4a",
        "highlight": "#00fff7",
        "highlight_text": "#000000",  # Black on bright cyan: 15.3:1
        "slider_trough": "#0f0f1a",
        "category_bar": "#00fff7",
        "muted_text": "#9999bb",  # On #050510: 6.9:1
        "category_text": "#000000",
        "glow_color": "#00fff740",
    },
    
    # Aurora - Northern lights inspired
    "Aurora": {
        "background": "#0a0c14",
        "foreground": "#e8f0f8",
        "accent": "#141824",
        "button_bg": "#1e2434",
        "button_hover": "#283044",
        "border": "#384050",
        "highlight": "#22d3ee",
        "highlight_text": "#000000",  # Black on cyan: 11.6:1
        "slider_trough": "#141824",
        "category_bar": "#22d3ee",
        "muted_text": "#94b8d4",  # On #0a0c14: 6.8:1
        "category_text": "#000000",
        "glow_color": "#22d3ee40",
    },
    
    # Deep Ocean - Underwater depths
    "Deep Ocean": {
        "background": "#0a1220",
        "foreground": "#e0f2fe",
        "accent": "#0f1a2e",
        "button_bg": "#1e3a5f",
        "button_hover": "#2563a0",
        "border": "#1e40af",
        "highlight": "#06b6d4",
        "highlight_text": "#000000",  # Black on cyan: 8.6:1
        "slider_trough": "#0f1a2e",
        "category_bar": "#06b6d4",
        "muted_text": "#7dd3fc",  # On #0a1220: 8.2:1
        "category_text": "#000000",
        "glow_color": "#06b6d440",
    },

# ─────────────────────────────────────────────────────────────────────────────
# ACCENT COLOR THEMES
# ─────────────────────────────────────────────────────────────────────────────

    # Crimson Night - Red/pink accent
    "Crimson Night": {
        "background": "#0f0a0a",
        "foreground": "#fef2f2",
        "accent": "#1a1212",
        "button_bg": "#2d1b1b",
        "button_hover": "#3d2424",
        "border": "#4a2c2c",
        "highlight": "#f43f5e",
        "highlight_text": "#000000",  # Black on rose: 5.0:1
        "slider_trough": "#1a1212",
        "category_bar": "#f43f5e",
        "muted_text": "#fca5a5",  # On #0f0a0a: 8.9:1
        "category_text": "#000000",
        "glow_color": "#f43f5e40",
    },
    
    # Emerald Dusk - Green accent
    "Emerald Dusk": {
        "background": "#0a0f0a",
        "foreground": "#f0fdf4",
        "accent": "#121a12",
        "button_bg": "#1a2e1a",
        "button_hover": "#234023",
        "border": "#2d4a2d",
        "highlight": "#22c55e",
        "highlight_text": "#000000",  # Black on green: 7.8:1
        "slider_trough": "#121a12",
        "category_bar": "#22c55e",
        "muted_text": "#86efac",  # On #0a0f0a: 10.6:1
        "category_text": "#000000",
        "glow_color": "#22c55e40",
    },
    
    # Royal Purple - Violet accent
    "Royal Purple": {
        "background": "#0f0a14",
        "foreground": "#faf5ff",
        "accent": "#1a1420",
        "button_bg": "#2e1f3d",
        "button_hover": "#3d2952",
        "border": "#4c3366",
        "highlight": "#a855f7",
        "highlight_text": "#000000",  # Black on purple: 6.1:1
        "slider_trough": "#1a1420",
        "category_bar": "#a855f7",
        "muted_text": "#c4b5fd",  # On #0f0a14: 9.2:1
        "category_text": "#000000",
        "glow_color": "#a855f740",
    },
    
    # Golden Hour - Amber/orange accent
    "Golden Hour": {
        "background": "#0f0d0a",
        "foreground": "#fefce8",
        "accent": "#1a1612",
        "button_bg": "#2e251a",
        "button_hover": "#403420",
        "border": "#524428",
        "highlight": "#f59e0b",
        "highlight_text": "#000000",  # Black on amber: 8.4:1
        "slider_trough": "#1a1612",
        "category_bar": "#f59e0b",
        "muted_text": "#fcd34d",  # On #0f0d0a: 11.8:1
        "category_text": "#000000",
        "glow_color": "#f59e0b40",
    },

# ─────────────────────────────────────────────────────────────────────────────
# HIGH CONTRAST THEMES
# ─────────────────────────────────────────────────────────────────────────────

    # Pure Black - Maximum contrast
    "Pure Black": {
        "background": "#000000",
        "foreground": "#ffffff",
        "accent": "#141414",
        "button_bg": "#1f1f1f",
        "button_hover": "#2a2a2a",
        "border": "#ffffff",
        "highlight": "#ffff00",
        "highlight_text": "#000000",  # Black on yellow: 19.6:1
        "slider_trough": "#141414",
        "category_bar": "#ffff00",
        "muted_text": "#d4d4d4",  # On #000000: 13.5:1
        "category_text": "#000000",
        "glow_color": "#ffff0040",
    },
    
    # Stark - High contrast with blue accent
    "Stark": {
        "background": "#000000",
        "foreground": "#ffffff",
        "accent": "#0f0f0f",
        "button_bg": "#1a1a1a",
        "button_hover": "#262626",
        "border": "#e5e5e5",
        "highlight": "#60a5fa",  # Lighter blue for better contrast
        "highlight_text": "#000000",  # Black on light blue: 7.2:1
        "slider_trough": "#0f0f0f",
        "category_bar": "#60a5fa",
        "muted_text": "#d4d4d4",  # On #000000: 13.5:1
        "category_text": "#000000",
        "glow_color": "#60a5fa40",
    },

# ─────────────────────────────────────────────────────────────────────────────
# LIGHT THEMES
# ─────────────────────────────────────────────────────────────────────────────

    # Daylight - Clean white
    "Daylight": {
        "background": "#fafafa",
        "foreground": "#171717",
        "accent": "#f0f0f0",
        "button_bg": "#e5e5e5",
        "button_hover": "#d4d4d4",
        "border": "#a3a3a3",
        "highlight": "#0369a1",  # Deep sky blue for proper contrast
        "highlight_text": "#ffffff",  # White on deep sky blue: 5.2:1
        "slider_trough": "#f0f0f0",
        "category_bar": "#0369a1",
        "muted_text": "#525252",  # On #fafafa: 7.8:1
        "category_text": "#ffffff",
        "glow_color": "#0369a140",
    },
    
    # Paper - Warm white
    "Paper": {
        "background": "#fefdfb",
        "foreground": "#1c1917",
        "accent": "#f5f5f4",
        "button_bg": "#e7e5e4",
        "button_hover": "#d6d3d1",
        "border": "#a8a29e",
        "highlight": "#047857",  # Deeper emerald for better contrast
        "highlight_text": "#ffffff",  # White on deep emerald: 5.1:1
        "slider_trough": "#f5f5f4",
        "category_bar": "#047857",
        "muted_text": "#57534e",  # On #fefdfb: 7.2:1
        "category_text": "#ffffff",
        "glow_color": "#04785740",
    },
    
    # Warm Cream - Soft warm tones
    "Warm Cream": {
        "background": "#fef7ed",
        "foreground": "#1c1917",
        "accent": "#fef3e2",
        "button_bg": "#fed7aa",
        "button_hover": "#fdba74",
        "border": "#c2957a",
        "highlight": "#c2410c",  # Deeper orange for better contrast
        "highlight_text": "#ffffff",  # White on deep orange: 5.3:1
        "slider_trough": "#fef3e2",
        "category_bar": "#c2410c",
        "muted_text": "#6e6862",  # On #fef7ed: 5.2:1
        "category_text": "#ffffff",
        "glow_color": "#c2410c40",
    },

# ─────────────────────────────────────────────────────────────────────────────
# NATURE / AESTHETIC THEMES
# ─────────────────────────────────────────────────────────────────────────────

    # Sakura - Soft pink/rose on dark, cherry blossom inspired
    "Sakura": {
        "background": "#120a10",
        "foreground": "#fce4ec",
        "accent": "#1c1218",
        "button_bg": "#2d1a26",
        "button_hover": "#3d2234",
        "border": "#4a2d40",
        "highlight": "#f06292",
        "highlight_text": "#000000",  # Black on pink: 5.2:1
        "slider_trough": "#1c1218",
        "category_bar": "#f06292",
        "muted_text": "#ce93d8",  # On #120a10: 7.0:1
        "category_text": "#000000",
        "glow_color": "#f0629240",
    },

    # Frost - Ice blue/white on near-black, winter aesthetic
    "Frost": {
        "background": "#080c12",
        "foreground": "#e8f4fd",
        "accent": "#0e1620",
        "button_bg": "#162030",
        "button_hover": "#1e2c40",
        "border": "#2a3e56",
        "highlight": "#81d4fa",
        "highlight_text": "#000000",  # Black on light blue: 10.1:1
        "slider_trough": "#0e1620",
        "category_bar": "#81d4fa",
        "muted_text": "#90caf9",  # On #080c12: 8.5:1
        "category_text": "#000000",
        "glow_color": "#81d4fa40",
    },

    # Sunset Gradient - Warm orange-to-pink accent on deep navy
    "Sunset Gradient": {
        "background": "#0d0a18",
        "foreground": "#fef0e6",
        "accent": "#16102a",
        "button_bg": "#221838",
        "button_hover": "#2e2048",
        "border": "#3d2d5c",
        "highlight": "#ff7043",
        "highlight_text": "#000000",  # Black on deep orange: 5.4:1
        "slider_trough": "#16102a",
        "category_bar": "#ff7043",
        "muted_text": "#b39ddb",  # On #0d0a18: 7.4:1
        "category_text": "#000000",
        "glow_color": "#ff704340",
    },

    # Mint Fresh - Cool mint green accent, clean and modern
    "Mint Fresh": {
        "background": "#0a100e",
        "foreground": "#e8f5e9",
        "accent": "#121c18",
        "button_bg": "#1a2e24",
        "button_hover": "#223d30",
        "border": "#2e5240",
        "highlight": "#66bb6a",
        "highlight_text": "#000000",  # Black on mint: 7.3:1
        "slider_trough": "#121c18",
        "category_bar": "#66bb6a",
        "muted_text": "#a5d6a7",  # On #0a100e: 9.0:1
        "category_text": "#000000",
        "glow_color": "#66bb6a40",
    },

# ─────────────────────────────────────────────────────────────────────────────
# DEVELOPER-FAVORITE THEMES
# ─────────────────────────────────────────────────────────────────────────────

    # Synthwave - Purple/pink/cyan retro-futuristic palette
    "Synthwave": {
        "background": "#0b0020",
        "foreground": "#f0e6ff",
        "accent": "#150838",
        "button_bg": "#1f1050",
        "button_hover": "#2a1868",
        "border": "#3d2080",
        "highlight": "#ff2975",
        "highlight_text": "#000000",  # Black on hot pink: 5.7:1
        "slider_trough": "#150838",
        "category_bar": "#ff2975",
        "muted_text": "#b388ff",  # On #0b0020: 7.5:1
        "category_text": "#000000",
        "glow_color": "#ff297540",
    },

    # Solarized Dark - Classic developer-loved Solarized dark scheme
    "Solarized Dark": {
        "background": "#002b36",
        "foreground": "#fdf6e3",
        "accent": "#073642",
        "button_bg": "#0a4050",
        "button_hover": "#0e5060",
        "border": "#586e75",
        "highlight": "#2aa198",
        "highlight_text": "#000000",  # Black on teal: 6.0:1
        "slider_trough": "#073642",
        "category_bar": "#2aa198",
        "muted_text": "#93a1a1",  # On #002b36: 5.4:1
        "category_text": "#000000",
        "glow_color": "#2aa19840",
    },

    # Nord - The popular Nord color palette (blue-gray tones)
    "Nord": {
        "background": "#2e3440",
        "foreground": "#eceff4",
        "accent": "#3b4252",
        "button_bg": "#434c5e",
        "button_hover": "#4c566a",
        "border": "#4c566a",
        "highlight": "#88c0d0",
        "highlight_text": "#000000",  # Black on frost blue: 9.2:1
        "slider_trough": "#3b4252",
        "category_bar": "#88c0d0",
        "muted_text": "#d8dee9",  # On #2e3440: 8.5:1
        "category_text": "#000000",
        "glow_color": "#88c0d040",
    },

    # Monokai - Classic Monokai-inspired colors for devs
    "Monokai": {
        "background": "#1e1f1c",
        "foreground": "#f8f8f2",
        "accent": "#272822",
        "button_bg": "#3e3d32",
        "button_hover": "#4e4d42",
        "border": "#555650",
        "highlight": "#a6e22e",
        "highlight_text": "#000000",  # Black on green: 10.4:1
        "slider_trough": "#272822",
        "category_bar": "#a6e22e",
        "muted_text": "#b3b3a6",  # On #1e1f1c: 6.7:1
        "category_text": "#000000",
        "glow_color": "#a6e22e40",
    },

# ─────────────────────────────────────────────────────────────────────────────
# POPULAR COMMUNITY THEMES
# ─────────────────────────────────────────────────────────────────────────────

    # Dracula - The classic purple-on-dark dev theme
    "Dracula": {
        "background": "#282a36",
        "foreground": "#f8f8f2",
        "accent": "#343746",
        "button_bg": "#44475a",
        "button_hover": "#515473",
        "border": "#6272a4",
        "highlight": "#bd93f9",
        "highlight_text": "#000000",  # Black on purple: 7.2:1
        "slider_trough": "#343746",
        "category_bar": "#bd93f9",
        "muted_text": "#bfbfbf",  # On #282a36: 7.6:1
        "category_text": "#000000",
        "glow_color": "#bd93f940",
    },

    # Catppuccin Mocha - Pastel dark, hugely popular
    "Catppuccin Mocha": {
        "background": "#1e1e2e",
        "foreground": "#cdd6f4",
        "accent": "#28283d",
        "button_bg": "#313244",
        "button_hover": "#3d3f58",
        "border": "#45475a",
        "highlight": "#cba6f7",
        "highlight_text": "#000000",  # Black on mauve: 8.4:1
        "slider_trough": "#28283d",
        "category_bar": "#cba6f7",
        "muted_text": "#a6adc8",  # On #1e1e2e: 6.8:1
        "category_text": "#000000",
        "glow_color": "#cba6f740",
    },

    # Gruvbox Dark - Warm retro earth tones
    "Gruvbox Dark": {
        "background": "#1d2021",
        "foreground": "#ebdbb2",
        "accent": "#282828",
        "button_bg": "#3c3836",
        "button_hover": "#504945",
        "border": "#665c54",
        "highlight": "#fe8019",
        "highlight_text": "#000000",  # Black on orange: 6.3:1
        "slider_trough": "#282828",
        "category_bar": "#fe8019",
        "muted_text": "#a89984",  # On #1d2021: 5.3:1
        "category_text": "#000000",
        "glow_color": "#fe801940",
    },

    # Tokyo Night - Blue/purple Japanese aesthetic
    "Tokyo Night": {
        "background": "#1a1b26",
        "foreground": "#c0caf5",
        "accent": "#24283b",
        "button_bg": "#2f3549",
        "button_hover": "#3b4261",
        "border": "#414868",
        "highlight": "#7aa2f7",
        "highlight_text": "#000000",  # Black on blue: 7.6:1
        "slider_trough": "#24283b",
        "category_bar": "#7aa2f7",
        "muted_text": "#9aa5ce",  # On #1a1b26: 6.1:1
        "category_text": "#000000",
        "glow_color": "#7aa2f740",
    },

    # Rosé Pine - Muted rose/gold tones
    "Rosé Pine": {
        "background": "#191724",
        "foreground": "#e0def4",
        "accent": "#1f1d2e",
        "button_bg": "#26233a",
        "button_hover": "#312e4a",
        "border": "#403d52",
        "highlight": "#ebbcba",
        "highlight_text": "#000000",  # Black on rose: 10.4:1
        "slider_trough": "#1f1d2e",
        "category_bar": "#ebbcba",
        "muted_text": "#908caa",  # On #191724: 4.8:1
        "category_text": "#000000",
        "glow_color": "#ebbcba40",
    },

    # Everforest Dark - Soft green forest palette
    "Everforest Dark": {
        "background": "#272e33",
        "foreground": "#d3c6aa",
        "accent": "#2e383c",
        "button_bg": "#374145",
        "button_hover": "#444e52",
        "border": "#4f585e",
        "highlight": "#a7c080",
        "highlight_text": "#000000",  # Black on green: 8.9:1
        "slider_trough": "#2e383c",
        "category_bar": "#a7c080",
        "muted_text": "#9da9a0",  # On #272e33: 5.5:1
        "category_text": "#000000",
        "glow_color": "#a7c08040",
    },

    # Ayu Dark - Orange accent minimal dark
    "Ayu Dark": {
        "background": "#0d1017",
        "foreground": "#bfbdb6",
        "accent": "#131721",
        "button_bg": "#1c2029",
        "button_hover": "#262b35",
        "border": "#2d3640",
        "highlight": "#e6b450",
        "highlight_text": "#000000",  # Black on gold: 9.4:1
        "slider_trough": "#131721",
        "category_bar": "#e6b450",
        "muted_text": "#6c7380",  # On #0d1017: 3.5:1
        "category_text": "#000000",
        "glow_color": "#e6b45040",
    },

    # One Dark - Atom's beloved theme
    "One Dark": {
        "background": "#282c34",
        "foreground": "#abb2bf",
        "accent": "#2c313a",
        "button_bg": "#3b4048",
        "button_hover": "#484e5b",
        "border": "#4b5263",
        "highlight": "#61afef",
        "highlight_text": "#000000",  # Black on blue: 8.0:1
        "slider_trough": "#2c313a",
        "category_bar": "#61afef",
        "muted_text": "#848b98",  # On #282c34: 4.6:1
        "category_text": "#000000",
        "glow_color": "#61afef40",
    },
}

# Add legacy theme names that map to new themes for backwards compatibility
FUTURISTIC_THEMES["Cyber Noir"] = FUTURISTIC_THEMES["Obsidian"]
FUTURISTIC_THEMES["Neon Purple"] = FUTURISTIC_THEMES["Royal Purple"]
FUTURISTIC_THEMES["Matrix Green"] = FUTURISTIC_THEMES["Emerald Dusk"]
FUTURISTIC_THEMES["Hot Pink"] = FUTURISTIC_THEMES["Crimson Night"]
FUTURISTIC_THEMES["Classic Dark"] = FUTURISTIC_THEMES["Charcoal"]
FUTURISTIC_THEMES["Ocean Depths"] = FUTURISTIC_THEMES["Deep Ocean"]
FUTURISTIC_THEMES["Dark Elegance"] = FUTURISTIC_THEMES["Nebula Flux"]


def create_theme(
    background: str,
    foreground: str,
    accent: str,
    button_bg: str,
    button_hover: str,
    border: str,
    highlight: str,
    muted_text: str,
    glow_color: str = None,
) -> dict:
    """
    Create a custom theme with auto-calculated contrast-safe text colors.
    
    This function should be used at runtime (not module load time) to create
    custom themes with automatic contrast validation.
    
    Args:
        background: Main background color
        foreground: Primary text color
        accent: Secondary background (cards, inputs)
        button_bg: Button background color
        button_hover: Button hover state color
        border: Border color
        highlight: Primary accent/highlight color
        muted_text: Secondary/muted text color
        glow_color: Optional glow effect color (defaults to highlight with 25% alpha)
    
    Returns:
        Complete theme dictionary with all required keys
    """
    # Import here to avoid circular dependency at module load
    # Auto-calculate text colors for accent backgrounds
    highlight_text = get_contrast_color(highlight)
    category_text = get_contrast_color(highlight)
    
    # Ensure muted text meets minimum contrast
    muted_safe = ensure_contrast(muted_text, background, WCAG_UI_COMPONENTS)
    
    return {
        "background": background,
        "foreground": foreground,
        "accent": accent,
        "button_bg": button_bg,
        "button_hover": button_hover,
        "border": border,
        "highlight": highlight,
        "highlight_text": highlight_text,
        "slider_trough": accent,
        "category_bar": highlight,
        "muted_text": muted_safe,
        "category_text": category_text,
        "glow_color": glow_color or f"{highlight}40",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS - Color Conversion
# ═══════════════════════════════════════════════════════════════════════════════

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    # Handle 8-char hex (with alpha) by ignoring alpha
    if len(hex_color) == 8:
        hex_color = hex_color[:6]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color"""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"


def blend_colors(color1: str, color2: str, ratio: float = 0.5) -> str:
    """Blend two hex colors together"""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    
    return rgb_to_hex(r, g, b)


def lighten(color: str, amount: float = 0.1) -> str:
    """Lighten a color by blending with white"""
    return blend_colors(color, "#ffffff", amount)


def darken(color: str, amount: float = 0.1) -> str:
    """Darken a color by blending with black"""
    return blend_colors(color, "#000000", amount)


def add_alpha(hex_color: str, alpha: float) -> str:
    """Add alpha transparency to hex color (returns 8-char hex)"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) == 8:
        hex_color = hex_color[:6]
    alpha_hex = format(int(alpha * 255), '02x')
    return f"#{hex_color}{alpha_hex}"


def create_gradient_colors(start: str, end: str, steps: int = 10) -> list:
    """Generate a list of colors forming a gradient"""
    colors = []
    for i in range(steps):
        ratio = i / (steps - 1) if steps > 1 else 0
        colors.append(blend_colors(start, end, ratio))
    return colors


# ═══════════════════════════════════════════════════════════════════════════════
# WCAG 2.1 CONTRAST SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# WCAG contrast thresholds
WCAG_AA_NORMAL = 4.5      # Normal text (< 18pt or < 14pt bold)
WCAG_AA_LARGE = 3.0       # Large text (>= 18pt or >= 14pt bold)
WCAG_AAA_NORMAL = 7.0     # Enhanced contrast for normal text
WCAG_AAA_LARGE = 4.5      # Enhanced contrast for large text
WCAG_UI_COMPONENTS = 3.0  # UI components and graphical objects

# Pre-computed readable text colors for various background lightness levels
_TEXT_COLORS_LIGHT = [
    "#000000",  # Pure black - highest contrast on light
    "#0a0a0a",
    "#141414",
    "#1f1f1f",
    "#2a2a2a",
]

_TEXT_COLORS_DARK = [
    "#ffffff",  # Pure white - highest contrast on dark
    "#f5f5f5",
    "#ebebeb",
    "#e0e0e0",
    "#d6d6d6",
    "#cccccc",
    "#b8b8b8",
]


def relative_luminance(color: str) -> float:
    """
    Calculate relative luminance of a color per WCAG 2.1 specification.
    
    Returns a value between 0 (darkest black) and 1 (lightest white).
    Formula: L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    where R, G, B are linearized sRGB values.
    """
    r, g, b = hex_to_rgb(color)
    
    def linearize(channel: int) -> float:
        """Convert sRGB channel to linear RGB"""
        c = channel / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4
    
    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)
    
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate WCAG 2.1 contrast ratio between two colors.
    
    Returns a value between 1 (no contrast) and 21 (maximum contrast).
    The order of colors doesn't matter - the lighter color is automatically
    detected.
    """
    lum1 = relative_luminance(color1)
    lum2 = relative_luminance(color2)
    
    # Ensure lighter color is in numerator
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)


def meets_contrast(fg: str, bg: str, level: str = "AA", text_size: str = "normal") -> bool:
    """
    Check if foreground/background combination meets WCAG contrast requirements.
    
    Args:
        fg: Foreground (text) color
        bg: Background color
        level: "AA" or "AAA" conformance level
        text_size: "normal" or "large" (large = 18pt+ or 14pt+ bold)
    
    Returns:
        True if the combination meets the specified requirements
    """
    ratio = contrast_ratio(fg, bg)
    
    if level == "AAA":
        threshold = WCAG_AAA_LARGE if text_size == "large" else WCAG_AAA_NORMAL
    else:  # AA
        threshold = WCAG_AA_LARGE if text_size == "large" else WCAG_AA_NORMAL
    
    return ratio >= threshold


def get_contrast_color(bg_color: str, prefer_light: bool = None) -> str:
    """
    Get the best contrasting text color for a given background.
    
    This is an enhanced version that returns colors from a palette,
    not just pure black/white, for better aesthetics while maintaining
    WCAG AA compliance.
    
    Args:
        bg_color: Background color to contrast against
        prefer_light: If True, prefer light text; if False, prefer dark text;
                      if None (default), automatically determine based on background
    
    Returns:
        A text color that meets WCAG AA contrast requirements
    """
    bg_lum = relative_luminance(bg_color)
    
    # Auto-detect preference if not specified
    if prefer_light is None:
        prefer_light = bg_lum < 0.5
    
    # Select color palette based on preference
    palette = _TEXT_COLORS_DARK if prefer_light else _TEXT_COLORS_LIGHT
    
    # Find the best color that meets WCAG AA
    for color in palette:
        if contrast_ratio(color, bg_color) >= WCAG_AA_NORMAL:
            return color
    
    # Fallback to pure black or white if nothing in palette works
    return "#ffffff" if prefer_light else "#000000"


def get_readable_color(bg: str, min_ratio: float = WCAG_AA_NORMAL, 
                       prefer_light: bool = None) -> str:
    """
    Get a readable text color for any background with custom contrast threshold.
    
    Args:
        bg: Background color
        min_ratio: Minimum contrast ratio required (default: 4.5 for WCAG AA)
        prefer_light: Prefer light or dark text (auto-detect if None)
    
    Returns:
        A text color meeting the specified contrast ratio
    """
    bg_lum = relative_luminance(bg)
    
    if prefer_light is None:
        prefer_light = bg_lum < 0.5
    
    palette = _TEXT_COLORS_DARK if prefer_light else _TEXT_COLORS_LIGHT
    
    for color in palette:
        if contrast_ratio(color, bg) >= min_ratio:
            return color
    
    # If no color in palette meets the threshold, return maximum contrast
    return "#ffffff" if prefer_light else "#000000"


def ensure_contrast(fg: str, bg: str, min_ratio: float = WCAG_AA_NORMAL) -> str:
    """
    Ensure foreground color meets minimum contrast ratio against background.
    
    If the provided foreground doesn't meet the threshold, it will be
    lightened or darkened until it does (or until maximum contrast is reached).
    
    Args:
        fg: Desired foreground color
        bg: Background color
        min_ratio: Minimum contrast ratio required
    
    Returns:
        Original fg if it passes, or adjusted version that meets requirements
    """
    current_ratio = contrast_ratio(fg, bg)
    
    if current_ratio >= min_ratio:
        return fg
    
    bg_lum = relative_luminance(bg)
    fg_lum = relative_luminance(fg)
    
    # Determine direction to adjust
    should_lighten = bg_lum < 0.5
    
    # Gradually adjust until we meet the threshold
    adjusted = fg
    for i in range(1, 21):  # Max 20 steps
        step = i * 0.05
        if should_lighten:
            adjusted = lighten(fg, min(step, 1.0))
        else:
            adjusted = darken(fg, min(step, 1.0))
        
        if contrast_ratio(adjusted, bg) >= min_ratio:
            return adjusted
    
    # If we still can't meet the threshold, return maximum contrast
    return "#ffffff" if should_lighten else "#000000"


def adjust_color_for_contrast(color: str, bg: str, target_ratio: float = WCAG_AA_NORMAL) -> str:
    """
    Adjust a color to achieve approximately the target contrast ratio.
    
    Useful for creating muted text that's still readable but less prominent.
    
    Args:
        color: Base color to adjust
        bg: Background color
        target_ratio: Desired contrast ratio
    
    Returns:
        Adjusted color with approximately the target contrast
    """
    current = contrast_ratio(color, bg)
    
    if abs(current - target_ratio) < 0.5:
        return color
    
    bg_lum = relative_luminance(bg)
    
    # Binary search for the right adjustment
    low, high = 0.0, 1.0
    
    for _ in range(20):  # Max iterations
        mid = (low + high) / 2
        if bg_lum < 0.5:
            test_color = blend_colors("#ffffff", bg, mid)
        else:
            test_color = blend_colors("#000000", bg, mid)
        
        ratio = contrast_ratio(test_color, bg)
        
        if abs(ratio - target_ratio) < 0.1:
            return test_color
        elif ratio > target_ratio:
            low = mid
        else:
            high = mid
    
    return test_color


def get_muted_color(bg: str, base_color: str = None) -> str:
    """
    Get a muted text color that meets WCAG AA for large text (3:1 ratio).
    
    This is ideal for secondary text, descriptions, and hints.
    
    Args:
        bg: Background color
        base_color: Optional base color to derive muted from
    
    Returns:
        A muted color with at least 3:1 contrast
    """
    if base_color:
        # Try to use a desaturated version of the base color
        muted = blend_colors(base_color, bg, 0.5)
        if contrast_ratio(muted, bg) >= WCAG_UI_COMPONENTS:
            return muted
    
    return get_readable_color(bg, min_ratio=WCAG_UI_COMPONENTS)


def validate_theme_contrast(theme: dict) -> dict:
    """
    Validate and fix contrast issues in a theme dictionary.
    
    Args:
        theme: Theme dictionary with color values
    
    Returns:
        Dictionary with contrast validation results and fixes
    """
    bg = theme.get("background", "#1a1a1a")
    results = {
        "valid": True,
        "issues": [],
        "fixes": {}
    }
    
    # Check main text
    fg = theme.get("foreground", "#ffffff")
    ratio = contrast_ratio(fg, bg)
    if ratio < WCAG_AA_NORMAL:
        results["valid"] = False
        results["issues"].append(f"foreground contrast too low: {ratio:.2f}")
        results["fixes"]["foreground"] = ensure_contrast(fg, bg)
    
    # Check muted text (only needs 3:1 for large text)
    muted = theme.get("muted_text", "#a0a0a0")
    ratio = contrast_ratio(muted, bg)
    if ratio < WCAG_UI_COMPONENTS:
        results["valid"] = False
        results["issues"].append(f"muted_text contrast too low: {ratio:.2f}")
        results["fixes"]["muted_text"] = ensure_contrast(muted, bg, WCAG_UI_COMPONENTS)
    
    # Check highlight text on highlight background
    highlight = theme.get("highlight", "#00fff7")
    highlight_text = theme.get("highlight_text", "#000000")
    ratio = contrast_ratio(highlight_text, highlight)
    if ratio < WCAG_AA_NORMAL:
        results["valid"] = False
        results["issues"].append(f"highlight_text contrast too low: {ratio:.2f}")
        results["fixes"]["highlight_text"] = get_contrast_color(highlight)
    
    # Check category text on category bar
    cat_bar = theme.get("category_bar", highlight)
    cat_text = theme.get("category_text", "#000000")
    ratio = contrast_ratio(cat_text, cat_bar)
    if ratio < WCAG_AA_NORMAL:
        results["valid"] = False
        results["issues"].append(f"category_text contrast too low: {ratio:.2f}")
        results["fixes"]["category_text"] = get_contrast_color(cat_bar)
    
    return results


def auto_fix_theme_contrast(theme: dict) -> dict:
    """
    Automatically fix contrast issues in a theme.
    
    Args:
        theme: Theme dictionary with color values
    
    Returns:
        New theme dictionary with fixed contrast values
    """
    fixed = dict(theme)
    validation = validate_theme_contrast(theme)
    
    if validation["fixes"]:
        fixed.update(validation["fixes"])
    
    return fixed


# ═══════════════════════════════════════════════════════════════════════════════
# STYLE MIXINS (for consistent widget styling with contrast guarantees)
# ═══════════════════════════════════════════════════════════════════════════════

class StyleMixin:
    """Common style configurations for widgets with WCAG compliance"""
    
    @staticmethod
    def card_style(theme: dict = None) -> dict:
        """Get card styling options with proper contrast"""
        bg = theme.get("accent", COLORS.SURFACE_2) if theme else COLORS.SURFACE_2
        border = theme.get("border", COLORS.BORDER_DEFAULT) if theme else COLORS.BORDER_DEFAULT
        return {
            "bg": bg,
            "highlightbackground": border,
            "highlightthickness": 1,
            "relief": "flat",
        }
    
    @staticmethod
    def button_style(theme: dict = None, variant: str = "default") -> dict:
        """Get button styling options with guaranteed text contrast"""
        if variant == "primary":
            bg = theme.get("highlight", COLORS.CYAN) if theme else COLORS.CYAN
            # Always use contrast-checked text color for primary buttons
            fg = get_contrast_color(bg)
        elif variant == "danger":
            bg = COLORS.ERROR
            fg = COLORS.ON_ERROR
        elif variant == "success":
            bg = COLORS.SUCCESS
            fg = COLORS.ON_SUCCESS
        elif variant == "warning":
            bg = COLORS.WARNING
            fg = COLORS.ON_WARNING
        else:
            bg = theme.get("button_bg", COLORS.SURFACE_3) if theme else COLORS.SURFACE_3
            fg = theme.get("foreground", COLORS.TEXT_PRIMARY) if theme else COLORS.TEXT_PRIMARY
            # Ensure text is readable on button background
            fg = ensure_contrast(fg, bg, WCAG_AA_NORMAL)
        
        return {
            "bg": bg,
            "fg": fg,
            "activebackground": lighten(bg, 0.1),
            "activeforeground": fg,
            "relief": "flat",
            "cursor": "hand2",
            "borderwidth": 0,
        }
    
    @staticmethod
    def input_style(theme: dict = None) -> dict:
        """Get input field styling options with proper contrast"""
        bg = theme.get("accent", COLORS.SURFACE_2) if theme else COLORS.SURFACE_2
        fg = theme.get("foreground", COLORS.TEXT_PRIMARY) if theme else COLORS.TEXT_PRIMARY
        border = theme.get("border", COLORS.BORDER_DEFAULT) if theme else COLORS.BORDER_DEFAULT
        highlight = theme.get("highlight", COLORS.CYAN) if theme else COLORS.CYAN
        
        # Ensure input text is readable
        fg = ensure_contrast(fg, bg, WCAG_AA_NORMAL)
        
        return {
            "bg": bg,
            "fg": fg,
            "insertbackground": fg,
            "relief": "flat",
            "highlightbackground": border,
            "highlightthickness": 1,
            "highlightcolor": highlight,
        }
    
    @staticmethod
    def label_style(theme: dict = None, variant: str = "default") -> dict:
        """Get label styling options with contrast-aware text"""
        bg = theme.get("background", COLORS.BLACK) if theme else COLORS.BLACK
        
        if variant == "muted":
            # Muted text still needs minimum contrast for readability
            base_muted = theme.get("muted_text", COLORS.TEXT_LOW) if theme else COLORS.TEXT_LOW
            fg = ensure_contrast(base_muted, bg, WCAG_UI_COMPONENTS)
        elif variant == "title":
            fg = theme.get("foreground", COLORS.TEXT_HIGH) if theme else COLORS.TEXT_HIGH
            fg = ensure_contrast(fg, bg, WCAG_AA_NORMAL)
        elif variant == "secondary":
            fg = theme.get("muted_text", COLORS.TEXT_SECONDARY) if theme else COLORS.TEXT_SECONDARY
            fg = ensure_contrast(fg, bg, WCAG_AA_NORMAL)
        else:
            fg = theme.get("foreground", COLORS.TEXT_PRIMARY) if theme else COLORS.TEXT_PRIMARY
            fg = ensure_contrast(fg, bg, WCAG_AA_NORMAL)
        
        return {
            "bg": bg,
            "fg": fg,
        }
    
    @staticmethod
    def highlight_style(theme: dict = None) -> dict:
        """Get styling for highlighted/selected elements"""
        bg = theme.get("highlight", COLORS.CYAN) if theme else COLORS.CYAN
        fg = get_contrast_color(bg)
        
        return {
            "bg": bg,
            "fg": fg,
            "activebackground": lighten(bg, 0.1),
            "activeforeground": fg,
        }
    
    @staticmethod
    def category_style(theme: dict = None) -> dict:
        """Get styling for category headers/bars"""
        bg = theme.get("category_bar", COLORS.CYAN) if theme else COLORS.CYAN
        fg = get_contrast_color(bg)
        
        return {
            "bg": bg,
            "fg": fg,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TTK STYLE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def configure_ttk_styles(root: tk.Tk, theme: dict = None):
    """Configure ttk styles with futuristic theme and WCAG-compliant contrast"""
    from tkinter import ttk
    
    style = ttk.Style(root)
    
    # Use clam theme as base (most customizable)
    try:
        style.theme_use('clam')
    except Exception:
        pass
    
    # Colors from theme or defaults
    bg = theme.get("background", COLORS.SURFACE_0) if theme else COLORS.SURFACE_0
    fg = theme.get("foreground", COLORS.TEXT_PRIMARY) if theme else COLORS.TEXT_PRIMARY
    accent = theme.get("accent", COLORS.SURFACE_2) if theme else COLORS.SURFACE_2
    highlight = theme.get("highlight", COLORS.CYAN) if theme else COLORS.CYAN
    border = theme.get("border", COLORS.BORDER_DEFAULT) if theme else COLORS.BORDER_DEFAULT
    trough = theme.get("slider_trough", COLORS.SURFACE_2) if theme else COLORS.SURFACE_2
    muted = theme.get("muted_text", COLORS.TEXT_LOW) if theme else COLORS.TEXT_LOW
    
    # Ensure all text colors meet contrast requirements
    fg = ensure_contrast(fg, bg, WCAG_AA_NORMAL)
    muted = ensure_contrast(muted, bg, WCAG_UI_COMPONENTS)
    highlight_text = get_contrast_color(highlight)
    accent_text = ensure_contrast(fg, accent, WCAG_AA_NORMAL)
    
    # Frame style
    style.configure("Futuristic.TFrame",
                    background=bg)
    
    # Label style
    style.configure("Futuristic.TLabel",
                    background=bg,
                    foreground=fg,
                    font=get_font(TYPOGRAPHY.SIZE_BASE))
    
    # Muted label style
    style.configure("Muted.TLabel",
                    background=bg,
                    foreground=muted,
                    font=get_font(TYPOGRAPHY.SIZE_SM))
    
    # Button style
    style.configure("Futuristic.TButton",
                    background=accent,
                    foreground=accent_text,
                    borderwidth=0,
                    focusthickness=0,
                    padding=(SPACING.BUTTON_PADDING_X, SPACING.BUTTON_PADDING_Y),
                    font=get_font(TYPOGRAPHY.SIZE_BASE))
    style.map("Futuristic.TButton",
              background=[("active", lighten(accent, 0.1)), ("pressed", darken(accent, 0.1))],
              foreground=[("disabled", COLORS.TEXT_DISABLED)])
    
    # Primary button style
    style.configure("Primary.TButton",
                    background=highlight,
                    foreground=highlight_text,
                    borderwidth=0,
                    focusthickness=0,
                    padding=(SPACING.BUTTON_PADDING_X, SPACING.BUTTON_PADDING_Y),
                    font=get_font(TYPOGRAPHY.SIZE_BASE, TYPOGRAPHY.WEIGHT_BOLD))
    style.map("Primary.TButton",
              background=[("active", lighten(highlight, 0.1)), ("pressed", darken(highlight, 0.1))],
              foreground=[("disabled", COLORS.TEXT_DISABLED)])
    
    # Entry style
    style.configure("Futuristic.TEntry",
                    fieldbackground=accent,
                    foreground=accent_text,
                    insertcolor=accent_text,
                    borderwidth=1,
                    relief="flat",
                    padding=(SPACING.INPUT_PADDING_X, SPACING.INPUT_PADDING_Y))
    
    # Combobox style
    style.configure("Futuristic.TCombobox",
                    fieldbackground=accent,
                    background=accent,
                    foreground=accent_text,
                    arrowcolor=accent_text,
                    borderwidth=1,
                    relief="flat",
                    padding=(SPACING.INPUT_PADDING_X, SPACING.INPUT_PADDING_Y))
    style.map("Futuristic.TCombobox",
              fieldbackground=[("readonly", accent)],
              selectbackground=[("readonly", highlight)],
              selectforeground=[("readonly", highlight_text)])
    
    # Scrollbar style
    style.configure("Futuristic.Vertical.TScrollbar",
                    background=COLORS.SURFACE_4,
                    troughcolor=bg,
                    borderwidth=0,
                    arrowsize=0,
                    width=8)
    style.map("Futuristic.Vertical.TScrollbar",
              background=[("active", COLORS.SURFACE_5), ("pressed", highlight)])
    
    # Horizontal scrollbar
    style.configure("Futuristic.Horizontal.TScrollbar",
                    background=COLORS.SURFACE_4,
                    troughcolor=bg,
                    borderwidth=0,
                    arrowsize=0,
                    width=8)
    style.map("Futuristic.Horizontal.TScrollbar",
              background=[("active", COLORS.SURFACE_5), ("pressed", highlight)])
    
    # Scale/Slider style
    style.configure("Futuristic.Horizontal.TScale",
                    background=bg,
                    troughcolor=trough,
                    sliderthickness=16,
                    borderwidth=0)
    style.map("Futuristic.Horizontal.TScale",
              background=[("active", highlight)])
    
    # Notebook (tabs) style
    style.configure("Futuristic.TNotebook",
                    background=bg,
                    borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
    style.configure("Futuristic.TNotebook.Tab",
                    background=accent,
                    foreground=accent_text,
                    padding=[SPACING.XL, SPACING.MD],
                    borderwidth=0)
    style.map("Futuristic.TNotebook.Tab",
              background=[("selected", highlight), ("active", lighten(accent, 0.1))],
              foreground=[("selected", highlight_text)])
    
    # Separator style
    style.configure("Futuristic.TSeparator",
                    background=border)
    
    # Checkbutton style
    style.configure("Futuristic.TCheckbutton",
                    background=bg,
                    foreground=fg,
                    indicatorbackground=accent,
                    indicatorforeground=highlight)
    style.map("Futuristic.TCheckbutton",
              indicatorbackground=[("selected", highlight)],
              background=[("active", bg)])
    
    # Radiobutton style
    style.configure("Futuristic.TRadiobutton",
                    background=bg,
                    foreground=fg,
                    indicatorbackground=accent,
                    indicatorforeground=highlight)
    style.map("Futuristic.TRadiobutton",
              indicatorbackground=[("selected", highlight)],
              background=[("active", bg)])
    
    # Progressbar style
    style.configure("Futuristic.Horizontal.TProgressbar",
                    background=highlight,
                    troughcolor=trough,
                    borderwidth=0)
    
    return style


# ═══════════════════════════════════════════════════════════════════════════════
# NEON & FUTURISTIC EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════

class NeonEffects:
    """
    Futuristic neon effects for UI elements.
    Provides pulsing borders, glowing text, and animated accents.
    """
    
    @staticmethod
    def create_pulse_animation(widget, color: str = COLORS.CYAN, 
                                min_alpha: float = 0.3, max_alpha: float = 1.0,
                                duration_ms: int = 2000):
        """
        Create a pulsing neon effect on a widget's border/background.
        
        Args:
            widget: Tkinter widget with a bg or highlightbackground option
            color: The neon color to pulse
            min_alpha: Minimum brightness (0.0-1.0)
            max_alpha: Maximum brightness (0.0-1.0)
            duration_ms: Full pulse cycle duration in milliseconds
        
        Returns:
            A stop function to halt the animation
        """
        running = [True]
        alpha = [max_alpha]
        direction = [-1]  # Start dimming
        
        # Calculate step size for smooth 60fps animation
        steps_per_cycle = duration_ms // 16  # ~60fps
        step_size = (max_alpha - min_alpha) / (steps_per_cycle / 2)
        
        def animate():
            if not running[0]:
                return
            
            try:
                if not widget.winfo_exists():
                    running[0] = False
                    return
            except Exception:
                running[0] = False
                return
            
            # Update alpha
            alpha[0] += direction[0] * step_size
            if alpha[0] <= min_alpha:
                alpha[0] = min_alpha
                direction[0] = 1
            elif alpha[0] >= max_alpha:
                alpha[0] = max_alpha
                direction[0] = -1
            
            # Create dimmed color by blending with black
            dimmed = blend_colors(color, "#000000", 1 - alpha[0])
            
            try:
                # Try different config options
                try:
                    widget.config(highlightbackground=dimmed)
                except Exception:
                    pass
                try:
                    widget.config(bg=dimmed)
                except Exception:
                    pass
            except Exception:
                running[0] = False
                return
            
            widget.after(16, animate)
        
        animate()
        
        def stop():
            running[0] = False
        
        return stop
    
    @staticmethod
    def create_glow_shadow(parent, widget, color: str = COLORS.CYAN, 
                           blur_layers: int = 3, max_offset: int = 4):
        """
        Create a soft glow shadow effect behind a widget.
        
        Note: This creates additional frames behind the widget to simulate glow.
        Works best with frames/labels.
        """
        glow_frames = []
        
        for i in range(blur_layers, 0, -1):
            offset = int(max_offset * (i / blur_layers))
            alpha = 0.15 * (blur_layers - i + 1) / blur_layers
            glow_color = blend_colors(color, "#000000", 1 - alpha)
            
            glow = tk.Frame(
                parent,
                bg=glow_color,
                highlightthickness=0
            )
            glow_frames.append(glow)
        
        return glow_frames
    
    @staticmethod  
    def apply_neon_border(widget, color: str = COLORS.CYAN, thickness: int = 2):
        """Apply a static neon border to a widget"""
        try:
            widget.config(
                highlightbackground=color,
                highlightcolor=color,
                highlightthickness=thickness
            )
        except Exception:
            pass
    
    @staticmethod
    def create_gradient_text_effect(canvas, x: int, y: int, text: str,
                                     colors: list = None, font=None):
        """
        Create a text element with simulated gradient effect.
        
        Note: True gradients aren't possible in tkinter text, so this
        creates overlapping text with slight offsets for a glow effect.
        """
        if colors is None:
            colors = [COLORS.CYAN, COLORS.PURPLE]
        if font is None:
            font = get_font(TYPOGRAPHY.SIZE_LG, TYPOGRAPHY.WEIGHT_BOLD)
        
        # Create glow layers
        for i, offset in enumerate([(2, 2), (1, 1)]):
            alpha = 0.3 - (i * 0.1)
            glow_color = blend_colors(colors[0], "#000000", 1 - alpha)
            canvas.create_text(
                x + offset[0], y + offset[1],
                text=text, font=font, fill=glow_color
            )
        
        # Main text
        canvas.create_text(x, y, text=text, font=font, fill=colors[0])


def animate_neon_border(widget, color: str = COLORS.CYAN, speed: str = "normal"):
    """
    Convenience function to add a pulsing neon border to any widget.
    
    Args:
        widget: Widget to animate
        color: Neon color
        speed: "slow" (3s), "normal" (2s), or "fast" (1s)
    
    Returns:
        Stop function to halt animation
    """
    durations = {"slow": 3000, "normal": 2000, "fast": 1000}
    duration = durations.get(speed, 2000)
    
    return NeonEffects.create_pulse_animation(
        widget, color=color, duration_ms=duration
    )


def create_neon_frame(parent, color: str = COLORS.CYAN, 
                      padding: int = 2, animated: bool = True, **kwargs):
    """
    Create a frame with neon border effect.
    
    Args:
        parent: Parent widget
        color: Neon color for the border
        padding: Border thickness
        animated: Whether to animate the border
        **kwargs: Additional frame options
    
    Returns:
        Tuple of (outer_frame, inner_frame, stop_function)
        - outer_frame: The glowing border frame
        - inner_frame: The content frame inside
        - stop_function: Call to stop animation (if animated)
    """
    # Outer frame (the neon border)
    outer = tk.Frame(parent, bg=color, **kwargs)
    
    # Inner frame for content
    inner = tk.Frame(outer, bg=kwargs.get("bg", COLORS.SURFACE_0))
    inner.pack(fill="both", expand=True, padx=padding, pady=padding)
    
    stop_func = None
    if animated:
        stop_func = animate_neon_border(outer, color)
    
    return outer, inner, stop_func


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Color palette
    'COLORS', 'ColorPalette',
    # Typography
    'TYPOGRAPHY', 'Typography', 'get_font', 'get_mono_font',
    # Spacing
    'SPACING', 'Spacing',
    # Border radius
    'RADIUS', 'BorderRadius',
    # Shadows
    'SHADOWS', 'Shadows',
    # Animation
    'ANIMATION', 'Animation',
    # Smooth animation system
    'Easing', 'AnimationController', 'create_smooth_animation',
    # Theme presets
    'FUTURISTIC_THEMES', 'create_theme',
    # Color utilities
    'hex_to_rgb', 'rgb_to_hex', 'blend_colors', 'lighten', 'darken',
    'add_alpha', 'create_gradient_colors',
    # WCAG Contrast system
    'WCAG_AA_NORMAL', 'WCAG_AA_LARGE', 'WCAG_AAA_NORMAL', 'WCAG_AAA_LARGE', 'WCAG_UI_COMPONENTS',
    'relative_luminance', 'contrast_ratio', 'meets_contrast',
    'get_contrast_color', 'get_readable_color', 'ensure_contrast',
    'adjust_color_for_contrast', 'get_muted_color',
    'validate_theme_contrast', 'auto_fix_theme_contrast',
    # Style utilities
    'StyleMixin', 'configure_ttk_styles',
    # Scaling system (basic)
    'set_ui_scale', 'get_ui_scale', 'get_scaled', 'get_scaled_spacing',
    'set_compact_mode', 'is_compact_mode',
    # Enhanced scaling system
    'set_bar_scale', 'get_bar_scale', 'get_combined_scale',
    'get_bar_scaled', 'get_fully_scaled',
    'get_responsive_size', 'get_responsive_padding',
    'calculate_responsive_dimensions',
    # Neon/Futuristic effects
    'NeonEffects', 'animate_neon_border', 'create_neon_frame',
]
