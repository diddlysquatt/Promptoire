"""
SettingsTypes - Type definitions for settings-related data structures
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class IconType(Enum):
    """Types of icons supported by the application"""
    EMOJI = "emoji"
    IMAGE = "image"
    DEFAULT = "default"


class ThemePreset(Enum):
    """Available theme presets"""
    DARK_ELEGANCE = "Dark Elegance"
    OCEAN_DEPTHS = "Ocean Depths"
    SUNSET_GLOW = "Sunset Glow"
    FOREST_MIST = "Forest Mist"
    NEON_DREAMS = "Neon Dreams"
    CYBERPUNK = "Cyberpunk"
    MINIMAL = "Minimal"
    SOLARIZED = "Solarized"
    MONOKAI = "Monokai"
    HIGH_CONTRAST = "High Contrast"
    MIDNIGHT_BLUE = "Midnight Blue"
    AURORA = "Aurora"
    CLASSIC_DARK = "Classic Dark"


@dataclass
class ThemeColors:
    """Color scheme definition for themes"""
    background: str
    foreground: str
    accent: str
    button_bg: str
    button_hover: str
    border: str
    highlight: str
    highlight_text: str
    slider_trough: str
    category_bar: str
    muted_text: Optional[str] = None
    category_text: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation"""
        return {
            "background": self.background,
            "foreground": self.foreground,
            "accent": self.accent,
            "button_bg": self.button_bg,
            "button_hover": self.button_hover,
            "border": self.border,
            "highlight": self.highlight,
            "highlight_text": self.highlight_text,
            "slider_trough": self.slider_trough,
            "category_bar": self.category_bar,
            "muted_text": self.muted_text,
            "category_text": self.category_text
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ThemeColors":
        """Create from dictionary representation"""
        return cls(
            background=data.get("background", "#1a1a1a"),
            foreground=data.get("foreground", "#ffffff"),
            accent=data.get("accent", "#333333"),
            button_bg=data.get("button_bg", "#2a2a2a"),
            button_hover=data.get("button_hover", "#3a3a3a"),
            border=data.get("border", "#444444"),
            highlight=data.get("highlight", "#0ea5e9"),
            highlight_text=data.get("highlight_text", "#ffffff"),
            slider_trough=data.get("slider_trough", "#3a3a3a"),
            category_bar=data.get("category_bar", "#222222"),
            muted_text=data.get("muted_text"),
            category_text=data.get("category_text")
        )


@dataclass
class IconSettings:
    """Icon configuration settings"""
    type: IconType
    value: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation"""
        return {
            "type": self.type.value,
            "value": self.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "IconSettings":
        """Create from dictionary representation"""
        return cls(
            type=IconType(data.get("type", "emoji")),
            value=data.get("value", "🧠")
        )


@dataclass
class Position:
    """Window position coordinates"""
    x: int
    y: int

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary representation"""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Position":
        """Create from dictionary representation"""
        return cls(x=data.get("x", 100), y=data.get("y", 100))


@dataclass
class Size:
    """Window size dimensions"""
    width: int
    height: int

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary representation"""
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Size":
        """Create from dictionary representation"""
        return cls(width=data.get("width", 500), height=data.get("height", 550))


@dataclass
class TraySettings:
    """System tray configuration"""
    show_recents: bool = True
    show_favorites: bool = True
    recents_count: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "show_recents": self.show_recents,
            "show_favorites": self.show_favorites,
            "recents_count": self.recents_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraySettings":
        """Create from dictionary representation"""
        return cls(
            show_recents=data.get("show_recents", True),
            show_favorites=data.get("show_favorites", True),
            recents_count=data.get("recents_count", 5)
        )


@dataclass
class Settings:
    """Main application settings configuration"""
    theme_preset: str
    theme: Dict[str, str]
    position: Position
    icon: IconSettings
    always_on_top: bool
    start_minimized: bool
    opacity: float
    drawer_size: Size
    bar_scale: float
    paste_delay_ms: int
    font_scale: float
    enable_animations: bool
    texture_intensity: float
    tray: TraySettings
    recent_prompts: List[str]
    favorite_prompts: List[str]
    window_decorations: Dict[str, Any]
    background_settings: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "theme_preset": self.theme_preset,
            "theme": self.theme,
            "position": self.position.to_dict(),
            "icon": self.icon.to_dict(),
            "always_on_top": self.always_on_top,
            "start_minimized": self.start_minimized,
            "opacity": self.opacity,
            "drawer_size": self.drawer_size.to_dict(),
            "bar_scale": self.bar_scale,
            "paste_delay_ms": self.paste_delay_ms,
            "font_scale": self.font_scale,
            "enable_animations": self.enable_animations,
            "texture_intensity": self.texture_intensity,
            "tray": self.tray.to_dict(),
            "recent_prompts": self.recent_prompts,
            "favorite_prompts": self.favorite_prompts,
            "window_decorations": self.window_decorations,
            "background_settings": self.background_settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create from dictionary representation"""
        return cls(
            theme_preset=data.get("theme_preset", "Classic Dark"),
            theme=data.get("theme", {}),
            position=Position.from_dict(data.get("position", {"x": 100, "y": 100})),
            icon=IconSettings.from_dict(data.get("icon", {"type": "emoji", "value": "🧠"})),
            always_on_top=data.get("always_on_top", True),
            start_minimized=data.get("start_minimized", False),
            opacity=data.get("opacity", 0.95),
            drawer_size=Size.from_dict(data.get("drawer_size", {"width": 500, "height": 550})),
            bar_scale=data.get("bar_scale", 1.0),
            paste_delay_ms=data.get("paste_delay_ms", 500),
            font_scale=data.get("font_scale", 1.0),
            enable_animations=data.get("enable_animations", True),
            texture_intensity=data.get("texture_intensity", 0.25),
            tray=TraySettings.from_dict(data.get("tray", {})),
            recent_prompts=data.get("recent_prompts", []),
            favorite_prompts=data.get("favorite_prompts", []),
            window_decorations=data.get("window_decorations", {}),
            background_settings=data.get("background_settings", {})
        )


# Type aliases for better readability
SettingsDict = Dict[str, Any]
ThemeDict = Dict[str, str]
PositionDict = Dict[str, int]
SizeDict = Dict[str, int]