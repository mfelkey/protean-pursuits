"""agents/leads/video/video_lead.py — Video Team Lead"""
import sys
sys.path.insert(0, "/home/mfelkey/protean-pursuits")
from agents.leads.base_lead import build_team_lead, invoke_team_flow


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

    mode: brief_only | short_form | long_form | avatar | demo |
          explainer | voiceover | full
    video_format: TIKTOK | REELS | SHORTS | YOUTUBE | WEBSITE | DEMO | VOICEOVER
    avatar_config: JSON string of per-project avatar definition (AVATAR mode)
    recording_path: path to screen recording file (DEMO mode)
    """
    args = [
        "--mode", mode,
        "--name", context["project_name"],
        "--format", video_format,
        "--duration", str(duration),
    ]
    if context.get("project_id"):
        args += ["--project-id", context["project_id"]]
    if topic:
        args += ["--topic", topic]
    if brand_brief:
        args += ["--brand-brief", brand_brief]
    if avatar_config:
        args += ["--avatar-config", avatar_config]
    if recording_path:
        args += ["--recording-path", recording_path]

    return invoke_team_flow("video-team", "flows/video_flow.py", args, context)
