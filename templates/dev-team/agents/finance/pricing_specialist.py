"""
agents/finance/pricing_specialist.py

Finance specialist — Pricing Strategy & Model (PRI)

Develops the go-to-market pricing strategy: tier structures, price points,
competitive positioning, margin analysis, sensitivity analysis.
Skipped automatically for internal tooling projects.

Run standalone:
  python agents/finance/pricing_specialist.py
"""

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")


def build_pricing_specialist() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Pricing Specialist",
        goal=(
            "Develop a defensible go-to-market pricing strategy — tier structures, "
            "price points, margin analysis, and competitive positioning — that "
            "maximises long-term revenue while fitting the product's market."
        ),
        backstory=(
            "You are a Pricing Strategist with 14 years of experience setting "
            "pricing for SaaS and data products across B2B and B2C markets. "
            "You combine economics, competitive analysis, and customer psychology "
            "to build pricing models that are fair to customers and profitable "
            "for the business. You are honest about what you don't know: when "
            "benchmark data is unavailable, you say so and model from first "
            "principles with documented assumptions. "
            "You are fluent in: tiered pricing, usage-based pricing, "
            "seat-based pricing, freemium conversion models, enterprise "
            "custom pricing, and hybrid models. You know the trade-offs of each "
            "and you pick the model that fits the product's go-to-market motion. "
            "You produce: the Pricing Strategy & Model (PRI), which the "
            "Financial Statements Modeler uses as input for revenue projections. "
            "FINANCE RATING REQUIREMENT: Begin with "
            "'FINANCE RATING: 🟢/🟡/🔴' and justify the rating. "
            "End with OPEN QUESTIONS listing pricing decisions for human input."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_pricing_model(context: dict, prd_text: str = "", bad_text: str = "",
                      roi_text: str = "", cea_text: str = "") -> tuple:
    """Produce PRI from PRD + BAD + ROI + CEA. Returns (updated_context, pri_path)."""

    ps = build_pricing_specialist()

    task = Task(
        description=f"""
You are the Pricing Specialist for project {context['project_id']} — {context['project_name']}.

PRODUCT REQUIREMENTS DOCUMENT (excerpt):
{prd_text[:4000] if prd_text else "Not provided."}

BUSINESS ANALYSIS DOCUMENT (excerpt):
{bad_text[:2000] if bad_text else "Not provided."}

ROI & BUSINESS CASE ANALYSIS (excerpt):
{roi_text[:2000] if roi_text else "Not provided."}

COST ESTIMATES & BUDGET DOCUMENT (excerpt):
{cea_text[:2000] if cea_text else "Not provided."}

Produce a complete Pricing Strategy & Model (PRI) covering ALL sections:

1. FINANCE RATING
   🟢 GREEN / 🟡 AMBER / 🔴 RED — with justification focused on pricing risk
   and revenue model viability.

2. RECOMMENDED PRICING MODEL
   Which model best fits this product and why:
   Freemium / Tiered subscription / Usage-based / Seat-based /
   Enterprise custom / Hybrid. Rationale for selection.

3. PRICING TIERS
   | Tier Name | Price (Monthly) | Price (Annual) | Included Features | Target Segment |
   Design 2–4 tiers (or describe enterprise tier). For each tier:
   - What's included
   - What's excluded (creates upgrade motivation)
   - Target customer segment and use case
   - Why this price point

4. UNIT ECONOMICS
   | Tier | Monthly Price | COGS per Customer | Gross Margin % | LTV (12mo) | LTV (36mo) |
   Show CAC assumptions used.

5. COMPETITIVE POSITIONING
   Name the 2–3 most likely competitors and their pricing (or state
   "competitor pricing not available — estimated"). Where does this
   product sit on price relative to competitors? Why?

6. FREEMIUM / TRIAL STRATEGY (if applicable)
   What's free forever vs. trial-limited. Conversion trigger design.
   Expected free-to-paid conversion rate with assumption basis.

7. REVENUE PROJECTIONS
   | Month | Free Users | Paid Tier 1 | Paid Tier 2 | Paid Tier 3 | MRR | ARR |
   Show 12-month BASE CASE scenario.
   State conversion rate and average revenue per user assumptions.

8. PRICE SENSITIVITY ANALYSIS
   If price is reduced by 20%, what is the estimated conversion rate increase?
   At what price point does the product become unprofitable (floor)?

9. PRICING RISKS
   Top 3 risks: commoditisation, race-to-bottom, enterprise procurement friction.
   Mitigation for each.

10. OPEN QUESTIONS
    Pricing decisions requiring human input before launch.

Output as well-formatted markdown.
""",
        expected_output="Complete Pricing Strategy & Model in markdown.",
        agent=ps
    )

    crew   = Crew(agents=[ps], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n💰 Pricing Specialist producing PRI for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path    = f"{out_dir}/{context['project_id']}_PRI_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 PRI saved: {path}")
    context["artifacts"].append({
        "name":       "Pricing Strategy & Model",
        "type":       "PRI",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Pricing Specialist"
    })
    context["status"] = "PRI_COMPLETE"
    log_event(context, "PRI_COMPLETE", path)
    save_context(context)
    return context, path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("❌ No project context found.")
        exit(1)
    with open(logs[0]) as f:
        context = json.load(f)

    prd_text = bad_text = roi_text = cea_text = ""
    for a in context.get("artifacts", []):
        t = a.get("type")
        p = a.get("path", "")
        if os.path.exists(p):
            with open(p) as f:
                txt = f.read(8000)
            if t == "PRD": prd_text = txt
            if t == "BAD": bad_text = txt
            if t == "ROI": roi_text = txt
            if t == "CEA": cea_text = txt

    print(f"📂 Loaded context: {logs[0]}")
    context, path = run_pricing_model(context, prd_text, bad_text, roi_text, cea_text)
    print(f"\n✅ PRI complete: {path}")
    with open(path) as f:
        print(f.read(500))
