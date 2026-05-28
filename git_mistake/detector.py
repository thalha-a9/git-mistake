"""
detector.py - Fast, offline pattern matching for the most common git disasters.
Covers ~80% of real-world cases without needing AI.
"""

from typing import Optional


def diagnose_locally(ctx: dict, problem: str) -> Optional[dict]:
    p = problem.lower()

    # ─── DETACHED HEAD ───────────────────────────────────────────────
    if ctx["branch"] == "DETACHED_HEAD" or "detached" in p:
        return {
            "diagnosis": "Detached HEAD state",
            "severity": "medium",
            "explanation": (
                "You checked out a specific commit hash instead of a branch. "
                "Any new commits you make here are 'floating' and will be lost "
                "unless you attach them to a branch."
            ),
            "steps": [
                "# Option A — Return to your previous branch (no changes kept)",
                "git checkout -",
                "",
                "# Option B — Save your work by creating a new branch here",
                "git checkout -b my-recovery-branch",
                "",
                "# Option C — Find the branch you came from in the reflog",
                "git reflog",
                "git checkout <branch-name>",
            ]
        }

    # ─── ACCIDENTAL HARD RESET ───────────────────────────────────────
    if ("reset" in p and "hard" in p) or ("lost" in p and "commit" in p):
        reflog_lines = ctx.get("reflog", "").split("\n")
        recovery_hint = ""
        for line in reflog_lines:
            if "reset" in line.lower():
                idx = reflog_lines.index(line)
                if idx + 1 < len(reflog_lines):
                    recovery_hint = reflog_lines[idx + 1].split()[0]
                break

        return {
            "diagnosis": "Accidental git reset --hard",
            "severity": "high",
            "explanation": (
                "Your commits are almost certainly still in git's reflog. "
                "Git keeps a hidden log of every HEAD movement for ~90 days. "
                f"{'Likely recovery hash: ' + recovery_hint if recovery_hint else 'Check reflog for the hash before the reset.'}"
            ),
            "steps": [
                "# Step 1 — View the reflog and find the commit BEFORE your reset",
                "git reflog",
                "",
                f"# Step 2 — Recover (replace {recovery_hint or '<hash>'} with the correct hash)",
                f"git reset --hard {recovery_hint or '<hash-before-reset>'}",
                "",
                "# OR: Recover safely into a new branch first",
                f"git checkout -b recovered-work {recovery_hint or '<hash-before-reset>'}",
            ]
        }

    # ─── MERGE CONFLICT ──────────────────────────────────────────────
    if ctx.get("merge_in_progress") or ("conflict" in p or ("merge" in p and "fail" in p)):
        return {
            "diagnosis": "Merge conflict",
            "severity": "medium",
            "explanation": (
                "Git found lines that differ between branches and can't decide "
                "which version to keep. You need to manually choose and then "
                "mark each file as resolved."
            ),
            "steps": [
                "# Step 1 — See every conflicted file",
                "git diff --name-only --diff-filter=U",
                "",
                "# Step 2 — Open each file; resolve the <<<<<<< / ======= / >>>>>>> markers",
                "",
                "# Step 3 — Mark resolved files as done",
                "git add <resolved-file>",
                "",
                "# Step 4 — Finish the merge",
                "git merge --continue",
                "",
                "# OR — Bail out completely and return to pre-merge state",
                "git merge --abort",
            ]
        }

    # ─── REBASE HELL ─────────────────────────────────────────────────
    if ctx.get("rebase_in_progress") or "rebase" in p:
        return {
            "diagnosis": "Rebase in progress or gone wrong",
            "severity": "medium",
            "explanation": (
                "A rebase replays your commits one by one onto the target branch. "
                "If a conflict occurred mid-rebase, git paused and is waiting for you. "
                "You can resolve and continue, skip the problematic commit, or abort entirely."
            ),
            "steps": [
                "# Option A — Resolve conflict then continue",
                "git add <resolved-file>",
                "git rebase --continue",
                "",
                "# Option B — Skip the conflicting commit entirely",
                "git rebase --skip",
                "",
                "# Option C — Abort and restore your branch to exactly how it was",
                "git rebase --abort",
            ]
        }

    # ─── COMMITTED TO WRONG BRANCH ───────────────────────────────────
    if "wrong branch" in p or ("commit" in p and "wrong" in p):
        return {
            "diagnosis": "Committed to the wrong branch",
            "severity": "low",
            "explanation": (
                "Your commits are on the wrong branch but they're safe. "
                "We'll carry them over to the correct branch using cherry-pick "
                "and then clean up the wrong branch."
            ),
            "steps": [
                "# Step 1 — Note the commit hashes you need to move",
                "git log --oneline -5",
                "",
                "# Step 2 — Switch to the correct branch",
                "git checkout correct-branch-name",
                "",
                "# Step 3 — Cherry-pick your commit(s) onto the correct branch",
                "git cherry-pick <commit-hash>",
                "",
                "# Step 4 — Go back and remove the commits from the wrong branch",
                "git checkout wrong-branch-name",
                "git reset --hard HEAD~1   # Replace 1 with number of commits to remove",
            ]
        }

    # ─── ACCIDENTALLY DELETED FILES ──────────────────────────────────
    if ("deleted" in p or "removed" in p or "rm " in p) and ("file" in p or "folder" in p or "recover" in p):
        return {
            "diagnosis": "Accidentally deleted tracked files",
            "severity": "medium",
            "explanation": (
                "If git was tracking the files before deletion, they can be fully "
                "restored from HEAD or from any earlier commit."
            ),
            "steps": [
                "# Restore a specific file from HEAD",
                "git checkout HEAD -- path/to/your/file",
                "",
                "# Restore ALL deleted tracked files at once",
                "git checkout HEAD -- .",
                "",
                "# If the deletion was committed — find the last commit that had the file",
                "git log --diff-filter=D --summary -- path/to/file",
                "git checkout <commit-before-deletion>^ -- path/to/file",
            ]
        }

    # ─── PUSHED SECRET / CREDENTIAL ──────────────────────────────────
    if "secret" in p or "password" in p or "api key" in p or "credential" in p or "token" in p:
        return {
            "diagnosis": "Sensitive data accidentally pushed",
            "severity": "high",
            "explanation": (
                "IMPORTANT: Assume the secret is compromised — rotate it immediately "
                "regardless of how quickly you remove it from history. "
                "Even a 1-second push can be scraped by bots."
            ),
            "steps": [
                "# IMMEDIATE ACTION — Revoke/rotate the exposed secret NOW",
                "# (Do this before anything else — history cleanup is secondary)",
                "",
                "# Step 1 — Remove the secret from the latest commit (if not yet pushed)",
                "git reset HEAD~1",
                "# Edit the file, remove the secret, then recommit",
                "",
                "# Step 2 — If already pushed, rewrite history with BFG (fastest)",
                "# Install: https://rtyley.github.io/bfg-repo-cleaner/",
                "bfg --replace-text secrets.txt",
                "git reflog expire --expire=now --all && git gc --prune=now --aggressive",
                "git push --force",
                "",
                "# Step 3 — Notify your team; force-push invalidates all open PRs",
            ]
        }

    # ─── UNTRACKED / MISSING FILES ───────────────────────────────────
    if "untracked" in p or ("missing" in p and "file" in p):
        return {
            "diagnosis": "Files not being tracked by git",
            "severity": "low",
            "explanation": (
                "Untracked files exist on disk but git is ignoring them — "
                "either they were never added, or they match a .gitignore pattern."
            ),
            "steps": [
                "# See all untracked files",
                "git status",
                "",
                "# Add a specific file",
                "git add path/to/file",
                "",
                "# Add everything untracked",
                "git add .",
                "",
                "# Check if a file is being blocked by .gitignore",
                "git check-ignore -v path/to/file",
            ]
        }

    return None  # No pattern matched — AI fallback needed
