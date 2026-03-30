"""agents/leads/hr/hr_lead.py — HR Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow


def build_hr_lead():
    return build_team_lead(
        team_name="hr-team",
        role="HR Team Lead",
        goal=(
            "Deliver people operations outputs — recruiting, onboarding, "
            "performance frameworks, HR policies, culture initiatives, and "
            "benefits design — by coordinating the embedded hr-team orchestrator."
        ),
        backstory=(
            "You are a Chief People Officer with 18 years of experience building "
            "people functions at high-growth technology companies. You are the PP "
            "interface to the hr-team — you translate project and team-expansion "
            "briefs into hr-team flow invocations and report people-ops "
            "deliverables back to the Project Manager. "
            "You work with a humans-only workforce model. You coordinate "
            "cross-team flags to Legal, Finance, Strategy, and QA proactively. "
            "All outputs require human approval before any action affecting "
            "a person is taken."
        )
    )


def run_hr_deliverable(context: dict, mode: str,
                       agent: str = None, brief: str = "") -> dict:
    """Invoke the hr-team flow for a given mode."""
    args = ["--mode", mode, "--name", context["project_name"]]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if agent:
        args += ["--agent", agent]
    if brief:
        args += ["--brief", brief]
    return invoke_team_flow("hr-team", "flows/hr_flow.py", args, context)
