"""
agents/dev/finance/billing_architect.py

Finance specialist — Billing & Payment Feature Spec (BPS)

Specifies billing and payment feature requirements: provider selection,
subscription/one-time/usage models, invoicing flows, refund handling,
PCI/compliance requirements.

Skipped automatically if no billing language is detected in the PRD.
When billing_integration=true in the project context, BPS is passed to
the Backend and Frontend developers as an authoritative upstream spec.

Run standalone:
  python agents/dev/finance/billing_architect.py
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

from core.input_guard import check_required_inputs, build_assumption_instructions


def build_billing_architect() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="Billing Architect",
        goal=(
            "Specify all billing and payment feature requirements with enough "
            "precision that a Backend Developer and Frontend Developer can "
            "implement them without follow-up questions."
        ),
        backstory=(
            "You are a Billing Architect with 13 years of experience designing "
            "payment systems and billing infrastructure for SaaS and marketplace "
            "companies. You have deep expertise in Stripe, Braintree, PayPal, "
            "and Adyen — and you know when to use each one. You understand "
            "PCI DSS compliance inside out and you know how to minimise "
            "scope for card data by design. "
            "You design billing systems that are: simple to implement initially, "
            "extensible for future pricing models, compliant with relevant "
            "regulations, and operationally maintainable (you have seen too "
            "many billing systems become unmaintainable nightmares). "
            "When billing_integration is true in the project context, your "
            "output (BPS) is consumed directly by the Backend and Frontend "
            "developers — treat it as an authoritative implementation spec, "
            "not a high-level guide. Include exact API call sequences, webhook "
            "event handlers required, database table changes, and UI flow "
            "requirements. "
            "FINANCE RATING REQUIREMENT: Begin with "
            "'FINANCE RATING: 🟢/🟡/🔴' and justify the rating. "
            "End with OPEN QUESTIONS listing billing decisions for human input."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_billing_spec(context: dict, prd_text: str = "",
                     tad_text: str = "", srr_text: str = "") -> tuple:
    """Produce BPS from PRD + TAD + SRR. Returns (updated_context, bps_path)."""

    billing_integration = context.get("billing_integration", False)
    ba = build_billing_architect()

    task = Task(
        description=f"""
You are the Billing Architect for project {context['project_id']} — {context['project_name']}.
billing_integration: {billing_integration}

PRODUCT REQUIREMENTS DOCUMENT (excerpt):
{prd_text[:5000] if prd_text else "Not provided."}

TECHNICAL ARCHITECTURE DOCUMENT (excerpt):
{tad_text[:3000] if tad_text else "Not provided."}

SECURITY REVIEW REPORT (excerpt):
{srr_text[:2000] if srr_text else "Not provided."}

Produce a complete Billing & Payment Feature Spec (BPS) covering ALL sections:

1. FINANCE RATING
   🟢 GREEN / 🟡 AMBER / 🔴 RED — with justification focused on payment risk
   and compliance posture.

2. BILLING MODEL
   Which billing model(s) this product uses:
   - Subscription (monthly/annual, per-seat, per-tier)
   - Usage-based (per-API-call, per-GB, per-event)
   - One-time purchase
   - Freemium with paid upgrade
   - Enterprise custom pricing
   Describe each model with pricing structure.

3. PAYMENT PROVIDER SELECTION
   Recommended provider with rationale. Alternatives considered.
   Key selection criteria: geography, fee structure, PCI scope reduction,
   developer experience, webhook reliability.

4. PAYMENT FLOWS (implementation-ready)
   For each payment scenario (subscription create, upgrade, downgrade,
   cancellation, one-time purchase, refund, failed payment):
   - User journey steps
   - Required API calls (provider + internal)
   - Webhook events to handle
   - Database state changes
   - UI state changes

5. SUBSCRIPTION LIFECYCLE
   Trial → paid → dunning → cancelled → reactivated.
   Dunning strategy: retry schedule, grace period, account suspension logic.

6. INVOICING & RECEIPTS
   Invoice generation: when, what data, format.
   Receipt emails: trigger events, required content.
   Tax handling: VAT/GST applicability, tax collection requirements.

7. REFUND POLICY & IMPLEMENTATION
   Policy (full/partial/no refunds, time window).
   Implementation: provider API calls, database updates, email triggers.

8. PCI DSS COMPLIANCE APPROACH
   PCI scope: how card data is handled (hosted fields, tokenisation).
   SAQ level applicable.
   Compliance responsibilities (what you own vs. what the provider owns).

9. DATABASE SCHEMA ADDITIONS
   New tables or columns required for billing:
   subscriptions, invoices, payment_methods, billing_events.
   With field names and types.

10. SECURITY REQUIREMENTS (from SRR cross-reference)
    Billing-specific security requirements surfaced by the SRR.
    How BPS addresses each.

11. OPEN QUESTIONS
    Billing decisions requiring human input before implementation begins.

{"NOTE: billing_integration=true — this BPS will be consumed by Backend and Frontend developers as an authoritative implementation spec. Be precise and complete." if billing_integration else "NOTE: billing_integration=false — this is advisory only."}

Output as well-formatted markdown.

{build_assumption_instructions()}
""",
        expected_output="Complete Billing & Payment Feature Spec in markdown.",
        agent=ba
    )

    crew   = Crew(agents=[ba], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n💰 Billing Architect producing BPS for: {context['project_name']}\n")
    result = str(crew.kickoff())

    out_dir = "output/finance"
    os.makedirs(out_dir, exist_ok=True)
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path    = f"{out_dir}/{context['project_id']}_BPS_{ts}.md"
    with open(path, "w") as f:
        f.write(result)

    print(f"\n💾 BPS saved: {path}")
    context["artifacts"].append({
        "name":       "Billing & Payment Feature Spec",
        "type":       "BPS",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Billing Architect"
    })
    context["status"] = "BPS_COMPLETE"
    log_event(context, "BPS_COMPLETE", path)
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

    prd_text = tad_text = srr_text = ""
    for a in context.get("artifacts", []):
        t = a.get("type")
        p = a.get("path", "")
        if os.path.exists(p):
            with open(p) as f:
                txt = f.read(8000)
            if t == "PRD": prd_text = txt
            if t == "TAD": tad_text = txt
            if t == "SRR": srr_text = txt

    print(f"📂 Loaded context: {logs[0]}")
    project_id = check_required_inputs(
        context.get("project_id", "PROJ-UNKNOWN"),
        prd_text,
        "",
    )
    context["project_id"] = project_id
    context, path = run_billing_spec(context, prd_text, tad_text, srr_text)
    print(f"\n✅ BPS complete: {path}")
    with open(path) as f:
        print(f.read(500))