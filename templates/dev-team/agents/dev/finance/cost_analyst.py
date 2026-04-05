"""
agents/dev/finance/cost_analyst.py

Finance specialist — Cost Estimates & Budget Document (CEA)

Produces a detailed cost estimate covering development costs, licensing,
tooling, infrastructure, and third-party services. Always runs first;
feeds into ROI, ICM, and FSR.

Run standalone:
  python agents/dev/finance/cost_analyst.py
"""

import sys
sys.path.insert(0, "/home/mfelkey/dev-team")
import pathlib as _pathlib
_REPO_ROOT = str(_pathlib.Path(__file__).resolve().parents[5])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

from core.input_guard import check_required_inputs, build_assumption_instructions


def build_cost_analyst() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Cost Analyst",
        goal=(
            "Produce a detailed, assumption-documented cost estimate and budget "
            "envelope for the project — covering development, infrastructure, "
            "licensing, and operations — across LOW / MID / HIGH scenarios."
        ),
        backstory=(
            "You are a Technology Cost Analyst with 14 years of experience "
            "estimating software development and infrastructure costs for "
            "SaaS, data, and enterprise products. You translate technical "
            "architecture documents into line-by-line cost models. "
            "You are meticulous about documenting every assumption: engineering "
            "rate used, hours estimated per feature area, cloud pricing tier "
            "assumed, licence type, and so on. You never present a number "
            "without its derivation. You produce estimates in three scenarios "
            "(LOW = conservative, MID = base case, HIGH = optimistic) and "
            "clearly state what drives the spread between them. "
            "You produce: the Cost Estimates & Budget Document (CEA), which "
            "feeds into the ROI Analysis, Infrastructure Cost Model, Financial "
            "Statements, and ultimately the Finance Summary Package. "
            "FINANCE RATING REQUIREMENT: Begin your output with "
            "'FINANCE RATING: 🟢/🟡/🔴' and justify the rating. "
            "End with an OPEN QUESTIONS section listing cost decisions that "
            "require human input before the build begins."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_cost_analysis(context: dict, prd_text: str = "",
                      tad_text: str = "") -> tuple:
    """Produce CEA from PRD + TAD. Returns (updated_context, cea_path)."""

    ca = build_cost_analyst()

    task = Task(
        description=f"""
You are the Cost Analyst for project {context['project_id']} — {context['project_name']}.

PRODUCT REQUIREMENTS DOCUMENT (excerpt):
{prd_text[:5000] if prd_text else "Not provided — estimate from project name."}

TECHNICAL ARCHITECTURE DOCUMENT (excerpt):
{tad_text[:4000] if tad_text else "Not provided — estimate from PRD."}

Produce a complete Cost Estimates & Budget Document (CEA) covering ALL sections:

1. FINANCE RATING
   🟢 GREEN / 🟡 AMBER / 🔴 RED — with 2-sentence justification.

2. SCOPE OF ESTIMATE
   What is and is not included. Key assumptions summary.

3. DEVELOPMENT COSTS
   Breakdown by role (engineer, designer, PM, QA) and phase (discovery,
   build, test, launch). Show hours × rate × headcount for each.
   LOW / MID / HIGH scenarios.

4. INFRASTRUCTURE COSTS (MONTHLY — STEADY STATE)
   Line-item cloud/hosting costs: compute, database, storage, CDN, egress,
   monitoring, secrets management, CI/CD runners.
   Show costs at LAUNCH scale and GROWTH scale (10x users).

5. THIRD-PARTY SERVICES & LICENCES
   APIs, analytics platforms, payment processors (if applicable),
   security scanning tools, design tools, monitoring SaaS.
   Monthly and annual totals.

6. ONE-TIME COSTS
   Domain, SSL, infrastructure provisioning, security audit,
   legal review, design assets.

7. BUDGET ENVELOPE SUMMARY
   | Scenario | Development | Infra (Yr 1) | 3rd-party (Yr 1) | One-Time | TOTAL Yr 1 |
   LOW / MID / HIGH rows.

8. COST ASSUMPTIONS
   Numbered list of every assumption made. Include: engineering rates,
   sprint velocity, cloud pricing tier, licence type, team size.

9. COST RISKS
   Top 3 risks that could push costs above the HIGH scenario.

10. OPEN QUESTIONS
    Decisions requiring human input before the estimate can be finalised.

Output as well-formatted markdown.

{build_assumption_instructions()}
""",
        expected_output="Complete CEA in markdown, opening with FINANCE RATING line.",
        agent=ca
    )

    crew   = Crew(agents=[ca], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n💰 Cost Analyst producing CEA for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path    = f"{out_dir}/{context['project_id']}_CEA_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 CEA saved: {path}")
    context["artifacts"].append({
        "name":       "Cost Estimates & Budget Document",
        "type":       "CEA",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Cost Analyst"
    })
    context["status"] = "CEA_COMPLETE"
    log_event(context, "CEA_COMPLETE", path)
    save_context(context)
    return context, path


if __name__ == "__main__":
    prd_text = ""
    tad_text = ""
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("❌ No project context found. Run classify.py first.")
        exit(1)
    with open(logs[0]) as f:
        context = json.load(f)

    prd_text = tad_text = ""
    for a in context.get("artifacts", []):
        if a.get("type") == "PRD" and os.path.exists(a.get("path", "")):
            with open(a["path"]) as f:
                prd_text = f.read(8000)
        if a.get("type") == "TAD" and os.path.exists(a.get("path", "")):
            with open(a["path"]) as f:
                tad_text = f.read(6000)

    if not prd_text:
        print("⚠️  PRD not found — proceeding with project name only.")

    print(f"📂 Loaded context: {logs[0]}")    context, path = run_cost_analysis(context, prd_text, tad_text)
    print(f"\n✅ CEA complete: {path}")
    with open(path) as f:
        print(f.read(500))