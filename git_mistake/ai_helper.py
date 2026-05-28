"""
ai_helper.py - Multi-provider AI fallback for complex git diagnosis.

Supported providers (auto-detected from env vars, tried in order):
  1. Anthropic Claude  →  ANTHROPIC_API_KEY
  2. OpenRouter        →  OPENROUTER_API_KEY
  3. NVIDIA NIM        →  NVIDIA_API_KEY

First key found wins. Set whichever you have.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional


# ── Shared system prompt for all providers ───────────────────────────────────
SYSTEM_PROMPT = """You are an elite Git recovery specialist. You receive a developer's git state
and their description of what went wrong. Your job is to provide exact, safe, step-by-step
recovery commands.

Rules:
- Always suggest creating a backup branch FIRST if there is any risk
- Prefer safe non-destructive commands over fast destructive ones
- Explain WHY each step works, briefly
- If multiple options exist, give the safest one first

Respond ONLY with a valid JSON object — no markdown fences, no preamble:
{
  "diagnosis": "One-line description of what went wrong",
  "severity": "low | medium | high",
  "explanation": "2-3 sentences explaining the root cause clearly",
  "steps": [
    "# Comment explaining what the next command does",
    "exact-git-command --with-flags",
    "",
    "# Another comment",
    "another-git-command"
  ]
}"""

# ── Model defaults per provider ───────────────────────────────────────────────
ANTHROPIC_MODEL  = "claude-sonnet-4-20250514"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"   # free tier, fast
NVIDIA_MODEL     = "meta/llama-3.1-8b-instruct"      # free on NVIDIA NIM


# ── Helpers ───────────────────────────────────────────────────────────────────
def _build_user_message(context: dict, problem: str) -> str:
    return f"""Git State:
- Branch: {context['branch']}
- Status:
{context['status']}
- Reflog (last 25):
{context['reflog']}
- Recent commits:
{context['recent_commits']}
- Stash: {context['stash'] or 'empty'}
- Diff stat:
{context['diff_stat']}
- Merge in progress: {context['merge_in_progress']}
- Rebase in progress: {context['rebase_in_progress']}
- Cherry-pick in progress: {context['cherry_pick_in_progress']}

Developer's problem:
{problem}"""


def _parse_response(raw: str) -> Optional[dict]:
    """Strip markdown fences and parse JSON."""
    raw = raw.strip()
    # Remove ```json ... ``` or ``` ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
        # Validate required keys
        if all(k in parsed for k in ("diagnosis", "severity", "explanation", "steps")):
            return parsed
        return None
    except json.JSONDecodeError:
        return None


def _post(url: str, headers: dict, payload: dict, timeout: int = 20) -> Optional[str]:
    """Generic POST, returns response body string or None."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 401 or "invalid_api_key" in body or "unauthorized" in body.lower():
            print(f"\033[91m  ⚠  API key rejected by {url.split('/')[2]} (401) — skipping.\033[0m")
        elif e.code == 429:
            print(f"\033[93m  ⚠  Rate limit hit on {url.split('/')[2]} — skipping.\033[0m")
        return None
    except urllib.error.URLError:
        return None


# ── Provider 1: Anthropic Claude ─────────────────────────────────────────────
def _try_anthropic(user_message: str) -> Optional[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None

    print("\033[2m  ↳ Trying Anthropic Claude...\033[0m")

    body = _post(
        url="https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        payload={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}],
        }
    )
    if not body:
        return None

    try:
        data = json.loads(body)
        raw = data["content"][0]["text"]
        return _parse_response(raw)
    except (KeyError, IndexError, json.JSONDecodeError):
        return None


# ── Provider 2: OpenRouter ────────────────────────────────────────────────────
def _try_openrouter(user_message: str) -> Optional[dict]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.environ.get("OPENROUTER_MODEL", OPENROUTER_MODEL)
    print(f"\033[2m  ↳ Trying OpenRouter ({model})...\033[0m")

    body = _post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/yourname/git-mistake",
            "X-Title": "git-mistake",
        },
        payload={
            "model": model,
            "max_tokens": 1000,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
        }
    )
    if not body:
        return None

    try:
        data = json.loads(body)
        raw = data["choices"][0]["message"]["content"]
        return _parse_response(raw)
    except (KeyError, IndexError, json.JSONDecodeError):
        return None


# ── Provider 3: NVIDIA NIM ────────────────────────────────────────────────────
def _try_nvidia(user_message: str) -> Optional[dict]:
    api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.environ.get("NVIDIA_MODEL", NVIDIA_MODEL)
    print(f"\033[2m  ↳ Trying NVIDIA NIM ({model})...\033[0m")

    body = _post(
        url="https://integrate.api.nvidia.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        payload={
            "model": model,
            "max_tokens": 1000,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
        }
    )
    if not body:
        return None

    try:
        data = json.loads(body)
        raw = data["choices"][0]["message"]["content"]
        return _parse_response(raw)
    except (KeyError, IndexError, json.JSONDecodeError):
        return None


# ── Public entry point ────────────────────────────────────────────────────────
def call_claude_api(context: dict, problem: str) -> Optional[dict]:
    """
    Try each configured AI provider in order.
    Returns structured diagnosis dict or None if all fail / no keys set.
    """
    # Check if any key is configured at all
    has_any_key = any([
        os.environ.get("ANTHROPIC_API_KEY"),
        os.environ.get("OPENROUTER_API_KEY"),
        os.environ.get("NVIDIA_API_KEY"),
    ])

    if not has_any_key:
        return None

    user_message = _build_user_message(context, problem)

    # Try providers in priority order — first success wins
    for provider_fn in (_try_anthropic, _try_openrouter, _try_nvidia):
        result = provider_fn(user_message)
        if result:
            return result

    return None
