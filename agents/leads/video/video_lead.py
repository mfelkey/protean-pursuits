"""agents/leads/video/video_lead.py — Video Team Lead

Coordinates the video-team's orchestrator flow. The PP project manager
calls `run_video_deliverable()` with a mode + structured parameters;
this module serializes the extras into a context JSON and invokes the
team flow as a subprocess via `invoke_team_flow`.

Mode casing is accepted in either case — "short_form" and "SHORT_FORM"
both resolve to the flow's SHORT_FORM mode. The flow itself uses the
UPPERCASE form throughout (function names, HITL gate IDs, output
directory names), so the lead upper-cases before passing through.

Structured parameters (video_format, duration, topic, brand_brief,
avatar_config, recording_path) are merged into a JSON payload and
passed to the flow via --context. The flow's load_context() parses
this into context["data"], from which agents read them.
"""
import json
import sys
sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow


MODES = {
    "BRIEF_ONLY", "SHORT_FORM", "LONG_FORM",
    "AVATAR", "DEMO", "EXPLAINER", "VOICEOVER", "FULL",
}

VIDEO_FORMATS = {
    "TIKTOK", "REELS", "SHORTS", "YOUTUBE", "WEBSITE", "DEMO", "VOICEOVER",
}


def build_video_lead():
    return build_team_lead(
        team_name="video-team",
        role="Video Team Lead",
        goal=(
            "Deliver complete, platform-optimised AI video production packages "
            "by coordinating the embedded video-team orchestrator — from tool "
            "selection through rendered output and human final approval."
        ),
        backstory=(
            "You are an Executive Video Producer with 15 years of experience "
            "producing AI-assisted video content for technology and analytics "
            "brands. You interface between PP project requirements and the "
            "video-team — translating campaign briefs into video flow invocations "
            "and reporting production status and final approved assets back to "
            "the Project Manager."
        ),
    )


def _normalise_mode(mode: str) -> str:
    """Accept mixed/lowercase and return the canonical UPPERCASE form."""
    if not mode:
        raise ValueError("mode is required")
    canon = mode.strip().upper()
    if canon not in MODES:
        raise ValueError(
            f"unknown video mode {mode!r}. "
            f"Valid modes: {sorted(MODES)}"
        )
    return canon


def _normalise_format(video_format: str) -> str:
    """Accept mixed/lowercase and return the canonical UPPERCASE form."""
    if not video_format:
        return "TIKTOK"
    canon = video_format.strip().upper()
    if canon not in VIDEO_FORMATS:
        raise ValueError(
            f"unknown video_format {video_format!r}. "
            f"Valid formats: {sorted(VIDEO_FORMATS)}"
        )
    return canon


def _build_task_string(mode: str, topic: str, brand_brief: str,
                       duration: int, video_format: str) -> str:
    """
    The flow requires --task (the natural-language work item). We build
    a reasonable default from the structured parameters if the caller
    didn't pass something richer via brand_brief.
    """
    if brand_brief:
        return brand_brief
    if topic:
        return (
            f"{mode.replace('_', ' ').title()} ({video_format}, "
            f"~{duration}s) — {topic}"
        )
    return f"{mode.replace('_', ' ').title()} ({video_format}, ~{duration}s)"


def _build_context_payload(
    context: dict,
    video_format: str,
    topic: str,
    duration: int,
    brand_brief: str,
    avatar_config: str,
    recording_path: str,
) -> str:
    """
    Merge the structured video parameters into a JSON blob the flow
    can parse via --context. avatar_config, if provided, may itself be
    a JSON string — we parse it so it nests correctly rather than
    ending up as an escaped string inside the payload.
    """
    payload = {
        "video_format": video_format,
        "duration": duration,
    }
    if topic:
        payload["topic"] = topic
    if brand_brief:
        payload["brand_brief"] = brand_brief
    if recording_path:
        payload["recording_path"] = recording_path
    if avatar_config:
        try:
            payload["avatar_config"] = json.loads(avatar_config)
        except (json.JSONDecodeError, TypeError):
            payload["avatar_config"] = avatar_config
    # Pass through any PP-level project identifiers the agents might
    # want downstream.
    if context.get("project_id"):
        payload["project_id"] = context["project_id"]
    if context.get("project_name"):
        payload["project_name"] = context["project_name"]
    return json.dumps(payload, separators=(",", ":"))


def run_video_deliverable(
    context: dict,
    mode: str,
    video_format: str = "TIKTOK",
    topic: str = "",
    duration: int = 60,
    brand_brief: str = "",
    avatar_config: str = "",
    recording_path: str = "",
) -> dict:
    """
    Invoke the video-team flow for a given mode.

    Args:
        context: PP-level project context (must include project_name;
            project_id is passed through if present).
        mode: Video flow mode. Accepts mixed case; normalized to UPPERCASE.
            One of: BRIEF_ONLY, SHORT_FORM, LONG_FORM, AVATAR, DEMO,
            EXPLAINER, VOICEOVER, FULL.
        video_format: Target format — TIKTOK, REELS, SHORTS, YOUTUBE,
            WEBSITE, DEMO, VOICEOVER. Default: TIKTOK.
        topic: Short description of the topic (used to build the flow's
            --task if brand_brief is not provided).
        duration: Target duration in seconds. Default: 60.
        brand_brief: Full brief text. If provided, becomes the flow's
            --task directly. Otherwise a task string is synthesized
            from mode + video_format + duration + topic.
        avatar_config: JSON string or opaque string describing the
            avatar rig (AVATAR mode only). Parsed into the context
            payload if it's valid JSON; passed through as a string
            otherwise.
        recording_path: Path to a screen recording file (DEMO mode).

    Returns:
        The mutated context dict (conventionally returned by
        invoke_team_flow).

    Raises:
        ValueError: if mode or video_format is not recognised.
    """
    canon_mode = _normalise_mode(mode)
    canon_format = _normalise_format(video_format)

    # The flow's own invariant: --save requires --project. We always
    # pass both when we have a project so save-worthy runs get persisted.
    project = (context.get("project_name") or "").strip()

    task = _build_task_string(
        mode=canon_mode,
        topic=topic,
        brand_brief=brand_brief,
        duration=duration,
        video_format=canon_format,
    )

    payload_json = _build_context_payload(
        context=context,
        video_format=canon_format,
        topic=topic,
        duration=duration,
        brand_brief=brand_brief,
        avatar_config=avatar_config,
        recording_path=recording_path,
    )

    args = [
        "--mode", canon_mode,
        "--task", task,
        "--context", payload_json,
    ]
    if project:
        args += ["--project", project, "--save"]

    return invoke_team_flow("video-team", "flows/video_flow.py", args, context)
