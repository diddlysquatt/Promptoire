"""The bridge exposed to the web UI as `window.pywebview.api.*`.

Every method returns plain JSON-able data and never raises across the bridge —
the UI gets {ok: bool, ...} envelopes so it can show friendly errors.
"""

from __future__ import annotations

import json
import re
import traceback
import webbrowser
from typing import Any

from .core import schema
from .platform import clipboard


def ok(**kw) -> dict:
    return {"ok": True, **kw}


def err(message: str, **kw) -> dict:
    return {"ok": False, "error": message, **kw}


class Api:
    def __init__(self, app):
        self._app = app  # the App controller (window, tray, hotkey, lib, settings)

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

    def copy_prompt(self, prompt_id: str, resolved_text: str | None = None) -> dict:
        """Copy a prompt. `resolved_text` lets the UI pass placeholder-filled text."""
        try:
            p, _, _ = self._app.library.find_prompt(prompt_id)
            if p is None and resolved_text is None:
                return err("Prompt not found")
            text = resolved_text if resolved_text is not None else p.get("prompt", "")
            if not clipboard.copy(text):
                return err("Clipboard unavailable")
            if p is not None:
                self._app.library.record_use(prompt_id)
                self._app.save_library_soon()
            behavior = self._app.settings.get("behavior", default={})
            if behavior.get("paste_after_copy"):
                self._app.after_copy_paste()
            spring = bool(behavior.get("copy_then_hide", True))
            if spring:
                self._app.hide_window()
            return ok(spring=spring, title=(p or {}).get("title", "Prompt"))
        except Exception as e:
            return err(str(e))

    def copy_text(self, text: str) -> dict:
        return ok() if clipboard.copy(text or "") else err("Clipboard unavailable")

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
            self._app.library.reorder_prompt(category_id, from_index, to_index)
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
            self._app.library.reorder_category(category_id, to_index)
            self._app.save_library()
            return ok()
        except Exception as e:
            return err(str(e))

    # ---- the bulk-improve loop ---------------------------------------------

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

    def save_export_file(self, full: bool = False) -> dict:
        try:
            path = self._app.save_file_dialog("prompts-export.json")
            if not path:
                return ok(cancelled=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._app.library.export_json(full=full))
            return ok(path=str(path))
        except Exception as e:
            return err(str(e))

    def load_import_file(self) -> dict:
        try:
            path = self._app.open_file_dialog()
            if not path:
                return ok(cancelled=True)
            with open(path, "r", encoding="utf-8") as f:
                return ok(text=f.read(), path=str(path))
        except Exception as e:
            return err(str(e))

    def ai_improve(self, full: bool = False) -> dict:
        """One-click: send the library + meta-prompt to the configured LLM API
        and return its (improved JSON) reply for previewing/merging."""
        try:
            from .core import ai_improve as _ai
            meta = self._app.settings.get("bulk_improve", "meta_prompt", default="")
            body = self._app.library.export_json(full=full)
            payload = f"{meta}\n\n```json\n{body}\n```"
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
                return err("Could not read that import. Paste JSON or a simple outline.")
            preview = self._app.library.merge_preview(data)
            return ok(preview=preview)
        except Exception as e:
            return err(str(e))

    def apply_merge(self, text: str, update_existing: bool = True, add_new: bool = True) -> dict:
        try:
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

    # ---- settings -----------------------------------------------------------

    def get_settings(self) -> dict:
        return ok(settings=self._app.settings.data)

    def update_settings(self, patch: dict) -> dict:
        try:
            self._app.apply_settings(patch or {})
            return ok(settings=self._app.settings.data)
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

    def open_external(self, url: str) -> dict:
        try:
            webbrowser.open(url)
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
        print(f"[selftest] report via bridge: {data}", file=_sys.stderr, flush=True)
        try:
            from .core import paths
            with open(paths.data_dir() / "_selftest.json", "w", encoding="utf-8") as f:
                json.dump(data or {}, f)
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
    return _parse_outline(text)


def _parse_loose_json(text: str) -> Any:
    """Parse JSON that may be wrapped in markdown code fences or have prose
    around it (LLMs love to add ```json fences and commentary)."""
    if text is None:
        return None
    s = text.strip()
    if not s:
        return None
    # Strip a leading ```json / ``` fence and trailing ```.
    if "```" in s:
        import re
        m = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
        if m:
            s = m.group(1).strip()
    try:
        return json.loads(s)
    except Exception:
        # Last resort: grab the outermost {...} block.
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end + 1])
            except Exception:
                return None
    return None


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])\s+(.+?)\s*$")
_FIELD_RE = re.compile(
    r"^\s*(title|prompt|body|text|tags|type|note|negative|model|params|seed|sampler|cfg)\s*:\s*(.*?)\s*$",
    re.IGNORECASE,
)
_SPLIT_RE = re.compile(r"\s+(?:[-–—]|::)\s+|:\s+")
_SEPARATOR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")


def _parse_outline(text: str) -> dict | None:
    """Convert a plain Markdown-ish outline into a v3 library.

    Supported shape:
      # Section
      ## Subsection
      - Prompt title: prompt body

    Headings become nested categories. Bullets, numbered items, `Title:` /
    `Prompt:` fields, and separated paragraphs become prompts. This is meant
    to make LLM-authored imports easy without forcing users to hand-edit JSON.
    """
    if text is None:
        return None
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    if not any(ln.strip() for ln in lines):
        return None

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
        parts = [p.strip() for p in re.split(r"\s*>\s*", raw_name) if p.strip()]
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

    for raw in lines:
        line = raw.strip()
        if not line:
            previous_blank = True
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            add_heading(len(heading.group(1)), heading.group(2).strip())
            previous_blank = False
            continue

        if _SEPARATOR_RE.match(line):
            finish_prompt()
            previous_blank = False
            continue

        bullet = _BULLET_RE.match(raw)
        if bullet:
            finish_prompt()
            block = ensure_block()
            _seed_outline_block(block, bullet.group(1).strip())
            previous_blank = False
            continue

        field = _FIELD_RE.match(line)
        if field:
            key = field.group(1).lower()
            value = field.group(2).strip()
            block = ensure_block()
            if key == "title":
                if previous_blank and block["started"]:
                    finish_prompt()
                    block = ensure_block()
                block["title"] = value
            elif key in ("prompt", "body", "text"):
                if previous_blank and block["started"] and not block["explicit_prompt"]:
                    finish_prompt()
                    block = ensure_block()
                block["prompt_lines"].append(value)
                block["explicit_prompt"] = True
                block["started"] = True
            elif key == "tags":
                block["tags"] = _split_tags(value)
            elif key == "type":
                block["type"] = value.lower()
            elif key == "note":
                block["note"] = value
            else:
                block["image"][key] = value
            previous_blank = False
            continue

        if previous_blank and current is not None and current.get("started") and not raw.startswith((" ", "\t")):
            finish_prompt()

        block = ensure_block()
        if not block["title"] and not block["prompt_lines"]:
            _seed_outline_block(block, line)
        else:
            append_prompt_line(line)
        previous_blank = False

    finish_prompt()

    if not saw_structure:
        return None
    if not any(True for _ in schema.iter_prompts(library)):
        return None
    return library


def _seed_outline_block(block: dict, text: str) -> None:
    left, right = _split_title_body(text)
    if right:
        block["title"] = left
        block["prompt_lines"].append(right)
    else:
        block["title"] = _derive_title(text)
        block["prompt_lines"].append(text)
    block["started"] = True


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


def _outline_block_to_prompt(block: dict) -> dict | None:
    body = "\n".join(ln for ln in block.get("prompt_lines", []) if ln is not None).strip()
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
