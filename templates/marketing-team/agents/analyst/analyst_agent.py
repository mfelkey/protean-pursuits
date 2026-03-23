import sys
sys.path.insert(0, "/home/mfelkey/marketing-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")


def build_analyst_agent() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Marketing Analyst Agent",
        goal=(
            "Pull data from analytics dashboards across all marketing channels, "
            "synthesise performance against KPIs from the Marketing Plan, identify "
            "optimisation opportunities, and produce structured reports for the "
            "Marketing Orchestrator and human review."
        ),
        backstory=(
            "You are a Senior Marketing Analyst with 10 years of experience measuring "
            "and optimising multi-channel digital marketing programmes for subscription "
            "SaaS products. You are equally fluent in social analytics, email metrics, "
            "video performance data, and subscription conversion funnels. "
            "You pull data from the analytics stack: social platform native analytics "
            "(X Analytics, Instagram Insights, TikTok Analytics, YouTube Studio), "
            "email platform metrics (open rate, CTR, conversion, churn), and product "
            "analytics (registered users, free-to-paid conversion, MRR, churn rate). "
            "You know the PROJECT_NAME_PLACEHOLDER Year 1 KPIs by heart and measure everything "
            "against them: 2,604 paid Sharp subscribers and $313,592 total net revenue "
            "by May 2027, 10,000 X followers and 3,000 Instagram followers within 6 "
            "months of launch, free-to-paid conversion rate of 4%, monthly paid churn "
            "below 5%. "
            "You do not report vanity metrics without context. Every metric you surface "
            "maps to a KPI, a trend, or an actionable recommendation. "
            "You produce three standing reports: a Weekly Performance Report every "
            "Monday morning, a Monthly Channel Deep-Dive on the first of each month, "
            "and an ad-hoc Optimisation Brief whenever a channel is materially "
            "underperforming against plan. "
            "You are the feedback loop for the entire marketing team. Your reports "
            "directly inform what the Social, Video, and Email agents produce next week."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_weekly_performance_report(context: dict, week_ending: str,
                                   metrics_summary: dict) -> dict:
    """
    Produce a weekly performance report from provided metrics.
    week_ending: ISO date string (e.g., '2026-06-19')
    metrics_summary: dict of channel metrics pulled from analytics APIs
    Returns updated context.
    """
    aa = build_analyst_agent()

    metrics_json = json.dumps(metrics_summary, indent=2)

    report_task = Task(
        description=f"""
You are the PROJECT_NAME_PLACEHOLDER Marketing Analyst Agent. Produce a complete Weekly Performance
Report for the week ending {week_ending}.

Raw metrics provided:
{metrics_json}

Year 1 KPI targets for reference:
- Paid Sharp subscribers (EOP May 2027): 2,604
- Total registered users (EOP May 2027): 8,595
- Monthly Recurring Revenue (May 2027): $49,476
- Free-to-paid conversion rate: 4% (ongoing)
- Monthly paid churn: <5% (ongoing)
- X followers (6 months post-launch): 10,000+
- Instagram followers (6 months post-launch): 3,000+
- YouTube Shorts subscribers (6 months post-launch): 1,000+
- TikTok followers (6 months post-launch): 2,000+
- Email / Waitlist subscribers at launch: 1,500+
- Discord members (3 months post-launch): 500+

Produce a complete Weekly Performance Report with ALL of the following sections:

1. EXECUTIVE SUMMARY (3–5 sentences)
   - Week-over-week headline changes
   - Biggest win and biggest concern
   - One priority action for next week

2. SUBSCRIBER & REVENUE METRICS
   - Total registered users (actual vs plan)
   - Paid Sharp subscribers (actual vs plan)
   - MRR (actual vs plan)
   - Free-to-paid conversion rate this week
   - Paid churn rate this week
   - Week-over-week deltas for each metric

3. SOCIAL PERFORMANCE
   - X: followers, impressions, engagements, top post
   - Instagram: followers, reach, engagements, top post
   - TikTok: followers, views, engagements, top video
   - YouTube Shorts: subscribers, views, watch time
   - Discord: members, active users, message volume
   - Week-over-week deltas. Flag any metric >10% below plan.

4. EMAIL PERFORMANCE
   - Sends this week, open rate, CTR, conversion rate
   - List growth (new subscribers, unsubscribes, net)
   - Best-performing subject line
   - Week-over-week deltas

5. OPTIMISATION RECOMMENDATIONS
   - Top 3 specific, actionable recommendations for next week
   - Each recommendation must map to a KPI and a specific agent action
     (e.g., "Social Agent: increase X thread frequency from 3x to 5x/week
      — rationale: X is 23% below follower target at current pace")

6. FLAGS FOR ORCHESTRATOR
   - Any channel materially underperforming (>15% below weekly plan pace)
   - Any compliance concern identified in published content
   - Any external factor (competitor activity, news event) affecting metrics

Output the complete Weekly Performance Report as well-formatted markdown.
""",
        expected_output="A complete Weekly Performance Report in markdown with metrics, analysis, and recommendations.",
        agent=aa
    )

    crew = Crew(
        agents=[aa],
        tasks=[report_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n📊 Analyst Agent generating Weekly Performance Report — week ending {week_ending}...\n")
    result = crew.kickoff()

    os.makedirs("output/reports", exist_ok=True)
    report_path = f"output/reports/{context['campaign_id']}_WPR_{week_ending}.md"

    with open(report_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Weekly Performance Report saved: {report_path}")

    context["artifacts"].append({
        "name": f"Weekly Performance Report — {week_ending}",
        "type": "WPR",
        "path": report_path,
        "status": "COMPLETE",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Analyst Agent"
    })
    log_event(context, "WPR_COMPLETE", report_path)
    context["status"] = "WPR_COMPLETE"
    save_context(context)

    return context, report_path


if __name__ == "__main__":
    from agents.orchestrator.orchestrator import create_campaign_context

    context = create_campaign_context(
        campaign_name="World Cup 2026 Launch Week",
        campaign_type="ANALYTICS"
    )

    # Sample metrics dict — in production this is populated from analytics API calls
    sample_metrics = {
        "registered_users": {"actual": 312, "plan": 250},
        "paid_sharp_subscribers": {"actual": 18, "plan": 50},
        "mrr": {"actual": 342.00, "plan": 950.00},
        "free_to_paid_conversion_rate": 0.058,
        "paid_churn_rate": 0.0,
        "social": {
            "x_followers": 487,
            "instagram_followers": 124,
            "tiktok_followers": 203,
            "youtube_shorts_subscribers": 41,
            "discord_members": 89
        },
        "email": {
            "list_size": 614,
            "sends_this_week": 1,
            "open_rate": 0.41,
            "ctr": 0.087,
            "conversion_rate": 0.031
        }
    }

    context, report_path = run_weekly_performance_report(
        context=context,
        week_ending="2026-06-19",
        metrics_summary=sample_metrics
    )

    print(f"\n✅ Analyst agent run complete.")
    print(f"📄 Report: {report_path}")
