# strategy-team — Template

> **This is a Protean Pursuits team template.**
> Instantiated by `scripts/refresh_templates.py` from `teams/strategy-team/`.
> Last refreshed: 2026-03-23 21:18 UTC
> Replace all `PROJECT_NAME_PLACEHOLDER` and `PROJ-TEMPLATE` tokens.

---

# Protean Pursuits — Strategy Team

**Project:** Protean Pursuits LLC  
**Version:** 1.0  
**Status:** Active  

> *Strategy without stress-testing is just optimism.*

---

## Overview

The Strategy Team produces company-level and project-level strategy across eleven specialist domains. All outputs carry mandatory confidence levels and require human review before forwarding to the Protean Pursuits Orchestrator for implementation.

---

## The Team — 11 Agents

| Agent | Domain | Primary Output |
|---|---|---|
| **Business Model** | Revenue architecture, unit economics, pricing | Business Model Canvas, pricing strategy, monetisation roadmap |
| **Go-to-Market** | ICP, channels, launch sequencing, growth loops | GTM playbook, channel strategy, launch plan |
| **Product Strategy** | Vision, positioning, roadmap narrative, differentiation | Product vision doc, positioning framework, build/buy/partner rec |
| **Partnership** | Distribution, technology, data, affiliate partnerships | Partnership opportunity map, partner brief templates |
| **Competitive Intelligence** | Competitive landscape, threat monitoring, win/loss | Competitive landscape report, competitor profiles, CI updates |
| **Financial Strategy** | Revenue modelling, unit economics, capital allocation | Pro forma, financial model, investment case |
| **OKR / Planning** | Quarterly objectives, outcome metrics, planning cycle | OKR sets (company + project), retrospective frameworks |
| **Risk & Scenario** | Pre-mortem, scenario planning, assumption registry | Scenario analysis, risk register, pre-mortem report |
| **Brand & Positioning** | Narrative, positioning, tone of voice, brand pillars | Brand strategy doc, positioning statement, messaging hierarchy |
| **Talent & Org** | Org design, hiring roadmap, human vs agent design | Org design doc, hiring roadmap, human-agent capability map |
| **Technology Strategy** | Build/buy/partner, platform strategy, AI/ML strategy | Tech strategy doc, differentiation analysis, platform brief |

---

## Confidence Levels

Every recommendation in every output is tagged:

| Level | Meaning |
|---|---|
| `[CONFIDENCE: HIGH]` | Strong evidence, clear precedent, low uncertainty — recommend proceeding |
| `[CONFIDENCE: MEDIUM]` | Reasonable evidence, some assumptions, moderate uncertainty — recommend with caveats |
| `[CONFIDENCE: LOW]` | Limited evidence, significant assumptions, high uncertainty — treat as hypothesis |

---

## Scope

| Scope | What it covers |
|---|---|
| **Company-level** | Protean Pursuits LLC baseline strategy — applies across all projects |
| **Project-level** | Project-specific overrides — builds on company baseline, addresses project market/context |

---

## Run Modes

### Brief (on-demand, single agent)
```bash
python flows/strategy_flow.py \
  --mode brief \
  --agent competitive_intel \
  --scope project \
  --project-id PROJ-TEMPLATE \
  --name "PROJECT_NAME_PLACEHOLDER" \
  --brief "Focus on direct analytics competitors in the sports betting space"
```

### Full Report (all 11 agents, sequential)
```bash
python flows/strategy_flow.py \
  --mode full_report \
  --scope company \
  --name "Protean Pursuits LLC"
```

### Competitive Update (recurring)
```bash
python flows/strategy_flow.py \
  --mode competitive \
  --scope project \
  --project-id PROJ-TEMPLATE \
  --name "PROJECT_NAME_PLACEHOLDER" \
  --brief "Focus on new entrants and pricing changes since last update"
```

### OKR Cycle (quarterly)
```bash
python flows/strategy_flow.py \
  --mode okr_cycle \
  --quarter Q3-2026 \
  --scope company \
  --name "Protean Pursuits LLC" \
  --prior-okr output/okr/STRAT-XXXXXX_OKR_PLANNING_20260601.md
```

---

## Human-in-the-Loop

All strategy outputs require human review before forwarding to the Protean Pursuits Orchestrator. You will receive an SMS and email notification with the artifact path. Respond via JSON file:

```json
{ "decision": "APPROVED" }
```
or
```json
{ "decision": "REJECTED", "reason": "The GTM channel sequencing doesn't reflect our current budget constraints" }
```

Approval requests time out after 48 hours.

---

## Repo Structure

```
strategy-team/
├── agents/
│   ├── orchestrator/         orchestrator.py, base_agent.py
│   ├── business_model/       business_model_agent.py
│   ├── gtm/                  gtm_agent.py
│   ├── product_strategy/     product_strategy_agent.py
│   ├── partnership/          partnership_agent.py
│   ├── competitive_intel/    competitive_intel_agent.py
│   ├── financial_strategy/   financial_strategy_agent.py
│   ├── okr_planning/         okr_agent.py
│   ├── risk_scenario/        risk_agent.py
│   ├── brand_positioning/    brand_agent.py
│   ├── talent_org/           talent_agent.py
│   └── technology_strategy/  tech_strategy_agent.py
├── flows/
│   └── strategy_flow.py      all four run modes
├── config/
│   └── .env.template
├── logs/                     strategy context JSON + approval records
├── memory/                   cross-run strategy memory
├── output/
│   ├── briefs/               on-demand single-agent outputs
│   ├── reports/              full strategy report outputs
│   ├── competitive/          recurring competitive updates
│   └── okr/                  quarterly OKR outputs
└── docs/                     reference documents
```

---

## Setup

```bash
git clone https://github.com/mfelkey/strategy-team.git
cd strategy-team
pip install crewai python-dotenv
cp config/.env.template config/.env
# Fill in config/.env
python flows/strategy_flow.py --mode brief --agent competitive_intel \
  --scope company --name "Protean Pursuits LLC"
```

---

## Integration with Protean Pursuits

The Strategy Team feeds the Protean Pursuits Orchestrator:

```
Strategy Team → [Human Review] → Protean Pursuits Orchestrator → Implementation
```

The Orchestrator receives approved strategy packages and translates them into:
- Project briefs for the Dev, DS, Marketing, Design, QA, and Legal teams
- Updated company baseline strategy in the framework memory
- OKR targets for the Project Manager to track
