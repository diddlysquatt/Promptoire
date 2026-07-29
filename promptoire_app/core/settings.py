"""User settings: load/save with sane defaults and forward-compatible merge."""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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
    "Improve the Promptoire records below. Preserve every existing Path and "
    "Title exactly so updates merge safely. Add new prompts only when requested "
    "and place each one in a useful existing or clearly named new path.\n\n"
    "STRICT OUTPUT CONTRACT:\n"
    "- Return records only: no introduction, analysis, code fence, Rules section, or closing note.\n"
    "- The first nonblank line must be Path:. Repeat this exact block for every prompt:\n"
    "  Path: Category > Subcategory\n"
    "  Title: Short stable title\n"
    "  Type: text or image\n"
    "  Prompt: Complete prompt text\n"
    "  Tags: optional, comma-separated\n"
    "- Never turn headings, labels, bullets, or paragraphs inside Prompt text into categories.\n"
    "- For image prompts, put every copyable model flag or suffix directly at the very end of Prompt "
    "(for example: --ar 16:9 --stylize 1000). Do not create separate Negative prompt, Image model, "
    "Parameters, CFG, sampler, or seed fields unless I explicitly ask for them.\n"
)

DENSITY_OPTIONS = ("comfortable", "compact", "titles")
OPENAI_MODEL_OPTIONS = ("gpt-5.6", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")

DEFAULTS: dict[str, Any] = {
    "version": 2,
    "theme": "matrix",          # key into the web theme registry
    "accent": "",                # optional override hex; "" = theme default
    "density": "compact",        # "comfortable" | "compact" | "titles"
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
        # Optional: lets "Improve with AI now" call OpenAI directly. Manual
        # copy/paste always works without an account or key.
        "provider": "openai",
        "api_key": "",
        "model": "gpt-5.6",
        "base_url": "",
    },
    "links": {
        "coffee": "https://buymeacoffee.com/promptoire",
        "repo": "https://github.com/diddlysquatt/Promptoire",
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


def _normalize_optional_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if not parsed.scheme and not raw.startswith(("/", "#")):
        prefixed = "https://" + raw
        parsed_prefixed = urlparse(prefixed)
        if parsed_prefixed.netloc:
            return prefixed
    return raw


def _generic_coffee_url(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = (parsed.path or "").strip("/")
    return (
        parsed.scheme.lower() in ("http", "https")
        and host == "buymeacoffee.com"
        and not path
        and not parsed.query
        and not parsed.fragment
    )


def _sanitize_links(data: dict) -> None:
    links = data.setdefault("links", {})
    if not isinstance(links, dict):
        data["links"] = copy.deepcopy(DEFAULTS["links"])
        return
    links["coffee"] = _normalize_optional_url(links.get("coffee"))
    links["repo"] = _normalize_optional_url(links.get("repo"))
    if _generic_coffee_url(links.get("coffee")):
        links["coffee"] = ""
    if _generic_url(links.get("repo")) == "https://github.com":
        links["repo"] = ""


def _sanitize_density(data: dict) -> None:
    if data.get("density") not in DENSITY_OPTIONS:
        data["density"] = DEFAULTS["density"]


def _official_openai_source(ai: dict) -> bool:
    provider = str(ai.get("provider") or "").strip().lower()
    base_url = str(ai.get("base_url") or "").strip()
    if provider != "openai":
        return False
    if not base_url:
        return True
    try:
        parsed = urlparse(base_url if "://" in base_url else "https://" + base_url)
        return (parsed.hostname or "").lower() == "api.openai.com" and parsed.path.rstrip("/") in ("", "/v1")
    except Exception:
        return False


def _sanitize_ai(data: dict, source_ai: dict | None = None) -> None:
    ai = data.get("ai")
    if not isinstance(ai, dict):
        data["ai"] = copy.deepcopy(DEFAULTS["ai"])
        return
    source = source_ai if isinstance(source_ai, dict) else ai
    api_key = str(ai.get("api_key") or "").strip()
    # Never reinterpret an Anthropic, DeepSeek, OpenRouter, or local-server
    # credential as an OpenAI key during the one-provider migration.
    if api_key and not _official_openai_source(source):
        api_key = ""
    ai["provider"] = "openai"
    ai["base_url"] = ""
    ai["api_key"] = api_key
    model = str(ai.get("model") or "").strip()
    ai["model"] = model if model in OPENAI_MODEL_OPTIONS else DEFAULTS["ai"]["model"]


class Settings:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: dict[str, Any] = copy.deepcopy(DEFAULTS)

    def load(self) -> "Settings":
        source_ai = None
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    source_ai = saved.get("ai") if isinstance(saved.get("ai"), dict) else None
                    self.data = _deep_merge(DEFAULTS, saved)
        except Exception:
            self.data = copy.deepcopy(DEFAULTS)
        _sanitize_links(self.data)
        _sanitize_density(self.data)
        _sanitize_ai(self.data, source_ai)
        if (isinstance(source_ai, dict) and source_ai.get("api_key")
                and not _official_openai_source(source_ai)):
            try:
                self.save()
            except Exception:
                pass
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
        _sanitize_links(self.data)
        _sanitize_density(self.data)
        _sanitize_ai(self.data)
