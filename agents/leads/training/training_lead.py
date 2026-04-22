"""agents/leads/training/training_lead.py — Training Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow


def build_training_lead():
    return build_team_lead(
        team_name="training-team",
        role="Training Team Lead",
        goal=(
            "Keep every Protean Pursuits team's knowledge base fresh and "
            "safe by coordinating the training-team curators, gating all "
            "ingestion through human approval, and alerting when critical "
            "domain updates land."
        ),
        backstory=(
            "You are the Head of Knowledge Management with 15 years of "
            "experience in enterprise RAG systems, curation pipelines, and "
            "regulatory-compliant information governance. You interface "
            "between PP project requirements and the training-team — "
            "scheduling curator runs, reviewing candidate knowledge items "
            "at the HITL gate, and surfacing freshness or alert reports "
            "to the Project Manager. Nothing enters the shared knowledge "
            "base without your sign-off."
        )
    )


def run_training_refresh(context: dict, mode: str,
                          team: str = None,
                          topic: str = None,
                          hours: int = 24) -> dict:
    """
    Dispatch a training-team flow run.

    mode: full | team | on_demand | status | alerts
    team: required for 'team' and 'on_demand'; one of the keys in TEAM_DOMAINS
    topic: required for 'on_demand'
    hours: lookback for 'alerts' (default 24)
    """
    args = ["--mode", mode]
    if team:
        args += ["--team", team]
    if topic:
        args += ["--topic", topic]
    if mode == "alerts" and hours:
        args += ["--hours", str(hours)]
    return invoke_team_flow("training-team", "flows/training_flow.py",
                            args, context)
