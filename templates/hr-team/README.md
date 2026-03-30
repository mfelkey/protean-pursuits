# HR Team — Protean Pursuits

People operations for the entire Protean Pursuits portfolio.

## Workforce model

**Humans only.** All recommendations assume a human workforce. Technology is
a tool that helps people do their best work — never a replacement for a person.
All outputs require human approval before any action affecting a person is taken.

## Agents

| Agent | Key | What it produces |
|---|---|---|
| HR Orchestrator | — | Coordinates the crew, synthesises People Package, fires HITL review |
| Recruiting Specialist | `recruiting` | Job descriptions, sourcing plans, interview guides, offer templates |
| Onboarding Specialist | `onboarding` | Pre-day-1 through 90-day plans, checklists, buddy programme frameworks |
| Performance & Compensation | `performance_comp` | Review templates, comp bands, goal-setting frameworks, promotion criteria |
| Policy & Compliance | `policy_compliance` | Employee handbook sections, standalone HR policies, compliance checklists |
| Culture & Engagement | `culture_engagement` | Engagement surveys, recognition programmes, DEI roadmaps, manager rubrics |
| Benefits Specialist | `benefits` | Benefits programme design, cost models, open enrolment comms, leave policies |

All agents use **Tier 1** (`TIER1_MODEL`) — reasoning and analysis, no code generation.

## Run modes

```
python flows/hr_flow.py --mode recruit
    --name "Senior Backend Engineer" --project-id PROJ-TEMPLATE
    --brief "Python/FastAPI, 8+ years, remote-first, IC track"

python flows/hr_flow.py --mode onboard
    --name "Q1 2026 Engineering Cohort" --project-id PROJ-TEMPLATE

python flows/hr_flow.py --mode review
    --name "H1 2026 Performance Cycle" --project-id PROJ-TEMPLATE

python flows/hr_flow.py --mode policy --agent policy_compliance
    --name "Remote Work Policy Update" --project-id PROJ-TEMPLATE

python flows/hr_flow.py --mode culture
    --name "Q2 Engagement Survey" --project-id PROJ-TEMPLATE

python flows/hr_flow.py --mode benefits
    --name "2026 Benefits Refresh" --project-id PROJ-TEMPLATE

python flows/hr_flow.py --mode full_cycle
    --name "PROJECT_NAME_PLACEHOLDER People Package" --project-id PROJ-TEMPLATE
```

## Output directories

| Directory | Contents |
|---|---|
| `output/recruiting/` | Job descriptions, interview guides, offer templates |
| `output/onboarding/` | Onboarding plans, checklists, 30/60/90-day frameworks |
| `output/policies/` | HR policies, handbook sections, benefits documents |
| `output/reports/` | Performance reviews, culture reports, people packages |

## Cross-team coordination

Every HR output ends with a **CROSS-TEAM FLAGS** section. Items flagged:

| Flag target | Typical triggers |
|---|---|
| **Legal** | Termination, discipline, accommodation, leave, classification, background checks, equity compliance |
| **Finance** | All compensation figures, headcount costs, benefits budget, 401k match |
| **Strategy** | Org design, headcount planning, leadership development, succession |
| **QA** | Compliance training tracking, process documentation, audit requirements |

## Human-in-the-loop

Every output triggers a HITL review gate before it is considered approved.
Approval files land in `logs/approvals/HR-*.response.json`.

```json
{ "decision": "APPROVED" }
{ "decision": "REJECTED", "reason": "Comp bands need Finance sign-off first" }
```

## Directory structure

```
templates/hr-team/
  agents/
    hr/
      orchestrator/   orchestrator.py + base_agent.py
      recruiting/     recruiting_agent.py
      onboarding/     onboarding_agent.py
      performance_comp/  performance_comp_agent.py
      policy_compliance/ policy_compliance_agent.py
      culture_engagement/ culture_engagement_agent.py
      benefits/       benefits_agent.py
  flows/
    hr_flow.py
  output/
    recruiting/  onboarding/  policies/  reports/
  config/
  memory/
  docs/
```

## From the PP Orchestrator

The HR Team Lead is at `agents/leads/hr/hr_lead.py`.

```python
from agents.leads.hr.hr_lead import build_hr_lead, run_hr_deliverable
run_hr_deliverable(context, mode="recruit", brief="Senior engineer, remote")
```
