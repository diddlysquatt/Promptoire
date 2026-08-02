"""The bridge exposed to the web UI as `window.pywebview.api.*`.

Every method returns plain JSON-able data and never raises across the bridge —
the UI gets {ok: bool, ...} envelopes so it can show friendly errors.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import sys
import threading
import traceback
import webbrowser
from typing import Any
from urllib.parse import urlparse

from .core import paths, schema
from .core.settings import DEFAULT_META_PROMPT, DEFAULT_OUTLINE_PROMPT
from .platform import clipboard, window_fx


def ok(**kw) -> dict:
    return {"ok": True, **kw}


def err(message: str, **kw) -> dict:
    return {"ok": False, "error": message, **kw}


class Api:
    def __init__(self, app):
        self._app = app  # the App controller (window, tray, hotkey, lib, settings)
        self._mutation_lock = threading.RLock()

    # ---- bootstrap ----------------------------------------------------------

    def get_state(self) -> dict:
        try:
            lib = self._app.library
            return ok(
                categories=lib.categories(),
                settings=self._app.settings.data,
                stats=lib.stats(),
                hotkey_available=self._app.hotkey.available,
                platform=self._app.platform_name(),
                version=self._app.version,
            )
        except Exception as e:
            return err(str(e), trace=traceback.format_exc())

    def search(self, query: str = "", type_filter: str = "all",
               favorites_only: bool = False, tag: str = "") -> dict:
        try:
            hits = self._app.library.search(
                query, type_filter=type_filter, favorites_only=favorites_only, tag=tag
            )
            return ok(results=hits, count=len(hits))
        except Exception as e:
            return err(str(e))

    # ---- the copy action (the whole point) ----------------------------------

    def copy_prompt(
        self,
        prompt_id: str,
        resolved_text: str | None = None,
        keep_open: bool = False,
    ) -> dict:
        """Copy a prompt, optionally bypassing spring-loaded auto-hide.

        `resolved_text` lets the UI pass placeholder-filled text. `keep_open`
        is the launcher's pin override, so one visible control governs both
        blur hiding and the native copy path.
        """
        try:
            p, _, _ = self._app.library.find_prompt(prompt_id)
            if p is None and resolved_text is None:
                return err("Prompt not found")
            text = resolved_text if resolved_text is not None else p.get("prompt", "")
            if not clipboard.copy(text):
                return err("Clipboard unavailable")
            last_used = None
            if p is not None:
                last_used = self._app.library.record_use(prompt_id)
                self._app.save_library_soon()
            behavior = self._app.settings.get("behavior", default={})
            if behavior.get("paste_after_copy"):
                self._app.after_copy_paste()
            spring = bool(behavior.get("copy_then_hide", True)) and not bool(keep_open)
            if spring:
                self._app.hide_window()
            return ok(
                spring=spring,
                title=(p or {}).get("title", "Prompt"),
                last_used=last_used,
            )
        except Exception as e:
            return err(str(e))

    def copy_text(self, text: str) -> dict:
        return ok() if clipboard.copy(text or "") else err("Clipboard unavailable")

    def get_clipboard_text(self) -> dict:
        try:
            text = clipboard.paste()
            if text is None:
                return err("Clipboard unavailable")
            return ok(text=text)
        except Exception as e:
            return err(str(e))

    # ---- prompt CRUD --------------------------------------------------------

    def add_prompt(self, category_id: str | None, fields: dict) -> dict:
        try:
            p = self._app.library.add_prompt(category_id, fields or {})
            self._app.save_library()
            return ok(prompt=p)
        except Exception as e:
            return err(str(e))

    def update_prompt(self, prompt_id: str, fields: dict) -> dict:
        try:
            p = self._app.library.update_prompt(prompt_id, fields or {})
            if p is None:
                return err("Prompt not found")
            self._app.save_library()
            return ok(prompt=p)
        except Exception as e:
            return err(str(e))

    def delete_prompt(self, prompt_id: str) -> dict:
        try:
            removed = self._app.library.delete_prompt(prompt_id)
            if removed is None:
                return err("Prompt not found")
            self._app.save_library()
            return ok(removed=removed)
        except Exception as e:
            return err(str(e))

    def restore_prompt(self, category_id: str, prompt: dict, index: int = -1) -> dict:
        """Undo a delete by re-inserting the exact prompt dict."""
        try:
            cat, _, _ = self._app.library.find_category(category_id)
            if cat is None:
                self._app.library.add_prompt(None, prompt)
            else:
                prompts = cat.setdefault("prompts", [])
                if 0 <= index <= len(prompts):
                    prompts.insert(index, prompt)
                else:
                    prompts.append(prompt)
            self._app.save_library()
            return ok()
        except Exception as e:
            return err(str(e))

    def toggle_favorite(self, prompt_id: str) -> dict:
        try:
            fav = self._app.library.toggle_favorite(prompt_id)
            if fav is None:
                return err("Prompt not found")
            self._app.save_library_soon()
            return ok(favorite=fav)
        except Exception as e:
            return err(str(e))

    def move_prompt(self, prompt_id: str, target_category_id: str, index: int | None = None) -> dict:
        try:
            okk = self._app.library.move_prompt(prompt_id, target_category_id, index)
            if not okk:
                return err("Move failed")
            self._app.save_library()
            return ok()
        except Exception as e:
            return err(str(e))

    def reorder_prompt(self, category_id: str, from_index: int, to_index: int) -> dict:
        try:
            okk = self._app.library.reorder_prompt(category_id, from_index, to_index)
            if not okk:
                return err("Reorder failed")
            self._app.save_library()
            return ok()
        except Exception as e:
            return err(str(e))

    # ---- category CRUD ------------------------------------------------------

    def add_category(self, name: str = "New Category", parent_id: str | None = None) -> dict:
        try:
            cat = self._app.library.add_category(name, parent_id)
            self._app.save_library()
            return ok(category=cat)
        except Exception as e:
            return err(str(e))

    def update_category(self, category_id: str, fields: dict) -> dict:
        try:
            cat = self._app.library.update_category(category_id, fields or {})
            if cat is None:
                return err("Category not found")
            self._app.save_library()
            return ok(category=cat)
        except Exception as e:
            return err(str(e))

    def delete_category(self, category_id: str) -> dict:
        try:
            okk = self._app.library.delete_category(category_id)
            self._app.save_library()
            return ok() if okk else err("Category not found")
        except Exception as e:
            return err(str(e))

    def reorder_category(self, category_id: str, to_index: int) -> dict:
        try:
            okk = self._app.library.reorder_category(category_id, to_index)
            if not okk:
                return err("Reorder failed")
            self._app.save_library()
            return ok()
        except Exception as e:
            return err(str(e))

    # ---- the bulk-improve loop ---------------------------------------------

    def _outline_prompt(self) -> str:
        prompt = self._app.settings.get("bulk_improve", "outline_prompt", default="")
        return str(prompt or DEFAULT_OUTLINE_PROMPT).strip()

    def bulk_prompt_defaults(self) -> dict:
        return ok(outline_prompt=DEFAULT_OUTLINE_PROMPT, meta_prompt=DEFAULT_META_PROMPT)

    def get_export(self, full: bool = False) -> dict:
        try:
            return ok(json=self._app.library.export_json(full=full))
        except Exception as e:
            return err(str(e))

    def copy_export(self, include_meta: bool = True, full: bool = False) -> dict:
        """Copy the whole library JSON (optionally prefixed by the meta-prompt)
        to the clipboard, ready to paste into any LLM."""
        try:
            body = self._app.library.export_json(full=full)
            if include_meta:
                meta = self._app.settings.get("bulk_improve", "meta_prompt", default="")
                payload = f"{meta}\n\n```json\n{body}\n```"
            else:
                payload = body
            if not clipboard.copy(payload):
                return err("Clipboard unavailable")
            return ok(chars=len(payload))
        except Exception as e:
            return err(str(e))

    def copy_outline_export(self, include_request: bool = True) -> dict:
        """Copy the current library in the simple outline format."""
        try:
            body = self._app.library.export_outline()
            payload = f"{self._outline_prompt()}\n\n{body}" if include_request else body
            if not clipboard.copy(payload):
                return err("Clipboard unavailable")
            return ok(chars=len(payload))
        except Exception as e:
            return err(str(e))

    def save_export_file(self, full: bool = False) -> dict:
        try:
            path = self._app.save_file_dialog(
                "prompts-export.json",
                ("JSON Files (*.json)", "All files (*.*)"),
            )
            if not path:
                return ok(cancelled=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._app.library.export_json(full=full))
            return ok(path=str(path))
        except Exception as e:
            return err(str(e))

    def save_outline_file(self) -> dict:
        try:
            path = self._app.save_file_dialog(
                "prompts-outline.txt",
                ("Outline/Text Files (*.txt;*.md)", "All files (*.*)"),
            )
            if not path:
                return ok(cancelled=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._app.library.export_outline())
            return ok(path=str(path))
        except Exception as e:
            return err(str(e))

    def load_import_file(self) -> dict:
        try:
            path = self._app.open_file_dialog((
                "Promptoire Imports (*.json;*.txt;*.md;*.csv)",
                "JSON Files (*.json)",
                "Text/Markdown/CSV Files (*.txt;*.md;*.csv)",
                "All files (*.*)",
            ))
            if not path:
                return ok(cancelled=True)
            with open(path, "r", encoding="utf-8") as f:
                return ok(text=f.read(), path=str(path))
        except Exception as e:
            return err(str(e))

    def ai_improve(self, full: bool = False) -> dict:
        """One-click: send the outline library to the configured LLM API
        and return its reply for previewing/merging."""
        try:
            from .core import ai_improve as _ai
            payload = f"{self._outline_prompt()}\n\n{self._app.library.export_outline()}"
            res = _ai.improve(self._app.settings.get("ai", default={}), payload)
            if res.get("ok"):
                return ok(text=res["text"], model=res.get("model", ""))
            return err(res.get("error", "AI request failed"))
        except Exception as e:
            return err(str(e))

    def merge_preview(self, text: str) -> dict:
        try:
            data = _parse_import_text(text)
            if data is None:
                return err("Could not read that import. Paste a simple outline or JSON.")
            preview = self._app.library.merge_preview(data)
            return ok(preview=preview)
        except Exception as e:
            return err(str(e))

    def apply_merge(self, text: str, update_existing: bool = True, add_new: bool = True) -> dict:
        try:
            with self._mutation_lock:
                data = _parse_import_text(text)
                if data is None:
                    return err("Could not read that import.")
                result = self._app.library.apply_merge(
                    data, update_existing=update_existing, add_new=add_new
                )
                self._app.save_library()
                return ok(result=result, stats=self._app.library.stats(),
                          categories=self._app.library.categories())
        except Exception as e:
            return err(str(e))

    def replace_all(self, text: str) -> dict:
        try:
            with self._mutation_lock:
                data = _parse_import_text(text)
                if data is None:
                    return err("Could not read that import.")
                self._app.library.replace_all(data)
                self._app.save_library()
                return ok(stats=self._app.library.stats(),
                          categories=self._app.library.categories())
        except Exception as e:
            return err(str(e))

    def backup_now(self) -> dict:
        try:
            self._app.library.save(backup=True)
            return ok()
        except Exception as e:
            return err(str(e))

    def open_data_folder(self) -> dict:
        try:
            folder = paths.data_dir()
            if hasattr(os, "startfile"):
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            return ok(path=str(folder))
        except Exception as e:
            return err(str(e))

    # ---- settings -----------------------------------------------------------

    def get_settings(self) -> dict:
        return ok(settings=self._app.settings.data)

    def update_settings(self, patch: dict) -> dict:
        try:
            effects = self._app.apply_settings(patch or {})
            return ok(settings=self._app.settings.data, effects=effects)
        except Exception as e:
            return err(str(e))

    def set_hotkey(self, combo: str) -> dict:
        try:
            applied = self._app.set_hotkey(combo)
            return ok(applied=applied, available=self._app.hotkey.available)
        except Exception as e:
            return err(str(e))

    # ---- window / app -------------------------------------------------------

    def hide_window(self) -> dict:
        self._app.hide_window()
        return ok()

    def show_window(self) -> dict:
        self._app.show_window()
        return ok()

    def quit_app(self) -> dict:
        self._app.quit()
        return ok()

    def set_window_size(self, width: int, height: int) -> dict:
        try:
            self._app.resize(int(width), int(height))
            return ok()
        except Exception as e:
            return err(str(e))

    def begin_window_resize(self, direction: str) -> dict:
        try:
            return ok(started=self._app.begin_window_resize(direction))
        except Exception as e:
            return err(str(e))

    def open_external(self, url: str) -> dict:
        try:
            target = (url or "").strip()
            parsed = urlparse(target)
            if parsed.scheme.lower() != "https" or not parsed.hostname:
                return err("Only secure web links can be opened.")
            webbrowser.open(target)
            return ok()
        except Exception as e:
            return err(str(e))

    def notify_blur(self) -> dict:
        """Called by JS when the window loses focus; honor hide-on-blur."""
        self._app.on_window_blur()
        return ok()

    def selftest_report(self, data: dict) -> dict:
        """No-op unless Python was started with --selftest. Then it records what
        the real WebView bridge observed and quits — proving the JS->Python
        round trip end-to-end with real data."""
        if not getattr(self._app, "selftest", False):
            return ok()
        import sys as _sys
        report = dict(data or {})
        try:
            hwnd = self._app._resolve_hwnd()
            report["native_hwnd"] = bool(hwnd)
            report["window_icon"] = window_fx.has_window_icon(hwnd)
            report["window_icon_applied"] = bool(self._app._window_icon_applied)
            report["minimum_window"] = [360, 420]
        except Exception:
            report["native_hwnd"] = False
            report["window_icon"] = False
            report["window_icon_applied"] = False
        print(f"[selftest] report via bridge: {report}", file=_sys.stderr, flush=True)
        try:
            from .core import paths
            with open(paths.data_dir() / "_selftest.json", "w", encoding="utf-8") as f:
                json.dump(report, f)
        except Exception as e:
            print(f"[selftest] write failed: {e!r}", file=_sys.stderr, flush=True)
        try:
            import threading
            threading.Timer(0.6, self._app.quit).start()
        except Exception:
            pass
        return ok()


def _parse_import_text(text: str) -> Any:
    data = _parse_loose_json(text)
    if data is not None:
        return data
    for candidate in _outline_candidates(text):
        data = _parse_csv_table(candidate)
        if data is not None:
            return data
    for candidate in _outline_candidates(text):
        data = _parse_outline(candidate)
        if data is not None:
            return data
    return None


def _parse_loose_json(text: str) -> Any:
    """Parse JSON that may be wrapped in markdown code fences or have prose
    around it (LLMs love to add ```json fences and commentary)."""
    if text is None:
        return None
    s = text.strip()
    if not s:
        return None
    # Strip the first fenced block before trying JSON; outline parsing reuses it too.
    fenced = _first_code_fence(s)
    if fenced is not None:
        s = fenced.strip()
    try:
        return json.loads(s)
    except Exception:
        # Last resort: grab the first outer object or array block.
        candidates = []
        for opener, closer in (("{", "}"), ("[", "]")):
            start = s.find(opener)
            end = s.rfind(closer)
            if start != -1 and end != -1 and end > start:
                candidates.append((start, end + 1))
        for start, end in sorted(candidates):
            try:
                return json.loads(s[start:end])
            except Exception:
                pass
    return None


_CODE_FENCE_RE = re.compile(r"```[A-Za-z0-9_-]*\s*(.*?)```", re.DOTALL)


def _first_code_fence(text: str | None) -> str | None:
    if not text or "```" not in text:
        return None
    m = _CODE_FENCE_RE.search(text.strip())
    return m.group(1).strip() if m else None


def _outline_candidates(text: str | None) -> list[str]:
    if text is None:
        return []
    candidates: list[str] = []
    fenced = _first_code_fence(text)
    for candidate in (fenced, text):
        if not candidate:
            continue
        structured = _structured_outline_tail(candidate)
        if structured and structured.strip() != candidate.strip():
            candidates.append(structured)
        candidates.append(candidate)
    return candidates


_EXPLICIT_OUTLINE_START_RE = re.compile(
    r"^\s*(?:path|section|category|folder|group|folder[\s_-]+path|category[\s_-]+path)\s*:\s*\S+",
    re.IGNORECASE,
)
_OUTLINE_PREAMBLE_MARKERS = (
    "improve this promptoire outline",
    "create a batch of prompts for my promptoire",
    "return only the outline",
    "pasted text(",
    "worked for ",
    "every prompt ends with",
    "here is the improved library",
    "here's the improved library",
)


def _structured_outline_tail(text: str) -> str | None:
    """Trim copied chat/request prose before a canonical outline.

    People often select an entire LLM conversation instead of only its answer.
    Only trim when the prefix clearly looks like Promptoire/LLM scaffolding;
    otherwise a relaxed outline that legitimately mixes plain headings with a
    later ``Section:`` block must remain intact.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for idx, raw in enumerate(lines):
        if not _EXPLICIT_OUTLINE_START_RE.match(raw):
            continue
        prefix = "\n".join(lines[:idx]).strip().lower()
        if prefix and any(marker in prefix for marker in _OUTLINE_PREAMBLE_MARKERS):
            return "\n".join(lines[idx:]).strip()
        break
    return None


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])\s+(.+?)\s*$")
_PROMPT_MARKER_RE = re.compile(
    r"^\s*(?:prompt|item|entry)\s*#?\s*"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*:\s*(.*?)\s*$",
    re.IGNORECASE,
)
_PATH_FIELD_RE = re.compile(
    r"^\s*("
    r"section|category|folder|group|path|folder[\s_-]+path|"
    r"category[\s_-]+path|subcategory|sub-category|subsection|sub-section|"
    r"sub[\s_-]*sub(?:category|section)|nested[\s_-]+sub(?:category|section)|"
    r"child[\s_-]+(?:category|section)"
    r")\s*:\s*(.*?)\s*$",
    re.IGNORECASE,
)
_FIELD_RE = re.compile(
    r"^\s*("
    r"title|prompt|body|text|tags|type|note|"
    r"negative(?:[\s_-]+prompt)?|image[\s_-]+model|model|"
    r"params?|parameters?|settings?|seed|sampler|"
    r"cfg(?:[\s_-]+scale)?|guidance(?:[\s_-]+scale)?"
    r")\s*:\s*(.*?)\s*$",
    re.IGNORECASE,
)
_SPLIT_RE = re.compile(r"\s+(?:[-–—]|::)\s+|:\s+")
_SEPARATOR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_CONTAINER_LABEL_RE = re.compile(r"^\s*(?:prompts?|items?|entries)\s*:\s*$", re.IGNORECASE)


def _parse_outline(text: str) -> dict | None:
    """Convert a plain Markdown-ish outline into a v3 library.

    Supported shape:
      # Section
      ## Subsection
      - Prompt title: prompt body

    Headings become nested categories. Deeper Markdown headings followed by
    plain body text can also become prompt titles. Bullets, numbered items,
    `Prompt 1:` markers, `Title:` / `Prompt:` fields, and separated paragraphs
    become prompts. This is meant to make LLM-authored imports easy without
    forcing users to hand-edit JSON.
    """
    if text is None:
        return None
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    if not any(ln.strip() for ln in lines):
        return None

    table = _parse_markdown_table(lines)
    if table is not None:
        return table

    library = {"version": schema.SCHEMA_VERSION, "categories": []}
    stack: list[tuple[int, dict]] = []
    current: dict | None = None
    current_cat: dict | None = None
    saw_structure = False
    previous_blank = False

    def active_category() -> dict:
        nonlocal saw_structure
        if stack:
            return stack[-1][1]
        saw_structure = True
        if not library["categories"]:
            library["categories"].append(schema.new_category("Imported"))
        return library["categories"][0]

    def find_child(cats: list[dict], name: str) -> dict | None:
        key = name.strip().lower()
        return next((c for c in cats if c.get("name", "").strip().lower() == key), None)

    def add_heading(level: int, raw_name: str) -> None:
        nonlocal current, current_cat, saw_structure
        finish_prompt()
        parts = [_clean_heading_name(p) for p in re.split(r"\s*>\s*", raw_name) if _clean_heading_name(p)]
        if not parts:
            return
        while stack and stack[-1][0] >= level:
            stack.pop()
        cats = stack[-1][1].setdefault("subcategories", []) if stack else library["categories"]
        parent_level = level - 1
        for offset, name in enumerate(parts):
            cat = find_child(cats, name)
            if cat is None:
                cat = schema.new_category(name)
                cats.append(cat)
            stack.append((parent_level + 1 + offset, cat))
            cats = cat.setdefault("subcategories", [])
        saw_structure = True
        current = None
        current_cat = None

    def add_path_field(raw_key: str, value: str, raw_for_level: str) -> bool:
        value = value.strip()
        if not value:
            return False
        key = _normalize_path_key(raw_key)
        if key in ("section", "category", "folder", "group", "path", "folderpath", "categorypath"):
            level = 1
        elif key in ("subsubcategory", "subsubsection"):
            level = max(3, _indent_heading_level(raw_for_level))
        elif key in ("nestedsubcategory", "nestedsubsection", "childcategory", "childsection"):
            level = max((stack[-1][0] + 1) if stack else 2, _indent_heading_level(raw_for_level))
        else:
            level = max(2, _indent_heading_level(raw_for_level))
        add_heading(level, value)
        return True

    def new_block(cat: dict) -> dict:
        return {
            "title": "",
            "prompt_lines": [],
            "tags": [],
            "type": "",
            "note": "",
            "image": {},
            "started": False,
            "explicit_prompt": False,
            "sealed": False,
            "cat": cat,
        }

    def ensure_block() -> dict:
        nonlocal current, current_cat, saw_structure
        if current is None:
            current_cat = active_category()
            current = new_block(current_cat)
        saw_structure = True
        return current

    def append_prompt_line(value: str) -> None:
        block = ensure_block()
        block["prompt_lines"].append(value)
        block["started"] = True

    def apply_field(raw_key: str, value: str, was_previous_blank: bool, *, force_new: bool = False) -> None:
        key = _normalize_outline_field(raw_key)
        value = value.strip()
        block = ensure_block()
        if key == "title":
            if (force_new or was_previous_blank) and block["started"]:
                finish_prompt()
                block = ensure_block()
            block["title"] = value
        elif key in ("prompt", "body", "text"):
            if was_previous_blank and block["started"] and not block["explicit_prompt"]:
                finish_prompt()
                block = ensure_block()
            block["prompt_lines"].append(value)
            block["explicit_prompt"] = True
            block["sealed"] = False
            block["started"] = True
        elif key == "tags":
            block["tags"] = _split_tags(value)
            block["sealed"] = block["explicit_prompt"]
        elif key == "type":
            block["type"] = value.lower()
            block["sealed"] = block["explicit_prompt"]
        elif key == "note":
            block["note"] = value
            block["sealed"] = block["explicit_prompt"]
        else:
            block["image"][key] = value
            block["sealed"] = block["explicit_prompt"]

    def finish_prompt() -> None:
        nonlocal current, current_cat
        if current is None or current_cat is None:
            current = None
            current_cat = None
            return
        prompt = _outline_block_to_prompt(current)
        if prompt is not None:
            current_cat.setdefault("prompts", []).append(prompt)
        current = None
        current_cat = None

    last_was_heading = False

    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            if current is not None and current.get("explicit_prompt"):
                # Prompt bodies may contain paragraphs, headings, lists,
                # rubrics, and legal/coding labels. Keep those inside Prompt.
                current["prompt_lines"].append("")
            previous_blank = True
            continue

        if (previous_blank and current is not None and current.get("started")
                and not current.get("explicit_prompt") and not raw.startswith((" ", "\t"))):
            finish_prompt()

        # After an explicit Prompt: field, ordinary text stays inside that
        # prompt even when it resembles a heading. Only reserved outline fields
        # can end or enrich the record.
        if current is not None and current.get("explicit_prompt"):
            if previous_blank and current.get("sealed") and _HEADING_RE.match(line):
                finish_prompt()
            else:
                path_field = _PATH_FIELD_RE.match(line)
                if path_field:
                    if add_path_field(path_field.group(1), path_field.group(2), raw):
                        last_was_heading = True
                    previous_blank = False
                    continue
                field = _FIELD_RE.match(line)
                if field:
                    key = _normalize_outline_field(field.group(1))
                    apply_field(
                        field.group(1), field.group(2), previous_blank,
                        force_new=key == "title",
                    )
                    previous_blank = False
                    last_was_heading = False
                    continue
                bullet = _BULLET_RE.match(raw)
                if bullet:
                    bullet_value = bullet.group(1).strip()
                    bullet_path = _PATH_FIELD_RE.match(bullet_value)
                    if bullet_path:
                        if add_path_field(bullet_path.group(1), bullet_path.group(2), raw):
                            last_was_heading = True
                        previous_blank = False
                        continue
                    bullet_field = _FIELD_RE.match(bullet_value)
                    if bullet_field:
                        key = _normalize_outline_field(bullet_field.group(1))
                        apply_field(
                            bullet_field.group(1), bullet_field.group(2), previous_blank,
                            force_new=key == "title",
                        )
                        previous_blank = False
                        last_was_heading = False
                        continue
                if bullet and current.get("sealed"):
                    # A new unlabeled bullet after record metadata starts the
                    # next prompt in relaxed/YAML-ish outlines.
                    finish_prompt()
                else:
                    current["prompt_lines"].append(raw.rstrip())
                    current["started"] = True
                    previous_blank = False
                    last_was_heading = False
                    continue

        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if _looks_like_prompt_heading(level, title, lines, idx):
                finish_prompt()
                block = ensure_block()
                block["title"] = _clean_heading_name(title)
                block["started"] = True
                previous_blank = False
                last_was_heading = False
            else:
                add_heading(level, title)
                previous_blank = False
                last_was_heading = True
            continue

        if _SEPARATOR_RE.match(line):
            finish_prompt()
            previous_blank = False
            last_was_heading = False
            continue

        if _CONTAINER_LABEL_RE.match(line):
            finish_prompt()
            previous_blank = False
            last_was_heading = False
            continue

        path_field = _PATH_FIELD_RE.match(line)
        if path_field:
            if add_path_field(path_field.group(1), path_field.group(2), raw):
                last_was_heading = True
            previous_blank = False
            continue

        marker = _PROMPT_MARKER_RE.match(line)
        if marker:
            finish_prompt()
            block = ensure_block()
            value = marker.group(1).strip()
            if value:
                _seed_outline_block(block, value, title_only=True)
            previous_blank = False
            last_was_heading = False
            continue

        if _looks_like_plain_heading(raw, lines, idx, current, previous_blank):
            level = _plain_heading_level(raw, stack, last_was_heading)
            add_heading(level, _clean_heading_name(line))
            previous_blank = False
            last_was_heading = True
            continue

        bullet = _BULLET_RE.match(raw)
        if bullet:
            value = bullet.group(1).strip()
            path_field = _PATH_FIELD_RE.match(value)
            if path_field:
                if add_path_field(path_field.group(1), path_field.group(2), raw):
                    last_was_heading = True
                previous_blank = False
                continue

            marker = _PROMPT_MARKER_RE.match(value)
            if marker:
                finish_prompt()
                block = ensure_block()
                marker_value = marker.group(1).strip()
                if marker_value:
                    _seed_outline_block(block, marker_value, title_only=True)
                previous_blank = False
                last_was_heading = False
                continue

            field = _FIELD_RE.match(value)
            if field:
                force_new = _normalize_outline_field(field.group(1)) == "title"
                apply_field(field.group(1), field.group(2), previous_blank, force_new=force_new)
                previous_blank = False
                last_was_heading = False
                continue

            if _looks_like_bullet_heading(raw, value, lines, idx):
                add_heading(_indent_heading_level(raw), _clean_heading_name(value))
                previous_blank = False
                last_was_heading = True
                continue

            finish_prompt()
            block = ensure_block()
            _seed_outline_block(block, value, title_only=True)
            previous_blank = False
            last_was_heading = False
            continue

        field = _FIELD_RE.match(line)
        if field:
            apply_field(field.group(1), field.group(2), previous_blank)
            previous_blank = False
            last_was_heading = False
            continue

        if (previous_blank and current is not None and current.get("started")
                and not current.get("explicit_prompt") and not raw.startswith((" ", "\t"))):
            finish_prompt()

        block = ensure_block()
        if not block["title"] and not block["prompt_lines"]:
            _seed_outline_block(block, line)
        else:
            append_prompt_line(line)
        previous_blank = False
        last_was_heading = False

    finish_prompt()

    if not saw_structure:
        return None
    if not any(True for _ in schema.iter_prompts(library)):
        return None
    return library


def _seed_outline_block(block: dict, text: str, *, title_only: bool = False) -> None:
    left, right = _split_title_body(text)
    if right:
        block["title"] = left
        block["prompt_lines"].append(right)
    else:
        block["title"] = _derive_title(text)
        if not title_only:
            block["prompt_lines"].append(text)
    block["started"] = True


def _clean_heading_name(text: str) -> str:
    return text.strip().rstrip(":").strip()


def _indent_width(raw: str) -> int:
    expanded = raw.replace("\t", "    ")
    return len(expanded) - len(expanded.lstrip(" "))


def _indent_heading_level(raw: str) -> int:
    return min((_indent_width(raw) // 2) + 1, 6)


def _plain_heading_level(raw: str, stack: list[tuple[int, dict]], last_was_heading: bool) -> int:
    if _indent_width(raw) == 0 and stack and last_was_heading:
        return min(stack[-1][0] + 1, 6)
    return _indent_heading_level(raw)


def _next_content_line(lines: list[str], idx: int) -> tuple[str, str] | None:
    for raw in lines[idx + 1:]:
        stripped = raw.strip()
        if stripped and not _SEPARATOR_RE.match(stripped):
            return raw, stripped
    return None


def _looks_like_plain_heading(
    raw: str,
    lines: list[str],
    idx: int,
    current: dict | None,
    previous_blank: bool,
) -> bool:
    line = _clean_heading_name(raw.strip())
    if not line or (current is not None and not previous_blank):
        return False
    if len(line) > 90:
        return False
    if _HEADING_RE.match(line) or _BULLET_RE.match(raw):
        return False
    if _FIELD_RE.match(raw.strip()) or _PATH_FIELD_RE.match(raw.strip()):
        return False
    if _CONTAINER_LABEL_RE.match(raw.strip()):
        return False
    if _split_title_body(line)[1]:
        return False

    nxt = _next_content_line(lines, idx)
    if nxt is None:
        return False

    next_raw, next_line = nxt
    if _indent_width(next_raw) > _indent_width(raw):
        return True
    if ">" in line and (_BULLET_RE.match(next_raw) or _FIELD_RE.match(next_line)):
        return True
    if current is None and (_BULLET_RE.match(next_raw) or _FIELD_RE.match(next_line)):
        return True
    return False


def _looks_like_prompt_heading(level: int, raw_title: str, lines: list[str], idx: int) -> bool:
    title = _clean_heading_name(raw_title)
    if level < 3 or not title or len(title) > 90:
        return False
    nxt = _next_content_line(lines, idx)
    if nxt is None:
        return False
    next_raw, next_line = nxt
    if _HEADING_RE.match(next_line) or _BULLET_RE.match(next_raw):
        return False
    if _PATH_FIELD_RE.match(next_line) or _PROMPT_MARKER_RE.match(next_line):
        return False
    field = _FIELD_RE.match(next_line)
    if field:
        return _normalize_outline_field(field.group(1)) != "title"
    return not bool(_split_title_body(next_line)[1])


def _looks_like_bullet_heading(raw: str, text: str, lines: list[str], idx: int) -> bool:
    line = _clean_heading_name(text)
    if not line or len(line) > 90:
        return False
    if _FIELD_RE.match(line) or _PATH_FIELD_RE.match(line) or _PROMPT_MARKER_RE.match(line):
        return False
    if _split_title_body(line)[1]:
        return False
    nxt = _next_content_line(lines, idx)
    if nxt is None:
        return False
    next_raw, _ = nxt
    return _indent_width(next_raw) > _indent_width(raw)


def _split_title_body(text: str) -> tuple[str, str]:
    m = _SPLIT_RE.search(text)
    if not m:
        return "", ""
    left = text[:m.start()].strip()
    right = text[m.end():].strip()
    if not left or not right:
        return "", ""
    if len(left) > 90:
        return "", ""
    return left, right


def _parse_markdown_table(lines: list[str]) -> dict | None:
    """Parse common LLM Markdown tables into a library.

    Expected minimum columns are `Title` and `Prompt`/`Body`/`Text`. Optional
    path columns such as `Section`, `Subsection`, or `Path` place prompts into
    nested categories; image and metadata columns map to normal prompt fields.
    """
    library = {"version": schema.SCHEMA_VERSION, "categories": []}

    for idx in range(len(lines) - 1):
        header_line = lines[idx].strip()
        separator_line = lines[idx + 1].strip()
        if not _looks_like_table_row(header_line) or not _looks_like_table_separator(separator_line):
            continue

        headers = [_normalize_table_header(c) for c in _split_markdown_table_row(header_line)]
        if not headers:
            continue
        title_idx = _first_header_index(headers, ("title", "name", "prompttitle"))
        prompt_idx = _first_header_index(headers, ("prompt", "body", "text", "content"))
        if title_idx is None or prompt_idx is None:
            continue

        for row_line in lines[idx + 2:]:
            if not row_line.strip():
                break
            if not _looks_like_table_row(row_line):
                break
            cells = _split_markdown_table_row(row_line)
            if not any(c.strip() for c in cells):
                continue
            row = {headers[i]: cells[i].strip() for i in range(min(len(headers), len(cells))) if headers[i]}
            _append_table_prompt(library, row)

    if any(True for _ in schema.iter_prompts(library)):
        return library
    return None


def _parse_csv_table(text: str | None) -> dict | None:
    """Parse pasted CSV/TSV tables with Title and Prompt columns."""
    if text is None:
        return None
    s = text.strip()
    if not s:
        return None
    lines = [ln for ln in s.replace("\r\n", "\n").replace("\r", "\n").split("\n") if ln.strip()]
    if len(lines) < 2 or ("," not in lines[0] and "\t" not in lines[0]):
        return None

    sample = "\n".join(lines[:8])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        dialect = csv.excel_tab if "\t" in lines[0] else csv.excel

    try:
        reader = csv.DictReader(io.StringIO("\n".join(lines)), dialect=dialect)
        raw_headers = reader.fieldnames or []
    except csv.Error:
        return None

    headers = [_normalize_table_header(h or "") for h in raw_headers]
    if _first_header_index(headers, ("title", "name", "prompttitle")) is None:
        return None
    if _first_header_index(headers, ("prompt", "body", "text", "content")) is None:
        return None

    library = {"version": schema.SCHEMA_VERSION, "categories": []}
    for raw_row in reader:
        row = {}
        for raw_key, value in raw_row.items():
            if raw_key is None:
                continue
            key = _normalize_table_header(raw_key)
            if key:
                row[key] = (value or "").strip()
        _append_table_prompt(library, row)

    if any(True for _ in schema.iter_prompts(library)):
        return library
    return None


def _append_table_prompt(library: dict, row: dict) -> bool:
    title = row.get("title") or row.get("name") or row.get("prompttitle") or ""
    prompt = row.get("prompt") or row.get("body") or row.get("text") or row.get("content") or ""
    if not title and not prompt:
        return False
    raw = {
        "title": title or _derive_title(prompt),
        "prompt": prompt or title,
        "tags": _split_tags(row.get("tags", "")),
        "note": row.get("note", ""),
    }
    ptype = (row.get("type") or "").strip().lower()
    if ptype:
        raw["type"] = ptype
    for key in schema.IMAGE_FIELDS:
        if row.get(key):
            raw[key] = row[key]
    _category_for_table_row(library, row).setdefault("prompts", []).append(
        schema.normalize_prompt(raw)
    )
    return True


def _looks_like_table_row(line: str) -> bool:
    return "|" in line and len(_split_markdown_table_row(line)) >= 2


def _looks_like_table_separator(line: str) -> bool:
    if not _looks_like_table_row(line):
        return False
    cells = _split_markdown_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _split_markdown_table_row(line: str) -> list[str]:
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        raw = raw[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for ch in raw:
        if escaped:
            current.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "|":
            cells.append(_clean_table_cell("".join(current)))
            current = []
        else:
            current.append(ch)
    if escaped:
        current.append("\\")
    cells.append(_clean_table_cell("".join(current)))
    return cells


def _clean_table_cell(value: str) -> str:
    text = value.strip()
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = text.replace("&vert;", "|").replace("&#124;", "|")
    return text.strip()


def _normalize_table_header(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "", value.strip().lower())
    aliases = {
        "category": "section",
        "folder": "section",
        "group": "section",
        "categorypath": "path",
        "sectionpath": "path",
        "folderpath": "path",
        "subsection": "subsection",
        "subcategory": "subsection",
        "subsubsection": "subsubsection",
        "subsubcategory": "subsubsection",
        "nestedsection": "nestedsubsection",
        "nestedsubsection": "nestedsubsection",
        "promptbody": "prompt",
        "prompttext": "prompt",
        "negativeprompt": "negative",
        "imagemodel": "model",
        "parameters": "params",
        "parameter": "params",
        "settings": "params",
        "cfgscale": "cfg",
        "guidancescale": "cfg",
    }
    return aliases.get(key, key)


def _first_header_index(headers: list[str], candidates: tuple[str, ...]) -> int | None:
    for candidate in candidates:
        if candidate in headers:
            return headers.index(candidate)
    return None


def _category_for_table_row(library: dict, row: dict) -> dict:
    path_value = row.get("path", "")
    if path_value:
        parts = [_clean_heading_name(p) for p in re.split(r"\s*>\s*", path_value) if _clean_heading_name(p)]
    else:
        parts = []
        for key in ("section", "subsection", "subsubsection", "nestedsubsection"):
            value = _clean_heading_name(row.get(key, ""))
            if value:
                parts.append(value)
    if not parts:
        parts = ["Imported"]

    siblings = library["categories"]
    current = None
    for name in parts:
        current = next((c for c in siblings if c.get("name", "").strip().lower() == name.lower()), None)
        if current is None:
            current = schema.new_category(name)
            siblings.append(current)
        siblings = current.setdefault("subcategories", [])
    return current


def _derive_title(text: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return "Imported prompt"
    if len(clean) <= 72:
        return clean
    return clean[:69].rstrip() + "..."


def _split_tags(value: str) -> list[str]:
    tags = []
    for item in re.split(r"[,#;]", value):
        item = item.strip().lower()
        if item and item not in tags:
            tags.append(item)
    return tags


def _normalize_path_key(raw_key: str) -> str:
    return re.sub(r"[\s_-]+", "", raw_key.strip().lower())


def _normalize_outline_field(raw_key: str) -> str:
    key = re.sub(r"[\s_-]+", " ", raw_key.strip().lower())
    aliases = {
        "negative prompt": "negative",
        "image model": "model",
        "param": "params",
        "parameter": "params",
        "parameters": "params",
        "setting": "params",
        "settings": "params",
        "cfg scale": "cfg",
        "guidance": "cfg",
        "guidance scale": "cfg",
    }
    return aliases.get(key, key)


def _outline_block_to_prompt(block: dict) -> dict | None:
    body = "\n".join(ln for ln in block.get("prompt_lines", []) if ln is not None).strip()
    body = _decode_quoted_outline_body(body)
    title = (block.get("title") or "").strip() or _derive_title(body)
    if not title and not body:
        return None
    ptype = (block.get("type") or "").strip().lower()
    raw = {
        "title": title,
        "prompt": body or title,
        "tags": block.get("tags") or [],
        "note": block.get("note") or "",
    }
    if ptype:
        raw["type"] = ptype
    raw.update(block.get("image") or {})
    return schema.normalize_prompt(raw)


def _decode_quoted_outline_body(body: str) -> str:
    if len(body) >= 2 and body.startswith('"') and body.endswith('"'):
        try:
            decoded = json.loads(body)
            if isinstance(decoded, str):
                return decoded
        except Exception:
            pass
    return body
