# Protean Pursuits — Capability Reference for External Claude Projects

> **Audience:** This document is written for other Claude-based AI projects that need to understand what Protean Pursuits (PP) can do, how to request work from it, and what constraints govern its behavior.

---

## 1. What Protean Pursuits Is

Protean Pursuits is a CrewAI + Ollama multi-agent framework. It receives plain-English project descriptions and routes them through a pipeline of specialist agents that produce complete, structured technical deliverables. It is **not a single agent** — it is a coordinated team of agents organized into crews, each producing a specific artifact in a fixed sequence.

**Two model tiers power all agents:**

| Tier | Model | Used For |
|---|---|---|
| Tier 1 | `ollama/qwen3:32b` | Reasoning, planning, analysis |
| Tier 2 | `ollama/qwen3-coder:30b` | Code generation, implementation |

---

## 2. Architecture

### Entry points

PP exposes three entry points. Use the lightest one that fits the job.

| Entry point | Command | When to use |
|---|---|---|
| **Full intake** | `flows/intake_flow.py` | New project from scratch — full orchestrator-led pipeline |
| **Team flow** | `flows/pp_flow.py --team X --mode Y` | Existing project — run one team's pipeline or a specific mode |
| **Agent direct** | `flows/pp_flow.py --team X --agent Y` | Targeted task — single agent, no orchestrator overhead |

All three share the same context resolution (`--project` → `--context-file` → `--context` → none), output paths, and HITL gates.

### Agent hierarchy

```
flows/intake_flow.py  (new projects)
flows/pp_flow.py      (team flows + agent direct)
        │
        ▼
PP Orchestrator
  └── Project Manager
        └── Team Leads (one per team)
              └── Team Orchestrators
                    └── Specialist Agents
```

PP's master orchestrator receives the request, classifies it, selects the relevant team(s), and routes accordingly. When using `pp_flow.py --team` you bypass intake and address a team or agent directly with an existing context.

---

## 3. Teams & Capabilities

PP has **8 active teams**. Each team follows the same structure internally: `agents/ flows/ config/ output/ memory/ docs/`.

### 3.1 Dev Team

The core software development team. Runs a sequential pipeline from requirements through deployable code.

**Planning agents (Tier 1):**

| Agent | Artifact | What It Produces |
|---|---|---|
| Product Manager | `PRD` | User stories, acceptance criteria, scope boundaries |
| Business Analyst | `BAD` | Stakeholder map, process flows, data dictionaries |
| Scrum Master | `Sprint Plan` | Prioritized backlog, story points, sprint sequencing |
| Technical Architect | `TAD` | System design, tech stack, data flows, deployment model |
| Security Reviewer | `SRR` 🟢/🟡/🔴 | Security audit — RED rating blocks the pipeline |
| UX/UI Designer | `UXD` + `UI Content Guide` | Every screen, interaction, label, and error message |

**Build agents (Tier 2):**

| Agent | Artifact | What It Produces |
|---|---|---|
| Senior Developer | `TIP` | Technical implementation plan |
| Backend Developer | `BIR` | Server-side implementation |
| Frontend Developer | `FIR` | Client-side implementation |
| Database Administrator | `DBAR` | Schema, queries, indexes |
| DevOps Engineer | `DIR` | Deployment pipelines, infrastructure configuration |

**Quality agents:**

| Agent | Tier | Artifact | What It Produces |
|---|---|---|---|
| QA Lead | T1 | `MTP` | Master test plan |
| Test Automation Engineer | T2 | `TAR` | Runnable test suite (Jest, Playwright, axe-core, k6) |

**Retrofit agents** — Re-process existing artifacts to strip provider-specific content and make the system deployment-agnostic. A Reconciliation agent produces a gap report if critical content is lost.

**Quality floor (enforced on all dev-team output):**
- No placeholder code — every function complete
- TypeScript for frontend/React Native; Python type hints on all signatures
- WCAG 2.1 AA accessibility; VoiceOver/TalkBack tested
- ≥ 80% unit test coverage on business logic
- Every critical user journey covered by E2E tests
- Secrets never hardcoded; all SRR CRITICAL/HIGH findings addressed

---

### 3.2 Mobile Team (Dev Team Extension)

Activates automatically when the project includes a mobile application. Runs after the core web pipeline.

| Agent | Artifact | What It Produces |
|---|---|---|
| Mobile UX Designer | `MUXD` | Unified mobile UX spec (iOS, Android, and RN work from this) |
| iOS Developer | `IIR` + Swift code | Native iOS app in Swift/SwiftUI with VoiceOver + secure storage |
| Android Developer | `AIR` + Kotlin code | Native Android app in Kotlin/Compose with TalkBack + encrypted storage |
| RN Architect | `RNAD` | React Native/Expo/TypeScript architecture document |
| RN Developer | `RN Guide` | Cross-platform implementation guide |
| Mobile DevOps | `MDIR` | Build pipelines, code signing, app store submission automation |
| Mobile QA | Mobile test suite | XCTest, JUnit5, Detox test suite |

---

### 3.3 Finance Group (Dev Team Sub-Crew)

**Not a standalone team.** Runs as a sub-crew of the dev team — after full planning (post UX Content Guide), before the build phase. Advisory only — it **never auto-blocks the pipeline**.

Triggers automatically when the PP Orchestrator detects financial language in the project description, or when explicitly requested.

| Agent | Artifact | What It Produces |
|---|---|---|
| Finance Orchestrator | `FSP` | Finance Summary Package — consolidates all below |
| Cost Analyst | `CEA` | Dev + infra + licensing costs (LOW/MID/HIGH scenarios) |
| ROI Analyst | `ROI` | NPV, IRR, payback period, break-even, risk-adjusted scenarios |
| Infrastructure Finance Modeler | `ICM` | TAD → cost lines, scaling curves, 3-year monthly projections |
| Billing Architect | `BPS` | Provider selection, payment flows, PCI/DSS requirements |
| Pricing Specialist | `PRI` | Pricing tiers, price points, unit economics, sensitivity analysis |
| Financial Statements Modeler | `FSR` | Income statement, cash flow, balance sheet (3-year) |
| Strategic Corp Finance Specialist | `SCF` | Capital structure, funding options, M&A considerations, risk register |

**Auto-skip rules:**
- `BPS` (Billing Architect) is skipped if no billing/payment/subscription language is found in the PRD
- `PRI` (Pricing Specialist) is skipped for internal tooling projects

Every Finance artifact opens with `FINANCE RATING: 🟢/🟡/🔴` and ends with an `OPEN QUESTIONS` section.

---

### 3.4 SME Group

**Project-agnostic domain specialists** — callable from any current or future PP project. The SME Orchestrator routes queries, synthesises multi-expert responses, and fires a HITL review gate on any multi-SME output.

**⚠️ Authorized callers only:** `pp_orchestrator`, `project_manager`, `strategy`, `legal`
Dev-team agents are **explicitly blocked** — a `PermissionError` is raised if attempted.

**Domains covered:**

| Registry Key | Domain |
|---|---|
| `sports_betting` | Cross-sport industry authority — all regulated markets worldwide |
| `world_football` | All global leagues, confederations, Asian handicap |
| `nba_ncaa_basketball` | NBA + March Madness |
| `nfl_ncaa_football` | NFL + CFP, college football |
| `mlb` | MLB + NPB + KBO + CPBL |
| `nhl_ncaa_hockey` | NHL + NCAA + KHL + Euro leagues |
| `mma` | UFC + Bellator + ONE + Rizin |
| `tennis` | ATP + WTA + Challengers + ITF |
| `world_rugby` | Union + League — Six Nations, NRL, State of Origin |
| `cricket` | Test + ODI + T20 + IPL — all formats, all nations |
| `wnba_ncaa_womens_basketball` | WNBA + NCAA women's |
| `thoroughbred_horse_racing` | US + UK/IRE + AUS + HK + JPN + FR + DXB |
| `harness_racing` | Standardbred worldwide — Hambletonian, V75, PMU |
| `mens_boxing` | All four sanctioning bodies, all 17 weight classes |
| `pga` | PGA Tour + DP World Tour + LIV + all majors + Ryder Cup |
| `lpga` | LPGA + JLPGA + KLPGA + women's majors + Solheim Cup |

Every SME output opens with `DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW` and ends with `CROSS-TEAM FLAGS` and `OPEN QUESTIONS`.

---

### 3.5 DS Team

Data science analysis team. Handles analytical workflows from initial planning through final reporting. Features complexity-adaptive filtering — pipeline depth scales automatically to LOW/MEDIUM/HIGH classifications.

---

### 3.6 Other Teams

#### HR Team
Run modes: `RECRUIT | ONBOARD | REVIEW | POLICY | CULTURE | BENEFITS | FULL_CYCLE`
Humans-only workforce model — never recommends replacing a person with AI. All outputs require human approval before any action affecting a person is taken. Mandatory cross-team flags on every output: Legal / Finance / Strategy / QA.
HITL gate: HR action gate fires before any action affecting a person.

#### Marketing Team
Run modes: `brief | copy | email | social | video | analytics | campaign`
No deliverable publishes autonomously — every output requires human approval before execution. HITL gates: `POST` (social), `EMAIL`, `VIDEO`.

| Mode | What it produces |
|---|---|
| `brief` | Campaign brief, channel plan |
| `copy` | Landing page copy, ad creative, app store listings, push copy |
| `email` | Email sequences, drip campaigns, transactional templates |
| `social` | Post drafts, visual briefs (X, Instagram, TikTok, Discord) |
| `video` | Scripts, visual direction briefs, music briefs |
| `analytics` | Channel performance reports, KPI dashboards |
| `campaign` | Full campaign package — all specialists in sequence |

#### Strategy Team
Run modes: `positioning | business_model | competitive | gtm | okr | financial | partnership | product | risk | talent | technology | full`
Authorized SME caller. HITL gates: `STRATEGY`, `OKR_CYCLE`, `COMPETITIVE`.

| Mode | What it produces |
|---|---|
| `positioning` | Brand positioning framework |
| `business_model` | Business model canvas + narrative |
| `competitive` | Competitive landscape, positioning gaps |
| `gtm` | GTM plan, channel strategy, launch sequencing |
| `okr` | OKR framework, measurement plan |
| `financial` | Financial strategy, funding roadmap |
| `partnership` | Partnership framework, target list |
| `product` | Product strategy, roadmap |
| `risk` | Risk register, scenario analysis |
| `talent` | Org design, hiring plan |
| `technology` | Technology strategy, build/buy/partner rec |
| `full` | All of the above in sequence |

#### Legal Team
Run modes: `contract | review | ip | privacy | regulatory | employment | corporate | dispute | full`
Authorized SME caller. HITL gate: `LEGAL_REVIEW` on every deliverable.

| Mode | What it produces |
|---|---|
| `contract` | Draft contracts, NDAs, service agreements |
| `review` | Redlined documents, risk memos |
| `ip` | IP assessment, licensing framework |
| `privacy` | GDPR/CCPA analysis, privacy impact assessment |
| `regulatory` | Compliance gap report |
| `employment` | Employment agreements, contractor frameworks |
| `corporate` | Entity structure recommendation |
| `dispute` | Dispute assessment, strategy memo |
| `full` | Complete legal package |

#### Design Team
Run modes: `research | wireframe | visual | motion | accessibility | full`
HITL gate: `DESIGN_REVIEW` on every mode — assets approved before handoff to dev.

| Mode | What it produces |
|---|---|
| `research` | User research report, journey maps |
| `wireframe` | Research report + wireframes |
| `visual` | UI designs, brand guide, design system |
| `motion` | Motion spec, animation briefs |
| `accessibility` | Accessibility audit (WCAG 2.1 AA), usability report |
| `full` | Complete design package |

#### QA Team (Standalone)
Run modes: `functional | performance | security | accessibility | data_quality | legal_review | marketing_review | test_cases | full`
Operates independently of the dev-team's internal quality phase. Can audit any team's deliverables. HITL gate: `QA_SIGN_OFF`.

| Mode | What it produces |
|---|---|
| `functional` | Functional test results, bug report |
| `performance` | Performance benchmarks, bottleneck analysis |
| `security` | Security test report 🟢/🟡/🔴 |
| `accessibility` | WCAG 2.1 AA audit |
| `data_quality` | Data quality scorecard |
| `legal_review` | Legal completeness report |
| `marketing_review` | Marketing compliance report |
| `test_cases` | Test case library |
| `full` | Full QA audit package |

---

### 3.7 Docs Agents (Dev Team)

| Agent | What It Produces |
|---|---|
| API Documentation & DevEx Writer | API docs, README, developer guides, onboarding content |
| Technical Writer | User guides, admin guides, runbooks, release notes, KB articles |

---

## 4. How to Request Work from PP

### 4.1 General Pattern

Address the PP Orchestrator with a plain-English description of what you need. Include:

1. **What you want built or analyzed** — be specific about the domain
2. **Any known constraints** — platform, tech stack preferences, compliance requirements
3. **Which optional crews to activate** — Finance Group, Mobile Team, SME consultation
4. **Any upstream artifacts you already have** — PP agents consume prior artifacts as context

You do **not** need to address individual agents, select a team, or specify artifact names. PP routes internally.

### 4.2 Example Handoff Prompts

**Full dev project (web):**
```
Please run a full dev-team pipeline for the following project:

[project description]

Constraints: [any known constraints]
Activate Finance Group: yes/no
Activate Mobile Team: yes/no
```

**Full dev project with mobile:**
```
Please run a full dev-team pipeline including the mobile team for:

[project description]

Target platforms: iOS / Android / React Native (cross-platform)
```

**Finance Group only (you have an existing PRD + TAD):**
```
Please run the Finance Group against the attached PRD and TAD.
Project type: [SaaS / internal tool / marketplace / etc.]
Billing integration required: yes/no
```

**SME consultation (authorized callers only):**
```
[As pp_orchestrator / project_manager / strategy / legal]
Please consult the SME group on the following question:

[question]

Relevant domains: [pga, lpga] — or leave blank for auto-detection
```

**HR workflow:**
```
Please run the HR team in [RECRUIT | ONBOARD | REVIEW | POLICY | CULTURE | BENEFITS | FULL_CYCLE] mode for:

[description]
```

**DS analysis:**
```
Please run the DS team on the following analytical request:

[description]

Complexity: [LOW / MEDIUM / HIGH — or leave blank for auto-detection]
```

**Team flow — existing project, specific mode:**
```bash
# Run the strategy team competitive intelligence mode
python flows/pp_flow.py --team strategy --mode competitive \
    --project my-project --task "Competitive landscape for sports betting app" --save

# Run a legal privacy review
python flows/pp_flow.py --team legal --mode privacy \
    --project my-project --task "GDPR and CCPA assessment for user data collection" --save

# Run a full QA audit
python flows/pp_flow.py --team qa --mode full \
    --project my-project --task "Full audit of v1.0 release candidate" --save
```

**Agent direct — single specialist, no orchestrator:**
```bash
# Get a competitive intelligence brief without running the full strategy pipeline
python flows/pp_flow.py --team strategy --agent competitive_intel_analyst \
    --task "Who are the top 5 competitors in regulated US sports betting?" \
    --project my-project --save

# Get app store copy without running a full marketing campaign
python flows/pp_flow.py --team marketing --agent copywriter \
    --task "App Store listing for iOS sports betting app — US market" \
    --project my-project --save

# Get a contract drafted without the full legal pipeline
python flows/pp_flow.py --team legal --agent contract_drafter \
    --task "Independent contractor agreement for ML engineer" \
    --context "Michigan law, 6-month engagement, IP assignment required"
```

### 4.3 Targeting a Specific Team or Agent

When you already have a project context and want to run a targeted operation without going through the full intake, use `pp_flow.py` directly.

**Run a team pipeline:**
```bash
python flows/pp_flow.py \
    --team <team> \
    --mode <mode> \
    --project <project_name> \
    --task "<plain-English task description>" \
    [--save]
```

**Run a single agent directly:**
```bash
python flows/pp_flow.py \
    --team <team> \
    --agent <registry_key> \
    --project <project_name> \
    --task "<plain-English task description>" \
    [--save]
```

**Supply context without a project file:**
```bash
# Inline context
python flows/pp_flow.py --team legal --agent contract_drafter \
    --task "Draft NDA for contractor" \
    --context "Michigan law, 2yr term, mutual NDA"

# Context from file
python flows/pp_flow.py --team ds --mode analysis \
    --task "Q1 churn analysis" \
    --context-file ~/briefs/q1_brief.txt
```

**Discover available modes and agents for a team:**
```bash
python flows/pp_flow.py --team <team> --list-modes
```

Context resolution order (first match wins): `--project` → `--context-file` → `--context` → none.
Output is always printed to stdout. Use `--save` (requires `--project`) to write to `output/<project>/`.

### 4.4 Passing Upstream Artifacts

When you already have artifacts from a prior PP run (or from your own pipeline), include them explicitly so PP agents consume them as authoritative upstream context rather than regenerating:

```
Upstream artifacts available:
- PRD: [attach or paste]
- TAD: [attach or paste]
- SRR: [attach or paste]

Please continue from [agent name / artifact name].
```

---

## 5. Checkpoint & HITL Behavior

PP pauses at defined checkpoints and waits for human approval before continuing. **If you are operating in an automated pipeline, you must account for these pauses.** PP will not proceed past a checkpoint without a response.

| Checkpoint | Trigger | What Happens |
|---|---|---|
| **CP-1** | After PRD | Human reviews requirements before analysis deepens |
| **CP-2** | After TAD | Human reviews architecture before security review |
| **CP-3** | After SRR | Security rating presented — RED blocks pipeline until resolved |
| **CP-4** | After Sprint Plan | Human approves backlog before build begins |
| **CP-4.5** | After FSP (Finance Summary Package) | Human reviews full financial picture before build begins |
| **CP-5** | After build phase | Human reviews all implementation reports before QA |
| **CP-6** | After TAR | Human approves test results before delivery |
| **Multi-SME gate** | After any multi-SME synthesis | Human reviews Domain Intelligence Brief before it is acted on |
| **HR action gate** | Before any HR action affecting a person | Human must approve — no exceptions |
| **DESIGN_REVIEW** | After every design team deliverable | Design assets approved before handoff to dev |
| **LEGAL_REVIEW** | After every legal team deliverable | Legal output approved before any action is taken |
| **QA_SIGN_OFF** | After QA team audits | Cross-team quality results reviewed and signed off |
| **STRATEGY** | After strategy team deliverables | Strategic outputs reviewed before execution |
| **OKR_CYCLE** | After OKR Planner output | OKR framework approved before adoption |
| **COMPETITIVE** | After competitive intelligence output | Competitive brief reviewed before it informs decisions |
| **POST** | After social media posts | Posts approved before scheduling or publishing |
| **EMAIL** | After email sequences | Email sends approved before execution |
| **VIDEO** | After video production deliverables | Scripts and briefs approved before production begins |

**Security RED block:** If the Security Reviewer rates the architecture 🔴 RED, the pipeline halts entirely. PP will not proceed to build until a human resolves the finding and re-runs the security review.

---

## 6. Constraints & Permissions

### What PP will not do

| Constraint | Source |
|---|---|
| Dev-team agents cannot call the SME Group | Hard permission block — raises `PermissionError` |
| HR team will never recommend replacing a human with AI | Hardcoded behavioral constraint |
| HR actions affecting a person require human approval before execution | No exceptions — enforced at flow level, cannot be bypassed via agent direct |
| Finance Group is advisory only — it will never auto-block the pipeline | By design |
| Secrets are never hardcoded in any generated artifact | Quality standard |
| No placeholder code in any build output | Quality standard |
| Video team flows raise `NotImplementedError` until agent templates are committed | Stub — modes locked in, wiring pending |

### Agent direct constraints

When invoking an agent via `pp_flow.py --agent`, the following rules still apply:
- **HR guardrails** are enforced at the flow level — humans-only model and cross-team flags are injected into every HR agent task regardless of invocation path
- **SME access controls** are enforced by `validate_caller()` — only authorized callers can invoke SME agents
- **HITL gates** in agent direct runs fire the same way as in orchestrated runs — output is not delivered without human approval where a gate is defined
- **`--save` requires `--project`** — agent direct output is stdout-only unless a project is specified

### Authorized SME callers

Only these callers may invoke the SME Group:
- `pp_orchestrator`
- `project_manager`
- `strategy`
- `legal`

Attempts from any other caller raise a `PermissionError`.

### Deployment agnosticism

All generated code uses environment variables for provider selection. No cloud provider names appear in application code. `DEPLOY_TARGET` controls provider modules. If you are consuming PP artifacts and feeding them into a cloud-specific pipeline, you are responsible for the provider mapping.

---

## 7. Artifact Quick Reference

| Code | Full Name | Produced By |
|---|---|---|
| `PRD` | Product Requirements Document | Product Manager |
| `BAD` | Business Analysis Document | Business Analyst |
| `TAD` | Technical Architecture Document | Technical Architect |
| `SRR` | Security Review Report | Security Reviewer |
| `UXD` | User Experience Document | UX/UI Designer |
| `TIP` | Technical Implementation Plan | Senior Developer |
| `BIR` | Backend Implementation Report | Backend Developer |
| `FIR` | Frontend Implementation Report | Frontend Developer |
| `DBAR` | Database Administration Report | Database Administrator |
| `DIR` | DevOps Implementation Report | DevOps Engineer |
| `MTP` | Master Test Plan | QA Lead |
| `TAR` | Test Automation Report | Test Automation Engineer |
| `MUXD` | Mobile UX Document | Mobile UX Designer |
| `IIR` | iOS Implementation Report | iOS Developer |
| `AIR` | Android Implementation Report | Android Developer |
| `RNAD` | React Native Architecture Document | RN Architect |
| `MDIR` | Mobile DevOps Implementation Report | Mobile DevOps |
| `CEA` | Cost Estimates & Budget Document | Cost Analyst |
| `ROI` | ROI & Business Case Analysis | ROI Analyst |
| `ICM` | Infrastructure Cost Model | Infrastructure Finance Modeler |
| `BPS` | Billing & Payment Feature Spec | Billing Architect |
| `PRI` | Pricing Strategy & Model | Pricing Specialist |
| `FSR` | Financial Statements Report | Financial Statements Modeler |
| `SCF` | Strategic Corporate Finance Report | Strategic Corp Finance Specialist |
| `FSP` | Finance Summary Package | Finance Orchestrator |

---

*Protean Pursuits — Agent System v2.1 — Capability Reference for External Projects*

*Updated April 2026 — reflects flow architecture (pp_flow, team flows, agent direct)*
