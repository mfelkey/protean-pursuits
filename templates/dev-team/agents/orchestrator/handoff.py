import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
import shutil
from datetime import datetime
from agents.orchestrator.orchestrator import log_event, save_context

# ── Handoff package structure ─────────────────────────────────────────────────

def create_handoff_package(
    context: dict,
    delivering_crew: str,
    receiving_crew: str,
    artifacts: list,
    summary: str,
    acceptance_criteria: list,
    limitations: list = None
) -> dict:
    """
    Build a formal handoff package from one crew to another.
    Returns the handoff package dict.
    """

    package = {
        "handoff_id": f"HO-{context['project_id']}-{delivering_crew}2{receiving_crew}",
        "project_id": context["project_id"],
        "created_at": datetime.utcnow().isoformat(),
        "status": "PENDING_APPROVAL",
        "delivering_crew": delivering_crew,
        "receiving_crew": receiving_crew,
        "summary": summary,
        "artifacts": artifacts,
        "acceptance_criteria": acceptance_criteria,
        "limitations": limitations or [],
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None
    }

    return package


def save_handoff_package(context: dict, package: dict) -> str:
    """
    Write handoff package to GitHub-tracked handoffs directory.
    Returns the file path.
    """

    # Determine directory based on crews involved
    delivering = package["delivering_crew"].lower()
    receiving = package["receiving_crew"].lower()

    if delivering == "ds" and receiving == "dev":
        handoff_dir = "ds/handoffs"
    elif delivering == "dev" and receiving == "ds":
        handoff_dir = "dev/handoffs"
    else:
        handoff_dir = "shared/handoffs"

    os.makedirs(handoff_dir, exist_ok=True)

    filename = f"{handoff_dir}/{package['handoff_id']}.json"
    with open(filename, "w") as f:
        json.dump(package, f, indent=2)

    print(f"📦 Handoff package saved: {filename}")
    return filename


def validate_handoff(package: dict, context: dict) -> tuple:
    """
    Validate that all artifacts exist and acceptance criteria are defined.
    Returns (is_valid: bool, issues: list).
    """

    issues = []

    # Check artifacts exist
    for artifact in package["artifacts"]:
        path = artifact.get("path")
        if path and not os.path.exists(path):
            issues.append(f"Missing artifact: {path}")

    # Check acceptance criteria defined
    if not package["acceptance_criteria"]:
        issues.append("No acceptance criteria defined")

    # Check summary provided
    if not package["summary"] or len(package["summary"]) < 20:
        issues.append("Summary too brief or missing")

    is_valid = len(issues) == 0
    return is_valid, issues


def request_handoff_approval(context: dict, package: dict) -> bool:
    """
    Present handoff package for human approval.
    Returns True if approved, False if rejected.
    """

    print(f"\n{'='*60}")
    print(f"📦 HANDOFF APPROVAL REQUIRED")
    print(f"{'='*60}")
    print(f"Handoff ID:       {package['handoff_id']}")
    print(f"From:             {package['delivering_crew']} Crew")
    print(f"To:               {package['receiving_crew']} Crew")
    print(f"\nSummary:\n{package['summary']}")
    print(f"\nArtifacts:")
    for a in package["artifacts"]:
        print(f"  - {a.get('name')}: {a.get('description')}")
    print(f"\nAcceptance Criteria:")
    for i, c in enumerate(package["acceptance_criteria"], 1):
        print(f"  {i}. {c}")
    if package["limitations"]:
        print(f"\nKnown Limitations:")
        for l in package["limitations"]:
            print(f"  ⚠️  {l}")
    print(f"{'='*60}")

    while True:
        response = input("\nType APPROVE or REJECT: ").strip().upper()
        if response == "APPROVE":
            package["status"] = "APPROVED"
            package["approved_at"] = datetime.utcnow().isoformat()
            log_event(context, f"HANDOFF APPROVED: {package['handoff_id']}")
            save_context(context)
            print(f"\n✅ Handoff approved. {package['receiving_crew']} Crew may proceed.")
            return True
        elif response == "REJECT":
            reason = input("Enter rejection reason: ").strip()
            package["status"] = "REJECTED"
            package["rejected_reason"] = reason
            log_event(context, f"HANDOFF REJECTED: {package['handoff_id']}", reason)
            save_context(context)
            print(f"\n❌ Handoff rejected. Returning to {package['delivering_crew']} Crew.")
            return False
        else:
            print("Please type APPROVE or REJECT.")


def execute_handoff(context: dict, package: dict) -> dict:
    """
    Full handoff workflow:
    1. Validate package
    2. Save to GitHub-tracked directory
    3. Request human approval
    4. Update context with result
    Returns updated context.
    """

    print(f"\n🔄 Initiating handoff: {package['delivering_crew']} → {package['receiving_crew']}")

    # Step 1: Validate
    is_valid, issues = validate_handoff(package, context)
    if not is_valid:
        print(f"\n❌ Handoff validation failed:")
        for issue in issues:
            print(f"   - {issue}")
        log_event(context, "HANDOFF_VALIDATION_FAILED", "; ".join(issues))
        save_context(context)
        return context

    print(f"✅ Handoff package validated.")

    # Step 2: Save package
    package_path = save_handoff_package(context, package)
    log_event(context, "HANDOFF_PACKAGE_SAVED", package_path)

    # Step 3: Human approval
    approved = request_handoff_approval(context, package)

    # Step 4: Update context
    if approved:
        context["handoffs"].append({
            "handoff_id": package["handoff_id"],
            "status": "APPROVED",
            "path": package_path
        })
        # Update status to reflect which crew is now active
        receiving = package["receiving_crew"]
        context["status"] = f"ACTIVE_{receiving}_PHASE2"
        context["next_action"] = f"{receiving}_CREW: Begin work on received artifacts"
    else:
        context["handoffs"].append({
            "handoff_id": package["handoff_id"],
            "status": "REJECTED",
            "reason": package.get("rejected_reason")
        })
        delivering = package["delivering_crew"]
        context["status"] = f"RETURNED_TO_{delivering}"
        context["next_action"] = f"{delivering}_CREW: Address rejection and resubmit handoff"

    save_context(context)
    return context


if __name__ == "__main__":
    # Test with sample project context
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found. Run classify.py first.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    print(f"📂 Loaded context: {logs[0]}")

    # Simulate a DS crew completing analysis and handing off to Dev
    package = create_handoff_package(
        context=context,
        delivering_crew="DS",
        receiving_crew="DEV",
        artifacts=[
            {
                "name": "Cleaned Trip Dataset",
                "description": "dataset cleaned and labeled",
                "path": "ds/data/dataset_clean.csv",
                "type": "dataset"
            },
            {
                "name": "Analysis Report",
                "description": "EDA findings and capture rate recommendations",
                "path": "ds/reports/analysis.md",
                "type": "report"
            },
            {
                "name": "Data Schema",
                "description": "Column definitions and data types for dashboard use",
                "path": "ds/data/schema.json",
                "type": "schema"
            }
        ],
        summary=(
            "The DS Crew has completed analysis of the project dataset. "
            "Key finding: 34% of contracted trips meet criteria for in-house capture. "
            "Estimated annual savings: $420,000. Cleaned dataset and schema are "
            "ready for dashboard development. All artifacts validated."
        ),
        acceptance_criteria=[
            "Dashboard displays trip data filterable by month and trip type",
            "In-house vs contracted breakdown visible at a glance",
            "Loads in under 2 seconds for full dataset",
            "Compatible with cleaned dataset schema provided"
        ],
        limitations=[
            "Dataset covers 2023 only — no multi-year trending possible yet",
            "Mode field has 3% null values — dashboard should handle gracefully"
        ]
    )

    context = execute_handoff(context, package)
