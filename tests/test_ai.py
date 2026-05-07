"""Tests for ai.py — Groq calls are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_ai_summary import ai
from git_ai_summary.git import CommitInfo, RepoContext


FAKE_RESPONSE = "# Generated content"


def _mock_call(monkeypatch, content: str = FAKE_RESPONSE):
    monkeypatch.setattr(ai, "_call", lambda system, user, **kw: content)


def test_generate_readme(monkeypatch):
    _mock_call(monkeypatch)
    ctx = RepoContext(name="my-repo", branch="main", remote_url=None, description=None)
    result = ai.generate_readme(ctx, ["file.py"], {"file.py": "x = 1"})
    assert result == FAKE_RESPONSE


def test_generate_changelog_no_commits():
    result = ai.generate_changelog([], since="v1.0.0")
    assert "No commits" in result


def test_generate_changelog_with_commits(monkeypatch):
    _mock_call(monkeypatch)
    commits = [
        CommitInfo(sha="abc123", short_sha="abc123", message="feat: add thing",
                   author="dev", date="2024-01-01")
    ]
    result = ai.generate_changelog(commits, since="v1.0.0", version="v1.1.0")
    assert result == FAKE_RESPONSE


def test_generate_pr_description(monkeypatch):
    _mock_call(monkeypatch)
    result = ai.generate_pr_description("diff --git a/f.py ...", branch="feature/x")
    assert result == FAKE_RESPONSE


def test_generate_pr_description_truncates_large_diff(monkeypatch):
    captured = {}

    def fake_call(system, user, **kw):
        captured["user"] = user
        return FAKE_RESPONSE

    monkeypatch.setattr(ai, "_call", fake_call)
    big_diff = "x" * 25_000
    ai.generate_pr_description(big_diff)
    assert "truncated" in captured["user"]


def test_client_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY not set"):
        ai._client()
