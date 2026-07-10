"""Promptoire data schema (v3) + faithful migration from older formats.

The v3 library is intentionally simple and LLM-friendly — that matters because
the headline workflow is exporting the whole library as an outline or JSON,
letting an LLM rewrite it, and re-importing. A clean, explicit shape makes that
round-trip reliable.

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


def _first_value(raw: dict, *keys: str) -> Any:
    for key in keys:
        if key in raw:
            return raw.get(key)
    return None


def _first_nonempty_value(raw: dict, *keys: str) -> Any:
    fallback = None
    for key in keys:
        if key not in raw:
            continue
        value = raw.get(key)
        if fallback is None:
            fallback = value
        if _as_str(value).strip():
            return value
    return fallback


_IMAGE_FIELD_ALIASES = {
    "negative": ("negative", "negative_prompt", "negativePrompt", "negative prompt"),
    "model": ("model", "image_model", "imageModel", "image model", "model_name", "modelName"),
    "params": ("params", "parameters", "parameter", "settings", "model_params", "modelParams"),
    "seed": ("seed",),
    "sampler": ("sampler",),
    "cfg": ("cfg", "cfg_scale", "cfgScale", "guidance", "guidance_scale", "guidanceScale"),
}


def _image_field_value(raw: dict, field: str) -> Any:
    return _first_nonempty_value(raw, *_IMAGE_FIELD_ALIASES.get(field, (field,)))


def _split_path(value: Any) -> list[str]:
    raw = _as_str(value).strip()
    if not raw:
        return []
    return [p.strip() for p in _re.split(r"\s*>\s*|\s*/\s*", raw) if p.strip()]


def _prompt_path_parts(raw: dict) -> list[str]:
    path = _first_value(raw, "path", "category_path", "categoryPath", "section_path", "sectionPath", "folder_path", "folderPath")
    parts = _split_path(path)
    if parts:
        return parts

    parts = []
    for key in ("section", "category", "folder", "group", "subsection", "subcategory", "sub_category", "subsubsection", "subsubcategory", "nestedsubsection"):
        value = _as_str(raw.get(key)).strip()
        if value:
            parts.extend(_split_path(value) or [value])
    return parts


def _category_for_path(categories: list[dict], parts: list[str]) -> dict:
    if not parts:
        parts = ["Uncategorized"]
    siblings = categories
    current = None
    for name in parts:
        key = name.strip().lower()
        current = next((c for c in siblings if c.get("name", "").strip().lower() == key), None)
        if current is None:
            current = new_category(name)
            siblings.append(current)
        siblings = current.setdefault("subcategories", [])
    return current


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


import re as _re

# Strong signals that a prompt is for an image model.
_IMAGE_MARKERS = _re.compile(
    r"--ar\b|--stylize\b|--niji\b|--chaos\b|--style\b|\bnegative prompt\b|"
    r"\bcfg\b|\bsampler\b|\bsteps:\s*\d|\bseed:\s*\d|::\s*\d",
    _re.IGNORECASE,
)


def looks_like_image_prompt(title: str, body: str) -> bool:
    return bool(_IMAGE_MARKERS.search(f"{title}\n{body}"))


def _derive_title(text: Any) -> str:
    clean = _re.sub(r"\s+", " ", _as_str(text)).strip()
    if not clean:
        return "Imported prompt"
    if len(clean) <= 72:
        return clean
    return clean[:69].rstrip() + "..."


# Category names that imply image prompts.
_ART_CATEGORY = _re.compile(
    r"\b(ai ?art|image|images|midjourney|stable ?diffusion|diffusion|dall[- ]?e|"
    r"flux|sdxl|sd|imagen|comfyui|art ?prompts?)\b",
    _re.IGNORECASE,
)


def normalize_prompt(raw: Any, default_type: str = "text") -> dict | None:
    """Coerce any plausible prompt dict into a valid v3 prompt.

    `default_type` is a hint from the owning category (e.g. an art category),
    used only when the prompt itself doesn't declare a type.
    """
    if isinstance(raw, str):
        body = raw.strip()
        if not body:
            return None
        ptype = "image" if looks_like_image_prompt("", body) else default_type
        if ptype not in PROMPT_TYPES:
            ptype = "text"
        return new_prompt(_derive_title(body), body, ptype)
    if not isinstance(raw, dict):
        return None
    # Accept several historical body keys.
    body = _first_value(raw, "prompt", "body", "text", "content")
    title = _as_str(raw.get("title")) or _as_str(raw.get("name"))
    body = _as_str(body)
    if not title and not body:
        return None

    ptype = _as_str(raw.get("type"), "").lower()
    if ptype not in PROMPT_TYPES:
        # Inference order: explicit image metadata > body markers > category hint.
        if any(_image_field_value(raw, f) for f in IMAGE_FIELDS) or looks_like_image_prompt(title, body):
            ptype = "image"
        elif default_type in PROMPT_TYPES:
            ptype = default_type
        else:
            ptype = "text"

    pid = _as_str(raw.get("id"))
    if not pid.startswith("prm_"):
        pid = make_prompt_id(title, body)

    if isinstance(raw.get("tags"), str):
        tag_items = [t.strip() for t in _re.split(r"[,#;]", raw.get("tags", ""))]
    else:
        tag_items = [_as_str(t).strip() for t in _as_list(raw.get("tags"))]
    tags = [t for t in tag_items if t]

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
        p[f] = _as_str(_image_field_value(raw, f))
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
        name = (
            _as_str(_first_value(raw, "name", "section", "category", "folder", "title")).strip()
            or _as_str(key).strip()
            or "Untitled"
        )
        cid = _as_str(raw.get("id"))
        if not cid.startswith("cat_"):
            cid = make_category_id(name)

        # Art-style categories hint that their prompts are image prompts.
        cat_default_type = "image" if _ART_CATEGORY.search(name) else "text"

        prompts = []
        prompt_container = _first_value(raw, "prompts", "items", "entries")
        for rp in _as_list(prompt_container):
            np = normalize_prompt(rp, default_type=cat_default_type)
            if np is not None:
                prompts.append(np)

        subs = _normalize_categories_container(
            _first_value(raw, "subcategories", "subsections", "sections", "categories", "children", "folders")
        )

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
    well-formed library so the app and the outline/JSON import loop stay robust.
    """
    if not isinstance(data, dict):
        # A bare list is interpreted as a list of prompts.
        if isinstance(data, list):
            categories: list[dict] = []
            for rp in data:
                np = normalize_prompt(rp)
                if not np:
                    continue
                path = _prompt_path_parts(rp) if isinstance(rp, dict) else []
                _category_for_path(categories, path or ["Imported"]).setdefault("prompts", []).append(np)
            return {"version": SCHEMA_VERSION, "categories": categories}
        return {"version": SCHEMA_VERSION, "categories": []}

    categories = _normalize_categories_container(
        _first_value(data, "categories", "sections", "folders", "groups")
    )

    # Stray top-level prompts (old format had an unused `prompts: []`).
    loose_container = _first_value(data, "prompts", "items", "entries")
    for raw_prompt in _as_list(loose_container):
        prompt = normalize_prompt(raw_prompt)
        if not prompt:
            continue
        path = _prompt_path_parts(raw_prompt) if isinstance(raw_prompt, dict) else []
        _category_for_path(categories, path or ["Uncategorized"]).setdefault("prompts", []).append(prompt)

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
