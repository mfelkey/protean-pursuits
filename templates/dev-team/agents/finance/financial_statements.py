"""
agents/finance/financial_statements.py

Finance specialist — Financial Statements Report (FSR)

Produces the three core projected financial statements:
Income Statement, Cash Flow Statement, Balance Sheet.
Driven by CEA, ROI, ICM, and PRI inputs.

Run standalone:
  python agents/finance/financial_statements.py
"""

import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")


def build_financial_statements() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Financial Statements Modeler",
        goal=(
            "Produce the three core projected financial statements — Income "
            "Statement, Cash Flow Statement, and Balance Sheet — from the "
            "outputs of the other Finance specialist agents."
        ),
        backstory=(
            "You are a Financial Statements Modeler with 15 years of experience "
            "building projected financial statements for technology companies "
            "at all stages from pre-revenue to Series B. You are a CPA who "
            "also understands software products deeply — you know the difference "
            "between a capitalised development cost and an operating expense, "
            "and you model it correctly. "
            "You are rigorous about cross-referencing your inputs: you explicitly "
            "verify that your income statement revenue lines match the PRI "
            "projections, that your COGS match the CEA + ICM, and that your "
            "cash flow matches the investment outflows in the CEA. When inputs "
            "are missing (e.g. no PRI because it's an internal tool), you state "
            "the assumption you used instead. "
            "You produce statements across three scenarios (pessimistic / base / "
            "optimistic) with a 3-year monthly projection for the base case. "
            "FINANCE RATING REQUIREMENT: Begin with "
            "'FINANCE RATING: 🟢/🟡/🔴' and justify the rating. "
            "End with OPEN QUESTIONS listing assumptions that require validation."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_financial_statements(context: dict, cea_text: str = "",
                              roi_text: str = "", icm_text: str = "",
                              pri_text: str = "") -> tuple:
    """Produce FSR from CEA + ROI + ICM + PRI. Returns (updated_context, fsr_path)."""

    fs = build_financial_statements()

    task = Task(
        description=f"""
You are the Financial Statements Modeler for project {context['project_id']} — {context['project_name']}.

COST ESTIMATES & BUDGET DOCUMENT (excerpt):
{cea_text[:3000] if cea_text else "Not provided — use estimates."}

ROI & BUSINESS CASE ANALYSIS (excerpt):
{roi_text[:3000] if roi_text else "Not provided — use estimates."}

INFRASTRUCTURE COST MODEL (excerpt):
{icm_text[:2500] if icm_text else "Not provided — use estimates."}

PRICING STRATEGY & MODEL (excerpt):
{pri_text[:2500] if pri_text else "Not provided — internal tool assumed, no external revenue."}

Produce a complete Financial Statements Report (FSR) covering ALL sections:

1. FINANCE RATING
   🟢 GREEN / 🟡 AMBER / 🔴 RED — with justification.

2. KEY ASSUMPTIONS
   Document every assumption driving the three statements. Include:
   revenue recognition policy, capitalisation policy for development costs,
   depreciation schedule, working capital assumptions, tax rate.

3. INCOME STATEMENT (PROJECTED — 3 YEARS)
   Annual summary + monthly detail for Year 1.
   | Line Item | Year 1 | Year 2 | Year 3 |
   Revenue (by tier/stream), COGS, Gross Profit, Gross Margin %,
   Operating Expenses (R&D, S&M, G&A), EBITDA, D&A, EBIT,
   Interest, EBT, Tax, Net Income.
   Show PESSIMISTIC / BASE / OPTIMISTIC for the annual summary.

4. CASH FLOW STATEMENT (PROJECTED — 3 YEARS)
   Annual summary + monthly detail for Year 1.
   Operating Activities: net income, add-backs (D&A, stock comp),
   working capital changes.
   Investing Activities: development capex, infrastructure capex.
   Financing Activities: funding received, debt repayment.
   Net Cash Flow, Opening Cash, Closing Cash.

5. BALANCE SHEET (PROJECTED — END OF EACH YEAR)
   Assets: Cash, AR, Prepaid, Capitalised Dev Costs, PP&E, Total Assets.
   Liabilities: AP, Deferred Revenue, Debt, Total Liabilities.
   Equity: Paid-in Capital, Retained Earnings/(Deficit), Total Equity.
   Verify: Assets = Liabilities + Equity for each year.

6. KEY FINANCIAL RATIOS
   | Ratio          | Year 1 | Year 2 | Year 3 |
   Gross margin %, EBITDA margin %, Burn rate (if pre-revenue),
   Runway (months at current burn), Current ratio, Quick ratio.

7. CROSS-REFERENCE VERIFICATION
   Explicitly confirm: income statement revenue aligns with PRI projections;
   COGS aligns with CEA + ICM; capex aligns with CEA development costs.
   Flag any inconsistencies between your model and the upstream inputs.

8. OPEN QUESTIONS
   Modelling assumptions that require human validation.

Output as well-formatted markdown.
""",
        expected_output="Complete Financial Statements Report in markdown.",
        agent=fs
    )

    crew   = Crew(agents=[fs], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n💰 Financial Statements Modeler producing FSR for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path    = f"{out_dir}/{context['project_id']}_FSR_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 FSR saved: {path}")
    context["artifacts"].append({
        "name":       "Financial Statements Report",
        "type":       "FSR",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Financial Statements Modeler"
    })
    context["status"] = "FSR_COMPLETE"
    log_event(context, "FSR_COMPLETE", path)
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

    cea_text = roi_text = icm_text = pri_text = ""
    for a in context.get("artifacts", []):
        t = a.get("type")
        p = a.get("path", "")
        if os.path.exists(p):
            with open(p) as f:
                txt = f.read(6000)
            if t == "CEA": cea_text = txt
            if t == "ROI": roi_text = txt
            if t == "ICM": icm_text = txt
            if t == "PRI": pri_text = txt

    print(f"📂 Loaded context: {logs[0]}")
    context, path = run_financial_statements(context, cea_text, roi_text, icm_text, pri_text)
    print(f"\n✅ FSR complete: {path}")
    with open(path) as f:
        print(f.read(500))
