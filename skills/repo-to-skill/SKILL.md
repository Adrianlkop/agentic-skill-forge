---
name: repo-to-skill
description: Convert a local codebase into a reusable agent skill that captures architecture, bounded contexts, conventions, and safe implementation rules. Use when onboarding to a repo or creating a reusable project memory skill.
when_to_use: repo to skill, repository skill, codebase onboarding, architecture skill, capture repo conventions, make a skill from this codebase, project memory
disable-model-invocation: true
context: fork
agent: general-purpose
allowed-tools: Bash(python3 *) Bash(python *) Bash(mkdir *) Bash(rm *) Bash(test *) Read Write Grep Glob LS
argument-hint: <path-to-repo> [skill-name-slug]
arguments: [repo_path, skill_name]
effort: high
---

# Repo-to-Skill Converter

Transform a local repository into a compact architecture and conventions skill. The generated skill should help the active agent work inside the codebase without relearning structure every session.

## Input

Usage:

```text
/repo-to-skill <path-to-repo> [skill-name-slug]
```

If the path is missing or does not exist, stop and show usage.

## Active Skills Root

Use the skills directory for the active agent:

- Codex: `~/.codex/skills`
- Claude Code: `~/.claude/skills`

Call this path `<skills_root>` throughout the workflow. If you are unsure, use the directory where this `repo-to-skill` skill is installed. If both are installed and the user did not specify a target, prefer the active agent's directory.

## Workflow

### Step 1 - Validate the repo path

Confirm the path exists and is a directory. Prefer absolute paths in all generated references.

### Step 2 - Determine the skill name

If `skill_name` is provided, normalize it to lowercase letters, numbers, and hyphens.

If no name is provided, derive it from the repository directory name.

Check whether `<skills_root>/<skill_name>/` already exists. If it exists, ask before overwriting or choose a `-2` suffix.

### Step 3 - Map the repository

Run:

```bash
python3 <skills_root>/repo-to-skill/scripts/map_repo.py "<path-to-repo>"
```

If `python3` is unavailable, use:

```bash
python <skills_root>/repo-to-skill/scripts/map_repo.py "<path-to-repo>"
```

The script writes:

- `repo_tree.txt` in the temporary work directory
- `metadata.json` in the temporary work directory

The script prints the exact work directory path. Use that path rather than assuming `/tmp`.

### Step 4 - Read high-signal files

Read `repo_tree.txt` and `metadata.json`.

Then quietly inspect 4-8 high-signal files if they exist:

- `README.md`
- `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, or equivalent manifest
- Main app entry point
- Test configuration
- Build or CI configuration
- Database schema or migration entry point
- Framework configuration files

Do not scan the whole repo unless needed. Avoid generated directories, dependency directories, and build outputs.

### Step 5 - Create the generated skill

Create:

```bash
mkdir -p <skills_root>/<skill_name>
```

Write:

- `SKILL.md`
- `architecture_map.md`
- `conventions.md`

### Step 6 - Generate `SKILL.md`

Keep it under 4,000 tokens. Put implementation rules before background.

Use this structure:

```markdown
---
name: <skill_name>
description: Architecture and implementation guide for <repo name>. Use when editing, debugging, testing, or reviewing this repository.
when_to_use: <repo name>, <domain terms>, <framework terms>, this codebase, this repo
allowed-tools: Read Grep Glob LS
argument-hint: [feature, file, module, or task]
---

# <Repo Name>

Source repo: <absolute path>
Generated: <date>

## Operating Rules

- Follow the existing patterns documented in `conventions.md`.
- Before editing a module, read its nearest tests and related configuration.
- Use `architecture_map.md` to identify ownership boundaries.
- Do not introduce new frameworks unless the repo already uses them or the user explicitly asks.

## Architecture Snapshot

<dense summary of app type, runtime, framework, data flow, and key modules>

## Core Workflows

- Build: `<command or unknown>`
- Test: `<command or unknown>`
- Lint/typecheck: `<command or unknown>`
- Run locally: `<command or unknown>`

## Module Index

- **<module>** -> files/directories, responsibility, common edit points

## Supporting Files

- [architecture_map.md](architecture_map.md) - bounded contexts and relationships
- [conventions.md](conventions.md) - naming, style, commands, tests, and safe edits
```

### Step 7 - Generate supporting files

`architecture_map.md`:

- List bounded contexts and modules.
- Note data stores, APIs, queues, jobs, external services, and UI boundaries if present.
- Include "Unknown from captured files" instead of guessing.

`conventions.md`:

- Commands from manifests and README.
- Naming patterns.
- Directory conventions.
- Testing style.
- Error handling and logging patterns.
- Dependency and configuration rules.
- Common pitfalls for future edits.

### Step 8 - Cleanup and report

Delete the temporary work directory printed by the script.

Report:

```text
Skill created: <skills_root>/<skill_name>/
Source repo: <path-to-repo>
Files: SKILL.md, architecture_map.md, conventions.md

Use:
  /<skill_name> <task>
```

## Quality Rules

1. Capture implementation rules, not a directory listing.
2. Prefer facts from files over guesses from framework names.
3. Mark unknowns explicitly.
4. Keep generated guidance practical for edits, tests, and reviews.
5. Respect existing architecture boundaries and local conventions.
