"""
tests/test_detector.py — Unit tests for local pattern matching
"""

import pytest
from git_mistake.detector import diagnose_locally


MOCK_CTX_CLEAN = {
    "branch": "main",
    "status": "",
    "reflog": "abc1234 HEAD@{0}: commit: add feature\ndef5678 HEAD@{1}: commit: init",
    "recent_commits": "abc1234 add feature",
    "stash": "",
    "diff_stat": "",
    "merge_in_progress": False,
    "rebase_in_progress": False,
    "cherry_pick_in_progress": False,
    "bisect_in_progress": False,
}

MOCK_CTX_DETACHED = {**MOCK_CTX_CLEAN, "branch": "DETACHED_HEAD"}
MOCK_CTX_MERGING  = {**MOCK_CTX_CLEAN, "merge_in_progress": True}
MOCK_CTX_REBASING = {**MOCK_CTX_CLEAN, "rebase_in_progress": True}


class TestDetachedHead:
    def test_detects_from_branch_state(self):
        result = diagnose_locally(MOCK_CTX_DETACHED, "I don't know what happened")
        assert result is not None
        assert "detached" in result["diagnosis"].lower()

    def test_detects_from_problem_description(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "I'm in a detached head state")
        assert result is not None

    def test_result_has_required_keys(self):
        result = diagnose_locally(MOCK_CTX_DETACHED, "help")
        assert all(k in result for k in ["diagnosis", "severity", "explanation", "steps"])

    def test_steps_is_list(self):
        result = diagnose_locally(MOCK_CTX_DETACHED, "help")
        assert isinstance(result["steps"], list)


class TestHardReset:
    def test_detects_hard_reset(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "I did git reset --hard and lost my commits")
        assert result is not None
        assert result["severity"] == "high"

    def test_detects_lost_commits(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "I lost my commits somehow")
        assert result is not None

    def test_recovery_hash_hint_in_steps(self):
        ctx = {**MOCK_CTX_CLEAN, "reflog": "abc HEAD@{0}: reset: moving to HEAD~1\ndef HEAD@{1}: commit: my work"}
        result = diagnose_locally(ctx, "I accidentally ran git reset --hard")
        assert result is not None
        joined = "\n".join(result["steps"])
        assert "def" in joined  # Recovery hash from reflog


class TestMergeConflict:
    def test_detects_from_context_flag(self):
        result = diagnose_locally(MOCK_CTX_MERGING, "something went wrong")
        assert result is not None
        assert "merge" in result["diagnosis"].lower()

    def test_detects_from_description(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "I have merge conflicts I can't resolve")
        assert result is not None

    def test_includes_abort_option(self):
        result = diagnose_locally(MOCK_CTX_MERGING, "help")
        steps = "\n".join(result["steps"])
        assert "abort" in steps


class TestRebase:
    def test_detects_rebase_in_progress(self):
        result = diagnose_locally(MOCK_CTX_REBASING, "rebase is stuck")
        assert result is not None
        assert "rebase" in result["diagnosis"].lower()

    def test_includes_skip_option(self):
        result = diagnose_locally(MOCK_CTX_REBASING, "help")
        steps = "\n".join(result["steps"])
        assert "skip" in steps


class TestWrongBranch:
    def test_detects_wrong_branch(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "I committed to the wrong branch")
        assert result is not None
        assert result["severity"] == "low"

    def test_cherry_pick_mentioned(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "committed to wrong branch")
        steps = "\n".join(result["steps"])
        assert "cherry-pick" in steps


class TestSecretLeak:
    def test_detects_api_key(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "I accidentally pushed my API key")
        assert result is not None
        assert result["severity"] == "high"

    def test_detects_password(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "pushed my password to GitHub")
        assert result is not None

    def test_rotate_advice_present(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "exposed my token")
        steps = "\n".join(result["steps"])
        assert "revoke" in steps.lower() or "rotate" in steps.lower()


class TestNoMatch:
    def test_returns_none_for_unknown(self):
        result = diagnose_locally(MOCK_CTX_CLEAN, "something really weird happened to my repo")
        assert result is None
