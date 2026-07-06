"""GUI-free smoke test of the full backend + API bridge.

Constructs the App against a temporary copy of the public sample library, but
never starts the webview loop, then exercises every data-path API method.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from promptoire_app.api import _parse_import_text
from promptoire_app.core import schema
from promptoire_app.core.library import PromptLibrary
from promptoire_app.main import App


def _run_checks():
    app = App(debug=False)
    api = app.api
    out = {}

    st = api.get_state()
    assert st["ok"], st
    out["state.stats"] = st["stats"]
    out["state.categories"] = [c["name"] for c in st["categories"]]
    out["state.hotkey_available"] = st["hotkey_available"]

    s = api.search("review")
    assert s["ok"], s
    out["search.review.count"] = s["count"]
    out["search.review.top"] = s["results"][0]["title"][:40] if s["results"] else None
    assert s["count"] >= 1, s

    s2 = api.search("", "image")
    out["search.image.count"] = s2["count"]
    assert s2["count"] >= 1, s2

    exp = api.get_export(False)
    assert exp["ok"], exp
    data = json.loads(exp["json"])
    out["export.cats"] = len(data["categories"])

    # round-trip: preview merging the export back -> all unchanged
    pv = api.merge_preview(exp["json"])
    assert pv["ok"], pv
    out["merge.added"] = len(pv["preview"]["added"])
    out["merge.updated"] = len(pv["preview"]["updated"])
    out["merge.unchanged"] = pv["preview"]["unchanged_count"]

    # loose-json parsing: wrap in a code fence + prose like an LLM would
    fenced = "Sure! Here is the improved library:\n```json\n" + exp["json"] + "\n```\nEnjoy!"
    pv2 = api.merge_preview(fenced)
    assert pv2["ok"], pv2
    out["merge.fenced.unchanged"] = pv2["preview"]["unchanged_count"]

    outline = """# Smoke Imports
## Nested
- ZZ outline import: Use this temporary outline prompt to verify non-JSON import.
"""
    pv3 = api.merge_preview(outline)
    assert pv3["ok"], pv3
    out["merge.outline.added"] = len(pv3["preview"]["added"])
    out["merge.outline.new_categories"] = pv3["preview"]["new_categories"]
    assert "Smoke Imports / Nested" in pv3["preview"]["new_categories"], pv3

    with tempfile.TemporaryDirectory() as d:
        tmp_lib = PromptLibrary(Path(d) / "prompts.json")
        tmp_lib.data = {"version": 3, "categories": []}
        tmp_lib.apply_merge(_parse_import_text(outline))
        assert tmp_lib.categories()[0]["name"] == "Smoke Imports"
        assert tmp_lib.categories()[0]["subcategories"][0]["name"] == "Nested"
        out["merge.outline.preserved_nested"] = True

    example = json.loads((Path(__file__).resolve().parents[1] / "prompts.example.json").read_text(encoding="utf-8"))
    example = schema.normalize_library(example)
    out["example.total"] = schema.count_prompts(example)
    assert out["example.total"] >= 5, out

    # copy_export (clipboard may be unavailable in headless; just check shape)
    ce = api.copy_export(True, False)
    out["copy_export.ok"] = ce.get("ok")

    # add/update/delete cycle (against a temp clone — we won't save)
    add = api.add_prompt(st["categories"][0]["id"], {"title": "ZZ smoke", "prompt": "hello {name}", "tags": ["smoke"]})
    out["add.ok"] = add["ok"]
    pid = add["prompt"]["id"]
    upd = api.update_prompt(pid, {"title": "ZZ smoke 2"})
    out["update.ok"] = upd["ok"]
    dele = api.delete_prompt(pid)
    out["delete.ok"] = dele["ok"]

    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\nALL SMOKE CHECKS PASSED")


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as data_dir:
        data_path = Path(data_dir)
        shutil.copy2(root / "prompts.example.json", data_path / "prompts.json")
        config = root / "promptoire.config.json"
        if config.exists():
            shutil.copy2(config, data_path / "promptoire.config.json")
        os.environ["PROMPTOIRE_DATA_DIR"] = str(data_path)
        return _run_checks()


if __name__ == "__main__":
    sys.exit(main())
