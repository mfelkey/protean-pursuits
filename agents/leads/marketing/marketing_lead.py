"""agents/leads/marketing/marketing_lead.py — Marketing Team Lead"""
import sys; sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow

def build_marketing_lead():
    return build_team_lead(
        team_name="marketing-team",
        role="Marketing Team Lead",
        goal="Execute go-to-market strategy by coordinating the embedded marketing-team orchestrator.",
        backstory=(
            "You are a VP of Marketing with 15 years of experience. You interface "
            "between PP project requirements and the marketing-team — translating "
            "GTM strategy into campaign flow invocations and reporting results "
            "back to the Project Manager."
        )
    )

def run_marketing_deliverable(context: dict, campaign_name: str,
                               campaign_type: str = "FULL") -> dict:
    args = ["--campaign", campaign_name, "--type", campaign_type]
    return invoke_team_flow("marketing-team", "flows/marketing_flow.py",
                            args, context)
