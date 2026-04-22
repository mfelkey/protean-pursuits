"""
core/context.py

Protean Pursuits — Shared project context management

Standardised project context object used by all teams.
Ensures consistent artifact tracking, event logging,
and status management across the portfolio.
"""

import os
import json
import uuid
from datetime import datetime


def create_project_context(
    project_name: str,
    project_type: str,
    team: str,
    scope: str = "PROJECT",
    project_id: str = None,
    parent_context: dict = None
) -> dict:
    """
    Create a standardised project context object.

    project_name:   human-readable name
    project_type:   what this context represents (CAMPAIGN, MATTER, QA_RUN, etc.)
    team:           which team owns this context (DEV, DS, MARKETING, etc.)
    scope:          PROJECT or COMPANY
    project_id:     PROJ-XXXXXXXX identifier (auto-generated if not provided)
    parent_context: parent PP context if running under Protean Pursuits
    """
    ctx = {
        "framework": "protean-pursuits",
        "project_id": project_id or f"PROJ-{uuid.uuid4().hex[:8].upper()}",
        "project_name": project_name,
        "project_type": project_type,
        "team": team,
        "scope": scope,
        "owner": "Protean Pursuits LLC",
        "created_at": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "artifacts": [],
        "blockers": [],
        "events": [],
    }
    if parent_context:
        ctx["parent_project_id"] = parent_context.get("project_id")
        ctx["parent_team"] = parent_context.get("team")
    return ctx


def save_context(context: dict, logs_dir: str = "logs") -> str:
    """Persist context to logs/.

    Defensive against bare contexts that don't have project_id or
    team populated (e.g. ad-hoc invocations via a team lead from a
    bare dict). Falls back to 'unknown' for each missing key rather
    than raising KeyError — logging a warning event is more useful
    than crashing when a lead tries to report a startup failure.
    """
    os.makedirs(logs_dir, exist_ok=True)
    project_id = context.get("project_id") or "unknown"
    team = context.get("team") or "unknown"
    path = f"{logs_dir}/{project_id}_{team}.json"
    with open(path, "w") as f:
        json.dump(context, f, indent=2)
    return path


def log_event(context: dict, event_type: str,
              detail: str = "", logs_dir: str = "logs") -> None:
    """Append a timestamped event to context and persist.

    Defensively initializes context["events"] if the caller passed a
    context that hasn't been through the full orchestrator init
    (e.g. ad-hoc invocations via a team lead from a bare dict).
    """
    if "events" not in context:
        context["events"] = []
    context["events"].append({
        "event_type": event_type,
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_context(context, logs_dir)


def add_artifact(context: dict, name: str, artifact_type: str,
                 path: str, created_by: str,
                 status: str = "PENDING_REVIEW",
                 metadata: dict = None) -> None:
    """Register an artifact in the project context."""
    entry = {
        "name": name,
        "type": artifact_type,
        "path": path,
        "status": status,
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat(),
    }
    if metadata:
        entry.update(metadata)
    if "artifacts" not in context:
        context["artifacts"] = []
    context["artifacts"].append(entry)


def add_blocker(context: dict, blocker_id: str, severity: str,
                description: str, owner: str) -> None:
    """Register a blocker in the project context."""
    if "blockers" not in context:
        context["blockers"] = []
    context["blockers"].append({
        "blocker_id": blocker_id,
        "severity": severity,
        "description": description,
        "owner": owner,
        "raised_at": datetime.utcnow().isoformat(),
        "status": "OPEN"
    })


def load_context(project_id: str, team: str,
                 logs_dir: str = "logs") -> dict:
    """Load a saved project context."""
    path = f"{logs_dir}/{project_id}_{team}.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Context not found: {path}")
    with open(path) as f:
        return json.load(f)


def get_latest_context(logs_dir: str = "logs") -> dict:
    """Load the most recently modified context file."""
    import glob
    files = sorted(glob.glob(f"{logs_dir}/PROJ-*.json"),
                   key=os.path.getmtime, reverse=True)
    if not files:
        raise FileNotFoundError("No project contexts found in logs/")
    with open(files[0]) as f:
        return json.load(f)
