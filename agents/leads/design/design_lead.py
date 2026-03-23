"""agents/leads/design/design_lead.py — Design Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow

def build_design_lead():
    return build_team_lead(
        team_name="design-team",
        role="Design Team Lead",
        goal="Deliver portfolio-wide design outputs by coordinating the embedded design-team orchestrator.",
        backstory=(
            "You are a Design Director with 18 years of experience. You interface "
            "between PP project requirements and the design-team — translating "
            "product and brand needs into design flow invocations and reporting "
            "design deliverables back to the Project Manager."
        )
    )

def run_design_deliverable(context: dict, mode: str,
                            agent: str = None,
                            brief: str = "") -> dict:
    args = ["--mode", mode, "--name", context["project_name"]]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if agent:
        args += ["--agent", agent]
    if brief:
        args += ["--brief", brief]
    return invoke_team_flow("design-team", "flows/design_flow.py",
                            args, context)
