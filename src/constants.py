"""
Application Constants for Promptoire
Central configuration and constant definitions
"""

import os
from pathlib import Path

# Application Information
APP_NAME = "Promptoire"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Promptoire Team"
APP_DESCRIPTION = "Interactive Prompt Management System"

# File Paths and Directories
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
OPS_DIR = BASE_DIR / "ops"
DOCS_DIR = OPS_DIR / "docs"
AGENT_LOGS_DIR = OPS_DIR / "agent_logs"
UTILS_DIR = SRC_DIR / "utils"

# Data Files
PROMPTS_FILE = BASE_DIR / "prompts.json"
SETTINGS_FILE = BASE_DIR / "settings.json"
LOGS_DIR = BASE_DIR / "logs"
BACKUPS_DIR = BASE_DIR / "backups"

# Configuration Files
CHROME_EXTENSION_DIR = BASE_DIR / "chrome-extension"
ICONS_DIR = BASE_DIR / "icons"

# File Extensions
JSON_EXT = ".json"
MD_EXT = ".md"
PY_EXT = ".py"
TXT_EXT = ".txt"

# Application Constants
MAX_PROMPT_LENGTH = 10000
MAX_PROMPT_NAME_LENGTH = 100
MAX_CATEGORY_NAME_LENGTH = 50
DEFAULT_ENCODING = "utf-8"

# UI Constants
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1200
WINDOW_DEFAULT_HEIGHT = 800

# Logging Constants
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Agent System Constants
AGENT_PREFIX = "A"
AGENT_LOG_PREFIX = "A"
AGENT_STATUS_PENDING = "pending"
AGENT_STATUS_IN_PROGRESS = "in_progress"
AGENT_STATUS_COMPLETED = "completed"
AGENT_STATUS_FAILED = "failed"

# Validation Constants
VALID_PROMPT_NAME_PATTERN = r"^[a-zA-Z0-9\s\-_]+$"
VALID_CATEGORY_NAME_PATTERN = r"^[a-zA-Z0-9\s\-_]+$"
MIN_PROMPT_LENGTH = 1
MIN_NAME_LENGTH = 1

# Backup Constants
BACKUP_PREFIX = "backup_"
BACKUP_DATE_FORMAT = "%Y%m%d_%H%M%S"
MAX_BACKUP_COUNT = 10

# Chrome Extension Constants
EXTENSION_NAME = "Promptoire Extension"
EXTENSION_VERSION = "1.0.0"

# Development Constants
DEBUG_MODE = False
TEST_MODE = False
DEV_MODE = False

# Error Messages
ERROR_FILE_NOT_FOUND = "File not found: {file_path}"
ERROR_INVALID_JSON = "Invalid JSON format: {error}"
ERROR_VALIDATION_FAILED = "Validation failed: {error}"
ERROR_PERMISSION_DENIED = "Permission denied: {operation}"

# Success Messages
SUCCESS_FILE_CREATED = "File created successfully: {file_path}"
SUCCESS_FILE_UPDATED = "File updated successfully: {file_path}"
SUCCESS_VALIDATION_PASSED = "Validation passed successfully"

# Configuration Keys
CONFIG_APP_NAME = "app_name"
CONFIG_VERSION = "version"
CONFIG_SETTINGS = "settings"
CONFIG_PROMPTS = "prompts"
CONFIG_CATEGORIES = "categories"
CONFIG_USER_PREFERENCES = "user_preferences"

# Time Constants
TIMEOUT_SECONDS = 30
RETRY_DELAY_SECONDS = 1
MAX_RETRIES = 3

# Memory and Performance Constants
MAX_MEMORY_USAGE_MB = 512
CACHE_SIZE = 100
BUFFER_SIZE = 8192

# Security Constants
ENCRYPTION_ENABLED = False
SECURE_MODE = False

# Export/Import Constants
EXPORT_FORMATS = ["json", "csv", "txt"]
DEFAULT_EXPORT_FORMAT = "json"
IMPORT_MAX_SIZE_MB = 10

# Template Constants
TEMPLATE_PLACEHOLDER_START = "{{"
TEMPLATE_PLACEHOLDER_END = "}}"
TEMPLATE_VARIABLE_PATTERN = r"\{\{(\w+)\}\}"

# Feature Flags
FEATURE_ADVANCED_TEMPLATES = True
FEATURE_CHROME_EXTENSION = True
FEATURE_PLUGIN_SYSTEM = False
FEATURE_DATA_ENCRYPTION = False
FEATURE_API_INTERFACE = False

# Development Tools
DIAGNOSTICS_ENABLED = True
DEBUG_LOGGING = False
PERFORMANCE_MONITORING = False

# Default Settings
DEFAULT_SETTINGS = {
    "theme": "light",
    "language": "en",
    "auto_save": True,
    "auto_backup": True,
    "backup_interval_hours": 24,
    "max_recent_prompts": 10,
    "window_width": WINDOW_DEFAULT_WIDTH,
    "window_height": WINDOW_DEFAULT_HEIGHT,
    "window_maximized": False
}

# Environment Variables
ENV_DEBUG = "PROMPTOIRE_DEBUG"
ENV_TEST = "PROMPTOIRE_TEST"
ENV_DEV = "PROMPTOIRE_DEV"

# Regular Expressions
REGEX_EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
REGEX_URL = r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?"
REGEX_PHONE = r"^\+?1?-?\.?\s?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$"

# HTTP Constants (for future API integration)
HTTP_TIMEOUT = 30
HTTP_RETRY_COUNT = 3
HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_SERVER_ERROR = 500

# Database Constants (for future database integration)
DB_CONNECTION_TIMEOUT = 30
DB_MAX_CONNECTIONS = 10
DB_POOL_SIZE = 5

# Monitoring and Analytics
ANALYTICS_ENABLED = False
USAGE_TRACKING = False
PERFORMANCE_TRACKING = False

# Compatibility
MIN_PYTHON_VERSION = (3, 8)
SUPPORTED_PLATFORMS = ["win32", "linux", "darwin"]

# UI Constants extracted from promptoire.py
DEFAULT_WINDOW_POSITION = {"x": 100, "y": 100}
DEFAULT_DRAWER_SIZE = {"width": 500, "height": 550}
DEFAULT_BAR_SCALE = 1.0
DEFAULT_FONT_SCALE = 1.0
DEFAULT_OPACITY = 0.95
DEFAULT_TEXTURE_INTENSITY = 0.25

# Scale limits
MIN_BAR_SCALE = 0.8
MAX_BAR_SCALE = 2.0
MIN_FONT_SCALE = 0.8
MAX_FONT_SCALE = 1.3

# Animation and timing delays
MINIMIZE_DELAY_MS = 200
SHOW_WINDOW_DELAY_MS = 150
ENFORCE_BORDERLESS_DELAYS = [10, 100, 250]
TOOLTIP_FADE_DELAY_MS = 100
PASTE_DELAY_MS = 500
DRAWER_FADE_STEP_MS = 30
DRAWER_FADE_INCREMENT = 0.15
DRAWER_INITIAL_ALPHA = 0.1

# UI component sizes
BASE_BUTTON_SIZE = 100
BASE_BUTTON_HEIGHT = 24
COMPACT_BUTTON_SIZE = 7
DEFAULT_BUTTON_SIZE = 8
LARGE_BUTTON_SIZE = 10
DEFAULT_ICON_SIZE = 16
DEFAULT_ICON_PAD = 6
DEFAULT_ICON_PATY = 3
TOOLTIP_OFFSET = 6

# Grid layout weights
GRID_WEIGHTS = {
    "icon_button": 1,
    "import_button": 0,
    "settings_button": 0,
    "prompts_button": 0,
    "drag_handle": 0
}

# Color blending ratios
DEFAULT_OUTLINE_BLEND = 0.35
DEFAULT_GLOW_BLEND = 0.25
DEFAULT_SHADOW_BLEND = 0.45
DEFAULT_GRADIENT_START_BLEND = 0.28
DEFAULT_GRADIENT_END_BLEND = 0.3
DEFAULT_MOUNTAIN_BLEND = 0.35
DEFAULT_STONE_BLEND = 0.45
DEFAULT_STONE_OUTLINE_BLEND = 0.2
BUTTON_HOVER_BLEND = 0.6
HANDLE_BLEND = 0.4
HANDLE_HOVER_BLEND = 0.45
BUTTON_PRESS_BLEND = 0.2

# Color values
DEFAULT_WHITE_COLOR = "#ffffff"
DEFAULT_BLACK_COLOR = "#000000"
DEFAULT_MUTED_TEXT_COLOR = "#666666"
DEFAULT_BORDER_COLOR = "#555555"
DEFAULT_SEARCH_ICON_COLOR = "#888888"

# Theme presets - imported from design_system for single source of truth
# Legacy import for backwards compatibility; all themes now defined in design_system.py
try:
    from .ui.design_system import FUTURISTIC_THEMES as THEME_PRESETS
except ImportError:
    # Fallback minimal theme if design_system not available
    THEME_PRESETS = {
        "Classic Dark": {
            "background": "#1a1a1a", "foreground": "#ffffff", "accent": "#333333",
            "button_bg": "#2a2a2a", "button_hover": "#3a3a3a", "border": "#444444",
            "highlight": "#0ea5e9", "highlight_text": "#ffffff", "slider_trough": "#3a3a3a",
            "category_bar": "#222222", "muted_text": "#a0aec0", "category_text": "#ffffff"
        }
    }

# System constants
WINDOWS_DPI_AWARENESS = 2  # PROCESS_PER_MONITOR_DPI_AWARE
GWL_STYLE = -16
GWL_EXSTYLE = -20
CSIDL_DESKTOPDIRECTORY = 0
SHGFP_TYPE_CURRENT = 0
MAX_PATH_LENGTH = 260

# ID generation
PROMPT_ID_PREFIX = "prm_"
CATEGORY_ID_PREFIX = "cat_"
ID_LENGTH = 12

# List limits
MAX_RECENT_PROMPTS = 20
MAX_NOTIFICATION_LENGTH = 60
DEFAULT_TRAY_RECENTS_COUNT = 5
MAX_EVENT_LOG_ENTRIES = 1000

# Font sizes
DEFAULT_FONT_SIZE = 9
DEFAULT_TITLE_FONT_SIZE = 11
DEFAULT_SEARCH_FONT_SIZE = 10
DEFAULT_STATS_FONT_SIZE = 8
DEFAULT_BUTTON_FONT_SIZE = 10
DEFAULT_EMOJI_FONT_SIZE = 12
DEFAULT_DRAG_HANDLE_FONT_SIZE = 10

# Padding and margins
DEFAULT_PADX = 8
DEFAULT_PADY = 4
DEFAULT_CONTAINER_PADX = 10
DEFAULT_CONTAINER_PADY = 10
DEFAULT_SEARCH_PADX = 5
DEFAULT_SEARCH_PADY = 2
DEFAULT_SEARCH_ENTRY_PADX = 3
DEFAULT_SEARCH_ENTRY_PADY = 3
DEFAULT_HEADER_PADY = 6
DEFAULT_STATS_PADY = 5
DEFAULT_HINT_PADX = 6
DEFAULT_HINT_PADY = 2

# Window decoration settings
DEFAULT_HIGHLIGHT_THICKNESS = 1
DEFAULT_BORDER_WIDTH = 0
DEFAULT_RELIEF = "flat"
DEFAULT_BUTTON_RELIEF = "flat"
DEFAULT_HOVER_RELIEF = "solid"

# Search and filtering
DEFAULT_SEARCH_PLACEHOLDER = "Search prompts..."
MIN_SEARCH_LENGTH = 1
MAX_SEARCH_RESULTS = 100

# Placeholder patterns
PLACEHOLDER_REGEX_PATTERN = r"\{([A-Za-z_][A-Za-z0-9_]{0,31})\}"
PLACEHOLDER_MAX_NAME_LENGTH = 32
NUMERIC_BRACE_PATTERN = r"\{\d+(?:,\d+)?\}"

# Image processing
DEFAULT_ICON_SIZE_PIL = (24, 24)
IMAGE_RESAMPLING_METHOD = "LANCZOS"

# URLs
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_GISTS_ENDPOINT = "/gists"
STRIPE_COFFEE_URL = "https://buy.stripe.com/cNiaEW3c0bsxcTL9gV3ZK00"

# File types
JSON_FILE_TYPE = [("JSON files", "*.json")]
IMAGE_FILE_TYPES = [("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")]