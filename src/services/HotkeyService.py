"""
Hotkey Service - Handles all hotkey operations for the Promptoire application
"""
import ctypes
from ctypes import wintypes
import logging
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    WM_HOTKEY = 0x0312
    WM_QUIT = 0x0012

    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000

    _WIN32_MODIFIERS = {
        "alt": MOD_ALT,
        "ctrl": MOD_CONTROL,
        "control": MOD_CONTROL,
        "shift": MOD_SHIFT,
        "windows": MOD_WIN,
        "win": MOD_WIN,
        "cmd": MOD_WIN,
        "command": MOD_WIN,
    }

    _WIN32_VK_MAP = {
        "space": 0x20,
        "enter": 0x0D,
        "return": 0x0D,
        "tab": 0x09,
        "esc": 0x1B,
        "escape": 0x1B,
        "backspace": 0x08,
        "delete": 0x2E,
        "del": 0x2E,
        "insert": 0x2D,
        "home": 0x24,
        "end": 0x23,
        "page up": 0x21,
        "pageup": 0x21,
        "page down": 0x22,
        "pagedown": 0x22,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
        "`": 0xC0,
    }


class HotkeyService:
    """Service class for handling global and local hotkey operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registered_hotkeys: Dict[str, Dict[str, Any]] = {}
        self.hotkey_registered = False
        self._recording_hotkey = False

        # Win32 fallback state (when keyboard module is unavailable or fails).
        self._win32_lock = threading.RLock()
        self._win32_hotkeys: Dict[int, Dict[str, Any]] = {}
        self._win32_listener_thread: Optional[threading.Thread] = None
        self._win32_listener_ready = threading.Event()
        self._win32_listener_running = False
        self._win32_thread_id = 0
        self._next_hotkey_id = 1

    def is_available(self) -> bool:
        """Check whether a global hotkey backend is available."""
        return KEYBOARD_AVAILABLE or IS_WINDOWS

    def normalize_hotkey_string(self, raw: str) -> str:
        """
        Normalize a hotkey string to a consistent format.

        Args:
            raw: Raw hotkey string (e.g., "ctrl+alt+x", "Ctrl + Alt + X")

        Returns:
            str: Normalized hotkey string (e.g., "ctrl+alt+x")
        """
        if not isinstance(raw, str):
            return ""

        normalized = raw.lower().replace(" ", "").replace("-", "+")
        parts = [part.strip() for part in normalized.split("+") if part.strip()]

        modifier_map = {
            "ctrl": "ctrl",
            "control": "ctrl",
            "alt": "alt",
            "shift": "shift",
            "win": "windows",
            "windows": "windows",
            "cmd": "windows",
            "command": "windows",
        }

        key_map = {
            "space": "space",
            "enter": "enter",
            "return": "enter",
            "tab": "tab",
            "escape": "esc",
            "esc": "esc",
            "backspace": "backspace",
            "delete": "delete",
            "del": "delete",
            "insert": "insert",
            "home": "home",
            "end": "end",
            "pageup": "page up",
            "pagedown": "page down",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "f1": "f1",
            "f2": "f2",
            "f3": "f3",
            "f4": "f4",
            "f5": "f5",
            "f6": "f6",
            "f7": "f7",
            "f8": "f8",
            "f9": "f9",
            "f10": "f10",
            "f11": "f11",
            "f12": "f12",
        }

        modifiers: List[str] = []
        main_key: Optional[str] = None

        for part in parts:
            if part in modifier_map:
                mod = modifier_map[part]
                if mod not in modifiers:
                    modifiers.append(mod)
            elif part in key_map:
                main_key = key_map[part]
            elif len(part) == 1:
                main_key = part.lower()
            else:
                main_key = part

        if main_key:
            return "+".join(modifiers + [main_key])
        if modifiers:
            return "+".join(modifiers)
        return ""

    def is_valid_hotkey_str(self, hotkey: str) -> bool:
        """
        Validate if a hotkey string is properly formatted and supported.

        Args:
            hotkey: Hotkey string to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(hotkey, str) or not hotkey.strip():
            return False

        try:
            normalized = self.normalize_hotkey_string(hotkey)
            if not normalized:
                return False

            parts = normalized.split("+")
            if len(parts) > 4:
                return False

            main_keys = [p for p in parts if p not in ["ctrl", "alt", "shift", "windows"]]
            if len(main_keys) > 1:
                return False

            if not main_keys:
                return False

            return True
        except Exception:
            return False

    def _parse_hotkey_for_win32(self, normalized_hotkey: str) -> Tuple[int, Optional[int]]:
        """Translate normalized hotkey text to Win32 modifier flags + VK code."""
        if not IS_WINDOWS or not normalized_hotkey:
            return 0, None

        parts = [p.strip().lower() for p in normalized_hotkey.split("+") if p.strip()]
        modifiers = 0
        main_key: Optional[str] = None

        for part in parts:
            if part in _WIN32_MODIFIERS:
                modifiers |= _WIN32_MODIFIERS[part]
            else:
                main_key = part

        if not main_key:
            return modifiers, None

        if len(main_key) == 1:
            ch = main_key.upper()
            if "A" <= ch <= "Z" or "0" <= ch <= "9":
                return modifiers, ord(ch)

        if main_key in _WIN32_VK_MAP:
            return modifiers, _WIN32_VK_MAP[main_key]

        if main_key.startswith("f") and main_key[1:].isdigit():
            fn = int(main_key[1:])
            if 1 <= fn <= 24:
                return modifiers, 0x6F + fn  # VK_F1 starts at 0x70

        return modifiers, None

    def _win32_hotkey_loop(self):
        """Background message loop for WM_HOTKEY handling."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        self._win32_thread_id = int(kernel32.GetCurrentThreadId())
        self._win32_listener_ready.set()

        msg = wintypes.MSG()

        while self._win32_listener_running:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result <= 0:
                break

            if msg.message == WM_HOTKEY:
                hotkey_id = int(msg.wParam)
                callback = None
                with self._win32_lock:
                    entry = self._win32_hotkeys.get(hotkey_id)
                    if entry:
                        callback = entry.get("callback")
                if callback:
                    try:
                        callback()
                    except Exception as e:
                        self.logger.error("Win32 hotkey callback failed: %s", e)

            try:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            except Exception:
                pass

        # Best-effort cleanup on loop termination.
        with self._win32_lock:
            ids = list(self._win32_hotkeys.keys())
        for hotkey_id in ids:
            try:
                user32.UnregisterHotKey(None, int(hotkey_id))
            except Exception:
                pass

        with self._win32_lock:
            self._win32_hotkeys.clear()
        self._win32_thread_id = 0
        self._win32_listener_running = False
        self._win32_listener_ready.clear()

    def _ensure_win32_listener(self) -> bool:
        """Start the Win32 listener thread if not already running."""
        if not IS_WINDOWS:
            return False

        with self._win32_lock:
            if self._win32_listener_running and self._win32_listener_thread and self._win32_listener_thread.is_alive():
                return True

            self._win32_listener_running = True
            self._win32_listener_ready.clear()
            self._win32_listener_thread = threading.Thread(
                target=self._win32_hotkey_loop,
                name="PromptoireWin32Hotkeys",
                daemon=True,
            )
            self._win32_listener_thread.start()

        self._win32_listener_ready.wait(timeout=1.0)
        return bool(self._win32_thread_id)

    def _stop_win32_listener(self):
        """Stop the Win32 listener thread cleanly."""
        if not IS_WINDOWS:
            return

        with self._win32_lock:
            thread_id = int(self._win32_thread_id or 0)
            thread = self._win32_listener_thread
            self._win32_listener_running = False

        if thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass

        if thread and thread.is_alive():
            thread.join(timeout=1.0)

        with self._win32_lock:
            self._win32_listener_thread = None
            self._win32_thread_id = 0
            self._win32_listener_ready.clear()

    def _register_hotkey_win32(self, normalized_hotkey: str, callback: Callable,
                               name: str = "", suppress: bool = False) -> bool:
        """Register a global hotkey via RegisterHotKey API."""
        if not IS_WINDOWS:
            return False

        if not self._ensure_win32_listener():
            self.logger.warning("Win32 hotkey listener unavailable")
            return False

        modifiers, vk_code = self._parse_hotkey_for_win32(normalized_hotkey)
        if vk_code is None:
            self.logger.warning("Hotkey unsupported by Win32 backend: %s", normalized_hotkey)
            return False

        with self._win32_lock:
            hotkey_id = self._next_hotkey_id
            self._next_hotkey_id += 1

        flags = int(modifiers | MOD_NOREPEAT)
        success = bool(ctypes.windll.user32.RegisterHotKey(None, int(hotkey_id), flags, int(vk_code)))
        if not success:
            self.logger.warning("Win32 RegisterHotKey failed for: %s", normalized_hotkey)
            return False

        with self._win32_lock:
            self._win32_hotkeys[int(hotkey_id)] = {
                "hotkey": normalized_hotkey,
                "callback": callback,
                "name": name or normalized_hotkey,
            }

        self.registered_hotkeys[normalized_hotkey] = {
            "name": name or normalized_hotkey,
            "callback": callback,
            "suppress": bool(suppress),
            "registered_time": time.time(),
            "backend": "win32",
            "id": int(hotkey_id),
        }
        self.hotkey_registered = True
        self.logger.info("Registered hotkey via Win32: %s (%s)", normalized_hotkey, name or normalized_hotkey)
        return True

    def register_hotkey(self, hotkey: str, callback: Callable, name: str = "",
                       suppress: bool = False, overwrite: bool = False) -> bool:
        """
        Register a global hotkey.

        Args:
            hotkey: Hotkey string (e.g., "ctrl+alt+x")
            callback: Function to call when hotkey is pressed
            name: Optional name for the hotkey
            suppress: Whether to suppress key stroke (keyboard backend only)
            overwrite: Whether to overwrite existing hotkey

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            normalized_hotkey = self.normalize_hotkey_string(hotkey)
            if not normalized_hotkey:
                self.logger.error("Invalid hotkey: %s", hotkey)
                return False

            if normalized_hotkey in self.registered_hotkeys:
                if not overwrite:
                    self.logger.warning("Hotkey already registered: %s", normalized_hotkey)
                    return False
                self.unregister_hotkey(normalized_hotkey)

            # Preferred backend: keyboard module.
            if KEYBOARD_AVAILABLE:
                try:
                    handle = keyboard.add_hotkey(normalized_hotkey, callback, suppress=bool(suppress))
                    self.registered_hotkeys[normalized_hotkey] = {
                        "name": name or normalized_hotkey,
                        "callback": callback,
                        "suppress": bool(suppress),
                        "registered_time": time.time(),
                        "backend": "keyboard",
                        "id": handle,
                    }
                    self.hotkey_registered = True
                    self.logger.info("Registered hotkey via keyboard: %s (%s)", normalized_hotkey, name or normalized_hotkey)
                    return True
                except Exception as e:
                    self.logger.warning("Keyboard backend failed for %s: %s", normalized_hotkey, e)

            # Fallback backend: Win32 RegisterHotKey.
            return self._register_hotkey_win32(normalized_hotkey, callback, name=name, suppress=suppress)
        except Exception as e:
            self.logger.error("Error registering hotkey %s: %s", hotkey, e)
            return False

    def unregister_hotkey(self, hotkey: str) -> bool:
        """
        Unregister a specific hotkey.

        Args:
            hotkey: Hotkey string to unregister

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            normalized_hotkey = self.normalize_hotkey_string(hotkey)
            entry = self.registered_hotkeys.get(normalized_hotkey)
            if not entry:
                self.logger.warning("Hotkey not found for unregistration: %s", normalized_hotkey)
                return False

            backend = entry.get("backend", "keyboard")
            if backend == "keyboard" and KEYBOARD_AVAILABLE:
                handle = entry.get("id", normalized_hotkey)
                try:
                    keyboard.remove_hotkey(handle)
                except Exception:
                    keyboard.remove_hotkey(normalized_hotkey)
            elif backend == "win32" and IS_WINDOWS:
                hotkey_id = int(entry.get("id", 0))
                if hotkey_id:
                    try:
                        ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
                    except Exception:
                        pass
                    with self._win32_lock:
                        self._win32_hotkeys.pop(hotkey_id, None)
                    if not self._win32_hotkeys:
                        self._stop_win32_listener()

            del self.registered_hotkeys[normalized_hotkey]
            self.hotkey_registered = bool(self.registered_hotkeys)
            self.logger.info("Unregistered hotkey: %s", normalized_hotkey)
            return True
        except Exception as e:
            self.logger.error("Error unregistering hotkey %s: %s", hotkey, e)
            return False

    def unregister_all_hotkeys(self) -> bool:
        """Unregister all registered hotkeys."""
        try:
            for hotkey in list(self.registered_hotkeys.keys()):
                try:
                    self.unregister_hotkey(hotkey)
                except Exception:
                    pass

            if KEYBOARD_AVAILABLE:
                try:
                    keyboard.unhook_all_hotkeys()
                except Exception:
                    pass

            if IS_WINDOWS:
                with self._win32_lock:
                    ids = list(self._win32_hotkeys.keys())
                for hotkey_id in ids:
                    try:
                        ctypes.windll.user32.UnregisterHotKey(None, int(hotkey_id))
                    except Exception:
                        pass
                with self._win32_lock:
                    self._win32_hotkeys.clear()
                self._stop_win32_listener()

            self.registered_hotkeys.clear()
            self.hotkey_registered = False
            self.logger.info("All hotkeys unregistered")
            return True
        except Exception as e:
            self.logger.error("Error unregistering all hotkeys: %s", e)
            return False

    def record_hotkey(self, timeout: float = 30.0) -> Optional[str]:
        """
        Record a hotkey from user input.

        Args:
            timeout: Maximum time to wait for hotkey input

        Returns:
            str: Normalized hotkey string if successful, None otherwise
        """
        if not KEYBOARD_AVAILABLE:
            self.logger.warning("Keyboard module not available for hotkey recording")
            return None

        try:
            if self._recording_hotkey:
                self.logger.warning("Hotkey recording already in progress")
                return None

            self._recording_hotkey = True
            self.logger.info("Starting hotkey recording...")

            # keyboard.read_hotkey handles timing internally; timeout kept for API compatibility.
            _ = timeout
            hotkey = keyboard.read_hotkey(suppress=False)
            normalized = self.normalize_hotkey_string(hotkey)

            if normalized and self.is_valid_hotkey_str(normalized):
                self.logger.info("Recorded hotkey: %s", normalized)
                return normalized

            self.logger.warning("Invalid hotkey recorded: %s", hotkey)
            return None
        except Exception as e:
            self.logger.error("Error recording hotkey: %s", e)
            return None
        finally:
            self._recording_hotkey = False

    def stop_recording(self):
        """Stop hotkey recording if in progress."""
        if self._recording_hotkey:
            self._recording_hotkey = False
            self.logger.info("Hotkey recording stopped")

    def get_registered_hotkeys(self) -> List[Dict[str, Any]]:
        """
        Get list of all registered hotkeys.

        Returns:
            List of dictionaries containing hotkey information
        """
        return [
            {
                "hotkey": hotkey,
                "name": info.get("name", hotkey),
                "suppress": bool(info.get("suppress", False)),
                "registered_time": info.get("registered_time", 0.0),
                "backend": info.get("backend", "keyboard"),
            }
            for hotkey, info in self.registered_hotkeys.items()
        ]

    def get_common_hotkey_choices(self) -> List[str]:
        """
        Get a list of common hotkey choices for user selection.

        Returns:
            List of common hotkey combinations
        """
        return [
            "alt+z",
            "alt+c",
            "ctrl+alt+x",
            "ctrl+alt+p",
            "ctrl+alt+space",
            "ctrl+shift+a",
            "ctrl+shift+p",
            "alt+space",
            "ctrl+`",
            "alt+`",
            "f6",
            "f7",
            "f8",
            "ctrl+shift+`",
        ]

    def test_hotkey(self, hotkey: str) -> Dict[str, Any]:
        """
        Test if a hotkey is properly formatted and can be registered.

        Args:
            hotkey: Hotkey string to test

        Returns:
            Dictionary with test results
        """
        result: Dict[str, Any] = {
            "original": hotkey,
            "normalized": self.normalize_hotkey_string(hotkey),
            "valid": False,
            "available": False,
            "error": None,
        }

        try:
            normalized = result["normalized"]
            if not normalized:
                result["error"] = "Invalid hotkey format"
                return result

            result["valid"] = self.is_valid_hotkey_str(normalized)
            if not result["valid"]:
                result["error"] = "Invalid hotkey format"
                return result

            result["available"] = normalized not in self.registered_hotkeys
            if not result["available"]:
                result["error"] = "Hotkey already registered"
                return result

            if not self.is_available():
                result["error"] = "No global hotkey backend available"
        except Exception as e:
            result["error"] = str(e)

        return result

    def simulate_key_press(self, key: str) -> bool:
        """
        Simulate a key press.

        Args:
            key: Key or key combination to simulate

        Returns:
            bool: True if successful, False otherwise
        """
        if not KEYBOARD_AVAILABLE:
            return False

        try:
            keyboard.send(key)
            return True
        except Exception as e:
            self.logger.error("Error simulating key press %s: %s", key, e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the hotkey service.

        Returns:
            Dictionary with service status information
        """
        return {
            "keyboard_available": KEYBOARD_AVAILABLE,
            "win32_available": IS_WINDOWS,
            "hotkey_registered": self.hotkey_registered,
            "registered_count": len(self.registered_hotkeys),
            "recording_hotkey": self._recording_hotkey,
            "registered_hotkeys": self.get_registered_hotkeys(),
        }

    def __del__(self):
        """Cleanup on shutdown."""
        try:
            self.unregister_all_hotkeys()
        except Exception:
            pass
