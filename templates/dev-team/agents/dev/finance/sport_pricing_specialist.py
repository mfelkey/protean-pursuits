"""
agents/dev/finance/sport_pricing_specialist.py

Finance specialist — Sport Subscription Pricing & Bundle Architecture (SPS)

Designs per-sport SKU structures, Sharp/Pro tier pricing, year-round coverage
bundles, seasonal pricing windows, and user-archetype-driven packaging for
sport-tech subscription products.

Structurally distinct from the generic Pricing Specialist (PRI):
  - Understands sport seasonality and coverage calendars
  - Reasons about user archetypes (US bettor, international bettor, etc.)
  - Prices sport-specific Sharp and Pro tiers per sport
  - Designs multi-sport bundles with discount logic
  - Handles sports with non-standard bet structures (e.g. Horse Racing: Tote, SP)
  - Benchmarks against real sport-data/odds competitors (OddsJam, Pinnacle, etc.)

Artifact type: SPS
Output directory: output/finance/

Run standalone (with full context brief):
  python agents/dev/finance/sport_pricing_specialist.py \\
      --project-id PROJ-PARALLAXEDGE \\
      --prd ~/projects/parallaxedge/docs/Parallax_PRD_v1_13.md \\
      --context "ParallaxEdge Pricing Strategy — Sport-Based Tier Redesign..."

Run from finance_flow.py:
  python flows/finance_flow.py --mode sport_pricing \\
      --project parallaxedge \\
      --task "Sport-based SKU and bundle design for ParallaxEdge" \\
      --context "Two tiers per sport: Sharp and Pro. Sports: Soccer, NFL, NBA..."
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


def build_sport_pricing_specialist() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Sport Subscription Pricing & Bundle Architect",
        goal=(
            "Design a defensible per-sport SKU structure, Sharp/Pro tier pricing, "
            "year-round bundle architecture, and launch sequencing strategy for a "
            "sport-tech subscription product — maximising ARPU and conversion "
            "while managing the complexity of multi-sport seasonal coverage."
        ),
        backstory=(
            "You are a Pricing Strategist with 12 years of experience designing "
            "subscription models for sport-data, sports-betting, and sports-media "
            "products across B2C markets in the US, UK, Australia, and Asia. "
            "You have priced sport-specific SaaS products at OddsJam, Action Network, "
            "Betway, and comparable operators. You understand that sport subscriptions "
            "are structurally different from generic SaaS: customers think in seasons "
            "not calendar years, coverage gaps kill retention, and a single-sport "
            "subscriber is inherently at risk of churn at season end. "
            "\n\n"
            "You are expert in: "
            "per-sport SKU design (Sharp / Pro / Elite tier ladders), "
            "seasonal pricing windows and annual equivalent pricing, "
            "multi-sport bundle discount architecture (2-sport, 3-sport, all-sport), "
            "user archetype packaging (US bettor vs international bettor), "
            "sport-specific bet structure edge cases (Horse Racing: Tote, SP, "
            "each-way; Cricket: format-specific; Rugby: union vs league), "
            "freemium-to-paid conversion in sport contexts, "
            "competitive benchmarking against OddsJam, Betegy, StatsBomb, "
            "Pinnacle, Bet365 data products, and similar. "
            "\n\n"
            "DISCIPLINE REQUIREMENTS: "
            "You MUST address every specific question, sport, price point, "
            "user archetype, competitor figure, bundle, and constraint named in the "
            "PROJECT BRIEF. You never substitute generic SaaS defaults. "
            "If the brief states OddsJam charges $399.99/mo for soccer, you use "
            "that figure in your competitive positioning. "
            "If the brief lists eight questions, you answer all eight explicitly. "
            "You do not invent user numbers (e.g. '50,000 free users in month 1') "
            "without basis in the brief or PRD — you model from stated assumptions "
            "and document them. "
            "\n\n"
            "FINANCE RATING REQUIREMENT: Begin with "
            "'FINANCE RATING: 🟢/🟡/🔴' and justify the rating in sport context. "
            "End with OPEN QUESTIONS listing pricing decisions for human input. "
            "CROSS-TEAM FLAGS: Flag any items requiring Legal (gambling regulations, "
            "geo-restrictions), Strategy (launch sequencing), or Marketing "
            "(positioning, promo mechanics) review."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_sport_pricing(context: dict, prd_text: str = "", bad_text: str = "",
                      roi_text: str = "", cea_text: str = "",
                      cli_context: str = "") -> tuple:
    """Produce SPS artifact. Returns (updated_context, sps_path).

    Args:
        context:     Project context dict (project_id, project_name, artifacts, status).
        prd_text:    PRD file contents.
        bad_text:    Business Analysis Document contents.
        roi_text:    ROI analysis contents.
        cea_text:    Cost Estimates & Budget contents.
        cli_context: Sport pricing brief supplied via --context flag.
                     Injected as PRIMARY INPUT ahead of all documents.
    """

    agent = build_sport_pricing_specialist()

    cli_block = ""
    if cli_context and cli_context.strip():
        cli_block = f"""
╔══════════════════════════════════════════════════════════════════╗
║  SPORT PRICING BRIEF  (PRIMARY INPUT — READ AND ACTION FIRST)   ║
╚══════════════════════════════════════════════════════════════════╝
{cli_context.strip()}

Every sport, question, price point, competitor figure, user archetype,
bundle scenario, and constraint described above MUST be addressed explicitly.
Do not substitute generic defaults. Do not omit any of the numbered questions.
══════════════════════════════════════════════════════════════════════
"""

    task = Task(
        description=f"""
You are the Sport Subscription Pricing & Bundle Architect for project
{context['project_id']} — {context['project_name']}.
{cli_block}
PRODUCT REQUIREMENTS DOCUMENT (excerpt):
{prd_text[:4000] if prd_text else "Not provided."}

BUSINESS ANALYSIS DOCUMENT (excerpt):
{bad_text[:2000] if bad_text else "Not provided."}

ROI & BUSINESS CASE ANALYSIS (excerpt):
{roi_text[:2000] if roi_text else "Not provided."}

COST ESTIMATES & BUDGET DOCUMENT (excerpt):
{cea_text[:2000] if cea_text else "Not provided."}

Produce a complete Sport Subscription Pricing & Bundle Architecture (SPS)
covering ALL sections below. Where the PROJECT BRIEF lists explicit questions,
answer them in the relevant section AND consolidate them in section 10.

─────────────────────────────────────────────────────────────────────

1. FINANCE RATING
   🟢 GREEN / 🟡 AMBER / 🔴 RED
   Justify the rating in terms of sport-specific pricing risk and revenue
   model viability (seasonality risk, churn windows, SKU complexity).

2. PRICING MODEL SELECTION
   Recommended model for a multi-sport subscription product:
   Per-sport tiered / All-sport flat / Hybrid bundle / Usage-based / Other.
   Rationale — why this model fits the product's go-to-market and the two
   user archetypes (US bettor, international bettor).

3. PER-SPORT SKU STRUCTURE
   For each sport in the brief, define:
   | Sport | Season Window | Sharp Price/mo | Pro Price/mo | Annual Sharp | Annual Pro |
   Justify each price point. Note any sport with non-standard tier logic
   (e.g. Horse Racing — Tote/SP/each-way complexity).
   Flag Phase 1 vs Phase 2 sports explicitly.

4. ELITE / ALL-SPORTS TIER
   Recommended Elite (all-sports) monthly and annual price.
   Positioning vs per-sport stacking.
   Effective discount vs buying all sports individually.

5. BUNDLE ARCHITECTURE
   Define at least the following bundles; add others if warranted by the brief:
   - US Bundle (Soccer + NFL + NBA or similar)
   - International Bundle (Soccer + Cricket + Rugby or similar)
   - Australian Bundle (Soccer + AFL + Cricket or similar)
   - Summer Fill (Soccer + MLB or similar)
   For each bundle:
   | Bundle Name | Sports Included | Monthly Price | Annual Price | Discount vs Individual |
   Justify the discount depth (2-sport, 3-sport, all-sport tiers).
   Recommend discount percentages and explain the economics.

6. LAUNCH SEQUENCING
   Phase 1 launch: which sports, which tiers, which bundles go live first and why.
   Migration strategy: launch with sport-based pricing vs migrate post-launch.
   Promo mechanics: first-N-signups offer, free Sharp promo, sunset of flat model.

7. COMPETITIVE POSITIONING
   Benchmark against named competitors in the brief (use stated figures).
   | Competitor | Sport | Their Price | Our Sharp | Our Pro | Our Position |
   Where are we priced relative to market? What does that signal to the customer?

8. USER ARCHETYPE PACKAGING
   US Bettor: Recommended starting SKU/bundle, expected upgrade path, ARPU.
   International Bettor: Recommended starting SKU/bundle, expected upgrade path, ARPU.
   Seasonal gap risk: what happens at season end? Retention mechanics.

9. UNIT ECONOMICS
   | Tier / Bundle | Monthly Price | COGS | Gross Margin % | LTV (12mo) | LTV (36mo) |
   Use the gross margin and fixed-cost figures from the brief where provided.
   Model ARPU for BASE, UPSIDE, and DOWNSIDE cases.
   12-month revenue projection table — base case only, with stated assumptions.
   Do not fabricate user volumes without basis; document every assumption.

10. EXPLICIT QUESTION RESPONSES
    Answer each numbered question from the PROJECT BRIEF in order.
    Label each: Q1, Q2, Q3 … Match the question count exactly.

11. PRICING RISKS
    Top risks specific to sport subscription pricing:
    - Seasonal churn at season end
    - SKU complexity driving decision paralysis
    - Geo-restriction / gambling regulation exposure
    - Competitor price compression
    Mitigation for each.

12. CROSS-TEAM FLAGS
    Items requiring review by: Legal / Strategy / Marketing / Finance Orchestrator.

13. OPEN QUESTIONS
    Pricing decisions requiring human input before launch.
    Unanswered items from the brief that need stakeholder resolution.

Output as well-formatted markdown.

{build_assumption_instructions()}
""",
        expected_output=(
            "Complete Sport Subscription Pricing & Bundle Architecture (SPS) in markdown. "
            "Opens with FINANCE RATING: 🟢/🟡/🔴. "
            "All numbered brief questions answered in section 10. "
            "No generic defaults substituted for specifics in the brief. "
            "Ends with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        agent=agent
    )

    crew   = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n🏟️  Sport Pricing Specialist producing SPS for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{out_dir}/{context['project_id']}_SPS_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 SPS saved: {path}")
    context["artifacts"].append({
        "name":       "Sport Subscription Pricing & Bundle Architecture",
        "type":       "SPS",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Sport Pricing Specialist"
    })
    context["status"] = "SPS_COMPLETE"
    context.setdefault("events", [])
    context.setdefault("logs", [])
    context.setdefault("project_name", context.get("project_id", "Unknown"))

    log_event(context, "SPS_COMPLETE", path)
    save_context(context)
    return context, path


# ── CLI ────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sport_pricing_specialist.py",
        description=(
            "Finance Group — Sport Subscription Pricing & Bundle Architect (SPS)\n\n"
            "Designs per-sport SKU structures, Sharp/Pro tiers, seasonal coverage\n"
            "bundles, and user-archetype packaging for sport-tech subscriptions.\n\n"
            "Use --context to pass the full sport pricing brief. The agent treats\n"
            "this as the PRIMARY INPUT and answers every question in it explicitly.\n"
            "Without --context the agent will use PRD and artifact context only."
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
        help="Path to the PRD markdown file.",
    )
    p.add_argument(
        "--context-file",
        dest="cli_context_file",
        default=None,
        help=(
            "Path to a .txt or .md file containing the pricing brief. "
            "Avoids shell $ escaping issues. "
            "If both --context and --context-file are supplied, --context-file wins."
        ),
    )
    p.add_argument(
        "--context",
        dest="cli_context",
        default=None,
        help=(
            "Full sport pricing brief. Injected verbatim as PRIMARY INPUT into the "
            "agent task. Include: sports roster, launch dates, current pricing, "
            "proposed tiers, user archetypes, competitor prices, bundles, and "
            "numbered questions you want answered."
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

    # ── Resolve --context-file (wins over --context if both supplied) ──────────
    if args.cli_context_file:
        _ctx_file_path = pathlib.Path(args.cli_context_file).expanduser()
        if not _ctx_file_path.exists():
            print(f"❌ --context-file not found: {_ctx_file_path}")
            import sys; sys.exit(1)
        args.cli_context = _ctx_file_path.read_text(encoding="utf-8").strip()
        print(f"📋 Context brief loaded from file: {_ctx_file_path} ({len(args.cli_context)} chars)")

    # ── Resolve project context ────────────────────────────────────────────────
    if args.project_id:
        context = {
            "project_id":   args.project_id,
            "project_name": args.project_id,
            "artifacts":    [],
            "status":       "SPS_STANDALONE",
        }
        print(f"📂 Using explicit project-id: {args.project_id}")
    else:
        logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
        if not logs:
            print(
                "❌ No project context found. "
                "Pass --project-id or ensure logs/PROJ-*.json exists."
            )
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

    if not prd_text and not args.cli_context:
        print(
            "⚠️  No PRD and no --context brief provided. "
            "Agent will have limited sport-specific context."
        )

    # ── Run ───────────────────────────────────────────────────────────────────
    # ── Input guard ───────────────────────────────────────────────────────────
    project_id = check_required_inputs(
        context.get("project_id", "PROJ-UNKNOWN"),
        prd_text,
        args.cli_context or "",
    )
    context["project_id"] = project_id

    context, path = run_sport_pricing(
        context,
        prd_text=prd_text,
        bad_text=bad_text,
        roi_text=roi_text,
        cea_text=cea_text,
        cli_context=args.cli_context or "",
    )

    print(f"\n✅ SPS complete: {path}")
    with open(path) as f:
        print(f.read(500))
