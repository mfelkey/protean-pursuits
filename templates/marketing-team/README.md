# marketing-team — Template

> **This is a Protean Pursuits team template.**
> Instantiated by `scripts/refresh_templates.py` from `teams/marketing-team/`.
> Last refreshed: 2026-03-23 21:18 UTC
> Replace all `PROJECT_NAME_PLACEHOLDER` and `PROJ-TEMPLATE` tokens.

---

# PROJECT_NAME_PLACEHOLDER — Marketing Team

**Project:** PROJ-TEMPLATE  
**Version:** 1.0  
**Status:** Active  
**Last updated:** March 2026

> *Discover opportunities most of the market misses.*

---

## Overview

This repository contains the AI agent team responsible for all PROJECT_NAME_PLACEHOLDER marketing
operations — social media, video production, email marketing, and performance analytics.

The marketing team is one of three teams in the PROJECT_NAME_PLACEHOLDER agent ecosystem:

```
parallax-orchestrator/     ← top-level cross-team coordination (separate repo)
├── dev-team/              ← product development agents
├── ds-team/               ← data science agents
└── marketing-team/        ← this repo
```

---

## Agent Roles

| Agent | Responsibilities | Tools |
|---|---|---|
| **Marketing Orchestrator** | Campaign planning, task management, cross-agent coordination, weekly/monthly reporting | Task Management APIs, Timelines |
| **Social Agent** | Daily posts for X, Instagram, TikTok, Discord; trend research; visual briefs | Trend Search APIs, Image Generation |
| **Video Agent** | TikTok, YouTube Shorts, long-form YouTube scripts; Veo visual direction; Lyria 3 music briefs | Veo, Lyria 3 |
| **Email Agent** | Newsletters, drip sequences, re-engagement campaigns; CRM segmentation | CRM APIs, Copywriting |
| **Analyst Agent** | Weekly/monthly performance reports; KPI tracking; optimisation recommendations | Analytics Dashboards |

---

## Human-in-the-Loop

All publishable deliverables require explicit human approval before being marked
publishable or sent. Three hard approval gates are enforced:

| Gate | Trigger | Notification |
|---|---|---|
| `POST` | Any social post draft completed | SMS + Email |
| `EMAIL` | Any email send draft completed | SMS + Email |
| `VIDEO` | Any video production package completed | SMS + Email |

Approval requests are written to `logs/approvals/`. To approve or reject, write a
response JSON file at the path specified in the notification:

```json
{ "decision": "APPROVED" }
```
or
```json
{ "decision": "REJECTED", "reason": "Brand voice issue in paragraph 2" }
```

Approval requests time out after 24 hours. Timed-out artifacts are NOT published.

---

## Repo Structure

```
marketing-team/
├── agents/
│   ├── orchestrator/       orchestrator.py — campaign context, notifications, approval gates
│   ├── social/             social_agent.py — post drafting and approval flow
│   ├── video/              video_agent.py  — video scripting and approval flow
│   ├── email/              email_agent.py  — email drafting and approval flow
│   └── analyst/            analyst_agent.py — performance reporting
├── config/
│   └── .env.template       Environment variable template — copy to .env and fill in
├── flows/
│   └── marketing_flow.py   Top-level campaign orchestration flow
├── logs/                   Campaign context JSON files + approval records
├── memory/                 Agent memory and brand context files
├── output/
│   ├── posts/              Social post drafts and approved packages
│   ├── emails/             Email drafts and approved packages
│   ├── videos/             Video production packages
│   └── reports/            Weekly and monthly performance reports
├── docs/                   Reference documents (Brand Guide, Marketing Plan, etc.)
└── marketing/              Campaign briefs and content calendars
```

---

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/mfelkey/marketing-team.git
   cd marketing-team
   ```

2. Install dependencies:
   ```bash
   pip install crewai python-dotenv
   ```

3. Configure environment:
   ```bash
   cp config/.env.template config/.env
   # Fill in all values in config/.env
   ```

4. Run a campaign:
   ```bash
   python flows/marketing_flow.py --campaign "World Cup 2026 Launch Week" --type FULL
   ```

---

## Brand Rules (Standing — Never Violate)

These rules are enforced in every agent's backstory and every task prompt:

- **No guaranteed wins or returns.** No certainty-of-outcome language.
- **Never say "we predict."** PROJECT_NAME_PLACEHOLDER surfaces opportunities; users decide.
- **No "beat the bookies"** or adversarial framing.
- **No tipster-style picks** without methodology reference.
- **Responsible gambling footer** required in all marketing emails and videos.
- **Brand voice:** Direct, data-literate, quietly confident. Never hypes.

Reference: `docs/PROJECT_NAME_PLACEHOLDER-Brand-Guide-v1_2.docx`

---

## Key KPIs (Year 1 — Jun 2026 to May 2027)

| KPI | Target |
|---|---|
| Paid Sharp subscribers (EOP May 2027) | 2,604 |
| Total registered users (EOP May 2027) | 8,595 |
| Monthly Recurring Revenue (May 2027) | $49,476 |
| Free-to-paid conversion rate | 4% |
| Monthly paid churn | <5% |
| X followers (6 months post-launch) | 10,000+ |
| Instagram followers (6 months post-launch) | 3,000+ |
| TikTok followers (6 months post-launch) | 2,000+ |
| Email list at launch | 1,500+ |
| Discord members (3 months post-launch) | 500+ |

Reference: `docs/PROJECT_NAME_PLACEHOLDER_Marketing_Plan_v2.docx`

---

## Project Context

- **Launch date:** June 11, 2026 (FIFA World Cup 2026 opening match)
- **Phase 1A scope:** Soccer — WC2026 only
- **Phase 1B:** EPL + UCL (August 2026)
- **Phase 1C:** NFL (September 4, 2026)
- **Phase 1D:** NBA (October 2026)
- **Entity:** PROJECT_NAME_PLACEHOLDER LLC, wholly owned by Protean Pursuits LLC

Reference: `docs/Parallax_PRD_v1_8.md`
