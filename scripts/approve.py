#!/usr/bin/env python3
"""
scripts/approve.py

Protean Pursuits — Interactive approval CLI

Lists all pending approval requests and lets you approve
or reject them interactively. Run in a separate terminal
while a flow is executing.

Usage:
    python3.11 scripts/approve.py           # interactive — shows pending, prompts
    python3.11 scripts/approve.py --watch   # auto-refresh every 10s
    python3.11 scripts/approve.py --list    # list all (pending + resolved)
    python3.11 scripts/approve.py --approve APPROVAL-XXXXXXXX
    python3.11 scripts/approve.py --reject  APPROVAL-XXXXXXXX "reason"
"""

import os
import json
import time
import argparse
import glob
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPROVAL_DIR = REPO_ROOT / "logs" / "approvals"


def find_pending() -> list:
    """Return all pending approval requests sorted by time."""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    requests = []
    for path in sorted(APPROVAL_DIR.glob("APPROVAL-*.json")):
        # Skip log files and response files
        if ".log." in path.name or ".response." in path.name:
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            response_path = path.with_suffix("").with_suffix(".response.json")
            # Skip if already responded
            if response_path.exists():
                continue
            data["_path"] = str(path)
            data["_response_path"] = str(response_path)
            requests.append(data)
        except Exception:
            continue
    return requests


def find_all() -> list:
    """Return all approval requests with their resolution status."""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    requests = []
    for path in sorted(APPROVAL_DIR.glob("APPROVAL-*.json")):
        if ".log." in path.name or ".response." in path.name:
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            response_path = path.with_suffix("").with_suffix(".response.json")
            if response_path.exists():
                with open(response_path) as f:
                    resp = json.load(f)
                data["_decision"] = resp.get("decision", "UNKNOWN")
                data["_reason"] = resp.get("reason", "")
            else:
                data["_decision"] = "PENDING"
            data["_path"] = str(path)
            requests.append(data)
        except Exception:
            continue
    return requests


def write_response(response_path: str, decision: str, reason: str = "") -> None:
    """Write an approval response file."""
    response = {"decision": decision.upper()}
    if reason:
        response["reason"] = reason
    with open(response_path, "w") as f:
        json.dump(response, f, indent=2)


def format_age(timestamp: str) -> str:
    """Format how long ago a request was made."""
    try:
        dt = datetime.fromisoformat(timestamp)
        delta = datetime.utcnow() - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        else:
            return f"{seconds // 3600}h ago"
    except Exception:
        return "unknown"


def print_pending(requests: list) -> None:
    """Print pending requests in a readable format."""
    if not requests:
        print("\n  ✅ No pending approvals.\n")
        return

    print(f"\n  {'─'*60}")
    print(f"  {'ID':<25} {'TYPE':<15} {'AGE':<10} SUMMARY")
    print(f"  {'─'*60}")
    for i, req in enumerate(requests, 1):
        age = format_age(req.get("requested_at", ""))
        gate = req.get("gate_type", "UNKNOWN")
        summary = req.get("summary", "")[:45]
        approval_id = req.get("approval_id", "UNKNOWN")
        print(f"  [{i}] {approval_id:<22} {gate:<15} {age:<10} {summary}")
    print(f"  {'─'*60}\n")


def interactive_mode(watch: bool = False) -> None:
    """Main interactive approval loop."""
    print("\n" + "="*62)
    print("  Protean Pursuits — Approval Manager")
    print("="*62)

    if watch:
        print("  Watch mode — refreshing every 10 seconds. Ctrl+C to exit.\n")

    while True:
        pending = find_pending()
        print_pending(pending)

        if not pending:
            if watch:
                print("  Waiting for new approvals...", end="\r")
                time.sleep(10)
                print(" " * 40, end="\r")
                continue
            else:
                break

        if watch:
            # In watch mode, auto-prompt for each pending item
            for req in pending:
                _prompt_approval(req)
            time.sleep(5)
            continue
        else:
            # Interactive mode — prompt once then exit
            for req in pending:
                _prompt_approval(req)
            # Check if more appeared
            remaining = find_pending()
            if remaining:
                print(f"  {len(remaining)} more pending. Run again to process.\n")
            break


def _prompt_approval(req: dict) -> None:
    """Prompt user to approve or reject a single request."""
    approval_id = req.get("approval_id", "UNKNOWN")
    gate_type = req.get("gate_type", "UNKNOWN")
    summary = req.get("summary", "No summary")
    artifact = req.get("artifact_path", "")
    age = format_age(req.get("requested_at", ""))

    print(f"  ┌─ {approval_id}")
    print(f"  │  Type:     {gate_type}")
    print(f"  │  Summary:  {summary}")
    print(f"  │  Artifact: {artifact}")
    print(f"  │  Waiting:  {age}")
    print(f"  └─")

    while True:
        try:
            choice = input("  Approve? [y]es / [n]o / [s]kip / [v]iew artifact: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting.")
            return

        if choice in ("y", "yes"):
            write_response(req["_response_path"], "APPROVED")
            print(f"  ✅ APPROVED — {approval_id}\n")
            break
        elif choice in ("n", "no"):
            try:
                reason = input("  Reason (optional): ").strip()
            except (KeyboardInterrupt, EOFError):
                reason = ""
            write_response(req["_response_path"], "REJECTED", reason)
            print(f"  ❌ REJECTED — {approval_id}\n")
            break
        elif choice in ("s", "skip"):
            print(f"  ⏭️  Skipped — {approval_id}\n")
            break
        elif choice in ("v", "view"):
            if artifact and os.path.exists(artifact):
                print(f"\n  {'─'*60}")
                with open(artifact) as f:
                    content = f.read()
                # Show first 50 lines
                lines = content.splitlines()[:50]
                for line in lines:
                    print(f"  {line}")
                if len(content.splitlines()) > 50:
                    print(f"  ... ({len(content.splitlines()) - 50} more lines)")
                print(f"  {'─'*60}\n")
            else:
                print(f"  ⚠️  Artifact not found: {artifact}\n")
        else:
            print("  Please enter y, n, s, or v.")


def list_all() -> None:
    """List all approvals with their status."""
    all_requests = find_all()
    if not all_requests:
        print("\n  No approval records found.\n")
        return

    print(f"\n  {'─'*70}")
    print(f"  {'ID':<25} {'TYPE':<15} {'STATUS':<12} SUMMARY")
    print(f"  {'─'*70}")
    for req in all_requests:
        decision = req.get("_decision", "PENDING")
        icon = {"APPROVED": "✅", "REJECTED": "❌", "PENDING": "⏳"}.get(decision, "❓")
        gate = req.get("gate_type", "UNKNOWN")
        summary = req.get("summary", "")[:35]
        approval_id = req.get("approval_id", "UNKNOWN")
        print(f"  {icon} {approval_id:<23} {gate:<15} {decision:<12} {summary}")
    print(f"  {'─'*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Protean Pursuits approval manager"
    )
    parser.add_argument("--watch", action="store_true",
                        help="Auto-refresh every 10s and prompt for new approvals")
    parser.add_argument("--list", action="store_true",
                        help="List all approvals (pending + resolved)")
    parser.add_argument("--approve", type=str, metavar="APPROVAL-ID",
                        help="Approve a specific request by ID")
    parser.add_argument("--reject", type=str, metavar="APPROVAL-ID",
                        help="Reject a specific request by ID")
    parser.add_argument("--reason", type=str, default="",
                        help="Reason for rejection (used with --reject)")
    args = parser.parse_args()

    if args.list:
        list_all()
    elif args.approve:
        # Find and approve by ID
        pending = find_all()
        match = [r for r in pending if r.get("approval_id") == args.approve]
        if not match:
            print(f"❌ Approval ID not found: {args.approve}")
        else:
            write_response(match[0]["_response_path"], "APPROVED")
            print(f"✅ APPROVED — {args.approve}")
    elif args.reject:
        pending = find_all()
        match = [r for r in pending if r.get("approval_id") == args.reject]
        if not match:
            print(f"❌ Approval ID not found: {args.reject}")
        else:
            write_response(match[0]["_response_path"], "REJECTED", args.reason)
            print(f"❌ REJECTED — {args.reject}")
    else:
        interactive_mode(watch=args.watch)
