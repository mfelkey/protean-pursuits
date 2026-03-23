"""agents/leads/strategy/strategy_lead.py — Strategy Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow

def build_strategy_lead():
    return build_team_lead(
        team_name="strategy-team",
        role="Strategy Team Lead",
        goal="Produce strategy outputs that guide the portfolio by coordinating the embedded strategy-team orchestrator.",
        backstory=(
            "You are a Strategy Lead with 15 years of experience. You interface "
            "between PP project requirements and the strategy-team — translating "
            "strategic questions into strategy flow invocations and reporting "
            "recommendations back to the Project Manager and Orchestrator."
        )
    )

def run_strategy_deliverable(context: dict, mode: str,
                              scope: str = "project",
                              agent: str = None,
                              brief: str = "") -> dict:
    args = ["--mode", mode, "--name", context["project_name"],
            "--scope", scope]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if agent:
        args += ["--agent", agent]
    if brief:
        args += ["--brief", brief]
    return invoke_team_flow("strategy-team", "flows/strategy_flow.py",
                            args, context)
