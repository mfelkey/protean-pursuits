"""
agents/leads/base_lead.py

Generic Team Lead base — all 7 team leads inherit from this.
Each lead accepts work from the Project Manager, briefs their agents,
tracks their deliverables, and reports status upward.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context, escalate_blocker

load_dotenv("config/.env")


def build_team_lead(team_name: str, role_description: str, backstory: str,
                    tier: str = "TIER1") -> Agent:
    """Generic factory for any Team Lead agent."""
    model_key = "TIER1_MODEL" if tier == "TIER1" else "TIER2_MODEL"
    llm = LLM(
        model=os.getenv(model_key, "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role=f"{team_name} Team Lead",
        goal=role_description,
        backstory=backstory,
        llm=llm,
        verbose=True,
        allow_delegation=True
    )


def run_sprint_deliverable(context: dict, team_name: str, agent: Agent,
                            sprint_number: int, deliverable_name: str,
                            deliverable_brief: str, output_dir: str) -> dict:
    """
    Generic sprint deliverable runner for any Team Lead.
    The lead produces the deliverable, saves it, and updates context.
    """
    task = Task(
        description=deliverable_brief,
        expected_output=f"Complete {deliverable_name} deliverable.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n🔨 [{team_name}] Sprint {sprint_number} — {deliverable_name}...\n")
    result = crew.kickoff()

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = deliverable_name.replace(" ", "_").upper()
    output_path = f"{output_dir}/{context['project_id']}_S{sprint_number:02d}_{safe_name}_{timestamp}.md"

    with open(output_path, "w") as f:
        f.write(str(result))

    context["artifacts"].append({
        "name": deliverable_name,
        "type": safe_name,
        "team": team_name,
        "sprint": sprint_number,
        "path": output_path,
        "status": "COMPLETE",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": f"{team_name} Team Lead"
    })
    log_event(context, f"{team_name.upper()}_DELIVERABLE_COMPLETE",
              f"Sprint {sprint_number}: {deliverable_name}")
    save_context(context)

    print(f"\n💾 [{team_name}] {deliverable_name} saved: {output_path}")
    return context, output_path
