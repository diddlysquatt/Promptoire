"""GUI-free smoke test of the full backend + API bridge.

Constructs the App against a temporary copy of the public sample library, but
never starts the webview loop, then exercises every data-path API method.
"""
import json
import copy
import os
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import promptoire_app.api as api_module
from promptoire_app.api import _parse_import_text
from promptoire_app import __version__
from promptoire_app.core import schema
from promptoire_app.core.library import PromptLibrary
from promptoire_app.core.settings import DEFAULTS as SETTINGS_DEFAULTS, Settings
from promptoire_app.main import App
from promptoire_app.platform import clipboard, startup, window_fx
from promptoire_app.platform.hotkey import GlobalHotkey


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
    out["state.version"] = st["version"]
    assert out["state.version"] == __version__, out["state.version"]

    opened_links = []
    original_webbrowser_open = api_module.webbrowser.open
    api_module.webbrowser.open = lambda value: opened_links.append(value) or True
    try:
        secure_link = api.open_external("https://github.com/diddlysquatt/Promptoire")
        blocked_links = [
            api.open_external("http://example.com"),
            api.open_external("file:///C:/Windows/System32/calc.exe"),
            api.open_external("javascript:alert(1)"),
            api.open_external("not a URL"),
        ]
    finally:
        api_module.webbrowser.open = original_webbrowser_open
    out["external_links.https_only"] = (
        secure_link.get("ok") is True
        and all(result.get("ok") is False for result in blocked_links)
        and opened_links == ["https://github.com/diddlysquatt/Promptoire"]
    )
    assert out["external_links.https_only"], (secure_link, blocked_links, opened_links)

    with (
        patch.object(clipboard, "_HAVE_PYPERCLIP", False),
        patch.object(sys, "platform", "win32"),
        patch("subprocess.Popen") as popen,
    ):
        popen.return_value.communicate.return_value = (b"", b"")
        popen.return_value.returncode = 0
        clipboard_fallback = clipboard.copy("safe clipboard fallback")
    popen_args, popen_kwargs = popen.call_args
    out["clipboard.shell_free_fallback"] = (
        clipboard_fallback is True
        and popen_args == (["clip.exe"],)
        and popen_kwargs == {"stdin": api_module.subprocess.PIPE}
    )
    assert out["clipboard.shell_free_fallback"], (popen.call_args, clipboard_fallback)

    out["settings.default_density"] = SETTINGS_DEFAULTS["density"]
    assert out["settings.default_density"] == "compact", SETTINGS_DEFAULTS["density"]
    with tempfile.TemporaryDirectory() as density_dir:
        density_path = Path(density_dir) / "promptoire.config.json"
        density_path.write_text(json.dumps({"density": "enormous"}), encoding="utf-8")
        sanitized_density = Settings(density_path).load().get("density")
    out["settings.invalid_density_fallback"] = sanitized_density
    assert sanitized_density == "compact", sanitized_density
    with tempfile.TemporaryDirectory() as appearance_dir:
        appearance_path = Path(appearance_dir) / "promptoire.config.json"
        appearance_path.write_text(
            json.dumps({"background": "unsafe-custom-css", "font": "comic-sans"}),
            encoding="utf-8",
        )
        sanitized_appearance = Settings(appearance_path).load().data
    out["settings.invalid_appearance_fallback"] = {
        "background": sanitized_appearance["background"],
        "font": sanitized_appearance["font"],
    }
    assert sanitized_appearance["background"] == "", sanitized_appearance
    assert sanitized_appearance["font"] == "system", sanitized_appearance
    with tempfile.TemporaryDirectory() as appearance_save_dir:
        appearance_save_path = Path(appearance_save_dir) / "promptoire.config.json"
        appearance_settings = Settings(appearance_save_path).load()
        appearance_settings.update({"background": "mist", "font": "rounded"})
        appearance_settings.save()
        persisted_appearance = Settings(appearance_save_path).load().data
    out["settings.appearance_persists"] = {
        "background": persisted_appearance["background"],
        "font": persisted_appearance["font"],
    }
    assert persisted_appearance["background"] == "mist", persisted_appearance
    assert persisted_appearance["font"] == "rounded", persisted_appearance
    assert SETTINGS_DEFAULTS["ai"]["provider"] == "openai", SETTINGS_DEFAULTS["ai"]
    assert SETTINGS_DEFAULTS["ai"]["model"] == "gpt-5.6", SETTINGS_DEFAULTS["ai"]
    with tempfile.TemporaryDirectory() as ai_dir:
        ai_path = Path(ai_dir) / "promptoire.config.json"
        ai_path.write_text(json.dumps({"ai": {
            "provider": "anthropic", "api_key": "sk-ant-must-not-migrate",
            "model": "claude-old", "base_url": "https://example.com/v1"
        }}), encoding="utf-8")
        migrated_ai = Settings(ai_path).load().get("ai")
        migrated_key_removed_from_disk = json.loads(ai_path.read_text(encoding="utf-8"))["ai"]["api_key"] == ""
    out["settings.ai_migrated"] = migrated_ai
    assert migrated_ai["provider"] == "openai" and migrated_ai["model"] == "gpt-5.6", migrated_ai
    assert migrated_ai["base_url"] == "", migrated_ai
    assert migrated_ai["api_key"] == "", migrated_ai
    assert migrated_key_removed_from_disk
    with tempfile.TemporaryDirectory() as openai_dir:
        openai_path = Path(openai_dir) / "promptoire.config.json"
        openai_path.write_text(json.dumps({"ai": {
            "provider": "openai", "api_key": "sk-openai-kept",
            "model": "gpt-5.6-terra", "base_url": "https://api.openai.com/v1"
        }}), encoding="utf-8")
        official_ai = Settings(openai_path).load().get("ai")
    assert official_ai["api_key"] == "sk-openai-kept", official_ai
    assert official_ai["model"] == "gpt-5.6-terra" and official_ai["base_url"] == "", official_ai
    hotkey_normalization = {
        raw: GlobalHotkey().normalize(raw)
        for raw in ("F8", "F9", "~", "`", "grave", "backquote", "Alt C", "Control Z")
    }
    out["settings.hotkey_normalization"] = hotkey_normalization
    assert hotkey_normalization == {
        "F8": "f8",
        "F9": "f9",
        "~": "`",
        "`": "`",
        "grave": "`",
        "backquote": "`",
        "Alt C": "alt+c",
        "Control Z": "ctrl+z",
    }, hotkey_normalization
    out["settings.startup_command"] = startup._launch_command()
    assert "Promptoire.bat" in out["settings.startup_command"], out["settings.startup_command"]
    original_startup_set_enabled = startup.set_enabled
    initial_startup = bool(app.settings.get("behavior", "launch_at_startup", default=False))
    startup_calls = []
    startup.set_enabled = lambda enabled: startup_calls.append(bool(enabled)) or True
    try:
        target_startup = not initial_startup
        startup_effects = app.apply_settings({"behavior": {"launch_at_startup": target_startup}})
        startup.set_enabled = lambda enabled: False
        startup_failed_safely = False
        try:
            app.apply_settings({"behavior": {"launch_at_startup": initial_startup}})
        except RuntimeError:
            startup_failed_safely = (
                app.settings.get("behavior", "launch_at_startup") == target_startup
            )
    finally:
        startup.set_enabled = original_startup_set_enabled
        app.settings.update({"behavior": {"launch_at_startup": initial_startup}})
        app.settings.save()
    out["settings.startup_apply_contract"] = {
        "effects": startup_effects,
        "calls": startup_calls,
        "failure_rolled_back": startup_failed_safely,
    }
    assert startup_effects.get("startup") is True, startup_effects
    assert startup_calls == [target_startup] and startup_failed_safely, out["settings.startup_apply_contract"]
    resize_codes = {
        edge: window_fx.resize_hit_test(edge)
        for edge in ("left", "right", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right")
    }
    out["window.resize_hit_tests"] = resize_codes
    assert all(resize_codes.values()) and window_fx.resize_hit_test("invalid") == 0, resize_codes
    resize_geometry = {
        "right": window_fx.resize_bounds((100, 100, 560, 660), "right", 80, 0, 360, 420),
        "top_left": window_fx.resize_bounds((100, 100, 560, 660), "top-left", 30, 40, 360, 420),
        "minimum": window_fx.resize_bounds((100, 100, 560, 660), "bottom-right", -900, -900, 360, 420),
    }
    out["window.resize_geometry"] = resize_geometry
    assert resize_geometry["right"] == (100, 100, 640, 660), resize_geometry
    assert resize_geometry["top_left"] == (130, 140, 560, 660), resize_geometry
    assert resize_geometry["minimum"] == (100, 100, 460, 520), resize_geometry
    assert window_fx.restore_window(0) is False
    native_resize = api.begin_window_resize("left")
    out["window.resize_api_shape"] = native_resize
    assert native_resize.get("ok") is True and native_resize.get("started") is False, native_resize

    # The global hotkey is a visibility toggle, not a focus toggle: a visible
    # window must hide on the first press even when some other app has focus.
    toggle_calls = []
    original_show_window = app.show_window
    original_toggle_hide_window = app.hide_window
    original_visible = app._visible
    app.show_window = lambda *args, **kwargs: (toggle_calls.append("show"), setattr(app, "_visible", True))[-1]
    app.hide_window = lambda: (toggle_calls.append("hide"), setattr(app, "_visible", False))[-1]
    try:
        app._visible = True
        app.toggle_window()
        app.toggle_window()
    finally:
        app.show_window = original_show_window
        app.hide_window = original_toggle_hide_window
        app._visible = original_visible
    out["window.hotkey_true_visibility_toggle"] = toggle_calls
    assert toggle_calls == ["hide", "show"], toggle_calls

    # Native minimize and close requests hide to the notification area. Only
    # the explicit tray Quit path is allowed to destroy the window.
    lifecycle_calls = []
    original_lifecycle_hide_window = app.hide_window
    original_quitting = app._quitting
    app.hide_window = lambda: lifecycle_calls.append("hide")
    try:
        app._quitting = False
        app._on_minimized()
        close_cancelled = app._on_closing() is False
        app._quitting = True
        quit_close_allowed = app._on_closing() is True
    finally:
        app.hide_window = original_lifecycle_hide_window
        app._quitting = original_quitting
    out["window.hide_to_tray_lifecycle"] = {
        "calls": lifecycle_calls,
        "close_cancelled": close_cancelled,
        "quit_close_allowed": quit_close_allowed,
    }
    assert lifecycle_calls == ["hide", "hide"], lifecycle_calls
    assert close_cancelled and quit_close_allowed, out["window.hide_to_tray_lifecycle"]

    restore_calls = []
    original_window = app.window
    original_raise_to_front = app._raise_to_front
    class _RestoreProbeWindow:
        def restore(self):
            restore_calls.append("restore")

        def show(self):
            restore_calls.append("show")

        def evaluate_js(self, _script):
            restore_calls.append("focus")

    try:
        app.window = _RestoreProbeWindow()
        app._raise_to_front = lambda: restore_calls.append("raise")
        app.show_window(at_cursor=False)
    finally:
        app.window = original_window
        app._raise_to_front = original_raise_to_front
    out["window.restore_before_tray_show"] = restore_calls
    assert restore_calls == ["restore", "show", "focus", "raise"], restore_calls

    s = api.search("review")
    assert s["ok"], s
    out["search.review.count"] = s["count"]
    out["search.review.top"] = s["results"][0]["title"][:40] if s["results"] else None
    assert s["count"] >= 1, s

    s2 = api.search("", "image")
    out["search.image.count"] = s2["count"]
    assert s2["count"] >= 1, s2

    # The launcher pin must override the native copy-then-hide path, not just
    # the browser blur handler. Use a resolved missing prompt so this check
    # does not change library usage counts.
    copied_text = []
    hide_calls = []
    original_clipboard_copy = clipboard.copy
    original_hide_window = app.hide_window
    original_copy_then_hide = app.settings.data.setdefault("behavior", {}).get("copy_then_hide")
    clipboard.copy = lambda text: copied_text.append(text) or True
    app.hide_window = lambda: hide_calls.append("hide")
    app.settings.data["behavior"]["copy_then_hide"] = True
    try:
        pinned_copy = api.copy_prompt("prm_missing", "Pinned copy", keep_open=True)
        normal_copy = api.copy_prompt("prm_missing", "Normal copy", keep_open=False)
    finally:
        clipboard.copy = original_clipboard_copy
        app.hide_window = original_hide_window
        app.settings.data["behavior"]["copy_then_hide"] = original_copy_then_hide
    out["copy.pin_override"] = {
        "pinned_spring": pinned_copy.get("spring"),
        "normal_spring": normal_copy.get("spring"),
        "hide_calls": len(hide_calls),
        "copied": copied_text,
    }
    assert pinned_copy.get("ok") and pinned_copy.get("spring") is False, pinned_copy
    assert normal_copy.get("ok") and normal_copy.get("spring") is True, normal_copy
    assert hide_calls == ["hide"] and copied_text == ["Pinned copy", "Normal copy"], out["copy.pin_override"]

    exp = api.get_export(False)
    assert exp["ok"], exp
    data = json.loads(exp["json"])
    out["export.cats"] = len(data["categories"])

    outline_export = app.library.export_outline()
    out["export.outline.has_path"] = "Path:" in outline_export
    out["export.outline.has_prompt"] = "Prompt:" in outline_export
    out["export.outline.has_image_field"] = "Negative prompt:" in outline_export
    assert out["export.outline.has_path"], outline_export
    assert out["export.outline.has_prompt"], outline_export
    assert out["export.outline.has_image_field"], outline_export
    outline_export_data = _parse_import_text(outline_export)
    assert outline_export_data is not None, outline_export
    out["export.outline.total"] = schema.count_prompts(schema.normalize_library(outline_export_data))
    assert out["export.outline.total"] == st["stats"]["total"], out

    # round-trip: preview merging the export back -> all unchanged
    pv = api.merge_preview(exp["json"])
    assert pv["ok"], pv
    out["merge.added"] = len(pv["preview"]["added"])
    out["merge.updated"] = len(pv["preview"]["updated"])
    out["merge.unchanged"] = pv["preview"]["unchanged_count"]

    pv_outline = api.merge_preview(outline_export)
    assert pv_outline["ok"], pv_outline
    out["merge.outline_export.added"] = len(pv_outline["preview"]["added"])
    out["merge.outline_export.updated"] = len(pv_outline["preview"]["updated"])
    out["merge.outline_export.unchanged"] = pv_outline["preview"]["unchanged_count"]
    assert out["merge.outline_export.added"] == 0, pv_outline
    assert out["merge.outline_export.updated"] == 0, pv_outline
    assert out["merge.outline_export.unchanged"] == st["stats"]["total"], pv_outline

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

    fenced_outline = """Here is the outline:
```md
Path: Writing > Editing
Title: Tight rewrite
Prompt: Rewrite {text} clearly.
```
"""
    fenced_outline_data = _parse_import_text(fenced_outline)
    assert fenced_outline_data is not None, fenced_outline
    fenced_outline_prompts = list(schema.iter_prompts(fenced_outline_data))
    out["outline.fenced.total"] = len(fenced_outline_prompts)
    assert out["outline.fenced.total"] == 1, fenced_outline_prompts
    fenced_prompt, _, fenced_path = fenced_outline_prompts[0]
    assert fenced_prompt["title"] == "Tight rewrite", fenced_prompt
    assert fenced_path == ["Writing", "Editing"], fenced_path

    copied_chat_outline = """Pasted text(3).txt
hey could you get this all back to me with the exact suffix
Worked for 5m 18s
Every prompt ends with your exact string:
--ar 16:9 --stylize 1000 --hd --preview --profile ro69unw

Library
Improve this Promptoire outline. Keep existing paths stable.

Rules:
- Return only the outline, with no code fence or extra commentary.
- Use Path: Category > Subcategory.

Path: AI Art > Dream Logic
Title: Moon orchard
Type: image
Prompt: A nocturnal orchard growing miniature moons --ar 16:9 --stylize 1000 --hd --preview --profile ro69unw
Tags: moon, surreal
"""
    copied_chat = _parse_import_text(copied_chat_outline)
    assert copied_chat is not None, copied_chat_outline
    copied_chat_prompts = list(schema.iter_prompts(copied_chat))
    out["outline.copied_chat.total"] = len(copied_chat_prompts)
    out["outline.copied_chat.categories"] = [c["name"] for c in copied_chat["categories"]]
    assert out["outline.copied_chat.total"] == 1, copied_chat_prompts
    assert out["outline.copied_chat.categories"] == ["AI Art"], copied_chat
    assert copied_chat_prompts[0][0]["prompt"].endswith(
        "--ar 16:9 --stylize 1000 --hd --preview --profile ro69unw"
    ), copied_chat_prompts[0][0]

    heading_body_outline = """Path: Law > Review
Title: Opinion audit
Type: text
Prompt: Audit the opinion carefully.

CONSTRAINTS
- Do not invent actors.

DECISION DATE
Use the date on the filed opinion.

FULL PANEL
List every judge.
Tags: legal, audit

Path: Coding > Debugging
Title: Failure map
Type: text
Prompt: Trace the failure and return the smallest safe fix.
"""
    heading_body = _parse_import_text(heading_body_outline)
    assert heading_body is not None, heading_body_outline
    heading_body_prompts = list(schema.iter_prompts(heading_body))
    out["outline.prompt_headings_stay_body"] = len(heading_body_prompts) == 2
    out["outline.prompt_headings_categories"] = [c["name"] for c in heading_body["categories"]]
    opinion = next(p for p, _, _ in heading_body_prompts if p["title"] == "Opinion audit")
    assert out["outline.prompt_headings_stay_body"], heading_body_prompts
    assert out["outline.prompt_headings_categories"] == ["Law", "Coding"], heading_body
    assert "CONSTRAINTS" in opinion["prompt"] and "FULL PANEL" in opinion["prompt"], opinion

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

    from promptoire_app.core import ai_improve as ai_mod
    captured = {}
    original_improve = ai_mod.improve
    custom_outline_prompt = "Custom outline instruction for smoke tests. Return only the outline."
    api.update_settings({"bulk_improve": {"outline_prompt": custom_outline_prompt}})
    try:
        def fake_improve(ai, payload, **kwargs):
            captured["payload"] = payload
            return {"ok": True, "text": rich_outline, "model": "fake-outline-model"}

        ai_mod.improve = fake_improve
        ai_direct = api.ai_improve(False)
    finally:
        ai_mod.improve = original_improve
    out["ai_improve.outline_payload"] = (
        ai_direct.get("ok") is True
        and "Path:" in captured.get("payload", "")
        and "```json" not in captured.get("payload", "")
        and "Return only the outline" in captured.get("payload", "")
        and custom_outline_prompt in captured.get("payload", "")
    )
    assert out["ai_improve.outline_payload"], captured.get("payload", "")

    markdown_prompt_heading = """# Writing
## Editing
### Tight rewrite
Rewrite {text} clearly while preserving the original voice.

### Style adapter
Prompt: Rewrite {text} so it fits this style guide: {style_guide}
Tags: writing, style

## Drafting
### First draft
Draft a useful first pass about {topic}.
"""
    md_heading = _parse_import_text(markdown_prompt_heading)
    assert md_heading is not None, markdown_prompt_heading
    md_heading_prompts = list(schema.iter_prompts(md_heading))
    out["outline.markdown_prompt_headings.total"] = len(md_heading_prompts)
    assert out["outline.markdown_prompt_headings.total"] == 3, md_heading_prompts
    md_heading_paths = {p["title"]: path for p, _, path in md_heading_prompts}
    assert md_heading_paths["Tight rewrite"] == ["Writing", "Editing"], md_heading_paths
    assert md_heading_paths["Style adapter"] == ["Writing", "Editing"], md_heading_paths
    assert md_heading_paths["First draft"] == ["Writing", "Drafting"], md_heading_paths
    style_adapter = next(p for p, _, _ in md_heading_prompts if p["title"] == "Style adapter")
    assert style_adapter["tags"] == ["writing", "style"], style_adapter
    assert style_adapter["prompt"].startswith("Rewrite {text}"), style_adapter

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

    yamlish_outline = """Section: Writing
Subsection: Editing
Prompts:
  - Title: Tight rewrite
    Prompt: Rewrite {text} clearly while preserving voice.
    Tags: editing, clarity
  - Title: Voice match
    Prompt: Rewrite {text} so it matches this voice sample: {voice_sample}
    Tags: writing

Section: AI Art
Subsection: Portraits
Items:
  - Title: Neon portrait
    Type: image
    Prompt: Neon portrait of {subject}.
    Negative prompt: blurry, watermark
    Image model: Midjourney v6
    Parameters: --ar 4:5
"""
    yamlish = _parse_import_text(yamlish_outline)
    assert yamlish is not None, yamlish_outline
    yamlish_prompts = list(schema.iter_prompts(yamlish))
    out["outline.yamlish.total"] = len(yamlish_prompts)
    assert out["outline.yamlish.total"] == 3, yamlish_prompts
    yamlish_paths = {p["title"]: path for p, _, path in yamlish_prompts}
    assert yamlish_paths["Tight rewrite"] == ["Writing", "Editing"], yamlish_paths
    assert yamlish_paths["Voice match"] == ["Writing", "Editing"], yamlish_paths
    assert yamlish_paths["Neon portrait"] == ["AI Art", "Portraits"], yamlish_paths
    voice = next(p for p, _, _ in yamlish_prompts if p["title"] == "Voice match")
    assert voice["prompt"].startswith("Rewrite {text}"), voice
    neon = next(p for p, _, _ in yamlish_prompts if p["title"] == "Neon portrait")
    assert neon["type"] == "image", neon
    assert neon["negative"] == "blurry, watermark", neon
    assert neon["model"] == "Midjourney v6", neon
    assert neon["params"] == "--ar 4:5", neon

    numbered_outline = """Section: Workflows
Subsection: Cleanup
Prompt 1:
Review {notes} and extract the next actions.
Prompt 2: Summarize {topic} for a busy reader.
Prompt three:
Title: Follow-up writer
Prompt: Write a concise follow-up about {topic}.
Tags: follow-up, email
- Agenda builder
Prompt: Turn {notes} into a timed meeting agenda.
"""
    numbered = _parse_import_text(numbered_outline)
    assert numbered is not None, numbered_outline
    numbered_prompts = list(schema.iter_prompts(numbered))
    out["outline.numbered_labels.total"] = len(numbered_prompts)
    assert out["outline.numbered_labels.total"] == 4, out
    numbered_paths = {p["title"]: path for p, _, path in numbered_prompts}
    assert numbered_paths["Review {notes} and extract the next actions."] == ["Workflows", "Cleanup"], numbered_paths
    assert numbered_paths["Summarize {topic} for a busy reader."] == ["Workflows", "Cleanup"], numbered_paths
    follow_up = next(p for p, _, _ in numbered_prompts if p["title"] == "Follow-up writer")
    assert follow_up["tags"] == ["follow-up", "email"], follow_up
    agenda = next(p for p, _, _ in numbered_prompts if p["title"] == "Agenda builder")
    assert agenda["prompt"] == "Turn {notes} into a timed meeting agenda.", agenda

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

    bullet_tree_outline = """- Workflows
  - Research
    - Literature
      - Source map: Map the strongest sources for {topic}, grouped by reliability.
    - Interviews
      - Question planner: Turn {notes} into prioritized interview questions.
- AI Art
  - Characters
    - Portraits
      - Mood board: Create a visual direction board for {character}.
"""
    bullet_tree = _parse_import_text(bullet_tree_outline)
    assert bullet_tree is not None, bullet_tree_outline
    bullet_tree_paths = {p["title"]: path for p, _, path in schema.iter_prompts(bullet_tree)}
    out["outline.bullet_tree_paths"] = bullet_tree_paths
    assert bullet_tree_paths["Source map"] == ["Workflows", "Research", "Literature"], bullet_tree_paths
    assert bullet_tree_paths["Question planner"] == ["Workflows", "Research", "Interviews"], bullet_tree_paths
    assert bullet_tree_paths["Mood board"] == ["AI Art", "Characters", "Portraits"], bullet_tree_paths

    nested_label_outline = """Section: Workflows
Subsection: Research
Sub-subsection: Literature
Source map: Map the strongest sources for {topic}.

Nested subsection: Interviews
Question planner: Turn {notes} into prioritized interview questions.
"""
    nested_label = _parse_import_text(nested_label_outline)
    assert nested_label is not None, nested_label_outline
    nested_label_paths = {p["title"]: path for p, _, path in schema.iter_prompts(nested_label)}
    out["outline.nested_label_paths"] = nested_label_paths
    assert nested_label_paths["Source map"] == ["Workflows", "Research", "Literature"], nested_label_paths
    assert nested_label_paths["Question planner"] == ["Workflows", "Research", "Literature", "Interviews"], nested_label_paths

    table_import = """Here are the prompts:

| Section | Subsection | Title | Prompt | Tags |
| --- | --- | --- | --- | --- |
| Writing | Editing | Tight rewrite | Rewrite {text} clearly while preserving voice. | editing, clarity |
| AI Art | Portraits | Cinematic portrait | A dramatic 85mm portrait of {subject}. | portrait #cinematic |

| Path | Title | Prompt |
| --- | --- | --- |
| Coding > Debugging | Bug sweep | Review {code} for subtle bugs. |

"""
    table_data = _parse_import_text(table_import)
    assert table_data is not None, table_import
    table_prompts = list(schema.iter_prompts(table_data))
    out["outline.table.total"] = len(table_prompts)
    assert out["outline.table.total"] == 3, table_prompts
    table_paths = {p["title"]: path for p, _, path in table_prompts}
    assert table_paths["Tight rewrite"] == ["Writing", "Editing"], table_paths
    assert table_paths["Cinematic portrait"] == ["AI Art", "Portraits"], table_paths
    assert table_paths["Bug sweep"] == ["Coding", "Debugging"], table_paths
    table_prompt = next(p for p, _, _ in table_prompts if p["title"] == "Tight rewrite")
    assert table_prompt["tags"] == ["editing", "clarity"], table_prompt

    csv_import = '''Path,Title,Prompt,Tags
"Writing > Editing","Tight rewrite","Rewrite {text} clearly while preserving voice.","editing, clarity"
"Coding > Debugging","Bug sweep","Review {code} for subtle bugs.","code, review"
'''
    csv_data = _parse_import_text(csv_import)
    assert csv_data is not None, csv_import
    csv_prompts = list(schema.iter_prompts(csv_data))
    out["outline.csv_table.total"] = len(csv_prompts)
    assert out["outline.csv_table.total"] == 2, csv_prompts
    csv_paths = {p["title"]: path for p, _, path in csv_prompts}
    assert csv_paths["Tight rewrite"] == ["Writing", "Editing"], csv_paths
    assert csv_paths["Bug sweep"] == ["Coding", "Debugging"], csv_paths
    csv_prompt = next(p for p, _, _ in csv_prompts if p["title"] == "Tight rewrite")
    assert csv_prompt["tags"] == ["editing", "clarity"], csv_prompt

    image_table = """| Path | Title | Type | Prompt | Negative prompt | Image model | Parameters | CFG scale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AI Art > Characters > Portraits | Neon character | image | Neon portrait of {subject}. | blurry, watermark | Midjourney v6 | --ar 4:5 | 7 |
"""
    image_table_data = _parse_import_text(image_table)
    assert image_table_data is not None, image_table
    image_prompt, _, image_path = next(schema.iter_prompts(image_table_data))
    out["outline.image_table.path"] = image_path
    assert image_path == ["AI Art", "Characters", "Portraits"], image_path
    assert image_prompt["type"] == "image", image_prompt
    assert image_prompt["negative"] == "blurry, watermark", image_prompt
    assert image_prompt["model"] == "Midjourney v6", image_prompt
    assert image_prompt["params"] == "--ar 4:5", image_prompt
    assert image_prompt["cfg"] == "7", image_prompt

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

    string_array_import = """[
  "Summarize {article} into key takeaways.",
  "Create an image prompt for a cinematic portrait of {subject}, --ar 4:5"
]"""
    string_array_data = _parse_import_text(string_array_import)
    assert string_array_data is not None, string_array_import
    string_array_lib = schema.normalize_library(string_array_data)
    string_prompts = list(schema.iter_prompts(string_array_lib))
    out["json_string_array.total"] = len(string_prompts)
    assert out["json_string_array.total"] == 2, string_prompts
    assert string_prompts[0][0]["title"] == "Summarize {article} into key takeaways.", string_prompts
    assert string_prompts[1][0]["type"] == "image", string_prompts

    json_alias_import = """{
  "sections": [
    {
      "name": "Writing",
      "subsections": [
        {
          "name": "Editing",
          "items": [
            {
              "title": "Tight rewrite",
              "content": "Rewrite {text} clearly while preserving voice.",
              "tags": "editing, clarity"
            }
          ]
        }
      ]
    }
  ],
  "entries": [
    {
      "title": "Inbox triage",
      "prompt": "Turn {messages} into prioritized replies."
    },
    {
      "section": "Coding",
      "subsection": "Review",
      "title": "Risk pass",
      "content": "Review {code} for likely regressions."
    }
  ]
}"""
    json_alias_data = _parse_import_text(json_alias_import)
    assert json_alias_data is not None, json_alias_import
    json_alias_lib = schema.normalize_library(json_alias_data)
    out["json_alias_import.total"] = schema.count_prompts(json_alias_lib)
    assert out["json_alias_import.total"] == 3, json_alias_lib
    json_alias_paths = {p["title"]: path for p, _, path in schema.iter_prompts(json_alias_lib)}
    assert json_alias_paths["Tight rewrite"] == ["Writing", "Editing"], json_alias_paths
    assert json_alias_paths["Inbox triage"] == ["Uncategorized"], json_alias_paths
    assert json_alias_paths["Risk pass"] == ["Coding", "Review"], json_alias_paths
    json_alias_prompt = next(p for p, _, _ in schema.iter_prompts(json_alias_lib) if p["title"] == "Tight rewrite")
    assert json_alias_prompt["prompt"].startswith("Rewrite {text}"), json_alias_prompt
    assert json_alias_prompt["tags"] == ["editing", "clarity"], json_alias_prompt

    array_path_import = """[
  {
    "path": "Writing > Drafting",
    "title": "First draft",
    "prompt": "Draft a useful first pass about {topic}."
  }
]"""
    array_path_data = _parse_import_text(array_path_import)
    assert array_path_data is not None, array_path_import
    array_path_lib = schema.normalize_library(array_path_data)
    array_path_prompt, _, array_path = next(schema.iter_prompts(array_path_lib))
    out["json_array_path"] = array_path
    assert array_path_prompt["title"] == "First draft", array_path_prompt
    assert array_path == ["Writing", "Drafting"], array_path

    image_json_alias_import = """[
  {
    "path": "AI Art > Characters > Portraits",
    "title": "Neon portrait",
    "prompt": "Neon portrait of {subject}.",
    "negative_prompt": "blurry, watermark",
    "image_model": "Midjourney v6",
    "parameters": "--ar 4:5",
    "cfg_scale": "7"
  }
]"""
    image_json_alias_data = _parse_import_text(image_json_alias_import)
    assert image_json_alias_data is not None, image_json_alias_import
    image_json_alias_lib = schema.normalize_library(image_json_alias_data)
    image_json_prompt, _, image_json_path = next(schema.iter_prompts(image_json_alias_lib))
    out["json_image_alias_path"] = image_json_path
    assert image_json_path == ["AI Art", "Characters", "Portraits"], image_json_path
    assert image_json_prompt["type"] == "image", image_json_prompt
    assert image_json_prompt["negative"] == "blurry, watermark", image_json_prompt
    assert image_json_prompt["model"] == "Midjourney v6", image_json_prompt
    assert image_json_prompt["params"] == "--ar 4:5", image_json_prompt
    assert image_json_prompt["cfg"] == "7", image_json_prompt

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

    # Safe merge must preview and apply the same plan, skip repeated input,
    # avoid arbitrary same-title matches, and preserve omitted local metadata.
    with tempfile.TemporaryDirectory() as d:
        merge_lib = PromptLibrary(Path(d) / "prompts.json")
        duplicate_import = {
            "version": 3,
            "categories": [{
                "name": "Workflows", "prompts": [], "subcategories": [{
                    "name": "Research", "subcategories": [], "prompts": [
                        {"id": "prm_incoming001", "title": "Evidence map", "prompt": "First body"},
                        {"id": "prm_incoming002", "title": "Evidence map", "prompt": "Second body"},
                    ],
                }],
            }],
        }
        preview_duplicate = merge_lib.merge_preview(duplicate_import)
        applied_duplicate = merge_lib.apply_merge(copy.deepcopy(duplicate_import))
        assert len(preview_duplicate["added"]) == 1, preview_duplicate
        assert len(preview_duplicate["duplicates"]) == 1, preview_duplicate
        assert applied_duplicate["added"] == 1 and applied_duplicate["updated"] == 0, applied_duplicate
        assert applied_duplicate["duplicates_skipped"] == 1, applied_duplicate
        assert schema.count_prompts(merge_lib.data) == 1, merge_lib.data
        assert len(preview_duplicate["new_categories"]) == applied_duplicate["new_categories"] == 2

        local = next(schema.iter_prompts(merge_lib.data))[0]
        local["tags"] = ["keep-me"]
        local["note"] = "Keep this note"
        sparse_update = copy.deepcopy(duplicate_import)
        sparse_update["categories"][0]["subcategories"][0]["prompts"] = [{
            "id": local["id"], "title": "Evidence map", "prompt": "Improved body"
        }]
        sparse_result = merge_lib.apply_merge(sparse_update)
        assert sparse_result["updated"] == 1, sparse_result
        assert local["tags"] == ["keep-me"] and local["note"] == "Keep this note", local

        local_category = merge_lib.categories()[0]["subcategories"][0]
        second_local = schema.new_prompt("Evidence map", "Another local body")
        local_category["prompts"].append(second_local)
        ambiguous_import = copy.deepcopy(duplicate_import)
        ambiguous_import["categories"][0]["subcategories"][0]["prompts"] = [{
            "id": "prm_no_local_match", "title": "Evidence map", "prompt": "Unsafe fallback"
        }]
        ambiguous_preview = merge_lib.merge_preview(ambiguous_import)
        ambiguous_result = merge_lib.apply_merge(ambiguous_import)
        assert not ambiguous_preview["added"] and not ambiguous_preview["updated"], ambiguous_preview
        assert len(ambiguous_preview["ambiguous"]) == 1, ambiguous_preview
        assert ambiguous_result["ambiguous_skipped"] == 1, ambiguous_result

        exact_import = copy.deepcopy(ambiguous_import)
        exact_prompt = exact_import["categories"][0]["subcategories"][0]["prompts"][0]
        exact_prompt["id"] = second_local["id"]
        exact_prompt["prompt"] = "Exact id update"
        exact_preview = merge_lib.merge_preview(exact_import)
        assert len(exact_preview["updated"]) == 1 and exact_preview["updated"][0]["matched_by"] == "id", exact_preview

        moved_path = {
            "version": 3,
            "categories": [{"name": "Entirely New", "subcategories": [], "prompts": [{
                "id": second_local["id"], "title": "Evidence map", "prompt": "Still update in place"
            }]}],
        }
        moved_preview = merge_lib.merge_preview(moved_path)
        moved_result = merge_lib.apply_merge(moved_path)
        assert moved_preview["new_categories"] == [], moved_preview
        assert moved_result["new_categories"] == 0, moved_result
        assert merge_lib.find_prompt(second_local["id"])[2] == ["Workflows", "Research"]

    with tempfile.TemporaryDirectory() as d:
        exact_lib = PromptLibrary(Path(d) / "prompts.json")
        exact_category = schema.new_category("Same Section")
        first_same = schema.new_prompt("Repeated title", "First local")
        second_same = schema.new_prompt("Repeated title", "Second local")
        exact_category["prompts"] = [first_same, second_same]
        exact_lib.data = {"version": 3, "categories": [exact_category]}
        exact_updates = {
            "version": 3, "categories": [{
                "id": exact_category["id"], "name": "Same Section", "subcategories": [], "prompts": [
                    {"id": first_same["id"], "title": "Repeated title", "prompt": "First updated"},
                    {"id": second_same["id"], "title": "Repeated title", "prompt": "Second updated"},
                ],
            }],
        }
        exact_updates_preview = exact_lib.merge_preview(exact_updates)
        exact_updates_result = exact_lib.apply_merge(exact_updates)
        assert len(exact_updates_preview["updated"]) == 2, exact_updates_preview
        assert not exact_updates_preview["duplicates"], exact_updates_preview
        assert exact_updates_result["updated"] == 2, exact_updates_result

    same_a = schema.new_prompt("Same", "Same body")
    same_b = schema.new_prompt("Same", "Same body")
    assert same_a["id"] != same_b["id"], (same_a, same_b)
    repair_data = {"version": 3, "categories": [{
        "id": "cat_repair", "name": "Repair", "prompts": [same_a, {**same_b, "id": same_a["id"]}], "subcategories": []
    }]}
    assert schema.repair_duplicate_prompt_ids(repair_data) == 1, repair_data
    assert len({p["id"] for p, _, _ in schema.iter_prompts(repair_data)}) == 2, repair_data
    with tempfile.TemporaryDirectory() as d:
        repair_path = Path(d) / "prompts.json"
        repair_path.write_text(json.dumps(repair_data | {"categories": [{
            "id": "cat_repair", "name": "Repair", "subcategories": [], "prompts": [
                {**same_a, "id": "prm_legacyduplicate"},
                {**same_b, "id": "prm_legacyduplicate"},
            ],
        }]}), encoding="utf-8")
        persisted_lib = PromptLibrary(repair_path).load()
        persisted_ids = [p["id"] for p, _, _ in schema.iter_prompts(persisted_lib.data)]
        disk_ids = [p["id"] for p, _, _ in schema.iter_prompts(json.loads(repair_path.read_text(encoding="utf-8")))]
        assert len(set(persisted_ids)) == 2 and disk_ids == persisted_ids, (persisted_ids, disk_ids)

    example = json.loads((Path(__file__).resolve().parents[1] / "prompts.example.json").read_text(encoding="utf-8"))
    example = schema.normalize_library(example)
    out["example.total"] = schema.count_prompts(example)
    assert out["example.total"] >= 5, out

    web_index_text = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "index.html").read_text(encoding="utf-8")
    shell = _ShellParser()
    shell.feed(web_index_text)
    required_ids = {
        "app", "brandCount", "btnPin", "btnImprove", "btnEditor", "btnSettings", "btnDensity",
        "btnCoffee", "btnClose", "viewLauncher", "search", "filters", "catrail",
        "results", "btnAdd", "viewEditor", "btnAddCategory",
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
    from PIL import Image
    icon_root = Path(__file__).resolve().parents[1]
    with Image.open(icon_root / "icons" / "promptoire.ico") as app_icon:
        bundled_icon_sizes = sorted(app_icon.ico.sizes())
    with Image.open(icon_root / "promptoire_app" / "web" / "assets" / "tray.png") as tray_icon:
        tray_contract = {
            "mode": tray_icon.mode,
            "size": tray_icon.size,
            "transparent_corner": tray_icon.convert("RGBA").getpixel((0, 0))[3] == 0,
        }
    out["frontend.shared_app_icon"] = {
        "ico_sizes": bundled_icon_sizes,
        "tray": tray_contract,
        "header_uses_asset": 'class="brand-mark" src="assets/tray.png"' in web_index_text,
        "about_uses_asset": 'class: "logo-big", src: "assets/tray.png"' in (
            icon_root / "promptoire_app" / "web" / "js" / "settings.js"
        ).read_text(encoding="utf-8"),
    }
    assert (16, 16) in bundled_icon_sizes and (256, 256) in bundled_icon_sizes, bundled_icon_sizes
    assert tray_contract == {"mode": "RGBA", "size": (128, 128), "transparent_corner": True}, tray_contract
    assert out["frontend.shared_app_icon"]["header_uses_asset"], out["frontend.shared_app_icon"]
    assert out["frontend.shared_app_icon"]["about_uses_asset"], out["frontend.shared_app_icon"]
    bulk_js = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "js" / "bulk.js").read_text(encoding="utf-8")
    bridge_js = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "js" / "bridge.js").read_text(encoding="utf-8")
    app_js = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "js" / "app.js").read_text(encoding="utf-8")
    launcher_js = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "js" / "launcher.js").read_text(encoding="utf-8")
    editor_js = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "js" / "editor.js").read_text(encoding="utf-8")
    settings_js = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "js" / "settings.js").read_text(encoding="utf-8")
    components_css = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "css" / "components.css").read_text(encoding="utf-8")
    base_css = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "css" / "base.css").read_text(encoding="utf-8")
    bulk_tokens = {
        "safe_merge_card": "merge-card",
        "replace_danger_zone": "danger-zone",
        "merge_action_guard": "Choose Add new or Update existing",
        "merge_state_sync": "syncMergeState",
        "title_match_badge": "matched by title",
        "outline_library_button": "Copy instructions + library",
        "outline_library_handler": "copyOutlineExport",
        "outline_request_modal": "Prompt batch request",
        "outline_request_topic": "Topic or workflow",
        "outline_request_builder": "buildOutlineRequest",
        "outline_request_blank": "Copy blank",
        "outline_instructions_inline": "outlineInstructions",
        "outline_instructions_label": "Improvement instructions",
        "outline_instructions_copy": "Copy instructions only",
        "instructions_reset_button": "Reset default",
        "instructions_default_bridge": "bulk_prompt_defaults",
        "outline_default_loaded": "Default instructions restored",
        "json_default_loaded": "Default JSON instructions loaded",
        "save_outline_button": "Save library outline",
        "save_outline_handler": "saveOutlineFile",
        "more_options_disclosure": "More options",
        "topic_request_label": "Create prompts for a topic",
        "json_instructions_button": "Edit JSON instructions",
        "outline_example_button": "Use outline example",
        "outline_example_handler": "insertOutlineExample",
        "paste_clipboard_button": "Paste from clipboard",
        "paste_clipboard_handler": "pasteClipboard",
        "manual_paste_preview": 'addEventListener("paste"',
        "clear_import_button": "Clear",
        "clear_import_handler": "clearImport",
        "outline_first_import_help": "Paste an outline or JSON",
        "outline_first_empty_import": "Paste an outline or JSON first",
        "incoming_preview_count": "incomingTotal",
        "selected_change_guard": "selectedChangeCount",
        "selected_change_empty_note": "No selected changes to merge",
        "merge_adds_only_note": "Adds new only",
        "merge_updates_only_note": "Updates existing only",
        "import_error_recovery": "Import not readable",
        "import_error_formats": "YAML-style list",
        "import_error_csv": "CSV table",
        "new_category_preview": "newCategoryPreview",
        "new_section_label": "New sections",
        "safe_duplicate_skip": "duplicates_skipped",
        "safe_ambiguous_skip": "ambiguous_skipped",
        "safe_blank_contract": "Blank imported fields never erase local content",
        "openai_panel": "OpenAI connection · optional",
        "openai_latest_models": "gpt-5.6-sol",
        "openai_save_before_improve": "if (!await saveAiSettings(false)) return;",
        "blank_instructions_feedback_improve": "if (!await persistOutlineInstructions(true)) return;",
        "blank_instructions_feedback_copy": "includeInstructions && !await persistOutlineInstructions(true)",
        "numbered_prompt_blocks": "Prompt 1:",
        "strict_output_contract": "STRICT OUTPUT CONTRACT",
        "canonical_record_path": "The first nonblank line must be Path:",
        "canonical_record_fields": "using only Path, Title, Type, Prompt, and optional Tags",
        "image_suffix_in_prompt": "put all copyable model flags at the very end of Prompt",
        "no_default_image_metadata": "Do not add separate",
        "merge_busy_guard": "Merging…",
    }
    missing_bulk_tokens = [name for name, token in bulk_tokens.items() if token not in bulk_js]
    out["frontend.bulk_contract_missing"] = missing_bulk_tokens
    assert not missing_bulk_tokens, missing_bulk_tokens
    out["frontend.outline_first_export"] = bulk_js.index("Copy instructions + library") < bulk_js.index("Copy JSON request + library")
    assert out["frontend.outline_first_export"], "Readable outline export should stay ahead of JSON export"
    out["frontend.new_category_preview_css"] = "diff-cat-chip" in components_css
    assert out["frontend.new_category_preview_css"], "diff-cat-chip"
    out["frontend.mock_nested_preview"] = "AI Art / Characters / Portraits" in bridge_js
    assert out["frontend.mock_nested_preview"], "AI Art / Characters / Portraits"
    out["frontend.version_fallbacks"] = (
        f'version:"{__version__}-preview"' in bridge_js
        and f'PR.state.version || "{__version__}"' in settings_js
    )
    assert out["frontend.version_fallbacks"], __version__
    out["frontend.mock_clipboard_import"] = "get_clipboard_text" in bridge_js and "AI Art > Characters > Portraits" in bridge_js
    assert out["frontend.mock_clipboard_import"], "get_clipboard_text"
    out["frontend.mock_save_outline"] = "save_outline_file" in bridge_js and "prompts-outline.txt" in bridge_js
    assert out["frontend.mock_save_outline"], "save_outline_file"
    out["frontend.data_folder_button"] = (
        "Local data folder" in settings_js
        and "openDataFolder" in settings_js
        and "open_data_folder" in bridge_js
        and "def open_data_folder" in (Path(__file__).resolve().parents[1] / "promptoire_app" / "api.py").read_text(encoding="utf-8")
    )
    assert out["frontend.data_folder_button"], "open_data_folder"
    out["frontend.mock_outline_prompt_setting"] = "outline_prompt" in bridge_js
    assert out["frontend.mock_outline_prompt_setting"], "outline_prompt"
    out["frontend.empty_import_shortcut"] = (
        "Import prompts" in launcher_js
        and 'PR.app.showView("bulk")' in launcher_js
        and "empty-actions" in components_css
    )
    assert out["frontend.empty_import_shortcut"], "empty import shortcut"
    out["frontend.category_rail_jump"] = (
        "jumpToCategory" in launcher_js
        and 'dataset: { id: cat.id }' in launcher_js
        and "const next = PR.state.catFilter === id ? null : id;" in launcher_js
        and "PR.state.catFilter = next;" in launcher_js
        and 'searchEl.value = "";' in launcher_js
        and '"aria-pressed": String(PR.state.catFilter === c.id)' in launcher_js
        and "RAIL_DRAG_THRESHOLD = 10" in launcher_js
    )
    assert out["frontend.category_rail_jump"], "category rail should navigate to the selected group"
    prompt_editor_contract = {
        "title_and_category_one_row": "prompt-editor-top" in editor_js and ".prompt-editor-top" in components_css,
        "expanded_prompt_and_note": all(token in editor_js for token in ("prompt-editor-prompt", "prompt-editor-note", "prompt-editor-tags")),
        "no_type_selector": 'label", { text: "Type"' not in editor_js and "segBtn(" not in editor_js,
        "no_image_details": "Optional image details" not in editor_js and ".image-details" not in components_css,
        "preserves_legacy_fields": all(token not in editor_js for token in ("negative: neg.value", "model: model.value", "params: params.value")),
        "new_type_from_category": "suggestedPromptType" in editor_js and "findCategoryPath" in editor_js and "countPromptTypes" in editor_js,
    }
    out["frontend.compact_prompt_editor"] = prompt_editor_contract
    assert all(prompt_editor_contract.values()), prompt_editor_contract
    out["frontend.support_button_compact"] = (
        'id="btnCoffee"' in (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "index.html").read_text(encoding="utf-8")
        and "Buy Me a Coffee" not in settings_js
        and "coffeeLinkField" not in settings_js
        and 'class: "coffee"' not in settings_js
    )
    assert out["frontend.support_button_compact"], "topbar-only support button"
    out["frontend.pin_is_single_autohide_control"] = (
        "Copy then vanish" not in settings_js
        and 'PR.bridge.call("copy_prompt", id, text, PR.state.pinned)' in launcher_js
        and "Pinned — auto-hide disabled" in app_js
        and "keep_open: bool = False" in (
            Path(__file__).resolve().parents[1] / "promptoire_app" / "api.py"
        ).read_text(encoding="utf-8")
    )
    assert out["frontend.pin_is_single_autohide_control"], "top pin should override every auto-hide path"
    launcher_html = (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "index.html").read_text(encoding="utf-8")
    launcher_layout = {
        "no_footer": "actionbar" not in launcher_html and "btnImprove2" not in launcher_html,
        "new_in_filters": launcher_html.index('id="btnAdd"') < launcher_html.index('id="btnDensity"'),
        "edit_library": "Edit&nbsp;Library" in launcher_html and 'title="Edit library"' in launcher_html,
        "gear_settings": "M19.4 15" in launcher_html,
    }
    out["frontend.launcher_layout"] = launcher_layout
    assert all(launcher_layout.values()), launcher_layout
    out["frontend.github_source_link"] = (
        "source-link" in settings_js
        and "configuredRepoUrl" in settings_js
        and "Open Promptoire on GitHub" in settings_js
        and "source-link" in components_css
    )
    assert out["frontend.github_source_link"], "source-link"
    out["frontend.about_creator_credit"] = (
        "Brought to you by Stoned Ape" in settings_js
        and ".about .creator-credit" in components_css
    )
    assert out["frontend.about_creator_credit"], "About should credit Stoned Ape"
    out["frontend.editor_toolbar_opaque"] = (
        ".editor-toolbar {" in components_css
        and "background: var(--bg);" in components_css
        and "position: sticky; top: 0; z-index: 2;" in components_css
    )
    assert out["frontend.editor_toolbar_opaque"], "Edit Library filter must be opaque while sticky"
    out["frontend.single_tree_toggle"] = (
        "tree-toggle" in editor_js
        and "allCategoriesCollapsed" in editor_js
        and 'title: "Expand all"' not in editor_js
        and 'title: "Collapse all"' not in editor_js
        and ".tree-toggle:hover" in components_css
    )
    assert out["frontend.single_tree_toggle"], "Edit Library should use one stateful expand/collapse button"
    appearance_contract = {
        "background_presets": "backgroundPicker" in settings_js and "applyBackground" in app_js and 'data-background="mist"' in base_css,
        "font_picker": "fontPicker" in settings_js and "applyFont" in app_js and 'data-font="rounded"' in base_css,
        "category_header_color": (
            "Category color" in editor_js
            and "--cat-accent" in components_css
            and ".cat-group:has(> .cat-header:hover)" in components_css
            and "linear-gradient(90deg" not in components_css
        ),
    }
    out["frontend.appearance_customization"] = appearance_contract
    assert all(appearance_contract.values()), appearance_contract
    out["frontend.generic_coffee_guard"] = (
        "isGenericCoffeeUrl" in app_js
        and "normalizeUrl" in app_js
        and 'host === "buymeacoffee.com"' in app_js
    )
    assert out["frontend.generic_coffee_guard"], "isGenericCoffeeUrl"
    settings_controls = {
        "toggle_click_target": (
            "z-index: 2" in components_css
            and components_css.count("pointer-events: none") >= 2
        ),
        "save_errors_rollback": (
            "async function save(patch)" in settings_js
            and "PR.state.settings = previous" in settings_js
            and "input.checked = !next" in settings_js
        ),
        "modifier_free_safe_keys": "F1–F24" in settings_js and 'key === "`"' in settings_js,
        "capture_stops_global_shortcuts": "e.stopPropagation()" in settings_js,
        "startup_and_tray_rows": "Launch at startup" in settings_js and "Show tray icon" in settings_js,
    }
    out["frontend.settings_controls"] = settings_controls
    assert all(settings_controls.values()), settings_controls
    density_contract = {
        "three_modes": all(mode in app_js and mode in settings_js for mode in ("comfortable", "compact", "titles")),
        "saved_setting": 'update_settings", { density: next }' in app_js and "densityPicker" in settings_js,
        "compact_cards": 'data-density="compact"' in components_css and "-webkit-line-clamp: 1" in components_css,
        "titles_only": 'data-density="titles"' in components_css and ".card-preview" in components_css,
        "toolbar_one_row": (
            ".filters { display: flex; align-items: center;" in base_css
            and "flex-wrap: nowrap" in base_css
            and "@media (max-width: 420px)" in base_css
        ),
        "rail_pointer_drag": all(token in launcher_js for token in ("setPointerCapture", "is-dragging", "startScroll", "suppressRailClick")),
        "rail_wheel_scroll": 'addEventListener("wheel"' in launcher_js and "scrollLeft += e.deltaY" in launcher_js,
        "resize_handles": "data-resize" in (Path(__file__).resolve().parents[1] / "promptoire_app" / "web" / "index.html").read_text(encoding="utf-8") and "resize-handle" in base_css,
        "resize_bridge": "begin_window_resize" in bridge_js and "begin_window_resize" in app_js,
    }
    out["frontend.compact_resize_contract"] = density_contract
    assert all(density_contract.values()), density_contract
    out["frontend.import_actions_two_rows"] = (
        'class: "btn-row import-actions"' in bulk_js
        and "grid-template-columns: repeat(6" in components_css
        and ".import-actions > .btn:nth-child(5) { grid-column: span 4; }" in components_css
        and "Negative prompt:" not in bulk_js
        and "Parameters:" not in bulk_js
    )
    assert out["frontend.import_actions_two_rows"], "compact two-row canonical import actions"
    out["settings.outline_prompt_default"] = all(
        token in SETTINGS_DEFAULTS["bulk_improve"]["outline_prompt"]
        for token in ("STRICT OUTPUT CONTRACT", "first nonblank line must be Path:", "copyable model flag")
    )
    assert out["settings.outline_prompt_default"], SETTINGS_DEFAULTS["bulk_improve"]
    out["settings.default_repo_link"] = SETTINGS_DEFAULTS["links"]["repo"] == "https://github.com/diddlysquatt/Promptoire"
    assert out["settings.default_repo_link"], SETTINGS_DEFAULTS["links"]
    out["settings.default_coffee_link"] = (
        SETTINGS_DEFAULTS["links"]["coffee"] == "https://buymeacoffee.com/promptoire"
        and 'coffee:"https://buymeacoffee.com/promptoire"' in bridge_js
    )
    assert out["settings.default_coffee_link"], SETTINGS_DEFAULTS["links"]
    sanitized_cases = []
    for coffee_url in ("https://www.buymeacoffee.com/", "https://buymeacoffee.com"):
        with tempfile.TemporaryDirectory() as settings_dir:
            saved_settings = Path(settings_dir) / "promptoire.config.json"
            saved_settings.write_text(json.dumps({
                "links": {
                    "coffee": coffee_url,
                    "repo": "https://github.com/",
                }
            }), encoding="utf-8")
            loaded_settings = Settings(saved_settings).load()
            sanitized_cases.append(
                loaded_settings.get("links", "coffee") == ""
                and loaded_settings.get("links", "repo") == ""
            )
    out["settings.sanitized_placeholder_links"] = all(sanitized_cases)
    assert out["settings.sanitized_placeholder_links"], sanitized_cases
    with tempfile.TemporaryDirectory() as settings_dir:
        saved_settings = Path(settings_dir) / "promptoire.config.json"
        saved_settings.write_text(json.dumps({
            "links": {
                "coffee": "buymeacoffee.com/promptoire",
                "repo": "github.com/diddlysquatt/Promptoire",
            }
        }), encoding="utf-8")
        loaded_settings = Settings(saved_settings).load()
        out["settings.support_links_normalized"] = (
            loaded_settings.get("links", "coffee") == "https://buymeacoffee.com/promptoire"
            and loaded_settings.get("links", "repo") == "https://github.com/diddlysquatt/Promptoire"
        )
    assert out["settings.support_links_normalized"], loaded_settings.data.get("links")
    with tempfile.TemporaryDirectory() as settings_dir:
        runtime_settings = Settings(Path(settings_dir) / "promptoire.config.json").load()
        runtime_settings.update({
            "links": {
                "coffee": "buymeacoffee.com/promptoire",
                "repo": "https://github.com/",
            }
        })
        out["settings.update_sanitizes_links"] = (
            runtime_settings.get("links", "coffee") == "https://buymeacoffee.com/promptoire"
            and runtime_settings.get("links", "repo") == ""
        )
    assert out["settings.update_sanitizes_links"], runtime_settings.data.get("links")

    root = Path(__file__).resolve().parents[1]
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    privacy_text = (root / "docs" / "PRIVACY.md").read_text(encoding="utf-8")
    security_text = (root / "SECURITY.md").read_text(encoding="utf-8")
    changelog_text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    contributing_text = (root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    gitignore_text = (root / ".gitignore").read_text(encoding="utf-8")
    bug_template = (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
    feature_template = (root / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml").read_text(encoding="utf-8")
    issue_config = (root / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
    pr_template = (root / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    pages_workflow = (root / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    site_html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    site_css = (root / "docs" / "styles.css").read_text(encoding="utf-8")
    site_privacy = (root / "docs" / "privacy.html").read_text(encoding="utf-8")
    site_smartscreen = (root / "docs" / "smartscreen.html").read_text(encoding="utf-8")
    smartscreen_text = (root / "docs" / "SMARTSCREEN.md").read_text(encoding="utf-8")
    launch_checklist = (root / "docs" / "LAUNCH_CHECKLIST.md").read_text(encoding="utf-8")
    release_checklist = (root / "docs" / "GITHUB_RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    launcher_bat = (root / "Promptoire.bat").read_text(encoding="utf-8")
    setup_bat = (root / "setup.bat").read_text(encoding="utf-8")
    release_bat = (root / "check-release.bat").read_text(encoding="utf-8")
    spec_text = (root / "Promptoire.spec").read_text(encoding="utf-8")
    version_info_text = (root / "version_info.txt").read_text(encoding="utf-8")
    publish_check_script = (root / "Check-GitHubPublish.ps1").read_text(encoding="utf-8")
    shortcut_script = (root / "Create-PromptoireShortcut.ps1").read_text(encoding="utf-8")
    shortcut_check_script = (root / "Check-PromptoireShortcut.ps1").read_text(encoding="utf-8")
    rename_script = (root / "Rename-PromptoireFolder.ps1").read_text(encoding="utf-8")
    release_tokens = {
        "readme_privacy_link": "[Privacy](docs/PRIVACY.md)" in readme_text,
        "readme_security_link": "[Security](SECURITY.md)" in readme_text,
        "readme_contributing_link": "[Contributing](CONTRIBUTING.md)" in readme_text,
        "readme_changelog_link": "[Changelog](CHANGELOG.md)" in readme_text,
        "readme_outline_first": "Export your *entire* library as a simple outline" in readme_text,
        "readme_pages_site": "https://diddlysquatt.github.io/Promptoire/" in readme_text,
        "readme_smartscreen_guide": "docs/SMARTSCREEN.md" in readme_text,
        "changelog_current_version": f"## {__version__} -" in changelog_text and "Outline-first bulk workflow" in changelog_text,
        "contributing_local_first": "local-first" in contributing_text.lower(),
        "contributing_private_data": "prompts.json" in contributing_text and "promptoire.config.json" in contributing_text,
        "contributing_release_check": "check-release.bat" in contributing_text,
        "contributing_publish_check": "Check-GitHubPublish.ps1" in contributing_text,
        "privacy_local_first": "local-first" in privacy_text.lower(),
        "privacy_optional_ai": "Improve with AI now" in privacy_text,
        "privacy_saved_outline_instructions": "visible outline improvement instructions" in privacy_text,
        "privacy_outline_clipboard": "Copy instructions + library" in privacy_text,
        "privacy_paste_clipboard": "Paste from clipboard" in privacy_text,
        "security_sensitive_files": "prompts.json" in security_text and "promptoire.config.json" in security_text,
        "gitignore_private_prompt": "prompts.json" in gitignore_text,
        "gitignore_private_config": "promptoire.config.json" in gitignore_text,
        "bug_template_privacy": "prompts.json" in bug_template and "API keys" in bug_template,
        "feature_template_simple": "simple" in feature_template.lower() and "local-first" in feature_template,
        "issue_blank_disabled": "blank_issues_enabled: false" in issue_config,
        "pr_template_private_data": (
            "check-release.bat" in pr_template
            and "prompts.json" in pr_template
            and "promptoire.config.json" in pr_template
        ),
        "release_selftest": (
            "--selftest" in release_checklist
            and '"mock": false' in release_checklist
            and '"native_hwnd": true' in release_checklist
            and '"window_icon": true' in release_checklist
            and '"window_icon_applied": true' in release_checklist
            and '"minimum_window": [360, 420]' in release_checklist
        ),
        "release_changelog_check": "CHANGELOG.md" in release_checklist,
        "release_ci_scope": "portable subset" in release_checklist and "local gate is" in release_checklist,
        "release_batch_documented": "check-release.bat" in readme_text and "check-release.bat" in release_checklist,
        "release_batch_private_guard": "git ls-files --error-unmatch" in release_bat and "prompts.json" in release_bat,
        "release_batch_selftest_guard": (
            "--selftest" in release_bat and "mock" in release_bat
            and "native_hwnd" in release_bat and "window_icon" in release_bat
            and "window_icon_applied" in release_bat
        ),
        "release_batch_native_tray_guard": (
            "tests\\test_native_tray.py" in release_bat
            and "minimize-to-tray" in release_checklist
            and (root / "tests" / "test_native_tray.py").exists()
        ),
        "release_batch_fresh_selftest": 'del /q "_selftest.json"' in release_bat,
        "packaged_version_metadata": (
            "version='version_info.txt'" in spec_text
            and f"StringStruct('FileVersion', '{__version__}')" in version_info_text
            and f"StringStruct('ProductVersion', '{__version__}')" in version_info_text
        ),
        "lightweight_image_plugins": (
            "PIL.AvifImagePlugin" in spec_text and "PIL.WebPImagePlugin" in spec_text
        ),
        "native_window_icon": (
            "set_window_icon" in (root / "promptoire_app" / "main.py").read_text(encoding="utf-8")
            and "def set_window_icon" in (root / "promptoire_app" / "platform" / "window_fx.py").read_text(encoding="utf-8")
            and "promptoire.ico" in spec_text
            and (root / "icons" / "promptoire.ico").exists()
            and (root / "promptoire_app" / "web" / "assets" / "tray.png").exists()
        ),
        "full_python_compile": "compileall -q promptoire_app tests" in release_checklist and "compileall -q promptoire_app tests" in ci_workflow,
        "all_frontend_js_checked": (
            all(f"node --check promptoire_app/web/js/{name}" in release_checklist for name in (
                "bridge.js", "state.js", "components.js", "launcher.js", "editor.js", "bulk.js", "settings.js", "app.js"
            ))
            and all(name in release_bat and name in ci_workflow for name in (
                "bridge.js", "state.js", "components.js", "launcher.js", "editor.js", "bulk.js", "settings.js", "app.js"
            ))
        ),
        "workflow_scope_note": "gh auth refresh --scopes workflow" in release_checklist,
        "pages_site_complete": all(token in site_html for token in (
            "promptoire-launcher.png", "promptoire-improve-library.png",
            "promptoire-settings.png", "privacy.html", "smartscreen.html",
            "buymeacoffee.com/promptoire",
        )) and "@media(max-width:660px)" in site_css,
        "readme_editor_screenshot": (
            "promptoire-edit-library.png" in readme_text
            and (root / "docs" / "assets" / "promptoire-edit-library.png").exists()
        ),
        "creator_credit_documented": (
            "Brought to you by Stoned Ape" in readme_text
            and "Brought to you by Stoned Ape" in site_html
        ),
        "pages_docs_complete": (
            "No hidden collection" in site_privacy
            and "The realistic paths" in site_smartscreen
            and "Microsoft Artifact Signing" in smartscreen_text
            and "SignPath Foundation" in smartscreen_text
        ),
        "pages_manual_deploy": (
            "workflow_dispatch:" in pages_workflow
            and "push:" not in pages_workflow
            and "actions/configure-pages@v5" in pages_workflow
            and "actions/upload-pages-artifact@v4" in pages_workflow
            and "actions/deploy-pages@v4" in pages_workflow
            and "Publish documentation site" in launch_checklist
        ),
        "generic_support_release_check": "blank/generic root links" in release_checklist,
        "github_source_release_check": "GitHub source link" in release_checklist,
        "data_folder_release_check": "local data folder" in release_checklist and "prompts.json" in release_checklist,
        "publish_check_documented": (
            "Check-GitHubPublish.ps1" in readme_text
            and "Check-GitHubPublish.ps1" in release_checklist
            and "workflow" in publish_check_script
            and "git remote" in publish_check_script
            and "check-release.bat" in publish_check_script
            and "Buy Me a Coffee support link" in publish_check_script
            and "Project folder display name" in publish_check_script
            and "Normalize-OptionalUrl" in publish_check_script
            and "Next steps:" in publish_check_script
            and "gh auth refresh -h github.com -s workflow" in publish_check_script
            and "[WARN]" in publish_check_script
            and "Private runtime paths occur in reachable git history" in publish_check_script
            and '"log",' in publish_check_script
            and '"--all",' in publish_check_script
        ),
        "launcher_passes_args": "-m promptoire_app %*" in launcher_bat,
        "outline_file_dialogs": "*.txt;*.md;*.csv" in (root / "promptoire_app" / "api.py").read_text(encoding="utf-8"),
        "shortcut_setup": (
            "Create-PromptoireShortcut.ps1" in setup_bat
            and "PROMPTOIRE.lnk" in shortcut_script
            and "icons\\promptoire.ico" in shortcut_script
        ),
        "shortcut_check_script": (
            "Check-PromptoireShortcut.ps1" in release_bat
            and "PROMPTOIRE.lnk" in shortcut_check_script
            and "Promptoire.bat" in shortcut_check_script
        ),
        "shortcut_release_check": "PROMPTOIRE` desktop shortcut" in release_checklist,
        "shortcut_release_verifier": "Check-PromptoireShortcut.ps1" in release_checklist,
        "folder_rename_helper": (
            "Rename-PromptoireFolder.ps1" in readme_text
            and "Rename-PromptoireFolder.ps1" in release_checklist
            and "PROMPTOIRE.__case_rename_tmp__" in rename_script
            and "Create-PromptoireShortcut.ps1" in rename_script
        ),
        "outline_library_release_check": (
            "Copy instructions + library" in release_checklist
            and "Copy library only" in release_checklist
            and "Copy instructions only" in release_checklist
            and "optional topic/workflow" in release_checklist
            and "Save library outline" in release_checklist
            and "More options" in release_checklist
        ),
        "outline_instruction_release_check": (
            "Save instructions" in release_checklist
            and "Improve with AI now" in release_checklist
        ),
        "openai_panel_release_check": (
            "OpenAI connection" in release_checklist
            and "bottom of Improve Library" in release_checklist
            and "GPT-5.6" in release_checklist
        ),
        "compact_launcher_release_check": (
            "no bottom action footer" in release_checklist
            and "360×420" in release_checklist
            and "Edit Library" in release_checklist
        ),
        "instruction_reset_release_check": "Reset default" in release_checklist,
        "clipboard_paste_release_check": "Paste from clipboard" in release_checklist,
        "manual_paste_release_check": "manual paste" in release_checklist.lower() and "auto-preview" in release_checklist.lower(),
        "clear_import_release_check": "Clear" in release_checklist and "import box" in release_checklist,
        "outline_file_release_check": ".txt" in release_checklist and ".md" in release_checklist and ".csv" in release_checklist,
        "nested_bullet_release_check": "nested bullet outlines" in release_checklist,
        "markdown_heading_release_check": "Markdown prompt headings" in release_checklist,
        "yamlish_release_check": "YAML-style" in release_checklist and "- Title:" in release_checklist,
        "markdown_table_release_check": "Markdown tables" in release_checklist,
        "csv_table_release_check": "CSV tables" in release_checklist,
        "json_alias_release_check": "sections/subsections/items" in release_checklist,
        "json_flat_path_release_check": "flat JSON prompt rows" in release_checklist,
        "json_image_alias_release_check": "negative_prompt" in release_checklist and "image_model" in release_checklist,
        "json_string_prompt_release_check": "plain JSON string prompts" in release_checklist,
        "incoming_preview_release_check": (
            "incoming/new/updated/unchanged counts" in release_checklist
            and "repeated/ambiguous skips" in release_checklist
        ),
        "selected_changes_release_check": "no selected changes" in release_checklist.lower(),
        "safe_merge_release_check": (
            "never moves/deletes prompts" in release_checklist
            and "never clears a nonblank local field" in release_checklist
            and "preview/apply report the same result" in release_checklist
        ),
    }
    out["release.docs_ready"] = release_tokens
    assert all(release_tokens.values()), release_tokens

    # copy_export (clipboard may be unavailable in headless; just check shape)
    ce = api.copy_export(True, False)
    out["copy_export.ok"] = ce.get("ok")
    coe = api.copy_outline_export(True)
    out["copy_outline_export.ok"] = coe.get("ok")
    defaults = api.bulk_prompt_defaults()
    out["bulk_prompt_defaults.ok"] = defaults.get("ok") and "STRICT OUTPUT CONTRACT" in defaults.get("outline_prompt", "")
    assert out["bulk_prompt_defaults.ok"], defaults
    sof = api.save_outline_file()
    out["save_outline_file.shape"] = "ok" in sof and (sof.get("ok") is False or sof.get("cancelled") or "path" in sof)
    assert out["save_outline_file.shape"], sof
    clip = api.get_clipboard_text()
    out["get_clipboard_text.shape"] = "ok" in clip and (clip.get("ok") is False or "text" in clip)
    assert out["get_clipboard_text.shape"], clip
    backups_before = set((Path(os.environ["PROMPTOIRE_DATA_DIR"]) / "backups").glob("prompts-*.json"))
    backup_result = api.backup_now()
    backups_after = set((Path(os.environ["PROMPTOIRE_DATA_DIR"]) / "backups").glob("prompts-*.json"))
    out["backup_now.created"] = backup_result.get("ok") is True and bool(backups_after - backups_before)
    assert out["backup_now.created"], backup_result
    if hasattr(os, "startfile"):
        original_startfile = os.startfile
        opened_folders = []
        os.startfile = lambda value: opened_folders.append(str(value))
        try:
            open_folder_result = api.open_data_folder()
        finally:
            os.startfile = original_startfile
        expected_data_folder = str(Path(os.environ["PROMPTOIRE_DATA_DIR"]))
        out["open_data_folder.target"] = (
            open_folder_result.get("ok") is True
            and open_folder_result.get("path") == expected_data_folder
            and opened_folders == [expected_data_folder]
        )
        assert out["open_data_folder.target"], (open_folder_result, opened_folders)

    # add/update/delete cycle (against a temp clone — we won't save)
    add = api.add_prompt(st["categories"][0]["id"], {"title": "ZZ smoke", "prompt": "hello {name}", "tags": ["smoke"]})
    out["add.ok"] = add["ok"]
    pid = add["prompt"]["id"]
    upd = api.update_prompt(pid, {"title": "ZZ smoke 2"})
    out["update.ok"] = upd["ok"]
    target_id = st["categories"][1]["id"]
    moved = api.move_prompt(pid, target_id, 0)
    moved_prompt, moved_cat, _ = app.library.find_prompt(pid)
    out["move_prompt.ok"] = (
        moved.get("ok") is True
        and moved_prompt is not None
        and moved_cat is not None
        and moved_cat.get("id") == target_id
        and moved_cat.get("prompts", [])[0].get("id") == pid
    )
    assert out["move_prompt.ok"], moved
    refused = api.move_prompt(pid, "cat_missing", None)
    still_there, still_cat, _ = app.library.find_prompt(pid)
    out["move_prompt.invalid_is_safe"] = (
        refused.get("ok") is False
        and still_there is not None
        and still_cat is not None
        and still_cat.get("id") == target_id
    )
    assert out["move_prompt.invalid_is_safe"], refused
    destination_prompts = moved_cat.get("prompts", [])
    reordered = api.reorder_prompt(target_id, 0, len(destination_prompts) - 1)
    out["reorder_prompt.ok"] = (
        reordered.get("ok") is True and destination_prompts[-1].get("id") == pid
    )
    assert out["reorder_prompt.ok"], reordered
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
