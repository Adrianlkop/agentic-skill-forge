---
name: slack-to-skill
description: Convert Slack JSON exports into a troubleshooting and tribal-knowledge agent skill. Use when the user wants to preserve team decisions, incident fixes, recurring errors, or undocumented operational knowledge.
when_to_use: slack to skill, tribal knowledge, troubleshooting skill, slack export, incident history, team decisions, recurring errors, undocumented fixes
disable-model-invocation: true
context: fork
agent: general-purpose
allowed-tools: Bash(python3 *) Bash(python *) Bash(mkdir *) Bash(rm *) Bash(test *) Read Write Grep Glob
argument-hint: <slack-json-file-or-export-directory> [skill-name-slug]
arguments: [slack_path, skill_name]
effort: high
---

# Slack-to-Skill Converter

Transform Slack exports into a local troubleshooting skill. The goal is to preserve useful team knowledge, not to archive chat.

## Privacy Check

Slack exports can contain sensitive data. Before processing, remind the user that generated files may include names, internal systems, customer details, secrets, or private decisions. If the export may include secrets, ask them to provide a sanitized export first.

## Input

Usage:

```text
/slack-to-skill <slack-json-file-or-export-directory> [skill-name-slug]
```

The path may be:

- A Slack JSON message file
- A Slack export directory containing channel folders and daily JSON files

If the path is missing or does not exist, stop and show usage.

## Active Skills Root

Use the skills directory for the active agent:

- Codex: `~/.codex/skills`
- Claude Code: `~/.claude/skills`

Call this path `<skills_root>` throughout the workflow. If you are unsure, use the directory where this `slack-to-skill` skill is installed. If both are installed and the user did not specify a target, prefer the active agent's directory.

## Workflow

### Step 1 - Determine the skill name

If `skill_name` is provided, normalize it to lowercase letters, numbers, and hyphens.

If no name is provided, use `tribal-knowledge` or derive from the Slack channel/export directory.

Check whether `<skills_root>/<skill_name>/` already exists. If it exists, ask before overwriting or choose a `-2` suffix.

### Step 2 - Parse the Slack export

Run:

```bash
python3 <skills_root>/slack-to-skill/scripts/parse_slack.py "<slack-json-file-or-export-directory>"
```

If `python3` is unavailable, use:

```bash
python <skills_root>/slack-to-skill/scripts/parse_slack.py "<slack-json-file-or-export-directory>"
```

The script writes:

- `slack_threads.txt` in the temporary work directory
- `metadata.json` in the temporary work directory

The script prints the exact work directory path. Use that path rather than assuming `/tmp`.

### Step 3 - Analyze the parsed conversations

Read `metadata.json` and `slack_threads.txt`.

Filter out:

- Small talk
- Status chatter with no reusable decision
- Duplicates
- Bot noise

Extract:

- Error messages, stack traces, error codes, failed commands
- Symptoms and root causes
- Agreed fixes and workarounds
- Operational procedures
- Decisions and rationale
- Links to source systems when useful and safe

Do not include secrets, credentials, private customer data, or personal gossip. If sensitive material appears, redact it.

### Step 4 - Create the generated skill

Create:

```bash
mkdir -p <skills_root>/<skill_name>
```

Write:

- `SKILL.md`
- `troubleshooting.md`

### Step 5 - Generate `SKILL.md`

Use this structure:

```markdown
---
name: <skill_name>
description: Tribal knowledge base from Slack discussions. Use when debugging recurring issues, checking prior team decisions, or looking for undocumented fixes.
when_to_use: <error terms, systems, team terms, incident names>
allowed-tools: Read Grep
argument-hint: [error, symptom, system, or decision]
---

# <Skill Name>

Generated from: <source path>

## How to Use This Skill

- Search `troubleshooting.md` for exact error text before inventing a fix.
- Prefer entries with explicit agreed fixes over speculation.
- Redacted details mean the original export contained sensitive content.
- If an issue is not covered, say no matching Slack knowledge was captured.

## High-Value Topics

- **<topic>**: <what was learned>

## Known Systems and Terms

- <system or domain term>

## Supporting Files

- [troubleshooting.md](troubleshooting.md) - issue, symptom, diagnosis, fix, and context entries
```

### Step 6 - Generate `troubleshooting.md`

Use Q&A or incident-note format:

```markdown
## <Issue or Error Name>

**Symptoms**: <observable failure>
**Likely cause**: <cause agreed in Slack, or "Unknown">
**Fix or workaround**: <specific command, code change, process, or escalation path>
**Context**: <short source-derived explanation>
**Source clues**: <channel/date/user if available and safe>
```

Group related errors. Preserve exact error strings. Redact secrets.

### Step 7 - Cleanup and report

Delete the temporary work directory printed by the script.

Report:

```text
Skill created: <skills_root>/<skill_name>/
Source: <slack path>
Files: SKILL.md, troubleshooting.md

Use:
  /<skill_name> <error or symptom>
```

## Quality Rules

1. Extract reusable operational knowledge, not chat history.
2. Preserve exact error strings and command names.
3. Redact sensitive data.
4. Distinguish agreed fixes from speculation.
5. Keep entries actionable and searchable.
