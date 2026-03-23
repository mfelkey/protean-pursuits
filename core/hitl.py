"""
core/hitl.py

Protean Pursuits — Shared Human-in-the-Loop approval gate

Single source of truth for all approval gates across the portfolio.
Teams running under Protean Pursuits use this. Standalone team repos
carry their own copy for independent operation.

Gate types used across teams:
  PRD, REPO_SPINUP, BLOCKER         — Orchestrator / PM
  POST, EMAIL, VIDEO                — Marketing
  STRATEGY, OKR_CYCLE, COMPETITIVE  — Strategy
  LEGAL_REVIEW                       — Legal
  DESIGN_REVIEW                      — Design
  QA_SIGN_OFF                        — QA
  DELIVERABLE                        — Generic
"""

import os
import json
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("config/.env")


def request_human_approval(
    gate_type: str,
    artifact_path: str,
    summary: str,
    timeout_hours: int = 24,
    approval_dir: str = "logs/approvals",
    notify_fn=None
) -> bool:
    """
    Pause execution and notify the human for approval.

    gate_type:     type of gate (POST, EMAIL, PRD, LEGAL_REVIEW, QA_SIGN_OFF, etc.)
    artifact_path: path to the artifact awaiting approval
    summary:       short description of what is being approved
    timeout_hours: hours before auto-timeout (default 24)
    approval_dir:  where to write approval request and response files
    notify_fn:     optional callable(subject, message) — defaults to print-only
                   pass core.notifications.notify_human for full SMS+email

    Returns True if approved, False if rejected or timed out.
    """
    os.makedirs(approval_dir, exist_ok=True)
    approval_id = f"APPROVAL-{uuid.uuid4().hex[:8].upper()}"
    approval_file = f"{approval_dir}/{approval_id}.json"
    response_file = f"{approval_dir}/{approval_id}.response.json"

    approval_request = {
        "approval_id": approval_id,
        "gate_type": gate_type,
        "artifact_path": artifact_path,
        "summary": summary,
        "requested_at": datetime.utcnow().isoformat(),
        "timeout_hours": timeout_hours,
        "status": "PENDING"
    }
    with open(approval_file, "w") as f:
        json.dump(approval_request, f, indent=2)

    message = (
        f"Gate type: {gate_type}\n"
        f"Summary: {summary}\n"
        f"Artifact: {artifact_path}\n"
        f"Approval ID: {approval_id}\n\n"
        f"To approve:\n"
        f'  write {{"decision": "APPROVED"}} to:\n'
        f"  {response_file}\n\n"
        f"To reject:\n"
        f'  write {{"decision": "REJECTED", "reason": "..."}} to:\n'
        f"  {response_file}\n\n"
        f"Timeout: {timeout_hours} hours."
    )

    if notify_fn:
        notify_fn(f"[APPROVAL REQUIRED] {gate_type} — {approval_id}", message)
    else:
        print(f"\n[APPROVAL REQUIRED] {gate_type} — {approval_id}")
        print(message)

    print(f"\n⏸️  [{gate_type}] Waiting for human approval — {approval_id}")
    print(f"   Artifact: {artifact_path}\n")

    elapsed = 0
    timeout = timeout_hours * 3600

    while elapsed < timeout:
        if os.path.exists(response_file):
            with open(response_file) as f:
                response = json.load(f)
            decision = response.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ [{gate_type}] Approved — {approval_id}")
                _log_decision(approval_dir, approval_id, gate_type, "APPROVED",
                              artifact_path)
                return True
            elif decision == "REJECTED":
                reason = response.get("reason", "No reason given")
                print(f"❌ [{gate_type}] Rejected — {approval_id}: {reason}")
                _log_decision(approval_dir, approval_id, gate_type, "REJECTED",
                              artifact_path, reason)
                return False
        time.sleep(30)
        elapsed += 30

    print(f"⏰ [{gate_type}] Timed out after {timeout_hours}h — {approval_id}. NOT proceeding.")
    _log_decision(approval_dir, approval_id, gate_type, "TIMEOUT", artifact_path)
    return False


def _log_decision(approval_dir: str, approval_id: str, gate_type: str,
                  decision: str, artifact_path: str, reason: str = "") -> None:
    log_path = f"{approval_dir}/{approval_id}.log.json"
    with open(log_path, "w") as f:
        json.dump({
            "approval_id": approval_id,
            "gate_type": gate_type,
            "decision": decision,
            "artifact_path": artifact_path,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }, f, indent=2)
