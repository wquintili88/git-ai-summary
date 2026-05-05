"""Git repository introspection using GitPython."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import git
from git import InvalidGitRepositoryError, Repo


class GitError(Exception):
    pass


def _find_repo(path: str | Path = ".") -> Repo:
    try:
        return Repo(str(path), search_parent_directories=True)
    except InvalidGitRepositoryError:
        raise GitError(f"No git repository found at or above '{path}'")


@dataclass
class CommitInfo:
    sha: str
    short_sha: str
    message: str
    author: str
    date: str
    files_changed: list[str] = field(default_factory=list)


@dataclass
class RepoContext:
    name: str
    branch: str
    remote_url: Optional[str]
    description: Optional[str]


def get_repo_context(path: str | Path = ".") -> RepoContext:
    repo = _find_repo(path)
    name = Path(repo.working_dir).name

    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = repo.head.commit.hexsha[:8]  # detached HEAD

    remote_url: Optional[str] = None
    if repo.remotes:
        remote_url = repo.remotes[0].url

    # Read description file if present (bare repos or set manually)
    desc_file = Path(repo.git_dir) / "description"
    description: Optional[str] = None
    if desc_file.exists():
        raw = desc_file.read_text().strip()
        if not raw.startswith("Unnamed repository"):
            description = raw

    return RepoContext(name=name, branch=branch, remote_url=remote_url, description=description)


def get_file_tree(path: str | Path = ".", max_files: int = 80) -> list[str]:
    """Return tracked file paths relative to repo root."""
    repo = _find_repo(path)
    try:
        tracked = [item.path for item in repo.head.commit.tree.traverse()
                   if item.type == "blob"]
    except ValueError:
        # Empty repo / no commits yet
        return []
    return tracked[:max_files]


def get_file_contents(path: str | Path = ".", extensions: tuple[str, ...] = ()) -> dict[str, str]:
    """Return {rel_path: content} for tracked text files, optionally filtered by extension."""
    repo = _find_repo(path)
    root = Path(repo.working_dir)
    result: dict[str, str] = {}

    try:
        blobs = [item for item in repo.head.commit.tree.traverse() if item.type == "blob"]
    except ValueError:
        return result

    for blob in blobs:
        if extensions and not any(blob.path.endswith(ext) for ext in extensions):
            continue
        abs_path = root / blob.path
        try:
            result[blob.path] = abs_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

    return result


def get_commits_since(tag_or_sha: str, path: str | Path = ".") -> list[CommitInfo]:
    """Return commits reachable from HEAD but not from *tag_or_sha*."""
    repo = _find_repo(path)
    try:
        rev_range = f"{tag_or_sha}..HEAD"
        commits = list(repo.iter_commits(rev_range))
    except git.GitCommandError as exc:
        raise GitError(f"Cannot resolve ref '{tag_or_sha}': {exc}") from exc

    result: list[CommitInfo] = []
    for c in commits:
        files = list(c.stats.files.keys()) if c.parents else []
        result.append(CommitInfo(
            sha=c.hexsha,
            short_sha=c.hexsha[:8],
            message=c.message.strip(),
            author=str(c.author),
            date=c.authored_datetime.strftime("%Y-%m-%d"),
            files_changed=files,
        ))
    return result


def get_staged_diff(path: str | Path = ".") -> str:
    """Return unified diff of staged (index vs HEAD) changes."""
    repo = _find_repo(path)
    try:
        diff = repo.git.diff("--cached", "--unified=3")
    except git.GitCommandError as exc:
        raise GitError(f"Failed to get staged diff: {exc}") from exc

    if not diff.strip():
        raise GitError("No staged changes found. Stage files with `git add` first.")
    return diff


def get_recent_commits(n: int = 20, path: str | Path = ".") -> list[CommitInfo]:
    repo = _find_repo(path)
    result: list[CommitInfo] = []
    try:
        for c in repo.iter_commits("HEAD", max_count=n):
            result.append(CommitInfo(
                sha=c.hexsha,
                short_sha=c.hexsha[:8],
                message=c.message.strip(),
                author=str(c.author),
                date=c.authored_datetime.strftime("%Y-%m-%d"),
            ))
    except (git.GitCommandError, ValueError):
        pass
    return result
