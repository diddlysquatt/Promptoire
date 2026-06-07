"""Optional one-click "improve my library" via a direct LLM API call.

Two providers:
  - "anthropic": uses the official `anthropic` SDK (lazy/optional dependency).
  - "openai":    OpenAI-compatible /chat/completions over stdlib HTTP — works
                 with OpenAI, OpenRouter, local servers, etc. via a base_url.

The whole feature is optional: if no API key is configured the UI hides it,
and the manual copy/paste loop always works without any of this.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-8"
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o"


def improve(ai: dict, payload: str, *, timeout: int = 180) -> dict:
    """Send `payload` (meta-prompt + library JSON) to the configured provider
    and return {ok, text} with the model's reply (expected to be improved JSON)."""
    ai = ai or {}
    provider = (ai.get("provider") or "anthropic").lower()
    api_key = (ai.get("api_key") or "").strip()
    if not api_key:
        return {"ok": False, "error": "No API key set. Add one in Settings → AI."}

    try:
        if provider == "anthropic":
            return _anthropic(ai, api_key, payload, timeout)
        return _openai(ai, api_key, payload, timeout)
    except Exception as e:  # never let the bridge see a raw traceback
        return {"ok": False, "error": str(e)}


def _anthropic(ai: dict, api_key: str, payload: str, timeout: int) -> dict:
    try:
        import anthropic  # type: ignore
    except Exception:
        return {"ok": False, "error": "The 'anthropic' package isn't installed. "
                "Run:  pip install anthropic   (or use the OpenAI provider / manual copy-paste)."}

    model = (ai.get("model") or "").strip() or DEFAULT_ANTHROPIC_MODEL
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=float(timeout))
        # Stream (the output JSON can be large) and adaptive thinking for quality.
        with client.messages.stream(
            model=model,
            max_tokens=32000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": payload}],
        ) as stream:
            msg = stream.get_final_message()
        text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
        if not text.strip():
            return {"ok": False, "error": "The model returned no text."}
        return {"ok": True, "text": text, "model": model}
    except anthropic.AuthenticationError:
        return {"ok": False, "error": "Anthropic rejected the API key (401)."}
    except anthropic.RateLimitError:
        return {"ok": False, "error": "Rate limited by Anthropic — wait a moment and retry."}
    except anthropic.APIStatusError as e:
        return {"ok": False, "error": f"Anthropic API error {e.status_code}: {getattr(e, 'message', '')}"}
    except Exception as e:
        return {"ok": False, "error": f"Anthropic call failed: {e}"}


def _openai(ai: dict, api_key: str, payload: str, timeout: int) -> dict:
    base = (ai.get("base_url") or "").strip().rstrip("/") or DEFAULT_OPENAI_BASE
    model = (ai.get("model") or "").strip() or DEFAULT_OPENAI_MODEL
    url = base + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": payload}],
        "temperature": 0.7,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        if not text.strip():
            return {"ok": False, "error": "The model returned no text."}
        return {"ok": True, "text": text, "model": model}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8")[:300]
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.code} from {base}: {detail}"}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Could not reach {base}: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error": f"OpenAI-compatible call failed: {e}"}
