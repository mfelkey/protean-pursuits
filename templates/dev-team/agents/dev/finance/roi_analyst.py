"""
agents/dev/finance/roi_analyst.py

Finance specialist — ROI & Business Case Analysis (ROI)

Builds the investment case: expected returns, payback period, NPV, IRR,
break-even, and risk-adjusted scenarios. Answers: is this worth building?

Run standalone:
  python agents/dev/finance/roi_analyst.py
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


def build_roi_analyst() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="ROI Analyst",
        goal=(
            "Build the business case — quantify expected returns, calculate NPV "
            "and IRR, model break-even, and produce a risk-adjusted "
            "recommendation: proceed, revise scope, or stop."
        ),
        backstory=(
            "You are a Corporate Finance and ROI Analyst with 16 years of "
            "experience building investment cases for technology projects at "
            "scale. You combine rigorous financial modelling with clear "
            "narrative — you can explain NPV to a CFO and to an engineer. "
            "You are honest about uncertainty: when a number is speculative, "
            "you say so and provide a range. You never dress up a weak "
            "business case with optimistic assumptions — you present the "
            "realistic base case and let the human decide. "
            "You produce: the ROI & Business Case Analysis (ROI), which "
            "answers the question 'is this project worth building?' with "
            "quantitative analysis across three scenarios. "
            "FINANCE RATING REQUIREMENT: Begin with "
            "'FINANCE RATING: 🟢/🟡/🔴' and justify the rating. "
            "End with OPEN QUESTIONS listing decisions that affect the ROI."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_roi_analysis(context: dict, prd_text: str = "",
                     bad_text: str = "", cea_text: str = "") -> tuple:
    """Produce ROI from PRD + BAD + CEA. Returns (updated_context, roi_path)."""

    ra = build_roi_analyst()

    task = Task(
        description=f"""
You are the ROI Analyst for project {context['project_id']} — {context['project_name']}.

PRODUCT REQUIREMENTS DOCUMENT (excerpt):
{prd_text[:4000] if prd_text else "Not provided."}

BUSINESS ANALYSIS DOCUMENT (excerpt):
{bad_text[:3000] if bad_text else "Not provided."}

COST ESTIMATES & BUDGET DOCUMENT (excerpt):
{cea_text[:3000] if cea_text else "Not provided — use project name to estimate."}

Produce a complete ROI & Business Case Analysis covering ALL sections:

1. FINANCE RATING
   🟢 GREEN / 🟡 AMBER / 🔴 RED — with 2-sentence justification.

2. BUSINESS CASE SUMMARY
   One paragraph: why this project exists, what it delivers, and why now.

3. EXPECTED BENEFITS & VALUE DRIVERS
   Quantify every benefit you can. For intangible benefits (user experience,
   brand value), describe the mechanism by which they drive financial value.
   Separate: revenue upside, cost reduction, risk mitigation, strategic option.

4. FINANCIAL MODEL
   | Metric           | Pessimistic | Base Case | Optimistic |
   - Total Investment (from CEA)
   - Year 1 / Year 2 / Year 3 projected benefit
   - Cumulative cash flow by year
   - Payback period (months)
   - NPV at 8% discount rate (3-year horizon)
   - IRR
   - Break-even month

5. SCENARIO ASSUMPTIONS
   What drives each scenario. Be explicit about revenue ramp rate,
   user acquisition assumptions, and cost growth assumptions.

6. RISK-ADJUSTED ANALYSIS
   Identify the top 3 financial risks. For each: probability, impact,
   adjusted expected value reduction.

7. RECOMMENDATION
   One of: PROCEED / REVISE SCOPE / STOP — with 3-bullet rationale.
   If REVISE SCOPE: what specifically to cut to improve the ROI.

8. SENSITIVITY ANALYSIS
   Which input variable has the highest impact on NPV?
   Show: ±10% change in that variable → NPV change.

9. OPEN QUESTIONS
   Decisions requiring human input before the ROI can be finalised.

Output as well-formatted markdown.

{build_assumption_instructions()}
""",
        expected_output="Complete ROI & Business Case Analysis in markdown.",
        agent=ra
    )

    crew   = Crew(agents=[ra], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n💰 ROI Analyst producing business case for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path    = f"{out_dir}/{context['project_id']}_ROI_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 ROI saved: {path}")
    context["artifacts"].append({
        "name":       "ROI & Business Case Analysis",
        "type":       "ROI",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "ROI Analyst"
    })
    context["status"] = "ROI_COMPLETE"
    log_event(context, "ROI_COMPLETE", path)
    save_context(context)
    return context, path


if __name__ == "__main__":
    prd_text = ""
    bad_text = ""
    cea_text = ""
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("❌ No project context found.")
        exit(1)
    with open(logs[0]) as f:
        context = json.load(f)

    prd_text = bad_text = cea_text = ""
    for a in context.get("artifacts", []):
        t = a.get("type")
        p = a.get("path", "")
        if os.path.exists(p):
            with open(p) as f:
                txt = f.read(8000)
            if t == "PRD":   prd_text = txt
            if t == "BAD":   bad_text = txt
            if t == "CEA":   cea_text = txt

    print(f"📂 Loaded context: {logs[0]}")    context, path = run_roi_analysis(context, prd_text, bad_text, cea_text)
    print(f"\n✅ ROI complete: {path}")
    with open(path) as f:
        print(f.read(500))