"""agents/leads/ds/ds_lead.py — DS Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow

def build_ds_lead():
    return build_team_lead(
        team_name="ds-team",
        role="DS Team Lead",
        goal="Deliver ML models, data pipelines, and analytical outputs by coordinating the embedded ds-team orchestrator.",
        backstory=(
            "You are a Lead Data Scientist with 12 years of experience building "
            "production ML systems. You interface between PP project requirements "
            "and the ds-team — translating analytical needs into ds-team flow "
            "invocations and reporting model status back to the Project Manager."
        )
    )

def run_ds_deliverable(context: dict, mode: str, brief: str = "") -> dict:
    args = ["--mode", mode, "--name", context["project_name"]]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if brief:
        args += ["--brief", brief]
    return invoke_team_flow("ds-team", "flows/ds_flow.py", args, context)
