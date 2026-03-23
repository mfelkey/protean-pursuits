# Protean Pursuits — AI Agent Framework

**Owner:** Protean Pursuits LLC (Michigan)  
**Version:** 1.0  
**Status:** Active  

> *A generic multi-team AI agent framework. Projects live in separate repos and are instantiated from templates here.*

---

## Architecture

```
Protean Pursuits Orchestrator
        │
        ▼
  Project Manager
        │
  ┌─────┴──────────────────────────────────────────┐
  ▼       ▼        ▼        ▼      ▼      ▼        ▼
Dev     DS    Marketing  Design   QA   Legal  Strategy
Lead    Lead    Lead      Lead   Lead   Lead    Lead
  │       │        │        │      │      │        │
agents  agents   agents   agents agents agents   agents
```

**Three-tier hierarchy:**
- **Orchestrator** — discovery, PRD generation, repo spin-up, portfolio oversight, HITL escalation
- **Project Manager** — timeline, budget, dependencies, weekly status, blocker resolution
- **Team Leads × 7** — own their team's deliverables, brief their agents, report to PM

---

## Teams

| Team | Responsibilities |
|---|---|
| **Dev** | Frontend, backend, infrastructure, CI/CD |
| **DS** | ML models, data pipelines, analytics, model cards |
| **Marketing** | GTM, content, social, email, campaigns, performance |
| **Design** | UX, UI, design system, brand, accessibility |
| **QA** | Test planning, execution, defect tracking, launch sign-off |
| **Legal** | Compliance, policy drafts, risk flags, counsel prep |
| **Strategy** | Market research, competitive analysis, business cases, OKRs |

---

## Two Intake Modes

### Discovery Mode
Start from scratch — the Orchestrator interviews you to understand the problem,
synthesises a Discovery Summary, generates a draft PRD, and gets your approval
before any team work begins.

```bash
python flows/intake_flow.py --mode discovery --name "My New Project"
```

### Brief Mode
You provide a PRD or brief — the Orchestrator classifies the work, recommends
teams, and hands off to the Project Manager after your approval.

```bash
python flows/intake_flow.py \
  --mode brief \
  --name "ParallaxEdge" \
  --prd docs/Parallax_PRD_v1_8.md \
  --weeks 12 \
  --budget 50000
```

---

## Human-in-the-Loop Gates

All irreversible decisions require explicit human approval:

| Gate | Trigger |
|---|---|
| `PRD` | Before any team work begins |
| `REPO_SPINUP` | Before creating project repos from templates |
| `BLOCKER` | Any CRITICAL blocker escalated from PM |
| `DELIVERABLE` | Configurable per-team (e.g. POST, EMAIL, VIDEO for Marketing) |

Approvals are written to `logs/approvals/`. Respond with a JSON file:
```json
{ "decision": "APPROVED" }
```
or
```json
{ "decision": "REJECTED", "reason": "needs more detail in section 3" }
```

---

## Repo Structure

```
protean-pursuits/
├── agents/
│   ├── orchestrator/         orchestrator.py — intake, PRD, spin-up, escalation
│   ├── project_manager/      project_manager.py — timeline, budget, status
│   └── leads/
│       ├── base_lead.py      generic Team Lead base
│       ├── dev/              dev_lead.py
│       ├── ds/               ds_lead.py
│       ├── marketing/        marketing_lead.py
│       ├── design/           design_lead.py
│       ├── qa/               qa_lead.py
│       ├── legal/            legal_lead.py
│       └── strategy/         strategy_lead.py
├── templates/
│   ├── dev_team/             copy → new project's dev-team repo
│   ├── ds_team/              copy → new project's ds-team repo
│   ├── marketing_team/       copy → new project's marketing-team repo
│   ├── design_team/
│   ├── qa_team/
│   ├── legal_team/
│   └── strategy_team/
├── flows/
│   └── intake_flow.py        discovery + brief intake entry point
├── config/
│   └── .env.template
├── logs/                     project contexts + approval records
├── memory/                   cross-project agent memory
└── docs/                     framework documentation
```

---

## Setup

```bash
git clone https://github.com/mfelkey/protean-pursuits.git
cd protean-pursuits
pip install crewai python-dotenv
cp config/.env.template config/.env
# Fill in config/.env
```

---

## Active Projects

| Project ID | Name | Status | Teams |
|---|---|---|---|
| PROJ-PARALLAX | ParallaxEdge | Active | dev, ds, marketing |

---

## Adding a New Project

1. Run intake flow (discovery or brief mode)
2. Approve PRD and repo spin-up when notified
3. Project repos are created from templates under `projects/`
4. PM generates kickoff plan and briefs Team Leads
5. Work begins — weekly status reports every Monday

---

## Protean Pursuits LLC

- **Entity:** Michigan LLC
- **Wholly owned by:** Protean Pursuits LLC (single-member)
- **Mission:** Build software products, data science platforms, and marketing programmes across multiple domains — with AI agent teams that maintain quality, transparency, and human oversight.
