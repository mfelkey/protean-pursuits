"""
flows/ds_flow.py

Protean Pursuits — DS Team Flow

Run modes:
  BRIEF       — single agent, on-demand task
  MODEL       — full model development pipeline
  PIPELINE    — data pipeline design and implementation
  ANALYSIS    — analytical report or investigation
  EVALUATION  — evaluate a data source, tool, or approach

Usage:
  python3.11 flows/ds_flow.py --mode brief \
      --name "PDB-02 StatsBomb Evaluation" \
      --brief "Evaluate StatsBomb open data for WC2026 xG..."

  python3.11 flows/ds_flow.py --mode evaluation \
      --name "Open-Meteo vs Tomorrow.io" \
      --brief "Compare weather API options..."
"""

import sys
import os
import json
import uuid
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv("config/.env")

from crewai import Agent, Task, Crew, Process, LLM


NOTIFICATION_AVAILABLE = False
try:
    import urllib.request, urllib.parse
    NOTIFICATION_AVAILABLE = True
except Exception:
    pass


def send_pushover(subject: str, message: str, priority: int = 0) -> bool:
    if not NOTIFICATION_AVAILABLE:
        return False
    user_key  = os.getenv("PUSHOVER_USER_KEY", "")
    api_token = os.getenv("PUSHOVER_API_TOKEN", "")
    if not user_key or not api_token:
        return False
    try:
        data = urllib.parse.urlencode({
            "token": api_token, "user": user_key,
            "title": subject[:250], "message": message[:1024],
            "priority": priority,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.pushover.net/1/messages.json",
            data=data, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("status") == 1:
                print(f"📱 Pushover sent: {subject[:60]}")
                return True
    except Exception as e:
        print(f"⚠️  Pushover failed: {e}")
    return False


def build_ds_agent(role: str, goal: str, backstory: str) -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192
    )
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_brief(name: str, brief: str, project_id: str = None) -> dict:
    """Run a single DS agent on an on-demand brief."""
    run_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
    print(f"\n{'='*60}")
    print(f"🔬 DS Team — Brief Run")
    print(f"   Name: {name}")
    print(f"   ID: {run_id}")
    print(f"   Started: {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")

    agent = build_ds_agent(
        role="Lead Data Scientist",
        goal=f"Produce a complete, actionable data science analysis for: {name}",
        backstory=(
            "You are the Lead Data Scientist at Protean Pursuits LLC, with 15 years "
            "of experience building production ML systems for sports analytics and "
            "betting platforms. You have deep expertise in soccer analytics, "
            "expected goals (xG) modeling, Dixon-Coles match outcome models, "
            "sports betting market microstructure, and data pipeline design. "
            "You are pragmatic and production-focused — you evaluate data sources "
            "against real implementation requirements, not theoretical ideals. "
            "When evaluating options you produce clear GO/NO-GO recommendations "
            "with specific rationale, not open-ended assessments. "
            "You are familiar with statsbombpy, Understat, API-Football, and other "
            "sports data providers. You understand what Dixon-Coles models require: "
            "historical shot-level xG data by team and match, sufficient historical "
            "depth (minimum 3-5 seasons or equivalent tournaments), and reliable "
            "coverage of the target competition."
        )
    )

    task = Task(
        description=f"""
{brief}

Produce a complete, well-structured analysis with:
1. EXECUTIVE SUMMARY — your recommendation in 2-3 sentences
2. DETAILED EVALUATION — findings for each option evaluated
3. RECOMMENDATION — clear GO/NO-GO with rationale
4. IMPLEMENTATION NOTES — if GO, how to proceed; specific steps, libraries, credit requirements
5. RISK FLAGS — any concerns or caveats the team should know
6. PRD IMPACT — any changes required to PRD schema or interface contract as a result

Format as clean markdown. Be specific and actionable.
Project: {name} (ID: {run_id}{f' | {project_id}' if project_id else ''})
""",
        expected_output="Complete data science analysis with executive summary, evaluation, recommendation, and implementation notes.",
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    result = str(crew.kickoff())

    # Save output
    os.makedirs("output/reports", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/reports/{run_id}_BRIEF_{ts}.md"
    with open(output_path, "w") as f:
        f.write(f"# {name}\n\n")
        f.write(f"**Run ID:** {run_id}\n")
        f.write(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write("---\n\n")
        f.write(result)

    print(f"\n💾 Output saved: {output_path}")

    # Publish to parallaxedge/docs/
    try:
        sys.path.insert(0, os.path.expanduser("~/projects/protean-pursuits"))
        from core.doc_publisher import publish_document
        publish_document(output_path, "ds", name, run_id)
    except Exception as e:
        print(f"⚠️  Auto-publish failed (run scripts/publish.py manually): {e}")

    # Notify
    send_pushover(
        subject=f"[DS] Brief complete — {name[:50]}",
        message=f"Run ID: {run_id}\nOutput: {output_path}\n\nReview and approve to close blocker.",
        priority=1
    )

    print(f"\n✅ DS Brief complete.")
    print(f"   Run ID: {run_id}")
    print(f"   Output: {output_path}")

    return {"run_id": run_id, "output": output_path, "result": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — DS Team")
    parser.add_argument("--mode",
        choices=["brief", "model", "pipeline", "analysis", "evaluation"],
        required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--brief", type=str, default="")
    parser.add_argument("--project-id", type=str, default=None)
    args = parser.parse_args()

    if args.mode in ("brief", "evaluation", "analysis"):
        if not args.brief:
            print("❌ --brief required for this mode")
            sys.exit(1)
        run_brief(args.name, args.brief, args.project_id)
    else:
        print(f"Mode '{args.mode}' — coming soon. Use --mode brief for now.")
