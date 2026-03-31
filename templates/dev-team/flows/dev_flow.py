"""
flows/dev_flow.py

Protean Pursuits — Dev Team Flow

Run modes:
  BRIEF       — single agent, on-demand task
  ARCHITECTURE — full system architecture design
  SPEC        — feature or component specification
  REVIEW      — code or design review

Usage:
  python3.11 flows/dev_flow.py --mode brief \
      --name "ParallaxEdge API Architecture" \
      --brief "Design the complete API..."
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


def send_pushover(subject: str, message: str, priority: int = 0) -> bool:
    import urllib.request, urllib.parse
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
            return result.get("status") == 1
    except Exception as e:
        print(f"⚠️  Pushover failed: {e}")
        return False


def build_dev_agent(role: str, goal: str, backstory: str) -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192
    )
    return Agent(
        role=role, goal=goal, backstory=backstory,
        llm=llm, verbose=True, allow_delegation=False
    )


def run_brief(name: str, brief: str, project_id: str = None) -> dict:
    run_id = f"DEV-{uuid.uuid4().hex[:8].upper()}"
    print(f"\n{'='*60}")
    print(f"⚙️  Dev Team — Brief Run")
    print(f"   Name: {name}")
    print(f"   ID: {run_id}")
    print(f"   Started: {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")

    agent = build_dev_agent(
        role="Principal Engineer",
        goal=f"Produce a complete, implementation-ready technical specification for: {name}",
        backstory=(
            "You are the Principal Engineer at Protean Pursuits LLC, with 15 years "
            "of experience building production web applications and APIs. You have "
            "deep expertise in FastAPI, Next.js, PostgreSQL, Redis, and modern "
            "SaaS architecture patterns. You are building ParallaxEdge — a sports "
            "betting analytics platform — and you understand the PRD deeply: "
            "the inputs_snapshot JSONB schema, the data_quality_score gate logic "
            "(BLOCK < 0.70, FLAG 0.70-0.85, PASS > 0.85), the model output "
            "specification in Section 7.1, and the rate limiting and observability "
            "requirements in Section 8.7. "
            "You produce precise, implementation-ready technical specifications — "
            "not vague directional guidance. Every output includes specific "
            "endpoint paths, HTTP methods, request/response schemas, and "
            "concrete implementation recommendations. "
            "You understand the DS team interface contract: the model produces "
            "home_win_prob, away_win_prob, draw_prob, fair_spread, fair_total, "
            "confidence_score, data_quality_score, inputs_snapshot JSONB, and "
            "flags JSONB. You know how to design the API layer that consumes "
            "these outputs and serves them to frontend users."
        )
    )

    task = Task(
        description=f"""
{brief}

Produce a complete, well-structured technical specification with:
1. Clear section headers
2. Specific endpoint paths, methods, schemas (not vague descriptions)
3. Concrete technology recommendations with rationale
4. Implementation-ready pseudocode or schema definitions where helpful
5. Timeline broken into specific tasks with day estimates
6. All dependencies on DS team clearly listed

Format as clean markdown. Be specific and actionable.
Project: {name} (ID: {run_id}{f' | {project_id}' if project_id else ''})
""",
        expected_output="Complete technical specification with endpoints, schemas, architecture decisions, and timeline.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task],
                process=Process.sequential, verbose=True)
    result = str(crew.kickoff())

    os.makedirs("output/specs", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/specs/{run_id}_BRIEF_{ts}.md"
    with open(output_path, "w") as f:
        f.write(f"# {name}\n\n")
        f.write(f"**Run ID:** {run_id}\n")
        f.write(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write("---\n\n")
        f.write(result)

    print(f"\n💾 Output saved: {output_path}")

    # Auto-publish to parallaxedge/docs/
    try:
        sys.path.insert(0, os.path.expanduser("~/projects/protean-pursuits"))
        from core.doc_publisher import publish_document
        publish_document(output_path, "dev", name, run_id)
    except Exception as e:
        print(f"⚠️  Auto-publish failed (run scripts/publish.py manually): {e}")

    send_pushover(
        subject=f"[DEV] Brief complete — {name[:50]}",
        message=f"Run ID: {run_id}\nOutput: {output_path}",
        priority=1
    )

    print(f"\n✅ Dev Brief complete.")
    print(f"   Run ID: {run_id}")
    print(f"   Output: {output_path}")

    return {"run_id": run_id, "output": output_path, "result": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — Dev Team")
    parser.add_argument("--mode",
        choices=["brief", "architecture", "spec", "review"],
        required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--brief", type=str, default="")
    parser.add_argument("--project-id", type=str, default=None)
    args = parser.parse_args()

    if args.mode in ("brief", "architecture", "spec", "review"):
        if not args.brief:
            print("❌ --brief required for this mode")
            sys.exit(1)
        run_brief(args.name, args.brief, args.project_id)
    else:
        print(f"Mode '{args.mode}' coming soon. Use --mode brief for now.")
