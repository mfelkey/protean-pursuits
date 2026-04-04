"""
templates/video-team/config/config.py

Video Team — configuration loader.

Loads environment variables from config/.env (or system env).
All video team agents and flows import from here rather than
calling os.getenv() directly, so env var names are centralised.

Usage:
    from config.config import cfg
    model = cfg.TIER1_MODEL
    heygen_key = cfg.HEYGEN_API_KEY
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the config/ directory (sibling of this file)
_ENV_PATH = Path(__file__).parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    # Fallback: look for .env in the team root
    _TEAM_ROOT = Path(__file__).parent.parent
    _FALLBACK = _TEAM_ROOT / ".env"
    if _FALLBACK.exists():
        load_dotenv(_FALLBACK)


class _Config:
    """Central config object. Attributes are read from environment at access time."""

    # ── Model tiers ───────────────────────────────────────────────────────────
    @property
    def TIER1_MODEL(self) -> str:
        return os.getenv("TIER1_MODEL", "ollama/qwen3:32b")

    @property
    def TIER2_MODEL(self) -> str:
        return os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b")

    @property
    def OLLAMA_BASE_URL(self) -> str:
        return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # ── Notifications ─────────────────────────────────────────────────────────
    @property
    def HUMAN_EMAIL(self) -> str:
        return os.getenv("HUMAN_EMAIL", "")

    @property
    def HUMAN_PHONE_NUMBER(self) -> str:
        return os.getenv("HUMAN_PHONE_NUMBER", "")

    @property
    def OUTLOOK_ADDRESS(self) -> str:
        return os.getenv("OUTLOOK_ADDRESS", "")

    @property
    def OUTLOOK_PASSWORD(self) -> str:
        return os.getenv("OUTLOOK_PASSWORD", "")

    # ── Git / GitHub ──────────────────────────────────────────────────────────
    @property
    def GITHUB_TOKEN(self) -> str:
        return os.getenv("GITHUB_TOKEN", "")

    @property
    def GITHUB_USERNAME(self) -> str:
        return os.getenv("GITHUB_USERNAME", "")

    # ── Observability ─────────────────────────────────────────────────────────
    @property
    def LANGFUSE_PUBLIC_KEY(self) -> str:
        return os.getenv("LANGFUSE_PUBLIC_KEY", "")

    @property
    def LANGFUSE_SECRET_KEY(self) -> str:
        return os.getenv("LANGFUSE_SECRET_KEY", "")

    @property
    def LANGFUSE_HOST(self) -> str:
        return os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # ── Video generation APIs ─────────────────────────────────────────────────
    @property
    def VEO2_PROJECT_ID(self) -> str:
        return os.getenv("VEO2_PROJECT_ID", "")

    @property
    def VEO2_LOCATION(self) -> str:
        return os.getenv("VEO2_LOCATION", "us-central1")

    @property
    def GOOGLE_APPLICATION_CREDENTIALS(self) -> str:
        return os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    @property
    def RUNWAY_API_KEY(self) -> str:
        return os.getenv("RUNWAY_API_KEY", "")

    @property
    def KLING_API_KEY(self) -> str:
        return os.getenv("KLING_API_KEY", "")

    @property
    def PIKA_API_KEY(self) -> str:
        return os.getenv("PIKA_API_KEY", "")

    @property
    def LUMA_API_KEY(self) -> str:
        return os.getenv("LUMA_API_KEY", "")

    # ── Avatar APIs ───────────────────────────────────────────────────────────
    @property
    def HEYGEN_API_KEY(self) -> str:
        return os.getenv("HEYGEN_API_KEY", "")

    @property
    def SYNTHESIA_API_KEY(self) -> str:
        return os.getenv("SYNTHESIA_API_KEY", "")

    @property
    def DID_API_KEY(self) -> str:
        return os.getenv("DID_API_KEY", "")

    # ── Audio / TTS APIs ──────────────────────────────────────────────────────
    @property
    def ELEVENLABS_API_KEY(self) -> str:
        return os.getenv("ELEVENLABS_API_KEY", "")

    @property
    def SUNO_API_KEY(self) -> str:
        return os.getenv("SUNO_API_KEY", "")

    @property
    def UDIO_API_KEY(self) -> str:
        return os.getenv("UDIO_API_KEY", "")

    @property
    def STABLE_AUDIO_API_KEY(self) -> str:
        return os.getenv("STABLE_AUDIO_API_KEY", "")

    # ── Image generation ──────────────────────────────────────────────────────
    @property
    def REPLICATE_API_KEY(self) -> str:
        return os.getenv("REPLICATE_API_KEY", "")

    # ── Tool cache ────────────────────────────────────────────────────────────
    @property
    def VIDEO_TOOL_CACHE_PATH(self) -> str:
        return os.getenv("VIDEO_TOOL_CACHE_PATH", "memory/tool_cache.json")

    # ── Convenience helpers ───────────────────────────────────────────────────

    def has_video_api(self) -> bool:
        """True if at least one video generation API key is configured."""
        return any([
            self.VEO2_PROJECT_ID,
            self.RUNWAY_API_KEY,
            self.KLING_API_KEY,
            self.PIKA_API_KEY,
            self.LUMA_API_KEY,
        ])

    def has_avatar_api(self) -> bool:
        """True if at least one avatar API key is configured."""
        return any([
            self.HEYGEN_API_KEY,
            self.SYNTHESIA_API_KEY,
            self.DID_API_KEY,
        ])

    def has_audio_api(self) -> bool:
        """True if at least one TTS or music API key is configured."""
        return any([
            self.ELEVENLABS_API_KEY,
            self.SUNO_API_KEY,
            self.UDIO_API_KEY,
            self.STABLE_AUDIO_API_KEY,
        ])

    def api_summary(self) -> str:
        """Return a human-readable summary of which API categories are configured."""
        lines = []
        lines.append(f"  Video gen:  {'✓' if self.has_video_api() else '✗ (BRIEF_ONLY mode only)'}")
        lines.append(f"  Avatar:     {'✓' if self.has_avatar_api() else '✗ (AVATAR mode unavailable)'}")
        lines.append(f"  Audio/TTS:  {'✓' if self.has_audio_api() else '✗ (script + visual only)'}")
        return "\n".join(lines)


# Singleton — import and use directly:
#   from config.config import cfg
cfg = _Config()
