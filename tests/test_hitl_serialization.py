"""
tests/test_hitl_serialization.py

Phase 4 follow-up — HITL gate machinery must tolerate pathlib.Path
objects in approval payloads (and any context data passed to
json.dump). Caught during video-team activation on 2026-04-22:

    ERROR | HITL gate error: Object of type PosixPath is not JSON serializable
    ERROR | [VIDEO_TOOL_SELECTION] Rejected or timed out. Pipeline halted.

Root cause: `save_output()` returns a Path; the flow passed it
unchanged to `request_human_approval(artifact_path=...)`, which
put it in a dict handed to `json.dump()` with no fallback.

Two-layer defense is applied:
  - Callsite coerces to str() before passing (primary fix)
  - HITL gate uses json.dump(..., default=str) (defensive net)

This test enforces the defensive net with a static AST scan:
every json.dump() in the HITL code paths must have default=str.
"""
import ast
import json
import os
import tempfile
from pathlib import Path

import pytest

UMBRELLA_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------
# Behavioral test — core/hitl.py's json.dump actually tolerates Path
# ------------------------------------------------------------------------

def test_core_hitl_request_serializes_path_artifact(tmp_path, monkeypatch):
    """request_human_approval must write the approval file cleanly
    when artifact_path happens to be a Path object (not just str)."""
    monkeypatch.chdir(tmp_path)
    os.environ.setdefault("TIER1_MODEL", "ollama/qwen3:32b")

    import sys
    sys.path.insert(0, str(UMBRELLA_ROOT))
    from core import hitl

    # Deliberately pass a Path (not a str). Before the fix this
    # would raise TypeError from json.dumps inside request_human_approval.
    # We can't actually wait for a response in a unit test, so we just
    # verify the approval file gets written (which is the line that was
    # crashing).
    artifact = Path(tmp_path) / "brief.md"
    artifact.write_text("test")

    # Immediately reject via pre-written response to avoid the long wait
    import threading
    import time

    approval_dir = tmp_path / "logs" / "approvals"

    def _auto_reject():
        # Wait for the approval file to appear, then write a rejection
        for _ in range(20):
            if approval_dir.exists():
                files = list(approval_dir.glob("APPROVAL-*.json"))
                if files:
                    approval_id = files[0].stem
                    (approval_dir / f"{approval_id}.response.json").write_text(
                        json.dumps({"decision": "REJECTED", "reason": "test"}))
                    return
            time.sleep(0.1)

    t = threading.Thread(target=_auto_reject, daemon=True)
    t.start()

    # This call should NOT raise — the fix means default=str handles Path.
    result = hitl.request_human_approval(
        gate_type="TEST",
        artifact_path=artifact,  # <-- a Path, not a str
        summary="test summary",
        timeout_hours=1,
        approval_dir=str(approval_dir),
    )

    # Returns False (we rejected), but the key assertion is that NO
    # TypeError was raised during json.dump.
    assert result is False


# ------------------------------------------------------------------------
# Static AST scan — every json.dump in HITL code must have default=
# ------------------------------------------------------------------------

# Files whose json.dump calls are HITL/context-adjacent and therefore
# must tolerate Path-like values.
HITL_FILES = [
    UMBRELLA_ROOT / "core" / "hitl.py",
    UMBRELLA_ROOT / "templates" / "dev-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "dev-team" / "agents" / "orchestrator" / "handoff.py",
    UMBRELLA_ROOT / "templates" / "ds-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "design-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "legal-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "marketing-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "qa-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "strategy-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "video-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "hr-team" / "agents" / "orchestrator" / "orchestrator.py",
    UMBRELLA_ROOT / "templates" / "hr-team" / "agents" / "hr" / "orchestrator" / "orchestrator.py",
]


def _json_dump_calls_missing_default(source: str) -> list[int]:
    """Return line numbers of json.dump() calls missing default=."""
    tree = ast.parse(source)
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Match `json.dump`
        if not (isinstance(func, ast.Attribute) and
                func.attr == "dump" and
                isinstance(func.value, ast.Name) and
                func.value.id == "json"):
            continue
        kwarg_names = {kw.arg for kw in node.keywords if kw.arg}
        if "default" not in kwarg_names:
            offenders.append(node.lineno)
    return offenders


@pytest.mark.parametrize("path", HITL_FILES,
                          ids=[str(p.relative_to(UMBRELLA_ROOT))
                               for p in HITL_FILES])
def test_every_json_dump_in_hitl_file_has_default_str(path):
    """Every json.dump() in a HITL-adjacent file must pass default=str."""
    if not path.exists():
        pytest.skip(f"File not present: {path}")
    source = path.read_text()
    offenders = _json_dump_calls_missing_default(source)
    assert not offenders, (
        f"{path.relative_to(UMBRELLA_ROOT)}: json.dump() calls at lines "
        f"{offenders} are missing 'default=str'. Non-str types like "
        f"pathlib.Path will crash serialization."
    )
