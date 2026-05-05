# git-ai-summary

CLI tool that uses the Claude API to generate README, CHANGELOG, and PR descriptions from a git repository.

## Features

- `git-ai readme` — scans your repo and generates a full README.md
- `git-ai changelog --since <tag>` — generates a Keep-a-Changelog section from commits
- `git-ai pr-desc` — generates a GitHub PR description from staged changes
- Markdown preview in terminal (`--preview`)
- Pipe-friendly: raw Markdown goes to stdout by default

## Installation

```bash
pip install git-ai-summary
```

Or from source:

```bash
git clone https://github.com/yourusername/git-ai-summary
cd git-ai-summary
pip install -e .
```

## Configuration

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

Or export directly:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
# Generate README (print to stdout)
git-ai readme

# Save to file
git-ai readme -o README.md

# Render preview in terminal
git-ai readme --preview

# Generate CHANGELOG since a tag
git-ai changelog --since v1.0.0
git-ai changelog --since v1.0.0 --version-label v1.1.0 -o CHANGELOG.md

# Generate PR description from staged changes
git add .
git-ai pr-desc
git-ai pr-desc --preview
```

## Options

| Command | Flag | Description |
|---------|------|-------------|
| all | `--repo PATH` | Path to git repo (default: `.`) |
| all | `--output PATH` | Write output to file |
| all | `--preview` | Render Markdown in terminal |
| `changelog` | `--since REF` | Tag or SHA to compare from (required) |
| `changelog` | `--version-label` | Release label (e.g. `v1.2.0`) |

## License

MIT
