"""
core/context_loader.py

Shared context resolution utility for all PP team flows and agent flows.

Resolution order (first match wins):
  1. project name  → output/<project>/context.json
  2. context_file  → load file contents as string
  3. context_str   → use inline string directly
  4. None          → return empty dict, log warning

Usage:
    from core.context_loader import load_context

    context = load_context(
        project=args.project,
        context_file=args.context_file,
        context_str=args.context,
    )
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve the repo root so output/ paths work regardless of cwd
# ---------------------------------------------------------------------------
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parent.parent  # core/ → repo root


def load_context(
    project: Optional[str] = None,
    context_file: Optional[str] = None,
    context_str: Optional[str] = None,
) -> dict:
    """
    Resolve and return a context dict.

    Returns a dict with at minimum:
        {
            "project": <name or None>,
            "raw": <string content or "">,
            "data": <parsed JSON dict or {}>,
            "source": <"project_json" | "file" | "inline" | "none">,
        }
    """

    # ------------------------------------------------------------------
    # 1. Project name → output/<project>/context.json
    # ------------------------------------------------------------------
    if project:
        context_path = _REPO_ROOT / "output" / project / "context.json"
        if context_path.exists():
            try:
                with open(context_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Context loaded from {context_path}")
                return {
                    "project": project,
                    "raw": json.dumps(data, indent=2),
                    "data": data,
                    "source": "project_json",
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {context_path}: {e}")
                sys.exit(f"[context_loader] ERROR: {context_path} is not valid JSON — {e}")
        else:
            logger.warning(
                f"--project '{project}' specified but no context.json found at "
                f"{context_path}. Falling through to context_file / context_str."
            )

    # ------------------------------------------------------------------
    # 2. Context file path
    # ------------------------------------------------------------------
    if context_file:
        cf = Path(context_file).expanduser().resolve()
        if cf.exists():
            try:
                raw = cf.read_text(encoding="utf-8")
                # Attempt JSON parse; fall back to plain string
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {"content": raw}
                logger.info(f"Context loaded from file: {cf}")
                return {
                    "project": project,
                    "raw": raw,
                    "data": data,
                    "source": "file",
                }
            except OSError as e:
                sys.exit(f"[context_loader] ERROR: Cannot read {cf} — {e}")
        else:
            sys.exit(f"[context_loader] ERROR: Context file not found: {cf}")

    # ------------------------------------------------------------------
    # 3. Inline context string
    # ------------------------------------------------------------------
    if context_str:
        try:
            data = json.loads(context_str)
        except json.JSONDecodeError:
            data = {"content": context_str}
        logger.info("Context loaded from inline --context string.")
        return {
            "project": project,
            "raw": context_str,
            "data": data,
            "source": "inline",
        }

    # ------------------------------------------------------------------
    # 4. No context provided
    # ------------------------------------------------------------------
    logger.warning(
        "No context provided (no --project, --context-file, or --context). "
        "Running with empty context — agent output quality may be reduced."
    )
    return {
        "project": project,
        "raw": "",
        "data": {},
        "source": "none",
    }


def require_artifact(context: dict, artifact_key: str, flag_hint: str) -> str:
    """
    Assert that a required upstream artifact exists in context.data.
    Exits with a clear error message if missing.

    Usage:
        tad = require_artifact(context, "TAD", "--project <name> or --context-file <path>")
    """
    value = context.get("data", {}).get(artifact_key)
    if not value:
        sys.exit(
            f"[context_loader] ERROR: Required artifact '{artifact_key}' not found in context.\n"
            f"  Hint: supply it via {flag_hint}"
        )
    return value


def save_output(content: str, project: Optional[str], team: str, filename: str) -> Optional[Path]:
    """
    Write output to output/<project>/<team>/<filename>.
    Returns the path written, or None if no project is set.
    """
    if not project:
        return None
    out_dir = _REPO_ROOT / "output" / project / team
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    out_path.write_text(content, encoding="utf-8")
    logger.info(f"Output saved to {out_path}")
    return out_path


def save_agent_direct_output(content: str, project: Optional[str], agent_key: str) -> Optional[Path]:
    """
    Write agent-direct output to output/<project>/agent_direct/<agent_key>_<timestamp>.md.
    Returns the path written, or None if no project is set.
    """
    if not project:
        return None
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = _REPO_ROOT / "output" / project / "agent_direct"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{agent_key}_{timestamp}.md"
    out_path.write_text(content, encoding="utf-8")
    logger.info(f"Agent direct output saved to {out_path}")
    return out_path
