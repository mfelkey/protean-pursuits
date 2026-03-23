#!/usr/bin/env python3
"""
scripts/refresh_templates.py

Protean Pursuits — Template refresh utility

Populates templates/<team>/ from the live teams/<team>/ submodules.
Strips all project-specific content, replacing with PROJ-TEMPLATE
and PROJECT_NAME_PLACEHOLDER tokens.

What is kept (hybrid template):
  - Directory structure
  - __init__.py files
  - base_agent.py / base_lead.py
  - orchestrator.py (core infrastructure only — notifications, HITL, context)
  - flows/<team>_flow.py (generic, project-agnostic)
  - config/.env.template
  - README.md (genericised)
  - .gitignore
  - output/, logs/, memory/ structure (.gitkeep files)

What is stripped / genericised:
  - Project-specific backstories referencing ParallaxEdge, AAVA, etc.
  - Hardcoded project IDs (PROJ-PARALLAXEDGE → PROJ-TEMPLATE)
  - Hardcoded project names
  - docs/ folder contents (project docs don't belong in templates)
  - logs/ contents
  - Any .env files (never template credentials)

Usage:
    python3.11 scripts/refresh_templates.py              # refresh all teams
    python3.11 scripts/refresh_templates.py marketing-team  # refresh one team
    python3.11 scripts/refresh_templates.py --list       # show template status
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
TEAMS_DIR = REPO_ROOT / "teams"
TEMPLATES_DIR = REPO_ROOT / "templates"

TEAMS = [
    "dev-team",
    "ds-team",
    "marketing-team",
    "strategy-team",
    "legal-team",
    "design-team",
    "qa-team",
]

# Files/dirs to always exclude from templates
EXCLUDE_PATTERNS = {
    ".git",
    ".env",
    "logs",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".DS_Store",
}

# Dirs to include as empty structure only (just .gitkeep)
STRUCTURE_ONLY_DIRS = {
    "logs",
    "memory",
    "output",
}

# Project-specific strings to genericise
REPLACEMENTS = [
    # Project IDs
    (r"PROJ-PARALLAXEDGE", "PROJ-TEMPLATE"),
    (r"PROJ-[A-Z0-9]{8}", "PROJ-TEMPLATE"),
    # Project names
    (r"ParallaxEdge", "PROJECT_NAME_PLACEHOLDER"),
    (r"parallaxedge", "project_name_placeholder"),
    (r"PARALLAX ?[Ee]dge", "PROJECT_NAME_PLACEHOLDER"),
    # AAVA / ambulance (belt and suspenders)
    (r"AAVA|ambulance|Ambulance|va-ambulance", "project"),
    # Sys path references to specific users
    (r'/home/mfelkey/', '/home/mfelkey/'),  # keep — this is set by user at runtime
]


def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded from templates."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if path.name.endswith(pattern[1:]):
                return True
        elif path.name == pattern:
            return True
    return False


def genericise_content(content: str) -> str:
    """Apply all project-specific → generic replacements."""
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    return content


def copy_team_to_template(team_name: str) -> None:
    """Copy a team submodule to its template directory, genericising content."""
    src = TEAMS_DIR / team_name
    dst = TEMPLATES_DIR / team_name

    if not src.exists() or not any(src.iterdir()):
        print(f"  ⚠️  {team_name}: submodule not populated — skipping")
        return

    # Clean and recreate destination
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    copied = 0
    skipped = 0

    for src_path in sorted(src.rglob("*")):
        # Skip excluded patterns
        if any(should_exclude(p) for p in src_path.parents) or should_exclude(src_path):
            skipped += 1
            continue

        rel = src_path.relative_to(src)
        dst_path = dst / rel

        # Handle structure-only directories — just create .gitkeep
        top_level = rel.parts[0] if rel.parts else ""
        if top_level in STRUCTURE_ONLY_DIRS:
            if src_path.is_dir():
                dst_path.mkdir(parents=True, exist_ok=True)
                (dst_path / ".gitkeep").touch()
            skipped += 1
            continue

        # Skip docs/ contents (keep structure but not files)
        if top_level == "docs":
            if src_path.is_dir():
                dst_path.mkdir(parents=True, exist_ok=True)
                (dst_path / ".gitkeep").touch()
            skipped += 1
            continue

        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
            continue

        # Copy and genericise text files
        try:
            content = src_path.read_text(encoding="utf-8")
            content = genericise_content(content)
            dst_path.write_text(content, encoding="utf-8")
            copied += 1
        except UnicodeDecodeError:
            # Binary file — copy as-is
            shutil.copy2(src_path, dst_path)
            copied += 1

    # Add template header to README
    readme = dst / "README.md"
    if readme.exists():
        content = readme.read_text()
        header = (
            f"# {team_name} — Template\n\n"
            f"> **This is a Protean Pursuits team template.**\n"
            f"> Instantiated by `scripts/refresh_templates.py` from `teams/{team_name}/`.\n"
            f"> Last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"> Replace all `PROJECT_NAME_PLACEHOLDER` and `PROJ-TEMPLATE` tokens.\n\n"
            f"---\n\n"
        )
        # Replace existing first line if it's already a template header
        if content.startswith("# " + team_name + " — Template"):
            lines = content.split("\n")
            # Find end of header block
            for i, line in enumerate(lines):
                if line == "---" and i < 10:
                    content = "\n".join(lines[i+2:])
                    break
        readme.write_text(header + content)

    print(f"  ✅ {team_name}: {copied} files copied, {skipped} skipped")


def show_status() -> None:
    """Show template population status for all teams."""
    print(f"\n  {'─'*55}")
    print(f"  {'TEAM':<25} {'TEMPLATE':<12} {'FILES':<8} LAST REFRESHED")
    print(f"  {'─'*55}")

    for team in TEAMS:
        src = TEAMS_DIR / team
        dst = TEMPLATES_DIR / team
        src_ok = src.exists() and any(src.iterdir())
        dst_ok = dst.exists() and any(dst.iterdir())

        if not src_ok:
            status = "⚠️  no submodule"
        elif not dst_ok:
            status = "❌ not populated"
        else:
            status = "✅ populated"

        file_count = sum(1 for _ in dst.rglob("*") if _.is_file()) if dst_ok else 0

        # Get last modified time of template
        if dst_ok:
            mtime = max((f.stat().st_mtime for f in dst.rglob("*") if f.is_file()), default=0)
            age = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        else:
            age = "—"

        print(f"  {team:<25} {status:<20} {file_count:<8} {age}")

    print(f"  {'─'*55}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Protean Pursuits template refresh utility"
    )
    parser.add_argument("team", nargs="?", default=None,
                        help=f"Team to refresh (default: all). Options: {TEAMS}")
    parser.add_argument("--list", action="store_true",
                        help="Show template status without refreshing")
    args = parser.parse_args()

    if args.list:
        show_status()
        return

    TEMPLATES_DIR.mkdir(exist_ok=True)

    teams_to_refresh = [args.team] if args.team else TEAMS

    print(f"\n🔄 Refreshing templates from submodules...")
    print(f"   Source:      teams/")
    print(f"   Destination: templates/")
    print(f"   Teams:       {', '.join(teams_to_refresh)}\n")

    for team in teams_to_refresh:
        if team not in TEAMS:
            print(f"  ❌ Unknown team: {team}. Options: {TEAMS}")
            continue
        print(f"  Processing {team}...")
        copy_team_to_template(team)

    print(f"\n✅ Template refresh complete.")
    show_status()


if __name__ == "__main__":
    main()
