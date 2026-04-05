"""
agents/dev/finance/pricing_specialist.py

Finance specialist — Pricing Strategy & Model (PRI)

Develops the go-to-market pricing strategy: tier structures, price points,
competitive positioning, margin analysis, sensitivity analysis.
Skipped automatically for internal tooling projects.

Run standalone:
  python agents/dev/finance/pricing_specialist.py

Run with explicit inputs (bypasses context JSON scan):
  python agents/dev/finance/pricing_specialist.py \\
      --project-id PROJ-EXAMPLE \\
      --prd /path/to/prd.md \\
      --context "Additional context or brief passed on the CLI."
"""

import sys
sys.path.insert(0, "/home/mfelkey/dev-team")
import pathlib as _pathlib
_REPO_ROOT = str(_pathlib.Path(__file__).resolve().parents[5])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import argparse
import glob
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

from core.input_guard import check_required_inputs, build_assumption_instructions


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
            "End with OPEN QUESTIONS listing pricing decisions for human input. "
            "CONTEXT DISCIPLINE: You MUST address every specific question, "
            "constraint, user archetype, competitor price point, and pricing "
            "scenario described in the PROJECT BRIEF / CLI CONTEXT block. "
            "Do not substitute generic SaaS defaults for specifics provided. "
            "If a brief says OddsJam charges $399.99/mo, use that figure. "
            "If a brief lists eight questions, answer all eight."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_pricing_model(context: dict, prd_text: str = "", bad_text: str = "",
                      roi_text: str = "", cea_text: str = "",
                      cli_context: str = "") -> tuple:
    """Produce PRI from PRD + BAD + ROI + CEA + optional CLI context.

    Args:
        context:     Project context dict (must contain project_id, project_name).
        prd_text:    PRD file contents (read by caller, passed in).
        bad_text:    Business Analysis Document contents.
        roi_text:    ROI analysis contents.
        cea_text:    Cost Estimates & Budget contents.
        cli_context: Freeform brief / context string supplied via --context flag.
                     Injected verbatim into the task so the agent cannot miss it.

    Returns:
        (updated_context, pri_path)
    """

    ps = build_pricing_specialist()

    # The cli_context block is placed FIRST and in a prominent labelled section
    # so the agent processes it before any document excerpts. This prevents
    # the model from defaulting to generic template answers.
    cli_block = ""
    if cli_context and cli_context.strip():
        cli_block = f"""
╔══════════════════════════════════════════════════════════════════╗
║  PROJECT BRIEF / CLI CONTEXT  (PRIMARY INPUT — READ FIRST)      ║
╚══════════════════════════════════════════════════════════════════╝
{cli_context.strip()}

Every question, constraint, price point, competitor figure, user archetype,
bundle, and SKU described above MUST be addressed explicitly in your output.
Do not substitute generic defaults. Do not invent competitors or price points
that are not supported by the brief or the PRD.
══════════════════════════════════════════════════════════════════════
"""

    task = Task(
        description=f"""
You are the Pricing Specialist for project {context['project_id']} — {context['project_name']}.
{cli_block}
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

{build_assumption_instructions()}
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


# ── CLI ────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pricing_specialist.py",
        description=(
            "Finance Group — Pricing Specialist (PRI)\n\n"
            "Without flags: loads the most-recent PROJ-*.json from logs/ and\n"
            "reads PRD/BAD/ROI/CEA artifacts from that context (original behaviour).\n\n"
            "With flags: --project-id and --prd override the context scan; "
            "--context injects a freeform brief directly into the agent task "
            "as the PRIMARY input, ensuring the agent cannot ignore it."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--project-id",
        dest="project_id",
        default=None,
        help="Project ID (e.g. PROJ-PARALLAXEDGE). Overrides the context JSON scan.",
    )
    p.add_argument(
        "--prd",
        dest="prd_path",
        default=None,
        help="Path to the PRD markdown file. Read and injected into the task.",
    )
    p.add_argument(
        "--context",
        dest="cli_context",
        default=None,
        help=(
            "Freeform brief / pricing strategy context. Injected verbatim into "
            "the agent task as the PRIMARY input before any document excerpts. "
            "This is what the agent MUST answer — use it for sport-specific "
            "briefs, specific questions, competitor figures, bundle structures, etc."
        ),
    )
    return p


if __name__ == "__main__":
    prd_text = ""
    bad_text = ""
    roi_text = ""
    cea_text = ""
    cli_context = ""
    parser = _build_parser()
    args   = parser.parse_args()

    # ── Resolve project context ────────────────────────────────────────────────
    if args.project_id:
        # Explicit project ID supplied: build a minimal context dict.
        # Don't scan logs/ — the caller is driving this run directly.
        context = {
            "project_id":   args.project_id,
            "project_name": args.project_id,
            "artifacts":    [],
            "status":       "PRICING_STANDALONE",
        }
        print(f"📂 Using explicit project-id: {args.project_id}")
    else:
        # Legacy behaviour: load most-recent context JSON from logs/
        logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
        if not logs:
            print("❌ No project context found. Pass --project-id or ensure logs/PROJ-*.json exists.")
            sys.exit(1)
        with open(logs[0]) as f:
            context = json.load(f)
        print(f"📂 Loaded context: {logs[0]}")
    # ── Resolve PRD text ───────────────────────────────────────────────────────
    prd_text = bad_text = roi_text = cea_text = ""

    if args.prd_path:
        prd_path = os.path.expanduser(args.prd_path)
        if not os.path.exists(prd_path):
            print(f"❌ PRD file not found: {prd_path}")
            sys.exit(1)
        with open(prd_path) as f:
            prd_text = f.read(8000)
        print(f"📄 PRD loaded: {prd_path} ({len(prd_text)} chars)")
    else:
        # Scan artifacts from context JSON for PRD/BAD/ROI/CEA
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

    # ── Warn if neither PRD nor context brief is provided ─────────────────────
    if not prd_text and not args.cli_context:
        print("⚠️  No PRD and no --context brief provided. Agent will produce generic output.")

    # ── Run ───────────────────────────────────────────────────────────────────
    # ── Input guard ───────────────────────────────────────────────────────────
    project_id = check_required_inputs(
        context.get("project_id", "PROJ-UNKNOWN"),
        prd_text,
        args.cli_context or "",
    )
    context["project_id"] = project_id

    context, path = run_pricing_model(
        context,
        prd_text=prd_text,
        bad_text=bad_text,
        roi_text=roi_text,
        cea_text=cea_text,
        cli_context=args.cli_context or "",
    )

    print(f"\n✅ PRI complete: {path}")
    with open(path) as f:
        print(f.read(500))
