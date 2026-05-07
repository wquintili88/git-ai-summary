# git-ai-summary

> CLI tool that auto-generates README, CHANGELOG, and PR descriptions from your git history using Groq AI (Llama 3.3 70B).

## Features

- `git-ai readme` — scans your repo and generates a professional README.md
- `git-ai changelog --since <tag>` — generates a Keep-a-Changelog section from commits
- `git-ai pr-desc` — generates a GitHub PR description from staged changes
- Rich Markdown preview in terminal (`--preview`)
- Pipe-friendly: raw Markdown goes to stdout by default

## Requirements

- Python 3.9+
- A [Groq API key](https://console.groq.com/keys) (free tier available)

## Installation

```bash
pip install git-ai-summary
```

Or from source:

```bash
git clone https://github.com/wquintili88/git-ai-summary
cd git-ai-summary
pip install -e .
```

## Configuration

```bash
cp .env.example .env
# Open .env and set your GROQ_API_KEY
```

Or export directly in your shell:

```bash
export GROQ_API_KEY=gsk_...
```

## Usage

```bash
# Generate README (print to stdout)
git-ai readme

# Save directly to file
git-ai readme -o README.md

# Render Markdown preview in terminal
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
|---|---|---|
| all | `--repo PATH` | Path to git repo (default: `.`) |
| all | `--output / -o PATH` | Write output to file |
| all | `--preview / -p` | Render Markdown in terminal |
| `changelog` | `--since / -s REF` | Tag or SHA to compare from (required) |
| `changelog` | `--version-label` | Release label (e.g. `v1.2.0`) |

## GitHub Action

Use `git-ai-summary` directly in your CI/CD workflows:

```yaml
- name: Generate PR description
  uses: wquintili88/git-ai-summary@main
  with:
    command: pr-desc
    groq_api_key: ${{ secrets.GROQ_API_KEY }}
```

### Action Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `command` | yes | — | `readme`, `changelog`, or `pr-desc` |
| `groq_api_key` | yes | — | Your Groq API key |
| `repo_path` | no | `.` | Path to the git repository |
| `output_file` | no | — | Write output to this file |
| `since` | no | — | Tag/SHA for changelog (required when `command=changelog`) |
| `version_label` | no | — | Release label for changelog |
| `python_version` | no | `3.12` | Python version to use |

### Action Outputs

| Output | Description |
|---|---|
| `content` | Generated Markdown content (when `output_file` is not set) |
| `output_file` | Path to the output file (when `output_file` is set) |

### Examples

**Auto-comment PR description:**

```yaml
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  describe:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Generate PR description
        id: desc
        uses: wquintili88/git-ai-summary@main
        with:
          command: pr-desc
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## AI-Generated PR Description\n\n${{ steps.desc.outputs.content }}`
            })
```

**Generate changelog on release:**

```yaml
- uses: wquintili88/git-ai-summary@main
  with:
    command: changelog
    groq_api_key: ${{ secrets.GROQ_API_KEY }}
    since: v1.0.0
    version_label: v1.1.0
    output_file: CHANGELOG.md
```

## Security

- Never commit your `.env` file — it is listed in `.gitignore`
- The `.env.example` file contains only placeholder values and is safe to commit

## Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

## License

MIT
