import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context, request_human_approval

load_dotenv("config/.env")


def build_video_agent() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Video Agent",
        goal=(
            "Script, structure, and produce video content for TikTok, YouTube Shorts, "
            "and long-form YouTube — including Veo visual direction briefs and Lyria 3 "
            "music briefs — and submit every video for human approval before publishing."
        ),
        backstory=(
            "You are a Video Producer and Scriptwriter with 10 years of experience "
            "creating high-performance short-form and long-form video content for "
            "data-driven sports, fintech, and analytics brands. "
            "You understand the grammar of each format: TikTok demands a hook in the "
            "first 1.5 seconds, a payoff before the 30-second mark, and a CTA that "
            "doesn't feel like an ad. YouTube Shorts follows similar rules but with "
            "more tolerance for depth. Long-form YouTube rewards structure, pacing, "
            "and genuine analytical insight over surface-level takes. "
            "You write scripts that sound natural when spoken — no corporate stiffness, "
            "no tipster hype. You write in the PROJECT_NAME_PLACEHOLDER brand voice: direct, "
            "data-literate, quietly confident. "
            "You produce complete Veo (Google) visual direction briefs — scene "
            "descriptions, shot types, motion direction, colour grading notes anchored "
            "to the PROJECT_NAME_PLACEHOLDER palette (Deep Navy, Signal Teal, Amber). "
            "You produce complete Lyria 3 (Google DeepMind) music briefs — mood, "
            "tempo, instrumentation, and energy arc for each video segment. "
            "You never produce content that guarantees outcomes, sounds like a tipster, "
            "or violates the PROJECT_NAME_PLACEHOLDER brand standing rules. Every video that "
            "references model outputs includes a clear 'for informational purposes' "
            "disclaimer. You never publish without explicit human approval."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_video_production(context: dict, format: str, topic: str,
                          sport: str, target_duration_seconds: int) -> dict:
    """
    Script and produce a complete video production package.
    format: 'TIKTOK' | 'SHORTS' | 'YOUTUBE'
    Submits for human approval before saving as publishable.
    Returns updated context.
    """
    va = build_video_agent()

    script_task = Task(
        description=f"""
You are the PROJECT_NAME_PLACEHOLDER Video Agent. Produce a complete video production package
for the following brief:

Format: {format}
Topic: {topic}
Sport / Competition: {sport}
Target Duration: {target_duration_seconds} seconds
Brand Voice: Direct, data-literate, quietly confident. Never hypes. Never guarantees.

BRAND RULES — NEVER VIOLATE:
- No guaranteed wins, guaranteed returns, or certainty of outcome language
- Never say "we predict" — surface opportunities; users decide
- No "beat the bookies" or adversarial framing
- Every model output reference must include a brief disclaimer

Produce a complete Video Production Package with ALL of the following:

1. SCRIPT
   - Full spoken script with timestamps (MM:SS)
   - On-screen text / lower thirds at each timestamp
   - B-roll / visual cue notes at each timestamp
   - Hook: exact opening line (first 1.5s for TikTok/Shorts)
   - Body: core content with analytical depth
   - CTA: final call-to-action (sign up, follow, join Discord)
   - Disclaimer: "PROJECT_NAME_PLACEHOLDER signals are for informational purposes only.
     Betting involves risk. Please gamble responsibly."

2. VEO VISUAL DIRECTION BRIEF
   - Scene-by-scene description (aligned to script timestamps)
   - Shot types (close-up, wide, data overlay, screen capture)
   - Motion direction (pan, zoom, cut speed)
   - Colour grading: Deep Navy (#0A1628), Signal Teal (#00D4B4), Amber (#F5A623)
   - Text overlay style and font direction
   - Transitions
   - Full Veo prompt string for each scene

3. LYRIA 3 MUSIC BRIEF
   - Overall mood: (e.g., focused, analytical, understated tension)
   - Tempo: BPM range
   - Instrumentation palette
   - Energy arc: (e.g., low build → peak at payoff → resolve at CTA)
   - Full Lyria 3 prompt string

4. PLATFORM OPTIMISATION NOTES
   - Aspect ratio and resolution spec
   - Caption / subtitle requirements
   - Thumbnail concept (for YouTube / Shorts)
   - First-frame visual recommendation (critical for TikTok autoplay)

5. COMPLIANCE CHECK
   - No guaranteed outcome language confirmed
   - Disclaimer present and positioned correctly
   - No tipster-style picks without methodology reference
   - Responsible gambling note included

Output the complete Video Production Package as well-formatted markdown.
""",
        expected_output="A complete Video Production Package with script, Veo brief, Lyria 3 brief, and compliance check.",
        agent=va
    )

    crew = Crew(
        agents=[va],
        tasks=[script_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🎬 Video Agent scripting {format} — {topic}...\n")
    result = crew.kickoff()

    os.makedirs("output/videos", exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    draft_path = f"output/videos/{context['campaign_id']}_{format}_{timestamp}_DRAFT.md"

    with open(draft_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Video production package saved: {draft_path}")

    # ── Human-in-the-loop: approval gate ─────────────────────────────────────
    approved = request_human_approval(
        gate_type="VIDEO",
        artifact_path=draft_path,
        summary=f"{format} — {topic} ({sport}, {target_duration_seconds}s)"
    )

    if approved:
        approved_path = draft_path.replace("_DRAFT.md", "_APPROVED.md")
        os.rename(draft_path, approved_path)
        context["artifacts"].append({
            "name": f"{format} Video — {topic}",
            "type": "VIDEO",
            "format": format,
            "path": approved_path,
            "status": "APPROVED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Video Agent"
        })
        log_event(context, "VIDEO_APPROVED", approved_path)
        context["status"] = "VIDEO_APPROVED"
    else:
        context["artifacts"].append({
            "name": f"{format} Video — {topic}",
            "type": "VIDEO",
            "format": format,
            "path": draft_path,
            "status": "REJECTED",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "Video Agent"
        })
        log_event(context, "VIDEO_REJECTED", draft_path)
        context["status"] = "VIDEO_REJECTED"

    save_context(context)
    return context


if __name__ == "__main__":
    from agents.orchestrator.orchestrator import create_campaign_context

    context = create_campaign_context(
        campaign_name="World Cup 2026 Launch Week",
        campaign_type="VIDEO"
    )

    context = run_video_production(
        context=context,
        format="TIKTOK",
        topic="What is xG and why should you care?",
        sport="FIFA World Cup 2026",
        target_duration_seconds=45
    )

    print(f"\n✅ Video agent run complete. Status: {context['status']}")
