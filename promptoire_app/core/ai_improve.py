"""Optional one-click library improvement through the official OpenAI API.

The feature intentionally supports one provider and a short, current model
list. It uses stdlib HTTP to keep Promptoire lightweight; manual copy/paste
continues to work without an OpenAI account or API key.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_MODEL = "gpt-5.6"


def improve(ai: dict, payload: str, *, timeout: int = 180) -> dict:
    """Send instructions plus an outline library to OpenAI."""
    ai = ai or {}
    api_key = str(ai.get("api_key") or "").strip()
    if not api_key:
        return {
            "ok": False,
            "error": "No OpenAI API key set. Add one at the bottom of Improve Library.",
        }

    model = str(ai.get("model") or "").strip() or DEFAULT_OPENAI_MODEL
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": payload}],
        "max_completion_tokens": 32000,
    }).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(
                str(part.get("text") or "") for part in content if isinstance(part, dict)
            )
        text = str(content or "")
        if not text.strip():
            return {"ok": False, "error": "OpenAI returned no text."}
        return {"ok": True, "text": text, "model": model}
    except urllib.error.HTTPError as error:
        detail = ""
        try:
            parsed = json.loads(error.read().decode("utf-8"))
            detail = str((parsed.get("error") or {}).get("message") or "")[:300]
        except Exception:
            pass
        suffix = f": {detail}" if detail else ""
        return {"ok": False, "error": f"OpenAI request failed ({error.code}){suffix}"}
    except urllib.error.URLError as error:
        return {"ok": False, "error": f"Could not reach OpenAI: {error.reason}"}
    except Exception as error:
        return {"ok": False, "error": f"OpenAI request failed: {error}"}
