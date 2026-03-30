"""
agents/dev/finance/finance_orchestrator.py

Protean Pursuits — Finance Group Orchestrator

Sub-crew of dev-team. Runs after full planning (after ux_content_guide.py)
and before the build phase. Advisory only — never blocks the pipeline.

What it does:
  1. Reads PRD + TAD to determine which specialist agents are relevant
  2. Auto-detects billing_integration from PRD language
  3. Sequences the 7 specialist agents: CEA → ROI → ICM → BPS → PRI → FSR → SCF
  4. Skips agents that are not relevant (logs reason)
  5. Reviews each output for internal consistency
  6. Retries a failed agent once before escalating
  7. Compiles the Finance Summary Package (FSP)
  8. Fires CP-4.5 (Finance Review checkpoint)

All Finance outputs are advisory. RED ratings surface as FLAGS — they never
block the pipeline automatically. You decide at CP-4.5 whether to proceed.

Run:
  python agents/dev/finance/finance_orchestrator.py
  (must be run from the dev-team root with a PROJ-*.json in logs/)

Single-agent shortcut:
  python agents/dev/finance/cost_analyst.py   # just the CEA
"""

import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import re
import json
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

# ── Finance rating constants ─────────────────────────────────────────────────

RATING_GREEN  = "🟢 GREEN"
RATING_AMBER  = "🟡 AMBER"
RATING_RED    = "🔴 RED"

FINANCE_INSTRUCTION = """
FINANCE OUTPUT STANDARDS — MANDATORY ON ALL OUTPUTS:

1. RATING LINE: Every Finance artifact must open with a one-line rating:
   FINANCE RATING: 🟢 GREEN | 🟡 AMBER | 🔴 RED
   Green = financially sound; Amber = proceed with noted caveats;
   Red = significant financial risk — flag for human review.

2. ASSUMPTIONS DOCUMENTED: Every numeric estimate must list its assumptions
   explicitly. Never present a number without its source or methodology.

3. SCENARIO RANGE: Where applicable, present LOW / MID / HIGH scenarios.
   Low = conservative; Mid = base case; High = optimistic.

4. NO FABRICATED NUMBERS: Do not invent market data, industry benchmarks,
   or competitor pricing. State "benchmark data not available — internal
   estimate" when you are working from first principles.

5. ADVISORY ONLY: All Finance outputs are advisory. They inform decisions —
   they do not make them. End every output with an OPEN QUESTIONS section
   listing decisions that require human input before build begins.

6. CROSS-REFERENCE: Where your artifact builds on another Finance output
   (e.g., FSR builds on CEA + ROI + ICM + PRI), explicitly cite the
   upstream artifact version and flag any inconsistencies you detect.
"""

# ── Billing trigger keywords ─────────────────────────────────────────────────

BILLING_KEYWORDS = [
    "payment", "billing", "subscription", "invoice", "invoicing",
    "stripe", "paypal", "braintree", "checkout", "charge", "credit card",
    "revenue", "monetize", "monetisation", "pricing tier", "paid plan",
    "freemium", "pro plan", "enterprise plan", "SaaS pricing", "usage-based",
    "seat-based", "per-user", "annual contract", "monthly plan", "refund",
    "dunning", "PCI", "payment gateway", "recurring", "one-time purchase",
]

INTERNAL_TOOL_KEYWORDS = [
    "internal tool", "internal tooling", "internal dashboard",
    "employee portal", "admin panel", "back-office", "backoffice",
    "no public users", "no external users", "staff only", "internal use only",
]


# ── Notification helpers ─────────────────────────────────────────────────────

def _send_sms(message: str) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        sms_addr = os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "") + "@txt.att.net"
        msg = MIMEText(message[:160])
        msg["From"] = os.getenv("OUTLOOK_ADDRESS")
        msg["To"]   = sms_addr
        msg["Subject"] = ""
        with smtplib.SMTP("smtp.office365.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️  SMS failed: {e}")
        return False


def _send_email(subject: str, body: str) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg["From"]    = os.getenv("OUTLOOK_ADDRESS")
        msg["To"]      = os.getenv("HUMAN_EMAIL")
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.office365.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️  Email failed: {e}")
        return False


def _notify(subject: str, message: str) -> None:
    _send_sms(f"[FINANCE] {subject}\n{message}")
    _send_email(f"[FINANCE] {subject}", message)


# ── CP-4.5 HITL gate ─────────────────────────────────────────────────────────

def request_finance_review(fsp_path: str, summary: str,
                            timeout_hours: int = 48) -> bool:
    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    review_id   = f"FIN-{uuid.uuid4().hex[:8].upper()}"
    request_file = f"{approval_dir}/{review_id}.json"
    response_file = f"{approval_dir}/{review_id}.response.json"

    with open(request_file, "w") as f:
        json.dump({
            "review_id":      review_id,
            "checkpoint":     "CP-4.5",
            "artifact_path":  fsp_path,
            "summary":        summary,
            "requested_at":   datetime.utcnow().isoformat(),
            "status":         "PENDING"
        }, f, indent=2)

    _notify(
        subject=f"[CP-4.5 FINANCE REVIEW] {review_id}",
        message=(
            f"Summary: {summary}\n"
            f"FSP: {fsp_path}\n\n"
            f"Approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n'
            f"Reject:  {{\"decision\": \"REJECTED\", \"reason\": \"...\"}}\n"
            f"Timeout: {timeout_hours}h"
        )
    )
    print(f"\n⏸️  CP-4.5 FINANCE REVIEW [{review_id}] — {summary}")
    print(f"📄 Review FSP: {fsp_path}")
    print(f"   Respond via: {response_file}")

    elapsed = 0
    while elapsed < timeout_hours * 3600:
        if os.path.exists(response_file):
            with open(response_file) as f:
                resp = json.load(f)
            decision = resp.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ CP-4.5 Approved — {review_id}")
                return True
            elif decision == "REJECTED":
                reason = resp.get("reason", "No reason given")
                print(f"❌ CP-4.5 Rejected — {review_id}: {reason}")
                return False
        time.sleep(30)
        elapsed += 30

    print(f"⏰ CP-4.5 timed out — {review_id}")
    return False


# ── Context helpers ───────────────────────────────────────────────────────────

def _load_artifact(context: dict, artifact_type: str,
                   max_chars: int = 6000) -> str:
    for a in context.get("artifacts", []):
        if a.get("type") == artifact_type and os.path.exists(a.get("path", "")):
            with open(a["path"]) as f:
                return f.read(max_chars)
    return ""


def _save_finance_artifact(context: dict, artifact_type: str,
                           content: str) -> str:
    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{out_dir}/{context['project_id']}_{artifact_type}_{ts}.md"
    with open(path, "w") as f:
        f.write(content)
    context["artifacts"].append({
        "name":       f"Finance — {artifact_type}",
        "type":       artifact_type,
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Finance Orchestrator"
    })
    log_event(context, f"{artifact_type}_COMPLETE", path)
    save_context(context)
    print(f"\n💾 [{artifact_type}] Saved: {path}")
    return path


# ── Detection helpers ─────────────────────────────────────────────────────────

def detect_billing_integration(prd_text: str) -> bool:
    text_lower = prd_text.lower()
    return any(kw.lower() in text_lower for kw in BILLING_KEYWORDS)


def detect_internal_tool(prd_text: str) -> bool:
    text_lower = prd_text.lower()
    return any(kw.lower() in text_lower for kw in INTERNAL_TOOL_KEYWORDS)


# ── Finance Orchestrator agent ────────────────────────────────────────────────

def build_finance_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Finance Orchestrator",
        goal=(
            "Produce a complete Finance Summary Package (FSP) by sequencing the "
            "Finance specialist agents — CEA, ROI, ICM, BPS, PRI, FSR, SCF — "
            "cross-checking their outputs for consistency, and synthesising a "
            "single executive-readable summary for CP-4.5 human review."
        ),
        backstory=(
            "You are the Finance Director at Protean Pursuits LLC — a corporate "
            "finance leader with 20 years of experience spanning CFO roles at "
            "SaaS, fintech, and data companies. You understand both the technical "
            "architecture of software products and the financial models that make "
            "them viable. You lead seven specialist Finance agents and are "
            "responsible for the financial picture of every project before a "
            "single line of production code is written. "
            "You sequence your specialists based on what the project actually "
            "needs — you skip irrelevant agents and log your reasoning. You cross-"
            "check numbers across outputs (e.g., does the ICM align with the TAD? "
            "does the FSR reflect the CEA totals?) and flag inconsistencies. You "
            "produce the Finance Summary Package: a single document consolidating "
            "all Finance outputs with overall ratings and open flags. "
            "You are advisory only — your job is to give the human the clearest "
            "possible financial picture, not to block the pipeline."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )


# ── Specialist runner ─────────────────────────────────────────────────────────

def _run_specialist(agent: Agent, context: dict, task_description: str,
                    artifact_type: str, max_retries: int = 1) -> tuple:
    """Run a Finance specialist agent, retry once on empty output."""
    for attempt in range(max_retries + 1):
        task = Task(
            description=task_description,
            expected_output=(
                f"Complete {artifact_type} Finance artifact beginning with "
                f"'FINANCE RATING: 🟢/🟡/🔴' and ending with an OPEN QUESTIONS section."
            ),
            agent=agent,
            max_retries=0
        )
        crew   = Crew(agents=[agent], tasks=[task],
                      process=Process.sequential, verbose=True)
        result = str(crew.kickoff())
        if len(result.strip()) > 200:
            path = _save_finance_artifact(context, artifact_type, result)
            return result, path
        print(f"⚠️  {artifact_type} output too short (attempt {attempt + 1}). "
              f"{'Retrying...' if attempt < max_retries else 'Escalating.'}")
    _notify(f"Finance agent failed — {artifact_type}",
            f"Project: {context['project_id']}\nOutput was empty after retries.")
    return "", ""


# ── FSP synthesis ─────────────────────────────────────────────────────────────

def _synthesise_fsp(context: dict, results: dict,
                    skipped: dict, billing_integration: bool) -> str:
    orch    = build_finance_orchestrator()
    excerpts = {k: v[:500] + "..." for k, v in results.items() if v}
    task = Task(
        description=f"""
You are the Finance Orchestrator for {context['project_id']} — {context['project_name']}.

All Finance specialist agents have completed. Synthesise their outputs into a
Finance Summary Package (FSP) — a single executive-readable document.

SPECIALIST OUTPUTS (excerpts):
{json.dumps(excerpts, indent=2)}

AGENTS SKIPPED:
{json.dumps(skipped, indent=2)}

BILLING INTEGRATION: {"ENABLED — BPS will feed into build pipeline" if billing_integration else "DISABLED"}

Your FSP must include ALL of the following sections:

1. OVERALL FINANCE RATING
   One of: 🟢 GREEN / 🟡 AMBER / 🔴 RED
   Brief justification (2-3 sentences).

2. EXECUTIVE SUMMARY (2 pages maximum)
   Key financial conclusions, recommendation (proceed / revise scope / halt),
   and the three most important financial risks.

3. ARTIFACT RATINGS TABLE
   | Artifact | Rating | Key Finding | Action Required |
   One row per artifact that ran.

4. OPEN FLAGS
   Numbered list of all 🔴 RED ratings and the most significant 🟡 AMBER
   items from any artifact. Each flag: description, artifact source, and
   recommended resolution.

5. BILLING INTEGRATION NOTE
   If billing_integration is true: confirm that BPS is in scope for the
   Backend and Frontend developers and summarise the key billing requirements.
   If false: state that no billing integration was detected.

6. AGENTS SKIPPED
   List skipped agents with the reason for each.

7. NEXT STEPS FOR CP-4.5 REVIEW
   Checklist the human reviewer should work through before approving.

{FINANCE_INSTRUCTION}
""",
        expected_output="Complete Finance Summary Package (FSP) in markdown.",
        agent=orch
    )
    crew   = Crew(agents=[orch], tasks=[task], process=Process.sequential, verbose=True)
    result = str(crew.kickoff())
    return result


# ── Main Finance crew run ─────────────────────────────────────────────────────

def run_finance_crew(context: dict) -> dict:
    """
    Entry point. Sequences all relevant Finance specialist agents,
    synthesises the FSP, and fires CP-4.5.
    Returns updated context.
    """
    from agents.dev.finance.cost_analyst          import build_cost_analyst,          run_cost_analysis
    from agents.dev.finance.roi_analyst           import build_roi_analyst,           run_roi_analysis
    from agents.dev.finance.infra_finance_modeler import build_infra_finance_modeler, run_infra_model
    from agents.dev.finance.billing_architect     import build_billing_architect,     run_billing_spec
    from agents.dev.finance.pricing_specialist    import build_pricing_specialist,    run_pricing_model
    from agents.dev.finance.financial_statements  import build_financial_statements,  run_financial_statements
    from agents.dev.finance.strategic_corp_finance import build_strategic_corp_finance, run_strategic_corp_finance

    project_id   = context["project_id"]
    project_name = context["project_name"]

    print(f"\n💰 Finance Orchestrator starting | {project_id} — {project_name}\n")

    # ── Read upstream artifacts ───────────────────────────────────────────────
    prd_text = _load_artifact(context, "PRD", max_chars=8000)
    tad_text = _load_artifact(context, "TAD", max_chars=6000)
    bad_text = _load_artifact(context, "BAD", max_chars=4000)
    srr_text = _load_artifact(context, "SRR", max_chars=3000)

    if not prd_text:
        print("❌ No PRD found in project context. Run product_manager.py first.")
        log_event(context, "FINANCE_ABORTED", "PRD not found")
        return context

    # ── Detection ─────────────────────────────────────────────────────────────
    billing_integration = detect_billing_integration(prd_text)
    is_internal         = detect_internal_tool(prd_text)

    context.setdefault("finance_crew", {
        "triggered_by":   "finance_orchestrator",
        "billing_integration": billing_integration,
        "agents_run":     [],
        "agents_skipped": [],
        "retry_log":      [],
        "status":         "RUNNING"
    })
    context["billing_integration"] = billing_integration

    print(f"🔍 Billing integration detected: {billing_integration}")
    print(f"🔍 Internal tool detected:       {is_internal}")

    results = {}
    skipped = {}

    # ── 1. Cost Analyst — always runs ────────────────────────────────────────
    print("\n💰 [1/7] Cost Analyst — CEA")
    context, cea_path = run_cost_analysis(context, prd_text, tad_text)
    results["CEA"] = _load_artifact(context, "CEA", 2000)
    context["finance_crew"]["agents_run"].append("cost_analyst")

    # ── 2. ROI Analyst — always runs ─────────────────────────────────────────
    print("\n💰 [2/7] ROI Analyst — ROI")
    cea_text = _load_artifact(context, "CEA", 3000)
    context, roi_path = run_roi_analysis(context, prd_text, bad_text, cea_text)
    results["ROI"] = _load_artifact(context, "ROI", 2000)
    context["finance_crew"]["agents_run"].append("roi_analyst")

    # ── 3. Infrastructure Finance Modeler — always runs ──────────────────────
    print("\n💰 [3/7] Infrastructure Finance Modeler — ICM")
    context, icm_path = run_infra_model(context, tad_text, cea_text)
    results["ICM"] = _load_artifact(context, "ICM", 2000)
    context["finance_crew"]["agents_run"].append("infra_finance_modeler")

    # ── 4. Billing Architect — only if billing detected ──────────────────────
    if billing_integration:
        print("\n💰 [4/7] Billing Architect — BPS (billing detected)")
        context, bps_path = run_billing_spec(context, prd_text, tad_text, srr_text)
        results["BPS"] = _load_artifact(context, "BPS", 2000)
        context["finance_crew"]["agents_run"].append("billing_architect")
    else:
        reason = "No billing/payment language detected in PRD"
        print(f"\n⏭️  [4/7] Billing Architect — SKIPPED ({reason})")
        skipped["billing_architect"] = reason
        context["finance_crew"]["agents_skipped"].append(
            {"agent": "billing_architect", "reason": reason})

    # ── 5. Pricing Specialist — skip for pure internal tools ─────────────────
    if not is_internal:
        print("\n💰 [5/7] Pricing Specialist — PRI")
        roi_text = _load_artifact(context, "ROI", 2000)
        context, pri_path = run_pricing_model(
            context, prd_text, bad_text, roi_text, cea_text)
        results["PRI"] = _load_artifact(context, "PRI", 2000)
        context["finance_crew"]["agents_run"].append("pricing_specialist")
    else:
        reason = "Internal tooling project — external pricing model not applicable"
        print(f"\n⏭️  [5/7] Pricing Specialist — SKIPPED ({reason})")
        skipped["pricing_specialist"] = reason
        context["finance_crew"]["agents_skipped"].append(
            {"agent": "pricing_specialist", "reason": reason})

    # ── 6. Financial Statements Modeler — always runs ────────────────────────
    print("\n💰 [6/7] Financial Statements Modeler — FSR")
    roi_text = _load_artifact(context, "ROI", 2000)
    icm_text = _load_artifact(context, "ICM", 2000)
    pri_text = _load_artifact(context, "PRI", 2000)
    context, fsr_path = run_financial_statements(
        context, cea_text, roi_text, icm_text, pri_text)
    results["FSR"] = _load_artifact(context, "FSR", 2000)
    context["finance_crew"]["agents_run"].append("financial_statements")

    # ── 7. Strategic Corporate Finance — always runs last ────────────────────
    print("\n💰 [7/7] Strategic Corporate Finance Specialist — SCF")
    fsr_text = _load_artifact(context, "FSR", 2000)
    context, scf_path = run_strategic_corp_finance(
        context, prd_text, roi_text, icm_text, pri_text, fsr_text, cea_text)
    results["SCF"] = _load_artifact(context, "SCF", 2000)
    context["finance_crew"]["agents_run"].append("strategic_corp_finance")

    # ── Synthesise FSP ────────────────────────────────────────────────────────
    print("\n💰 Finance Orchestrator — synthesising FSP...")
    fsp_content = _synthesise_fsp(context, results, skipped, billing_integration)
    fsp_path    = _save_finance_artifact(context, "FSP", fsp_content)

    context["finance_crew"]["status"] = "COMPLETE"
    log_event(context, "FINANCE_CREW_COMPLETE", fsp_path)
    save_context(context)

    # ── CP-4.5 ────────────────────────────────────────────────────────────────
    approved = request_finance_review(
        fsp_path,
        f"Finance Review — {project_name} ({project_id})"
    )

    if approved:
        context["status"] = "FINANCE_APPROVED"
        log_event(context, "CP_4_5_APPROVED", fsp_path)
        print("\n✅ CP-4.5 approved — proceeding to build phase.")
        if billing_integration:
            print("💳 billing_integration=true — BPS will be passed to Backend + Frontend.")
    else:
        context["status"] = "FINANCE_REJECTED"
        log_event(context, "CP_4_5_REJECTED", fsp_path)
        print("\n❌ CP-4.5 rejected — re-run with updated scope or re-run finance_orchestrator.py.")

    save_context(context)
    return context


# ── Standalone entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("❌ No project context found. Run classify.py first.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    print(f"📂 Loaded context: {logs[0]}")
    context = run_finance_crew(context)

    print(f"\n✅ Finance crew complete.")
    print(f"   Status:              {context['status']}")
    print(f"   Billing integration: {context.get('billing_integration', False)}")
    fsp = next((a for a in context["artifacts"] if a["type"] == "FSP"), None)
    if fsp:
        print(f"   FSP: {fsp['path']}")
