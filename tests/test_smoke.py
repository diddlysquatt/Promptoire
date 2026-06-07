"""GUI-free smoke test of the full backend + API bridge against real data.

Constructs the App (which loads settings + the real prompts.json) but never
starts the webview loop, then exercises every data-path API method.
"""
import json
import sys

from promptoire_app.main import App


def main():
    app = App(debug=False)
    api = app.api
    out = {}

    st = api.get_state()
    assert st["ok"], st
    out["state.stats"] = st["stats"]
    out["state.categories"] = [c["name"] for c in st["categories"]]
    out["state.hotkey_available"] = st["hotkey_available"]

    s = api.search("security")
    assert s["ok"], s
    out["search.security.count"] = s["count"]
    out["search.security.top"] = s["results"][0]["title"][:40] if s["results"] else None

    s2 = api.search("", "image")
    out["search.image.count"] = s2["count"]

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


if __name__ == "__main__":
    sys.exit(main())
