"""agents/leads/dev/dev_lead.py — Dev Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow

def build_dev_lead():
    return build_team_lead(
        team_name="dev-team",
        role="Dev Team Lead",
        goal="Deliver production-ready software on time and to spec by coordinating the embedded dev-team orchestrator.",
        backstory=(
            "You are a Principal Engineer and Engineering Lead with 15 years of "
            "experience shipping production software. You are the PP interface to "
            "the dev-team — you translate project briefs into dev-team flow "
            "invocations and report build status back to the Project Manager."
        )
    )

def run_dev_deliverable(context: dict, mode: str, brief: str = "") -> dict:
    """Invoke the dev-team flow for a given mode."""
    args = ["--mode", mode, "--name", context["project_name"]]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if brief:
        args += ["--brief", brief]
    return invoke_team_flow("dev-team", "flows/dev_flow.py", args, context)
