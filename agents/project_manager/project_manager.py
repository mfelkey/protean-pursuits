"""
agents/project_manager/project_manager.py

Protean Pursuits — Project Manager Agent

Sits between the Orchestrator and Team Leads.
Owns timeline, budget, cross-team dependencies, status reports,
and day-to-day blocker resolution.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import (
    log_event, save_context, notify_human, escalate_blocker
)

load_dotenv("config/.env")


def build_project_manager() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Project Manager",
        goal=(
            "Translate Orchestrator directives into executable work for Team Leads — "
            "maintaining timeline, budget, cross-team dependency map, weekly status "
            "reports, and escalating unresolved blockers to the Orchestrator."
        ),
        backstory=(
            "You are a Senior Project Manager with 15 years of experience running "
            "complex multi-team software and data product programmes. You have deep "
            "expertise in agile delivery, dependency management, risk tracking, and "
            "stakeholder communication. "
            "You sit between the Orchestrator and the seven Team Leads. The Orchestrator "
            "gives you a project brief, PRD, team composition, and high-level timeline. "
            "You break that down into a sprint-level work plan, assign deliverables to "
            "each Team Lead, track dependencies (e.g. Design must complete UX before "
            "Dev starts frontend; DS model contract must be locked before Dev builds "
            "API integration), and flag schedule risk early. "
            "You track budget at the team level. You know the burn rate for each team "
            "and alert the Orchestrator when projected spend exceeds allocation by more "
            "than 10%. "
            "You produce three standing reports: a Weekly Status Report every Monday "
            "(one page per active project: RAG status, completed items, in-progress "
            "items, blockers, next week plan), a Sprint Review Summary at the end of "
            "each sprint, and an ad-hoc Blocker Report whenever a blocker threatens "
            "the critical path. "
            "You resolve blockers at the Team Lead level where possible. When you "
            "cannot resolve a blocker within 48 hours, you escalate to the Orchestrator "
            "with full context. CRITICAL blockers are escalated immediately — no 48-hour "
            "window. "
            "You never reassign work between teams without Orchestrator approval. You "
            "never extend a deadline without Orchestrator approval. You never exceed "
            "budget without Orchestrator approval."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )


def run_project_kickoff(context: dict, prd_path: str, teams: list,
                         timeline_weeks: int, budget_usd: float) -> dict:
    """
    Generate a full project work plan from PRD.
    Assigns deliverables to each Team Lead and sets sprint structure.
    Returns updated context with timeline and budget initialized.
    """
    pm = build_project_manager()

    with open(prd_path) as f:
        prd_content = f.read()

    kickoff_task = Task(
        description=f"""
You are the Protean Pursuits Project Manager. A new project has been approved.
Produce a complete Project Kickoff Plan for the following:

Project: {context['project_name']} ({context['project_id']})
Teams assigned: {', '.join(teams)}
Timeline: {timeline_weeks} weeks
Budget: ${budget_usd:,.2f} USD

PRD (excerpt):
{prd_content[:4000]}

Produce a complete Project Kickoff Plan with ALL of the following:

1. SPRINT PLAN
   - Sprint length recommendation (1 or 2 weeks) with rationale
   - Sprint-by-sprint breakdown for the full timeline
   - Each sprint: goals, deliverables per team, definition of done

2. CROSS-TEAM DEPENDENCY MAP
   - List every dependency between teams (e.g. "DS model interface contract
     must be complete before Dev starts API integration layer")
   - For each dependency: blocking team, dependent team, due date, risk if missed

3. BUDGET ALLOCATION
   - Budget split by team (as % and USD)
   - Monthly burn rate projection
   - Contingency reserve recommendation (suggest 10-15%)

4. MILESTONE SCHEDULE
   - Key milestones with dates (from project start)
   - Each milestone: owner team(s), success criteria, dependencies

5. RISK REGISTER
   - Top 5 risks with probability (H/M/L), impact (H/M/L), mitigation
   - Any CRITICAL blockers identified from PRD review

6. TEAM LEAD BRIEFING TEMPLATE
   - Standard briefing format to send to each Team Lead at kickoff
   - Include: project context, their deliverables, dependencies they own,
     their budget allocation, first sprint goals

Output the complete Project Kickoff Plan as well-formatted markdown.
""",
        expected_output="Complete Project Kickoff Plan in markdown.",
        agent=pm
    )

    crew = Crew(agents=[pm], tasks=[kickoff_task], process=Process.sequential, verbose=True)
    print(f"\n📋 Project Manager generating kickoff plan — {context['project_name']}...\n")
    result = crew.kickoff()

    os.makedirs("logs", exist_ok=True)
    plan_path = f"logs/{context['project_id']}_KICKOFF_PLAN.md"
    with open(plan_path, "w") as f:
        f.write(str(result))

    context["artifacts"].append({
        "name": "Project Kickoff Plan",
        "type": "KICKOFF_PLAN",
        "path": plan_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Project Manager"
    })
    context["timeline"] = {"weeks": timeline_weeks, "plan_path": plan_path}
    context["budget"] = {"total_usd": budget_usd, "allocated": True}
    context["status"] = "KICKOFF_COMPLETE"
    log_event(context, "KICKOFF_COMPLETE", plan_path)
    save_context(context)

    print(f"\n💾 Kickoff plan saved: {plan_path}")
    notify_human(
        subject=f"Project kickoff complete — {context['project_name']}",
        message=(
            f"Project: {context['project_name']} ({context['project_id']})\n"
            f"Teams: {', '.join(teams)}\n"
            f"Timeline: {timeline_weeks} weeks\n"
            f"Budget: ${budget_usd:,.2f}\n\n"
            f"Kickoff plan: {plan_path}\n\n"
            f"Team Leads are ready to receive their briefings."
        )
    )
    return context, plan_path


def run_weekly_status_report(context: dict, week_number: int,
                              team_updates: dict) -> dict:
    """
    Generate weekly cross-team status report.
    team_updates: dict keyed by team name with status, completed, in_progress, blockers
    """
    pm = build_project_manager()
    updates_json = json.dumps(team_updates, indent=2)

    report_task = Task(
        description=f"""
You are the Protean Pursuits Project Manager.
Generate the Weekly Status Report for Week {week_number} of project
'{context['project_name']}' ({context['project_id']}).

Team updates provided:
{updates_json}

Produce a complete Weekly Status Report with:

1. EXECUTIVE SUMMARY
   - Overall RAG status (Red / Amber / Green) with one-line rationale
   - Top achievement this week
   - Top risk or concern

2. PER-TEAM STATUS TABLE
   | Team | RAG | Completed | In Progress | Blockers | Next Week |
   (one row per team, concise)

3. DEPENDENCY STATUS
   - Any cross-team dependencies at risk of being missed
   - Mitigation recommendations

4. OPEN BLOCKERS
   - All open blockers: ID, team, severity, age, status, next action

5. BUDGET SNAPSHOT
   - Spend to date vs plan
   - Projected end-of-project variance

6. NEXT WEEK PRIORITIES
   - Top 3 cross-team priorities for next week
   - Owner for each

Output as clean markdown. Keep to one page (approx 400-500 words).
""",
        expected_output="Weekly Status Report in markdown, approx one page.",
        agent=pm
    )

    crew = Crew(agents=[pm], tasks=[report_task], process=Process.sequential, verbose=True)
    print(f"\n📊 Project Manager generating Week {week_number} status report...\n")
    result = crew.kickoff()

    os.makedirs("logs", exist_ok=True)
    report_path = f"logs/{context['project_id']}_WSR_W{week_number:02d}.md"
    with open(report_path, "w") as f:
        f.write(str(result))

    context["artifacts"].append({
        "name": f"Weekly Status Report — Week {week_number}",
        "type": "WSR",
        "path": report_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Project Manager"
    })
    log_event(context, "WSR_COMPLETE", report_path)
    save_context(context)

    notify_human(
        subject=f"Week {week_number} status — {context['project_name']}",
        message=f"Weekly status report ready: {report_path}"
    )
    return context, report_path
