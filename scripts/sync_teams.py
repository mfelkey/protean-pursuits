"""
scripts/sync_teams.py

Protean Pursuits — Submodule sync utility

Usage:
    python scripts/sync_teams.py              # update all teams to latest
    python scripts/sync_teams.py marketing-team  # update one team
    python scripts/sync_teams.py --status     # show current submodule state
"""

import sys
import subprocess
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEAMS = [
    "dev-team", "ds-team", "marketing-team", "strategy-team",
    "legal-team", "design-team", "qa-team"
]


def show_status():
    print("\n📋 Submodule status:")
    result = subprocess.run(
        ["git", "submodule", "status"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    for line in result.stdout.strip().split("\n"):
        prefix = line[0] if line else " "
        icon = {"+" : "🔄 behind", "-": "⚠️  not init", "U": "❌ conflict",
                " ": "✅ current"}.get(prefix, "❓")
        print(f"  {icon}  {line[1:].strip()}")


def sync_all():
    print("\n🔄 Pulling latest from all team submodules...")
    result = subprocess.run(
        ["git", "submodule", "update", "--remote", "--merge"],
        cwd=REPO_ROOT, capture_output=False, text=True
    )
    if result.returncode == 0:
        print("✅ All submodules updated")
        _commit_pointer_update("Update all team submodule pointers to latest")
    else:
        print("❌ Submodule update failed")


def sync_one(team_name: str):
    if team_name not in TEAMS:
        print(f"❌ Unknown team: {team_name}. Options: {TEAMS}")
        return
    team_path = os.path.join(REPO_ROOT, "teams", team_name)
    print(f"\n🔄 Pulling latest: {team_name}")
    subprocess.run(["git", "pull", "origin", "main"],
                   cwd=team_path, check=True)
    _commit_pointer_update(f"Update submodule pointer: {team_name}")
    print(f"✅ {team_name} updated")


def _commit_pointer_update(message: str):
    subprocess.run(["git", "add", "teams/"], cwd=REPO_ROOT)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if status.stdout.strip():
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=REPO_ROOT
        )
        print(f"📝 Committed: {message}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args == ["--status"]:
        show_status()
        if not args:
            sync_all()
    elif len(args) == 1 and not args[0].startswith("--"):
        sync_one(args[0])
    else:
        print(__doc__)
