"""agents/leads/qa/qa_lead.py — QA Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow

def build_qa_lead():
    return build_team_lead(
        team_name="qa-team",
        role="QA Team Lead",
        goal="Ensure nothing ships without quality sign-off by coordinating the embedded qa-team orchestrator.",
        backstory=(
            "You are a VP of Quality Assurance with 18 years of experience. "
            "You interface between PP project requirements and the qa-team — "
            "translating quality requirements into QA flow invocations and "
            "reporting PASS/CONDITIONAL/FAIL verdicts back to the Project Manager. "
            "Nothing ships without your team's sign-off."
        )
    )

def run_qa_deliverable(context: dict, mode: str,
                        target: str = "dev",
                        agents: str = None,
                        brief: str = "") -> dict:
    args = ["--mode", mode, "--name", context["project_name"],
            "--target", target]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if agents:
        args += ["--agents", agents]
    if brief:
        args += ["--brief", brief]
    return invoke_team_flow("qa-team", "flows/qa_flow.py", args, context)
