"""
agents/dev/finance/infra_finance_modeler.py

Finance specialist — Infrastructure Cost Model (ICM)

Translates the TAD's technical architecture into a financial model:
line-item infrastructure costs, scaling curves, cloud vs on-prem trade-offs,
and a month-by-month projection for years 1–3.

Run standalone:
  python agents/dev/finance/infra_finance_modeler.py
"""

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
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


def build_infra_finance_modeler() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Infrastructure Finance Modeler",
        goal=(
            "Translate the technical architecture into a financial model: "
            "map every infrastructure component to a cost line, build scaling "
            "curves, model cloud vs. on-prem trade-offs, and produce a "
            "month-by-month cost projection for years 1–3."
        ),
        backstory=(
            "You are an Infrastructure Finance Modeler — a specialist who sits "
            "at the intersection of cloud architecture and corporate finance. "
            "You have 12 years of experience modelling infrastructure costs for "
            "SaaS and data platform companies. You understand how AWS, GCP, and "
            "Azure pricing actually works (reserved vs. on-demand, egress charges, "
            "managed service premiums) and you model it accurately. "
            "You translate every component in a Technical Architecture Document "
            "into a named cost line with monthly cost at launch, 6-month, "
            "12-month, and 36-month scale points. You model what happens to "
            "costs at 10x and 100x user load. You flag architectural choices "
            "that are disproportionately expensive at scale. "
            "You produce: the Infrastructure Cost Model (ICM), which the "
            "Financial Statements Modeler and Strategic Finance Specialist "
            "use as input. "
            "FINANCE RATING REQUIREMENT: Begin with "
            "'FINANCE RATING: 🟢/🟡/🔴' and justify the rating. "
            "End with OPEN QUESTIONS listing decisions that affect infra costs."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_infra_model(context: dict, tad_text: str = "",
                    cea_text: str = "") -> tuple:
    """Produce ICM from TAD + CEA. Returns (updated_context, icm_path)."""

    ifm = build_infra_finance_modeler()

    task = Task(
        description=f"""
You are the Infrastructure Finance Modeler for project {context['project_id']} — {context['project_name']}.

TECHNICAL ARCHITECTURE DOCUMENT (excerpt):
{tad_text[:5000] if tad_text else "Not provided — model from project name."}

COST ESTIMATES & BUDGET DOCUMENT (excerpt):
{cea_text[:3000] if cea_text else "Not provided."}

Produce a complete Infrastructure Cost Model (ICM) covering ALL sections:

1. FINANCE RATING
   🟢 GREEN / 🟡 AMBER / 🔴 RED — with 2-sentence justification.

2. ARCHITECTURE COMPONENTS MAPPED TO COSTS
   For each component identified in the TAD:
   | Component | Service | Size/Tier | Monthly Cost (Launch) | Monthly Cost (10x) |
   Include: compute, database, cache, storage, CDN, networking/egress,
   CI/CD, monitoring/observability, secrets, backup, logging.

3. SCALING COST CURVES
   Show monthly infrastructure spend at: launch, 3 months, 6 months,
   12 months, 24 months, 36 months.
   Use LOW / MID / HIGH growth assumptions.
   Present as both table and prose narrative.

4. SCALING COST DRIVERS
   Which components drive the most cost growth at scale?
   What is the cost per active user at each scale point?
   Flag any components with super-linear cost scaling.

5. CLOUD VS. ON-PREM ANALYSIS (where applicable)
   For any component where on-prem is a realistic alternative:
   Break-even analysis (at what scale does on-prem become cheaper?).
   Recommendation with rationale.

6. COST OPTIMISATION OPPORTUNITIES
   Top 3-5 architectural choices that could reduce infrastructure spend
   without material capability reduction. Estimated saving per item.

7. YEAR 1–3 MONTHLY PROJECTION
   | Month | Compute | DB | Storage | Networking | Other | Total |
   Show 36 months across MID scenario.

8. YEAR 1–3 SUMMARY
   | Year | Total Infra Spend | % of Total Costs | Cost per User |
   Align with CEA totals where CEA is available.

9. ASSUMPTIONS
   Cloud provider assumed, pricing model (on-demand/reserved/spot),
   data transfer volumes, storage growth rate, replication factor.

10. OPEN QUESTIONS
    Architectural decisions that significantly affect cost modelling.

Output as well-formatted markdown.

{build_assumption_instructions()}
""",
        expected_output="Complete Infrastructure Cost Model in markdown.",
        agent=ifm
    )

    crew   = Crew(agents=[ifm], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n💰 Infrastructure Finance Modeler producing ICM for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path    = f"{out_dir}/{context['project_id']}_ICM_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 ICM saved: {path}")
    context["artifacts"].append({
        "name":       "Infrastructure Cost Model",
        "type":       "ICM",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Infrastructure Finance Modeler"
    })
    context["status"] = "ICM_COMPLETE"
    context.setdefault("events", [])
    context.setdefault("logs", [])
    context.setdefault("project_name", context.get("project_id", "Unknown"))

    log_event(context, "ICM_COMPLETE", path)
    save_context(context)
    return context, path


if __name__ == "__main__":
    tad_text = ""
    cea_text = ""
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("❌ No project context found.")
        exit(1)
    with open(logs[0]) as f:
        context = json.load(f)

    tad_text = cea_text = ""
    for a in context.get("artifacts", []):
        t = a.get("type")
        p = a.get("path", "")
        if os.path.exists(p):
            with open(p) as f:
                txt = f.read(8000)
            if t == "TAD": tad_text = txt
            if t == "CEA": cea_text = txt

    print(f"📂 Loaded context: {logs[0]}")    context, path = run_infra_model(context, tad_text, cea_text)
    print(f"\n✅ ICM complete: {path}")
    with open(path) as f:
        print(f.read(500))