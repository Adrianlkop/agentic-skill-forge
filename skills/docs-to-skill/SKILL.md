---
name: docs-to-skill
description: Convert public documentation pages into a compact reusable agent skill with core concepts, API reference, and examples. Use when the user wants to turn docs, API references, SDK docs, or framework docs into a reusable local skill.
when_to_use: docs to skill, documentation skill, API docs skill, convert docs, learn this library, make a skill from docs, stop hallucinating APIs
disable-model-invocation: true
context: fork
agent: general-purpose
allowed-tools: Bash(python3 *) Bash(python *) Bash(mkdir *) Bash(rm *) Bash(test *) Read Write Grep Glob
argument-hint: <url> [skill-name-slug]
arguments: [url, skill_name]
effort: high
---

# Docs-to-Skill Converter

Transform public documentation into a reusable agent skill. Extract structure, APIs, examples, constraints, and gotchas. Do not create a raw documentation dump.

## Input

Usage:

```text
/docs-to-skill <url> [skill-name-slug]
```

If the first argument is missing or is not an `http://` or `https://` URL, stop and show the usage.

## Active Skills Root

Use the skills directory for the active agent:

- Codex: `~/.codex/skills`
- Claude Code: `~/.claude/skills`

Call this path `<skills_root>` throughout the workflow. If you are unsure, use the directory where this `docs-to-skill` skill is installed. If both are installed and the user did not specify a target, prefer the active agent's directory.

## Workflow

### Step 1 - Determine the skill name

If `skill_name` is provided, use it after normalizing to lowercase letters, numbers, and hyphens.

If no name is provided, derive a slug from the URL host and first meaningful path segment. Examples:

- `https://docs.astro.build` -> `astro-docs`
- `https://nextjs.org/docs/app` -> `nextjs-docs`

Check whether `<skills_root>/<skill_name>/` already exists. If it exists, ask before overwriting or choose a `-2` suffix.

### Step 2 - Scrape the source page

Run the extraction script:

```bash
python3 <skills_root>/docs-to-skill/scripts/scrape.py "<url>"
```

If `python3` is unavailable, use:

```bash
python <skills_root>/docs-to-skill/scripts/scrape.py "<url>"
```

The script writes:

- `raw_docs.md` in the temporary work directory
- `metadata.json` in the temporary work directory

The script prints the exact work directory path. Use that path rather than assuming `/tmp`.

### Step 3 - Analyze the extracted docs

Read `metadata.json` and `raw_docs.md`.

Identify:

- Product, framework, SDK, or API name
- Primary concepts and mental model
- Install/setup commands
- Public functions, classes, endpoints, configuration keys, and CLI commands
- Required code patterns and common mistakes
- Version notes or compatibility constraints if present

If the scraped page is thin, still generate a skill, but include a clear scope note that it covers only the captured page.

### Step 4 - Create the generated skill

Create:

```bash
mkdir -p <skills_root>/<skill_name>
```

Write these files:

- `SKILL.md`
- `api_reference.md`
- `code_examples.md`

### Step 5 - Generate `SKILL.md`

Keep the file under 4,000 tokens and front-load the most important rules.

Use this structure:

```markdown
---
name: <skill_name>
description: Grounded reference for <product/docs name>. Use when working with <main APIs, features, or workflows>.
when_to_use: <10-15 trigger phrases, comma-separated>
allowed-tools: Read Grep
argument-hint: [topic, API, command, or workflow]
---

# <Docs Name>

Generated from: <url>

## How to Use This Skill

- Use this skill when answering questions about <product>.
- Before giving API details, read `api_reference.md` if the relevant API is not in the core notes.
- Before writing code, read `code_examples.md` for local examples and patterns.
- If a topic is not covered here, say that this skill does not contain it instead of guessing.

## Core Concepts

<dense, practical concepts>

## Common Workflows

<setup, configuration, usage flows>

## Rules and Gotchas

<constraints, version notes, common mistakes>

## Topic Index

- **<topic>** -> `api_reference.md` or `code_examples.md`

## Supporting Files

- [api_reference.md](api_reference.md) - APIs, commands, configuration, options
- [code_examples.md](code_examples.md) - examples and implementation patterns
```

### Step 6 - Generate supporting files

`api_reference.md`:

- Group by API area.
- Preserve exact names and syntax.
- Include parameters, return values, flags, config keys, environment variables, and constraints when present.
- Use "Not captured in source" when the docs do not include a detail.

`code_examples.md`:

- Include only examples grounded in the captured docs.
- Preserve code syntax and commands where available.
- Explain when to use each pattern.
- Add gotchas beside the relevant examples.

### Step 7 - Cleanup and report

Delete the temporary work directory printed by the script.

Report:

```text
Skill created: <skills_root>/<skill_name>/
Source: <url>
Files: SKILL.md, api_reference.md, code_examples.md

Use:
  /<skill_name> <topic>
```

## Quality Rules

1. Extract stable structure, not page prose.
2. Do not invent APIs or options that were not in the captured docs.
3. Preserve exact names for functions, commands, flags, config keys, and environment variables.
4. Keep `SKILL.md` compact; move details into supporting files.
5. State scope limits when the source page does not cover the full product.
