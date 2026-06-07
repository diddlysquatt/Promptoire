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
        removed = self.delete_prompt(prompt_id)
        if removed is None:
            return False
        cat, _, _ = self.find_category(target_category_id)
        if cat is None:
            # Put it back where deletion happened is hard; drop into first cat.
            cats = self.categories()
            cat = cats[0] if cats else self.categories().append(new_category("My Prompts")) or self.categories()[0]
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

    def record_use(self, prompt_id: str) -> None:
        p, _, _ = self.find_prompt(prompt_id)
        if p is not None:
            p["uses"] = int(p.get("uses", 0)) + 1
            p["last_used"] = now_iso()

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

    def search(self, query: str = "", *, type_filter: str = "all",
               favorites_only: bool = False, tag: str = "") -> list[dict]:
        """Return a flat, ranked list of prompt hits with their category path."""
        q = (query or "").strip().lower()
        tagq = (tag or "").strip().lower()
        results: list[tuple[float, dict]] = []

        for p, cat, path in iter_prompts(self.data):
            if type_filter in ("text", "image") and p.get("type", "text") != type_filter:
                continue
            if favorites_only and not p.get("favorite"):
                continue
            ptags = [t.lower() for t in p.get("tags", [])]
            if tagq and tagq not in ptags:
                continue

            score = 0.0
            if q:
                title = p.get("title", "").lower()
                body = p.get("prompt", "").lower()
                catname = (cat.get("name", "") if cat else "").lower()
                hay_tags = " ".join(ptags)
                score = _match_score(q, title, body, hay_tags, catname)
                if score <= 0:
                    continue
            # Light boost for favorites / usage so good stuff floats up.
            score += (2.0 if p.get("favorite") else 0.0) + min(int(p.get("uses", 0)), 20) * 0.05

            hit = {
                "id": p["id"],
                "type": p.get("type", "text"),
                "title": p.get("title", ""),
                "prompt": p.get("prompt", ""),
                "tags": p.get("tags", []),
                "note": p.get("note", ""),
                "favorite": p.get("favorite", False),
                "uses": p.get("uses", 0),
                "category_id": cat.get("id") if cat else None,
                "category_name": cat.get("name", "") if cat else "",
                "category_color": cat.get("color", "") if cat else "",
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

    def merge_preview(self, incoming: Any) -> dict:
        """Diff an incoming library against current state, matching by prompt id.

        Returns a structured preview the UI shows before anything is written:
          added:    prompts whose id is new (or absent) -> will be created
          updated:  prompts whose id exists and content differs -> before/after
          unchanged: same id, identical content
          new_categories: category names that don't exist yet
        Nothing is mutated here.
        """
        lib = normalize_library(incoming)
        by_id = {p["id"]: (p, cat) for p, cat, _ in iter_prompts(self.data)}
        existing_cat_names = {c["name"].lower() for c, _, _ in iter_categories(self.data)}

        added, updated, unchanged = [], [], []
        seen_new_cats: set[str] = set()
        new_categories: list[str] = []

        for p, cat, path in iter_prompts(lib):
            cname = cat.get("name", "") if cat else ""
            if cname and cname.lower() not in existing_cat_names and cname.lower() not in seen_new_cats:
                seen_new_cats.add(cname.lower())
                new_categories.append(cname)

            target = by_id.get(p["id"])
            entry = {
                "id": p["id"],
                "type": p.get("type", "text"),
                "title": p.get("title", ""),
                "category_name": cname,
            }
            if target is None:
                added.append(entry)
            else:
                cur = target[0]
                changes = _diff_prompt(cur, p)
                if changes:
                    updated.append({**entry, "changes": changes,
                                    "before_title": cur.get("title", "")})
                else:
                    unchanged.append(entry)

        return {
            "added": added,
            "updated": updated,
            "unchanged_count": len(unchanged),
            "new_categories": new_categories,
            "incoming_total": schema.count_prompts(lib),
        }

    def apply_merge(self, incoming: Any, *, update_existing: bool = True,
                    add_new: bool = True) -> dict:
        """Apply a merge. Matches prompts by id. Never deletes local prompts.

        - Existing prompt (same id): fields overwritten from incoming (if update_existing).
        - New prompt: appended to a category matching its incoming category name
          (created if missing), if add_new.
        """
        lib = normalize_library(incoming)
        by_id = {p["id"]: p for p, _, _ in iter_prompts(self.data)}
        n_updated = n_added = n_cats = 0

        # Index existing top-level + nested categories by lowercase name.
        def cat_by_name(name: str) -> dict | None:
            for c, _, _ in iter_categories(self.data):
                if c["name"].lower() == name.lower():
                    return c
            return None

        for p, cat, _ in iter_prompts(lib):
            content_fields = ("type", "title", "prompt", "tags", "note") + schema.IMAGE_FIELDS
            if p["id"] in by_id:
                if update_existing:
                    cur = by_id[p["id"]]
                    for k in content_fields:
                        if k in p:
                            cur[k] = p[k]
                    cur["updated_at"] = now_iso()
                    n_updated += 1
            elif add_new:
                cname = cat.get("name", "") if cat else ""
                dest = cat_by_name(cname) if cname else None
                if dest is None:
                    dest = new_category(cname or "Imported")
                    self.categories().append(dest)
                    n_cats += 1
                dest.setdefault("prompts", []).append(p)
                n_added += 1

        return {"updated": n_updated, "added": n_added, "new_categories": n_cats}

    def replace_all(self, incoming: Any) -> None:
        self.data = normalize_library(incoming)


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


def _diff_prompt(cur: dict, inc: dict) -> dict:
    """Return {field: {before, after}} for content fields that differ."""
    fields = ("type", "title", "prompt", "tags", "note") + schema.IMAGE_FIELDS
    changes: dict[str, dict] = {}
    for k in fields:
        if k not in inc:
            continue
        a, b = cur.get(k), inc.get(k)
        if isinstance(a, list) or isinstance(b, list):
            if list(a or []) != list(b or []):
                changes[k] = {"before": a, "after": b}
        elif (a or "") != (b or ""):
            changes[k] = {"before": a, "after": b}
    return changes
