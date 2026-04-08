Protean Pursuits

# Agent System Operating Manual

Your AI team of teams — 70+ agents that turn a plain-English
project description into architecture, code, tests, and deployment.

CrewAI · Ollama · ChromaDB · qwen3 · GitHub

Version 3.1 — April 2026  ·  Reflects commit `fdaabc3` and beyond

## Contents

**Part I — Use It**

1. [How It Works — The Big Picture](#s1)
2. [What Kind of Project Am I Running?](#s2)
3. [Meet the Teams](#s3)
4. [Agent Groups (Finance, SME, HR)](#s4)
5. [Run Your First Project](#s5)
6. [Command Cheat Sheet](#s6)
7. [Checkpoints — When It Asks You Something](#s7)
8. [When Things Go Wrong](#s8)

**Part II — Customize It**

9. [Change Models, Tune Agents, Add New Ones](#s9)
10. [Day-to-Day Operations](#s10)

**Part III — Reference**

11. [Appendix A — Full Agent Roster](#app-a)
12. [Appendix B — Artifact Registry](#app-b)
13. [Appendix C — Context Object Schema](#app-c)
14. [Appendix D — Conflict Resolution & Escalation](#app-d)
15. [Appendix E — Quality Standards](#app-e)
16. [Appendix F — Model Tier Reference](#app-f)

# 1. How It Works

You describe what you want in plain English. Protean Pursuits routes it through a hierarchy of AI agents — each an expert at a specific job — in a fixed sequence. You approve the work at key checkpoints. At the end you have a full set of documents, architecture, code, and tests.

### The orchestration hierarchy

YOU ──→ Plain-English project description
│
▼
┌──────────────────────────────────────────────────────────┐
│ PP ORCHESTRATOR (agents/orchestrator/orchestrator.py) │
│ Discovery interview · PRD auto-gen · Team assignment │
│ Cross-project memory · Blocker escalation │
└────────────────────┬─────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────┐
│ PROJECT MANAGER (agents/project\_manager/) │
│ Sprint planning · Timeline · Cross-team deps · Status │
└──┬────────────────────────────────────────────────┬──────┘
│ │
▼ ▼
Team Lead Team Lead
(agents/leads/dev/) (agents/leads/hr/) …etc
│ │
▼ ▼
Team Orchestrator Team Orchestrator
│ │
▼ ▼
Specialist Agents Specialist Agents

### Three rules the system never breaks

1. **Nothing starts without a clear spec.** The PP Orchestrator turns your request into a structured project (PRD) before any team touches it — either via a discovery interview or from a brief you supply directly.
2. **Nothing passes a checkpoint without your approval.** The system sends SMS + email, then waits. No agent ships anything autonomously.
3. **Everything is logged.** Every decision, artifact, and approval is written to a project context JSON file and to git history.

**Notification setup:** SMS goes via AT&T email-to-text gateway. Email goes via Outlook SMTP. Configure `HUMAN_PHONE_NUMBER`, `HUMAN_EMAIL`, `OUTLOOK_ADDRESS`, and `OUTLOOK_PASSWORD` in `config/.env`.

# 2. What Kind of Project Am I Running?

The PP Orchestrator classifies your request into one of three types and routes accordingly. You don't pick — it figures it out from your description.

What does your project need?
│
┌───────────────┼───────────────┐
▼ ▼ ▼
Software only? Data analysis Both?
(app, API, only? (EDA, (analyze data,
dashboard, ML model, then build an
automation) stats, reports) app from results)
│ │ │
▼ ▼ ▼
DEV crew DS crew JOINT
30+ agents run 14+ agents run DS runs first,
full web + data pipeline hands off to Dev
mobile pipeline with a formal
package

| If you say… | It becomes | What runs |
| --- | --- | --- |
| "Build me a dashboard for tracking orders" | **DEV** | Full dev pipeline: requirements → architecture → code → tests |
| "Analyze last year's sales data and show me patterns" | **DS** | Data science pipeline: EDA → analysis → models → reporting |
| "Analyze our trip data, then build a dashboard from the results" | **JOINT** | DS pipeline first → handoff package → DEV pipeline second |

**Be specific.** "Build a dashboard" produces vague output. "Build an interactive dashboard showing monthly trip data with filters for type, date range, and provider, deployed as a containerized web app" gives agents much better starting material.

# 3. Meet the Teams

Protean Pursuits has **9 active teams**, each with its own orchestrator, specialists, flow, and output directory. Every team follows the same internal structure: `agents/ flows/ config/ output/ memory/ docs/`.

## Dev Team — Core Software Pipeline

The primary software engineering team. Runs a sequential pipeline from requirements through deployable code and tests. All agents read env vars for model selection — no model names are hardcoded.

### 🔵 Planning Agents Tier 1

#### Product Manager

Turns your project description into a detailed requirements document — user stories, acceptance criteria, scope boundaries, and a clear definition of done.

📥 Project spec → 📄 **PRD** (Product Requirements Document)

#### Business Analyst

Goes deeper than the PRD. Maps stakeholders, draws process flows, builds data dictionaries. Answers every structural question the PRD leaves open.

📥 PRD → 📄 **BAD** (Business Analysis Document)

#### Scrum Master

Breaks requirements into sprints — prioritized backlog, story points, sprint sequencing, and definition of ready.

📥 PRD + BAD → 📄 **Sprint Plan**

#### Technical Architect

Designs the whole system — technologies, data flows, deployment model, component boundaries, and integration points. Deployment-agnostic: uses `DEPLOY_TARGET` env var, never cloud provider names in code.

📥 PRD + BAD + Sprint Plan → 📄 **TAD** (Technical Architecture Document)

#### Security Reviewer

Reviews the architecture for security holes, compliance gaps, and privacy risks. A 🔴 RED rating hard-blocks the pipeline — build agents cannot run until the finding is resolved.

📥 PRD + TAD → 📄 **SRR** rated 🟢 GREEN / 🟡 AMBER / 🔴 RED

#### UX/UI Designer

Designs every screen, interaction, and user journey. Defines the complete information architecture.

📥 PRD + BAD + SRR → 📄 **UXD** (User Experience Document)

#### UX Content Guide

Writes every label, button, tooltip, placeholder, and error message. Developers never make up UI text — they copy it from here.

📥 UXD → 📄 **UI Content Guide**

### 🟢 Build Agents Tier 2

#### Senior Developer

Translates architecture into a concrete coding plan — project structure, module boundaries, coding standards, implementation order. This is the bible the other developers follow.

📥 PRD + TAD + UXD → 📄 **TIP** (Technical Implementation Plan)

#### Backend Developer

Builds server-side code — APIs, authentication, business logic, data access. Complete working code, no placeholders, no TODOs.

📥 TIP + TAD → 📄 **BIR** (Backend Implementation Report) + code

#### Frontend Developer

Builds the user interface — pages, components, state management, API integration. Uses exact text from the Content Guide.

📥 TIP + UXD + BIR + Content Guide → 📄 **FIR** (Frontend Implementation Report) + code

#### Database Administrator

Reviews and optimizes the schema — indexes, migrations, backups, capacity planning. Developers do not modify the database without this agent's sign-off.

📥 BIR + TAD + SRR → 📄 **DBAR** (Database Administration Report)

#### DevOps Engineer

Sets up everything for build, test, and deploy — Docker, CI/CD pipelines, infrastructure-as-code, secrets management. Deployment-agnostic output.

📥 TIP + TAD + SRR → 📄 **DIR** (DevOps Implementation Report)

### 🟠 Quality Agents

#### QA Lead Tier 1

Reads every document the team produced and designs the test plan — what to test, how, and what "done" means.

📥 PRD + TIP + BIR + FIR + UXD → 📄 **MTP** (Master Test Plan)

#### Test Automation Engineer Tier 2

Writes the actual test code — unit tests, API tests, E2E tests, accessibility tests. Real code that runs: Jest, Playwright, axe-core, k6.

📥 MTP + BIR + FIR + TIP → 📄 **TAR** (Test Automation Report) + test code

### 📱 Mobile Agents (activates automatically when project includes a mobile app)

#### Mobile UX Designer Tier 1

Designs the mobile experience — iOS, Android, and React Native all work from this one document.

📥 PRD → 📄 **MUXD** (Mobile UX Document)

#### iOS Developer Tier 2

Builds the native iOS app in Swift/SwiftUI with VoiceOver accessibility and secure storage.

📥 MUXD + PRD → 📄 **IIR** (iOS Implementation Report) + Swift code

#### Android Developer Tier 2

Builds the native Android app in Kotlin/Jetpack Compose with TalkBack and encrypted storage.

📥 MUXD + PRD → 📄 **AIR** (Android Implementation Report) + Kotlin code

#### RN Architect Tier 2

Designs the React Native/Expo/TypeScript architecture in two parts. Part 2 receives Part 1's actual output as context — not the raw spec — to prevent re-generation loops.

📥 MUXD + PRD → 📄 **RNAD P1** + **RNAD P2**

#### RN Developer Tier 2

Produces the cross-platform implementation guide. Receives RNAD P1 output — not the raw spec — as context injection.

📥 RNAD + MUXD → 📄 **RN Guide**

#### Mobile DevOps Engineer Tier 2

Build pipelines, code signing, TestFlight/Play Console automation, EAS Build, Fastlane, GitHub Actions for mobile.

📥 IIR / AIR / RN Guide → 📄 **MDIR** (Mobile DevOps Report)

#### Mobile QA Specialist Tier 1

Writes the mobile test suite — XCTest, JUnit5/Espresso, Detox. Tests accessibility on real device flows.

📥 MTP + IIR + AIR + RN Guide → Mobile test suite

### 🔁 Retrofit Agents Tier 2

Re-process existing artifacts to strip provider-specific content and make the system deployment-agnostic. These agents process *finalized* documents — they are deliberately excluded from RAG injection.

| Agent | File | Input | Output |
| --- | --- | --- | --- |
| TAD Retrofit | `dev/build/tad_retrofit.py` | TAD | TAD-R |
| BIR Retrofit | `dev/build/backend_developer_retrofit.py` | BIR | BIR-R |
| DIR Retrofit | `dev/build/devops_engineer_retrofit.py` | DIR | DIR-R |
| SRR Retrofit | `dev/build/srr_retrofit.py` | SRR | SRR-R |
| MTP Retrofit | `dev/quality/qa_lead_retrofit.py` | MTP | MTP-R |
| Reconciliation | `dev/reconciliation.py` | All -R artifacts | Gap report |

### 📚 Docs Agents

#### API Documentation & DevEx Writer

Produces API reference docs, README, developer guides, SDK quickstarts, and onboarding content.

Location: `templates/dev-team/agents/docs/devex_writer.py`

#### Technical Writer

Produces user guides, admin guides, runbooks, release notes, KB articles, and internal onboarding content.

Location: `templates/dev-team/agents/docs/technical_writer.py`

### RAG Memory (ChromaDB)

Planning and build agents are RAG-wired via ChromaDB. The Knowledge Curator populates the store from four sources: GitHub releases, ArXiv papers, NVD/OWASP security feeds, and VA/CMS policy bulletins. Run manually:

# Tech/security sources
python agents/shared/knowledge\_curator/curator.py --source github --source security
# Research + policy sources
python agents/shared/knowledge\_curator/curator.py --source arxiv --source va\_cms

## DS Team — Data Science Pipeline

Handles analytical workflows from initial framing through final reporting. Features **complexity-adaptive filtering** — the pipeline depth scales automatically to LOW / MEDIUM / HIGH complexity classifications. LOW projects skip agents and checkpoints that aren't needed.

Anti-hallucination discipline is enforced via a `validators.py` module with six checks: source grounding, fabricated statistics detection, confidence marker enforcement, section completeness, forbidden content filtering, and upstream consistency. All DS agent outputs require `[ASSUMPTION]` and `[VERIFY]` tags where applicable.

**DS → DEV handoff (JOINT projects):** The DS team produces a formal handoff package. The DEV team receives it as authoritative upstream context and does not re-run the analysis.

## Design Team

| Agent | File |
| --- | --- |
| Design Orchestrator | `agents/orchestrator/orchestrator.py` |
| UX Researcher | `agents/ux_research/ux_research_agent.py` |
| Wireframing Specialist | `agents/wireframing/wireframing_agent.py` |
| UI Designer | `agents/ui_design/ui_design_agent.py` |
| Brand Identity Specialist | `agents/brand_identity/brand_identity_agent.py` |
| Design System Architect | `agents/design_system/design_system_agent.py` |
| Motion & Animation Designer | `agents/motion_animation/motion_agent.py` |
| Accessibility Specialist | `agents/accessibility/accessibility_agent.py` |
| Usability Analyst | `agents/usability/usability_agent.py` |

HITL gate type: `DESIGN_REVIEW`. All outputs require your approval before assets are handed to the Dev team.

## Legal Team

| Agent | File |
| --- | --- |
| Legal Orchestrator | `agents/orchestrator/orchestrator.py` |
| Contract Drafter | `agents/contract_drafting/contract_agent.py` |
| Document Reviewer | `agents/document_review/review_agent.py` |
| Corporate Entity Specialist | `agents/corporate_entity/corporate_agent.py` |
| IP & Licensing Specialist | `agents/ip_licensing/ip_agent.py` |
| Privacy & Data Counsel | `agents/privacy_data/privacy_agent.py` |
| Regulatory Compliance Specialist | `agents/regulatory_compliance/compliance_agent.py` |
| Employment & Contractor Counsel | `agents/employment_contractor/employment_agent.py` |
| Litigation & Dispute Specialist | `agents/litigation_dispute/litigation_agent.py` |

HITL gate type: `LEGAL_REVIEW`. Legal is an **authorized SME caller** — it may invoke the SME Group directly.

## Marketing Team

Location: `templates/marketing-team/` · HITL gate types: `POST`, `EMAIL`, `VIDEO`. Every deliverable is submitted for human approval before publishing or execution — no agent publishes autonomously.

#### Marketing Orchestrator

Plans, coordinates, and tracks all marketing campaigns across social, video, email, and analytics workstreams — ensuring every deliverable is on-brand, on-schedule, and approved by the human before publishing.

File: `agents/orchestrator/orchestrator.py`

#### Marketing Analyst

Pulls data from analytics dashboards across all marketing channels, synthesises performance against KPIs from the Marketing Plan, identifies optimisation opportunities, and produces structured reports for the Marketing Orchestrator and human review.

📄 Channel performance reports, KPI dashboards · File: `agents/analyst/analyst_agent.py`

#### Copywriter

Writes persuasive, on-brand copy for every marketing surface — landing pages, paid ads, app store listings, push notifications, in-product marketing, campaign messaging, and brand campaigns — that converts readers into users and users into advocates.

📄 Landing page copy, ad creative, app store listings, push copy, campaign messaging · File: `agents/copywriter/copywriter_agent.py`

#### Email Specialist

Writes and structures all email communications — newsletters, drip sequences, transactional emails, and re-engagement campaigns — using CRM segmentation data to personalise at scale. Submits every send for human approval before execution.

📄 Email sequences, drip campaigns, transactional templates · File: `agents/email/email_agent.py` · Gate: `EMAIL`

#### Social Media Specialist

Researches trending topics, drafts daily on-brand posts for X, Instagram, TikTok, and Discord, generates or sources supporting visuals, and submits every post for human approval before scheduling or publishing.

📄 Social post drafts, visual briefs · File: `agents/social/social_agent.py` · Gate: `POST`

#### Video Producer

Scripts, structures, and produces video content for TikTok, YouTube Shorts, and long-form YouTube — including Veo visual direction briefs and Lyria 3 music briefs. Submits every video for human approval before publishing.

📄 Scripts, visual direction briefs, music briefs · File: `agents/video/video_agent.py` · Gate: `VIDEO`

## Strategy Team

| Agent | File |
| --- | --- |
| Strategy Orchestrator | `agents/orchestrator/orchestrator.py` |
| Brand Positioning Strategist | `agents/brand_positioning/brand_agent.py` |
| Business Model Designer | `agents/business_model/business_model_agent.py` |
| Competitive Intelligence Analyst | `agents/competitive_intel/competitive_intel_agent.py` |
| Financial Strategist | `agents/financial_strategy/financial_strategy_agent.py` |
| GTM Strategist | `agents/gtm/gtm_agent.py` |
| OKR Planner | `agents/okr_planning/okr_agent.py` |
| Partnership Strategist | `agents/partnership/partnership_agent.py` |
| Product Strategist | `agents/product_strategy/product_strategy_agent.py` |
| Risk & Scenario Planner | `agents/risk_scenario/risk_agent.py` |
| Talent & Org Designer | `agents/talent_org/talent_agent.py` |
| Technology Strategist | `agents/technology_strategy/tech_strategy_agent.py` |

HITL gate types: `STRATEGY`, `OKR_CYCLE`, `COMPETITIVE`. Strategy is an **authorized SME caller**.

## QA Team (Standalone)

A cross-team QA crew that operates independently of the Dev team's internal quality phase. Can be engaged to audit any team's deliverables.

| Agent | File |
| --- | --- |
| QA Orchestrator | `agents/orchestrator/orchestrator.py` |
| Functional Testing Specialist | `agents/functional_testing/functional_agent.py` |
| Performance Testing Specialist | `agents/performance_testing/performance_agent.py` |
| Security Testing Specialist | `agents/security_testing/security_agent.py` |
| Accessibility Auditor | `agents/accessibility_audit/accessibility_audit_agent.py` |
| Data Quality Analyst | `agents/data_quality/data_quality_agent.py` |
| Legal Completeness Reviewer | `agents/legal_completeness/legal_qa_agent.py` |
| Marketing Compliance Reviewer | `agents/marketing_compliance/marketing_qa_agent.py` |
| Test Case Developer | `agents/test_case_development/test_case_agent.py` |

HITL gate type: `QA_SIGN_OFF`.

## Video Team

| Agent | File |
| --- | --- |
| Video Orchestrator | `agents/orchestrator/orchestrator.py` |
| Script Writer | `agents/script/script_writer.py` |
| Visual Director | `agents/visual/visual_director.py` |
| Audio Producer | `agents/audio/audio_producer.py` |
| Avatar Producer | `agents/avatar/avatar_producer.py` |
| Tool Intelligence Analyst | `agents/tool_intelligence/tool_analyst.py` |
| API Engineer | `agents/production/api_engineer.py` |
| Compliance Reviewer | `agents/compliance/compliance_reviewer.py` |

HITL gate types: `VIDEO_TOOL_SELECTION` (after Tool Analyst, before any creative work), `SCRIPT_REVIEW` (after Script Writer, before API calls), `VIDEO_FINAL` (after Compliance Reviewer, before any publish action). No video deliverable is produced autonomously.

Run modes: `BRIEF_ONLY | SHORT_FORM | LONG_FORM | AVATAR | DEMO | EXPLAINER | VOICEOVER | FULL`

# 4. Agent Groups

Agent groups are specialized crews that operate alongside the main teams. They have their own access rules, invocation patterns, and behavioral constraints.

## Finance Group Dev Team Sub-Crew

**Not a standalone team.** Runs as a sub-crew of the Dev team — after full planning (post UX Content Guide), before the build phase. Advisory only — it **never auto-blocks the pipeline**. Fires checkpoint CP-4.5 on FSP completion. Location: `templates/dev-team/agents/finance/`

**Auto-detection rules:** Billing Architect (`BPS`) is skipped if no billing/payment/subscription language is found in the PRD. Pricing Specialist (`PRI`) is skipped for internal tooling projects. The orchestrator scans PRD keywords at runtime and logs any skip with its reason.

**Output standards enforced on every Finance artifact:** opens with `FINANCE RATING: 🟢 GREEN | 🟡 AMBER | 🔴 RED`; every numeric estimate documents its assumptions; LOW / MID / HIGH scenarios where applicable; no fabricated benchmarks; ends with `OPEN QUESTIONS`.

**Invocation:**

python agents/finance/finance\_orchestrator.py # full crew run
python agents/finance/cost\_analyst.py # single-agent shortcut

#### Finance Orchestrator Tier 1

Reads PRD + TAD to determine which specialists are relevant, sequences the 7-agent crew (CEA → ROI → ICM → BPS → PRI → FSR → SCF), cross-checks outputs for internal consistency, retries a failed agent once before escalating, compiles the Finance Summary Package, and fires CP-4.5.

📥 PRD + TAD → 📄 **FSP** (Finance Summary Package) · File: `finance_orchestrator.py`

#### Cost Analyst Tier 1

Produces a detailed, assumption-documented cost estimate and budget envelope — development costs, infrastructure, licensing, tooling, and third-party services — across LOW / MID / HIGH scenarios. Always runs first; feeds into ROI, ICM, and FSR.

📥 PRD + TAD → 📄 **CEA** (Cost Estimates & Budget) · File: `cost_analyst.py`

#### ROI Analyst Tier 1

Builds the investment case — quantifies expected returns, calculates NPV and IRR, models break-even, and produces a risk-adjusted recommendation: proceed, revise scope, or stop. Answers: is this worth building?

📥 PRD + CEA → 📄 **ROI** (ROI & Business Case Analysis) · File: `roi_analyst.py`

#### Infrastructure Finance Modeler Tier 1

Translates the technical architecture into a financial model — maps every infrastructure component (TAD) to a cost line, builds scaling curves, models cloud vs. on-prem trade-offs, and produces a month-by-month cost projection for years 1–3.

📥 TAD + CEA → 📄 **ICM** (Infrastructure Cost Model) · File: `infra_finance_modeler.py`

#### Billing Architect Tier 1

Specifies all billing and payment feature requirements with enough precision that Backend and Frontend developers can implement without follow-up questions. Covers provider selection (Stripe, Braintree, PayPal, Adyen), payment flows, subscription lifecycle, refunds, and PCI/DSS requirements.

📥 PRD + TAD → 📄 **BPS** (Billing & Payment Feature Spec) · File: `billing_architect.py`

⚠️ CONDITIONAL: Skipped if no billing/payment/subscription language detected in PRD

#### Pricing Specialist Tier 1

Develops a defensible go-to-market pricing strategy — tier structures, price points, margin analysis, and competitive positioning — that maximises long-term revenue while fitting the product's market. Combines economics, competitive analysis, and customer psychology.

📥 PRD + CEA + ROI → 📄 **PRI** (Pricing Strategy & Model) · File: `pricing_specialist.py`

⚠️ CONDITIONAL: Skipped for internal tooling projects

#### Financial Statements Modeler Tier 1

Produces the three core projected financial statements — Income Statement, Cash Flow Statement, and Balance Sheet — synthesised from all other Finance specialist outputs. 3-year projections, CPA-grade methodology.

📥 CEA + ROI + ICM + PRI → 📄 **FSR** (Financial Statements Report) · File: `financial_statements.py`

#### Strategic Corporate Finance Specialist Tier 1

Synthesises all Finance outputs into a strategic corporate finance strategy — capital structure, funding options, M&A considerations, financial risk register — and produces a two-page executive summary suitable for stakeholder or investor review. Always runs last.

📥 All Finance artifacts → 📄 **SCF** (Strategic Corp Finance Report) · File: `strategic_corp_finance.py`

## SME Group Access-Controlled

Project-agnostic domain specialists callable from any current or future Protean Pursuits project. Location: `agents/sme/`

**⛔ Authorized callers only:** `pp_orchestrator`, `project_manager`, `strategy`, `legal`. Dev-team agents are explicitly blocked — a `PermissionError` is raised at runtime via `validate_caller()`. Attempting to call from an unauthorized agent raises immediately; there is no fallback.

**Three invocation patterns:**

# Single SME direct
run\_sme\_consult(context, "pga", question, caller="project\_manager")
# Multi-SME orchestrated (fires HITL review gate on synthesis)
run\_sme\_crew(context, ["pga", "lpga"], question, caller="strategy")
# Auto-detect domains from keywords
run\_sme\_crew(context, [], question, caller="pp\_orchestrator")

**Output standards on every SME artifact:** opens with `DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW`; ends with `CROSS-TEAM FLAGS` and `OPEN QUESTIONS`. Multi-SME synthesis fires a HITL review gate before the Domain Intelligence Brief is acted on.

#### SME Orchestrator

Routes incoming questions to the correct specialist(s) based on keyword detection or explicit registry keys, manages multi-SME crew execution, synthesises individual outputs into a Domain Intelligence Brief, and fires the HITL review gate on any multi-expert output.

📄 Domain Intelligence Brief · File: `sme_orchestrator.py`

#### Sports Betting Expert · `sports_betting`

Provides authoritative cross-sport and industry-level expertise — market structures, operator economics, regulatory landscape, product design, bettor behaviour, and global market nuances — to any PP project operating in or adjacent to sports wagering. The top-level industry authority; use when the question spans multiple sports or is about the industry itself.

File: `sports_betting_expert.py`

#### World Football & Soccer Betting Expert · `world_football`

Deep domain expertise on football/soccer betting markets worldwide — leagues, competitions (EPL, La Liga, Bundesliga, Serie A, Ligue 1, Champions League, World Cup, CONCACAF, AFC, CAF, CONMEBOL), market structures, Asian handicap pricing dynamics, and bettor behaviour across every country where football wagering operates.

File: `world_football_expert.py`

#### NBA & NCAA Men's Basketball Betting Expert · `nba_ncaa_basketball`

Deep domain expertise on NBA and NCAA men's basketball betting markets — league structures, market types (spread, moneyline, totals, player props), pricing dynamics, totals behaviour, March Madness, and regulatory nuances across every jurisdiction where basketball wagering operates.

File: `nba_ncaa_basketball_expert.py`

#### NFL & NCAA Football Betting Expert · `nfl_ncaa_football`

Deep domain expertise on NFL and NCAA football betting markets — league structures, spread dynamics, totals behaviour, player props, futures markets, College Football Playoff, and regulatory nuances across every jurisdiction where American football wagering operates.

File: `nfl_ncaa_football_expert.py`

#### MLB Betting Expert · `mlb`

Deep domain expertise on MLB and baseball betting markets worldwide — league structures, moneyline and run line dynamics, pitcher-driven pricing, totals behaviour, props markets, and coverage of NPB (Japan), KBO (Korea), and CPBL (Taiwan) in addition to MLB.

File: `mlb_expert.py`

#### NHL & NCAA Men's Hockey Betting Expert · `nhl_ncaa_hockey`

Deep domain expertise on NHL and NCAA men's hockey betting markets — puck line and moneyline dynamics, goaltender pricing, totals behaviour, props markets, KHL and major European league coverage, and regulatory nuances across every jurisdiction where hockey wagering operates.

File: `nhl_ncaa_hockey_expert.py`

#### MMA Betting Expert · `mma`

Deep domain expertise on MMA betting markets worldwide — promotion structures (UFC, Bellator, ONE Championship, Rizin), moneyline dynamics, method-of-victory markets, fighter analysis frameworks, props pricing, and regulatory nuances across every jurisdiction where MMA wagering operates.

File: `mma_expert.py`

#### Tennis Betting Expert · `tennis`

Deep domain expertise on tennis betting markets worldwide — ATP Tour, WTA Tour, Challenger and ITF circuits, surface dynamics (hard, clay, grass), match and set betting, live in-play tennis markets, player prop markets, and regulatory nuances across every jurisdiction where tennis wagering operates.

File: `tennis_expert.py`

#### World Rugby Betting Expert · `world_rugby`

Deep domain expertise on rugby union and rugby league betting markets worldwide — Six Nations, Rugby Championship, NRL, State of Origin, Super Rugby, Premiership, United Rugby Championship, spread and totals dynamics, props markets, and regulatory nuances across every jurisdiction where rugby wagering operates.

File: `world_rugby_expert.py`

#### Cricket Betting Expert · `cricket`

Deep domain expertise on cricket betting markets worldwide — all three formats (Test, ODI, T20), all major competitions (IPL, The Hundred, Big Bash, CPL, PSL, SA20), pitch and weather dynamics, player prop markets (runs, wickets, milestones), and regulatory nuances across every jurisdiction where cricket wagering operates.

File: `cricket_expert.py`

#### WNBA & NCAA Women's Basketball Betting Expert · `wnba_ncaa_womens_basketball`

Deep domain expertise on WNBA and NCAA women's basketball betting markets — league structures, spread and totals dynamics, player props, market growth trajectory, and regulatory nuances across every jurisdiction where women's basketball wagering operates.

File: `wnba_ncaa_womens_basketball_expert.py`

#### Thoroughbred Horse Racing Betting Expert · `thoroughbred_horse_racing`

Deep domain expertise on thoroughbred horse racing betting markets worldwide — US (Breeders' Cup, Kentucky Derby, Belmont, Preakness), UK/Ireland (Royal Ascot, Cheltenham, Grand National), Australia (Melbourne Cup, Cox Plate), Hong Kong, Japan, France, and Dubai; pari-mutuel and fixed-odds structures, handicapping frameworks, and exotic wagering (exacta, trifecta, superfecta, Pick 6).

File: `thoroughbred_horse_racing_expert.py`

#### Harness Racing Betting Expert · `harness_racing`

Deep domain expertise on harness racing (standardbred) betting markets worldwide — trotting and pacing dynamics, Hambletonian, Meadowlands Pace, V75 (Sweden), V86, PMU (France), pari-mutuel structures, exotic wagering, and regulatory nuances across every jurisdiction where harness wagering operates.

File: `harness_racing_expert.py`

#### Men's Professional Boxing Betting Expert · `mens_boxing`

Deep domain expertise on men's professional boxing betting markets worldwide — all four sanctioning bodies (WBC, WBA, IBF, WBO), all 17 weight classes, moneyline and method-of-victory dynamics, round betting, props markets (knockdowns, scorecards), and regulatory nuances across every jurisdiction where boxing wagering operates.

File: `mens_boxing_expert.py`

#### PGA Tour Betting Expert · `pga`

Deep domain expertise on PGA Tour and men's professional golf betting markets worldwide — tournament structures, outright and head-to-head markets, course fit analysis, DP World Tour, LIV Golf, all four majors (Masters, US Open, The Open, PGA Championship), Ryder Cup, live in-play golf, and props markets across every jurisdiction where men's professional golf wagering operates.

File: `pga_expert.py`

#### LPGA Tour Betting Expert · `lpga`

Deep domain expertise on LPGA Tour and women's professional golf betting markets worldwide — tournament structures, outright and head-to-head markets, course fit analysis, JLPGA (Japan) and KLPGA (Korea) tour coverage, women's majors (ANA Inspiration, US Women's Open, Women's British Open, KPMG, Chevron), Solheim Cup, and props markets across every jurisdiction where women's professional golf wagering operates.

File: `lpga_expert.py`

## HR Team Standalone Team

A fully standalone team with its own template and live submodule at `teams/hr-team/` (`github.com/mfelkey/hr-team`). Lead: `agents/leads/hr/hr_lead.py`.

**Humans-only workforce model.** The HR team will never recommend replacing a person with AI. All outputs require human approval before any action affecting a person is taken. No exceptions.

**Run modes:** `RECRUIT | ONBOARD | REVIEW | POLICY | CULTURE | BENEFITS | FULL_CYCLE`

**Mandatory cross-team flags on every output:** Legal / Finance / Strategy / QA

| Agent | File |
| --- | --- |
| HR Orchestrator | `agents/hr/orchestrator/orchestrator.py` |
| Recruiting Specialist | `agents/hr/recruiting/recruiting_agent.py` |
| Onboarding Specialist | `agents/hr/onboarding/onboarding_agent.py` |
| Performance & Compensation Specialist | `agents/hr/performance_comp/performance_comp_agent.py` |
| Policy & Compliance Specialist | `agents/hr/policy_compliance/policy_compliance_agent.py` |
| Culture & Engagement Specialist | `agents/hr/culture_engagement/culture_engagement_agent.py` |
| Benefits Specialist | `agents/hr/benefits/benefits_agent.py` |

HITL gate type: `HR action gate` — fires before any action affecting a person.

# 5. Run Your First Project

## Prerequisites

| Tool | Install | Verify |
| --- | --- | --- |
| Ollama | `curl -fsSL https://ollama.com/install.sh | sh` | `curl http://localhost:11434/api/tags` |
| qwen3:32b | `ollama pull qwen3:32b` | Appears in tags list |
| qwen3-coder:30b | `ollama pull qwen3-coder:30b` | Appears in tags list |
| nomic-embed-text | `ollama pull nomic-embed-text` | Appears in tags list |
| Python 3.10+ | System package manager | `python3 --version` |
| CrewAI | `pip install "crewai[tools]"` | `python -c "import crewai"` |
| ChromaDB | `pip install chromadb` | `python -c "import chromadb"` |

## First-time environment setup

cd ~/projects/protean-pursuits
cp config/.env.template config/.env
# Edit config/.env — set these at minimum:
TIER1\_MODEL=ollama/qwen3:32b
TIER2\_MODEL=ollama/qwen3-coder:30b
EMBED\_MODEL=nomic-embed-text
OLLAMA\_BASE\_URL=http://localhost:11434
HUMAN\_EMAIL=you@example.com
HUMAN\_PHONE\_NUMBER=+15551234567
OUTLOOK\_ADDRESS=you@outlook.com
OUTLOOK\_PASSWORD=your-app-password

## Standard dev-team run

# 1. Start Ollama (if not running as a service)
ollama serve &
# 2. Navigate to your project directory (a cloned/renamed dev-team instance)
cd ~/projects/my-project
# 3. Classify your project
python agents/orchestrator/classify.py
# 4. Planning phase — runs in sequence
python agents/dev/strategy/product\_manager.py
⏸️ CP-1: Review PRD — type APPROVE or REJECT
python agents/dev/strategy/business\_analyst.py
python agents/dev/strategy/scrum\_master.py
python agents/dev/strategy/technical\_architect.py
⏸️ CP-2: Review architecture
python agents/dev/strategy/security\_reviewer.py
⏸️ CP-3: Review security rating
python agents/dev/strategy/ux\_designer.py
python agents/dev/strategy/ux\_content\_guide.py
⏸️ CP-4: Review UX & content
# 5. (Optional) Finance Group
python agents/finance/finance\_orchestrator.py
⏸️ CP-4.5: Review Finance Summary Package
# 6. Build phase
python agents/dev/build/senior\_developer.py
python agents/dev/build/backend\_developer.py
python agents/dev/build/frontend\_developer.py
python agents/dev/build/database\_admin.py
python agents/dev/build/devops\_engineer.py
⏸️ CP-5: Review implementation reports
# 7. Quality phase
python agents/dev/quality/qa\_lead.py
python agents/dev/quality/test\_automation\_engineer.py
⏸️ CP-6: Approve test results — final release gate

## Mobile add-on (after CP-4)

python agents/mobile/ux/mobile\_ux\_designer.py
python agents/mobile/ios/ios\_developer.py # iOS only
python agents/mobile/android/android\_developer.py # Android only
python agents/mobile/rn/react\_native\_architect\_part1.py # RN
python agents/mobile/rn/react\_native\_architect\_part2.py
python agents/mobile/rn/react\_native\_developer.py
python agents/mobile/devops/mobile\_devops\_engineer.py
python agents/mobile/qa/mobile\_qa\_specialist.py

## Retrofit run (deployment-agnostic cleanup)

python agents/dev/build/tad\_retrofit.py
python agents/dev/build/backend\_developer\_retrofit.py
python agents/dev/build/devops\_engineer\_retrofit.py
python agents/dev/build/srr\_retrofit.py
python agents/dev/quality/qa\_lead\_retrofit.py
python agents/dev/reconciliation.py

## HR team run

cd ~/projects/hr-team
python flows/hr\_flow.py --mode RECRUIT # or ONBOARD | REVIEW | POLICY | CULTURE | BENEFITS | FULL\_CYCLE

## Direct team access (post-initiation)

After a project is running, any team can be contacted directly with a plain-English brief — no full intake required. Each intake flow loads existing project context if you supply `--project`, or builds a minimal stub on cold start. The team orchestrator selects the appropriate run mode from the brief.

**All 8 teams have a dedicated intake flow at `flows/`:**

```bash
# Marketing — campaigns, copy, social, email, video, analytics
python flows/marketing_intake_flow.py \
    --project <name> --brief "Refresh App Store listing and 3-email drip for lapsed users" --save

# DS — EDA, analysis, models, pipeline
python flows/ds_intake_flow.py \
    --project <name> --brief "Run churn analysis on Q3 user cohort" --save

# Legal — contracts, review, IP, privacy, regulatory, employment, corporate, dispute
python flows/legal_intake_flow.py \
    --project <name> --brief "Review Terms of Service for GDPR compliance gaps" --save

# Strategy — positioning, GTM, competitive, OKR, financial, partnership, product, risk, talent, technology
python flows/strategy_intake_flow.py \
    --project <name> --brief "Build a competitive landscape for the US sports betting market" --save

# Design — research, wireframe, visual, motion, accessibility
python flows/design_intake_flow.py \
    --project <name> --brief "Wireframe the bet slip flow and onboarding screens" --save

# QA — functional, performance, security, accessibility, data quality, legal/marketing review, test cases
python flows/qa_intake_flow.py \
    --project <name> --brief "Security and accessibility audit on the new bet slip feature" --save

# HR — recruit, onboard, review, policy, culture, benefits (humans-only model enforced)
python flows/hr_intake_flow.py \
    --project <name> --brief "Draft onboarding plan for two new frontend engineers" --save

# Video — brief only, short form, long form, avatar, demo, explainer, voiceover, full campaign
python flows/video_intake_flow.py \
    --project <name> --brief "60s TikTok ad for ParallaxEdge launch — Q3, US market" --save
```

**Cold start (no existing project):** omit `--project` — you will be prompted for a project name and a minimal context stub is created automatically.

**Non-interactive (scripted use):** add `--non-interactive --project <name>` to suppress all prompts.

**Brief too short?** The flow detects briefs under 20 words and asks for additional context before proceeding. Skip with Enter or pass a fuller brief up front.

# 6. Command Cheat Sheet

Check Ollama is running

`curl http://localhost:11434/api/tags`

List downloaded models

`ollama list`

Pull a new model

`ollama pull <model-name>`

Check project status

`cat logs/PROJ-*.json | python -m json.tool | grep status`

Search output for TODOs

`grep -ri "todo\|placeholder\|TBD" output/`

Archive a project

`mkdir -p logs/archive && mv logs/PROJ-*.json logs/archive/`

Commit after agent run

`git add -A && git commit -m "PROJ-XXXXX: Agent → artifact"`

Export patch for local apply

`git format-patch HEAD~1 -o ~/Downloads/`

Apply patch locally

`git am ~/Downloads/<patch>.patch`

Abort stale rebase state

`git am --abort`

Refresh Knowledge Curator

`python agents/shared/knowledge_curator/curator.py --source github --source security`

Approve a checkpoint

Type `APPROVE` at the terminal prompt

Contact a team directly (post-initiation)

`python flows/<team>_intake_flow.py --project <name> --brief "<what you need>" --save`

List available teams for direct intake

`ls flows/*_intake_flow.py`

Cold-start a team without an existing project

`python flows/marketing_intake_flow.py --brief "<brief>"` *(prompts for project name)*

Non-interactive intake (scripted use)

`python flows/ds_intake_flow.py --project <name> --non-interactive --brief "<brief>" --save`

# 7. Checkpoints — When It Asks You Something

At defined points in every pipeline, the system stops and waits for you. It sends an SMS (AT&T gateway) and email (Outlook SMTP), prints the checkpoint summary in the terminal, writes a request file to `logs/approvals/`, and polls for a JSON response file.

### What to do when it stops:

1. Open the artifact file it references (e.g. `output/PROJ-XXXXX_PRD.md`)
2. Read through it — check FLAGS.md for known gaps first
3. Return to the terminal and type `APPROVE` or `REJECT`
4. If you reject, provide a reason — it is saved to the audit log and informs the re-run

### All checkpoint gates

| Gate | After which agent | What you're checking |
| --- | --- | --- |
| **CP-1: Requirements** | Product Manager → PRD | Are user stories right? Scope correct? Right things out of scope? |
| **CP-2: Architecture** | Technical Architect → TAD | Does the tech make sense? Achievable? Fits your infrastructure? |
| **CP-3: Security** | Security Reviewer → SRR | Is the rating acceptable? RED rating must be resolved before proceeding. |
| **CP-4: Design** | UX Content Guide → UI Content Guide | Does the UI make sense for users? Language clear? All screens covered? |
| **CP-4.5: Finance** | Finance Orchestrator → FSP | Do the financials make sense? Review all 🟢/🟡/🔴 ratings. Open Questions addressed? |
| **CP-5: Build** | DevOps Engineer → DIR | Spot-check the code. Search for TODO/placeholder. Does it look complete? |
| **CP-6: Release** | Test Automation Engineer → TAR | Tests pass? No open critical issues? Confident this is done? |
| **Multi-SME gate** | SME Orchestrator → Domain Intelligence Brief | Is the synthesised domain intelligence accurate and actionable? |
| **HR action gate** | Before any HR action affecting a person | Human must approve — no exceptions, no automation bypass. |
| **DESIGN\_REVIEW** | Design team deliverables | Design assets approved before handoff to Dev. |
| **QA\_SIGN\_OFF** | QA team | Cross-team quality audit results. |
| **LEGAL\_REVIEW** | Legal team | Legal deliverables approved before any action. |
| **VIDEO\_TOOL\_SELECTION** | Video Tool Analyst | Tool choices locked in before any creative work begins. |
| **SCRIPT\_REVIEW** | Video Script Writer | Script approved before API calls or asset generation. |
| **VIDEO\_FINAL** | Video Compliance Reviewer | Final review before any publish or distribution action. |

**Security RED block:** If the Security Reviewer rates the architecture 🔴 RED, the pipeline halts entirely. No build agents run until a human resolves the finding and the security review is re-run and approved.

**Terminal dies during a checkpoint?** The project context was saved before the gate fired. Re-run the same agent — it picks up where it left off. The approval request file in `logs/approvals/` persists across restarts.

# 8. When Things Go Wrong

## 🔇 Agent sits there doing nothing (30+ minutes)

**What happened:** LLM timeout or context window exhausted.

**Fix:** Press Ctrl+C. Verify Ollama: `curl http://localhost:11434/api/tags`. Re-run the same agent — it starts over and overwrites the previous (empty/partial) output.

## 🔁 Agent repeats the same text over and over

**What happened:** Model lost its stop instruction — most common failure with large local LLM outputs.

**Fix:** Press Ctrl+C. Open the output file and delete the repeated section. To prevent it next time, open the agent's Python file and add `max_tokens=4096` to the `Task()` constructor and add "OUTPUT DISCIPLINE: stop after all sections are complete" to the agent's backstory. Full instructions: `templates/dev-team/agents/mobile/output_guard_patch.md`

## 📄 "No project context found"

**Fix:** Run `python agents/orchestrator/classify.py` first to create the context file.

## 📄 "Missing TIP" / "Missing PRD" / missing upstream artifact

**Fix:** Run agents in order. Check which one was skipped.

## 🤖 Output has `// TODO` or placeholder code

**Fix:** Open the agent's Python file, find the `Task(description=...)` block, and add: "No placeholders. No TODO comments. Every function must be complete and working." Re-run.

## 💥 Output is about the wrong project

**What happened:** Upstream artifact excerpt was too short, model lost context.

**Fix:** In the agent's `run_*` function, find `f.read()[:3000]` and increase it (try `[:6000]` or `[:8000]`). Re-run.

## 🔌 Ollama connection refused

sudo systemctl start ollama
curl http://localhost:11434/api/tags # verify

## 💾 Out of memory (Ollama crashes or machine freezes)

**Fix:** Don't run planning agents and build agents simultaneously — they load different models. Run the full planning phase, then the build phase. If the 32b model is too large, edit `TIER1_MODEL` in `config/.env` to use a smaller variant.

## 🔄 Stale rebase state (git am fails)

git am --abort # safe to run even on a clean repo
git am ~/Downloads/<patch>.patch # retry

## 🔄 How to start over

mkdir -p logs/archive
mv logs/PROJ-\*.json logs/archive/
python agents/orchestrator/classify.py # fresh start

## 🔄 How to re-run one agent

Just run it again. It overwrites its previous output and updates the project context. Downstream agents pick up the new version on their next run.

## ⚠️ SME group PermissionError

**What happened:** A dev-team agent tried to call the SME group directly — this is blocked by `validate_caller()`.

**Fix:** SME calls must go through an authorized caller: `pp_orchestrator`, `project_manager`, `strategy`, or `legal`. Restructure your flow accordingly.

# 9. Change Models, Tune Agents, Add New Ones

## Switch to a different LLM

Two lines in `config/.env` control the entire team:

TIER1\_MODEL=ollama/qwen3:32b # Planning agents (reasoners)
TIER2\_MODEL=ollama/qwen3-coder:30b # Build agents (coders)

To change: `ollama pull <model-name>` → update the env var → done. No code changes needed.

## Make an agent behave differently

| What to change | Where | Example |
| --- | --- | --- |
| Personality & expertise | `Agent(backstory="...")` in `build_*` function | Add "You always prefer serverless" to the Architect's backstory |
| What it produces | `Task(description="...")` in `run_*` function | Add section 10: REGULATORY REQUIREMENTS to the PRD template |
| How much upstream context it sees | `f.read()[:3000]` in `run_*` function | Change to `[:6000]` for more context |
| Stop looping | Backstory + Task constructor | Add "OUTPUT DISCIPLINE: stop after all sections complete" + `max_tokens=4096` |

## Add a new agent

1. Copy an existing agent file that's close in function (e.g. `backend_developer.py`)
2. Implement a `build_*` function returning a CrewAI `Agent` with role, goal, backstory, and LLM
3. Implement a `run_*` function: create a `Task`, run it in a `Crew`, save output, update context
4. Add a `__main__` block that loads the project context and finds upstream artifacts
5. Set `sys.path.insert(0, "/home/mfelkey/<team-name>")` at the top
6. Match the artifact naming pattern: `{PROJ}_{TYPE}.md`

**Pattern consistency is non-negotiable.** New agents must exactly match existing structural patterns: file layout, orchestrator shape, artifact naming, cross-team flag utilities. Read a comparable agent before writing a new one.

**RAG retrofit rule:** Retrofit agents (TAD-R, BIR-R, DIR-R, SRR-R, MTP-R, Reconciliation) process finalized documents and are deliberately excluded from RAG injection. Do not add `rag_inject` calls to these agents.

**Context injection over raw docs:** For multi-part agents (e.g. RN Architect), feed Part 1's actual output as context into Part 2 rather than the raw architecture document. This prevents re-generation loops.

**Undefined variable discipline:** Template variables like `{tad_content}` must be defined before use. The uniform fallback is `{prompt_context}` from the context manager.

# 10. Day-to-Day Operations

## What to watch in the terminal

| You see… | It means… |
| --- | --- |
| `🔍 Classifying project request...` | Orchestrator is thinking about your request |
| `📋 Product Manager generating PRD for: ...` | An agent started working |
| Streaming text (agent "typing") | LLM is generating — normal, let it run |
| `💾 PRD saved: output/PROJ-XXXXX_PRD.md` | Agent finished. Artifact is on disk. |
| `⏸️ CHECKPOINT: ...` | Your turn — review and APPROVE or REJECT |
| `📱 SMS sent via AT&T gateway...` | You've been notified |
| `⚠️ SMS failed: ...` | Check OUTLOOK\_ADDRESS / OUTLOOK\_PASSWORD in .env |

## Reviewing output efficiently

1. **Quick check:** The terminal prints the first 500 chars. Does it start with the right headings?
2. **Full review (at checkpoints):** Open the `.md` file. Skim section headings first.
3. **Red flag search:** `grep -ri "todo\|placeholder\|implement here\|TBD" output/`
4. **Check FLAGS.md:** Tracks known gaps. Always review before every checkpoint.

## Git workflow

Commit after each agent completes. Use the project ID in every message:

git add -A && git commit -m "PROJ-XXXXX: Product Manager → PRD complete"
# After full pipeline:
git tag PROJ-XXXXX-v1.0
# After retrofit:
git tag PROJ-XXXXX-v1.0-retrofit
# Export patch for local apply (avoids credential issues):
git format-patch HEAD~1 -o ~/Downloads/

## Multiple projects

The system runs one project at a time (Ollama serves one model at a time). To switch:

mkdir -p logs/archive && mv logs/PROJ-\*.json logs/archive/
python agents/orchestrator/classify.py # new project

## Updating the stack

| What | How |
| --- | --- |
| Ollama | `curl -fsSL https://ollama.com/install.sh | sh` — models are preserved |
| CrewAI | `pip install --upgrade "crewai[tools]"` |
| New LLM model | `ollama pull <model-name>` → update `config/.env` |
| ChromaDB | `pip install --upgrade chromadb` |

**Key pattern reminder:** Every agent reads upstream artifacts from the `artifacts` array in the project context JSON by `type` (e.g. `"PRD"`, `"TAD"`). When it finishes, it appends its own artifact to the same array. That's how agents find each other's work.

## Flow architecture — choosing the right entry point

Four layers sit between you and the agent hierarchy. Use the lightest one that fits:

| Layer | File | Use when |
| --- | --- | --- |
| **0 — Full intake** | `flows/intake_flow.py` | Starting a brand new project from scratch |
| **1 — Team intake** | `flows/<team>_intake_flow.py` | Post-initiation task for a specific team — plain-English brief, orchestrator picks mode |
| **2 — Team flow** | `templates/<team>/flows/<team>_flow.py` | You know exactly which mode you want |
| **3 — Agent direct** | `templates/<team>/flows/<team>_agent_flow.py` | Bypass the orchestrator entirely — one agent, one task |

Context resolution is identical across all layers: `--project` → `--context-file` → `--context` → none.

---

## Part III — Reference

Detailed reference material. You don't need to read this to use the system — it's here when you need to look something up.

# Appendix A — Full Agent Roster

| Layer | Agent | File (relative to team root) | Tier | Produces |
| --- | --- | --- | --- | --- |
| PP Core | PP Orchestrator | `agents/orchestrator/orchestrator.py` | T1 | Project context, PRD, team routing |
| Project Manager | `agents/project_manager/project_manager.py` | T1 | Sprint plan, status reports, blocker escalation |
| Dev — Plan | Product Manager | `agents/dev/strategy/product_manager.py` | T1 | PRD |
| Business Analyst | `agents/dev/strategy/business_analyst.py` | T1 | BAD |
| Scrum Master | `agents/dev/strategy/scrum_master.py` | T1 | Sprint Plan |
| Technical Architect | `agents/dev/strategy/technical_architect.py` | T1 | TAD |
| Security Reviewer | `agents/dev/strategy/security_reviewer.py` | T1 | SRR 🟢/🟡/🔴 |
| UX/UI Designer | `agents/dev/strategy/ux_designer.py` | T1 | UXD |
| UX Content Guide | `agents/dev/strategy/ux_content_guide.py` | T1 | UI Content Guide |
| Dev — Build | Senior Developer | `agents/dev/build/senior_developer.py` | T2 | TIP |
| Backend Developer | `agents/dev/build/backend_developer.py` | T2 | BIR |
| Frontend Developer | `agents/dev/build/frontend_developer.py` | T2 | FIR |
| Database Administrator | `agents/dev/build/database_admin.py` | T2 | DBAR |
| DevOps Engineer | `agents/dev/build/devops_engineer.py` | T2 | DIR |
| Dev — Quality | QA Lead | `agents/dev/quality/qa_lead.py` | T1 | MTP |
| Test Automation Engineer | `agents/dev/quality/test_automation_engineer.py` | T2 | TAR |
| Dev — Docs | DevEx Writer | `agents/docs/devex_writer.py` | T1 | API docs, README, developer guides |
| Technical Writer | `agents/docs/technical_writer.py` | T1 | User guides, runbooks, release notes |
| Mobile | Mobile UX Designer | `agents/mobile/ux/mobile_ux_designer.py` | T1 | MUXD |
| iOS Developer | `agents/mobile/ios/ios_developer.py` | T2 | IIR + Swift |
| Android Developer | `agents/mobile/android/android_developer.py` | T2 | AIR + Kotlin |
| RN Architect (Pt1+2) | `agents/mobile/rn/react_native_architect_part*.py` | T2 | RNAD P1, P2 |
| RN Developer | `agents/mobile/rn/react_native_developer.py` | T2 | RN Guide |
| Mobile DevOps | `agents/mobile/devops/mobile_devops_engineer.py` | T2 | MDIR |
| Mobile QA Specialist | `agents/mobile/qa/mobile_qa_specialist.py` | T1 | Mobile test suite |
| Retrofit | TAD Retrofit | `agents/dev/build/tad_retrofit.py` | T2 | TAD-R |
| BIR Retrofit | `agents/dev/build/backend_developer_retrofit.py` | T2 | BIR-R |
| DIR Retrofit | `agents/dev/build/devops_engineer_retrofit.py` | T2 | DIR-R |
| SRR Retrofit | `agents/dev/build/srr_retrofit.py` | T2 | SRR-R |
| MTP Retrofit | `agents/dev/quality/qa_lead_retrofit.py` | T2 | MTP-R |
| Reconciliation | `agents/dev/reconciliation.py` | T2 | Gap report |
| Finance Group | Finance Orchestrator | `agents/finance/finance_orchestrator.py` | T1 | FSP |
| Cost Analyst | `agents/finance/cost_analyst.py` | T1 | CEA |
| ROI Analyst | `agents/finance/roi_analyst.py` | T1 | ROI |
| Infrastructure Finance Modeler | `agents/finance/infra_finance_modeler.py` | T1 | ICM |
| Billing Architect | `agents/finance/billing_architect.py` | T1 | BPS (conditional) |
| Pricing Specialist | `agents/finance/pricing_specialist.py` | T1 | PRI (conditional) |
| Financial Statements Modeler | `agents/finance/financial_statements.py` | T1 | FSR |
| Strategic Corp Finance Specialist | `agents/finance/strategic_corp_finance.py` | T1 | SCF |
| SME Group | SME Orchestrator | `agents/sme/sme_orchestrator.py` | T1 | Domain Intelligence Brief |
| Sports Betting Expert | `agents/sme/sports_betting_expert.py` | T1 | Domain assessment |
| World Football Expert | `agents/sme/world_football_expert.py` | T1 | Domain assessment |
| NBA/NCAA Basketball Expert | `agents/sme/nba_ncaa_basketball_expert.py` | T1 | Domain assessment |
| NFL/NCAA Football Expert | `agents/sme/nfl_ncaa_football_expert.py` | T1 | Domain assessment |
| MLB Expert | `agents/sme/mlb_expert.py` | T1 | Domain assessment |
| NHL/NCAA Hockey Expert | `agents/sme/nhl_ncaa_hockey_expert.py` | T1 | Domain assessment |
| MMA Expert | `agents/sme/mma_expert.py` | T1 | Domain assessment |
| Tennis Expert | `agents/sme/tennis_expert.py` | T1 | Domain assessment |
| World Rugby Expert | `agents/sme/world_rugby_expert.py` | T1 | Domain assessment |
| Cricket Expert | `agents/sme/cricket_expert.py` | T1 | Domain assessment |
| WNBA/NCAA Women's Basketball Expert | `agents/sme/wnba_ncaa_womens_basketball_expert.py` | T1 | Domain assessment |
| Thoroughbred Horse Racing Expert | `agents/sme/thoroughbred_horse_racing_expert.py` | T1 | Domain assessment |
| Harness Racing Expert | `agents/sme/harness_racing_expert.py` | T1 | Domain assessment |
| Men's Boxing Expert | `agents/sme/mens_boxing_expert.py` | T1 | Domain assessment |
| PGA Expert | `agents/sme/pga_expert.py` | T1 | Domain assessment |
| LPGA Expert | `agents/sme/lpga_expert.py` | T1 | Domain assessment |
| HR Team | HR Orchestrator | `agents/hr/orchestrator/orchestrator.py` | T1 | Sequences HR crew |
| Recruiting Specialist | `agents/hr/recruiting/recruiting_agent.py` | T1 | JD, sourcing plan, interview guide |
| Onboarding Specialist | `agents/hr/onboarding/onboarding_agent.py` | T1 | Onboarding plan |
| Performance & Comp Specialist | `agents/hr/performance_comp/performance_comp_agent.py` | T1 | Review framework, comp analysis |
| Policy & Compliance Specialist | `agents/hr/policy_compliance/policy_compliance_agent.py` | T1 | Policy docs, compliance audit |
| Culture & Engagement Specialist | `agents/hr/culture_engagement/culture_engagement_agent.py` | T1 | Engagement plan |
| Benefits Specialist | `agents/hr/benefits/benefits_agent.py` | T1 | Benefits analysis |
| Video Team | Video Orchestrator | `agents/orchestrator/orchestrator.py` | T1 | Sequences video crew, selects mode from brief |
| Script Writer | `agents/script/script_writer.py` | T1 | Video scripts — all formats |
| Visual Director | `agents/visual/visual_director.py` | T1 | Visual direction briefs, shot lists |
| Audio Producer | `agents/audio/audio_producer.py` | T1 | Music briefs, SFX notes |
| Avatar Producer | `agents/avatar/avatar_producer.py` | T1 | Avatar/spokesperson direction briefs |
| Tool Intelligence Analyst | `agents/tool_intelligence/tool_analyst.py` | T1 | Tool selection report — VIDEO\_TOOL\_SELECTION gate |
| API Engineer | `agents/production/api_engineer.py` | T1 | Production pipeline config |
| Compliance Reviewer | `agents/compliance/compliance_reviewer.py` | T1 | Compliance clearance — VIDEO\_FINAL gate |

# Appendix B — Artifact Registry

| Code | Full Name | Produced By | Consumed By | File Pattern |
| --- | --- | --- | --- | --- |
| PRD | Product Requirements Document | Product Manager | BA, SM, TA, SR, UX, SD, QA | `{PROJ}_PRD.md` |
| BAD | Business Analysis Document | Business Analyst | SM, TA, UX | `{PROJ}_BAD.md` |
| Sprint Plan | Sprint Planning Document | Scrum Master | TA | `{PROJ}_SPRINT.md` |
| TAD | Technical Architecture Document | Technical Architect | SR, SD, BD, DevOps, DBA, Finance | `{PROJ}_TAD.md` |
| SRR | Security Review Report | Security Reviewer | UX, DevOps, DBA, Mobile DevOps | `{PROJ}_SRR.md` |
| UXD | User Experience Document | UX/UI Designer | Content Guide, SD, FD, QA | `{PROJ}_UXD.md` |
| UI Content Guide | UI Content Guide | UX Content Guide | FD | `{PROJ}_CONTENT.md` |
| TIP | Technical Implementation Plan | Senior Developer | BD, FD, DevOps, TAE, Mobile DevOps | `{PROJ}_TIP.md` |
| BIR | Backend Implementation Report | Backend Developer | FD, DBA, QA, TAE | `{PROJ}_BIR.md` |
| FIR | Frontend Implementation Report | Frontend Developer | QA, TAE | `{PROJ}_FIR.md` |
| DBAR | Database Administration Report | Database Administrator | DevOps | `{PROJ}_DBAR.md` |
| DIR | DevOps Implementation Report | DevOps Engineer | QA, TAE | `{PROJ}_DIR.md` |
| MTP | Master Test Plan | QA Lead | TAE | `{PROJ}_MTP.md` |
| TAR | Test Automation Report | Test Automation Engineer | (Terminal) | `{PROJ}_TAR.md` |
| MUXD | Mobile UX Document | Mobile UX Designer | iOS, Android, RN, Mobile QA | `{PROJ}_MUXD.md` |
| IIR | iOS Implementation Report | iOS Developer | Mobile DevOps, Mobile QA | `{PROJ}_IIR.md` |
| AIR | Android Implementation Report | Android Developer | Mobile DevOps, Mobile QA | `{PROJ}_AIR.md` |
| RNAD | React Native Architecture Doc | RN Architect | RN Developer | `{PROJ}_RNAD_P1.md`, `_P2.md` |
| RN Guide | RN Implementation Guide | RN Developer | Mobile DevOps, Mobile QA | `rn_guide_complete_{ts}.md` |
| MDIR | Mobile DevOps Report | Mobile DevOps Engineer | Mobile QA | `{PROJ}_MDIR.md` |
| CEA | Cost Estimates & Budget | Cost Analyst | Finance Orchestrator | `{PROJ}_CEA.md` |
| ROI | ROI & Business Case Analysis | ROI Analyst | Finance Orchestrator | `{PROJ}_ROI.md` |
| ICM | Infrastructure Cost Model | Infrastructure Finance Modeler | Finance Orchestrator | `{PROJ}_ICM.md` |
| BPS | Billing & Payment Feature Spec | Billing Architect | Finance Orchestrator | `{PROJ}_BPS.md` |
| PRI | Pricing Strategy & Model | Pricing Specialist | Finance Orchestrator | `{PROJ}_PRI.md` |
| FSR | Financial Statements Report | Financial Statements Modeler | Finance Orchestrator | `{PROJ}_FSR.md` |
| SCF | Strategic Corp Finance Report | Strategic Corp Finance Specialist | Finance Orchestrator | `{PROJ}_SCF.md` |
| FSP | Finance Summary Package | Finance Orchestrator | Human (CP-4.5), Build phase | `{PROJ}_FSP.md` |
| \*-R | Retrofit / revised versions | Retrofit agents | Reconciliation | `{PROJ}_{TYPE}_R.md` |

# Appendix C — Context Object Schema

The project context is the JSON file (`logs/PROJ-{id}.json`) that holds the entire state of a project. Every agent reads and writes to it.

### Top-level fields

| Field | Type | What it is |
| --- | --- | --- |
| `project_id` | string | Unique ID — format: `PROJ-{8-char-hex}` |
| `created_at` | ISO datetime | When the project was created |
| `status` | string | `INITIATED` → `CLASSIFIED` → `ROUTED_TO_DEV` → … → `COMPLETE` |
| `classification` | string | `DEV`, `DS`, or `JOINT` |
| `original_request` | string | Your original project description, word for word |
| `structured_spec` | object | Structured version: title, deliverables, complexity, success criteria |
| `assigned_crew` | string | Which crew is working |
| `artifacts` | array | Every document produced — name, type, path, timestamp, agent |
| `checkpoints` | array | Every checkpoint — name, timestamp, APPROVED or REJECTED |
| `handoffs` | array | Inter-crew handoff records (JOINT projects) |
| `audit_log` | array | Every event in order with timestamps |

### JSON Schema (for validation)

```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ProjectContext",
  "type": "object",
  "required": ["project_id","created_at","status","classification",
               "original_request","structured_spec","checkpoints",
               "handoffs","artifacts","audit_log"],
  "properties": {
    "project_id":       { "type": "string", "pattern": "^PROJ-[A-F0-9]{8}$" },
    "created_at":       { "type": "string", "format": "date-time" },
    "status":           { "type": "string" },
    "classification":   { "type": "string", "enum": ["DEV","DS","JOINT","UNKNOWN"] },
    "original_request": { "type": "string" },
    "structured_spec": {
      "type": "object",
      "properties": {
        "title":                { "type": "string" },
        "description":          { "type": "string" },
        "business_goal":        { "type": "string" },
        "deliverables":         { "type": "array", "items": { "type": "string" } },
        "success_criteria":     { "type": "array", "items": { "type": "string" } },
        "estimated_complexity": { "type": "string", "enum": ["LOW","MEDIUM","HIGH"] },
        "data_required":        { "type": "boolean" },
        "primary_crew":         { "type": "string", "enum": ["DEV","DS","JOINT"] },
        "handoff_direction":    { "type": ["string","null"] }
      }
    },
    "assigned_crew": { "type": ["string","null"] },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name":       { "type": "string" },
          "type":       { "type": "string" },
          "path":       { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" },
          "agent":      { "type": "string" }
        }
      }
    },
    "checkpoints": { "type": "array" },
    "handoffs":    { "type": "array" },
    "audit_log": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "timestamp": { "type": "string", "format": "date-time" },
          "event":     { "type": "string" },
          "detail":    { "type": "string" }
        }
      }
    }
  }
}
```

# Appendix D — Conflict Resolution & Escalation Matrix

## Who wins when agents disagree?

1. **You** — always the final authority
2. **Security Reviewer** — overrides architecture and implementation on security matters
3. **Technical Architect** — overrides implementation decisions on architecture matters
4. **Senior Developer (TIP)** — overrides build agents on implementation approach
5. **Database Administrator** — overrides Backend Developer on schema/query matters
6. **QA Lead** — can block release but cannot override architecture or security

## What gets escalated to you automatically

| Situation | What happens |
| --- | --- |
| Any checkpoint reached | SMS + email, system waits for APPROVE/REJECT |
| Security rated 🔴 RED | Development blocked until you decide |
| Classification fails | You manually classify or rephrase |
| Handoff validation fails | Missing artifacts — you review completeness |
| Agent produces no output | Likely timeout — you investigate |
| Budget/vendor/policy decisions flagged | Agent can't proceed without your call |
| Conflicting upstream artifacts | Agent documents conflict, system halts at next checkpoint |
| Retrofit lost critical content | Reconciliation report shows gaps, you decide resolution |
| CRITICAL blocker (any team) | Project Manager escalates immediately — no 48-hour window |
| HR action affecting a person | HR gate fires, no automated action taken |
| Multi-SME synthesis complete | HITL review gate fires on Domain Intelligence Brief |

## What agents resolve on their own

| Situation | Resolution |
| --- | --- |
| Minor formatting issues | Cleaned automatically |
| JSON wrapped in markdown fences | Stripped before parsing |
| DBA finds missing indexes | Adds them in DBAR — no re-run needed |
| Retrofit removes provider-specific content | Expected — documented in reconciliation report |
| Non-blocking ambiguity in upstream doc | Flagged in output with `[ASSUMPTION]` / `[VERIFY]` tags, continues, you see it at checkpoint |
| Project Manager blocker (non-critical) | PM resolves at Team Lead level within 48 hours before escalating |

# Appendix E — Quality Standards

### Code

| Rule | Standard |
| --- | --- |
| No placeholder code | Every function complete. No `// TODO`, no `# implement here`. |
| Type safety | TypeScript for frontend/RN. Python type hints on all function signatures. |
| Error handling | Every API call and file operation has explicit error handling. |
| Security | All SRR CRITICAL/HIGH findings addressed. Secrets never hardcoded. |
| Accessibility | WCAG 2.1 AA. VoiceOver/TalkBack tested. Every interactive element labeled. |
| Deployment agnostic | No cloud provider names in app code. `DEPLOY_TARGET` env var controls provider modules. |

### Documents

| Rule | Standard |
| --- | --- |
| Complete | Every section from the task description must be present. |
| Actionable | A developer can execute from the report without asking further questions. |
| Traceable | Every decision traces back to PRD, SRR, or UXD. |
| Consistent | Same terminology and naming across all artifacts. |
| Tagged uncertainty | DS and SME outputs use `[ASSUMPTION]` and `[VERIFY]` tags where data is inferred. |

### Tests

| Type | Target | Tools |
| --- | --- | --- |
| Unit | ≥80% coverage on business logic | Jest, XCTest, JUnit5 |
| Component | Every UI component has a render test | React Testing Library, Compose UI Testing |
| API | Positive + negative cases per endpoint | Supertest |
| E2E | Every critical user journey | Playwright (web), Detox (mobile) |
| Accessibility | No CRITICAL/SERIOUS axe violations | axe-core |
| Performance | Baseline established, no >10% regression | k6 |

### Finance outputs

| Rule | Standard |
| --- | --- |
| Rating required | Every artifact opens with `FINANCE RATING: 🟢/🟡/🔴` |
| Open questions | Every artifact ends with an `OPEN QUESTIONS` section |
| Advisory only | Finance Group never auto-blocks the pipeline |
| Scenario coverage | Cost and ROI analyses include LOW / MID / HIGH scenarios |

### SME outputs

| Rule | Standard |
| --- | --- |
| Domain assessment | Every output opens with `DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW` |
| Cross-team flags | Every output ends with `CROSS-TEAM FLAGS` |
| Open questions | Every output ends with `OPEN QUESTIONS` |
| Multi-SME HITL | All synthesised multi-SME outputs require human review before use |

# Appendix F — Model Tier Reference

| Tier | Current Model | Env Var | Purpose | Agents |
| --- | --- | --- | --- | --- |
| **Tier 1** | `ollama/qwen3:32b` | `TIER1_MODEL` | Reasoning, planning, analysis | PP Orchestrator, Project Manager, all Team Leads, Product Manager, Business Analyst, Scrum Master, Technical Architect, Security Reviewer, UX Designer, UX Content Guide, QA Lead, Mobile UX Designer, Mobile QA, all Finance agents, all SME agents, all HR agents |
| **Tier 2** | `ollama/qwen3-coder:30b` | `TIER2_MODEL` | Code generation, implementation | Senior Developer, Backend Developer, Frontend Developer, DBA, DevOps Engineer, Test Automation Engineer, iOS Developer, Android Developer, RN Architect, RN Developer, Mobile DevOps Engineer, all Retrofit agents, Reconciliation |
| **Embed** | `nomic-embed-text` | `EMBED_MODEL` | Vector embeddings for ChromaDB RAG memory | All agents (via ChromaDB + Knowledge Curator) |

All agents read model selection from env vars — model names are never hardcoded in agent files. To upgrade the entire system to a new model, update the env var and pull the new model with Ollama. No code changes required.

Protean Pursuits — Agent System Operating Manual — Version 3.1 — April 2026
Grounded in commit `fdaabc3` · github.com/mfelkey/protean-pursuits