"""
flows/ds_flow.py

Protean Pursuits — DS Team Flow

Run modes:
  brief       DS Orchestrator only — on-demand scoping or quick analysis
  evaluation  Data Evaluator → Reporting Analyst → DS Orchestrator
  analysis    Data Framer → EDA Analyst → Statistical Analyst → Reporting Analyst → DS Orchestrator
  model       Data Framer → EDA Analyst → ML Engineer → Reporting Analyst → DS Orchestrator
  pipeline    Data Framer → Pipeline Engineer → ML Engineer → Reporting Analyst → DS Orchestrator

Complexity-adaptive routing (analysis, model, pipeline modes):
  LOW    — Data Framer → Reporting Analyst → DS Orchestrator (skips EDA, Stats, ML detail)
  MEDIUM — full pipeline as above
  HIGH   — full pipeline as above + DS Orchestrator flags SME consultation if needed

All outputs follow the six-section structure:
  1. Executive Summary  2. Detailed Findings  3. Recommendation
  4. Implementation Notes  5. Risk Flags  6. PRD Impact
  + CROSS-TEAM FLAGS + OPEN QUESTIONS

Usage:
  python3.11 flows/ds_flow.py --mode brief \\
      --name "StatsBomb xG Evaluation" \\
      --brief "Evaluate StatsBomb open data for WC2026 xG modeling..."

  python3.11 flows/ds_flow.py --mode model \\
      --name "Dixon-Coles Match Outcome Model" \\
      --brief "Design a Dixon-Coles model for EPL match outcome prediction..."

  python3.11 flows/ds_flow.py --mode pipeline \\
      --name "Odds Feed Ingestion Pipeline" \\
      --brief "Design a pipeline to ingest live odds from three providers..."

Via pp_flow.py:
  python flows/pp_flow.py --team ds --mode analysis \\
      --project parallaxedge --task "Q1 churn analysis" --save
"""

import sys
import os
import json
import uuid
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv("config/.env")

from crewai import Task, Crew, Process

# ── Notifications ─────────────────────────────────────────────────────────────

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


# ── Agent loader ──────────────────────────────────────────────────────────────

def _load_agents(keys: list) -> dict:
    from agents.ds.ds_orchestrator import build_ds_orchestrator
    from agents.ds.data_evaluator import build_data_evaluator
    from agents.ds.data_framer import build_data_framer
    from agents.ds.eda_analyst import build_eda_analyst
    from agents.ds.statistical_analyst import build_statistical_analyst
    from agents.ds.ml_engineer import build_ml_engineer
    from agents.ds.pipeline_engineer import build_pipeline_engineer
    from agents.ds.reporting_analyst import build_reporting_analyst

    builders = {
        "ds_orchestrator":    build_ds_orchestrator,
        "data_evaluator":     build_data_evaluator,
        "data_framer":        build_data_framer,
        "eda_analyst":        build_eda_analyst,
        "statistical_analyst": build_statistical_analyst,
        "ml_engineer":        build_ml_engineer,
        "pipeline_engineer":  build_pipeline_engineer,
        "reporting_analyst":  build_reporting_analyst,
    }
    return {k: builders[k]() for k in keys if k in builders}


# ── Output helpers ────────────────────────────────────────────────────────────

REPORT_STRUCTURE = """
Every output must follow this six-section structure:
1. EXECUTIVE SUMMARY — key recommendation in 2-3 sentences, non-technical language
2. DETAILED FINDINGS — consolidated findings, each tagged with source agent
3. RECOMMENDATION — clear decision (GO/NO-GO, approach A vs B, etc.)
4. IMPLEMENTATION NOTES — concrete next steps if recommendation is GO
5. RISK FLAGS — ordered HIGH/MEDIUM/LOW with likelihood, impact, mitigation
6. PRD IMPACT — required changes to PRD/schema/interface contract (or 'None')

Followed by:
CROSS-TEAM FLAGS — items requiring Legal / Finance / Strategy / QA / SME attention
OPEN QUESTIONS — numbered list tagged [VERIFY]
All inferences tagged [ASSUMPTION].
No fabricated statistics or findings.
"""


def _save_output(run_id: str, name: str, mode: str, content: str,
                 project: str = None) -> str:
    os.makedirs("output/reports", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"output/reports/{run_id}_{mode.upper()}_{ts}.md"
    with open(path, "w") as f:
        f.write(f"# {name}\n\n")
        f.write(f"**Run ID:** {run_id}\n")
        f.write(f"**Mode:** {mode.upper()}\n")
        if project:
            f.write(f"**Project:** {project}\n")
        f.write(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write("---\n\n")
        f.write(content)
    print(f"💾 Output saved: {path}")

    # Attempt doc publish
    try:
        sys.path.insert(0, os.path.expanduser("~/projects/protean-pursuits"))
        from core.doc_publisher import publish_document
        publish_document(path, "ds", name, run_id)
    except Exception as e:
        print(f"⚠️  Auto-publish failed (run scripts/publish.py manually): {e}")

    return path


def _run_crew(agent_keys: list, name: str, brief: str, mode: str,
              run_id: str, project: str = None) -> str:
    """Build crew from agent keys, run sequentially, return combined output."""
    agents_dict = _load_agents(agent_keys)
    agent_list = list(agents_dict.values())
    context_str = f"Project: {name} (Run ID: {run_id}{f' | {project}' if project else ''})"

    tasks = []
    for i, (key, agent) in enumerate(agents_dict.items()):
        prefix = "" if i == 0 else "Use the output of the previous task as your primary input context.\n\n"
        tasks.append(Task(
            description=(
                f"{prefix}{context_str}\n\nMode: {mode.upper()}\n\nBrief:\n{brief}"
                f"\n\n{REPORT_STRUCTURE}"
            ),
            expected_output=(
                f"Complete structured deliverable from {key.replace('_', ' ')} "
                f"following the six-section report structure. "
                f"No placeholders. No fabricated statistics."
            ),
            agent=agent,
        ))

    crew = Crew(
        agents=agent_list,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return str(crew.kickoff())


# ── Mode runners ──────────────────────────────────────────────────────────────

def run_brief(name: str, brief: str, project: str = None,
              context: dict = None, save: bool = True) -> dict:
    """
    DS Orchestrator only — on-demand scoping or quick analysis.
    Replaces the previous single-agent brief with the DS Orchestrator persona.
    """
    run_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
    _print_header("Brief", name, run_id)
    send_pushover(f"[DS] Brief starting — {name[:50]}", f"Run ID: {run_id}", priority=0)

    # Merge pp_flow context into brief if supplied
    full_brief = brief
    if context and context.get("raw"):
        full_brief = f"{brief}\n\nAdditional project context:\n{context['raw']}"

    result = _run_crew(
        agent_keys=["ds_orchestrator"],
        name=name, brief=full_brief, mode="brief",
        run_id=run_id, project=project or (context or {}).get("project"),
    )

    output_path = _save_output(run_id, name, "brief", result,
                               project=project or (context or {}).get("project"))
    _print_footer(run_id, output_path)
    send_pushover(
        f"[DS] Brief complete — {name[:50]}",
        f"Run ID: {run_id}\nOutput: {output_path}",
        priority=1,
    )
    return {"run_id": run_id, "output": output_path, "result": result}


def run_evaluation(name: str, brief: str, project: str = None,
                   context: dict = None, save: bool = True) -> dict:
    """
    Data Evaluator → Reporting Analyst → DS Orchestrator.
    Evaluates data sources, APIs, tools, or approaches.
    """
    run_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
    _print_header("Evaluation", name, run_id)
    send_pushover(f"[DS] Evaluation starting — {name[:50]}", f"Run ID: {run_id}")

    full_brief = brief
    if context and context.get("raw"):
        full_brief = f"{brief}\n\nAdditional project context:\n{context['raw']}"

    result = _run_crew(
        agent_keys=["data_evaluator", "reporting_analyst", "ds_orchestrator"],
        name=name, brief=full_brief, mode="evaluation",
        run_id=run_id, project=project or (context or {}).get("project"),
    )

    output_path = _save_output(run_id, name, "evaluation", result,
                               project=project or (context or {}).get("project"))
    _print_footer(run_id, output_path)
    send_pushover(f"[DS] Evaluation complete — {name[:50]}",
                  f"Run ID: {run_id}\nOutput: {output_path}", priority=1)
    return {"run_id": run_id, "output": output_path, "result": result}


def run_analysis(name: str, brief: str, complexity: str = "MEDIUM",
                 project: str = None, context: dict = None,
                 save: bool = True) -> dict:
    """
    Complexity-adaptive analytical report.
    LOW:    Data Framer → Reporting Analyst → DS Orchestrator
    MEDIUM/HIGH: Data Framer → EDA Analyst → Statistical Analyst →
                 Reporting Analyst → DS Orchestrator
    """
    run_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
    _print_header("Analysis", name, run_id)
    complexity = complexity.upper()

    full_brief = brief
    if context and context.get("raw"):
        full_brief = f"{brief}\n\nAdditional project context:\n{context['raw']}"
    full_brief = f"[Complexity: {complexity}]\n\n{full_brief}"

    if complexity == "LOW":
        agent_keys = ["data_framer", "reporting_analyst", "ds_orchestrator"]
    else:
        agent_keys = [
            "data_framer", "eda_analyst", "statistical_analyst",
            "reporting_analyst", "ds_orchestrator",
        ]

    send_pushover(f"[DS] Analysis starting — {name[:50]}",
                  f"Run ID: {run_id} | Complexity: {complexity}")

    result = _run_crew(
        agent_keys=agent_keys,
        name=name, brief=full_brief, mode="analysis",
        run_id=run_id, project=project or (context or {}).get("project"),
    )

    output_path = _save_output(run_id, name, "analysis", result,
                               project=project or (context or {}).get("project"))
    _print_footer(run_id, output_path)
    send_pushover(f"[DS] Analysis complete — {name[:50]}",
                  f"Run ID: {run_id}\nOutput: {output_path}", priority=1)
    return {"run_id": run_id, "output": output_path, "result": result}


def run_model(name: str, brief: str, complexity: str = "MEDIUM",
              project: str = None, context: dict = None,
              save: bool = True) -> dict:
    """
    Model development pipeline.
    LOW:    Data Framer → ML Engineer → Reporting Analyst → DS Orchestrator
    MEDIUM/HIGH: Data Framer → EDA Analyst → ML Engineer →
                 Reporting Analyst → DS Orchestrator
    """
    run_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
    _print_header("Model", name, run_id)
    complexity = complexity.upper()

    full_brief = brief
    if context and context.get("raw"):
        full_brief = f"{brief}\n\nAdditional project context:\n{context['raw']}"
    full_brief = f"[Complexity: {complexity}]\n\n{full_brief}"

    if complexity == "LOW":
        agent_keys = ["data_framer", "ml_engineer", "reporting_analyst", "ds_orchestrator"]
    else:
        agent_keys = [
            "data_framer", "eda_analyst", "ml_engineer",
            "reporting_analyst", "ds_orchestrator",
        ]

    send_pushover(f"[DS] Model starting — {name[:50]}",
                  f"Run ID: {run_id} | Complexity: {complexity}")

    result = _run_crew(
        agent_keys=agent_keys,
        name=name, brief=full_brief, mode="model",
        run_id=run_id, project=project or (context or {}).get("project"),
    )

    output_path = _save_output(run_id, name, "model", result,
                               project=project or (context or {}).get("project"))
    _print_footer(run_id, output_path)
    send_pushover(f"[DS] Model complete — {name[:50]}",
                  f"Run ID: {run_id}\nOutput: {output_path}", priority=1)
    return {"run_id": run_id, "output": output_path, "result": result}


def run_pipeline(name: str, brief: str, complexity: str = "MEDIUM",
                 project: str = None, context: dict = None,
                 save: bool = True) -> dict:
    """
    Data pipeline design pipeline.
    LOW:    Data Framer → Pipeline Engineer → Reporting Analyst → DS Orchestrator
    MEDIUM/HIGH: Data Framer → Pipeline Engineer → ML Engineer →
                 Reporting Analyst → DS Orchestrator
    """
    run_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
    _print_header("Pipeline", name, run_id)
    complexity = complexity.upper()

    full_brief = brief
    if context and context.get("raw"):
        full_brief = f"{brief}\n\nAdditional project context:\n{context['raw']}"
    full_brief = f"[Complexity: {complexity}]\n\n{full_brief}"

    if complexity == "LOW":
        agent_keys = [
            "data_framer", "pipeline_engineer",
            "reporting_analyst", "ds_orchestrator",
        ]
    else:
        agent_keys = [
            "data_framer", "pipeline_engineer", "ml_engineer",
            "reporting_analyst", "ds_orchestrator",
        ]

    send_pushover(f"[DS] Pipeline starting — {name[:50]}",
                  f"Run ID: {run_id} | Complexity: {complexity}")

    result = _run_crew(
        agent_keys=agent_keys,
        name=name, brief=full_brief, mode="pipeline",
        run_id=run_id, project=project or (context or {}).get("project"),
    )

    output_path = _save_output(run_id, name, "pipeline", result,
                               project=project or (context or {}).get("project"))
    _print_footer(run_id, output_path)
    send_pushover(f"[DS] Pipeline complete — {name[:50]}",
                  f"Run ID: {run_id}\nOutput: {output_path}", priority=1)
    return {"run_id": run_id, "output": output_path, "result": result}


# ── Print helpers ─────────────────────────────────────────────────────────────

def _print_header(mode: str, name: str, run_id: str) -> None:
    print(f"\n{'='*60}")
    print(f"🔬 DS Team — {mode}")
    print(f"   Name:    {name}")
    print(f"   Run ID:  {run_id}")
    print(f"   Started: {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")


def _print_footer(run_id: str, output_path: str) -> None:
    print(f"\n✅ DS run complete.")
    print(f"   Run ID:  {run_id}")
    print(f"   Output:  {output_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — DS Team")
    parser.add_argument(
        "--mode",
        choices=["brief", "evaluation", "analysis", "model", "pipeline"],
        required=True,
    )
    parser.add_argument("--name", type=str, required=True,
                        help="Short name for this DS run (used in output filename)")
    parser.add_argument("--brief", type=str, default="",
                        help="Plain-English task description")
    parser.add_argument("--complexity", type=str, default="MEDIUM",
                        choices=["LOW", "MEDIUM", "HIGH"],
                        help="Complexity level — controls pipeline depth (default: MEDIUM)")
    parser.add_argument("--project", type=str, default=None,
                        help="Project name for context and output organisation")
    parser.add_argument("--project-id", type=str, default=None,
                        help="Project ID (legacy alias for --project)")
    args = parser.parse_args()

    if args.mode != "brief" and not args.brief:
        print("❌ --brief required for all modes except brief")
        import sys; sys.exit(1)

    project = args.project or args.project_id

    if args.mode == "brief":
        run_brief(name=args.name, brief=args.brief, project=project)
    elif args.mode == "evaluation":
        run_evaluation(name=args.name, brief=args.brief, project=project)
    elif args.mode == "analysis":
        run_analysis(name=args.name, brief=args.brief,
                     complexity=args.complexity, project=project)
    elif args.mode == "model":
        run_model(name=args.name, brief=args.brief,
                  complexity=args.complexity, project=project)
    elif args.mode == "pipeline":
        run_pipeline(name=args.name, brief=args.brief,
                     complexity=args.complexity, project=project)
