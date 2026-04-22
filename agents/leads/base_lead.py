"""
agents/leads/base_lead.py

Protean Pursuits — Team Lead base class

Each Team Lead bridges the PP Project Manager and the embedded
team orchestrator in teams/<team-name>/.

Standalone team repos remain fully independent — they run directly
from their own directory without any PP dependency.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")

# TEAMS_DIR resolves to <umbrella-repo>/teams.
# base_lead.py lives at <umbrella>/agents/leads/base_lead.py, so two
# parent walks reach the umbrella root, and one more segment ('teams')
# gets us to the team submodules dir. (Previous version had an extra
# '..' and silently pointed one level above the repo root, which meant
# team_exists() returned False for every team — masked because the
# leads framework had never actually been exercised end-to-end until
# Phase 4 / 2026-04-22.)
TEAMS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "teams")
)


def get_team_path(team_name: str) -> str:
    return os.path.join(TEAMS_DIR, team_name)


def team_exists(team_name: str) -> bool:
    path = get_team_path(team_name)
    return os.path.isdir(path) and bool(os.listdir(path))


def invoke_team_flow(team_name: str, flow_script: str,
                     args: list, context: dict) -> dict:
    """Invoke a team flow script as a subprocess and log the result."""
    from core.notifications import notify_human
    from core.context import log_event, save_context, add_artifact

    team_path = get_team_path(team_name)
    if not team_exists(team_name):
        msg = (f"Submodule not populated: {team_name}. "
               f"Run: git submodule update --init --recursive")
        print(f"❌ {msg}")
        notify_human(f"Team unavailable — {team_name}", msg)
        log_event(context, "TEAM_UNAVAILABLE", team_name)
        return context

    script_path = os.path.join(team_path, flow_script)
    if not os.path.exists(script_path):
        print(f"❌ Flow not found: {script_path}")
        log_event(context, "FLOW_NOT_FOUND", script_path)
        return context

    key = team_name.upper().replace("-", "_")
    cmd = [sys.executable, script_path] + args
    print(f"\n🚀 [{team_name}] {' '.join(cmd)}\n")
    log_event(context, f"{key}_STARTED", " ".join(args))

    try:
        result = subprocess.run(cmd, cwd=team_path, text=True, timeout=7200)
        if result.returncode == 0:
            log_event(context, f"{key}_COMPLETE")
            context["status"] = f"{key}_COMPLETE"
        else:
            log_event(context, f"{key}_ERROR", f"exit {result.returncode}")
            notify_human(f"Team run failed — {team_name}",
                         f"Project: {context['project_name']}\n"
                         f"Exit: {result.returncode}\nArgs: {' '.join(args)}")
    except subprocess.TimeoutExpired:
        log_event(context, f"{key}_TIMEOUT")
        notify_human(f"Team timed out — {team_name}",
                     f"Project: {context['project_name']}")

    # Collect output artifacts
    from core.context import add_artifact
    team_output = os.path.join(team_path, "output")
    if os.path.isdir(team_output):
        for root, _, files in os.walk(team_output):
            for fname in sorted(files):
                if fname.endswith(".md") and not fname.startswith("."):
                    add_artifact(context, fname, key,
                                 os.path.join(root, fname),
                                 f"{team_name} orchestrator", "COMPLETE")

    save_context(context)
    return context


def build_team_lead(team_name: str, role: str, goal: str,
                    backstory: str) -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role=role, goal=goal,
        backstory=(
            backstory +
            f"\n\nYou delegate all specialist work to the embedded {team_name} "
            f"orchestrator at teams/{team_name}/. You translate PP briefs into "
            f"flow invocations, monitor execution, and report back to the PM."
        ),
        llm=llm, verbose=True, allow_delegation=True
    )
