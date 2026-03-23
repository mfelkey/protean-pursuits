"""
core/git_helper.py

Protean Pursuits — Shared git push utility

Used by all team orchestrators when running under Protean Pursuits.
Standalone team repos carry their own copy in agents/orchestrator/git_helper.py.
"""

import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("config/.env")


def git_push(repo_path: str, commit_message: str, branch: str = "main") -> bool:
    """
    Stage all changes, commit, and push to GitHub.
    Uses GITHUB_TOKEN and GITHUB_USERNAME from config/.env.
    """
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME", "mfelkey")

    if not token or token == "your-github-pat-here":
        print("⚠️  GITHUB_TOKEN not set — cannot push.")
        return False

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path, capture_output=True, text=True
        )
        remote_url = result.stdout.strip()
        if "@github.com" not in remote_url:
            remote_url = remote_url.replace(
                "https://github.com",
                f"https://{token}@github.com"
            )
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote_url],
                cwd=repo_path, check=True
            )

        subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path, capture_output=True, text=True
        )
        if not status.stdout.strip():
            print(f"ℹ️  Nothing to commit in {repo_path}")
            return True

        subprocess.run(
            ["git", "commit", "-m", commit_message,
             "--author", f"{username} <{username}@users.noreply.github.com>"],
            cwd=repo_path, check=True
        )
        subprocess.run(
            ["git", "push", "origin", branch],
            cwd=repo_path, check=True
        )
        print(f"✅ Pushed: {repo_path} → {branch}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed: {e}")
        return False


def git_push_submodule(submodule_path: str, commit_message: str) -> bool:
    """Push a submodule and update the parent repo's submodule reference."""
    if not git_push(submodule_path, commit_message):
        return False
    # Update parent repo's submodule pointer
    parent_path = os.path.dirname(os.path.abspath(submodule_path))
    try:
        subprocess.run(["git", "add", submodule_path], cwd=parent_path, check=True)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=parent_path, capture_output=True, text=True
        )
        if status.stdout.strip():
            subprocess.run(
                ["git", "commit", "-m",
                 f"Update submodule pointer: {os.path.basename(submodule_path)}"],
                cwd=parent_path, check=True
            )
            subprocess.run(["git", "push", "origin", "main"],
                           cwd=parent_path, check=True)
            print(f"✅ Submodule pointer updated in parent repo")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Submodule pointer update failed: {e}")
    return True


def submodule_update_all(repo_path: str) -> bool:
    """Pull latest commits for all submodules."""
    try:
        subprocess.run(
            ["git", "submodule", "update", "--remote", "--merge"],
            cwd=repo_path, check=True
        )
        print(f"✅ All submodules updated")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Submodule update failed: {e}")
        return False
