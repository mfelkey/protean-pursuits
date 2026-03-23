#!/usr/bin/env python3
"""
scripts/setup_env.py

Protean Pursuits — Environment setup utility

Prompts for all required values once and writes config/.env
to protean-pursuits and all 7 team submodules simultaneously.

Usage:
    python scripts/setup_env.py              # interactive setup
    python scripts/setup_env.py --update     # update existing .env files
    python scripts/setup_env.py --show       # show current values (masked)
    python scripts/setup_env.py --team marketing-team  # write one team only
"""

import os
import sys
import argparse
import getpass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TEAMS = [
    "dev-team",
    "ds-team",
    "marketing-team",
    "strategy-team",
    "legal-team",
    "design-team",
    "qa-team",
]

# All repos that need a .env
ALL_REPOS = [REPO_ROOT] + [REPO_ROOT / "teams" / t for t in TEAMS]

# Field definitions: (key, prompt, default, secret, required)
FIELDS = [
    # LLM
    ("TIER1_MODEL",       "Tier 1 LLM model",        "ollama/qwen3:32b",           False, True),
    ("TIER2_MODEL",       "Tier 2 LLM model",        "ollama/qwen3-coder:30b",     False, True),
    ("OLLAMA_BASE_URL",   "Ollama base URL",          "http://localhost:11434",     False, True),
    # Human-in-the-loop
    ("HUMAN_EMAIL",       "Your email address",       "",                           False, True),
    ("HUMAN_PHONE_NUMBER","Your phone (e.g. +15551234567)", "",                    False, True),
    ("OUTLOOK_ADDRESS",   "Outlook email address for notifications", "mike.felkey@outlook.com", False, True),
    ("OUTLOOK_PASSWORD",  "Outlook password",                          "",                           True,  True),
    # GitHub
    ("GITHUB_TOKEN",      "GitHub Personal Access Token", "",                      True,  True),
    ("GITHUB_USERNAME",   "GitHub username",          "mfelkey",                   False, True),
    # Observability (optional)
    ("LANGFUSE_PUBLIC_KEY","Langfuse public key (optional, press Enter to skip)", "", True, False),
    ("LANGFUSE_SECRET_KEY","Langfuse secret key (optional, press Enter to skip)", "", True, False),
    ("LANGFUSE_HOST",     "Langfuse host",            "https://cloud.langfuse.com", False, False),
]

# Team-specific extra fields
TEAM_EXTRA_FIELDS = {
    "marketing-team": [
        ("X_API_KEY",           "X (Twitter) API key (optional)",      "", True,  False),
        ("X_API_SECRET",        "X API secret (optional)",             "", True,  False),
        ("X_ACCESS_TOKEN",      "X access token (optional)",           "", True,  False),
        ("X_ACCESS_SECRET",     "X access secret (optional)",          "", True,  False),
        ("INSTAGRAM_ACCESS_TOKEN","Instagram access token (optional)", "", True,  False),
        ("INSTAGRAM_ACCOUNT_ID","Instagram account ID (optional)",     "", False, False),
        ("DISCORD_BOT_TOKEN",   "Discord bot token (optional)",        "", True,  False),
        ("DISCORD_GUILD_ID",    "Discord guild ID (optional)",         "", False, False),
        ("CRM_API_KEY",         "CRM API key (optional)",              "", True,  False),
        ("CRM_PLATFORM",        "CRM platform (e.g. mailchimp)",       "", False, False),
    ],
    "legal-team": [],
    "strategy-team": [],
    "design-team": [],
    "qa-team": [],
}


def mask(value: str) -> str:
    """Mask a secret value for display."""
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def read_existing_env(env_path: Path) -> dict:
    """Read existing .env file into a dict."""
    values = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                values[k.strip()] = v.strip()
    return values


def prompt_value(key: str, prompt: str, default: str,
                 secret: bool, existing: str = "") -> str:
    """Prompt the user for a value."""
    display_default = mask(existing) if (secret and existing) else (existing or default)
    suffix = f" [{display_default}]" if display_default else ""

    while True:
        try:
            if secret:
                value = getpass.getpass(f"  {prompt}{suffix}: ")
            else:
                value = input(f"  {prompt}{suffix}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSetup cancelled.")
            sys.exit(0)

        # Use existing/default if user pressed Enter
        if not value:
            value = existing or default

        return value


def write_env(repo_path: Path, values: dict, extra_fields: list = None) -> None:
    """Write a .env file to repo_path/config/.env."""
    config_dir = repo_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    env_path = config_dir / ".env"

    template_path = config_dir / ".env.template"
    header = ""
    if template_path.exists():
        # Preserve section comments from template
        lines = []
        for line in template_path.read_text().splitlines():
            if line.startswith("#") or line.strip() == "":
                lines.append(line)
            else:
                break
        header = "\n".join(lines) + "\n\n" if lines else ""

    lines = [f"# Generated by scripts/setup_env.py\n"]

    sections = {
        "LLM": ["TIER1_MODEL", "TIER2_MODEL", "OLLAMA_BASE_URL"],
        "Human-in-the-loop": ["HUMAN_EMAIL", "HUMAN_PHONE_NUMBER",
                               "OUTLOOK_ADDRESS", "OUTLOOK_PASSWORD"],
        "GitHub": ["GITHUB_TOKEN", "GITHUB_USERNAME"],
        "Observability": ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"],
    }

    written_keys = set()
    for section, keys in sections.items():
        lines.append(f"# ── {section} {'─' * (60 - len(section))}")
        for key in keys:
            if key in values:
                lines.append(f"{key}={values[key]}")
                written_keys.add(key)
        lines.append("")

    # Write any extra team-specific fields
    if extra_fields:
        lines.append("# ── Team-specific ─────────────────────────────────────────────")
        for key, _, _, _, _ in extra_fields:
            if key in values:
                lines.append(f"{key}={values.get(key, '')}")
                written_keys.add(key)
        lines.append("")

    # Write any remaining values not in sections
    remaining = {k: v for k, v in values.items() if k not in written_keys}
    if remaining:
        lines.append("# ── Additional ────────────────────────────────────────────────")
        for k, v in remaining.items():
            lines.append(f"{k}={v}")

    env_path.write_text("\n".join(lines) + "\n")
    print(f"  ✅ Written: {env_path}")


def show_current(repo_path: Path = None) -> None:
    """Display current .env values (masked) for all or one repo."""
    repos = [repo_path] if repo_path else ALL_REPOS
    for repo in repos:
        env_path = repo / "config" / ".env"
        name = repo.name if repo != REPO_ROOT else "protean-pursuits"
        if env_path.exists():
            values = read_existing_env(env_path)
            print(f"\n📄 {name}:")
            for key, _, _, secret, _ in FIELDS:
                val = values.get(key, "")
                display = mask(val) if secret else (val or "(not set)")
                print(f"  {key:<25} {display}")
        else:
            print(f"\n⚠️  {name}: no .env found (run setup_env.py)")


def run_interactive(update: bool = False, target_team: str = None) -> None:
    """Run interactive setup."""
    print("\n" + "="*60)
    print("  Protean Pursuits — Environment Setup")
    print("="*60)

    if target_team:
        target_path = REPO_ROOT / "teams" / target_team
        if not target_path.exists():
            print(f"❌ Team not found: {target_team}")
            sys.exit(1)
        repos_to_write = [target_path]
        print(f"\nSetting up: {target_team} only\n")
    else:
        repos_to_write = ALL_REPOS
        print(f"\nThis will write config/.env to {len(repos_to_write)} repos:")
        print(f"  protean-pursuits + {len(TEAMS)} team submodules\n")

    # Read existing values from protean-pursuits .env as defaults
    existing = read_existing_env(REPO_ROOT / "config" / ".env")

    print("Enter values below. Press Enter to keep existing/default value.\n")

    # Collect shared values
    values = {}
    print("── LLM Configuration ──────────────────────────────────────")
    for key, prompt, default, secret, required in FIELDS[:3]:
        values[key] = prompt_value(key, prompt, default, secret, existing.get(key, ""))

    print("\n── Human-in-the-Loop Notifications (Outlook) ──────────────")
    for key, prompt, default, secret, required in FIELDS[3:7]:
        values[key] = prompt_value(key, prompt, default, secret, existing.get(key, ""))

    print("\n── GitHub ──────────────────────────────────────────────────")
    for key, prompt, default, secret, required in FIELDS[7:9]:
        values[key] = prompt_value(key, prompt, default, secret, existing.get(key, ""))

    print("\n── Observability (optional) ────────────────────────────────")
    for key, prompt, default, secret, required in FIELDS[9:]:
        values[key] = prompt_value(key, prompt, default, secret, existing.get(key, ""))

    # Write to all target repos
    print(f"\n── Writing .env files ──────────────────────────────────────")
    for repo in repos_to_write:
        name = repo.name if repo != REPO_ROOT else "protean-pursuits"
        team_key = name if name in TEAM_EXTRA_FIELDS else None

        # Collect team-specific extras if needed
        repo_values = dict(values)
        extra = TEAM_EXTRA_FIELDS.get(team_key, [])
        if extra and not target_team:
            # Only prompt for extras if doing full setup, not single-team
            pass  # extras are optional, use empty defaults

        write_env(repo, repo_values, extra)

    print(f"\n✅ Setup complete — {len(repos_to_write)} .env file(s) written.")
    print("\n⚠️  Reminder: rotate your GitHub token periodically.")
    print("   Never commit .env files — they are in .gitignore.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Protean Pursuits environment setup"
    )
    parser.add_argument("--update", action="store_true",
                        help="Update existing .env files (re-prompts with current values)")
    parser.add_argument("--show", action="store_true",
                        help="Show current .env values (masked)")
    parser.add_argument("--team", type=str, default=None,
                        help=f"Write .env for one team only: {TEAMS}")
    args = parser.parse_args()

    if args.show:
        repo = REPO_ROOT / "teams" / args.team if args.team else None
        show_current(repo)
    else:
        run_interactive(update=args.update, target_team=args.team)
