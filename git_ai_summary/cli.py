"""Entry point for the git-ai CLI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from . import ai, git

load_dotenv()  # load .env if present

app = typer.Typer(
    name="git-ai",
    help="Generate README, CHANGELOG, and PR descriptions with Groq AI.",
    add_completion=True,
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True, style="bold red")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"git-ai-summary {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=_version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


# ---------------------------------------------------------------------------
# readme
# ---------------------------------------------------------------------------

@app.command()
def readme(
    repo: Path = typer.Option(Path("."), "--repo", "-r", help="Path to git repo."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file."),
    preview: bool = typer.Option(False, "--preview", "-p", help="Render Markdown preview in terminal."),
) -> None:
    """Generate a README.md from the repository code."""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console, transient=True) as progress:
        try:
            progress.add_task("Reading repository...", total=None)
            ctx = git.get_repo_context(repo)
            tree = git.get_file_tree(repo)
            contents = git.get_file_contents(repo, extensions=(".py", ".js", ".ts", ".go", ".rs",
                                                                ".java", ".rb", ".md", ".toml",
                                                                ".yaml", ".yml", ".json"))
            progress.add_task("Calling Claude API...", total=None)
            result = ai.generate_readme(ctx, tree, contents)
        except git.GitError as exc:
            err_console.print(f"Git error: {exc}")
            raise typer.Exit(1)
        except RuntimeError as exc:
            err_console.print(str(exc))
            raise typer.Exit(1)

    _output(result, output, preview, default_filename="README.md")


# ---------------------------------------------------------------------------
# changelog
# ---------------------------------------------------------------------------

@app.command()
def changelog(
    since: str = typer.Option(..., "--since", "-s", help="Tag or commit SHA to compare from."),
    repo: Path = typer.Option(Path("."), "--repo", "-r", help="Path to git repo."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file."),
    version: Optional[str] = typer.Option(None, "--version-label", help="Release label (e.g. v1.2.0)."),
    preview: bool = typer.Option(False, "--preview", "-p", help="Render Markdown preview in terminal."),
) -> None:
    """Generate a CHANGELOG section from commits since a tag or SHA."""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console, transient=True) as progress:
        try:
            progress.add_task(f"Fetching commits since {since}...", total=None)
            commits = git.get_commits_since(since, repo)
            console.print(f"[dim]Found {len(commits)} commit(s).[/dim]")
            progress.add_task("Calling Claude API...", total=None)
            result = ai.generate_changelog(commits, since=since, version=version)
        except git.GitError as exc:
            err_console.print(f"Git error: {exc}")
            raise typer.Exit(1)
        except RuntimeError as exc:
            err_console.print(str(exc))
            raise typer.Exit(1)

    _output(result, output, preview, default_filename="CHANGELOG.md")


# ---------------------------------------------------------------------------
# pr-desc
# ---------------------------------------------------------------------------

@app.command(name="pr-desc")
def pr_desc(
    repo: Path = typer.Option(Path("."), "--repo", "-r", help="Path to git repo."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file."),
    preview: bool = typer.Option(False, "--preview", "-p", help="Render Markdown preview in terminal."),
) -> None:
    """Generate a Pull Request description from staged changes."""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console, transient=True) as progress:
        try:
            progress.add_task("Reading staged diff...", total=None)
            diff = git.get_staged_diff(repo)
            ctx = git.get_repo_context(repo)
            progress.add_task("Calling Claude API...", total=None)
            result = ai.generate_pr_description(diff, branch=ctx.branch)
        except git.GitError as exc:
            err_console.print(f"Git error: {exc}")
            raise typer.Exit(1)
        except RuntimeError as exc:
            err_console.print(str(exc))
            raise typer.Exit(1)

    _output(result, output, preview, default_filename="PR_DESCRIPTION.md")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _output(
    content: str,
    output: Optional[Path],
    preview: bool,
    default_filename: str,
) -> None:
    if output:
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Saved to[/green] {output}")
    elif preview:
        console.print(Markdown(content))
    else:
        # Write raw Markdown to stdout so it can be piped
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
