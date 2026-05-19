$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceSkillsDir = Join-Path $scriptDir "skills"
$targets = if ($env:SKILLFORGE_TARGETS) {
    $env:SKILLFORGE_TARGETS -split "[,\s]+" | Where-Object { $_ }
} else {
    @("claude", "codex")
}

if (-not (Test-Path -LiteralPath $sourceSkillsDir -PathType Container)) {
    throw "skills directory not found at $sourceSkillsDir"
}

function Install-SkillsToDirectory {
    param([string]$SkillsDir)

    Write-Host "Installing SkillForge skills into $SkillsDir"
    New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

    Get-ChildItem -LiteralPath $sourceSkillsDir -Directory | ForEach-Object {
        $skillName = $_.Name
        $targetDir = Join-Path $SkillsDir $skillName

        Write-Host "Installing $skillName"
        if (Test-Path -LiteralPath $targetDir) {
            Remove-Item -LiteralPath $targetDir -Recurse -Force
        }

        Copy-Item -LiteralPath $_.FullName -Destination $targetDir -Recurse

        Get-ChildItem -LiteralPath $targetDir -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force
        Get-ChildItem -LiteralPath $targetDir -File -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue |
            Remove-Item -Force
    }
}

foreach ($target in $targets) {
    switch ($target.ToLowerInvariant()) {
        "claude" {
            $skillsDir = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME ".claude\skills" }
            Install-SkillsToDirectory -SkillsDir $skillsDir
        }
        "codex" {
            $skillsDir = if ($env:CODEX_SKILLS_DIR) { $env:CODEX_SKILLS_DIR } else { Join-Path $HOME ".codex\skills" }
            Install-SkillsToDirectory -SkillsDir $skillsDir
        }
        default {
            throw "Unknown target '$target'. Use claude, codex, or both comma-separated."
        }
    }
}

Write-Host "Done."
Write-Host "Try:"
Write-Host "  Use docs-to-skill on <url> with optional <slug>"
Write-Host "  Use repo-to-skill on <path> with optional <slug>"
Write-Host "  Use slack-to-skill on <json-file-or-export-dir> with optional <slug>"
