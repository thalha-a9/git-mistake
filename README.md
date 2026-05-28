# 🆘 git-mistake

> **Describe your git disaster in plain English. Get exact fix commands instantly.**

[![CI](https://github.com/thalha-a9/git-mistake/actions/workflows/ci.yml/badge.svg)](https://github.com/thalha-a9/git-mistake/actions)
[![PyPI](https://img.shields.io/pypi/v/git-mistake)](https://pypi.org/project/git-mistake/)
[![Python](https://img.shields.io/pypi/pyversions/git-mistake)](https://pypi.org/project/git-mistake/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[![asciicast](https://asciinema.org/a/XCTuGbvUM32VM0ZX.svg)](https://asciinema.org/a/XCTuGbvUM32VM0ZX)

---

## Why

Git has ~150 commands and error messages designed by a kernel hacker in 2005.
Every developer — from interns to 10-year veterans — eventually types the wrong
thing and freezes. `git-mistake` reads your actual repo state, understands what
went wrong, and tells you **exactly** what to run.

No Stack Overflow rabbit hole. No guessing. Just the fix.

---

## Install

```bash
pip install git-mistake
```

Or run without installing:

```bash
pipx run git-mistake "your problem here"
```

---

## Usage

```bash
# Describe your problem directly
git-mistake "I accidentally ran git reset --hard and lost my commits"
git-mistake "I committed to the wrong branch"
git-mistake "I have a merge conflict and I don't know how to resolve it"
git-mistake "I accidentally pushed my API key to GitHub"
git-mistake "I'm in a detached HEAD state"

# Interactive mode — just run with no arguments
git-mistake

# Pattern matching only — no AI, works fully offline
git-mistake --no-ai "I did git reset --hard"

# Dump your current git state (useful for bug reports)
git-mistake --context
```

---

## How It Works

```
Your repo state              Your problem description
      │                               │
      └──────────────┬────────────────┘
                     ▼
          ┌─────────────────────┐
          │  Pattern Matcher    │  ← Covers ~80% of cases instantly, offline
          └────────┬────────────┘
                   │ No match?
                   ▼
          ┌─────────────────────┐
          │  AI Engine          │  ← Handles complex/unusual situations
          └────────┬────────────┘
                   │
                   ▼
         Exact fix commands + explanation
```

**Stage 1 — Offline pattern matching** reads your `git reflog`, `git status`,
and in-progress operation flags (merge, rebase, cherry-pick) to instantly
resolve common disasters without any API call.

**Stage 2 — AI fallback** kicks in for complex or unusual situations. Supports
3 providers — set whichever key you have.

---

## Covered Scenarios

| Problem | Severity |
|---|---|
| Accidental `git reset --hard` | 🔴 High |
| Pushed secrets / credentials | 🔴 High |
| Detached HEAD state | 🟡 Medium |
| Merge conflict stuck | 🟡 Medium |
| Rebase gone wrong | 🟡 Medium |
| Accidentally deleted tracked files | 🟡 Medium |
| Committed to wrong branch | 🟢 Low |
| Untracked files / .gitignore issues | 🟢 Low |
| Everything else | AI fallback |

---

## AI Setup (Optional)

Works offline for common cases. For complex issues, set **any one** of these:

| Provider | Env Variable | Get Key | Free Tier |
|---|---|---|---|
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | — |
| **OpenRouter** | `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) | ✅ Yes |
| **NVIDIA NIM** | `NVIDIA_API_KEY` | [build.nvidia.com](https://build.nvidia.com) | ✅ Yes |

```bash
# Set whichever you have — only one needed
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENROUTER_API_KEY="sk-or-..."
export NVIDIA_API_KEY="nvapi-..."

# Make it permanent
echo 'export OPENROUTER_API_KEY="sk-or-..."' >> ~/.zshrc

# Override the default model
export OPENROUTER_MODEL="google/gemma-3-27b-it"
export NVIDIA_MODEL="meta/llama-3.3-70b-instruct"
```

> OpenRouter and NVIDIA NIM both have **free tiers** — no credit card needed.

---

## Architecture

```
git-mistake/
├── git_mistake/
│   ├── cli.py        # Entry point, argument parsing, orchestration
│   ├── context.py    # Reads all git state (reflog, status, flags)
│   ├── detector.py   # Fast offline pattern matching (~80% of cases)
│   ├── ai_helper.py  # Multi-provider AI fallback (Anthropic / OpenRouter / NVIDIA)
│   └── display.py    # Terminal colors and formatted output
├── tests/
│   └── test_detector.py   # 18 unit tests
├── .github/workflows/ci.yml
└── pyproject.toml
```

**Design decisions:**
- **Zero dependencies** — stdlib only (`subprocess`, `urllib`, `json`). No requests, no rich, no click.
- **Offline-first** — pattern matching runs before any API call is made.
- **Context-aware** — reads actual `.git/` state, not just your description.
- **Safe by default** — always suggests a backup branch before destructive commands.

---

## Contributing

Bug reports with `git-mistake --context` output are incredibly useful.
PRs adding new patterns to `detector.py` are always welcome.

```bash
git clone https://github.com/thalha-a9/git-mistake
cd git-mistake
pip install -e .
python -m pytest tests/ -v
```

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built for every developer who has typed `git reset` and immediately regretted it.*
