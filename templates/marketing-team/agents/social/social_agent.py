import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context, request_human_approval

load_dotenv("config/.env")


def build_social_agent() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Social Media Agent",
        goal=(
            "Research trending topics in sports betting and analytics, draft daily "
            "on-brand posts for X, Instagram, TikTok, and Discord, generate or source "
            "supporting visuals, and submit every post for human approval before "
            "scheduling or publishing."
        ),
        backstory=(
            "You are a Social Media Strategist and Copywriter with 8 years of experience "
            "building engaged audiences for data-driven sports and fintech brands. "
            "You have an instinct for what resonates on each platform — X rewards "
            "sharp, data-literate takes and well-constructed threads; Instagram rewards "
            "clean visuals and punchy sub-copy; TikTok rewards hooks that land in the "
            "first two seconds; Discord rewards authenticity and community ownership. "
            "You use trend search APIs to identify breakout topics in sports betting, "
            "fantasy sports, and sports analytics before they peak. You know how to "
            "ride a trending moment without compromising brand integrity. "
            "You write in the PROJECT_NAME_PLACEHOLDER brand voice without exception: direct, "
            "data-literate, quietly confident. You never hype. You never guarantee. "
            "You never say 'beat the bookies.' You never sound like a tipster. "
            "Every post you draft references real model logic, real data, or a real "
            "educational concept — you do not manufacture engagement bait. "
            "You understand the visual identity: Deep Navy backgrounds, Signal Teal "
            "accents, clean data layouts. You brief image generation tools with "
            "precise, on-brand prompts and review outputs before including them. "
            "You produce a Daily Post Pack for each platform with copy, visual brief, "
            "hashtag set, and recommended posting time. You never publish without "
            "explicit human approval."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_daily_post_pack(context: dict, platform: str, topic: str, sport: str) -> dict:
    """
    Draft a daily post pack for a given platform and topic.
    Submits for human approval before saving as publishable.
    Returns updated context.
    """
    sa = build_social_agent()

    draft_task = Task(
        description=f"""
You are the PROJECT_NAME_PLACEHOLDER Social Media Agent. Draft a complete post pack for the
following brief:

Platform: {platform}
Topic: {topic}
Sport / Competition: {sport}
Brand Voice: Direct, data-literate, quietly confident. Never hypes. Never guarantees.
             Never says 'beat the bookies'. Never sounds like a tipster.

BRAND RULES — NEVER VIOLATE:
- No guaranteed wins, guaranteed returns, or certainty of outcome language
- Never say "we predict" — PROJECT_NAME_PLACEHOLDER surfaces opportunities; users decide
- No "beat the bookies" or adversarial framing
- No language implying the platform replaces judgment rather than informing it

Produce a complete Daily Post Pack with ALL of the following:

1. PLATFORM-SPECIFIC POST COPY
   - Primary copy (platform character limit compliant)
   - For X: thread structure if >280 chars (number each post 1/N)
   - For Instagram: caption + first comment hashtag block
   - For TikTok: hook (first 2 seconds), body, CTA, on-screen text cues
   - For Discord: channel recommendation + message tone notes

2. VISUAL BRIEF
   - Description of the required visual or graphic
   - Colour: Deep Navy (#0A1628) background, Signal Teal (#00D4B4) accents
   - Data elements to display (if applicable)
   - Image generation prompt (ready for Imagen/DALL-E/Midjourney)

3. HASHTAG SET
   - Primary hashtags (3–5, high relevance)
   - Secondary hashtags (5–8, discovery)
   - Brand hashtag: #PROJECT_NAME_PLACEHOLDER

4. ENGAGEMENT HOOKS
   - One question to drive comments/replies
   - One CTA (e.g., link in bio, sign up for waitlist, join Discord)

5. SCHEDULING RECOMMENDATION
   - Recommended post time (timezone: ET)
   - Rationale (audience online patterns, sport schedule alignment)

6. COMPLIANCE CHECK
   - Confirm no guaranteed outcome language
   - Confirm no "beat the bookies" framing
   - Confirm no tipster-style picks without methodology reference
   - Confirm responsible gambling footer included where required

Output the complete Daily Post Pack as well-formatted markdown.
""",
        expected_output="A complete Daily Post Pack in markdown with copy, visual brief, hashtags, and compliance check.",
        agent=sa
    )

    crew = Crew(
        agents=[sa],
        tasks=[draft_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n📱 Social Agent drafting {platform} post pack — {topic}...\n")
    result = crew.kickoff()

    os.makedirs("output/posts", exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    draft_path = f"output/posts/{context['campaign_id']}_{platform}_{timestamp}_DRAFT.md"

    with open(draft_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Post pack draft saved: {draft_path}")

    # ── Human-in-the-loop: approval gate ─────────────────────────────────────
    approved = request_human_approval(
        gate_type="POST",
        artifact_path=draft_path,
        summary=f"{platform} post — {topic} ({sport})"
    )

    if approved:
        approved_path = draft_path.replace("_DRAFT.md", "_APPROVED.md")
        os.rename(draft_path, approved_path)
        context["artifacts"].append({
            "name": f"{platform} Post Pack — {topic}",
            "type": "POST",
            "platform": platform,
            "path": approved_path,
            "status": "APPROVED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Social Agent"
        })
        log_event(context, "POST_APPROVED", approved_path)
        context["status"] = "POST_APPROVED"
    else:
        context["artifacts"].append({
            "name": f"{platform} Post Pack — {topic}",
            "type": "POST",
            "platform": platform,
            "path": draft_path,
            "status": "REJECTED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Social Agent"
        })
        log_event(context, "POST_REJECTED", draft_path)
        context["status"] = "POST_REJECTED"

    save_context(context)
    return context


if __name__ == "__main__":
    from agents.orchestrator.orchestrator import create_campaign_context

    context = create_campaign_context(
        campaign_name="World Cup 2026 Launch Week",
        campaign_type="SOCIAL"
    )

    context = run_daily_post_pack(
        context=context,
        platform="X",
        topic="xG model — Group Stage Day 1 signals",
        sport="FIFA World Cup 2026"
    )

    print(f"\n✅ Social agent run complete. Status: {context['status']}")
