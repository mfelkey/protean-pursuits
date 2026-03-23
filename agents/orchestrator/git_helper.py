"""
agents/orchestrator/git_helper.py

Protean Pursuits — Git push helper

Allows any agent to commit and push changes to a project repo
using the GITHUB_TOKEN from config/.env.
"""

import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("config/.env")


def git_push(repo_path: str, commit_message: str,
             branch: str = "main") -> bool:
    """
    Stage all changes, commit, and push to GitHub.
    Uses GITHUB_TOKEN and GITHUB_USERNAME from .env.
    Returns True on success, False on failure.
    """
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME", "mfelkey")

    if not token or token == "your-github-pat-here":
        print("⚠️  GITHUB_TOKEN not set in config/.env — cannot push.")
        return False

    try:
        # Update remote URL to include token
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path, capture_output=True, text=True
        )
        remote_url = result.stdout.strip()

        # Inject token into URL if not already present
        if "@github.com" not in remote_url:
            remote_url = remote_url.replace(
                "https://github.com",
                f"https://{token}@github.com"
            )
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote_url],
                cwd=repo_path, check=True
            )

        # Stage all
        subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)

        # Check if there's anything to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path, capture_output=True, text=True
        )
        if not status.stdout.strip():
            print(f"ℹ️  Nothing to commit in {repo_path}")
            return True

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_message,
             "--author", f"{username} <{username}@users.noreply.github.com>"],
            cwd=repo_path, check=True
        )

        # Push
        subprocess.run(
            ["git", "push", "origin", branch],
            cwd=repo_path, check=True
        )

        print(f"✅ Pushed to GitHub: {repo_path} → {branch}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed: {e}")
        return False


def git_push_artifact(repo_path: str, artifact_path: str,
                       artifact_type: str, project_id: str) -> bool:
    """
    Convenience wrapper — commit and push a single new artifact.
    """
    message = (
        f"[{project_id}] Add {artifact_type} artifact\n\n"
        f"Path: {artifact_path}\n"
        f"Generated: {datetime.utcnow().isoformat()}"
    )
    return git_push(repo_path, message)
