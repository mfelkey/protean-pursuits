"""
agents/finance/strategic_corp_finance.py

Finance specialist — Strategic Corporate Finance Report (SCF)

The synthesis and strategy layer. Reads all other Finance outputs and produces:
capital structure recommendations, funding options, M&A considerations,
financial risk register, and a two-page executive summary.
Runs last in the Finance sequence.

Run standalone:
  python agents/finance/strategic_corp_finance.py
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


def build_strategic_corp_finance() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Strategic Corporate Finance Specialist",
        goal=(
            "Synthesise all Finance outputs into a strategic corporate finance "
            "strategy — capital structure, funding options, M&A considerations, "
            "financial risk register — and produce a two-page executive summary "
            "suitable for stakeholder or investor review."
        ),
        backstory=(
            "You are a Strategic Corporate Finance Specialist with 20 years of "
            "experience at the intersection of technology, venture capital, and "
            "corporate strategy. You have served as CFO at three tech companies, "
            "advised on $2B+ in M&A transactions, and guided 12 companies through "
            "Series A to IPO. You can translate complex financial models into "
            "clear strategic recommendations that boards and investors can act on. "
            "You are the last Finance agent to run — you read all previous Finance "
            "outputs and synthesise them into the strategic picture. You are "
            "intellectually honest: if the financial case for this project is "
            "weak, you say so directly. You give the human what they need to make "
            "a clear-eyed funding and build decision. "
            "You consider: stage of company (pre-revenue, growth, established), "
            "capital efficiency, dilution management, debt vs. equity trade-offs, "
            "and strategic optionality (build vs. buy vs. partner). "
            "FINANCE RATING REQUIREMENT: Begin with "
            "'FINANCE RATING: 🟢/🟡/🔴' — this is the overall Finance group "
            "rating and must synthesise all upstream ratings. "
            "End with OPEN QUESTIONS listing strategic decisions for human input."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_strategic_corp_finance(context: dict, prd_text: str = "",
                                roi_text: str = "", icm_text: str = "",
                                pri_text: str = "", fsr_text: str = "",
                                cea_text: str = "") -> tuple:
    """Produce SCF from all upstream Finance artifacts."""

    scf_agent = build_strategic_corp_finance()

    task = Task(
        description=f"""
You are the Strategic Corporate Finance Specialist for project
{context['project_id']} — {context['project_name']}.

You are the LAST Finance agent. Read ALL upstream Finance outputs and
produce the strategic corporate finance synthesis.

PRODUCT REQUIREMENTS DOCUMENT (excerpt):
{prd_text[:3000] if prd_text else "Not provided."}

COST ESTIMATES & BUDGET (excerpt):
{cea_text[:2000] if cea_text else "Not provided."}

ROI & BUSINESS CASE (excerpt):
{roi_text[:2500] if roi_text else "Not provided."}

INFRASTRUCTURE COST MODEL (excerpt):
{icm_text[:2000] if icm_text else "Not provided."}

PRICING STRATEGY & MODEL (excerpt):
{pri_text[:2000] if pri_text else "Not provided."}

FINANCIAL STATEMENTS (excerpt):
{fsr_text[:2500] if fsr_text else "Not provided."}

Produce a complete Strategic Corporate Finance Report (SCF) covering ALL sections:

1. FINANCE RATING (OVERALL)
   🟢 GREEN / 🟡 AMBER / 🔴 RED — synthesising all upstream ratings.
   This is the Finance group's overall verdict. Justify in 3-4 sentences.

2. EXECUTIVE SUMMARY (2 pages maximum)
   For a non-technical executive or investor audience.
   - What this project is and why it matters financially
   - The investment required and the expected return
   - The key risks and how they are mitigated
   - The recommended funding approach
   - The go/no-go recommendation with rationale

3. CAPITAL STRUCTURE RECOMMENDATIONS
   How should this project be funded?
   Options with trade-offs:
   - Bootstrapped from operating cash flow
   - Angel / pre-seed / seed funding
   - Venture capital
   - Revenue-based financing
   - Debt / credit facility
   - Strategic partnership / joint venture
   Recommendation with rationale for this specific project.

4. FUNDING STAGE & AMOUNT GUIDANCE
   If external capital is recommended:
   - How much to raise (based on CEA runway model)
   - When to raise (milestone-triggered vs. calendar)
   - What stage (pre-seed / seed / Series A)
   - Key investor profile for this product

5. BUILD VS. BUY VS. PARTNER ANALYSIS
   Are there components of this project where buying or partnering
   is more capital-efficient than building? Analyse with cost comparison.

6. M&A CONSIDERATIONS
   - Is this product likely to be an acquisition target? At what stage?
   - Are there strategic acquirers who would value it?
   - Are there acquisitions that would accelerate this product?
   - Indicative valuation range (revenue multiple or DCF basis).

7. FINANCIAL RISK REGISTER
   | Risk | Probability | Impact | Mitigation | Residual Risk |
   At least 6 financial risks covering: funding risk, revenue miss,
   cost overrun, competitive pricing pressure, regulatory, FX (if applicable).

8. CROSS-REFERENCE SUMMARY
   Confirm consistency across all Finance artifacts.
   Flag any material inconsistencies between CEA, ROI, ICM, PRI, FSR.

9. OPEN QUESTIONS
   Strategic financial decisions requiring human input before build begins.

Output as well-formatted markdown. The Executive Summary section must be
readable by a non-technical stakeholder as a standalone document.
""",
        expected_output="Complete Strategic Corporate Finance Report in markdown.",
        agent=scf_agent
    )

    crew   = Crew(agents=[scf_agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n💰 Strategic Corp Finance Specialist producing SCF for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path    = f"{out_dir}/{context['project_id']}_SCF_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 SCF saved: {path}")
    context["artifacts"].append({
        "name":       "Strategic Corporate Finance Report",
        "type":       "SCF",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Strategic Corporate Finance Specialist"
    })
    context["status"] = "SCF_COMPLETE"
    log_event(context, "SCF_COMPLETE", path)
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

    prd_text = cea_text = roi_text = icm_text = pri_text = fsr_text = ""
    for a in context.get("artifacts", []):
        t = a.get("type")
        p = a.get("path", "")
        if os.path.exists(p):
            with open(p) as f:
                txt = f.read(6000)
            if t == "PRD": prd_text = txt
            if t == "CEA": cea_text = txt
            if t == "ROI": roi_text = txt
            if t == "ICM": icm_text = txt
            if t == "PRI": pri_text = txt
            if t == "FSR": fsr_text = txt

    print(f"📂 Loaded context: {logs[0]}")
    context, path = run_strategic_corp_finance(
        context, prd_text, roi_text, icm_text, pri_text, fsr_text, cea_text)
    print(f"\n✅ SCF complete: {path}")
    with open(path) as f:
        print(f.read(500))
