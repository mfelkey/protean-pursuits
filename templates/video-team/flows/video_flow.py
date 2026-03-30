"""
flows/video_flow.py

Protean Pursuits — Video Team Flow

Run modes:
  BRIEF_ONLY  — tool evaluation + script + visual + audio (no API calls)
  SHORT_FORM  — full pipeline, <60s social (TikTok / Reels / Shorts)
  LONG_FORM   — full pipeline, 2–10min (YouTube / website)
  AVATAR      — full pipeline, avatar/spokesperson foregrounded
  DEMO        — script + audio + production (screen recording input supplied by human)
  EXPLAINER   — full pipeline, animated explainer / motion graphics
  VOICEOVER   — script + audio + production (no visual generation)
  FULL        — all modes sequenced as a campaign package

HITL gates (3 per job):
  1. VIDEO_TOOL_SELECTION — after TRR: approve the tool stack before any brief is written
  2. SCRIPT_REVIEW        — after SP: approve the full script before any generation
  3. VIDEO_FINAL          — after production: approve rendered output before publishable

Usage:
  python flows/video_flow.py --mode short_form
      --name "PROJECT_NAME_PLACEHOLDER Launch Teaser"
      --project-id PROJ-TEMPLATE
      --format TIKTOK
      --topic "What makes our signal different"
      --duration 45

  python flows/video_flow.py --mode avatar
      --name "PROJECT_NAME_PLACEHOLDER Spokesperson"
      --project-id PROJ-TEMPLATE
      --format SHORTS
      --topic "How to read our dashboard"
      --duration 60
      --avatar-config '{"avatar_id":"heygenXXX","name":"Alex","style":"professional","voice_id":"elvXXX","language":"en-US","custom_notes":""}'

  python flows/video_flow.py --mode demo
      --name "PROJECT_NAME_PLACEHOLDER Dashboard Demo"
      --project-id PROJ-TEMPLATE
      --recording-path /path/to/screen_recording.mp4
      --topic "Onboarding walkthrough"
"""

import sys
sys.path.insert(0, "/home/mfelkey/video-team")

import os
import json
import argparse
from datetime import datetime
from crewai import Task, Crew, Process
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import (
    build_video_orchestrator,
    create_video_context, save_context, log_event, save_artifact,
    notify_human, request_human_approval, VIDEO_STANDARDS,
)
from agents.tool_intelligence.tool_analyst import build_tool_analyst
from agents.script.script_writer import build_script_writer
from agents.visual.visual_director import build_visual_director
from agents.avatar.avatar_producer import build_avatar_producer
from agents.audio.audio_producer import build_audio_producer
from agents.production.api_engineer import build_api_engineer
from agents.compliance.compliance_reviewer import build_compliance_reviewer

load_dotenv("config/.env")

TOOL_CACHE_PATH = os.getenv("VIDEO_TOOL_CACHE_PATH", "memory/tool_cache.json")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_tool_cache() -> dict:
    if os.path.exists(TOOL_CACHE_PATH):
        with open(TOOL_CACHE_PATH) as f:
            return json.load(f)
    return {}


def _save_tool_cache(trr_data: dict) -> None:
    os.makedirs(os.path.dirname(TOOL_CACHE_PATH) or "memory", exist_ok=True)
    with open(TOOL_CACHE_PATH, "w") as f:
        json.dump({
            "last_updated": datetime.utcnow().isoformat(),
            "recommendation": trr_data,
        }, f, indent=2)


def _run_agent(agent, context: dict, task_description: str,
               expected_output: str, prior: str = "") -> tuple:
    """Run a single agent task and save the artifact. Returns (result_str, path)."""
    full_description = (
        f"Project: {context['project_name']} (ID: {context['project_id']})\n"
        f"Video ID: {context['video_id']}\n"
        f"Run Mode: {context['run_mode']}\n\n"
        f"{task_description}"
        + (f"\n\nPrior outputs for context:\n{prior}" if prior else "")
        + f"\n\n{VIDEO_STANDARDS}"
    )
    task = Task(
        description=full_description,
        expected_output=expected_output,
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    role_slug = agent.role.replace(" ", "_").replace("&", "and").upper()
    print(f"\n🎬 [{role_slug}] Running...\n")
    result = str(crew.kickoff())
    path = save_artifact(
        context, agent.role, role_slug, result,
        "output/briefs" if role_slug != "API_PRODUCTION_ENGINEER" else "output/renders",
    )
    return result, path


# ── Gate 1: Tool selection ────────────────────────────────────────────────────

def run_tool_evaluation(context: dict, video_format: str, topic: str) -> dict:
    """
    Run the Tool Intelligence Analyst and fire VIDEO_TOOL_SELECTION gate.
    Returns context with tool_selection populated.
    """
    prior_cache = _load_tool_cache()
    prior_summary = (
        f"Previous recommendation (for delta comparison):\n"
        f"{json.dumps(prior_cache.get('recommendation', {}), indent=2)}"
        if prior_cache else "No previous recommendation on file."
    )

    analyst = build_tool_analyst()
    task_desc = (
        f"Search the web RIGHT NOW for the latest AI video and audio generation "
        f"tools and APIs. Today's date is {datetime.utcnow().strftime('%Y-%m-%d')}. "
        f"Do not rely solely on training data — search for recent releases, "
        f"benchmarks, and API availability changes.\n\n"
        f"Target format: {video_format}\n"
        f"Topic: {topic}\n\n"
        f"{prior_summary}\n\n"
        f"Produce a complete Tool Recommendation Report (TRR) with:\n"
        f"1. TOP 3 VIDEO GENERATION TOOLS — ranked with scores on all 6 criteria\n"
        f"2. PRIMARY VIDEO TOOL RECOMMENDATION — with full API call signature and "
        f"required env var names\n"
        f"3. TOP 3 AUDIO/MUSIC GENERATION TOOLS — ranked with scores\n"
        f"4. PRIMARY AUDIO TOOL RECOMMENDATION — with full API call signature and "
        f"required env var names\n"
        f"5. TTS/VOICEOVER TOOL RECOMMENDATION — for spoken voiceover generation\n"
        f"6. AVATAR PLATFORM RECOMMENDATION — for spokesperson/avatar content\n"
        f"7. DELTA FLAG: SAME or CHANGED vs prior recommendation, with rationale\n"
        f"8. OPEN QUESTIONS — any tool choices requiring human input"
    )

    result, path = _run_agent(
        analyst, context, task_desc,
        "Complete Tool Recommendation Report with rankings, API signatures, and delta flag.",
    )

    # Gate 1: human approves tool stack
    approved = request_human_approval(
        gate_type="VIDEO_TOOL_SELECTION",
        artifact_path=path,
        summary=f"Tool stack recommendation for {video_format} — {topic}",
    )

    if not approved:
        log_event(context, "TOOL_SELECTION_REJECTED", path)
        context["status"] = "TOOL_SELECTION_REJECTED"
        save_context(context)
        print("\n❌ Tool selection rejected. Edit the TRR or re-run with --mode brief_only.")
        return context

    # Parse and store approved tool selection
    context["tool_selection"] = {
        "approved_at": datetime.utcnow().isoformat(),
        "trr_path": path,
        "raw_recommendation": result[:500],  # excerpt for context
    }
    _save_tool_cache({"trr_path": path, "excerpt": result[:500]})
    log_event(context, "TOOL_SELECTION_APPROVED", path)
    context["status"] = "TOOL_SELECTION_APPROVED"
    save_context(context)
    return context


# ── Gate 2: Script review ─────────────────────────────────────────────────────

def run_script_phase(context: dict, video_format: str, topic: str,
                      duration: int, brand_brief: str,
                      include_visual: bool = True,
                      include_audio: bool = True,
                      include_avatar: bool = False) -> dict:
    """
    Run Script Writer, Visual Director, Audio Producer, and optionally Avatar Producer.
    Fire SCRIPT_REVIEW gate after Script Writer (before generation tools are called).
    Returns context with SP, VDB, AUB, APB artifacts.
    """
    tool_context = (
        f"Approved tool stack:\n{json.dumps(context.get('tool_selection', {}), indent=2)}\n\n"
    )
    avatar_context = (
        f"Avatar config:\n{json.dumps(context.get('avatar_config', {}), indent=2)}\n\n"
        if include_avatar else ""
    )

    # Script Writer
    script_desc = (
        f"{tool_context}{avatar_context}"
        f"Format: {video_format}\n"
        f"Topic: {topic}\n"
        f"Target Duration: {duration} seconds\n"
        f"Brand Brief: {brand_brief}\n\n"
        f"Produce a complete Script Package (SP) with:\n"
        f"- Full spoken script with MM:SS timestamps\n"
        f"- On-screen text / lower thirds at each timestamp\n"
        f"- B-roll / visual cue notes at each timestamp\n"
        f"- Hook (exact opening line)\n"
        f"- Body with analytical depth appropriate to format\n"
        f"- CTA (final call to action)\n"
        f"- Compliance disclaimer if required\n"
        f"- COMPLIANCE CHECKLIST at end\n"
        f"- OPEN QUESTIONS numbered list"
    )
    script_result, script_path = _run_agent(
        build_script_writer(), context, script_desc,
        "Complete Script Package with timestamps, on-screen text, and compliance checklist.",
    )

    # Gate 2: human approves script before any generation
    approved = request_human_approval(
        gate_type="SCRIPT_REVIEW",
        artifact_path=script_path,
        summary=f"Script for {video_format} — {topic} ({duration}s)",
    )

    if not approved:
        log_event(context, "SCRIPT_REJECTED", script_path)
        context["status"] = "SCRIPT_REJECTED"
        save_context(context)
        print("\n❌ Script rejected. Edit the SP and re-run from script phase.")
        return context

    log_event(context, "SCRIPT_APPROVED", script_path)
    prior = f"--- SCRIPT PACKAGE ---\n{script_result[:800]}...\n"

    # Visual Director (skip for VOICEOVER mode)
    if include_visual:
        visual_desc = (
            f"{tool_context}"
            f"Format: {video_format}\nTopic: {topic}\nDuration: {duration}s\n\n"
            f"Produce a complete Visual Direction Brief (VDB) aligned to the approved script. "
            f"Include scene-by-scene direction, shot types, motion, colour grading, "
            f"AI image frame specs where needed, full prompt strings for the approved "
            f"video generation tool, and transition specifications."
        )
        visual_result, _ = _run_agent(
            build_visual_director(), context, visual_desc,
            "Complete Visual Direction Brief with per-scene prompts and specs.",
            prior=prior,
        )
        prior += f"\n--- VISUAL DIRECTION BRIEF ---\n{visual_result[:600]}...\n"

    # Audio Producer
    if include_audio:
        audio_desc = (
            f"{tool_context}"
            f"Format: {video_format}\nTopic: {topic}\nDuration: {duration}s\n\n"
            f"Produce a complete Audio Production Brief (AUB) using the approved "
            f"audio tool. Include music generation prompt, TTS/voiceover parameters, "
            f"SFX cue sheet, and mix guide."
        )
        _run_agent(
            build_audio_producer(), context, audio_desc,
            "Complete Audio Production Brief with music prompt, TTS params, and mix guide.",
            prior=prior,
        )

    # Avatar Producer (only for AVATAR mode)
    if include_avatar:
        avatar_desc = (
            f"Avatar config: {json.dumps(context.get('avatar_config', {}), indent=2)}\n\n"
            f"Produce a complete Avatar Production Brief (APB) for the approved script. "
            f"Include dialogue segmentation, expression direction, gesture notes, "
            f"background specification, and full API call parameters for the approved "
            f"avatar platform."
        )
        _run_agent(
            build_avatar_producer(), context, avatar_desc,
            "Complete Avatar Production Brief with API parameters and expression direction.",
            prior=prior,
        )

    context["status"] = "BRIEFS_COMPLETE"
    save_context(context)
    return context


# ── Gate 3: Production + final approval ──────────────────────────────────────

def run_production_phase(context: dict, recording_path: str = None) -> dict:
    """
    Run API Production Engineer and Compliance Reviewer.
    Fire VIDEO_FINAL gate after compliance review.
    recording_path: path to human-supplied screen recording (DEMO mode only).
    """
    tool_context = json.dumps(context.get("tool_selection", {}), indent=2)
    artifacts_summary = json.dumps(
        [{"name": a["name"], "path": a["path"]} for a in context.get("artifacts", [])],
        indent=2
    )

    # API Production Engineer
    prod_desc = (
        f"Approved tool stack:\n{tool_context}\n\n"
        f"All production briefs are in output/briefs/. "
        f"Artifact index:\n{artifacts_summary}\n\n"
        + (f"Screen recording supplied at: {recording_path}\n"
           f"Produce AI-generated intro/outro clips and voiceover to wrap it.\n\n"
           if recording_path else "")
        + f"Execute the production briefs:\n"
        f"1. Call the approved video generation API for each scene in the VDB\n"
        f"2. Call the approved audio/TTS API for voiceover and music\n"
        f"3. Call the approved avatar API if an APB is present\n"
        f"4. Save all raw generated assets to output/renders/ with correct naming\n"
        f"5. Produce an Assembly Manifest JSON listing all assets and statuses\n"
        f"6. Flag any GENERATION_FAILED scenes prominently\n"
        f"Do NOT publish, upload, or share any file."
    )
    prod_result, prod_path = _run_agent(
        build_api_engineer(), context, prod_desc,
        "Assembly Manifest JSON and summary of all generated assets.",
    )

    prior = f"--- PRODUCTION MANIFEST ---\n{prod_result[:800]}...\n"

    # Compliance Reviewer
    compliance_desc = (
        f"Review the complete video production package for this job.\n"
        f"All artifacts are indexed at:\n{artifacts_summary}\n\n"
        f"Production output:\n{prior}\n\n"
        f"Produce a Compliance Report (COR) with:\n"
        f"1. OVERALL RATING: PASS / CONDITIONAL PASS / FAIL\n"
        f"2. BRAND COMPLIANCE findings\n"
        f"3. PLATFORM POLICY findings\n"
        f"4. LEGAL & REGULATORY findings\n"
        f"5. TECHNICAL SPEC findings\n"
        f"6. ITEMISED ISSUES — specific fix instructions for any finding\n"
        f"7. CLEARED FOR HUMAN REVIEW: YES / NO"
    )
    _, compliance_path = _run_agent(
        build_compliance_reviewer(), context, compliance_desc,
        "Compliance Report with PASS/CONDITIONAL PASS/FAIL rating and itemised findings.",
        prior=prior,
    )

    # Gate 3: human final approval
    approved = request_human_approval(
        gate_type="VIDEO_FINAL",
        artifact_path=compliance_path,
        summary=(
            f"Final video package for {context['project_name']} "
            f"({context['run_mode']}). Review compliance report and renders."
        ),
    )

    if not approved:
        log_event(context, "VIDEO_FINAL_REJECTED", compliance_path)
        context["status"] = "VIDEO_FINAL_REJECTED"
        save_context(context)
        print("\n❌ Final video rejected. Review COR findings and re-run production phase.")
        return context

    # Mark render files as approved
    renders_dir = "output/renders"
    if os.path.isdir(renders_dir):
        for fname in os.listdir(renders_dir):
            if context["video_id"] in fname and "_RAW" in fname:
                approved_name = fname.replace("_RAW", "_APPROVED")
                os.rename(
                    os.path.join(renders_dir, fname),
                    os.path.join(renders_dir, approved_name),
                )

    log_event(context, "VIDEO_FINAL_APPROVED", compliance_path)
    context["status"] = "VIDEO_FINAL_APPROVED"
    save_context(context)
    print(f"\n✅ Video package approved. Video ID: {context['video_id']}")
    return context


# ── Mode runners ──────────────────────────────────────────────────────────────

def run_brief_only(context: dict, video_format: str, topic: str,
                    duration: int, brand_brief: str) -> dict:
    context = run_tool_evaluation(context, video_format, topic)
    if context["status"] != "TOOL_SELECTION_APPROVED":
        return context
    context = run_script_phase(
        context, video_format, topic, duration, brand_brief,
        include_visual=True, include_audio=True, include_avatar=False,
    )
    return context


def run_short_form(context: dict, video_format: str, topic: str,
                    duration: int, brand_brief: str) -> dict:
    context = run_tool_evaluation(context, video_format, topic)
    if context["status"] != "TOOL_SELECTION_APPROVED":
        return context
    context = run_script_phase(
        context, video_format, topic, duration, brand_brief,
        include_visual=True, include_audio=True, include_avatar=False,
    )
    if context["status"] != "BRIEFS_COMPLETE":
        return context
    return run_production_phase(context)


def run_long_form(context: dict, video_format: str, topic: str,
                   duration: int, brand_brief: str) -> dict:
    context = run_tool_evaluation(context, video_format, topic)
    if context["status"] != "TOOL_SELECTION_APPROVED":
        return context
    context = run_script_phase(
        context, video_format, topic, duration, brand_brief,
        include_visual=True, include_audio=True, include_avatar=False,
    )
    if context["status"] != "BRIEFS_COMPLETE":
        return context
    return run_production_phase(context)


def run_avatar(context: dict, video_format: str, topic: str,
                duration: int, brand_brief: str) -> dict:
    if not context.get("avatar_config"):
        print("❌ avatar_config is required for AVATAR mode. Pass --avatar-config.")
        context["status"] = "AVATAR_CONFIG_MISSING"
        return context
    context = run_tool_evaluation(context, video_format, topic)
    if context["status"] != "TOOL_SELECTION_APPROVED":
        return context
    context = run_script_phase(
        context, video_format, topic, duration, brand_brief,
        include_visual=True, include_audio=True, include_avatar=True,
    )
    if context["status"] != "BRIEFS_COMPLETE":
        return context
    return run_production_phase(context)


def run_demo(context: dict, topic: str, duration: int,
              brand_brief: str, recording_path: str) -> dict:
    if not recording_path or not os.path.exists(recording_path):
        print(f"❌ Screen recording not found at: {recording_path}")
        context["status"] = "RECORDING_NOT_FOUND"
        return context
    context = run_tool_evaluation(context, "DEMO", topic)
    if context["status"] != "TOOL_SELECTION_APPROVED":
        return context
    context = run_script_phase(
        context, "DEMO", topic, duration, brand_brief,
        include_visual=False, include_audio=True, include_avatar=False,
    )
    if context["status"] != "BRIEFS_COMPLETE":
        return context
    return run_production_phase(context, recording_path=recording_path)


def run_explainer(context: dict, video_format: str, topic: str,
                   duration: int, brand_brief: str) -> dict:
    context = run_tool_evaluation(context, video_format, topic)
    if context["status"] != "TOOL_SELECTION_APPROVED":
        return context
    context = run_script_phase(
        context, video_format, topic, duration, brand_brief,
        include_visual=True, include_audio=True, include_avatar=False,
    )
    if context["status"] != "BRIEFS_COMPLETE":
        return context
    return run_production_phase(context)


def run_voiceover(context: dict, topic: str, duration: int,
                   brand_brief: str) -> dict:
    context = run_tool_evaluation(context, "VOICEOVER", topic)
    if context["status"] != "TOOL_SELECTION_APPROVED":
        return context
    context = run_script_phase(
        context, "VOICEOVER", topic, duration, brand_brief,
        include_visual=False, include_audio=True, include_avatar=False,
    )
    if context["status"] != "BRIEFS_COMPLETE":
        return context
    return run_production_phase(context)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — Video Team")
    parser.add_argument("--mode", required=True,
                        choices=["brief_only", "short_form", "long_form",
                                 "avatar", "demo", "explainer", "voiceover", "full"])
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--project-id", default=None)
    parser.add_argument("--format", default="TIKTOK",
                        choices=["TIKTOK", "REELS", "SHORTS", "YOUTUBE",
                                 "WEBSITE", "DEMO", "VOICEOVER"])
    parser.add_argument("--topic", default="", help="Video topic / brief")
    parser.add_argument("--duration", type=int, default=60, help="Target duration in seconds")
    parser.add_argument("--brand-brief", default="", help="Brand voice / guidelines text")
    parser.add_argument("--avatar-config", default=None,
                        help="JSON string of per-project avatar config")
    parser.add_argument("--recording-path", default=None,
                        help="Path to screen recording (DEMO mode only)")
    args = parser.parse_args()

    avatar_config = None
    if args.avatar_config:
        try:
            avatar_config = json.loads(args.avatar_config)
        except json.JSONDecodeError:
            print("❌ --avatar-config must be valid JSON.")
            sys.exit(1)

    context = create_video_context(
        project_name=args.name,
        run_mode=args.mode.upper(),
        project_id=args.project_id,
        avatar_config=avatar_config,
    )

    print(f"\n🎬 Protean Pursuits Video Team | {args.mode.upper()} | {args.name}")
    print(f"   Video ID: {context['video_id']}\n")

    mode = args.mode.lower()
    if mode == "brief_only":
        context = run_brief_only(context, args.format, args.topic,
                                  args.duration, args.brand_brief)
    elif mode == "short_form":
        context = run_short_form(context, args.format, args.topic,
                                  args.duration, args.brand_brief)
    elif mode == "long_form":
        context = run_long_form(context, args.format, args.topic,
                                 args.duration, args.brand_brief)
    elif mode == "avatar":
        context = run_avatar(context, args.format, args.topic,
                              args.duration, args.brand_brief)
    elif mode == "demo":
        context = run_demo(context, args.topic, args.duration,
                            args.brand_brief, args.recording_path)
    elif mode == "explainer":
        context = run_explainer(context, args.format, args.topic,
                                 args.duration, args.brand_brief)
    elif mode == "voiceover":
        context = run_voiceover(context, args.topic, args.duration,
                                 args.brand_brief)
    elif mode == "full":
        print("FULL mode runs all formats in sequence. "
              "Run each mode separately for campaign packages.")
        sys.exit(0)

    print(f"\n✅ Done. Video ID: {context['video_id']} | Status: {context['status']}")
