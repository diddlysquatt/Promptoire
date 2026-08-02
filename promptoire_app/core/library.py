"""PromptLibrary — load/save and all mutations over the v3 library.

Pure data layer: no UI, no globals. The pywebview API wraps this.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from . import schema
from .schema import (
    iter_categories,
    iter_prompts,
    new_category,
    new_prompt,
    normalize_library,
    normalize_prompt,
    now_iso,
)

# Fields surfaced in the LLM-facing export (the bulk-improve loop). We keep
# `id` (so re-import can match safely) and the content the model should refine,
# and drop volatile bookkeeping (uses/timestamps/favorite) to keep the JSON
# clean and easy for an LLM to edit.
_EXPORT_PROMPT_FIELDS = ("id", "type", "title", "prompt", "tags", "note")
_CONTENT_PROMPT_FIELDS = ("type", "title", "prompt", "tags", "note") + schema.IMAGE_FIELDS


class PromptLibrary:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: dict = {"version": schema.SCHEMA_VERSION, "categories": []}

    # ---- persistence --------------------------------------------------------

    def load(self) -> "PromptLibrary":
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.data = normalize_library(raw)
            else:
                # Fresh install: seed a small curated library and persist it.
                from .defaults import default_library
                self.data = default_library()
                try:
                    self.save(backup=False)
                except Exception:
                    pass
        except Exception:
            # Never crash on a bad file — fall back to last good backup if any.
            recovered = self._load_latest_backup()
            self.data = recovered if recovered is not None else {
                "version": schema.SCHEMA_VERSION,
                "categories": [],
            }
        repaired = schema.repair_duplicate_prompt_ids(self.data)
        if repaired:
            try:
                self.save()
            except Exception:
                pass
        return self

    def save(self, *, backup: bool = True) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write via temp file + replace.
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
        if backup:
            self._rotate_backup()

    def _backups_dir(self) -> Path:
        d = self.path.parent / "backups"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _rotate_backup(self, keep: int = 12) -> None:
        try:
            d = self._backups_dir()
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(self.path, d / f"prompts-{stamp}.json")
            backups = sorted(d.glob("prompts-*.json"))
            for old in backups[:-keep]:
                old.unlink(missing_ok=True)
        except Exception:
            pass

    def _load_latest_backup(self) -> dict | None:
        try:
            d = self.path.parent / "backups"
            backups = sorted(d.glob("prompts-*.json"))
            for cand in reversed(backups):
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        return normalize_library(json.load(f))
                except Exception:
                    continue
        except Exception:
            pass
        return None

    # ---- lookups ------------------------------------------------------------

    def categories(self) -> list[dict]:
        return self.data.setdefault("categories", [])

    def find_prompt(self, prompt_id: str):
        for p, cat, path in iter_prompts(self.data):
            if p.get("id") == prompt_id:
                return p, cat, path
        return None, None, None

    def find_category(self, category_id: str):
        for cat, parent, path in iter_categories(self.data):
            if cat.get("id") == category_id:
                return cat, parent, path
        return None, None, None

    def _siblings_of_category(self, category_id: str) -> list[dict] | None:
        cat, parent, _ = self.find_category(category_id)
        if cat is None:
            return None
        return parent["subcategories"] if parent else self.categories()

    # ---- prompt CRUD --------------------------------------------------------

    def add_prompt(self, category_id: str | None, fields: dict) -> dict:
        p = new_prompt(
            title=fields.get("title", ""),
            body=fields.get("prompt", fields.get("body", "")),
            type=fields.get("type", "text"),
            tags=fields.get("tags", []),
            note=fields.get("note", ""),
            **{k: fields.get(k, "") for k in schema.IMAGE_FIELDS},
        )
        cat, _, _ = self.find_category(category_id) if category_id else (None, None, None)
        if cat is None:
            cats = self.categories()
            if not cats:
                cats.append(new_category("My Prompts"))
            cat = cats[0]
        cat.setdefault("prompts", []).append(p)
        return p

    def update_prompt(self, prompt_id: str, fields: dict) -> dict | None:
        p, _, _ = self.find_prompt(prompt_id)
        if p is None:
            return None
        allowed = {"title", "prompt", "type", "tags", "note", "favorite"} | set(schema.IMAGE_FIELDS)
        for k, v in fields.items():
            if k in allowed:
                p[k] = v
        if "type" in fields and p["type"] not in schema.PROMPT_TYPES:
            p["type"] = "text"
        p["updated_at"] = now_iso()
        return p

    def delete_prompt(self, prompt_id: str) -> dict | None:
        for cat, _, _ in iter_categories(self.data):
            prompts = cat.get("prompts", [])
            for i, p in enumerate(prompts):
                if p.get("id") == prompt_id:
                    return prompts.pop(i)
        return None

    def move_prompt(self, prompt_id: str, target_category_id: str, index: int | None = None) -> bool:
        cat, _, _ = self.find_category(target_category_id)
        if cat is None:
            # Validate the destination before removing anything from the source.
            return False
        removed = self.delete_prompt(prompt_id)
        if removed is None:
            return False
        prompts = cat.setdefault("prompts", [])
        if index is None or index < 0 or index > len(prompts):
            prompts.append(removed)
        else:
            prompts.insert(index, removed)
        return True

    def reorder_prompt(self, category_id: str, from_index: int, to_index: int) -> bool:
        cat, _, _ = self.find_category(category_id)
        if cat is None:
            return False
        prompts = cat.get("prompts", [])
        if not (0 <= from_index < len(prompts)):
            return False
        item = prompts.pop(from_index)
        to_index = max(0, min(to_index, len(prompts)))
        prompts.insert(to_index, item)
        return True

    def toggle_favorite(self, prompt_id: str) -> bool | None:
        p, _, _ = self.find_prompt(prompt_id)
        if p is None:
            return None
        p["favorite"] = not p.get("favorite", False)
        p["updated_at"] = now_iso()
        return p["favorite"]

    def record_use(self, prompt_id: str) -> str | None:
        p, _, _ = self.find_prompt(prompt_id)
        if p is not None:
            p["uses"] = int(p.get("uses", 0)) + 1
            used_at = now_iso()
            p["last_used"] = used_at
            return used_at
        return None

    # ---- category CRUD ------------------------------------------------------

    def add_category(self, name: str = "New Category", parent_id: str | None = None,
                     icon: str = "", color: str = "") -> dict:
        cat = new_category(name, icon, color)
        if parent_id:
            parent, _, _ = self.find_category(parent_id)
            if parent is not None:
                parent.setdefault("subcategories", []).append(cat)
                return cat
        self.categories().append(cat)
        return cat

    def update_category(self, category_id: str, fields: dict) -> dict | None:
        cat, _, _ = self.find_category(category_id)
        if cat is None:
            return None
        for k in ("name", "icon", "color", "collapsed"):
            if k in fields:
                cat[k] = fields[k]
        return cat

    def delete_category(self, category_id: str) -> bool:
        siblings = self._siblings_of_category(category_id)
        if siblings is None:
            return False
        for i, c in enumerate(siblings):
            if c.get("id") == category_id:
                siblings.pop(i)
                return True
        return False

    def reorder_category(self, category_id: str, to_index: int) -> bool:
        siblings = self._siblings_of_category(category_id)
        if siblings is None:
            return False
        idx = next((i for i, c in enumerate(siblings) if c.get("id") == category_id), None)
        if idx is None:
            return False
        item = siblings.pop(idx)
        to_index = max(0, min(to_index, len(siblings)))
        siblings.insert(to_index, item)
        return True

    # ---- search -------------------------------------------------------------

    def _category_display_meta(self) -> dict:
        """Per-category effective accents: color falls back to the nearest
        colored ancestor, so subcategory prompts always render with an accent."""
        meta: dict[str, dict] = {}

        def walk(cats: Iterable[dict], inherited: str):
            for c in cats:
                color = c.get("color") or inherited
                meta[c.get("id", "")] = {"color": color, "icon": c.get("icon", "")}
                walk(c.get("subcategories", []), color)

        walk(self.categories(), "")
        return meta

    def search(self, query: str = "", *, type_filter: str = "all",
               favorites_only: bool = False, tag: str = "") -> list[dict]:
        """Return a flat, ranked list of prompt hits with their category path.

        Query grammar: whitespace-separated terms must ALL match (AND);
        `#tag` terms filter by tag (prefix match), e.g. `mecha #maximalist`.
        """
        q = (query or "").strip().lower()
        terms: list[str] = []
        tag_terms: list[str] = []
        for tok in q.split():
            if tok.startswith("#") and len(tok) > 1:
                tag_terms.append(tok[1:])
            elif tok != "#":
                terms.append(tok)
        explicit_tag = (tag or "").strip().lower().lstrip("#")
        if explicit_tag:
            tag_terms.append(explicit_tag)

        cat_meta = self._category_display_meta()
        results: list[tuple[float, dict]] = []

        for p, cat, path in iter_prompts(self.data):
            if type_filter in ("text", "image") and p.get("type", "text") != type_filter:
                continue
            if favorites_only and not p.get("favorite"):
                continue
            ptags = [t.lower() for t in p.get("tags", [])]
            if tag_terms and not all(
                any(t.startswith(tt) for t in ptags) for tt in tag_terms
            ):
                continue

            score = 0.0
            if terms:
                title = p.get("title", "").lower()
                body = p.get("prompt", "").lower()
                catpath = " ".join(n.lower() for n in path)
                hay_tags = " ".join(ptags)
                for t in terms:
                    s = _match_score(t, title, body, hay_tags, catpath)
                    if s <= 0:
                        score = -1.0
                        break
                    score += s
                if score < 0:
                    continue
            # Light boost for favorites / usage so good stuff floats up.
            score += (2.0 if p.get("favorite") else 0.0) + min(int(p.get("uses", 0)), 20) * 0.05

            cmeta = cat_meta.get(cat.get("id", "") if cat else "", {})
            hit = {
                "id": p["id"],
                "type": p.get("type", "text"),
                "title": p.get("title", ""),
                "prompt": p.get("prompt", ""),
                "tags": p.get("tags", []),
                "note": p.get("note", ""),
                "favorite": p.get("favorite", False),
                "uses": p.get("uses", 0),
                "last_used": p.get("last_used", ""),
                "category_id": cat.get("id") if cat else None,
                "category_name": cat.get("name", "") if cat else "",
                "category_color": cmeta.get("color", ""),
                "category_icon": cmeta.get("icon", ""),
                "path": [n for n in path if n],
                "score": round(score, 3),
            }
            for f in schema.IMAGE_FIELDS:
                hit[f] = p.get(f, "")
            results.append((score, hit))

        # Stable sort: score desc, then title asc.
        results.sort(key=lambda t: (-t[0], t[1]["title"].lower()))
        return [h for _, h in results]

    # ---- stats --------------------------------------------------------------

    def stats(self) -> dict:
        total = 0
        text = 0
        image = 0
        favs = 0
        for p, _, _ in iter_prompts(self.data):
            total += 1
            if p.get("type") == "image":
                image += 1
            else:
                text += 1
            if p.get("favorite"):
                favs += 1
        ncats = sum(1 for _ in iter_categories(self.data))
        return {"total": total, "text": text, "image": image, "favorites": favs, "categories": ncats}

    # ---- export / import (the bulk-improve loop) ----------------------------

    def export_dict(self, *, full: bool = False) -> dict:
        """Library as JSON. `full` keeps everything; otherwise an LLM-clean view."""
        if full:
            return self.data

        def clean_cat(cat: dict) -> dict:
            out = {"id": cat.get("id"), "name": cat.get("name", "")}
            if cat.get("icon"):
                out["icon"] = cat["icon"]
            if cat.get("color"):
                out["color"] = cat["color"]
            prompts = []
            for p in cat.get("prompts", []):
                cp = {k: p.get(k) for k in _EXPORT_PROMPT_FIELDS if k in p}
                if p.get("type") == "image":
                    for f in schema.IMAGE_FIELDS:
                        if p.get(f):
                            cp[f] = p[f]
                prompts.append(cp)
            out["prompts"] = prompts
            subs = [clean_cat(s) for s in cat.get("subcategories", [])]
            if subs:
                out["subcategories"] = subs
            return out

        return {
            "version": schema.SCHEMA_VERSION,
            "categories": [clean_cat(c) for c in self.categories()],
        }

    def export_json(self, *, full: bool = False) -> str:
        return json.dumps(self.export_dict(full=full), indent=2, ensure_ascii=False)

    def export_outline(self) -> str:
        """Library as the plain outline format accepted by the importer."""
        lines: list[str] = []

        def add_prompt(path: list[str], p: dict) -> None:
            if lines:
                lines.append("")
            lines.append(f"Path: {_outline_one_line(' > '.join(path) or 'Imported')}")
            lines.append(f"Title: {_outline_one_line(p.get('title', '')) or 'Untitled'}")
            ptype = p.get("type", "text") if p.get("type") in schema.PROMPT_TYPES else "text"
            lines.append(f"Type: {ptype}")

            body = _outline_prompt_body(p.get("prompt", ""))
            body_lines = body.split("\n") if body else [""]
            lines.append(f"Prompt: {body_lines[0]}")
            lines.extend(body_lines[1:])

            tags = [_outline_one_line(t) for t in p.get("tags", []) if _outline_one_line(t)]
            if tags:
                lines.append("Tags: " + ", ".join(tags))
            note = _outline_one_line(p.get("note", ""))
            if note:
                lines.append(f"Note: {note}")

            if ptype == "image" or any(p.get(f) for f in schema.IMAGE_FIELDS):
                field_labels = {
                    "negative": "Negative prompt",
                    "model": "Image model",
                    "params": "Parameters",
                    "seed": "Seed",
                    "sampler": "Sampler",
                    "cfg": "CFG scale",
                }
                for key, label in field_labels.items():
                    value = _outline_one_line(p.get(key, ""))
                    if value:
                        lines.append(f"{label}: {value}")

        def walk(cats: list[dict], path: list[str]) -> None:
            for cat in cats:
                name = _outline_one_line(cat.get("name", "")) or "Imported"
                here = path + [name]
                for prompt in cat.get("prompts", []):
                    add_prompt(here, prompt)
                walk(cat.get("subcategories", []), here)

        walk(self.categories(), [])
        return ("\n".join(lines).strip() + "\n") if lines else ""

    def _merge_plan(self, incoming: Any) -> dict:
        """Resolve one immutable plan shared by preview and apply."""
        lib = normalize_library(incoming)
        by_id: dict[str, list[tuple[dict, dict]]] = {}
        by_path_title: dict[tuple[tuple[str, ...], str], list[tuple[dict, dict]]] = {}
        for prompt, category, path in iter_prompts(self.data):
            by_id.setdefault(prompt.get("id", ""), []).append((prompt, category))
            title_key = _path_title_key(path, prompt.get("title", ""))
            if title_key:
                by_path_title.setdefault(title_key, []).append((prompt, category))

        actions: list[dict] = []
        duplicates: list[dict] = []
        ambiguous: list[dict] = []
        seen_ids: set[str] = set()
        seen_titles: set[tuple[tuple[str, ...], str]] = set()

        for prompt, category, path in iter_prompts(lib):
            category_name = " / ".join(part for part in path if part) or (
                category.get("name", "") if category else ""
            )
            entry = {
                "id": prompt.get("id", ""),
                "type": prompt.get("type", "text"),
                "title": prompt.get("title", ""),
                "category_name": category_name,
            }
            prompt_id = prompt.get("id", "")
            title_key = _path_title_key(path, prompt.get("title", ""))
            repeated_id = bool(prompt_id and prompt_id in seen_ids)
            repeated_title = bool(title_key and title_key in seen_titles)
            if prompt_id:
                seen_ids.add(prompt_id)
            if title_key:
                seen_titles.add(title_key)
            if repeated_id:
                duplicates.append({
                    **entry,
                    "reason": "repeated id",
                })
                continue

            target: tuple[dict, dict] | None = None
            matched_by = ""
            ambiguity = ""
            id_matches = by_id.get(prompt_id, []) if prompt_id else []
            if len(id_matches) == 1:
                target = id_matches[0]
                matched_by = "id"
            elif len(id_matches) > 1:
                ambiguity = "more than one local prompt has this id"
            elif repeated_title:
                duplicates.append({
                    **entry,
                    "reason": "repeated title in the same section",
                })
                continue
            elif title_key:
                title_matches = by_path_title.get(title_key, [])
                if len(title_matches) == 1:
                    target = title_matches[0]
                    matched_by = "title"
                elif len(title_matches) > 1:
                    ambiguity = "more than one local prompt has this title in the same section"

            if ambiguity:
                ambiguous.append({**entry, "reason": ambiguity})
                continue
            if target is None:
                actions.append({"kind": "add", "prompt": prompt, "path": path, "entry": entry})
                continue

            current = target[0]
            changes = _diff_prompt(current, prompt)
            public = {
                **entry,
                "existing_id": current.get("id", ""),
                "matched_by": matched_by,
            }
            if changes:
                public.update(changes=changes, before_title=current.get("title", ""))
                kind = "update"
            else:
                kind = "unchanged"
            actions.append({
                "kind": kind,
                "prompt": prompt,
                "path": path,
                "target": current,
                "changes": changes,
                "entry": public,
            })

        return {
            "library": lib,
            "actions": actions,
            "duplicates": duplicates,
            "ambiguous": ambiguous,
        }

    def merge_preview(self, incoming: Any) -> dict:
        """Preview a non-destructive id-or-exact-path/title merge.

        Duplicate incoming rows and ambiguous local fallbacks are reported and
        skipped. Blank incoming fields do not erase nonblank local content.
        Nothing is mutated here.
        """
        plan = self._merge_plan(incoming)
        added = [a["entry"] for a in plan["actions"] if a["kind"] == "add"]
        updated = [a["entry"] for a in plan["actions"] if a["kind"] == "update"]
        unchanged = [a["entry"] for a in plan["actions"] if a["kind"] == "unchanged"]

        existing_paths = {_canonical_path_key(path) for _, _, path in iter_categories(self.data)}
        new_categories: list[str] = []
        for action in plan["actions"]:
            if action["kind"] != "add":
                continue
            parts = [part for part in action["path"] if part] or ["Imported"]
            for depth in range(1, len(parts) + 1):
                prefix = parts[:depth]
                key = _canonical_path_key(prefix)
                if key not in existing_paths:
                    existing_paths.add(key)
                    new_categories.append(" / ".join(prefix))

        return {
            "added": added,
            "updated": updated,
            "unchanged_count": len(unchanged),
            "duplicates": plan["duplicates"],
            "ambiguous": plan["ambiguous"],
            "new_categories": new_categories,
            "incoming_total": schema.count_prompts(plan["library"]),
        }

    def apply_merge(self, incoming: Any, *, update_existing: bool = True,
                    add_new: bool = True) -> dict:
        """Apply the exact plan shown by :meth:`merge_preview`.

        ID matches win; otherwise a unique normalized title in the exact
        section path can match. Updates never move or delete local prompts,
        and blank incoming fields never erase nonblank local values. Adds only
        create unmatched prompts and their missing category path.
        """
        plan = self._merge_plan(incoming)
        n_updated = n_added = n_cats = 0

        def category_for_path(path: list[str]) -> dict:
            nonlocal n_cats
            parts = [part for part in path if part] or ["Imported"]
            siblings = self.categories()
            current = None
            for name in parts:
                name_key = _canonical_name(name)
                current = next(
                    (c for c in siblings if _canonical_name(c.get("name", "")) == name_key),
                    None,
                )
                if current is None:
                    current = new_category(name)
                    siblings.append(current)
                    n_cats += 1
                siblings = current.setdefault("subcategories", [])
            return current

        for action in plan["actions"]:
            if action["kind"] == "update" and update_existing:
                current = action["target"]
                incoming_prompt = action["prompt"]
                for field in action["changes"]:
                    current[field] = incoming_prompt[field]
                current["updated_at"] = now_iso()
                n_updated += 1
            elif action["kind"] == "add" and add_new:
                destination = category_for_path(action["path"])
                destination.setdefault("prompts", []).append(action["prompt"])
                n_added += 1

        return {
            "updated": n_updated,
            "added": n_added,
            "new_categories": n_cats,
            "duplicates_skipped": len(plan["duplicates"]),
            "ambiguous_skipped": len(plan["ambiguous"]),
        }

    def replace_all(self, incoming: Any) -> None:
        self.data = normalize_library(incoming)
        schema.repair_duplicate_prompt_ids(self.data)


# ---- scoring helpers --------------------------------------------------------

def _match_score(q: str, title: str, body: str, tags: str, cat: str) -> float:
    """Cheap, good-enough relevance: weighted substring + subsequence."""
    score = 0.0
    if q in title:
        score += 10 - (title.index(q) * 0.05)
        if title.startswith(q):
            score += 5
    elif _subsequence(q, title):
        score += 3
    if q in tags:
        score += 6
    if q in cat:
        score += 4
    # Body: substring only. Subsequence over long text matches almost anything,
    # so it's pure noise here — titles (short) are where subsequence helps.
    if q in body:
        score += 2
    return score


def _subsequence(needle: str, haystack: str) -> bool:
    it = iter(haystack)
    return all(ch in it for ch in needle)


def _canonical_name(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _canonical_path_key(path: list[str]) -> tuple[str, ...]:
    return tuple(_canonical_name(part) for part in path if _canonical_name(part))


def _path_title_key(path: list[str], title: str) -> tuple[tuple[str, ...], str] | None:
    """Stable fallback match for non-JSON imports that do not carry ids."""
    title_key = _canonical_name(title)
    if not title_key:
        return None
    return (_canonical_path_key(path), title_key)


def _outline_one_line(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def _outline_prompt_body(value: Any) -> str:
    body = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return json.dumps(body, ensure_ascii=False) if "\n" in body else body


def _diff_prompt(cur: dict, inc: dict) -> dict:
    """Return safe, nonblank incoming fields that differ.

    Bulk imports are intentionally additive: an LLM omitting tags, notes, or
    image metadata must not silently erase useful local values. Intentional
    clearing remains available through Edit Library or Replace Library.
    """
    changes: dict[str, dict] = {}
    for k in _CONTENT_PROMPT_FIELDS:
        if k not in inc:
            continue
        a, b = cur.get(k), inc.get(k)
        if isinstance(b, list):
            if not b and a:
                continue
        elif isinstance(b, str):
            if not b.strip() and a:
                continue
        elif b is None and a is not None:
            continue
        if isinstance(a, list) or isinstance(b, list):
            if list(a or []) != list(b or []):
                changes[k] = {"before": a, "after": b}
        elif (a or "") != (b or ""):
            changes[k] = {"before": a, "after": b}
    return changes
