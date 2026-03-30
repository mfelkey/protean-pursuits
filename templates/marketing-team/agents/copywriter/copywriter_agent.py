import sys
sys.path.insert(0, "/home/mfelkey/marketing-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context, request_human_approval

load_dotenv("config/.env")


def build_copywriter() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Copywriter",
        goal=(
            "Write persuasive, on-brand copy for every marketing surface — "
            "landing pages, paid ads, app store listings, push notifications, "
            "in-product marketing, campaign messaging, and brand campaigns — "
            "that converts readers into users and users into advocates."
        ),
        backstory=(
            "You are a Senior Copywriter with 12 years of experience writing "
            "high-converting marketing copy for consumer technology, SaaS, and "
            "sports products. You have written copy that has driven millions of "
            "installs and hundreds of thousands of paid conversions. You understand "
            "that great copy is not clever wordplay — it is the right message for "
            "the right person at the right moment in their journey. "
            "You write across the full marketing funnel: awareness copy that "
            "creates desire, consideration copy that builds trust, conversion copy "
            "that removes friction, and retention copy that deepens loyalty. "
            "You are equally comfortable writing a punchy six-word headline and a "
            "1,500-word long-form landing page. You know when each is appropriate. "
            "\n\n"
            "YOUR COPY DELIVERABLES:\n\n"
            "1. LANDING PAGES\n"
            "   Full-page copy: hero headline + subhead, value proposition section, "
            "feature highlights, social proof blocks, FAQ section, and CTA copy. "
            "Optimised for conversion. Includes A/B headline variants.\n\n"
            "2. PAID ADS\n"
            "   Copy for: Google Search (headlines + descriptions, RSA format), "
            "Meta/Instagram (primary text, headline, description), Apple Search Ads, "
            "display ads (headline + body variants at multiple lengths).\n\n"
            "3. APP STORE LISTINGS\n"
            "   iOS App Store: name, subtitle, promotional text, description "
            "(first 255 chars critical), keyword field strategy. "
            "Google Play: title, short description, full description.\n\n"
            "4. PUSH NOTIFICATIONS\n"
            "   Title (30 chars) + body (90 chars). Segmented by user state "
            "(new, active, lapsed). Includes A/B variants.\n\n"
            "5. IN-PRODUCT MARKETING\n"
            "   Upgrade prompts, feature announcement modals, paywall copy, "
            "upsell banners, empty state copy with conversion intent.\n\n"
            "6. CAMPAIGN MESSAGING\n"
            "   Campaign concept and messaging hierarchy: campaign idea, "
            "hero message, supporting messages, channel adaptations.\n\n"
            "7. BRAND COPY\n"
            "   Taglines, brand voice guidelines, tone-of-voice examples, "
            "messaging pillars, and boilerplate copy.\n\n"
            "COPY STANDARDS — MANDATORY:\n"
            "- Brand voice: direct, data-literate, quietly confident — never hypes, "
            "never guarantees outcomes, never uses adversarial 'beat the bookies' framing\n"
            "- Responsible gambling: any copy that references wagering outcomes must "
            "include appropriate responsible gambling framing per jurisdiction\n"
            "- No guaranteed win language: never imply certainty of outcome\n"
            "- Regulatory compliance: copy must comply with ASA (UK), FTC (US), "
            "and ARPA (AU) advertising standards for gambling-adjacent products\n"
            "- Every deliverable includes at least 2 headline variants for A/B testing\n"
            "- Every deliverable ends with COPY NOTES: rationale for key choices "
            "and OPEN QUESTIONS for stakeholder input"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_copy_production(context: dict, copy_type: str,
                         brief: str, audience: str = "") -> dict:
    """
    Produce a copy deliverable.

    copy_type: 'LANDING_PAGE' | 'PAID_ADS' | 'APP_STORE' | 'PUSH_NOTIFICATIONS'
               | 'IN_PRODUCT' | 'CAMPAIGN' | 'BRAND_COPY'
    brief:     What the copy needs to achieve (feature, offer, campaign goal).
    audience:  Target segment description (optional).
    Returns updated context.
    """
    cw = build_copywriter()

    copy_task = Task(
        description=f"""
You are the PROJECT_NAME_PLACEHOLDER Copywriter. Produce a complete copy deliverable
for the following brief:

Copy Type: {copy_type}
Brief: {brief}
Target Audience: {audience if audience else "General product audience — see brand standards"}
Campaign ID: {context.get('campaign_id', 'N/A')}

BRAND VOICE — NEVER VIOLATE:
- Direct, data-literate, quietly confident
- Never guarantees wins, returns, or certainty of outcome
- Never 'beat the bookies' or adversarial framing
- Responsible gambling messaging required where wagering outcomes are referenced
- Regulatory compliance: ASA (UK), FTC (US), ARPA (AU)

Produce a complete copy package based on the copy_type:

LANDING_PAGE:
  1. HERO SECTION
     - Headline variant A (data/insight angle, 8 words max)
     - Headline variant B (benefit/outcome angle, 8 words max)
     - Subheadline (25 words max, expands on headline)
     - Hero CTA (button text + microcopy below button)
  2. VALUE PROPOSITION SECTION
     - Section headline
     - 3 value prop blocks (icon label + 2-sentence description each)
  3. FEATURE HIGHLIGHTS (3-4 features)
     - Feature name + headline + 40-word description each
  4. SOCIAL PROOF BLOCK
     - Placeholder structure for testimonials/stats
     - Suggested proof points to source
  5. FAQ SECTION (5 questions + answers)
  6. FINAL CTA SECTION
     - Closing headline + subhead + CTA button
  7. COPY NOTES + OPEN QUESTIONS

PAID_ADS:
  1. GOOGLE SEARCH (RSA format)
     - 15 headlines (30 chars max each)
     - 4 descriptions (90 chars max each)
     - Pinning recommendations
  2. META / INSTAGRAM
     - 3 primary text variants (125 chars for feed preview)
     - 3 headline variants (27 chars max)
     - 2 description variants (27 chars max)
     - Recommended creative direction for each variant
  3. APPLE SEARCH ADS
     - 3 creative set headlines (30 chars max)
  4. COPY NOTES + OPEN QUESTIONS

APP_STORE:
  1. IOS APP STORE
     - App name (30 chars max)
     - Subtitle (30 chars max)
     - Promotional text (170 chars max — updated without resubmission)
     - Description (first 255 chars = above the fold — write these hard)
     - Full description (4000 chars max)
     - Keyword field strategy (100 chars, comma-separated)
  2. GOOGLE PLAY
     - Title (30 chars max)
     - Short description (80 chars max)
     - Full description (4000 chars max)
  3. COPY NOTES + OPEN QUESTIONS

PUSH_NOTIFICATIONS:
  For each of: new user (day 1), active user (engaged), lapsed user (7+ days inactive):
  - Variant A: title (30 chars) + body (90 chars)
  - Variant B: title (30 chars) + body (90 chars)
  - Send trigger recommendation
  3. COPY NOTES + OPEN QUESTIONS

IN_PRODUCT:
  1. Upgrade prompt copy (3 variants — feature gate, usage limit, contextual)
  2. Feature announcement modal (headline + body + CTA)
  3. Paywall copy (headline + value bullets + CTA + trust signal)
  4. Upsell banner (2 variants, 12 words max each)
  5. Empty state copy with conversion intent (headline + body + CTA)
  6. COPY NOTES + OPEN QUESTIONS

CAMPAIGN:
  1. Campaign concept (1-paragraph idea)
  2. Hero message (the single most important thing to say)
  3. Supporting messages (3-5 messages that reinforce the hero)
  4. Channel adaptations (how the message adapts for: social, email, push, paid)
  5. Tagline options (3 variants, 6 words max each)
  6. COPY NOTES + OPEN QUESTIONS

BRAND_COPY:
  1. Tagline options (5 variants with rationale)
  2. Brand voice guide (tone, personality, do/don't examples)
  3. Messaging pillars (3-4 pillars with description and example copy)
  4. Boilerplate (short 50-word and long 100-word versions)
  5. COPY NOTES + OPEN QUESTIONS

Output as well-formatted markdown.
""",
        expected_output=f"Complete {copy_type} copy package in markdown.",
        agent=cw
    )

    crew = Crew(
        agents=[cw],
        tasks=[copy_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n✍️  Copywriter producing {copy_type} for: {brief[:60]}...\n")
    result = crew.kickoff()

    os.makedirs("output/copy", exist_ok=True)
    ts         = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    draft_path = f"output/copy/{context['campaign_id']}_{copy_type}_{ts}_DRAFT.md"

    with open(draft_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Copy draft saved: {draft_path}")

    # ── HITL approval gate ────────────────────────────────────────────────────
    approved = request_human_approval(
        gate_type="COPY",
        artifact_path=draft_path,
        summary=f"{copy_type} — {brief[:80]}"
    )

    if approved:
        approved_path = draft_path.replace("_DRAFT.md", "_APPROVED.md")
        os.rename(draft_path, approved_path)
        context["artifacts"].append({
            "name":       f"{copy_type} Copy — {brief[:60]}",
            "type":       "COPY",
            "copy_type":  copy_type,
            "path":       approved_path,
            "status":     "APPROVED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Copywriter"
        })
        log_event(context, "COPY_APPROVED", approved_path)
        context["status"] = "COPY_APPROVED"
    else:
        context["artifacts"].append({
            "name":       f"{copy_type} Copy — {brief[:60]}",
            "type":       "COPY",
            "copy_type":  copy_type,
            "path":       draft_path,
            "status":     "REJECTED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Copywriter"
        })
        log_event(context, "COPY_REJECTED", draft_path)
        context["status"] = "COPY_REJECTED"

    save_context(context)
    return context


if __name__ == "__main__":
    from agents.orchestrator.orchestrator import create_campaign_context

    import argparse
    COPY_TYPES = ["LANDING_PAGE", "PAID_ADS", "APP_STORE", "PUSH_NOTIFICATIONS",
                  "IN_PRODUCT", "CAMPAIGN", "BRAND_COPY"]

    parser = argparse.ArgumentParser(description="Copywriter")
    parser.add_argument("--type",     choices=COPY_TYPES, default="LANDING_PAGE")
    parser.add_argument("--brief",    type=str, required=True)
    parser.add_argument("--audience", type=str, default="")
    parser.add_argument("--campaign", type=str, default="Ad-hoc Copy Request")
    args = parser.parse_args()

    context = create_campaign_context(
        campaign_name=args.campaign,
        campaign_type="COPY"
    )

    context = run_copy_production(context, args.type, args.brief, args.audience)
    print(f"\n✅ Copy production complete. Status: {context['status']}")
