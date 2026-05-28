"""
context.py - Collects all relevant git state for diagnosis
"""

import subprocess
import os


def run_git(*args) -> tuple[str, int]:
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode


def is_git_repo() -> bool:
    _, rc = run_git("rev-parse", "--git-dir")
    return rc == 0


def get_git_context() -> dict:
    ctx = {}

    # Gather git dir ONCE — reused for both branch detection and flag checks
    git_dir, _ = run_git("rev-parse", "--git-dir")
    git_dir = git_dir.strip()

    ctx["status"], _        = run_git("status", "--porcelain", "-b")
    ctx["reflog"], _        = run_git("reflog", "--oneline", "-25")
    ctx["branch"], _        = run_git("branch", "--show-current")
    ctx["recent_commits"], _ = run_git("log", "--oneline", "-10")
    ctx["stash"], _         = run_git("stash", "list")
    ctx["remotes"], _       = run_git("remote", "-v")
    ctx["diff_stat"], _     = run_git("diff", "--stat")

    if not ctx["branch"]:
        ctx["branch"] = "DETACHED_HEAD"

    # Detect in-progress operations via .git directory sentinel files
    ctx["merge_in_progress"]       = os.path.exists(os.path.join(git_dir, "MERGE_HEAD"))
    ctx["rebase_in_progress"]      = (
        os.path.exists(os.path.join(git_dir, "rebase-merge")) or
        os.path.exists(os.path.join(git_dir, "rebase-apply"))
    )
    ctx["cherry_pick_in_progress"] = os.path.exists(os.path.join(git_dir, "CHERRY_PICK_HEAD"))
    ctx["bisect_in_progress"]      = os.path.exists(os.path.join(git_dir, "BISECT_LOG"))

    return ctx
