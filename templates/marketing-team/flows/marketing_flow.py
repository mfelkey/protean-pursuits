"""
flows/marketing_flow.py

Top-level campaign flow for PROJECT_NAME_PLACEHOLDER marketing team.
Orchestrates Social, Video, Email, and Analyst agents for a named campaign.

Usage:
    python flows/marketing_flow.py --campaign "World Cup 2026 Launch Week" --type FULL
"""

import sys
sys.path.insert(0, "/home/mfelkey/marketing-team")

import os
import json
import argparse
from datetime import datetime

from agents.orchestrator.orchestrator import (
    create_campaign_context, save_context, log_event, notify_human
)
from agents.social.social_agent import run_daily_post_pack
from agents.video.video_agent import run_video_production
from agents.email.email_agent import run_email_production
from agents.analyst.analyst_agent import run_weekly_performance_report


def run_launch_week_campaign(campaign_name: str) -> dict:
    """
    Full launch week campaign flow.
    Runs Social, Video, and Email agents in parallel-ready sequence.
    All outputs require human approval before being marked publishable.
    """
    context = create_campaign_context(
        campaign_name=campaign_name,
        campaign_type="LAUNCH_WEEK"
    )

    notify_human(
        subject=f"Campaign started — {campaign_name}",
        message=(
            f"Campaign ID: {context['campaign_id']}\n"
            f"Started at: {context['created_at']}\n\n"
            f"Agents queued:\n"
            f"  1. Social Agent — X post pack (WC2026 Day 1 signals)\n"
            f"  2. Video Agent — TikTok (What is xG?)\n"
            f"  3. Email Agent — Newsletter (Free tier, soccer, US)\n\n"
            f"Each deliverable will require your approval before publishing.\n"
            f"You will receive a separate notification for each approval gate."
        )
    )

    log_event(context, "CAMPAIGN_STARTED", campaign_name)

    # ── Social ────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("STEP 1 — Social Agent")
    print("="*60)
    context = run_daily_post_pack(
        context=context,
        platform="X",
        topic="xG model — Group Stage Day 1 signals",
        sport="FIFA World Cup 2026"
    )

    # ── Video ─────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("STEP 2 — Video Agent")
    print("="*60)
    context = run_video_production(
        context=context,
        format="TIKTOK",
        topic="What is xG and why should you care?",
        sport="FIFA World Cup 2026",
        target_duration_seconds=45
    )

    # ── Email ─────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("STEP 3 — Email Agent")
    print("="*60)
    context = run_email_production(
        context=context,
        email_type="NEWSLETTER",
        segment="Free tier, soccer-interested, US, registered last 30 days",
        subject_hint="World Cup Day 1 — our model's top signals",
        sport="FIFA World Cup 2026"
    )

    # ── Final summary ─────────────────────────────────────────────────────────
    context["status"] = "CAMPAIGN_COMPLETE"
    log_event(context, "CAMPAIGN_COMPLETE", campaign_name)
    save_context(context)

    approved = [a for a in context["artifacts"] if a.get("status") == "APPROVED"]
    rejected = [a for a in context["artifacts"] if a.get("status") == "REJECTED"]

    notify_human(
        subject=f"Campaign complete — {campaign_name}",
        message=(
            f"Campaign ID: {context['campaign_id']}\n"
            f"Completed at: {datetime.utcnow().isoformat()}\n\n"
            f"Approved deliverables: {len(approved)}\n"
            f"Rejected deliverables: {len(rejected)}\n\n"
            + "\n".join([f"  ✅ {a['name']}" for a in approved])
            + ("\n" + "\n".join([f"  ❌ {a['name']}" for a in rejected]) if rejected else "")
        )
    )

    return context


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PROJECT_NAME_PLACEHOLDER Marketing Team Flow")
    parser.add_argument("--campaign", type=str, default="World Cup 2026 Launch Week",
                        help="Campaign name")
    parser.add_argument("--type", type=str, default="FULL",
                        choices=["FULL", "SOCIAL_ONLY", "VIDEO_ONLY", "EMAIL_ONLY"],
                        help="Flow type")
    args = parser.parse_args()

    print(f"\n🚀 PROJECT_NAME_PLACEHOLDER Marketing Team — {args.campaign}")
    print(f"   Flow type: {args.type}")
    print(f"   Started: {datetime.utcnow().isoformat()}\n")

    context = run_launch_week_campaign(args.campaign)

    print(f"\n✅ Marketing flow complete.")
    print(f"   Campaign ID: {context['campaign_id']}")
    print(f"   Status: {context['status']}")
    print(f"   Artifacts: {len(context['artifacts'])}")
