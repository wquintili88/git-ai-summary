"""Tests for git.py"""

from __future__ import annotations

import pytest

from git_ai_summary.git import (
    CommitInfo,
    GitError,
    RepoContext,
    get_repo_context,
    get_file_tree,
    get_commits_since,
    get_staged_diff,
)


def test_get_repo_context_returns_repo_context(tmp_path):
    """get_repo_context returns a RepoContext for a valid repo."""
    import git as gitlib
    repo = gitlib.Repo.init(tmp_path)
    # Need at least one commit for branch to resolve
    (tmp_path / "file.txt").write_text("hello")
    repo.index.add(["file.txt"])
    repo.index.commit("init", author=gitlib.Actor("test", "test@test.com"),
                      committer=gitlib.Actor("test", "test@test.com"))

    ctx = get_repo_context(tmp_path)
    assert isinstance(ctx, RepoContext)
    assert ctx.name == tmp_path.name
    assert ctx.branch == "master" or ctx.branch == "main"


def test_get_repo_context_raises_on_non_repo(tmp_path):
    """get_repo_context raises GitError when not a git repo."""
    with pytest.raises(GitError, match="No git repository found"):
        get_repo_context(tmp_path)


def test_get_file_tree_returns_list(tmp_path):
    """get_file_tree returns list of tracked file paths."""
    import git as gitlib
    repo = gitlib.Repo.init(tmp_path)
    (tmp_path / "a.py").write_text("x = 1")
    (tmp_path / "b.py").write_text("y = 2")
    repo.index.add(["a.py", "b.py"])
    repo.index.commit("init", author=gitlib.Actor("test", "test@test.com"),
                      committer=gitlib.Actor("test", "test@test.com"))

    tree = get_file_tree(tmp_path)
    assert "a.py" in tree
    assert "b.py" in tree


def test_get_file_tree_empty_repo(tmp_path):
    """get_file_tree returns empty list for repo with no commits."""
    import git as gitlib
    gitlib.Repo.init(tmp_path)
    assert get_file_tree(tmp_path) == []


def test_get_commits_since_invalid_ref(tmp_path):
    """get_commits_since raises GitError for unknown ref."""
    import git as gitlib
    repo = gitlib.Repo.init(tmp_path)
    (tmp_path / "f.txt").write_text("x")
    repo.index.add(["f.txt"])
    repo.index.commit("init", author=gitlib.Actor("test", "test@test.com"),
                      committer=gitlib.Actor("test", "test@test.com"))

    with pytest.raises(GitError, match="Cannot resolve ref"):
        get_commits_since("nonexistent-tag-xyz", tmp_path)


def test_get_staged_diff_raises_when_nothing_staged(tmp_path):
    """get_staged_diff raises GitError when no staged changes."""
    import git as gitlib
    repo = gitlib.Repo.init(tmp_path)
    (tmp_path / "f.txt").write_text("x")
    repo.index.add(["f.txt"])
    repo.index.commit("init", author=gitlib.Actor("test", "test@test.com"),
                      committer=gitlib.Actor("test", "test@test.com"))

    with pytest.raises(GitError, match="No staged changes"):
        get_staged_diff(tmp_path)
