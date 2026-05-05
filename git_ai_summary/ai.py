"""Groq API calls via the Groq SDK."""

from __future__ import annotations

import os
from typing import Optional

from groq import Groq

from .git import CommitInfo, RepoContext

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096


def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Add it to .env or export it in your shell."
        )
    return Groq(api_key=api_key)


def _call(system: str, user: str, max_tokens: int = MAX_TOKENS) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------

_README_SYSTEM = """\
You are a senior technical writer. Given information about a git repository, \
generate a clear, professional README.md in GitHub-flavored Markdown.

Structure:
1. Project title + one-sentence description
2. Features (bullet list)
3. Installation
4. Usage (with code examples)
5. Configuration / Environment variables (if any)
6. Contributing
7. License (MIT unless stated otherwise)

Be concise. Use fenced code blocks. Do NOT add placeholder sections for things \
not evidenced by the provided context.
"""


def generate_readme(
    ctx: RepoContext,
    file_tree: list[str],
    file_contents: dict[str, str],
) -> str:
    tree_str = "\n".join(file_tree[:60])
    # Keep payload under ~20k chars to stay well within context limits
    contents_str = ""
    budget = 18_000
    for path, content in file_contents.items():
        chunk = f"\n### {path}\n```\n{content[:3000]}\n```\n"
        if len(contents_str) + len(chunk) > budget:
            break
        contents_str += chunk

    user = f"""\
Repository: {ctx.name}
Branch: {ctx.branch}
Remote: {ctx.remote_url or "N/A"}
{f'Description: {ctx.description}' if ctx.description else ''}

File tree:
{tree_str}

Key file contents:
{contents_str}

Generate the README.md now.
"""
    return _call(_README_SYSTEM, user)


# ---------------------------------------------------------------------------
# CHANGELOG
# ---------------------------------------------------------------------------

_CHANGELOG_SYSTEM = """\
You are a technical writer generating a CHANGELOG in Keep-a-Changelog format \
(https://keepachangelog.com). Given a list of git commits, group them into \
sections: Added, Changed, Fixed, Removed, Security, Deprecated. \
Ignore merge commits and trivial chores unless they matter to users. \
Output only the Markdown for the new release section (no existing history).
"""


def generate_changelog(commits: list[CommitInfo], since: str, version: Optional[str] = None) -> str:
    if not commits:
        return "No commits found since the specified tag/SHA."

    commit_lines = "\n".join(
        f"- [{c.short_sha}] {c.message.splitlines()[0]}  ({c.author}, {c.date})"
        for c in commits
    )
    release_label = version or "Unreleased"

    user = f"""\
Commits since {since} (newest first):

{commit_lines}

Generate the changelog section for release: {release_label}
"""
    return _call(_CHANGELOG_SYSTEM, user)


# ---------------------------------------------------------------------------
# PR description
# ---------------------------------------------------------------------------

_PR_SYSTEM = """\
You are a senior engineer writing a GitHub Pull Request description. \
Given a unified diff of staged changes, produce a PR description with:

1. **Summary** — what this PR does and why (2-4 sentences)
2. **Changes** — bullet list of notable changes grouped by type (feat/fix/refactor/docs/chore)
3. **Testing** — how to verify the changes
4. **Screenshots / Notes** (optional, only if relevant from the diff)

Be precise. Reference file names and function names where helpful. \
Do NOT invent details not present in the diff.
"""


def generate_pr_description(diff: str, branch: Optional[str] = None) -> str:
    # Trim very large diffs
    if len(diff) > 20_000:
        diff = diff[:20_000] + "\n\n[... diff truncated ...]"

    user = f"""\
{'Branch: ' + branch if branch else ''}

Staged diff:
```diff
{diff}
```

Write the PR description now.
"""
    return _call(_PR_SYSTEM, user)
