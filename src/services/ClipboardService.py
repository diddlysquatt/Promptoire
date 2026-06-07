"""
Clipboard Service - Handles all clipboard operations for the Promptoire application
"""
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Union
import logging

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class ClipboardService:
    """Service class for handling clipboard operations"""

    def __init__(self, root: tk.Tk = None):
        """
        Initialize clipboard service

        Args:
            root: Tkinter root window for tkinter clipboard operations
        """
        self.root = root
        self.logger = logging.getLogger(__name__)
        self._fallback_root = None

    def _ensure_root(self):
        """Ensure we have a root window for tkinter clipboard operations"""
        if self.root is None:
            if self._fallback_root is None:
                self._fallback_root = tk.Tk()
                self._fallback_root.withdraw()  # Hide the window
            return self._fallback_root
        return self.root

    def copy_to_clipboard(self, text: str, show_confirmation: bool = False) -> bool:
        """
        Copy text to clipboard using available methods

        Args:
            text: Text to copy to clipboard
            show_confirmation: Whether to show a confirmation message

        Returns:
            bool: True if successful, False otherwise
        """
        if not text or not isinstance(text, str):
            self.logger.warning("Invalid text provided for clipboard copy")
            return False

        try:
            # Try pyperclip first (more reliable)
            if PYPERCLIP_AVAILABLE:
                pyperclip.copy(text)
                if show_confirmation:
                    messagebox.showinfo("Copied", "Text copied to clipboard.")
                return True

            # Fallback to tkinter clipboard
            root = self._ensure_root()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()  # Ensure clipboard is updated

            if show_confirmation:
                messagebox.showinfo("Copied", "Text copied to clipboard.")
            return True

        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")
            if show_confirmation:
                messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")
            return False

    def get_clipboard_text(self) -> Optional[str]:
        """
        Get text from clipboard using available methods

        Returns:
            str: Clipboard text if successful, None otherwise
        """
        try:
            # Try pyperclip first (more reliable)
            if PYPERCLIP_AVAILABLE:
                return pyperclip.paste()

            # Fallback to tkinter clipboard
            root = self._ensure_root()
            try:
                clipboard_text = root.clipboard_get()
                return clipboard_text if clipboard_text else None
            except tk.TclError:
                # Clipboard is empty or contains non-text data
                return None

        except Exception as e:
            self.logger.error(f"Error getting clipboard text: {e}")
            return None

    def clear_clipboard(self) -> bool:
        """
        Clear the clipboard

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try pyperclip first
            if PYPERCLIP_AVAILABLE:
                pyperclip.copy('')  # Copy empty string
                return True

            # Fallback to tkinter clipboard
            root = self._ensure_root()
            root.clipboard_clear()
            root.update()
            return True

        except Exception as e:
            self.logger.error(f"Error clearing clipboard: {e}")
            return False

    def copy_with_paste_simulation(self, text: str) -> bool:
        """
        Copy text to clipboard and simulate paste (Ctrl+V)

        Args:
            text: Text to copy and paste

        Returns:
            bool: True if successful, False otherwise
        """
        if self.copy_to_clipboard(text):
            try:
                if KEYBOARD_AVAILABLE:
                    import time
                    time.sleep(0.1)  # Small delay to ensure clipboard is ready
                    keyboard.send("ctrl+v")
                    return True
                else:
                    self.logger.warning("Keyboard module not available for paste simulation")
                    return False
            except Exception as e:
                self.logger.error(f"Error simulating paste: {e}")
                return False
        return False

    def copy_prompt_with_formatting(self, prompt_text: str, prompt_name: str = "",
                                  show_confirmation: bool = True) -> bool:
        """
        Copy a formatted prompt to clipboard

        Args:
            prompt_text: The prompt text to copy
            prompt_name: Optional name for the prompt
            show_confirmation: Whether to show confirmation message

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format the prompt if name is provided
            if prompt_name:
                formatted_text = f"=== {prompt_name} ===\n\n{prompt_text}"
            else:
                formatted_text = prompt_text

            return self.copy_to_clipboard(formatted_text, show_confirmation)

        except Exception as e:
            self.logger.error(f"Error copying formatted prompt: {e}")
            return False

    def copy_multiple_prompts(self, prompts: list, separator: str = "\n\n---\n\n",
                            show_confirmation: bool = True) -> bool:
        """
        Copy multiple prompts to clipboard with separators

        Args:
            prompts: List of prompt dictionaries with 'text' and optional 'name' keys
            separator: Separator between prompts
            show_confirmation: Whether to show confirmation message

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not prompts:
                self.logger.warning("No prompts provided for copying")
                return False

            formatted_prompts = []
            for prompt in prompts:
                if isinstance(prompt, dict):
                    text = prompt.get('text', '')
                    name = prompt.get('name', '')
                    if name:
                        formatted_prompts.append(f"=== {name} ===\n\n{text}")
                    else:
                        formatted_prompts.append(text)
                elif isinstance(prompt, str):
                    formatted_prompts.append(prompt)

            combined_text = separator.join(formatted_prompts)
            confirmation_msg = f"Copied {len(prompts)} prompt(s) to clipboard."

            if show_confirmation:
                return self.copy_to_clipboard(combined_text, True)
            else:
                return self.copy_to_clipboard(combined_text, False)

        except Exception as e:
            self.logger.error(f"Error copying multiple prompts: {e}")
            return False

    def is_clipboard_available(self) -> bool:
        """
        Check if clipboard functionality is available

        Returns:
            bool: True if clipboard is available, False otherwise
        """
        return PYPERCLIP_AVAILABLE or self.root is not None

    def get_clipboard_methods(self) -> dict:
        """
        Get information about available clipboard methods

        Returns:
            dict: Information about available methods
        """
        return {
            'pyperclip_available': PYPERCLIP_AVAILABLE,
            'keyboard_available': KEYBOARD_AVAILABLE,
            'tkinter_available': self.root is not None or self._fallback_root is not None,
            'preferred_method': 'pyperclip' if PYPERCLIP_AVAILABLE else 'tkinter'
        }

    def __del__(self):
        """Cleanup when service is destroyed"""
        if self._fallback_root is not None:
            try:
                self._fallback_root.destroy()
            except:
                pass