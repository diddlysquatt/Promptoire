"""Promptoire data schema (v3) + faithful migration from older formats.

The v3 library is intentionally simple and LLM-friendly — that matters because
the headline feature is exporting the whole library as JSON, letting an LLM
rewrite it, and re-importing. A clean, explicit shape makes that round-trip
reliable.

    library = {
        "version": 3,
        "categories": [ Category, ... ]
    }

    Category = {
        "id": "cat_xxx",
        "name": "Coding",
        "icon": "",            # optional emoji
        "color": "",           # optional accent hex, e.g. "#3b82f6"
        "collapsed": false,
        "prompts": [ Prompt, ... ],
        "subcategories": [ Category, ... ]
    }

    Prompt = {
        "id": "prm_xxx",
        "type": "text" | "image",
        "title": "...",
        "prompt": "...",       # the body (kept as `prompt` for back-compat)
        "tags": [ "..." ],
        "note": "",
        "favorite": false,
        "uses": 0,
        "created_at": "ISO-8601",
        "updated_at": "ISO-8601",

        # image-only (present/meaningful when type == "image"):
        "negative": "",
        "model": "",           # "Midjourney v6", "SDXL", "Flux.1", ...
        "params": "",          # "--ar 16:9 --stylize 250" or "Steps: 30, CFG: 7"
        "seed": "",
        "sampler": "",
        "cfg": ""
    }
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 3

PROMPT_TYPES = ("text", "image")

# Fields that only carry meaning for image prompts.
IMAGE_FIELDS = ("negative", "model", "params", "seed", "sampler", "cfg")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _short_hash(*parts: str, n: int = 12) -> str:
    h = hashlib.sha1("\x1f".join(p or "" for p in parts).encode("utf-8")).hexdigest()
    return h[:n]


def make_prompt_id(title: str = "", body: str = "") -> str:
    """Stable, content-derived id when we have content; random otherwise."""
    if title or body:
        return "prm_" + _short_hash(title, body)
    return "prm_" + uuid.uuid4().hex[:12]


def make_category_id(name: str = "") -> str:
    if name:
        return "cat_" + _short_hash(name, uuid.uuid4().hex[:6])
    return "cat_" + uuid.uuid4().hex[:12]


def _as_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    if isinstance(v, str):
        return v
    return str(v)


def _as_list(v: Any) -> list:
    if isinstance(v, list):
        return v
    if v is None:
        return []
    return [v]


def new_prompt(
    title: str = "",
    body: str = "",
    type: str = "text",
    tags: list[str] | None = None,
    note: str = "",
    **image_fields: Any,
) -> dict:
    ts = now_iso()
    p = {
        "id": make_prompt_id(title, body),
        "type": type if type in PROMPT_TYPES else "text",
        "title": title,
        "prompt": body,
        "tags": list(tags or []),
        "note": note,
        "favorite": False,
        "uses": 0,
        "created_at": ts,
        "updated_at": ts,
    }
    for f in IMAGE_FIELDS:
        p[f] = _as_str(image_fields.get(f, ""))
    return p


def new_category(name: str = "New Category", icon: str = "", color: str = "") -> dict:
    return {
        "id": make_category_id(name),
        "name": name,
        "icon": icon,
        "color": color,
        "collapsed": False,
        "prompts": [],
        "subcategories": [],
    }


def normalize_prompt(raw: Any) -> dict | None:
    """Coerce any plausible prompt dict into a valid v3 prompt."""
    if not isinstance(raw, dict):
        return None
    # Accept several historical body keys.
    body = raw.get("prompt")
    if body is None:
        body = raw.get("body", raw.get("text", ""))
    title = _as_str(raw.get("title")) or _as_str(raw.get("name"))
    body = _as_str(body)
    if not title and not body:
        return None

    ptype = _as_str(raw.get("type"), "text").lower()
    if ptype not in PROMPT_TYPES:
        # Heuristic: looks like an image prompt if it has image-only metadata.
        ptype = "image" if any(raw.get(f) for f in IMAGE_FIELDS) else "text"

    pid = _as_str(raw.get("id"))
    if not pid.startswith("prm_"):
        pid = make_prompt_id(title, body)

    tags = [_as_str(t) for t in _as_list(raw.get("tags")) if _as_str(t).strip()]

    created = _as_str(raw.get("created_at")) or now_iso()
    updated = _as_str(raw.get("updated_at")) or created

    p = {
        "id": pid,
        "type": ptype,
        "title": title,
        "prompt": body,
        "tags": tags,
        "note": _as_str(raw.get("note")),
        "favorite": bool(raw.get("favorite", False)),
        "uses": int(raw.get("uses", raw.get("usage_count", 0)) or 0),
        "created_at": created,
        "updated_at": updated,
    }
    for f in IMAGE_FIELDS:
        p[f] = _as_str(raw.get(f, ""))
    return p


def _normalize_categories_container(container: Any) -> list[dict]:
    """Old format keyed categories by NAME (dict); v3 uses an ordered list.

    Handles dict-of-categories, list-of-categories, and nested subcategories
    in either shape. Preserves order (dict insertion order in py3.7+).
    """
    out: list[dict] = []
    if isinstance(container, dict):
        items = container.items()
    elif isinstance(container, list):
        items = [(None, c) for c in container]
    else:
        return out

    for key, raw in items:
        if not isinstance(raw, dict):
            continue
        name = _as_str(raw.get("name")).strip() or _as_str(key).strip() or "Untitled"
        cid = _as_str(raw.get("id"))
        if not cid.startswith("cat_"):
            cid = make_category_id(name)

        prompts = []
        for rp in _as_list(raw.get("prompts")):
            np = normalize_prompt(rp)
            if np is not None:
                prompts.append(np)

        subs = _normalize_categories_container(raw.get("subcategories"))

        out.append(
            {
                "id": cid,
                "name": name,
                "icon": _as_str(raw.get("icon")),
                "color": _as_str(raw.get("color")),
                "collapsed": bool(raw.get("collapsed", False)),
                "prompts": prompts,
                "subcategories": subs,
            }
        )
    return out


def normalize_library(data: Any) -> dict:
    """Return a valid v3 library from any historical/foreign shape.

    Tolerant by design: never raises on plausible input, always returns a
    well-formed library so the app and the JSON re-import loop stay robust.
    """
    if not isinstance(data, dict):
        # A bare list is interpreted as a list of prompts.
        if isinstance(data, list):
            cat = new_category("Imported")
            for rp in data:
                np = normalize_prompt(rp)
                if np:
                    cat["prompts"].append(np)
            return {"version": SCHEMA_VERSION, "categories": [cat] if cat["prompts"] else []}
        return {"version": SCHEMA_VERSION, "categories": []}

    categories = _normalize_categories_container(data.get("categories"))

    # Stray top-level prompts (old format had an unused `prompts: []`).
    loose = [normalize_prompt(p) for p in _as_list(data.get("prompts"))]
    loose = [p for p in loose if p]
    if loose:
        bucket = next((c for c in categories if c["name"].lower() == "uncategorized"), None)
        if bucket is None:
            bucket = new_category("Uncategorized")
            categories.append(bucket)
        bucket["prompts"].extend(loose)

    return {"version": SCHEMA_VERSION, "categories": categories}


# ---- traversal helpers -------------------------------------------------------

def iter_prompts(library: dict):
    """Yield (prompt, category, path_names) for every prompt, depth-first."""

    def walk(cats: list[dict], path: list[str]):
        for cat in cats:
            here = path + [cat.get("name", "")]
            for p in cat.get("prompts", []):
                yield p, cat, here
            yield from walk(cat.get("subcategories", []), here)

    yield from walk(library.get("categories", []), [])


def iter_categories(library: dict):
    """Yield (category, parent_or_None, path_names) for every category."""

    def walk(cats: list[dict], parent, path: list[str]):
        for cat in cats:
            here = path + [cat.get("name", "")]
            yield cat, parent, here
            yield from walk(cat.get("subcategories", []), cat, here)

    yield from walk(library.get("categories", []), None, [])


def count_prompts(library: dict) -> int:
    return sum(1 for _ in iter_prompts(library))
