"""Tests for CLI commands using Typer test client."""

from __future__ import annotations

from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_ai_summary.cli import app
from git_ai_summary.git import GitError, RepoContext

runner = CliRunner()

FAKE_CONTENT = "# Generated"


def _mock_readme(monkeypatch):
    monkeypatch.setattr("git_ai_summary.cli.git.get_repo_context",
                        lambda p: RepoContext("repo", "main", None, None))
    monkeypatch.setattr("git_ai_summary.cli.git.get_file_tree", lambda p: [])
    monkeypatch.setattr("git_ai_summary.cli.git.get_file_contents", lambda p, extensions: {})
    monkeypatch.setattr("git_ai_summary.cli.ai.generate_readme",
                        lambda ctx, tree, contents: FAKE_CONTENT)


def test_readme_stdout(monkeypatch):
    _mock_readme(monkeypatch)
    result = runner.invoke(app, ["readme"])
    assert result.exit_code == 0
    assert FAKE_CONTENT in result.output


def test_readme_git_error(monkeypatch):
    monkeypatch.setattr("git_ai_summary.cli.git.get_repo_context",
                        lambda p: (_ for _ in ()).throw(GitError("not a repo")))
    result = runner.invoke(app, ["readme"])
    assert result.exit_code == 1


def test_changelog_requires_since(monkeypatch):
    result = runner.invoke(app, ["changelog"])
    assert result.exit_code != 0


def test_changelog_stdout(monkeypatch):
    monkeypatch.setattr("git_ai_summary.cli.git.get_commits_since", lambda since, p: [])
    monkeypatch.setattr("git_ai_summary.cli.ai.generate_changelog",
                        lambda commits, since, version: FAKE_CONTENT)
    result = runner.invoke(app, ["changelog", "--since", "v1.0.0"])
    assert result.exit_code == 0
    assert FAKE_CONTENT in result.output


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "git-ai-summary" in result.output
