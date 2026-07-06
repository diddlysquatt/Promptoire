"""GUI-free smoke test of the full backend + API bridge.

Constructs the App against a temporary copy of the public sample library, but
never starts the webview loop, then exercises every data-path API method.
"""
import json
import os
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from promptoire_app.api import _parse_import_text
from promptoire_app.core import schema
from promptoire_app.core.library import PromptLibrary
from promptoire_app.main import App


class _ShellParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])


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

    rich_outline = """# AI Art > Characters
Title: Portrait Builder
Type: image
Prompt: Create a cinematic portrait of {subject} with dramatic rim lighting.
Tags: portrait, cinematic
Negative prompt: blurry, watermark
Image model: Midjourney v6
Parameters: --ar 4:5 --stylize 250
CFG scale: 7

# Workflows
## Research
1. Source map: Map the key sources for {topic}, group them by reliability, and list open questions.
"""
    rich = _parse_import_text(rich_outline)
    assert rich is not None, rich_outline
    rich_prompts = list(schema.iter_prompts(rich))
    out["outline.rich.total"] = len(rich_prompts)
    assert out["outline.rich.total"] == 2, out
    portrait = next(p for p, _, path in rich_prompts if p["title"] == "Portrait Builder")
    assert portrait["type"] == "image", portrait
    assert portrait["negative"] == "blurry, watermark", portrait
    assert portrait["model"] == "Midjourney v6", portrait
    assert portrait["params"] == "--ar 4:5 --stylize 250", portrait
    assert portrait["cfg"] == "7", portrait
    research_path = next(path for p, _, path in rich_prompts if p["title"] == "Source map")
    assert research_path == ["Workflows", "Research"], research_path

    with tempfile.TemporaryDirectory() as d:
        tmp_lib = PromptLibrary(Path(d) / "prompts.json")
        tmp_lib.data = {"version": 3, "categories": []}
        result = tmp_lib.apply_merge(rich)
        assert result["added"] == 2, result
        assert tmp_lib.categories()[0]["subcategories"][0]["name"] == "Characters"
        out["merge.outline.rich_added"] = result["added"]

    relaxed_outline = """Workflows
  Research
    Evidence map: Map the strongest sources for {topic}, grouped by reliability.
    - Question list: Turn {notes} into prioritized unanswered questions.

Section: Writing
Subsection: Editing
Prompt: Rewrite {text} for clarity while keeping the original voice.
Tags: editing, clarity
"""
    relaxed = _parse_import_text(relaxed_outline)
    assert relaxed is not None, relaxed_outline
    relaxed_prompts = list(schema.iter_prompts(relaxed))
    out["outline.relaxed.total"] = len(relaxed_prompts)
    assert out["outline.relaxed.total"] == 3, out
    relaxed_paths = {p["title"]: path for p, _, path in relaxed_prompts}
    assert relaxed_paths["Evidence map"] == ["Workflows", "Research"], relaxed_paths
    assert relaxed_paths["Question list"] == ["Workflows", "Research"], relaxed_paths
    editing = next(p for p, _, _ in relaxed_prompts if p["title"].startswith("Rewrite"))
    assert editing["tags"] == ["editing", "clarity"], editing

    path_outline = """Path: AI Art > Scenes > Landscapes
Dreamy landscape: A vast {place} at golden hour, painterly atmosphere, cinematic light.
"""
    path_import = _parse_import_text(path_outline)
    assert path_import is not None, path_outline
    path_prompts = list(schema.iter_prompts(path_import))
    deep_path = next(path for p, _, path in path_prompts if p["title"] == "Dreamy landscape")
    out["outline.path_field"] = deep_path
    assert deep_path == ["AI Art", "Scenes", "Landscapes"], deep_path

    sibling_outline = """Section: Writing
Subsection: Editing
Tight rewrite: Rewrite {text} clearly.

Subsection: Drafting
First draft: Draft a first pass about {topic}.

Section: Coding
Subsection: Debugging
Bug sweep: Review {code} for bugs.
"""
    sibling = _parse_import_text(sibling_outline)
    assert sibling is not None, sibling_outline
    sibling_paths = {p["title"]: path for p, _, path in schema.iter_prompts(sibling)}
    out["outline.sibling_subsections"] = sibling_paths
    assert sibling_paths["Tight rewrite"] == ["Writing", "Editing"], sibling_paths
    assert sibling_paths["First draft"] == ["Writing", "Drafting"], sibling_paths
    assert sibling_paths["Bug sweep"] == ["Coding", "Debugging"], sibling_paths

    array_import = """Here are a few prompts:
[
  {"title": "Array import", "prompt": "Use {topic} to verify array imports."}
]
"""
    array_data = _parse_import_text(array_import)
    assert array_data is not None, array_import
    array_lib = schema.normalize_library(array_data)
    out["loose_array.total"] = schema.count_prompts(array_lib)
    assert out["loose_array.total"] == 1, out

    with tempfile.TemporaryDirectory() as d:
        tmp_lib = PromptLibrary(Path(d) / "prompts.json")
        tmp_lib.data = {"version": 3, "categories": []}
        first_outline = """Workflows
  Research
    Evidence map: Map the strongest sources for {topic}.
"""
        revised_outline = """Workflows
  Research
    Evidence map: Map the strongest sources for {topic}, grouped by reliability and open questions.
"""
        tmp_lib.apply_merge(_parse_import_text(first_outline))
        revised = _parse_import_text(revised_outline)
        pv_title = tmp_lib.merge_preview(revised)
        out["merge.title_match.updated"] = len(pv_title["updated"])
        assert out["merge.title_match.updated"] == 1, pv_title
        assert pv_title["updated"][0]["matched_by"] == "title", pv_title
        result = tmp_lib.apply_merge(revised)
        out["merge.title_match.result"] = result
        assert result["updated"] == 1 and result["added"] == 0, result
        assert schema.count_prompts(tmp_lib.data) == 1, tmp_lib.data
        result_again = tmp_lib.apply_merge(revised)
        out["merge.title_match.repeat"] = result_again
        assert result_again["updated"] == 0 and result_again["added"] == 0, result_again
        no_update = tmp_lib.apply_merge(_parse_import_text("""Workflows
  Research
    Evidence map: A third body that should not duplicate when updates are off.
"""), update_existing=False, add_new=True)
        assert no_update["updated"] == 0 and no_update["added"] == 0, no_update
        assert schema.count_prompts(tmp_lib.data) == 1, tmp_lib.data

    example = json.loads((Path(__file__).resolve().parents[1] / "prompts.example.json").read_text(encoding="utf-8"))
    example = schema.normalize_library(example)
    out["example.total"] = schema.count_prompts(example)
    assert out["example.total"] >= 5, out

    shell = _ShellParser()
    shell.feed((Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "index.html").read_text(encoding="utf-8"))
    required_ids = {
        "app", "brandCount", "btnPin", "btnImprove", "btnEditor", "btnSettings",
        "btnCoffee", "btnClose", "viewLauncher", "search", "filters", "catrail",
        "results", "btnAdd", "btnImprove2", "viewEditor", "btnAddCategory",
        "viewBulk", "bulkBody", "viewSettings", "settingsBody", "toastHost", "modalHost",
    }
    missing_ids = sorted(required_ids - shell.ids)
    out["frontend.required_ids_missing"] = missing_ids
    assert not missing_ids, missing_ids
    expected_scripts = [
        "js/bridge.js", "js/state.js", "js/components.js", "js/launcher.js",
        "js/editor.js", "js/bulk.js", "js/settings.js", "js/app.js",
    ]
    out["frontend.script_order"] = shell.scripts
    assert shell.scripts == expected_scripts, shell.scripts
    bulk_js = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "js" / "bulk.js").read_text(encoding="utf-8")
    bulk_tokens = {
        "safe_merge_card": "merge-card",
        "replace_danger_zone": "danger-zone",
        "merge_action_guard": "Choose Add new or Update existing",
        "merge_state_sync": "syncMergeState",
        "title_match_badge": "matched by title",
        "outline_example_button": "Use outline example",
        "outline_example_handler": "insertOutlineExample",
    }
    missing_bulk_tokens = [name for name, token in bulk_tokens.items() if token not in bulk_js]
    out["frontend.bulk_contract_missing"] = missing_bulk_tokens
    assert not missing_bulk_tokens, missing_bulk_tokens

    root = Path(__file__).resolve().parents[1]
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    privacy_text = (root / "docs" / "PRIVACY.md").read_text(encoding="utf-8")
    security_text = (root / "SECURITY.md").read_text(encoding="utf-8")
    gitignore_text = (root / ".gitignore").read_text(encoding="utf-8")
    bug_template = (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
    feature_template = (root / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml").read_text(encoding="utf-8")
    issue_config = (root / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
    pr_template = (root / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    release_checklist = (root / "docs" / "GITHUB_RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    launcher_bat = (root / "Promptoire.bat").read_text(encoding="utf-8")
    release_tokens = {
        "readme_privacy_link": "[Privacy](docs/PRIVACY.md)" in readme_text,
        "readme_security_link": "[Security](SECURITY.md)" in readme_text,
        "privacy_local_first": "local-first" in privacy_text.lower(),
        "privacy_optional_ai": "Improve with AI now" in privacy_text,
        "security_sensitive_files": "prompts.json" in security_text and "promptoire.config.json" in security_text,
        "gitignore_private_prompt": "prompts.json" in gitignore_text,
        "gitignore_private_config": "promptoire.config.json" in gitignore_text,
        "bug_template_privacy": "prompts.json" in bug_template and "API keys" in bug_template,
        "feature_template_simple": "simple" in feature_template.lower() and "local-first" in feature_template,
        "issue_blank_disabled": "blank_issues_enabled: false" in issue_config,
        "pr_template_private_data": "prompts.json" in pr_template and "promptoire.config.json" in pr_template,
        "release_selftest": "--selftest" in release_checklist and '"mock": false' in release_checklist,
        "launcher_passes_args": "-m promptoire_app %*" in launcher_bat,
    }
    out["release.docs_ready"] = release_tokens
    assert all(release_tokens.values()), release_tokens

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
