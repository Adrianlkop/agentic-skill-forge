# SkillForge for Agentic Coding

SkillForge is a small, open-source library of agent skills that turn messy source material into reusable local skills.

It uses a lightweight agentic architecture: small extraction scripts prepare raw material, then Claude Code, Codex, or another skills-compatible agent synthesizes compact skill files that can be loaded on demand.

## Status

Alpha. The core skill workflows and extraction scripts are implemented, tested locally, and designed to be easy to audit. The project is ready for early users who understand the current limitations.

## What This Repo Provides

| Skill | Use Case | Input |
| --- | --- | --- |
| `docs-to-skill` | Convert a product docs page or API docs page into a grounded reference skill | Public URL |
| `repo-to-skill` | Convert a local codebase into an architecture and conventions skill | Local repository path |
| `slack-to-skill` | Convert Slack export conversations into a troubleshooting knowledge base | Slack JSON file or export directory |

## Installation

Clone or download this repository, then run the installer from the repository root.

macOS, Linux, WSL, or Git Bash:

```bash
cd skill-forge
bash install.sh
```

Windows PowerShell:

```powershell
cd skill-forge
.\install.ps1
```

By default, the installer copies everything under `skills/` into both:

- `~/.claude/skills/`
- `~/.codex/skills/`

To install to one target only:

```bash
SKILLFORGE_TARGETS=claude bash install.sh
SKILLFORGE_TARGETS=codex bash install.sh
```

```powershell
$env:SKILLFORGE_TARGETS = "codex"
.\install.ps1
```

## Usage

```text
/docs-to-skill https://docs.astro.build astro-docs
```

Creates a new skill from a documentation page. The generated skill should include:

- `SKILL.md` for core concepts and navigation instructions
- `api_reference.md` for public APIs, commands, configuration keys, and options
- `code_examples.md` for idiomatic examples and patterns

```text
/repo-to-skill ./my-monorepo billing-module
```

Creates a repo onboarding skill from a local codebase. The generated skill should include:

- `SKILL.md` for architecture overview and rules
- `architecture_map.md` for bounded contexts and module responsibilities
- `conventions.md` for naming, style, commands, and project norms

```text
/slack-to-skill ./slack_export/engineering.json tribal-knowledge
```

Creates a troubleshooting skill from Slack exports. The generated skill should include:

- `SKILL.md` for when to consult the tribal knowledge base
- `troubleshooting.md` for issue, symptom, diagnosis, fix, and source context entries

## How It Works

```text
source material
  |
  v
zero-dependency script
  |
  v
temporary work directory
  |
  v
agent synthesizes skill files
  |
  v
~/.claude/skills/<generated-skill>/ or ~/.codex/skills/<generated-skill>/
```

The scripts do extraction only. They do not summarize, classify, embed, or call models. The agent does the reasoning after reading the extracted material.

## Limitations

- `docs-to-skill` currently extracts a single URL. It does not crawl full documentation sites.
- `repo-to-skill` maps repository structure and asks Claude to inspect high-signal files. It does not index every source file.
- `slack-to-skill` parses Slack JSON files and export directories, but the generated skill quality depends on the export being sanitized and focused.
- Slack exports can contain private data, credentials, customer information, or internal decisions. Sanitize exports before using them.

## Design Principles

1. Keep extraction scripts dependency-light and easy to audit.
2. Generate structured knowledge, not raw dumps.
3. Front-load each generated `SKILL.md` with the highest-value operating rules.
4. Keep detailed references in separate files so Claude reads them on demand.
5. Preserve source-specific precision: exact API names, repo conventions, incident symptoms, error strings, and agreed fixes.

## Repository Structure

```text
skill-forge/
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- skills/
|   |-- docs-to-skill/
|   |   |-- agents/
|   |   |   `-- openai.yaml
|   |   |-- SKILL.md
|   |   `-- scripts/
|   |       `-- scrape.py
|   |-- repo-to-skill/
|   |   |-- agents/
|   |   |   `-- openai.yaml
|   |   |-- SKILL.md
|   |   `-- scripts/
|   |       `-- map_repo.py
|   `-- slack-to-skill/
|       |-- agents/
|       |   `-- openai.yaml
|       |-- SKILL.md
|       `-- scripts/
|           `-- parse_slack.py
|-- install.sh
|-- install.ps1
|-- LICENSE
`-- README.md
```

## Adding a New X-to-Skill

1. Create `skills/<name-to-skill>/SKILL.md`.
2. Add a small extraction script under `skills/<name-to-skill>/scripts/`.
3. Write the skill prompt so the active agent validates input, runs the script, reads the temporary output, creates `<skills_root>/<slug>/`, and removes temporary files.
4. Keep generated skill files compact and navigable.

## Contributing

Issues and pull requests are welcome. Keep new skills aligned with the project architecture:

- one skill folder under `skills/`
- one `SKILL.md`
- optional helper scripts under `scripts/`
- no mandatory third-party runtime dependencies unless the use case clearly requires them

## License

MIT
