# Protean Pursuits — AI Agent Framework

**Owner:** Protean Pursuits LLC (Michigan)  
**Version:** 2.0  
**Architecture:** Monorepo with git submodules  

> *Seven independent teams. One cohesive portfolio.*

---

## Architecture

```
Protean Pursuits Orchestrator
        │
  Project Manager
        │
  ┌─────┴─────────────────────────────────────────────┐
  ▼       ▼        ▼         ▼      ▼      ▼       ▼
Dev     DS    Marketing  Strategy Legal Design   QA
Lead    Lead    Lead       Lead   Lead   Lead   Lead
  │       │        │         │      │      │       │
  ▼       ▼        ▼         ▼      ▼      ▼       ▼
teams/  teams/  teams/    teams/ teams/ teams/ teams/
dev-    ds-     marketing- strat  legal  design  qa-
team    team    team       team   team   team    team
  │       │        │         │      │      │       │
  └───────┴────────┴─────────┴──────┴──────┴───────┘
           ↕ git submodules (also standalone repos)
```

Each team repo is both a **git submodule** (cohesive portfolio mode) and
a **standalone repo** (independent operation mode). The same codebase,
two ways to run it.

---

## Two Ways to Run

### Standalone mode — run any team directly
```bash
cd teams/marketing-team
python flows/marketing_flow.py --campaign "World Cup Launch" --type FULL
```

### Protean Pursuits mode — orchestrate across all teams
```bash
python flows/intake_flow.py --mode brief --name "ParallaxEdge" \
  --prd docs/Parallax_PRD_v1_8.md --weeks 12 --budget 50000
```

---

## Teams (git submodules)

| Team | Repo | Agents | Specialty |
|---|---|---|---|
| `dev-team` | github.com/mfelkey/dev-team | Dev pipeline | Software |
| `ds-team` | github.com/mfelkey/ds-team | DS pipeline | Data & ML |
| `marketing-team` | github.com/mfelkey/marketing-team | 5 agents | GTM & content |
| `strategy-team` | github.com/mfelkey/strategy-team | 11 agents | Portfolio strategy |
| `legal-team` | github.com/mfelkey/legal-team | 8 agents | Commercial law |
| `design-team` | github.com/mfelkey/design-team | 8 agents | UX/UI/brand |
| `qa-team` | github.com/mfelkey/qa-team | 8 agents | Portfolio quality |

---

## Shared Core (`core/`)

Utilities shared across all teams when running under Protean Pursuits:

| Module | Contents |
|---|---|
| `core/notifications.py` | `notify_human()`, `send_sms()`, `send_email()` |
| `core/hitl.py` | `request_human_approval()` — universal HITL gate |
| `core/context.py` | `create_project_context()`, `save_context()`, `log_event()` |
| `core/git_helper.py` | `git_push()`, `git_push_submodule()`, `submodule_update_all()` |

Standalone team repos carry their own copy of these utilities for independent operation.

---

## Setup

```bash
# Clone with all submodules
git clone --recurse-submodules https://github.com/mfelkey/protean-pursuits.git
cd protean-pursuits

# Or if already cloned without submodules
git submodule update --init --recursive

pip install crewai python-dotenv
cp config/.env.template config/.env
# Fill in config/.env
```

---

## Keeping Teams in Sync

```bash
# Update all teams to latest
python scripts/sync_teams.py

# Update one team
python scripts/sync_teams.py marketing-team

# Check sync status
python scripts/sync_teams.py --status
```

---

## Human-in-the-Loop

All approvals use `core/hitl.py`. Respond via JSON file:
```json
{ "decision": "APPROVED" }
```
or
```json
{ "decision": "REJECTED", "reason": "needs revision" }
```

---

## Active Projects

| Project ID | Name | Status | Teams |
|---|---|---|---|
| PROJ-PARALLAX | ParallaxEdge | Ready | dev, ds, marketing, strategy, legal, design, qa |
