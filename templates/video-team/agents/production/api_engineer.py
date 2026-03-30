"""
agents/production/api_engineer.py

API Production Engineer — calls approved video/audio APIs, assembles output.

This agent runs AFTER human approval of both the tool selection (TRR)
and the script (SP). It is the only agent that makes external API calls
and writes video files to disk.

Output directory: output/renders/
  Raw files are saved as {VIDEO_ID}_{SCENE}_{ts}_RAW.{ext}
  Assembled output: {VIDEO_ID}_{MODE}_{ts}_ASSEMBLED.mp4

After assembly, the flow triggers the VIDEO_FINAL HITL gate before
marking any file as publishable.
"""
import sys
sys.path.insert(0, "/home/mfelkey/video-team")

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from agents.orchestrator.base_agent import build_video_agent

load_dotenv("config/.env")


def build_api_engineer() -> object:
    return build_video_agent(
        role="API Production Engineer",
        goal=(
            "Execute the approved video and audio production briefs by calling "
            "the selected APIs, handling errors and retries, saving all raw "
            "generated assets to output/renders/, and producing an assembly "
            "manifest for the final video package."
        ),
        backstory=(
            "You are a senior production engineer with deep expertise in AI "
            "generation APIs — Veo 2 (Vertex AI), Runway Gen-4, Kling, HeyGen, "
            "ElevenLabs, Suno, and their equivalents. You consume the Tool "
            "Recommendation Report to know exactly which APIs are approved for "
            "this job. You never call an API that was not approved in the TRR. "
            "You consume the Visual Direction Brief, Audio Production Brief, "
            "Script Package, and Avatar Production Brief as your execution "
            "instructions. You do not interpret or adjust their creative content "
            "— you execute them faithfully. "
            "You implement robust API call patterns: exponential backoff on rate "
            "limits, clear error messages on auth failures, and graceful "
            "degradation (if a scene fails after three retries, you log it as "
            "GENERATION_FAILED and continue with remaining scenes rather than "
            "halting the entire job). "
            "You save all raw generated assets to output/renders/ with the naming "
            "convention {VIDEO_ID}_{SCENE}_{timestamp}_RAW.{ext}. You produce an "
            "Assembly Manifest (JSON) listing every asset, its scene number, "
            "duration, and generation status. You flag any GENERATION_FAILED "
            "scenes prominently in the manifest so the human can decide at the "
            "VIDEO_FINAL gate whether to re-run those scenes or accept the gap. "
            "You never write to any directory outside output/renders/. "
            "You never publish, upload, or share any file — that is always a "
            "human decision after the VIDEO_FINAL approval gate."
        ),
        tier="TIER2",
    )


# ── API caller helpers ────────────────────────────────────────────────────────

def _call_with_retry(fn, max_attempts: int = 3, backoff_base: int = 5):
    """Call fn() with exponential backoff. Returns (success, result)."""
    for attempt in range(max_attempts):
        try:
            result = fn()
            return True, result
        except Exception as e:
            wait = backoff_base * (2 ** attempt)
            print(f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    return False, None


def call_runway(prompt: str, duration: int, api_key: str) -> dict:
    """
    Call Runway Gen-4 API.
    Returns {"status": "ok"|"failed", "asset_url": str, "error": str}
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06",
    }
    payload = {
        "model": "gen4_turbo",
        "promptText": prompt,
        "duration": duration,
        "ratio": "1280:720",
    }
    def _call():
        r = requests.post(
            "https://api.dev.runwayml.com/v1/image_to_video",
            headers=headers, json=payload, timeout=120
        )
        r.raise_for_status()
        return r.json()

    ok, data = _call_with_retry(_call)
    if ok and data:
        return {"status": "ok", "task_id": data.get("id"), "error": None}
    return {"status": "failed", "task_id": None, "error": "Max retries exceeded"}


def call_heygen(script: str, avatar_id: str, voice_id: str, api_key: str) -> dict:
    """
    Call HeyGen v2 API to generate an avatar video.
    Returns {"status": "ok"|"failed", "video_id": str, "error": str}
    """
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": avatar_id},
            "voice": {"type": "text", "input_text": script, "voice_id": voice_id},
        }],
        "dimension": {"width": 1280, "height": 720},
    }
    def _call():
        r = requests.post(
            "https://api.heygen.com/v2/video/generate",
            headers=headers, json=payload, timeout=120
        )
        r.raise_for_status()
        return r.json()

    ok, data = _call_with_retry(_call)
    if ok and data:
        return {"status": "ok", "video_id": data.get("data", {}).get("video_id"), "error": None}
    return {"status": "failed", "video_id": None, "error": "Max retries exceeded"}


def call_elevenlabs_tts(text: str, voice_id: str, api_key: str,
                         output_path: str) -> dict:
    """
    Call ElevenLabs TTS and save MP3 to output_path.
    Returns {"status": "ok"|"failed", "path": str, "error": str}
    """
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }
    def _call():
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers, json=payload, timeout=60, stream=True
        )
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path

    ok, path = _call_with_retry(_call)
    if ok:
        return {"status": "ok", "path": path, "error": None}
    return {"status": "failed", "path": None, "error": "Max retries exceeded"}


def build_assembly_manifest(video_id: str, scenes: list,
                              output_dir: str) -> str:
    """
    Write assembly manifest JSON.
    scenes: [{"scene": int, "asset_path": str, "duration": int,
               "status": "ok"|"failed", "error": str}]
    """
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/{video_id}_MANIFEST_{ts}.json"
    manifest = {
        "video_id": video_id,
        "generated_at": datetime.utcnow().isoformat(),
        "total_scenes": len(scenes),
        "succeeded": sum(1 for s in scenes if s["status"] == "ok"),
        "failed": sum(1 for s in scenes if s["status"] == "failed"),
        "scenes": scenes,
    }
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"💾 Assembly manifest saved: {path}")
    return path
