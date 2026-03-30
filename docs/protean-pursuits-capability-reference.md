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

```
PP Orchestrator
  └── Project Manager
        └── Team Leads (one per team)
              └── Team Orchestrators
                    └── Specialist Agents
```

PP's master orchestrator receives the request, classifies it, selects the relevant team(s), and routes accordingly. **You do not need to address individual agents** — describe what you need and PP routes it.

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

| Team | Run Modes | Key Constraint |
|---|---|---|
| **HR Team** | `RECRUIT \| ONBOARD \| REVIEW \| POLICY \| CULTURE \| BENEFITS \| FULL_CYCLE` | Humans-only workforce model — never recommends replacing a person with AI. All outputs require human approval before any action affecting a person is taken. Mandatory cross-team flags on every output: Legal / Finance / Strategy / QA. |
| **Marketing Team** | — | Copywriter agent produces landing pages, paid ads, app store listings, push notifications, in-product copy, campaign messaging |
| **Strategy Team** | — | Authorized SME caller |
| **Legal Team** | — | Authorized SME caller |
| **Design Team** | — | Visual design deliverables |
| **QA Team** | — | Standalone QA crew separate from dev-team quality phase |

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

### 4.3 Passing Upstream Artifacts

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

**Security RED block:** If the Security Reviewer rates the architecture 🔴 RED, the pipeline halts entirely. PP will not proceed to build until a human resolves the finding and re-runs the security review.

---

## 6. Constraints & Permissions

### What PP will not do

| Constraint | Source |
|---|---|
| Dev-team agents cannot call the SME Group | Hard permission block — raises `PermissionError` |
| HR team will never recommend replacing a human with AI | Hardcoded behavioral constraint |
| HR actions affecting a person require human approval before execution | No exceptions |
| Finance Group is advisory only — it will never auto-block the pipeline | By design |
| Secrets are never hardcoded in any generated artifact | Quality standard |
| No placeholder code in any build output | Quality standard |

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

*Protean Pursuits — Agent System v2.0 — Capability Reference for External Projects*
