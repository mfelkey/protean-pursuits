"""
Context Manager — agents/orchestrator/context_manager.py

Bridge between the orchestrator's project context and smart_extract.
Provides high-level functions that agents call instead of manual file reads.

Usage in any agent:
    from agents.orchestrator.context_manager import (
        load_agent_context, format_context_for_prompt, on_artifact_saved
    )

    ctx = load_agent_context(context, "backend_dev", ["TIP", "TAD", "MTP", "TAR"])
    prompt_context = format_context_for_prompt(ctx)
"""

import os
from typing import Optional

try:
    from agents.utils.smart_extract import (
        get_context, get_multi_context, index_artifact
    )
except ImportError:
    # Fallback if smart_extract not yet available
    import sys
    sys.path.insert(0, os.path.expanduser("~/dev-team"))
    from agents.utils.smart_extract import (
        get_context, get_multi_context, index_artifact
    )


# ═══════════════════════════════════════════════════════════════════
#  ORCHESTRATOR INTEGRATION
# ═══════════════════════════════════════════════════════════════════

def _find_artifact_path(context: dict, artifact_type: str) -> Optional[str]:
    """
    Find the file path for an artifact type in the project context.

    Searches the artifacts array for the most recent artifact of the
    given type. Returns the path or None if not found.
    """
    path = None
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        # Flexible matching: "BIR" matches "BIR", "BIR-R", etc.
        if atype == artifact_type or atype.startswith(artifact_type):
            candidate = artifact.get("path", "")
            if candidate and os.path.exists(candidate):
                path = candidate  # Take the last (most recent) match
    return path


def load_agent_context(context: dict, consumer: str,
                       artifact_types: list,
                       max_chars_per_artifact: int = 6000) -> dict:
    """
    Load smart-extracted context for an agent from the project.

    This is the main function agents call. It:
      1. Finds each artifact's file path from the project context
      2. Extracts only the sections the consumer agent needs
      3. Returns a dict of {artifact_type: extracted_text}

    Args:
        context: The project context dict (from PROJ-*.json)
        consumer: Agent ID (e.g., "backend_dev", "pen_test")
        artifact_types: List of artifact type codes to load
                       (e.g., ["TIP", "TAD", "MTP", "TAR"])
        max_chars_per_artifact: Max chars per artifact (default 6000)

    Returns:
        Dict of {artifact_type: extracted_text}
        Missing artifacts are silently skipped.
    """
    project_id = context.get("project_id", "")

    # Build the artifacts dict: {type: path}
    artifacts = {}
    for atype in artifact_types:
        path = _find_artifact_path(context, atype)
        if path:
            artifacts[atype] = path

    # Extract using smart_extract
    return get_multi_context(
        artifacts=artifacts,
        consumer=consumer,
        project_id=project_id,
        max_chars_per_artifact=max_chars_per_artifact
    )


def format_context_for_prompt(ctx: dict, labels: dict = None) -> str:
    """
    Format extracted context into a prompt-ready string.

    Takes the dict from load_agent_context and produces labeled
    sections suitable for insertion into a Task description.

    Args:
        ctx: Dict from load_agent_context {artifact_type: text}
        labels: Optional override labels {artifact_type: "DISPLAY NAME"}

    Returns:
        Formatted string with labeled sections.
    """
    default_labels = {
        "PRD": "PRODUCT REQUIREMENTS DOCUMENT (PRD)",
        "BAD": "BUSINESS ANALYSIS DOCUMENT (BAD)",
        "SPRINT_PLAN": "SPRINT PLAN",
        "TAD": "TECHNICAL ARCHITECTURE DOCUMENT (TAD)",
        "SRR": "SECURITY REVIEW REPORT (SRR)",
        "UXD": "USER EXPERIENCE DOCUMENT (UXD)",
        "CONTENT_GUIDE": "UI CONTENT GUIDE",
        "TIP": "TECHNICAL IMPLEMENTATION PLAN (TIP)",
        "PBD": "PERFORMANCE BUDGET DOCUMENT (PBD)",
        "MTP": "MASTER TEST PLAN (MTP)",
        "TAR": "TEST AUTOMATION REPORT (TAR)",
        "BIR": "BACKEND IMPLEMENTATION REPORT (BIR)",
        "FIR": "FRONTEND IMPLEMENTATION REPORT (FIR)",
        "DBAR": "DATABASE ADMINISTRATION REPORT (DBAR)",
        "DIR": "DEVOPS IMPLEMENTATION REPORT (DIR)",
        "DSKR": "DESKTOP APPLICATION REPORT (DSKR)",
        "DXR": "DEVELOPER EXPERIENCE REPORT (DXR)",
        "PTR": "PENETRATION TEST REPORT (PTR)",
        "SAR": "SCALABILITY ARCHITECTURE REVIEW (SAR)",
        "PAR": "PERFORMANCE AUDIT REPORT (PAR)",
        "AAR": "ACCESSIBILITY AUDIT REPORT (AAR)",
        "LCR": "LICENSE COMPLIANCE REPORT (LCR)",
        "VERIFY": "VERIFICATION REPORT",
        "MUXD": "MOBILE UX DOCUMENT (MUXD)",
        "IIR": "iOS IMPLEMENTATION REPORT (IIR)",
        "AIR": "ANDROID IMPLEMENTATION REPORT (AIR)",
        "RNAD_P1": "REACT NATIVE ARCHITECTURE (PART 1)",
        "RNAD_P2": "REACT NATIVE ARCHITECTURE (PART 2)",
        "RN_GUIDE": "REACT NATIVE IMPLEMENTATION GUIDE",
        "MDIR": "MOBILE DEVOPS REPORT (MDIR)",
        "MOBILE_TEST_PLAN": "MOBILE TEST PLAN",
        "MOBILE_PTR": "MOBILE PENETRATION TEST REPORT",
        "MOBILE_SAR": "MOBILE SCALABILITY REVIEW",
        "MOBILE_VERIFY": "MOBILE VERIFICATION REPORT",
    }

    if labels:
        default_labels.update(labels)

    parts = []
    for atype, text in ctx.items():
        if text and text.strip():
            label = default_labels.get(atype, atype)
            parts.append(f"=== {label} ===\n{text}")

    return "\n\n".join(parts)


def on_artifact_saved(context: dict, artifact_type: str, filepath: str):
    """
    Hook to call after an agent saves an artifact.

    Indexes the artifact into ChromaDB for semantic search by
    downstream agents. Idempotent — safe to call multiple times.

    Args:
        context: Project context dict
        artifact_type: Type code (e.g., "BIR", "TAD")
        filepath: Path to the saved artifact file
    """
    project_id = context.get("project_id", "")
    if project_id and filepath and os.path.exists(filepath):
        try:
            index_artifact(filepath, artifact_type, project_id)
        except Exception:
            # ChromaDB indexing is optional — don't crash the agent
            pass


def index_project_artifacts(context: dict):
    """
    Bulk index all artifacts in a project into ChromaDB.

    Call this once when loading a project to ensure all existing
    artifacts are indexed. Idempotent.
    """
    project_id = context.get("project_id", "")
    if not project_id:
        return

    count = 0
    for artifact in context.get("artifacts", []):
        atype = artifact.get("type", "")
        path = artifact.get("path", "")
        if atype and path and os.path.exists(path):
            try:
                index_artifact(path, atype, project_id)
                count += 1
            except Exception:
                pass

    return count
