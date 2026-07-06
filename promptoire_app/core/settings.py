"""User settings: load/save with sane defaults and forward-compatible merge."""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_META_PROMPT = (
    "You are a senior prompt engineer. Below is my entire prompt library as JSON.\n"
    "Improve EVERY prompt: make each clearer, more specific, and more effective for "
    "modern LLMs and image models, while preserving its original intent and my voice.\n\n"
    "Rules:\n"
    "- Return ONLY valid JSON in the EXACT same schema (same keys, same structure).\n"
    "- Keep each prompt's \"id\" UNCHANGED so I can merge your version back in.\n"
    "- You may refine \"title\", \"prompt\", \"tags\", \"note\", and image fields "
    "(negative, model, params, etc.). Do not invent new ids or delete prompts.\n"
    "- For image prompts (\"type\": \"image\"), tighten the prompt and negative, and keep "
    "parameters valid for the named model.\n"
    "- Add 2-4 useful tags per prompt where missing.\n"
    "- You may also ADD a few high-value new prompts in fitting categories (give those a "
    "new id starting with \"new_\").\n\n"
    "Here is the library:\n"
)

DEFAULT_OUTLINE_PROMPT = (
    "Improve this Promptoire outline. Keep existing section paths and prompt "
    "titles stable when updating existing prompts so Promptoire can merge by "
    "title. Add new prompts only where they fit.\n\n"
    "Rules:\n"
    "- Return only the outline, with no code fence or extra commentary.\n"
    "- Keep the section/subsection structure easy to scan.\n"
    "- Use prompt rows like: Title: Prompt body.\n"
    "- Use Path: Section > Subsection > Nested subsection when a prompt belongs deep in the library.\n"
    "- For image prompts, keep fields like Type, Negative prompt, Image model, Parameters, and CFG scale.\n"
)

DEFAULTS: dict[str, Any] = {
    "version": 2,
    "theme": "matrix",          # key into the web theme registry
    "accent": "",                # optional override hex; "" = theme default
    "hotkey": "ctrl+alt+space",  # global toggle for the launcher
    "behavior": {
        "copy_then_hide": True,   # spring-loaded: vanish after a copy
        "hide_on_blur": True,     # close when it loses focus
        "open_at_cursor": True,   # popup appears near the mouse
        "paste_after_copy": False,
        "launch_at_startup": False,
        "show_tray": True,
        "single_instance": True,
    },
    "window": {
        "width": 460,
        "height": 560,
        "opacity": 1.0,
        "remember_position": True,
        "x": None,
        "y": None,
    },
    "search": {
        "fuzzy": True,
    },
    "bulk_improve": {
        "outline_prompt": DEFAULT_OUTLINE_PROMPT,
        "meta_prompt": DEFAULT_META_PROMPT,
    },
    "ai": {
        # Optional: lets the "Improve with AI now" button call an API directly.
        # Empty api_key = the button points to Settings; manual copy/paste always works.
        "provider": "anthropic",          # "anthropic" | "openai"
        "api_key": "",
        "model": "",                       # blank = provider default
        "base_url": "",                    # OpenAI-compatible endpoints only
    },
    "links": {
        # Set this to your own Buy Me a Coffee / Ko-fi / GitHub Sponsors URL.
        "coffee": "",
        # Blank until the real public repository exists.
        "repo": "",
    },
    "onboarded": False,
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _generic_url(value: Any) -> str:
    return str(value or "").strip().rstrip("/").lower()


def _sanitize_links(data: dict) -> None:
    links = data.setdefault("links", {})
    if not isinstance(links, dict):
        data["links"] = copy.deepcopy(DEFAULTS["links"])
        return
    if _generic_url(links.get("coffee")) == "https://www.buymeacoffee.com":
        links["coffee"] = ""
    if _generic_url(links.get("repo")) == "https://github.com":
        links["repo"] = ""


class Settings:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: dict[str, Any] = copy.deepcopy(DEFAULTS)

    def load(self) -> "Settings":
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    self.data = _deep_merge(DEFAULTS, saved)
        except Exception:
            self.data = copy.deepcopy(DEFAULTS)
        _sanitize_links(self.data)
        return self

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    # convenience accessors -----------------------------------------------
    def get(self, *keys, default=None):
        node: Any = self.data
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def update(self, patch: dict) -> None:
        self.data = _deep_merge(self.data, patch or {})
