"""agents/leads/legal/legal_lead.py — Legal Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow

def build_legal_lead():
    return build_team_lead(
        team_name="legal-team",
        role="Legal Team Lead",
        goal="Manage legal risk and produce legal outputs by coordinating the embedded legal-team orchestrator.",
        backstory=(
            "You are a General Counsel equivalent with 20 years of experience. "
            "You interface between PP project requirements and the legal-team — "
            "translating legal needs into legal flow invocations and reporting "
            "risk levels and required actions back to the Project Manager."
        )
    )

def run_legal_deliverable(context: dict, mode: str,
                           doc_type: str = None,
                           jurisdiction: str = "US",
                           industry: str = None,
                           brief: str = "") -> dict:
    args = ["--mode", mode, "--name", context["project_name"],
            "--jurisdiction", jurisdiction]
    if doc_type:
        args += ["--type", doc_type]
    if industry:
        args += ["--industry", industry]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if brief:
        args += ["--brief", brief]
    return invoke_team_flow("legal-team", "flows/legal_flow.py", args, context)
