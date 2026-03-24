# PARALLAX edge
## Product Requirements Document
**Version 1.9 | Launch Release | Confidential**

**1 change: PDB-02 closed. Supersedes PRD v1.8.**

| Field | Detail |
|---|---|
| Product | Parallax — Sports Betting Analytics Platform |
| Version | 1.9 — PDB-02 closed: StatsBomb + Understat accepted as WC2026 xG source. Soccer model training authorized. |
| Previous Version | 1.8 — Launch milestone resequencing + June 11 full-product launch + PDB-01/PDB-02 escalation |
| Date | March 2026 |
| Status | ACTIVE — Supersedes v1.0, v1.1, v1.2, v1.3, v1.4, v1.5, v1.6, v1.7, v1.8 |
| **Phase 1A — Primary Launch (Full Product)** | **June 11, 2026 — FIFA World Cup 2026 opening match. Full product live: auth, odds, model output, bet tracker, alerts, track record. Soccer scope: WC2026 only.** |
| **Phase 1B — Soccer Expansion** | **August 2026 — EPL season open + UEFA Champions League group stage added to soccer model.** |
| **Phase 1C — NFL** | **September 4, 2026 — NFL regular season open.** |
| **Phase 1D — NBA** | **October 2026 — NBA regular season open.** |
| **Phase 2 Sports (Season-Gated, Post-Phase-1D)** | **MLB, NHL, Tennis (ATP/WTA + Grand Slams), NCAA Football (FBS), NCAA Men's Basketball (D1), NCAA Women's Basketball (March Madness only), World Rugby (Six Nations, Rugby Championship, Rugby World Cup, URC, Premiership, Top 14)** |
| Primary Audience | Development Agent Team, Data Science Agent Team |
| Methodology | Test-Driven Development (TDD) |
| New in v1.9 | CHG-51 — see change log below |

---

# Change Log — v1.8 to v1.9

One change. PDB-02 closure — soccer model training now authorized.

| Change ID | Section | Summary | Priority |
|---|---|---|---|
| CHG-51 | 0.1 / 7.1 / 11.1 | **PDB-02 closed. StatsBomb Open Data accepted as primary WC2026 xG source. Understat club proxy accepted as gap-fill.** Decision date: 2026-03-24. Product Lead approval: confirmed. Step 2.5 joint DS+Dev Section 7.1 review: complete — no schema changes required. xg_source_method field already present in inputs_snapshot soccer keys: 'direct' (StatsBomb) and 'club_proxy' (Understat gap-fill) values confirmed. PDB-02 blocker box updated to CLOSED. Soccer model training for WC2026 is now authorized to begin. DS team must credit StatsBomb in all published methodology documentation. Ingestion path: statsbombpy Python client (pip install statsbombpy). | Critical |

---

# Change Log — v1.7 to v1.8

Six changes applied following launch target confirmation (June 11, 2026 — full product), explicit sport phase sequencing, PDB-01/PDB-02 escalation, affiliate timeline correction, and user_bets schema improvement. All changes are additive or corrective — no existing feature specifications, API contracts, or model interface contract modified.

| Change ID | Section | Summary | Priority |
|---|---|---|---|
| CHG-45 | Header / 1.2 / 2.1 / 11 | **Launch milestone resequencing.** June 11, 2026 is now the primary full-product launch date (Phase 1A). EPL + UCL added in Phase 1B (August 2026). NFL added Phase 1C (September 4, 2026). NBA added Phase 1D (October 2026). Previous "August 2026 soft launch / September 2026 NFL open" header language replaced. The term "Phase 1 (Launch)" in Section 1.2 scope table now refers to the June 11 full-product launch only. WC2026-only soccer scope at Phase 1A is explicit. Section 2.1 business goals timeframes updated to reference "post-Phase-1A launch" instead of generic "post-launch." Section 11 checklist split into two tiers: June 11 gate and post-Phase-1A expansion items. | Critical |

| CHG-46 | 0.1 / 11.1 | **PDB-01 and PDB-02 escalated to critically overdue.** With June 11 as the confirmed launch date, 80 days remain at time of writing. Both blockers were originally gated on "2 weeks from PRD v1.2 sign-off" — that deadline has passed. PDB-01 (Open-Meteo licensing) and PDB-02 (WC2026 xG source) must be resolved immediately. New language added to both blocker boxes: CRITICALLY OVERDUE — RESOLVE THIS WEEK. Escalation path documented. Soccer model training cannot begin until PDB-02 is closed. Weather pipeline cannot be designed until PDB-01 is closed. With 80 days to June 11, neither can wait. | Critical |

| CHG-47 | 1.2 | **Phase 1 scope table updated to reflect explicit sport phasing.** Phase 1 column split into Phase 1A (June 11 — WC2026 soccer only), Phase 1B (EPL + UCL), Phase 1C (NFL), Phase 1D (NBA). Previous "Phase 1 (Launch)" column covered all four simultaneously — this was always incorrect given sequential season calendars. The scope table now reflects the confirmed deployment sequence. | Critical |

| CHG-48 | 11.3 | **Affiliate agreement requirement split between June 11 gate and post-launch target.** Previous checklist required "minimum 3 sportsbooks" as a pre-launch Critical item. Confirmed: no affiliate agreements will be in place at June 11 launch. Updated: affiliate agreements are a post-Phase-1A target (High priority, target within 60 days of launch). June 11 checklist item updated to: "Affiliate disclosure infrastructure in place (code, disclosure label, footer) — zero active partners required at launch." Rationale: affiliate revenue is not on the critical path for launch; trust and track record are. Premature affiliate deals before the model has a live track record weaken negotiating position. | High |

| CHG-49 | 4.1.15 | **user_bets table: match_table discriminator column added.** The existing schema routed tennis bet lookups via sport_slug at the application layer, with no schema-level indicator of which table game_id references. This is a silent footgun for reporting queries joining user_bets to match detail. New column added: match_table VARCHAR(30) NOT NULL DEFAULT 'games' — values: 'games' \| 'tennis_matches'. Application layer must populate this field at bet creation. Reporting queries must use match_table to route joins. Great Expectations check added: match_table must equal 'tennis_matches' for all rows where sport_slug = 'tennis'. | High |

| CHG-50 | 10.2 / 14.1 | **Data license audit: Phase 3 gate item given a recommended start date.** Section 10.2 risk register note updated to flag that legal review lead times for data licensing opinions are typically 3–6 months. Recommended start: no later than 60 days post-Phase-1A launch (approximately August 2026). Section 14.1 standing convention note updated accordingly. This is not a launch blocker — it is a Phase 3 planning gate that requires sufficient lead time to avoid delaying commercial API development unnecessarily. | Medium |

---

# Change Log — v1.6 to v1.7

One change. Additive only — no modifications to existing sections, schemas, API contracts, or model interface contract.

| Change ID | Section | Summary | Priority |
|---|---|---|---|
| CHG-44 | 1.2, 10.2, 11.3, 14 (new) | Phase 3 commercial API licensing specification added as Section 14. Defines what can and cannot be sold via a commercial API, establishes the data license audit as a hard pre-build blocker, specifies the two permissible product boundaries (model outputs only vs enriched outputs), outlines the technical architecture differences from the consumer-facing API, and documents the legal risks requiring resolution before any commercial API build begins. Section 1.2 Revenue row updated to move API licensing from Phase 2 to Phase 3 (it was already listed under Phase 3+ in the scope table — this corrects the Revenue row which incorrectly listed it as Phase 2). Section 10.2 risk register updated with data re-sale license violation risk. Section 11.3 pre-launch checklist updated with Phase 3 planning item for legal workstream. | High |

---

# Change Log — v1.5 to v1.6

Fourteen changes applied following sport expansion decisions, schema gap remediation, and i18n foundation review. Changes span scope, schema, model interface contract, polling schedule, dependencies, risk register, and pre-launch checklist. No changes to existing Phase 1 feature specifications, API rate limits, or management dashboard.

| Change ID | Section | Summary | Priority |
|---|---|---|---|
| CHG-30 | Header / 1.2 | Phase 2 sport scope confirmed. Phasing is per-sport based on season calendar rather than a single simultaneous Phase 2 launch. Sports and competitions confirmed: MLB (season calendar gate), NHL (season calendar gate), Tennis — ATP Tour + WTA Tour + Four Grand Slams (season calendar gate), NCAA Football — FBS only (Power 4 + Group of 5, 133 programs; FCS deferred to Phase 3), NCAA Men's Basketball — D1 full season including March Madness, NCAA Women's Basketball — March Madness (NCAA Tournament) only (full season deferred to Phase 3 — betting market and data availability insufficient for full-season coverage), World Rugby — Six Nations, Rugby Championship, Rugby World Cup, URC, Premiership Rugby, Top 14. NCAA player props: game-level markets only (spread, moneyline, totals) for all NCAA sports; player prop scope flagged for legal review before any prop expansion — see Section 1.2 note. Header table updated. Section 1.2 updated accordingly. | Critical |World Cup 2026

| CHG-31 | 4.1 (new 4.1.13, 4.1.14) | Two new tables added for Tennis: `tennis_matches` (Section 4.1.13 — player-based match entity, separate from `games` table; home/away team ID model does not apply to individual sport) and `player_ratings` (Section 4.1.14 — surface-aware player Elo rating store). Tennis is modelled at player level, not team level. | Critical |

| CHG-32 | 4.1.4 | `games.week` column documented as nullable for non-NFL sports. Comment added: NULL for NBA, MLB, NHL, tennis (uses `tennis_matches`), and soccer. For NCAA Football, `week` maps to the college football week number. For Rugby, `week` maps to the round number within the competition phase. | High |

| CHG-33 | 4.1.5 | `odds.market_type` enum extended for Phase 2 sports. Added: `'run_line'` (MLB), `'puck_line'` (NHL), `'first_5_innings'` (MLB), `'period'` (NHL period betting), `'set_winner'` (tennis), `'match_tiebreak'` (tennis), `'try_scorer'` (rugby). Note added: `run_line` and `puck_line` are sport-specific aliases for spread betting — treat as `spread` in model output calculations but preserve native label for display. | High |

| CHG-34 | 4.1.4 | Neutral-site venue weather gap resolved. New field added to `games`: `neutral_venue_lat DECIMAL(9,6)` and `neutral_venue_lng DECIMAL(9,6)`. When `is_neutral_site = true` AND `venue_roof = 'open'`, weather pipeline must use `neutral_venue_lat/lng` for Open-Meteo query rather than either team's `venue_lat/lng`. Covers: WC2026 neutral venues, UCL finals, Rugby World Cup venues, NCAA bowl games and tournament sites. Dev Team to seed neutral venue coordinates for all known scheduled neutral-site outdoor games before pipeline build. | High |

| CHG-35 | 7.1 | `inputs_snapshot` keys defined for Phase 2 sports. Added MLB-only keys, NHL-only keys, Tennis-only keys (match-level, not game-level), Rugby-only keys, and NCAA Football / NCAA Men's Basketball shared keys (identical to NFL and NBA respectively with addition of `is_conference_game`). Full specification in Section 7.1. | Critical |

| CHG-36 | 7.2 | Data quality gate rules defined for Phase 2 sport-specific critical inputs. MLB: if `is_starting_pitcher_confirmed = false`, output BLOCKED entirely (not flagged — pitcher is the dominant model variable; unconfirmed pitcher output has no brand-consistent signal value). NHL: if `is_starting_goalie_confirmed = false`, `data_quality_score` capped at 0.70 (FLAG threshold floor — output published with warning but not blocked). Tennis: if player ranking or surface win rate data is unavailable for either player, `data_quality_score` capped at 0.75. Rugby: no sport-specific cap beyond standard gate. | Critical |

| CHG-37 | 7.3 | Polling schedule extended for all Phase 2 sports. NCAA Football and NCAA Men's Basketball use same polling pattern as NFL and NBA respectively. Tennis uses match-day polling schedule (pre-match injury/withdrawal). Rugby uses match-week schedule consistent with soccer. MLB and NHL rows carried forward from API Requirements v0.5 deferred documentation. Full schedule in Section 7.3. | High |

| CHG-38 | 8.5 | i18n string externalization mandated from day one. All user-facing strings must be stored in locale files (`/locales/en.json`) using Next.js i18n key pattern, even though English is the only shipped locale at launch. No hardcoded strings permitted in frontend components. This is a TDD-enforceable NFR: CI must fail if string literals are detected in UI components outside locale files. First target non-English locale: French (Roland Garros / Six Nations / French soccer market). No launch date set — triggered by Year 1 international user data. | High |

| CHG-39 | 8.5 | Responsible gambling messaging extended for international markets. UK (GamStop / BeGambleAware), Australia (Gambling Help Online), and France (ANJ) each have distinct mandated messaging content and display requirements. `country_code` on the `users` table is the routing field. Dev Team to implement locale-aware responsible gambling message component with per-country content at launch (English content for all markets at v1 — translated content in future locale releases). | High |

| CHG-40 | 9.1 | Dashboard sport tabs updated. Current: All \| NFL \| NBA \| Soccer. Updated: All \| NFL \| NBA \| Soccer \| NCAA \| Tennis \| Rugby (tabs for Phase 2 sports hidden until that sport's data is live — not visible at Phase 1 launch). | Low |

| CHG-41 | 10.1 | External dependencies table updated for Phase 2 sports. Tennis (Open Era historical data / Jeff Sackmann GitHub dataset), NCAA Football (cfbfastR / collegefootballdata.com API), NCAA Men's Basketball (cbbdata / Sports Reference), World Rugby (ESPN Stats & Info / World Rugby API candidate) rows added. | High |

| CHG-42 | 10.2 | Risk register updated. New risks added: Tennis player data model requires separate `tennis_matches` table — integration risk if Dev and DS teams assume shared `games` schema; NCAA player prop regulatory restriction by state — game-level markets only for NCAA at launch; prop market expansion requires legal review across all 38+ US states with legal sports betting before implementation; World Rugby odds liquidity thinner than major US sports — The Odds API rugby coverage to be verified before Phase 2 contract extension. | High |

| CHG-43 | 11.1, 11.2, 11.3 | Pre-launch checklist updated. Phase 2 planning items added to Section 11.1 (data and model): one item per new Phase 2 sport confirming training data source and blocker status. Section 11.2 (product and engineering): neutral venue coordinates seeded for all known outdoor neutral-site games. Section 11.3 (business and legal): NCAA player prop legal review item added; Rugby odds coverage verification with The Odds API added; i18n string externalization CI check confirmed. | High |

---

# Change Log — v1.4 to v1.5

Two changes applied following Management Dashboard specification. All changes are additive — no existing sections, schemas, API contracts, or model interface contract modified.

| Change ID | Section | Summary | Priority |
|---|---|---|---|
| CHG-28 | 8.7 (new) | Section 8.7 Observability & Monitoring added to Non-Functional Requirements. Specifies instrumentation requirements for uptime history tracking (90-day per-service, Statuspage.io / Grafana probe source, amber/red thresholds), rate limit monitoring (Redis counters per endpoint group per tier, HTTP 429 event log, global ceiling utilisation), and Grafana alerting configuration for all critical monitors. This is a technical NFR — it specifies what must be instrumented and alertable, not how it is displayed. Dev Team owner. | High |

| CHG-29 | 13 (new), 11.2 | Section 13 Management Dashboard added as a standalone internal tooling specification. Defines the internal Product Lead–only dashboard as a required pre-launch deliverable: access control, seven display panels with data sources and alert thresholds (KPIs, model performance, infrastructure status, uptime history, rate limit monitoring, financial detail, affiliates), and a full wireframe. Section 11.2 pre-launch checklist updated with two new High-priority items. | High |

---

# Change Log — v1.3 to v1.4

Seven changes applied following Champions League scope lock decision. All changes relate exclusively to the addition of UEFA Champions League as committed launch scope. No changes to feature specifications, data schemas, API contracts, or model interface contract in this version, except where UCL is additive to existing soccer scope references.

| Change ID | Section | Summary | Priority |
|---|---|---|---|
| CHG-22 | Header / 1.2 | Champions League promoted from stretch goal to committed launch scope. Header table Soccer Launch Competitions field updated. Section 1.2 Launch Scope Summary table updated: UCL moved from Out of Scope to In Scope. | Critical |

| CHG-23 | 0.1 | PDB-03 added: UCL historical xG data source — hard blocker on UCL model training. Evaluation approach left open-ended (no prescribed vendor order). Owner: DS Team. | Critical |

| CHG-24 | 7.3 | All injury and referee polling schedule rows previously referencing "EPL or WC2026" updated to "EPL, WC2026, or Champions League." | High |

| CHG-25 | 10.1 | External Dependencies table: UCL xG training data source added as a dependency row alongside EPL and WC2026 soccer entries. | High |

| CHG-26 | 11.1 | Pre-Launch Checklist: UCL historical data ingestion checklist item added, consistent with EPL and WC2026 entries. Gated on PDB-03. | High |

| CHG-27 | 11.3 | Pre-Launch Checklist: API-Football scope confirmation item updated to explicitly name Champions League alongside EPL and WC2026. | High |

---

# 0. Pre-Development Requirements

> **READ THIS SECTION FIRST — BOTH TEAMS**
> This section defines every decision, confirmation, and validation that must be completed before either agent team begins implementation work. These are not suggestions. They are gates. Red boxes = hard blockers. Do not build the affected component until resolved. Amber boxes = required decisions with prescribed direction. Follow the stated direction. Green boxes = standing conventions. Apply for the lifetime of both documents. Each item maps to a detailed entry in its relevant section and to Section 11 pre-launch checklist.

## 0.1 Hard Blockers — Do Not Build Until Resolved

> **CHANGE CHG-19 (v1.3): Parallelization and hard deadlines formalized**
> PDB-01 and PDB-02 are independent of each other and must run simultaneously. Neither blocks the other. Both must close before PRD v1.3 is finalized (Step 3). If either escalates mid-evaluation, new changes belong in CHG-22+ not as post-v1.3 surprises. Step 2.5 — Joint DS + Dev Section 7 Review (NEW — required gate before finalization): Before PRD v1.3 is finalized, DS team and Dev team must jointly review Section 7 only: specifically the inputs_snapshot schema (Section 7.1) and the data_quality gate logic (Section 7.2). This is not a full document review. It is a targeted interface review. Purpose: if PDB-01 or PDB-02 resolution changes what inputs the soccer model can receive, Section 7.1 must be updated before the version is published — not after. Changes to inputs_snapshot or data_quality logic cascade immediately into the API doc interface contract and are the most likely source of silent DS/Dev misalignment at integration. Time required: approximately 1 hour. Must occur after PDB-01 and PDB-02 are both closed. Hard deadline for both PDB-01 and PDB-02: 2 weeks from PRD v1.2 sign-off. This deadline is not open-ended. If unresolved at the deadline, default actions apply (see below). Soccer model training cannot begin until PDB-02 is closed. Weather pipeline design cannot begin until PDB-01 is closed.

---

> **PRE-DEV BLOCKER PDB-01: Open-Meteo Commercial Licensing — Hard Blocker on Weather Pipeline Design**

> ⚠️ **[CHG-46] CRITICALLY OVERDUE — RESOLVE THIS WEEK.** The original 2-week deadline from PRD v1.2 sign-off has passed. June 11, 2026 is confirmed as the full-product launch date — approximately 80 days from time of writing. Weather pipeline design cannot begin until this is resolved. If PDB-01 remains open by end of this week, default immediately to Tomorrow.io without further evaluation (see default action below). Do not allow this blocker to delay pipeline work any further.
>
> Escalation path if unresolved by end of this week: Engineering Lead declares PDB-01 resolved via default — Tomorrow.io selected. Update weather_snapshots.source to 'tomorrow-io'. Notify Product Lead. Mark closed.
>
> DO NOT begin weather data pipeline design or implementation until this is resolved. Parallax is a commercial subscription platform and almost certainly does not qualify for Open-Meteo's free non-commercial tier. Building the weather pipeline against the free tier and then discovering a commercial license is required forces a pipeline rebuild.
>
> Required action — in order:
> 1. Legal confirms Parallax's classification under Open-Meteo's licensing terms.
> 2. If commercial license required: obtain Open-Meteo enterprise plan pricing.
> 3. If pricing acceptable: proceed with Open-Meteo. Update weather_snapshots.source to 'open-meteo-enterprise'.
> 4. If pricing not acceptable OR no response by the 2-week deadline: default to Tomorrow.io (500 free calls/day for development, paid at production). Visual Crossing ($35/month) is the secondary fallback. Update weather_snapshots.source to 'tomorrow-io' or 'visual-crossing' accordingly.
>
> Owner: Legal (licensing classification) + Engineering (vendor selection on resolution).
> PRD reference: Section 7.2 (model inputs), Section 10.2 (risk register), Section 11.1.
> API Requirements reference: v0.4 Open Question 3 — now a hard blocker, not open-ended.

---

> **PRE-DEV BLOCKER PDB-02: World Cup 2026 xG Data Source — ✅ CLOSED (CHG-51, 2026-03-24)**
> ✅ **RESOLVED.** StatsBomb Open Data (primary) + Understat club proxy (gap-fill) accepted. The original 2-week deadline from PRD v1.2 sign-off has passed. June 11, 2026 is confirmed as the full-product launch date — approximately 80 days from time of writing. Soccer model training for WC2026 cannot begin until this is resolved. With ~80 days to launch, the DS team needs every available day for training, backtesting, and calibration. A further week of delay on data source selection materially compresses the model development window.
>
> Escalation path if unresolved by end of this week: DS Lead evaluates StatsBomb open data immediately (github.com/statsbomb/open-data — no access request required, data is public). If StatsBomb WC2018/WC2022 data meets Dixon-Coles input requirements after a 48-hour evaluation, mark PDB-02 resolved as Option 1. If it does not, default immediately to Option 2 (club proxy). Do not spend more than one week on evaluation. The cost of a slightly less precise xG source is far lower than the cost of delayed model training.
>
> DO NOT begin soccer model training for World Cup 2026 fixtures until this is resolved. The DS team member who owns the WC2026 data pipeline must be designated before evaluation begins and must participate in the Step 2.5 joint Section 7 review. Understat does NOT reliably cover World Cup tournament fixtures. The Dixon-Coles soccer model requires historical xG inputs. Without a confirmed WC2026 xG data source, the DS team cannot train or validate the World Cup component of the soccer model.
>
> Prescribed direction — evaluate in this order:
> - Option 1 (recommended): StatsBomb Open Data. Repository: github.com/statsbomb/open-data. Python client: statsbombpy (pip install statsbombpy). Available: WC2018 and WC2022 shot-level event data with xG. DS team: evaluate data quality and coverage against Dixon-Coles input requirements. If accepted: ingest into S3 alongside Understat. Credit StatsBomb in all published methodology documentation. This is the expected outcome.
> - Option 2 (fallback — no new vendor): Club-level xG proxy. Build a player-weighted club-to-international xG mapping using Understat club data for players in each WC2026 squad. Methodologically defensible. Requires no additional data source. Disclose the proxy methodology on the methodology page. Use this option only if StatsBomb data fails quality requirements.
> - Option 3 (only if Options 1 and 2 are rejected): API-Football xG coverage. Verify whether API-Football includes xG for WC2026 tournament fixtures. Already in vendor stack — no new contract required if confirmed.
>
> Impact of outcome on Section 7.1: if Option 2 (club proxy) is chosen, the inputs_snapshot schema for soccer may require a new field (e.g. xg_source_method: 'direct' | 'club_proxy'). This must be resolved in the Step 2.5 joint review.
>
> Owner: DS Team (designated pipeline owner).
> PRD reference: Section 7.1 (inputs_snapshot soccer keys), Section 11.1.
> API Requirements reference: v0.4 Open Question 9 — now prescribed, not open-ended.

---

> **[CHG-23] PRE-DEV BLOCKER PDB-03: UEFA Champions League xG Data Source — Hard Blocker on UCL Model Training**
> DO NOT begin soccer model training for Champions League fixtures until this is resolved. The DS team member who owns the UCL data pipeline must be designated before evaluation begins.
>
> Understat covers EPL club data but does not provide reliable UCL tournament fixture coverage. The Dixon-Coles soccer model requires historical xG inputs. Without a confirmed UCL xG data source, the DS team cannot train or validate the Champions League component of the soccer model.
>
> Evaluation approach: The DS team is responsible for identifying and evaluating available UCL xG data sources. No prescribed vendor order is mandated for PDB-03. Candidate sources include but are not limited to StatsBomb Open Data, FBref, and API-Football. The DS team should assess data quality and historical depth against Dixon-Coles input requirements and select the source that best meets them. The chosen source and rationale must be documented before model training begins.
>
> If the selected UCL xG source introduces a new vendor not currently in the stack, Engineering must confirm the vendor addition before the contract is signed and before PDB-03 is marked resolved.
>
> Impact of outcome on Section 7.1: if UCL xG data requires a different source method than EPL, the inputs_snapshot schema may need extension. DS and Dev teams must confirm in a joint review consistent with the Step 2.5 pattern before UCL model training begins.
>
> Owner: DS Team (designated pipeline owner).
> PRD reference: Section 7.1 (inputs_snapshot soccer keys), Section 10.1 (dependencies), Section 11.1.

---

## 0.2 Required Decisions With Prescribed Direction

> **CHANGE CHG-20 (v1.3): OQ-4 dependency on OQ-2 corrected — referee bundling is sequential, not parallel**
> Previous framing: OQ-4 (referee data bundling) was listed as a parallel open item alongside OQ-2 (BALLDONTLIE validation). Corrected framing: OQ-4 is sequentially dependent on OQ-2. Reason: referee data bundling can only be confirmed with the chosen production stats vendor. The vendor cannot be chosen until BALLDONTLIE validation determines whether SportsDataIO or Sportradar is required. Attempting to confirm bundling before the vendor is selected produces a meaningless answer.
>
> Corrected dependency map:
> - OQ-2 (BALLDONTLIE validation) → resolves → vendor selection
> - vendor selection → unblocks → OQ-4 (referee data bundling confirmation)
> - OQ-4 cannot begin until OQ-2 is complete.
>
> Independent items (genuinely parallel — not blocked by OQ-2):
> - OQ-5 (Pinnacle CLV confirmation) — verify with The Odds API independently
> - OQ-10 (concurrent user volume) — Engineering estimate, no vendor dependency
> - PDB-01 (Open-Meteo licensing) — Legal task, independent of stats vendor
> - PDB-02 (WC2026 xG data) — DS task, independent of stats vendor
> - PDB-03 (UCL xG data) — DS task, independent of stats vendor
>
> PDR-01 below is updated to reflect this corrected dependency structure.

---

> **PRE-DEV REQUIREMENT PDR-01: BALLDONTLIE Validation — Gate for Production Vendor Decision and Downstream Items**
> The BALLDONTLIE validation is the gate for the production stats vendor decision. The vendor decision then gates OQ-4 (referee data bundling). OQ-4 cannot begin until PDR-01 is complete. This is now explicit.
>
> What to validate:
> - NBA play-by-play latency: real-time per-second delivery reliability
> - NFL EPA coverage: matches nflfastR as the reference standard
> - NBA referee crew foul rate percentile: field available and populated
> - Historical data completeness: NBA back to 1979, NFL coverage depth
>
> Dependency map (corrected per CHG-20):
> - PDR-01 complete → vendor selected → OQ-4 (referee bundling) can begin
> - PDR-01 complete → vendor selected → injury polling vendor confirmed
> - PDR-01 complete → vendor selected → stats contract signed
> - OQ-5 (Pinnacle CLV), OQ-10 (concurrent volume): independent, run in parallel
>
> Prescribed direction: DS Team runs validation against a 2-week sample of live NBA and NFL data. If BALLDONTLIE meets all production requirements: defer SportsDataIO/Sportradar contract. Continue with BALLDONTLIE through development. If BALLDONTLIE fails on any critical dimension: escalate immediately to Engineering and begin SportsDataIO free trial in parallel. Do not wait for full validation to complete before starting paid vendor evaluation.
>
> Owner: DS Team (validation) + Engineering (vendor decision).
> PRD reference: Section 10.1 (dependencies), Section 10.2 (risk register), Section 11.1.

---

> **PRE-DEV REQUIREMENT PDR-02: Vendor Contract Prerequisites — Four Items Before Any Contract Is Signed**
> No vendor contract may be signed until all four are confirmed.
>
> 1. Pinnacle closing line confirmed in chosen odds vendor feed. (Independent — run now.) Verify explicitly with The Odds API for NFL, NBA, EPL, WC2026, and Champions League. Required for all CLV calculations per PRD Section 5.4.2 / US-009 AC-1.

> 2. NBA referee crew foul rate percentile bundled in chosen stats vendor contract. (Dependent on PDR-01 — cannot confirm until vendor is selected.) referee_foul_rate_percentile is a required model input (Section 7.1). If null at game time, data_quality_score is capped at 0.84 (Section 7.2).

> 3. NFL and NBA real-time injury feeds included in chosen stats vendor contract. (Dependent on PDR-01 — cannot confirm until vendor is selected.) nflreadr covers historical injury data for training only — not production polling. Real-time polling windows (Section 7.3) must be served by the paid stats vendor.

> 4. Expected concurrent user volume estimated and validated against vendor QPS limits. (Independent — run now. Target: 4 weeks from PRD v1.2 sign-off.) Required before any vendor rate limit negotiation in contract discussions.
>
> Owner: Engineering.
> PRD reference: Section 5.4.2, Section 7.1, Section 7.2, Section 7.3, Section 10.1.

---

> **PRE-DEV REQUIREMENT PDR-03: GDPR and Legal Prerequisites — Before Any User Data Is Collected**
> No user-facing product may collect any personal data until all three are complete.
>
> 1. Cookiebot configured and verified — free tier setup, geo-targeting confirmed, audit logging verified with legal counsel. PRD Section 8.4.

> 2. Data Processing Agreements (DPAs) signed with all vendors processing EU user data: The Odds API, chosen stats vendor, weather vendor, Cookiebot, Stripe, Supabase, Firebase FCM. PRD Section 11.3.

> 3. Privacy policy and terms of service reviewed by legal counsel and live on site before any account creation is permitted.
>
> Owner: Legal + Engineering.
> PRD reference: Section 8.4, Section 11.3.

---

## 0.3 Standing Conventions

> **STANDING CONVENTION: Rate Limit Single Source of Truth**
> The per-endpoint-group rate limit table in API Requirements Section 7 is the single authoritative source for rate limit specifications. PRD Section 6.2 defines global ceiling values only. Any change to rate limits requires a simultaneous update to BOTH documents. Changes to either document in isolation are not permitted. Both updates must be reviewed and approved by the Product Lead before implementation.
> API Requirements reference: v1.0 Section 7.

---

> **STANDING CONVENTION: Cross-Reference Lock — PRD Section Numbering**
> Any PRD section renumbering or addition triggers a mandatory API Requirements update before the new PRD version is published. The API Requirements document must be updated to reflect new section references in the same publication cycle as the PRD version that caused the change. Publishing a PRD version without a corresponding API doc update is not permitted when that PRD version changes section numbers or adds new sections.
> API Requirements reference: v1.0 Document Control.

---

# 1. Executive Summary

Parallax is an AI-powered sports betting analytics platform that provides bettors with fair value odds, model-driven insights, and professional-grade tools to identify where the market misprices outcomes. The name derives from the astronomical measurement technique — the gap between apparent and actual position — directly metaphorizing the platform's core value proposition.

> **"See the true line."**
> Every feature, every data display, and every model output should reinforce this promise. The market sees one thing. Parallax shows you where the truth diverges.

## 1.1 Product Vision

To become the most trusted sports betting analytics platform globally — the Bloomberg Terminal for bettors — providing professional-grade tools, transparent AI-driven fair value odds, and the data infrastructure to make genuinely informed betting decisions.

## 1.2 Launch Scope Summary

*[CHG-22: Champions League moved from Out of Scope to In Scope. Stretch goal qualifier removed.]*
*[CHG-30: Phase 2 sports confirmed with per-sport season-calendar phasing. FBS only for NCAA Football. NCAA Women's Basketball deferred to Phase 3. FCS deferred to Phase 3.]*

*[CHG-45, CHG-47: Phase 1 column split into explicit sub-phases reflecting confirmed deployment sequence. Phase 1A = June 11 full-product launch (WC2026 soccer only). Phase 1B = EPL + UCL (August 2026). Phase 1C = NFL (September 4, 2026). Phase 1D = NBA (October 2026).]*

| Dimension | Phase 1A — June 11, 2026 (Full Product Launch) | Phase 1B — August 2026 | Phase 1C — September 4, 2026 | Phase 1D — October 2026 | Phase 2 (Season-Gated, Post-Phase-1D) | Phase 3+ |

						

| Sports | Soccer (WC2026 only) | Soccer expanded (EPL + UCL added) | NFL | NBA | MLB, NHL, Tennis, NCAA Football (FBS), NCAA Men's Basketball (D1), World Rugby | Golf, Cricket, NCAA Women's Basketball, NCAA FCS Football, additional soccer leagues |

| **Soccer Competitions** | **World Cup 2026 only** | **EPL + UEFA Champions League added** | — | — | La Liga, Bundesliga, Serie A, MLS, Ligue 1 | Additional UEFA competitions |

| **Rugby Competitions** | — | Six Nations, Rugby Championship, Rugby World Cup, URC, Premiership Rugby, Top 14 | — |

| **Tennis Competitions** | — | ATP Tour, WTA Tour, Four Grand Slams | ATP Challenger, WTA 125 |

| **NCAA Competitions** | — | FBS College Football (Power 4 + Group of 5 only), NCAA D1 Men's Basketball (full season incl. March Madness), NCAA Women's Basketball (March Madness / NCAA Tournament only — full season Phase 3) | FCS Football, NCAA Women's Basketball full season |

| Tiers | Free, Sharp ($19/month) | Free, Sharp | Free, Sharp | Free, Sharp | Pro, Elite, Syndicate (timing TBD) | — |
| Platforms | Web (Next.js), PWA | Web, PWA | Web, PWA | Web, PWA | Native iOS, Native Android | — |
| Betting Markets | Soccer: Spread (Asian Handicap), Moneyline (1X2), Totals, BTTS | Soccer expanded to EPL + UCL; same markets | NFL: Spread, Moneyline, Totals | NBA: Spread, Moneyline, Totals | Run line (MLB), Puck line (NHL), First 5 innings (MLB), Period betting (NHL), Set winner / Match tiebreak (Tennis), Try scorer (Rugby). **NCAA: game-level markets only — player prop scope gated on legal review.** | Player props (non-NCAA and post-legal-review NCAA), live betting, correct score |

| Revenue | Subscriptions only — no affiliate agreements at Phase 1A launch [CHG-48] | Subscriptions; affiliate agreements target: within 60 days post-Phase-1A | Subscriptions + Affiliates | Subscriptions + Affiliates | Pro/Elite/Syndicate tiers | API licensing (Phase 3 — see Section 14), white label |
| Auth | Email + OAuth (Google) | Email + OAuth | Email + OAuth | Email + OAuth | SSO, enterprise auth | — |
| i18n | English only — strings externalized to locale files from day one (CHG-38) | English only | English only | English only | French (trigger: Year 1 international user data) | Spanish, others TBD |

> **NCAA Player Props — Scope Note [CHG-30]**
> At Phase 2 launch, NCAA model output covers game-level markets only: spread, moneyline, and totals. Player props are not in scope at launch. This is not a permanent exclusion — it is a legal gate. Multiple US states with legal sports betting either prohibit or significantly restrict wagering on college athlete props, and this regulatory landscape is actively tightening. The platform's analytics layer does not currently have the infrastructure to enforce state-level market restrictions on a per-user basis. Before any NCAA player prop functionality is implemented, legal counsel must complete a review covering all active US sports betting jurisdictions and confirm the permissible scope. This review is a pre-launch checklist item for any NCAA prop feature (Section 11.3, CHG-43). The `ncaa_props_excluded` flag in model outputs (Section 7.1) is `true` at Phase 2 launch and must remain `true` until the legal review is completed and a PRD amendment is issued.

---

# 2. Goals and Success Metrics

## 2.1 Business Goals

| Goal | Target | Timeframe |
|---|---|---|
| Registered users | 5,000+ | 3 months post-Phase-1A launch (by September 11, 2026) |
| Paid subscribers | 500+ | 3 months post-Phase-1A launch (by September 11, 2026) |
| Monthly Recurring Revenue | $20,000+ | 6 months post-Phase-1A launch (by December 11, 2026) |
| Affiliate revenue | $5,000+/month | 6 months post-Phase-1A launch — affiliate agreements not required at June 11 launch [CHG-48] |
| Free to paid conversion | 5–8% | Ongoing |
| Monthly churn (paid) | Under 5% | Ongoing |
| X (Twitter) followers | 10,000+ | 6 months post-Phase-1A launch (by December 11, 2026) |

## 2.2 Model Performance Goals

| Metric | Target | Measurement |
|---|---|---|
| Brier Score (NFL) | Below 0.240 | Walk-forward validation, weekly |
| Brier Score (NBA) | Below 0.230 | Walk-forward validation, weekly |
| Brier Score (Soccer — EPL + WC2026 + UCL) | Below 0.220 | Walk-forward validation, weekly |
| Closing Line Value (CLV) | Positive on >55% of flagged value bets | Published predictions vs closing line |
| Calibration Error | Below 0.025 | Monthly calibration curve review |
| Model uptime | 99.5%+ | Grafana monitoring |
| Odds feed latency | Under 60 seconds from source | Pipeline monitoring |

## 2.3 Product Quality Goals

| Metric | Target |
|---|---|
| Page load time (P95) | Under 2.5 seconds globally |
| API response time (P95) | Under 300ms |
| PWA Lighthouse score | 90+ across all categories |
| Core Web Vitals | All green |
| Uptime SLA | 99.9% monthly |
| Test coverage | Minimum 80% across all services |

---

# 3. User Personas

| Persona | Description | Primary Goal | Tier |
|---|---|---|---|
| Casual Carl | Recreational bettor, 1–3x per week, favorite teams | Odds comparison, understanding vig, basic value identification | Free |
| Student Sam | Analytically curious student, limited budget | Education, understanding models, building knowledge | Free |
| Serious Hannah | Dedicated hobbyist, 10–20 hrs/week, tracks performance | CLV tracking, model outputs, line movement intelligence | Sharp |
| Semi-Pro Marcus | Treats betting as second income, multi-book | Full model access, sharp money indicators, all leagues | Pro (post-launch) |

---

# 4. Data Schema Definitions

Authoritative for both agent teams. Any deviation requires a documented change request approved by the Product Lead. All timestamps stored in UTC. All monetary values stored in USD.

## 4.1 Core Entities

### 4.1.1 Sports

```
Table: sports
sport_id UUID PK | slug VARCHAR(20) UNIQUE | name VARCHAR(100) | active BOOLEAN | created_at TIMESTAMPTZ
```

### 4.1.2 Leagues

```
Table: leagues
league_id UUID PK | sport_id UUID FK | slug VARCHAR(50) UNIQUE | name VARCHAR(100)
country VARCHAR(100) | active BOOLEAN | season_current VARCHAR(20) | created_at TIMESTAMPTZ
Phase 1 launch slugs: 'nfl' | 'nba' | 'epl' | 'world_cup_2026' | 'champions_league'
Phase 2 slugs (seed at Phase 2 planning, active = false until sport launch):
  MLB:                 'mlb'
  NHL:                 'nhl'
  Tennis:              'atp_tour' | 'wta_tour' | 'atp_gs' | 'wta_gs'
                       -- Grand Slams use separate slugs to distinguish from regular tour events
  NCAA Football (FBS): 'ncaa_fbs'
                       -- FBS only. FCS is Phase 3 — do not seed FCS slugs at Phase 2.
  NCAA Basketball:     'ncaa_d1_mb'    -- Men's D1 full season
                       'ncaa_wbb_t'    -- Women's Basketball Tournament (March Madness) only
                       -- Women's full season is Phase 3 — do not seed full-season slug at Phase 2.
  Rugby:               'six_nations' | 'rugby_championship' | 'rugby_world_cup'
                       'urc' | 'premiership_rugby' | 'top_14'
Phase 3 slugs (do not seed until Phase 3 planning):
  FCS Football:              'ncaa_fcs'
  Women's Basketball (full): 'ncaa_d1_wb'   -- full season; 'ncaa_wbb_t' already seeded at Phase 2 for tournament
  Golf, Cricket:             TBD at Phase 3 scoping
```

### 4.1.3 Teams

```
Table: teams
team_id UUID PK | league_id UUID FK | slug | name | abbreviation | city | conference | division
venue_name | venue_city | venue_lat DECIMAL(9,6) | venue_lng DECIMAL(9,6)
venue_surface VARCHAR(50)  -- 'grass' | 'turf'
venue_roof VARCHAR(50)     -- 'open' | 'dome' | 'retractable'  [AUTHORITATIVE WEATHER FLAG]
timezone | logo_url | active BOOLEAN | created_at | updated_at
```

### 4.1.4 Games

```
Table: games
game_id UUID PK | league_id FK | home_team_id FK | away_team_id FK
season | week | game_date | kickoff_utc | status | home_score | away_score
home_score_ht | away_score_ht | period | attendance
weather_id UUID FK  -- ALL outdoor/open-roof venues across ALL sports.
                    -- venue_roof = 'open' or 'retractable' is the flag.
                    -- Covers: outdoor NFL, open EPL grounds, WC2026 outdoor venues, UCL outdoor venues,
                    --         outdoor MLB stadiums (~20 of 30), outdoor Rugby venues, NCAA outdoor stadiums.
neutral_venue_lat DECIMAL(9,6)  -- [CHG-34] Populated when is_neutral_site = true AND venue is outdoor.
neutral_venue_lng DECIMAL(9,6)  -- Weather pipeline uses these coords instead of team venue coords.
                                -- Covers: WC2026 neutral venues, UCL finals, Rugby World Cup venues,
                                --         NCAA bowl games and tournament sites.
                                -- Dev Team: seed before pipeline build for all known scheduled neutral outdoor games.
is_neutral_site | is_divisional | is_playoff | is_primetime
external_ids JSONB | created_at | updated_at

NOTE — week column nullability [CHG-32]:
  NFL: week number (1–18 regular season + playoffs). Required, never null.
  NCAA Football: college football week number (1–15 + bowl/playoff). Required, never null.
  Rugby: round number within competition phase (e.g. Round 1–5 for Six Nations). Required, never null.
  NBA / NHL / MLB: NULL — games identified by game_date and external_ids.
  Soccer: NULL for WC2026 group stage phase (use external_ids for matchday); EPL matchweek stored in external_ids JSONB.
  Tennis: not applicable — tennis uses tennis_matches table (CHG-31), not games table.
  Downstream queries filtering by week MUST include a NULL check or sport_slug filter. Sport-agnostic
  queries that assume week is always populated will produce silent data gaps for non-NFL sports.
```

### 4.1.5 Odds

```
Table: odds
odds_id UUID PK | game_id FK | book_id FK
market_type VARCHAR(50)  -- Phase 1: 'spread'|'moneyline'|'total'|'1x2'|'asian_handicap'|'btts'
                         -- Phase 2 additions [CHG-33]:
                         --   MLB:    'run_line'         (spread alias — display as run_line, calculate as spread)
                         --           'first_5_innings'  (distinct market, no spread/total equivalent)
                         --   NHL:    'puck_line'        (spread alias — display as puck_line, calculate as spread)
                         --           'period'           (period betting, use period field to specify)
                         --   Tennis: 'set_winner'       (set-level market)
                         --           'match_tiebreak'   (match tiebreak market)
                         --   Rugby:  'try_scorer'       (player-level — display only; not a model output market)
period VARCHAR(20) DEFAULT 'full_game'  -- 'full_game'|'first_half'|'first_5_innings'|'period_1'|'period_2'|'period_3'|'set_1'|'set_2' etc.
home_odds | away_odds | draw_odds (soccer/rugby) | spread_home | spread_away
total_line | over_odds | under_odds | is_opening | is_current | recorded_at
INDEX: idx_odds_game_book_market ON odds(game_id, book_id, market_type)
INDEX: idx_odds_recorded_at ON odds(recorded_at DESC)
```

### 4.1.6 Books

```
Table: books
book_id UUID PK | slug VARCHAR(50) UNIQUE | name VARCHAR(100)
is_sharp BOOLEAN | is_affiliate BOOLEAN | affiliate_url | logo_url
regions VARCHAR[] | active BOOLEAN | display_order INTEGER | created_at
NOTE: Pinnacle must always be displayed regardless of is_affiliate status.
```

### 4.1.7 Model Outputs

```
Table: model_outputs
output_id UUID PK | game_id FK | model_version VARCHAR(50) | sport_slug VARCHAR(20)
home_win_prob | away_win_prob | draw_prob (soccer) | fair_spread | fair_total
fair_home_odds_dec | fair_away_odds_dec | fair_draw_odds_dec (soccer)
confidence_score DECIMAL(4,3)   -- 0.000 to 1.000
data_quality_score DECIMAL(4,3) -- 0.000 to 1.000
                                -- < 0.70: BLOCKED — pipeline must not publish
                                -- 0.70–0.85: publish with data_quality_flag: true
                                -- > 0.85: publish normally
inputs_snapshot JSONB NOT NULL | flags JSONB
generated_at | is_published BOOLEAN | published_at
CONSTRAINT: CHECK (data_quality_score >= 0.70 OR is_published = false)
```

### 4.1.8 Predictions

```
Table: predictions
prediction_id UUID PK | game_id FK | output_id FK | model_version
market_type | predicted_side | model_probability | market_odds_at_pub (locked at pub)
market_spread_at_pub | edge_pct | closing_odds_dec | clv_pct
result  -- 'win'|'loss'|'push'|'pending' | published_at | settled_at
```

### 4.1.9 Users

```
Table: users
user_id UUID PK | email VARCHAR(255) UNIQUE | email_verified | display_name
auth_provider  -- 'email'|'google'
subscription_tier DEFAULT 'free'  -- 'free'|'sharp'|'pro'|'elite'
subscription_id | subscription_status | subscription_end
country_code | timezone DEFAULT 'UTC'
odds_format DEFAULT 'american'  -- 'american'|'decimal'|'fractional'
currency DEFAULT 'USD'  -- 'USD'|'GBP'|'EUR'|'AUD'
sports_followed DEFAULT '{nfl,nba,soccer}'
  -- [CHG-30] Update default to '{nfl,nba,soccer}' at Phase 1 launch.
  -- At Phase 2 launch, run migration to add new sport slugs to users who have not customised this field.
  -- Do NOT retroactively update customised preferences. Add new sport slugs only to users still on the default.
marketing_consent | gdpr_consent | gdpr_consent_at | age_verified
created_at | updated_at | last_seen_at
```

### 4.1.10 Team Ratings

```
Table: team_ratings
rating_id UUID PK | team_id FK | model_version | season | week
rating_offense | rating_defense | rating_net | rating_overall | games_played | computed_at
UNIQUE: (team_id, model_version, season, week)
NOTE: This table covers all team-based sports (NFL, NBA, Soccer, MLB, NHL, NCAA Football, NCAA Basketball, Rugby).
      Tennis does NOT use this table — see player_ratings (Section 4.1.14).
```

### 4.1.11 Weather Snapshots

```
Table: weather_snapshots
weather_id UUID PK | game_id FK | temperature_f | wind_speed_mph | wind_direction_deg
precipitation_in | humidity_pct | conditions | is_dome BOOLEAN DEFAULT false
venue_lat | venue_lng  -- coordinate used for weather API query (stored for provenance)
                       -- For neutral-site outdoor games, this is games.neutral_venue_lat/lng, not team venue coords.
forecast_at | source VARCHAR(50)  -- 'open-meteo'|'open-meteo-enterprise'|'tomorrow-io'|'visual-crossing'
created_at
```

### 4.1.12 Alerts

```
Table: user_alerts
alert_id UUID PK | user_id FK | alert_type | sport_slug | team_id FK | game_id FK
threshold_value | market_type | delivery_channels VARCHAR[] | is_active | created_at

Table: alert_events
event_id UUID PK | alert_id FK | user_id FK | game_id FK | event_type | event_data JSONB
delivered_push | delivered_email | triggered_at
```

### 4.1.13 Tennis Matches [CHG-31]

Tennis is an individual sport. The `games` table home/away team model does not apply. All tennis matches are stored in a separate `tennis_matches` table. The `games` table is not used for tennis.

```
Table: tennis_matches
match_id UUID PK | league_id FK
player1_id UUID FK  -- references players table (Section 4.1.14 player_ratings; players table implied)
player2_id UUID FK  -- player1 = higher seed / home equivalent for display purposes
surface VARCHAR(20)  -- 'hard'|'clay'|'grass'|'indoor_hard'
tournament_name VARCHAR(100) | tournament_round VARCHAR(50)  -- 'R128'|'R64'|'R32'|'R16'|'QF'|'SF'|'F'
season | match_date | start_time_utc | status
player1_sets | player2_sets | sets_detail JSONB  -- e.g. [{p1: 6, p2: 3}, {p1: 7, p2: 6}]
is_best_of_5 BOOLEAN  -- Grand Slams men's singles: true. All others: false.
venue_name | venue_city | venue_lat DECIMAL(9,6) | venue_lng DECIMAL(9,6)
venue_roof VARCHAR(50)  -- 'open'|'retractable'|'indoor' — weather applies to 'open' and 'retractable' only
weather_id UUID FK  -- populated when venue_roof = 'open' or 'retractable'
external_ids JSONB | created_at | updated_at

Table: players
player_id UUID PK | slug VARCHAR(100) UNIQUE | full_name VARCHAR(200) | nationality VARCHAR(100)
tour VARCHAR(10)  -- 'atp'|'wta'
current_ranking INTEGER | date_of_birth | turned_pro INTEGER | active BOOLEAN
logo_url | created_at | updated_at

Table: tennis_odds
tennis_odds_id UUID PK | match_id FK | book_id FK
market_type VARCHAR(50)  -- 'moneyline'|'spread'|'total'|'set_winner'|'match_tiebreak'
period VARCHAR(20) DEFAULT 'full_match'
player1_odds | player2_odds | spread_player1 | spread_player2
total_line | over_odds | under_odds | is_opening | is_current | recorded_at
INDEX: idx_tennis_odds_match_book ON tennis_odds(match_id, book_id, market_type)
```

### 4.1.14 Player Ratings (Tennis) [CHG-31]

```
Table: player_ratings
rating_id UUID PK | player_id FK | model_version | season
surface VARCHAR(20)  -- 'hard'|'clay'|'grass'|'indoor_hard' — rating is surface-specific
elo_rating DECIMAL(8,2) | elo_uncertainty DECIMAL(6,4)
surface_win_rate_52w DECIMAL(5,4)  -- rolling 52-week win rate on this surface
surface_games_played INTEGER | computed_at TIMESTAMPTZ
UNIQUE: (player_id, model_version, season, surface)
NOTE: Elo ratings are surface-stratified. A player has up to 4 active ratings simultaneously (one per surface).
      Model selects the rating matching the match surface. If surface_games_played < 10, data_quality_score is capped.
```

### 4.1.15 User Bets

*[CHG-49: match_table discriminator column added. Removes silent join ambiguity between games and tennis_matches tables.]*

```
Table: user_bets
bet_id UUID PK | user_id FK | game_id FK | book_id FK
match_table VARCHAR(30) NOT NULL DEFAULT 'games'
  -- 'games'         : all sports except tennis (NFL, NBA, Soccer, MLB, NHL, NCAA, Rugby)
  -- 'tennis_matches': tennis bets only — game_id references tennis_matches.match_id
  -- Application layer MUST populate this field at bet creation.
  -- Reporting queries MUST use match_table to route joins to the correct source table.
  -- Great Expectations check: match_table = 'tennis_matches' for all rows where sport_slug = 'tennis'.
  --                           match_table = 'games' for all rows where sport_slug != 'tennis'.
sport_slug | league_slug | market_type | bet_side
odds_taken_dec | odds_taken_american | stake | potential_payout
result DEFAULT 'pending' | profit_loss | closing_odds_dec | clv_pct
notes | tags | bet_placed_at | settled_at | created_at | updated_at
```

---

# 5. Feature Specifications

All acceptance criteria numbered AC-N within each user story. Format US-XXX AC-N for cross-referencing. Tests are written before implementation per TDD mandate.

## 5.1 Authentication and User Management

### 5.1.1 Feature Description

Email/password and Google OAuth. GDPR consent and age verification enforced globally. Supabase. See Section 0 PDR-03 — no user data collected until GDPR prerequisites are complete.

**US-001** — As a **new visitor**, I want to register with my email and password so that I can create a Parallax account and access the free tier immediately.

Acceptance Criteria (TDD):
- GIVEN a valid email and password (8+ chars, 1 uppercase, 1 number), WHEN I submit, THEN account created, verification email sent within 30 seconds, and I am logged in to the free tier dashboard
- GIVEN an email already registered, WHEN I attempt registration, THEN error 'An account with this email already exists' is displayed and no duplicate created
- GIVEN any registration attempt, WHEN submitted globally, THEN GDPR consent checkbox must be checked or submission is blocked
- GIVEN any registration attempt, WHEN submitted, THEN age verification must be confirmed or submission is blocked
- GIVEN a failed registration, WHEN resubmitted, THEN email is preserved and only password fields are cleared

---

**US-002** — As a **registered user**, I want to log in with Google OAuth so that I can access my account without managing a separate password.

Acceptance Criteria (TDD):
- GIVEN I click 'Continue with Google', WHEN I authorize, THEN I am logged in within 5 seconds and redirected to my dashboard
- GIVEN a new Google account, WHEN OAuth completes, THEN a new account is created and GDPR and age consent screens are shown before dashboard access
- GIVEN an existing email matching the Google email, WHEN OAuth completes, THEN accounts are merged and I am logged in
- GIVEN an OAuth failure or cancellation, WHEN the flow returns, THEN I see 'Google sign-in was cancelled or failed. Please try again.'

---

**US-003** — As a **logged-in user**, I want to manage my account preferences so that the platform displays odds in my preferred format and timezone.

Acceptance Criteria (TDD):
- GIVEN I change odds format, WHEN saved, THEN all odds across the platform update immediately without page refresh
- GIVEN I set my timezone, WHEN I view any game, THEN kickoff times display in my timezone with abbreviation
- GIVEN I set my currency, WHEN pricing is displayed, THEN prices show in my currency with USD equivalent in tooltip
- GIVEN I change any preference, WHEN saved, THEN success confirmation shown and preference persists across sessions

---

## 5.2 Odds Comparison Engine

### 5.2.1 Feature Description

Real-time odds from multiple sportsbooks. Best available line, vig calculation, no-vig fair odds, line movement history. Pinnacle always displayed. Primary vendor: The Odds API. See Section 0 PDR-02 item 1 for Pinnacle confirmation requirement.

| Capability | Free Tier | Sharp Tier |
|---|---|---|
| Books displayed | Top 5 books | All available (10+) |
| Line movement history | Current only | Full history from open |
| Odds formats | American only | American, decimal, fractional |
| Vig + no-vig display | Vig only | Vig + no-vig fair odds |
| Best line highlighting | Yes | Yes + book recommendation |
| Alert on line move | No | Yes (configurable) |
| Historical odds | No | 3 months |

**US-004** — As a **free tier user**, I want to see live odds from multiple sportsbooks for any game so that I can identify the best line without visiting multiple sites.

Acceptance Criteria (TDD):
- GIVEN I navigate to any scheduled game, WHEN odds are available, THEN odds from minimum 5 books displayed within 2 seconds
- GIVEN odds are displayed, THEN the best moneyline and spread for each side is highlighted in green
- GIVEN American format by default, WHEN I toggle to decimal, THEN all odds update immediately without page refresh
- GIVEN free tier, WHEN I attempt to view more than 5 books, THEN remainder are blurred with 'Unlock all books with Sharp'
- GIVEN odds are stale (over 90 seconds old), THEN yellow warning 'Odds may be delayed' is shown with last update timestamp
- GIVEN no odds available, THEN 'Odds not yet available for this game' is displayed

---

**US-005** — As a **sharp tier user**, I want to view the full line movement history for a game so that I can identify when sharp money moved the line.

Acceptance Criteria (TDD):
- GIVEN I am a Sharp subscriber, WHEN I view the line movement chart, THEN movement shown from opening line to current with timestamps
- GIVEN significant movement (2+ points spread, 3+ total), THEN annotated with timestamp and magnitude
- GIVEN I hover over any point, THEN tooltip shows time, spread, total, and which book moved first
- GIVEN Pinnacle moves before recreational books, THEN Pinnacle line shown in distinct color with 'Sharp Book' label

---

## 5.3 Parallax Model Output Display

### 5.3.1 Feature Description

AI-generated fair value odds vs market odds with explicit edge calculation. Free: 3 outputs/day. Sharp: unlimited with full detail including input factors, confidence, and data quality indicators.

**US-006** — As a **free tier user**, I want to see the Parallax model's fair value odds for upcoming games so that I can understand where the model sees value compared to the market.

Acceptance Criteria (TDD):
- GIVEN I navigate to the model section, WHEN outputs are available, THEN I see model win probabilities, fair value odds, and gap vs market
- GIVEN free tier with 3 outputs viewed today, WHEN I attempt a fourth, THEN I see 'You have used your 3 free daily model previews. Upgrade to Sharp for unlimited access'
- GIVEN a model output is displayed, WHEN edge is positive, THEN edge indicator shown in green; WHEN negative, in grey
- GIVEN I click 'How is this calculated?', THEN a modal explains the methodology in plain language

---

**US-007** — As a **sharp tier user**, I want to see the full model output including input factors and confidence so that I can evaluate the model's reasoning and decide whether to act on it.

Acceptance Criteria (TDD):
- GIVEN I am a Sharp subscriber, WHEN I view any model output, THEN I see probabilities, fair odds for all markets, confidence score, data quality score, and key input factors
- GIVEN key factors are displayed, THEN I see home/away ratings, rest differential, weather flag, injury flag, and home advantage value
- GIVEN confidence score below 0.60, THEN yellow warning 'Lower confidence — limited data' is shown
- GIVEN data quality score 0.70–0.85, THEN yellow warning 'Data quality flag — verify before betting' is shown
- GIVEN data quality score below 0.70, WHEN the DS pipeline runs, THEN this output is NOT published and never shown to any user
- GIVEN model outputs are available, WHEN I view the value screen, THEN games sorted by edge percentage with filters

---

## 5.4 Bet Tracker

### 5.4.1 Feature Description

Manual bet logging with performance analytics. CLV auto-populated when closing odds available. Free: 50 bet limit. Sharp: unlimited.

**US-008** — As a **free tier user**, I want to log my bets manually so that I can track my betting performance over time.

Acceptance Criteria (TDD):
- GIVEN I click 'Log Bet', WHEN I complete the form, THEN bet saved with game, market, side, odds, and stake
- GIVEN free tier at 50 bets, WHEN I attempt bet 51, THEN 'Free tier limit of 50 bets reached. Upgrade to Sharp for unlimited tracking' is shown
- GIVEN a bet is logged, WHEN the game result is final, THEN result auto-populated within 30 minutes of final whistle
- GIVEN a bet is settled, WHEN CLV data is available, THEN clv_pct auto-populated

---

**US-009** — As a **sharp tier user**, I want to view my full betting performance analytics so that I can evaluate whether I am beating the closing line.

Acceptance Criteria (TDD):
- GIVEN I am a Sharp subscriber, WHEN I view the tracker, THEN I see win rate, ROI, P&L, and average CLV across all logged bets
- GIVEN I filter by sport or date range, WHEN applied, THEN all performance metrics update to reflect the filtered subset
- GIVEN average CLV is positive, THEN displayed in green with tooltip 'Beating the closing line on average — a strong indicator of long-term edge'
- GIVEN average CLV is negative, THEN displayed in red with tooltip 'Below closing line on average'

---

## 5.5 Alerts Engine

### 5.5.1 Feature Description

Push and email alerts for line moves, model edge thresholds, and injury news. Sharp tier only. Firebase FCM for push. 2-minute SLA from trigger to delivery.

**US-010** — As a **sharp tier user**, I want to receive an alert when a game's line moves significantly so that I can act before the market corrects.

Acceptance Criteria (TDD):
- GIVEN I set a line movement alert for a game, WHEN the spread moves 2+ points or total moves 3+, THEN I receive a push notification within 2 minutes
- GIVEN I have set delivery to email, WHEN the threshold is met, THEN email delivered within 2 minutes
- GIVEN a line move alert fires, THEN notification includes game, market, old line, new line, and timestamp
- GIVEN I have disabled push, WHEN threshold is met, THEN email-only delivery is used

---

**US-011** — As a **sharp tier user**, I want to receive an alert when the Parallax model identifies a high-edge bet so that I am notified of value without checking the platform constantly.

Acceptance Criteria (TDD):
- GIVEN I set an edge threshold alert (e.g., 4%+), WHEN a model output exceeds the threshold, THEN I receive notification within 2 minutes of model publication
- GIVEN the alert fires, THEN notification includes game, market, edge percentage, model probability, and current market odds
- GIVEN the game is within 1 hour of kickoff, THEN alert is suppressed (too late to act) unless user has enabled late alerts

---

**US-012** — As a **user**, I want to view the Parallax public track record so that I can evaluate model performance before subscribing.

Acceptance Criteria (TDD):
- GIVEN I navigate to the track record page without logging in, THEN I see full prediction history, win rate, avg CLV, and Brier score — no auth required
- GIVEN I filter by sport, WHEN applied, THEN all summary metrics and table rows update to the filtered sport
- GIVEN I filter by date range, WHEN applied, THEN summary metrics recalculate for the selected range
- GIVEN a prediction is displayed, THEN model probability, market odds at publication (locked), closing odds, CLV, and result are all visible
- GIVEN no predictions exist yet, THEN 'No predictions published yet — check back at launch' is shown

---

# 6. API Specification

## 6.1 Base URL

```
https://api.parallaxedge.com/v1
```

## 6.2 Global Rate Limits

Rate limits by tier and endpoint group are defined in API Requirements v1.0 Section 7 — the single source of truth. Global ceiling values only in this section.

| Tier | Global ceiling |
|---|---|
| Unauthenticated | 20 req/min |
| Free | 60 req/min |
| Sharp | 300 req/min |

## 6.3 Core Endpoint Contracts

### GET /api/v1/games/{sport}

```
Query: date (default today) | league | status | limit (max 50) | offset
Response 200: {
  games: [{ game_id, league, home_team, away_team, kickoff_utc,
             status, scores, is_divisional, is_primetime,
             has_model_output, weather_flag }],
  total, limit, offset
}
```

### GET /api/v1/games/{game_id}/odds

```
Query: market_type | period
Response 200: {
  game_id, last_updated,
  markets: {
    spread: {
      books: [{ book, home_odds, away_odds, spread_home, is_best_home,
                affiliate_url, recorded_at }],
      vig_pct, no_vig_home_odds, no_vig_away_odds,
      books_shown, books_total, tier_limited: bool
    }
  }
}
```

### GET /api/v1/games/{game_id}/model

```
Auth: Required. Free tier: 3/day server-side limit.
Response 200: {
  game_id, model_version, generated_at,
  probabilities: { home_win, away_win, draw },
  fair_odds: { spread, moneyline, total },
  market_comparison: { spread_edge_home, spread_edge_away, total_edge_over, total_edge_under },
  confidence_score, data_quality_score,
  key_factors: { home/away ratings, rest days, home_advantage_pts,
                 weather_impact, injury_adjusted, is_divisional },
  flags: { weather_impact, injury_adjusted, low_confidence, data_quality_flag, early_season },
  tier_limited: bool
}
data_quality_flag: true when score < 0.85. Outputs < 0.70 never returned (blocked at source).
```

### POST /api/v1/bets

```
Body: { game_id, book_id, sport_slug, league_slug, market_type, bet_side,
        odds_taken_american, stake, bet_placed_at, notes?, tags? }
Response 201: { bet_id, potential_payout, result: 'pending', created_at }
Error 403: { error: { code: 'TIER_INSUFFICIENT', message: 'Free tier limit of 50 bets reached' } }
```

### GET /api/v1/track-record

```
Auth: None (public).
Query: sport | market_type | from_date | to_date | limit (max 200) | offset
Response 200: {
  summary: { total_predictions, record, win_rate, avg_clv, brier_score, roi },
  predictions: [{ game, market_type, predicted_side, model_probability,
                  market_odds_at_pub, closing_odds, clv_pct, result, published_at }]
}
```

---

# 7. DS Team — Model Interface Contract

Authoritative contract between the DS Agent Team and the Dev Agent Team. No deviation without a documented change request approved by the Product Lead. The Step 2.5 joint review (Section 0 CHG-19) covers Section 7.1 and 7.2 specifically.

## 7.1 Model Output Specification

```
Required fields — all models:
  game_id | model_version | sport_slug
  home_win_prob + away_win_prob = 1.0000 (NFL/NBA/NCAA Football/NCAA Basketball/Rugby)
  home_win_prob + draw_prob + away_win_prob = 1.0000 (soccer/rugby where draw is a valid outcome)
  player1_win_prob + player2_win_prob = 1.0000 (tennis — no draw)
  fair_spread | fair_total | fair_home_odds_dec | fair_away_odds_dec
  fair_draw_odds_dec (soccer and rugby where draw market exists)
  confidence_score (0.000–1.000)
  data_quality_score: < 0.70 BLOCK | 0.70–0.85 FLAG | > 0.85 PASS
  inputs_snapshot JSONB | flags JSONB

inputs_snapshot keys — all team-sport models (NFL, NBA, Soccer, MLB, NHL, NCAA Football, NCAA Basketball, Rugby):
  home/away: rating_offense, rating_defense, rating_overall, games_played
  home/away: rest_days, injury_adjustment
  home_advantage_pts | is_neutral_site | is_divisional | is_playoff
  weather_wind_mph | weather_temp_f | weather_precipitation | is_dome (outdoor venues)

inputs_snapshot keys — NBA only:
  home/away: back_to_back, pace
  referee_foul_rate_percentile  -- if null, data_quality_score MUST be capped at 0.84

inputs_snapshot keys — Soccer (EPL + WC2026 + Champions League):
  home/away: xg_attack, xg_defense, league_avg_goals
  xg_source_method: 'direct' | 'club_proxy'  -- required if PDB-02 resolves to Option 2
  NOTE: WC2026 xG source confirmed per Section 0 PDB-02 before training begins.
  NOTE: UCL xG source confirmed per Section 0 PDB-03 before UCL model training begins.

inputs_snapshot keys — MLB only [CHG-35]:
  home/away: team_era_rolling, team_bullpen_era_rolling, team_woba_rolling, team_babip_rolling
  home_starter_era | home_starter_fip | home_starter_xfip | home_starter_k_rate | home_starter_bb_rate
  away_starter_era | away_starter_fip | away_starter_xfip | away_starter_k_rate | away_starter_bb_rate
  is_starting_pitcher_confirmed BOOLEAN  -- CRITICAL: if false, output is BLOCKED (see Section 7.2 CHG-36)
  park_factor DECIMAL(5,3)  -- run environment adjustment for this specific ballpark
  NOTE: weather inputs apply to ~20 of 30 MLB outdoor stadiums. is_dome flag sourced from venue_roof field.

inputs_snapshot keys — NHL only [CHG-35]:
  home/away: corsi_for_pct_rolling, fenwick_for_pct_rolling, xg_for_rolling, xg_against_rolling
  home/away: power_play_pct, penalty_kill_pct, goals_for_rolling, goals_against_rolling
  home_goalie_save_pct | home_goalie_gaa | home_goalie_gsax  -- goals saved above expected
  away_goalie_save_pct | away_goalie_gaa | away_goalie_gsax
  is_starting_goalie_confirmed BOOLEAN  -- if false, data_quality_score capped at 0.70 (see Section 7.2 CHG-36)
  NOTE: all NHL arenas are indoor — no weather inputs. is_dome always true.

inputs_snapshot keys — Tennis only [CHG-35]:
  NOTE: tennis uses match_id (from tennis_matches), not game_id. sport_slug = 'tennis'.
  player1_elo | player2_elo  -- surface-specific Elo from player_ratings table
  player1_elo_uncertainty | player2_elo_uncertainty
  player1_surface_win_rate_52w | player2_surface_win_rate_52w
  player1_surface_games_played | player2_surface_games_played
  surface  -- 'hard'|'clay'|'grass'|'indoor_hard'
  is_best_of_5 BOOLEAN
  tournament_round  -- 'R128'|'R64'|...|'F' — affects model confidence (early rounds have wider distribution)
  weather_wind_mph | weather_temp_f | weather_precipitation | is_dome  -- outdoor courts only
  NOTE: if player1_surface_games_played < 10 OR player2_surface_games_played < 10,
        data_quality_score capped at 0.75 (see Section 7.2 CHG-36).

inputs_snapshot keys — NCAA Football (FBS) only [CHG-35]:
  IDENTICAL to NFL inputs_snapshot keys with the following additions:
  is_conference_game BOOLEAN  -- conference games weighted differently in home field model
  is_rivalry_game BOOLEAN     -- flag for historically significant rivalry matchups
  is_bowl_game BOOLEAN        -- bowl games are neutral site; home_advantage_pts = 0
  NOTE: FBS only. FCS is Phase 3 — no inputs_snapshot definition required at this time.
  NOTE: ncaa_props_excluded flag is true at Phase 2 launch. Set to false only after legal review
        is completed and a PRD amendment is issued (Section 1.2, CHG-30).

inputs_snapshot keys — NCAA Men's Basketball (D1) only [CHG-35]:
  IDENTICAL to NBA inputs_snapshot keys with the following additions:
  is_conference_game BOOLEAN
  is_conference_tournament BOOLEAN
  tournament_seed_home | tournament_seed_away  -- NULL outside tournament; 1–16 during March Madness
  tournament_region VARCHAR(20)                -- NULL outside tournament; 'East'|'West'|'South'|'Midwest'
  NOTE: referee_foul_rate_percentile applies identically to NCAA Men's Basketball as to NBA.
        If null at game time, data_quality_score capped at 0.84. Same cap, same vendor dependency.
  NOTE: ncaa_props_excluded flag is true at Phase 2 launch. Set to false only after legal review
        is completed and a PRD amendment is issued (Section 1.2, CHG-30).

inputs_snapshot keys — NCAA Women's Basketball (Tournament only) [CHG-35]:
  IDENTICAL to NCAA Men's Basketball inputs_snapshot keys.
  tournament_seed_home | tournament_seed_away  -- always populated (tournament-only scope)
  tournament_region VARCHAR(20)                -- always populated (tournament-only scope)
  NOTE: Women's Basketball scope is March Madness (NCAA Tournament) only at Phase 2.
        Full season is Phase 3. Data pipeline only needs to activate for tournament window.
  NOTE: ncaa_props_excluded flag applies identically to Women's Basketball.

inputs_snapshot keys — Rugby only [CHG-35]:
  home/away: rating_attack, rating_defense, rating_overall, games_played
  home/away: rest_days, injury_adjustment
  home/away: tries_scored_rolling, tries_conceded_rolling, points_for_rolling, points_against_rolling
  home_advantage_pts | is_neutral_site | is_playoff | competition_phase  -- 'group'|'knockout'|'final'
  weather_wind_mph | weather_temp_f | weather_precipitation | is_dome  -- most rugby is outdoor
  NOTE: draw is a valid match outcome in rugby — model must output three-way probabilities.
        fair_draw_odds_dec is required. market_type '1x2' applies for match result betting.

flags required keys (all sports):
  weather_impact | injury_adjusted | low_confidence (< 0.60)
  data_quality_flag (0.70–0.85) | early_season (< 4 games) | model_updated_injury
  pitcher_unconfirmed (MLB — set when is_starting_pitcher_confirmed = false; output blocked, not flagged)
  goalie_unconfirmed (NHL — set when is_starting_goalie_confirmed = false)
  low_surface_sample (Tennis — set when either player has < 10 surface games)
  ncaa_props_excluded (NCAA all sports — true at Phase 2 launch; indicates props not in model scope;
                       set to false only after legal review + PRD amendment per Section 1.2 CHG-30)
```

> **Note on xg_source_method field**
> This field is conditional on the PDB-02 and PDB-03 resolution outcomes. If Option 1 (StatsBomb) is selected for WC2026: xg_source_method = 'direct' for all WC2026 outputs. If Option 2 (club proxy) is selected: xg_source_method = 'club_proxy' for WC2026 outputs. For UCL outputs, the source method field must reflect the source confirmed under PDB-03. This field must be included in the inputs_snapshot if a non-direct source method is chosen for any competition. The Step 2.5 joint DS + Dev review will confirm whether this field needs to be updated in the inputs_snapshot schema and the API /model endpoint response contract. If confirmed, the API doc Section 7 model output contract must be updated simultaneously.

## 7.2 Model Update SLAs and Data Quality Gates

*[CHG-36: Phase 2 sport-specific data quality gate rules added.]*

| Trigger | SLA | Priority |
|---|---|---|
| Nightly scheduled run | All games updated by 06:00 UTC daily | Standard |
| Injury designation change (key player) | Model regenerated within 15 minutes | High |
| Late scratch (2 hours before game) | Model regenerated within 10 minutes | Critical |
| Weather update (6 hours before outdoor game) | Model regenerated within 20 minutes | High |
| Line movement exceeds 2 points | Model comparison refreshed within 5 minutes | Standard |
| Result ingestion | predictions table updated within 30 minutes of final whistle | Standard |
| data_quality_score < 0.70 | Output blocked. DS team alerted within 5 minutes. | High |
| data_quality_score 0.70–0.85 | Output published with data_quality_flag: true. | Standard |
| NFL referee crew assignment | Poll once daily Wednesday through Friday. | Standard |
| NBA referee crew assignment (game day AM) | Poll every 30 min 08:00–14:00 ET; every 60 min until tip-off. | Standard |
| Soccer referee assignment (EPL + WC2026 + UCL) | Poll once at 48hr before kickoff; once at 24hr before kickoff. | Standard |

**Phase 2 sport-specific data quality gate rules [CHG-36]:**

| Sport | Condition | Gate Rule | Rationale |
|---|---|---|---|
| **MLB** | `is_starting_pitcher_confirmed = false` | Output **BLOCKED entirely** — do not publish, do not flag, do not display. Set `pitcher_unconfirmed` flag. DS team alerted. | Starting pitcher is the single dominant MLB model variable. An unconfirmed pitcher model output has no brand-consistent signal value. This is stricter than the standard 0.70 block — the block is on a boolean condition, not a score. |
| **NHL** | `is_starting_goalie_confirmed = false` | `data_quality_score` capped at **0.70** (floor of FLAG band). Output published with `data_quality_flag: true` and `goalie_unconfirmed: true`. | Goalie starter is the highest-impact NHL variable but team-level Corsi/xG inputs retain some signal value. Flagging rather than blocking preserves utility while warning users. |
| **Tennis** | Either player's `surface_games_played < 10` on the match surface | `data_quality_score` capped at **0.75**. Output published with `data_quality_flag: true` and `low_surface_sample: true`. | Insufficient surface-specific sample undermines Elo reliability. Cap is above block threshold — output retains display value with appropriate user warning. |
| **NCAA Men's Basketball** | `referee_foul_rate_percentile` null at game time | `data_quality_score` capped at **0.84** — identical rule to NBA. | NCAA D1 officials data follows same model input dependency as NBA. Same cap, same vendor resolution path. |
| **Rugby** | No sport-specific gate beyond standard 0.70/0.85 thresholds. | Standard gate applies. | Rugby team-level inputs do not have a single dominant variable analogous to MLB pitcher or NHL goalie. |
| **NCAA Football (FBS)** | No sport-specific gate beyond standard thresholds. | Standard gate applies. | Starting QB status is an important input but is captured via the standard `injury_adjustment` field and the existing injury polling schedule — no additional gate required. |

## 7.3 Injury and Referee Polling — Full Schedule

*[CHG-24: All rows previously referencing "EPL or WC2026" updated to "EPL, WC2026, or Champions League."]*
*[CHG-37: Phase 2 sport polling schedules added.]*

**Phase 1 sports (live at launch):**

| Sport | Data Type | Window | Interval |
|---|---|---|---|
| NFL | Injury | Game week: Wed 00:00 – Sun 23:59 | Every 5 minutes |
| NFL | Injury | Game day pre-kickoff: 3 hours before earliest kickoff | Every 2 minutes |
| NFL | Injury | Off-season / Mon–Tue during season | Every 60 minutes |
| NFL | Referee | Game week: Wednesday through Friday | Once daily |
| NBA | Injury | Any day with 1+ scheduled NBA games | Every 5 minutes |
| NBA | Injury | Game day pre-tip-off: 3 hours before earliest tip-off | Every 2 minutes |
| NBA | Injury | Non-game days | Every 60 minutes |
| NBA | Referee | Game day morning: 08:00–14:00 ET | Every 30 minutes |
| NBA | Referee | Game day afternoon: 14:00 ET until tip-off | Every 60 minutes |
| Soccer | Injury | Match week: 72 hours before any EPL, WC2026, or Champions League match | Every 5 minutes |
| Soccer | Injury | Match day pre-kickoff: 3 hours before kickoff | Every 2 minutes |
| Soccer | Injury | Non-match days | Every 60 minutes |
| Soccer | Referee | Match week: 48 hours before each EPL, WC2026, or Champions League match | Once at 48hr mark |
| Soccer | Referee | Match week: 24 hours before each EPL, WC2026, or Champions League match | Once at 24hr mark |

> **nflreadr — Historical vs Real-Time**
> nflreadr covers historical NFL injury data for model training (S3 ingestion via Airflow). nflreadr is NOT suitable for real-time production injury polling. The 5-minute and 2-minute polling windows above must be served by the production stats vendor API (SportsDataIO or Sportradar). See Section 0 PDR-02 item 3.

**Phase 2 sports (activate at respective sport launch — document for planning):**

| Sport | Data Type | Window | Interval | Notes |
|---|---|---|---|---|
| MLB | Probable Pitchers | 48hr before game through confirmed starter | Every 30 min (48–24hr); every 5 min (24hr–game time) | Most time-critical MLB input. Confirmed starter typically released 2–4hr pre-game. If unconfirmed at model run time: output BLOCKED (Section 7.2 CHG-36). |
| MLB | IL / Day-to-Day | Game days continuous; off-days every 60 min | Every 5 min game days; every 60 min off-days | IL designations affect lineup construction and team ratings. |
| NHL | Goalie Starter | Game day from morning skate (~10:00–11:30 ET) through puck drop | Every 5 min from 09:00 ET; every 2 min from 90 min pre-puck-drop | Single highest-impact NHL variable. If unconfirmed: data_quality_score capped at 0.70 (Section 7.2 CHG-36). |
| NHL | IR / Day-to-Day | Game days continuous; off-days every 60 min | Every 5 min game days; every 60 min off-days | Key forward/defender absences affect Corsi%, xG, and totals model. |
| Tennis | Withdrawal / Retirement Risk | Match day from draw confirmation through match start | Every 60 min from draw; every 15 min within 3hr of match start | Player withdrawals between draw and match are common, particularly at multi-day tournaments. Withdrawal triggers output suppression and alert to Sharp users. No referee equivalent for tennis. |
| NCAA Football (FBS) | Injury | Game week: Mon 00:00 – Sat 23:59 | Every 5 minutes (mirrors NFL schedule) | Starting QB status is highest-priority input. Official availability reports typically released Wed–Fri. |
| NCAA Football (FBS) | Injury | Game day pre-kickoff: 3 hours before kickoff | Every 2 minutes | |
| NCAA Football (FBS) | Referee | Game week | Once daily Wed–Fri (mirrors NFL) | FBS referee crew assignments released on similar schedule to NFL. |
| NCAA Men's Basketball | Injury | Any day with 1+ scheduled games | Every 5 minutes (mirrors NBA) | |
| NCAA Men's Basketball | Injury | Game day pre-tip-off: 3 hours before tip-off | Every 2 minutes | |
| NCAA Men's Basketball | Referee | Game day morning: 08:00–14:00 ET | Every 30 minutes (mirrors NBA) | referee_foul_rate_percentile applies — same cap rule as NBA if null. |
| NCAA Women's Basketball | Injury | Tournament window only: 72 hours before each scheduled tournament game | Every 5 minutes (mirrors NBA) | Pipeline activates only during NCAA Tournament window. No polling outside tournament. |
| NCAA Women's Basketball | Injury | Tournament game day pre-tip-off: 3 hours before tip-off | Every 2 minutes | |
| Rugby | Injury / Squad | Match week: 72 hours before any scheduled match | Every 5 minutes (mirrors soccer) | Official squad announcements typically 48–72hr pre-match for international rugby. |
| Rugby | Injury / Squad | Match day pre-kickoff: 3 hours before kickoff | Every 2 minutes | |
| Rugby | Injury / Squad | Non-match days | Every 60 minutes | Covers player availability during international windows and club competition weeks. |
| Rugby | Referee | Match week: 48hr and 24hr before each match | Once at 48hr; once at 24hr (mirrors soccer) | Match official assignments released 24–48hr before fixtures. |

## 7.4 Model Versioning Protocol

- Version format: {sport}_v{major}.{minor}.{patch}  e.g. nfl_v1.2.3
- Major: Architecture change — full rebacktest + Product Lead sign-off
- Minor: Feature addition — walk-forward validation report required
- Patch: Parameter tuning — calibration check must pass
- All versions stored indefinitely in MLflow — never deleted
- Version displayed to users — full transparency
- Historical predictions retain their original model version — track record integrity

---

# 8. Non-Functional Requirements

## 8.1 Performance

| Requirement | Target | Measurement |
|---|---|---|
| Page load time (P95) | Under 2.5 seconds globally | Synthetic monitoring from US, UK, EU, AU |
| API response time (P95) | Under 300ms | API gateway metrics |
| Odds feed freshness | Under 60 seconds from source | Pipeline monitoring |
| Model output freshness | Under 6 hours (scheduled) | Airflow DAG monitoring |
| Alert delivery latency | Under 2 minutes from trigger | Alert event log |
| PWA Lighthouse score | 90+ all categories | Automated CI check |
| Core Web Vitals (LCP) | Under 2.5 seconds | Field data monitoring |

## 8.2 Availability and Reliability

| Requirement | Target |
|---|---|
| Platform uptime SLA | 99.9% monthly |
| Planned maintenance | Tuesdays 02:00–04:00 UTC |
| RTO | 15 minutes during NFL Sunday; 4 hours otherwise |
| RPO | Zero for user bet data; 1 hour for model outputs |
| Database backup | Continuous WAL archiving + daily snapshots; 30-day retention |
| Graceful degradation | Serve last known good odds if feed fails — never serve errors as data |

## 8.3 Security

- HTTPS everywhere — HSTS configured
- All secrets in AWS Secrets Manager or GCP Secret Manager — zero hardcoded credentials
- Database encryption at rest (AES-256) and in transit (TLS 1.3)
- JWT tokens: RS256 signed, 1-hour expiry, refresh token rotation
- Rate limiting: per-user and per-IP via Redis
- Input validation: Pydantic on all API inputs
- Parameterized queries only — no string concatenation in SQL
- Penetration test before launch and annually thereafter

## 8.4 Compliance

| Requirement | Implementation |
|---|---|
| GDPR consent | Cookiebot — consent at registration, timestamp recorded, immutable audit log |
| GDPR right to access | User data export endpoint — delivered within 30 days |
| GDPR right to erasure | PII removed within 72 hours; bet data anonymized |
| CCPA | Privacy policy disclosures, opt-out of marketing data sharing |
| Cookie consent | Cookiebot — geo-targeted, Google Consent Mode v2 certified |
| Age verification | Acknowledgment checkbox at registration, country-specific messaging |
| Tax collection | Stripe Tax enabled before first transaction |
| Data residency | EU user data processed and stored in EU-region infrastructure |
| Affiliate disclosure | 'Affiliate partner' label on all book links; footer disclaimer |
| Vendor DPAs | DPAs signed with all vendors processing EU user data before launch |

## 8.5 Localization

*[CHG-38: i18n string externalization mandated from day one.]*
*[CHG-39: Responsible gambling messaging extended for international markets.]*

| Requirement | Specification |
|---|---|
| Odds formats | American, Decimal, Fractional — user-selectable, platform-wide instant update |
| Timezone | All times stored UTC, displayed in user timezone with abbreviation |
| Currency | USD, GBP, EUR, AUD at launch — Stripe handles conversion |
| Date format | MM/DD/YYYY (US), DD/MM/YYYY (UK/AU/EU) based on locale |
| i18n routing | Next.js built-in i18n routing — English only at launch |

**String externalization — mandatory from day one [CHG-38]:**

All user-facing strings must be stored in locale files using the Next.js i18n key pattern (`/locales/en.json`), even though English is the only shipped locale at launch. No hardcoded string literals are permitted in frontend components. This is a TDD-enforceable NFR.

- CI pipeline must include a lint rule that fails if string literals are detected in UI components outside locale files. This check must pass before any frontend PR is merged.
- Scope: all UI copy, error messages, alert text, model explanation labels, data quality flag descriptions, responsible gambling messaging, and legal disclaimer text.
- Exclusion: code-internal strings (log messages, database values, API field names) are not subject to this rule.
- Rationale: retrofitting string externalization after a codebase is built is a high-effort, error-prone operation. The cost of doing it correctly upfront is small; the cost of not doing it is large. The first target non-English locale is **French** — triggered by Year 1 international user data, not a fixed date. French is the priority because it covers Roland Garros (tennis), Six Nations (rugby — France is a major market), and the French soccer betting market (relevant to future La Liga / Ligue 1 expansion). Spanish is the second target (Latin American soccer + rugby + Argentine rugby market).

**Responsible gambling messaging — locale-aware routing [CHG-39]:**

Responsible gambling message content and display requirements are market-specific regulatory obligations, not just UX preferences. The `country_code` field on the `users` table is the authoritative routing field.

| Market | Regulator | Required messaging / resources | Routing condition |
|---|---|---|---|
| United Kingdom | UK Gambling Commission | GamStop self-exclusion scheme; BeGambleAware (www.begambleaware.org); National Gambling Helpline 0808 8020 133 | `country_code = 'GB'` |
| Australia | State-based (varies) | Gambling Help Online (www.gamblinghelponline.org.au); 1800 858 858 | `country_code = 'AU'` |
| France | ANJ (Autorité Nationale des Jeux) | Joueurs Info Service (www.joueurs-info-service.fr); 09 74 75 13 13 | `country_code = 'FR'` |
| Ireland | Gambling Regulatory Authority of Ireland | Gamble Aware Ireland; problem gambling helpline | `country_code = 'IE'` |
| United States | NCPG | National Problem Gambling Helpline 1-800-522-4700; state-specific resources | `country_code = 'US'` (default) |
| All other markets | — | NCPG helpline as default international fallback | All other `country_code` values |

Implementation requirements:
- Responsible gambling component must display locale-appropriate content based on `country_code` at registration and in footer on all pages.
- English content for all markets at v1 launch. Translated content in French and other locales to be implemented alongside the first non-English locale release.
- Legal must confirm UK, Australian, and French messaging content meets jurisdictional requirements before those markets are actively marketed to.
- Component must be testable per-country in CI without a live user account (mock `country_code` injection required).

## 8.6 Test Coverage (TDD)

> **TDD Mandate**
> Both agent teams develop using TDD. Tests written BEFORE implementation. No feature is complete until all AC-N criteria have corresponding passing tests. CI pipeline blocks merge if coverage falls below minimum thresholds.

| Component | Minimum Coverage | Test Types Required |
|---|---|---|
| API endpoints | 90% | Unit, integration, contract |
| Model pipeline | 85% | Unit, data quality, backtesting |
| Feature store computation | 90% | Unit, regression |
| Data ingestion DAGs | 80% | Unit, integration, failure scenarios |
| Alert engine | 85% | Unit, integration, end-to-end |
| Frontend components | 75% | Unit (Jest), E2E (Playwright) |
| Authentication flows | 95% | Unit, integration, security |
| Bet tracker | 90% | Unit, integration |
| Odds calculation (vig, CLV) | 100% | Unit — mathematical precision required |
| Great Expectations suites (all DS training sources) | 100% | All suites must pass before CHG-06 checklist item is marked complete |

---

## 8.7 Observability & Monitoring

*[CHG-28: Section 8.7 added — observability instrumentation requirements.]*

This section defines what must be instrumented, tracked, and alertable. It is a technical NFR. The Management Dashboard that surfaces these signals to the Product Lead is specified separately in Section 13.

### 8.7.1 Uptime History Tracking

Per-service uptime must be recorded and queryable at daily granularity for a rolling 90-day window. Each day must carry one of four statuses: Operational, Degraded, Outage, Maintenance. The following services must each be tracked independently as distinct probes:

- API Gateway (`api.parallaxedge.com/v1`)
- Supabase (DB / Auth)
- Cloudflare CDN
- AWS / GCP Hosting
- MLflow / Model Infrastructure
- Odds Feed Pipeline
- Alert Engine
- Stripe Payments

**Data source:** Statuspage.io API or Grafana synthetic uptime probes. Both are already in the infrastructure stack (Statuspage.io: Section 11.2 checklist; Grafana: Section 11.1 and 11.2 checklists). Per-service uptime percentage over the trailing 90 days must be computable on demand.

**Alert thresholds:** services falling below 99.5% uptime (trailing 30 days) must trigger a Grafana alert to the Product Lead. Services falling below 99.0% must trigger a critical alert.

### 8.7.2 Rate Limit Monitoring Instrumentation

*Rate limit values are defined in API Requirements v1.0 Section 7 — the single source of truth. This section specifies what must be instrumented, not the limit values themselves.*

The following signals must be captured in real time from Redis and exposed to the Management Dashboard (Section 13):

- Current req/min per endpoint group, per tier (Free and Sharp)
- HTTP 429 event count per endpoint group per tier, rolling 24-hour window
- HTTP 429 events per hour (24-hour history) for bar chart rendering
- Global ceiling utilisation: Unauthenticated / Free / Sharp, rolling 1-minute peak
- Per-user and per-IP Redis enforcement operational status
- Tier access gate verification status: Free model output gate (3/day server-side counter), Free bet tracker gate (50-bet server-side counter), HTTP 429 `Retry-After` header presence

**Alert threshold:** if any endpoint group exceeds 80% of its per-tier ceiling in a rolling 1-minute window, a Grafana alert fires. If a global ceiling is breached (HTTP 429 returned), a critical alert fires immediately.

### 8.7.3 Grafana Alerting — Required Monitors

The "Grafana alerting configured for all critical monitors" checklist item in Section 11.2 must include, at minimum, the following monitors:

| Monitor | Condition | Severity |
|---|---|---|
| Platform uptime (any service) | < 99.9% MTD | Critical |
| API response time P95 | > 300ms | Warning |
| Odds feed freshness | > 60s from source | Warning |
| Model output freshness | > 6 hours (any game) | Warning |
| Data quality suppression | Any output blocked (DQ < 0.70) | Critical |
| Model regen SLA — late scratch | > 10 minutes | Critical |
| Model regen SLA — injury designation | > 15 minutes | Warning |
| Alert delivery latency | > 2 minutes | Critical |
| Rate limit — endpoint group utilisation | > 80% ceiling | Warning |
| Rate limit — global ceiling breached | HTTP 429 returned | Critical |
| MLflow / model infra | Any degraded status | Warning |
| Nightly run completion | Not complete by 06:05 UTC | Warning |

---

# 9. Wireframe Descriptions

Mobile-first. Breakpoints: mobile < 768px, tablet 768–1024px, desktop > 1024px.

## 9.1 Dashboard

*[CHG-40: Sport tabs updated for Phase 2 sports.]*

```
NAV: Logo | Games | Model | Tracker | Alerts | [Tier badge] | Avatar
HERO LEFT (60%): 'Today's Games' — 2-col card grid | sport badge | model edge pill
HERO RIGHT (40%): 'Top Value Bets' sorted by edge | Free: 3 rows, rest blurred
SPORT TABS: All | NFL | NBA | Soccer | NCAA | Tennis | Rugby
  -- Phase 2 tabs (NCAA, Tennis, Rugby) are hidden until that sport's data pipeline is live.
  -- Tab visibility is controlled by a feature flag per sport_slug, not a code deployment.
  -- 'All' tab always shows all active sports only — never shows tabs for inactive sports.
TRACK RECORD STRIP: W-L-P | Avg CLV | Brier Score | link
```

## 9.2 Game Detail

```
HEADER: Logos | Teams | Time (user TZ) | League | Status | Venue
WEATHER STRIP: All outdoor/open-roof venues across ALL sports (NFL, EPL, WC2026, UCL)
TABS: Odds | Model | Line Movement | Stats
ODDS TAB: Comparison table | Vig/no-vig strip | Free: 5 books, rest locked
MODEL TAB: Probability bar | Fair odds table | Confidence + DQ scores
  Key factors expandable (Sharp only) | [Log Bet] [Set Alert] [Share]
LINE MOVEMENT: Time series (Sharp only) | Free: blurred + upgrade CTA
STATS: Season stats side by side | H2H last 5 meetings
```

## 9.3 Bet Tracker

```
HEADER: 'My Bets' | [+ Log Bet] | Filter | Search
PERFORMANCE STRIP: Total bets | Win rate | ROI | P&L | Avg CLV (Sharp only)
BETS TABLE: Date | Game | Market | Bet | Odds | Stake | Result | P&L | CLV
  Result: Win (green) | Loss (red) | Push (grey) | Pending (amber)
FREE LIMIT BAR: 'X / 50 bets used [===---] Upgrade for unlimited'
```

## 9.4 Track Record (Public)

```
HEADER: 'Parallax Model Track Record' | 'All predictions published before game time'
SUMMARY CARDS: W-L-P | Win Rate | Avg CLV | Brier Score
FILTER BAR: Sport | Market type | Date range | Model version
PERFORMANCE CHART: ROI over time (filterable)
PREDICTIONS TABLE: Date | Game | Market | Predicted side | Model prob |
  Odds at pub (locked) | Closing odds | CLV | Result
```

---

# 10. Dependencies and Risks

## 10.1 External Dependencies

*[CHG-25: UCL xG training data source row added.]*
*[CHG-41: Phase 2 sport training data dependencies added.]*

| Dependency | Provider | Criticality | Fallback |
|---|---|---|---|
| Live odds + Pinnacle CLV | The Odds API | Critical | Last cached odds with staleness warning. Pinnacle confirmed per PDR-02 item 1. |
| NFL historical (training) | nflfastR / nflreadr (free) | Critical | MIT licensed, GitHub Actions nightly — no fallback needed |
| NFL real-time (production) | SportsDataIO or Sportradar | Critical | Delay model update; serve prior version. Decision gated on PDR-01. |
| NBA historical (dev + training) | BALLDONTLIE (free) | Critical | SportsDataIO free trial if validation fails (PDR-01). |
| NBA real-time (production) | SportsDataIO or Sportradar | Critical | Delay model update; serve prior version. |
| Soccer xG — EPL (training) | Understat (free) | Critical | Goals-based ratings as temporary fallback. |
| Soccer xG — WC2026 (training) | StatsBomb Open Data or club proxy | Critical | Club-level xG proxy per Section 0 PDB-02 Option 2. |
| **Soccer xG — Champions League (training)** | **TBD — confirmed per PDB-03** | **Critical** | **Goals-based ratings as temporary fallback pending PDB-03 resolution.** |
| Soccer live stats (production) | API-Football paid tier | Critical | API-Football free tier (100 req/day) short-term fallback. |
| Weather — all outdoor venues | Open-Meteo (if licensed) or Tomorrow.io | High | Model without weather adjustment; weather_impact: false flagged in output. |
| Authentication | Supabase | Critical | No fallback — Supabase SLA 99.9% |
| Payments + tax | Stripe + Stripe Tax | Critical | No fallback — Stripe SLA 99.99% |
| Consent management | Cookiebot | High | Manual consent flow — not sustainable beyond 24 hours |
| CDN + DDoS | Cloudflare | High | Origin server at degraded performance |
| Push notifications | Firebase FCM | Medium | Email-only fallback during FCM outage |
| **MLB historical (training)** | **pybaseball / Statcast / Retrosheet (free)** | **Phase 2 — Critical at activation** | **Goals/runs-based ratings as fallback. Retrosheet provides pre-Statcast era data.** |
| **MLB real-time (production)** | **SportsDataIO or Sportradar (official partner)** | **Phase 2 — Critical at activation** | **Delay model; serve prior version. The Odds API already covers MLB odds — no new odds vendor needed.** |
| **NHL historical (training)** | **hockeyR + MoneyPuck (free)** | **Phase 2 — Critical at activation** | **Goals-based ratings. NHL Open API for development.** |
| **NHL real-time (production)** | **SportsDataIO or Sportradar (official partner)** | **Phase 2 — Critical at activation** | **Delay model; serve prior version. The Odds API already covers NHL odds.** |
| **Tennis historical (training)** | **Jeff Sackmann Open Era dataset (GitHub — free, MIT license)** | **Phase 2 — Critical at activation** | **Reduced historical depth; surface Elo trained on fewer seasons.** |
| **Tennis real-time (production)** | **TBD — ATP/WTA official feed or SportsDataIO** | **Phase 2 — High at activation** | **Delay match output; no live scoring dependency for pre-match model.** |
| **NCAA Football historical (training)** | **cfbfastR / collegefootballdata.com API (free)** | **Phase 2 — Critical at activation** | **ESPN Stats & Info as secondary source.** |
| **NCAA Football real-time (production)** | **SportsDataIO or Sportradar** | **Phase 2 — Critical at activation** | **Delay model; serve prior version.** |
| **NCAA Men's Basketball historical (training)** | **cbbdata / Sports Reference / BigDataBall (free tier)** | **Phase 2 — Critical at activation** | **Reduced historical depth.** |
| **NCAA Men's Basketball real-time (production)** | **SportsDataIO or Sportradar** | **Phase 2 — Critical at activation** | **Delay model; serve prior version.** |
| **World Rugby historical (training)** | **ESPN Stats & Info / World Rugby Stats Centre / rugbydb (community)** | **Phase 2 — High at activation** | **Goals/points-based ratings from publicly available historical results.** |
| **World Rugby real-time (production)** | **TBD — World Rugby API (candidate) or SportsDataIO** | **Phase 2 — Critical at activation** | **World Rugby API availability and stability must be confirmed before Phase 2 contract decisions. The Odds API rugby coverage must be verified before contract extension (Section 10.2 CHG-42).** |

## 10.2 Risk Register

*[CHG-42: Phase 2 sport risks added.]*

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Open-Meteo requires commercial license | High | Medium | Hard blocker PDB-01. 2-week deadline. Default to Tomorrow.io if unresolved. |
| WC2026 xG data unavailable from Understat | High | High | Hard blocker PDB-02. StatsBomb open data is prescribed first evaluation. Club proxy is the no-cost fallback. |
| UCL xG data source not confirmed before training window | Medium | High | Hard blocker PDB-03. DS team to evaluate and confirm source before UCL model training begins. |
| BALLDONTLIE fails production validation | Medium | High | Cascade risk per PDR-01. Four downstream decisions blocked. SportsDataIO free trial begins in parallel if validation fails. |
| OQ-4 attempted before OQ-2 is resolved | Medium | Medium | Now explicit per CHG-20. OQ-4 is blocked by OQ-2 in the PM dependency map. |
| Section 7 inputs_snapshot changes missed in joint review | Medium | High | Step 2.5 joint DS + Dev review required before PRD v1.3 finalization per CHG-19. |
| Model underperforms vs market in first season | Medium | High | Focus on secondary markets; publish all predictions transparently. |
| Odds feed outage during peak NFL/NBA window | Low | High | Cache last known odds; staleness indicator; Cloudflare buffer. |
| Data quality issue causes incorrect model output | Medium | High | Great Expectations suites; two-tier DQ gate (block 0.70, flag 0.85). |
| GDPR compliance gap post-launch | Low | High | Cookiebot configured and DPAs signed per PDR-03 before any user data is collected. |
| Build timeline slips past August 2026 | Medium | Medium | Section 0 blockers resolved first. No feature additions during build phase. |
| **Tennis player data model diverges between DS and Dev teams** | **Medium** | **High** | **Tennis uses `tennis_matches` table, not `games` table (CHG-31). DS team must not write model outputs to `model_outputs` with a `game_id` FK pointing to a non-existent game row. Step 2.5 joint review must explicitly cover tennis match ID routing before Phase 2 tennis model development begins.** |
| **NCAA player props implemented without legal review** | **Medium** | **High** | **Game-level markets only at Phase 2 launch — player prop scope requires legal review across all 38+ US states with legal sports betting before implementation (Section 1.2, CHG-30). The `ncaa_props_excluded` flag in outputs is `true` at launch. A documented PRD amendment is required to change this flag. No implementation of NCAA prop functionality without that amendment and the associated legal sign-off (Section 11.3, CHG-43).** |
| **World Rugby odds liquidity insufficient for CLV calculation** | **Medium** | **Medium** | **The Odds API's rugby coverage depth (number of bookmakers, Pinnacle inclusion) must be verified before Phase 2 rugby contract extension. Pinnacle is required for CLV calculation (Section 5.4.2). If Pinnacle does not price rugby markets, CLV cannot be calculated for rugby predictions — the track record and bet tracker CLV fields would be null for rugby bets. Verify before committing to rugby Phase 2 launch date.** |
| **Neutral-site outdoor venue weather pipeline silent failure** | **Medium** | **Medium** | **Weather pipeline must use `neutral_venue_lat/lng` from the `games` table for neutral outdoor venues, not team venue coordinates (CHG-34). If `neutral_venue_lat/lng` are null when `is_neutral_site = true` AND venue is outdoor, the weather query silently uses incorrect coordinates. Dev Team must seed neutral venue coordinates for all known scheduled outdoor neutral-site games before pipeline build. Great Expectations suite must validate that `neutral_venue_lat/lng` is populated for all games where `is_neutral_site = true` and weather is expected.** |
| **i18n string hardcoding creates retrofit debt** | **Low (mitigated)** | **Medium** | **Mitigated by CHG-38 mandate: all strings in locale files from day one; CI lint rule blocks hardcoded literals. Risk is residual only if CI rule is bypassed or exempted without Product Lead approval.** |
| **[CHG-44] Commercial API data re-sale license violation** | **High** | **Critical** | **Multiple data inputs (commercial stats vendors, odds APIs, scraped sources) carry license terms that prohibit downstream re-sale or redistribution to third parties. Building a commercial API that exposes this data — even indirectly via derived outputs — without completing a data license audit first creates material IP and contract breach risk. Hard blocker: data license audit must be completed by legal counsel before any commercial API architecture or build work begins. See Section 14.** |
| **[CHG-50] Commercial API legal review delayed past Phase 3 window** | **Medium** | **Medium** | **Legal review lead times for data licensing opinions are typically 3–6 months. If the audit is not initiated until Phase 3 is actively being scoped, it will delay commercial API development by that same margin. Recommended start: no later than 60 days post-Phase-1A launch (approximately August 2026). This does not require engineering engagement at that point — legal workstream only. See Section 14.1 and Section 11.3.** |

---

# 11. Pre-Launch Checklist

> **Checklist Structure — v1.8 Update [CHG-45]**
> Section 0 Pre-Development Requirements must be resolved BEFORE this checklist is started.
>
> **Two-tier gate structure (added v1.8):**
> - **June 11 gate (Phase 1A):** Items marked "Critical — June 11 gate" must be complete before the platform is publicly accessible on June 11, 2026. These cover the full product scope: auth, WC2026 model output, odds, bet tracker, alerts, and track record.
> - **Post-Phase-1A expansion:** Items marked with a phase (1B, 1C, 1D) or "post-Phase-1A target" are not June 11 launch blockers. They are required before the relevant sport or feature goes live.
>
> Critical items with no phase qualifier: must be complete before free tier is publicly accessible. High items: must be complete or have a documented exception from the Product Lead.

## 11.1 Data and Model

*[CHG-26: UCL historical data ingestion checklist item added.]*
*[CHG-43: Phase 2 sport planning items added.]*

| Item | Priority | Owner |
|---|---|---|
| **[CHG-46] [PDB-01] Open-Meteo licensing confirmed OR Tomorrow.io contracted — CRITICALLY OVERDUE — resolve this week — June 11 gate** | **Critical — June 11 gate** | **Legal + Engineering** |
| **[CHG-46] [PDB-02] WC2026 xG source confirmed — StatsBomb evaluation complete — CRITICALLY OVERDUE — resolve this week — June 11 gate** | **Critical — June 11 gate** | **DS Team** |
| **[PDB-03] UCL xG source confirmed — DS team evaluation complete before UCL model training begins** | **Critical** | **DS Team** |
| [CHG-19] Step 2.5 joint DS + Dev Section 7 review completed after PDB-01 and PDB-02 close | Critical | Both Teams |
| [PDR-01] BALLDONTLIE data quality validated — SportsDataIO/Sportradar decision made | Critical | DS Team + Engineering |
| NFL historical data ingested — 5 seasons minimum (nflfastR / nflreadr) | Critical | DS Team |
| NBA historical data ingested — 5 seasons minimum (BALLDONTLIE) | Critical | DS Team |
| EPL historical data ingested — 5 seasons minimum (Understat / FBref) | Critical | DS Team |
| WC2026 historical xG data ingested — source confirmed per PDB-02 | Critical | DS Team |
| **UCL historical xG data ingested — 5 seasons minimum — source confirmed per PDB-03** | **Critical** | **DS Team** |
| NFL model v1 backtested with walk-forward validation | Critical | DS Team |
| NBA model v1 backtested with walk-forward validation | Critical | DS Team |
| Soccer model v1 (EPL + WC2026 + Champions League) backtested with walk-forward validation | Critical | DS Team |
| Model calibration check passing (Brier score within targets per Section 2.2) | Critical | DS Team |
| Interface contract validated end-to-end between DS and Dev teams | Critical | Both Teams |
| Great Expectations suites written and passing for all DS training sources | High | DS Team |
| Model monitoring dashboard live in Grafana | High | DS Team |
| Drift detection configured and tested | High | DS Team |
| Referee data bundling confirmed with chosen stats vendor (after PDR-01 resolved) | High | Engineering |
| Pinnacle closing line confirmed in chosen odds vendor feed (independent — run now) | Critical | Engineering |
| Injury and referee polling DAGs live with dynamic frequency scheduling | Critical | DS Team |
| Two-tier data quality gate tested: block at 0.70, flag at 0.85 | Critical | DS Team |
| **[PHASE 2 PLANNING — CHG-43] MLB: confirm pybaseball/Statcast sufficiency for training vs paid Statcast feed requirement; confirm SportsDataIO or Sportradar as production vendor; confirm probable pitcher polling DAG design** | **Phase 2 gate** | **DS Team + Engineering** |
| **[PHASE 2 PLANNING — CHG-43] NHL: confirm NHL Open API stability for development; confirm SportsDataIO or Sportradar as production vendor; confirm goalie starter polling DAG design and blocked-output rule** | **Phase 2 gate** | **DS Team + Engineering** |
| **[PHASE 2 PLANNING — CHG-43] Tennis: confirm Jeff Sackmann dataset coverage and quality for Elo training; confirm tennis real-time data vendor (ATP/WTA feed or SportsDataIO); Step 2.5-equivalent joint review of tennis_matches schema and player_ratings interface contract** | **Phase 2 gate** | **DS Team + Engineering** |
| **[PHASE 2 PLANNING — CHG-43] NCAA Football (FBS): confirm cfbfastR / collegefootballdata.com coverage for 5+ seasons training; confirm FBS-only scope enforcement in data pipeline (no FCS ingestion); confirm production stats vendor covers FBS referee data** | **Phase 2 gate** | **DS Team + Engineering** |
| **[PHASE 2 PLANNING — CHG-43] NCAA Men's Basketball: confirm cbbdata / Sports Reference coverage for 5+ seasons training; confirm referee foul rate percentile available for NCAA D1 officials from chosen stats vendor** | **Phase 2 gate** | **DS Team + Engineering** |
| **[PHASE 2 PLANNING — CHG-43] NCAA Women's Basketball (Tournament only): confirm data source coverage for March Madness historical results and team ratings; confirm pipeline activates only for tournament window (no full-season ingestion at Phase 2); confirm same-vendor coverage as Men's programme to avoid separate contract** | **Phase 2 gate** | **DS Team + Engineering** |
| **[PHASE 2 PLANNING — CHG-43] World Rugby: confirm World Rugby API or alternative for real-time production data; confirm The Odds API rugby coverage includes Pinnacle (required for CLV — see Section 10.2 CHG-42); confirm historical data source quality for team ratings model** | **Phase 2 gate** | **DS Team + Engineering** |

## 11.2 Product and Engineering

*[CHG-43: Neutral venue coordinates and i18n CI check items added.]*

| Item | Priority | Owner |
|---|---|---|
| Test coverage minimums passing in CI for all components (Section 8.6) | Critical | Dev Team |
| All TDD acceptance criteria (AC-N) passing for US-001 through US-012 | Critical | Dev Team |
| HTTPS enforced — HSTS configured | Critical | Dev Team |
| Cookiebot consent flow tested: GDPR geo-targeting, CCPA, audit logging verified | Critical | Dev Team |
| Stripe Tax enabled and verified with test transactions before any live payments | Critical | Dev Team |
| Age verification flow tested across jurisdictions | Critical | Dev Team |
| Supabase auth tested: email + Google OAuth, account merging, 5-session limit | Critical | Dev Team |
| Rate limiting tested per-endpoint-group per tier (API Requirements v1.0 Section 7) | Critical | Dev Team |
| Alert delivery SLA tested: 2-minute end-to-end via FCM confirmed | Critical | Dev Team |
| weather_id FK populated for all outdoor/open-roof venues: NFL, EPL, WC2026, UCL | High | Dev Team |
| **[CHG-34, CHG-43] neutral_venue_lat/lng seeded for all known scheduled outdoor neutral-site games (WC2026 venues, UCL final site, NCAA bowl game sites). Great Expectations check confirms no null neutral_venue_lat/lng for outdoor neutral-site games before pipeline build.** | **High** | **Dev Team** |
| **[CHG-38, CHG-43] i18n string externalization CI lint rule active — build fails on hardcoded string literals in UI components. Confirmed passing before first frontend PR merge.** | **High** | **Dev Team** |
| **[CHG-39, CHG-43] Responsible gambling component tested for all routed markets (US, GB, AU, FR, IE) using mock country_code injection. English content confirmed for all markets at launch.** | **High** | **Dev Team** |
| Cloudflare CDN and DDoS protection configured | High | Dev Team |
| Statuspage.io live and integrated | High | Dev Team |
| Grafana alerting configured for all critical monitors | High | Dev Team |
| Database backups verified with test restore | High | Dev Team |
| PWA manifest and service worker — Lighthouse 90+ verified | High | Dev Team |
| Core Web Vitals passing in production | High | Dev Team |
| SEO: sitemap, robots.txt, structured data, meta tags verified | High | Dev Team |
| [PDR-02 item 4] Concurrent user volume estimated and validated against vendor QPS limits | High | Engineering |
| **[CHG-29] Management Dashboard live and accessible to Product Lead at internal route — all 7 panels rendering with live data** | **High** | **Dev Team** |
| **[CHG-28] Rate limit monitoring verified against live Redis counters in staging — per-endpoint, per-tier utilisation and 429 event log confirmed operational** | **High** | **Dev Team** |

## 11.3 Business and Legal

*[CHG-27: API-Football scope confirmation item updated to include Champions League.]*
*[CHG-43: NCAA player prop legal review item and rugby odds verification item added.]*

| Item | Priority | Owner |
|---|---|---|
| parallaxedge.com domain registered and secured | Critical | Product Lead |
| @parallaxedge handles secured: X, Instagram, TikTok, LinkedIn, YouTube, Discord | Critical | Product Lead |
| Trademark application filed for 'Parallax' in relevant classes | Critical | Product Lead |
| Privacy policy live and reviewed by legal counsel | Critical | Product Lead |
| Terms of service live and reviewed by legal counsel | Critical | Product Lead |
| **[CHG-48] Affiliate disclosure infrastructure in place: affiliate label component, footer disclaimer, disclosure rendering on all book link pages — zero active partner agreements required at Phase 1A (June 11) launch** | **Critical — June 11 gate** | **Dev Team + Product Lead** |
| **[CHG-48] Affiliate agreements signed — minimum 3 Tier 1 sportsbooks — target within 60 days of Phase-1A launch (by approximately August 10, 2026). Not a June 11 launch gate.** | **High — post-Phase-1A target** | **Product Lead** |
| [PDR-03] DPAs signed with all vendors processing EU user data | Critical | Legal |
| Cookiebot account created — geo-targeting and audit logging confirmed with legal | Critical | Legal + Engineering |
| Track record page live with first predictions published before any paid tier opens | Critical | Product Lead |
| Methodology page live | High | Product Lead |
| Intercom customer support configured with tier-aware routing | High | Product Lead |
| **Soccer competition scope communicated to API-Football for correct tier selection (EPL + WC2026 + Champions League)** | **High** | **Engineering** |
| **[CHG-43] NCAA player props legal review: legal counsel to confirm the permissible scope of NCAA betting markets across all active US sports betting jurisdictions. At Phase 2 launch, NCAA model output covers game-level markets only (spread, moneyline, totals) — player props require a separate legal review before any implementation. The review must confirm: (a) which US states permit or restrict college athlete props; (b) whether the platform's analytics-layer classification provides any protection; (c) the specific markets that are safely in scope for a future prop expansion. Review must be documented and a PRD amendment issued before any NCAA prop feature work begins.** | **Phase 2 gate — High** | **Legal** |
| **[CHG-43] World Rugby odds coverage: verify with The Odds API that Pinnacle is included in rugby market coverage before Phase 2 rugby contract extension. Pinnacle is required for CLV calculation (Section 5.4.2). If Pinnacle does not price rugby markets, CLV is unavailable for rugby predictions — this must be disclosed in the methodology page and bet tracker before rugby launches.** | **Phase 2 gate — High** | **Engineering + Product Lead** |
| **[CHG-43] Responsible gambling messaging: legal counsel to confirm UK (GamStop/BeGambleAware), Australian (Gambling Help Online), and French (ANJ/Joueurs Info Service) English-language content meets jurisdictional requirements before those markets are actively marketed to. French content specifically required before any paid French-language locale release.** | **High** | **Legal** |
| **[CHG-44, CHG-50 — PHASE 3 PLANNING] Commercial API data license audit: before any commercial API architecture, pricing, or build work begins, legal counsel must complete a full audit of all data input licenses (commercial stats vendors, odds APIs, open-source sources) to determine which data flows can legally appear — directly or derivatively — in a commercially licensed API output. This audit gates the entire Phase 3 commercial API workstream. No engineering scoping for the commercial API may begin until the audit is complete and the permissible product boundary is confirmed in writing. See Section 14 for full requirements. [CHG-50] Recommended initiation: no later than 60 days post-Phase-1A launch (approximately August 2026). Legal workstream only at initiation — no engineering involvement required until audit is complete.** | **Phase 3 gate — Critical; recommended start August 2026** | **Legal** |

---

# 12. Document Revision History

| Version | Date | Summary |
|---|---|---|
| 1.0 | March 2026 | Initial PRD. Free + Sharp, NFL/NBA/Soccer, Web + PWA. |
| 1.1 | March 2026 | 12 changes from API Requirements v0.3 review. Cookiebot, two-tier DQ gate, alert SLA 2 min, soccer scope confirmed, weather_id scope, referee polling, AC numbering. |
| 1.2 | March 2026 | 6 changes from API Requirements v0.4 review. Section 0 Pre-Development Requirements added (CHG-18). WC2026 xG prescribed (CHG-13). Open-Meteo Critical blocker (CHG-14). BALLDONTLIE cascade mapped (CHG-15). Rate limit convention (CHG-16). Soccer referee polling (CHG-17). |
| 1.3 | March 2026 | 3 changes from sequencing review feedback. CHG-19: Steps 1+2 parallelized with hard relative deadlines; Step 2.5 joint Section 7 review gate added. CHG-20: OQ-4 dependency on OQ-2 corrected — referee bundling is sequential, not parallel. CHG-21: Cross-reference lock convention added to Document Control. |
| 1.4 | March 2026 | 7 changes from Champions League scope lock. CHG-22: UCL promoted from stretch goal to committed launch scope — header and Section 1.2 updated. CHG-23: PDB-03 added — UCL xG data source hard blocker, open-ended evaluation. CHG-24: Section 7.3 polling schedule extended to include UCL. CHG-25: Section 10.1 UCL xG dependency added. CHG-26: Section 11.1 UCL data ingestion checklist item added. CHG-27: Section 11.3 API-Football scope confirmation updated to include UCL. |
| 1.5 | March 2026 | 2 changes from Management Dashboard specification. CHG-28: Section 8.7 added — Observability & Monitoring NFR. CHG-29: Section 13 added — Management Dashboard standalone spec, 7 panels, full wireframe. Section 11.2 updated with 2 new High-priority checklist items. |
| 1.6 | March 2026 | 14 changes from sport expansion, schema gap remediation, and i18n foundation review. CHG-30: Phase 2 sport scope confirmed — MLB, NHL, Tennis (ATP/WTA/Grand Slams), NCAA Football (FBS only; FCS Phase 3), NCAA Men's Basketball (D1 full season), NCAA Women's Basketball (March Madness / Tournament only; full season Phase 3), World Rugby (Six Nations, Rugby Championship, Rugby World Cup, URC, Premiership, Top 14) — all season-calendar-gated. NCAA game-level markets only at launch; player prop expansion gated on legal review. CHG-31: Tennis schema — new `tennis_matches`, `players`, `tennis_odds`, `player_ratings` tables. CHG-32: `games.week` nullability documented. CHG-33: `odds.market_type` enum extended. CHG-34: Neutral-site venue weather gap resolved — `neutral_venue_lat/lng` added to `games`. CHG-35: `inputs_snapshot` keys defined for all Phase 2 sports. CHG-36: Phase 2 DQ gate rules. CHG-37: Polling schedule extended for all Phase 2 sports. CHG-38: i18n string externalization mandated. CHG-39: Responsible gambling locale routing. CHG-40: Dashboard sport tabs updated. CHG-41: External dependencies extended. CHG-42: Risk register updated. CHG-43: Pre-launch checklist updated. |
| 1.7 | March 2026 | 1 change. CHG-44: Section 14 added — Phase 3 commercial API licensing specification. Covers data license audit hard blocker (per-source risk assessment for all pipeline inputs), permissible product boundary (Boundary A: model outputs only; Boundary B: enriched outputs subject to audit clearance), technical architecture requirements (API key management, usage metering, metered billing, commercial rate limiting, audit log, developer portal, data provenance tagging), endpoint design principles, indicative pricing models (per-call, annual flat, revenue share, white label), and legal requirements before commercial API launch (commercial ToS, MSA template, IP ownership opinion, competitor clause, export control). Section 1.2 Revenue row corrected — API licensing moved from Phase 2 to Phase 3. Section 10.2 risk register updated with data re-sale license violation risk (High likelihood, Critical impact). Section 11.3 Phase 3 planning item added gating all commercial API engineering on legal audit completion. |
| **1.8** | **March 2026** | **6 changes. CHG-45: Launch milestone resequencing — June 11, 2026 confirmed as Phase 1A full-product launch date (WC2026 soccer only); Phase 1B = EPL + UCL (August 2026); Phase 1C = NFL (September 4, 2026); Phase 1D = NBA (October 2026). Header, Section 1.2 scope table, Section 2.1 business goals, and Section 11 checklist preamble updated. CHG-46: PDB-01 (Open-Meteo) and PDB-02 (WC2026 xG) escalated to CRITICALLY OVERDUE with immediate resolution directive and escalation paths — both original 2-week deadlines have passed with June 11 now confirmed. CHG-47: Section 1.2 scope table restructured — Phase 1 column split into Phase 1A/1B/1C/1D columns reflecting confirmed deployment sequence. CHG-48: Affiliate agreement requirement split — infrastructure (disclosure label, component, footer) required at June 11; active partner agreements deferred to post-Phase-1A target (within 60 days). Section 11.3 checklist updated accordingly. CHG-49: user_bets table (Section 4.1.15) — match_table VARCHAR(30) NOT NULL DEFAULT 'games' discriminator column added to eliminate silent join ambiguity between games and tennis_matches tables. Application layer population requirement and Great Expectations validation check documented. CHG-50: Commercial API data license audit given recommended start date of no later than 60 days post-Phase-1A launch (approximately August 2026) to avoid compressing Phase 3 development window. Section 10.2 risk register and Section 14.1 standing convention updated.** |

---

# 13. Management Dashboard

*[CHG-29: Section 13 added — standalone internal tooling specification.]*

The Management Dashboard is an internal, Product Lead–only interface surfacing real-time technical and business performance. It is not user-facing. It is a required pre-launch deliverable (Section 11.2). The observability instrumentation that feeds it is specified in Section 8.7.

## 13.1 Access Control

The Management Dashboard is served at a non-public internal route (e.g. `/internal/dashboard`). Access is restricted by IP allowlist or HTTP Basic Auth — Product Lead's discretion. No subscription tier logic applies. The route must never be indexed by search engines (`X-Robots-Tag: noindex, nofollow`). It must not appear in `sitemap.xml`.

## 13.2 Technical Requirements

- Desktop-only. Minimum viewport: 1200px. No responsive breakpoints required below 1200px.
- Data refreshed on each full page load. No WebSocket / polling requirement for v1 — a manual refresh is acceptable.
- No user authentication beyond the access control in Section 13.1.
- All monetary values displayed in USD.
- All timestamps displayed in UTC.

## 13.3 Panel Specifications

### Panel 1 — KPI Strip

Six cards displayed in a single row. Each card shows: current value, month-over-month delta, and target or ceiling.

| Card | Metric | Data Source | Target / Ceiling |
|---|---|---|---|
| MRR | Current month subscription + affiliate net revenue | Stripe API | $20,000 @ 6 months post-launch |
| Paid Subscribers | Sharp tier subscribers, EOP current month | Supabase `users` table | 500 @ 3 months; 2,604 @ May 2027 |
| Total Registered | All registered users | Supabase `users` table | 5,000 @ 3 months post-launch |
| Affiliate Revenue | Current month affiliate commissions | Internal affiliate ledger | $5,000/month @ 6 months |
| Monthly Churn | Paid cancellations ÷ prior-month paid base | Stripe API | Ceiling: 5.0% |
| Free-to-Paid Conversion | New paid this month ÷ new free registrations | Supabase + Stripe | Target: 5–8% |

### Panel 2 — Revenue & Subscriber Build

Two side-by-side charts spanning the full FY Jun 2026 – May 2027 projection window.

Left chart: monthly revenue stacked bar (subscription net + affiliate). Right chart: paid subscriber EOP per month. Both charts: historical months rendered at full opacity; projected months rendered at reduced opacity with dashed outline. Below the subscriber chart: current churn rate and current F→P conversion rate displayed as highlighted stat boxes.

Data source: Stripe API (actuals) + Section 5 pro forma table (projections).

### Panel 3 — Model Performance

Three columns:

**Left — Brier scores and CLV:**
Horizontal fill bars for NFL, NBA, and Soccer Brier scores showing current value vs target ceiling. CLV Rate fill bar vs 55% target. Calibration Error fill bar vs 0.025 ceiling. Bars colour-coded: green = passing, amber = within 10% of threshold, red = breached.

**Centre — Data Quality Gate (today):**
Three count tiles: Pass (DQ > 0.85) / Flagged (DQ 0.70–0.85) / Suppressed (DQ < 0.70). Below tiles: model update SLA compliance status per trigger type (Section 7.2), with pass/fail indicator for each.

**Right — Active model versions and polling:**
Active model version string per sport (format per Section 7.4). Current injury polling intervals per sport. Odds feed latency (rolling average, last 10 refreshes).

Data source: MLflow (Brier scores, CLV, calibration, model versions), `model_outputs` table (DQ gate counts), Airflow DAG logs (SLA compliance), Redis / pipeline logs (feed latency).

### Panel 4 — Infrastructure & System Health

Two columns.

**Left:** MTD platform uptime gauge (circular). P95 API response time. P95 page load time. Lighthouse PWA score. Per-service status list: each service shows a coloured dot (green / amber / red), service name, and current status string. Services: API Gateway, Supabase, Cloudflare CDN, AWS/GCP Hosting, MLflow, Odds Feed Pipeline, Alert Engine, Stripe Payments.

**Right:** Data pipeline live event feed — last 10 events in reverse chronological order. Each entry: UTC timestamp, status dot, source system, event description. Event types to capture: odds feed refresh, injury designation change ingested, model regen triggered and outcome, DQ gate flag or suppression event, nightly run completion.

Data source: Section 8.7.1 uptime probes (Statuspage.io / Grafana), API gateway metrics (response time), Airflow event log (pipeline feed).

### Panel 5 — Service Uptime History (90 days)

Full-width panel. Per-service row for each of the 8 services defined in Section 8.7.1. Each row: service name, 90 day-blocks (one block = one calendar day, coloured by status), trailing 90-day uptime percentage. Legend: Operational (green) / Degraded (amber) / Outage (red) / Maintenance (slate). Day axis: 90 days ago → Today.

Colouring rules for uptime percentage: ≥ 99.5% green; 99.0–99.5% amber; < 99.0% red.

Data source: Section 8.7.1 uptime tracking (Statuspage.io API or Grafana probe history).

### Panel 6 — Rate Limit Monitoring

*Rate limit values displayed here are sourced from Redis counters. The canonical limit values are defined in API Requirements v1.0 Section 7.*

Four sub-panels arranged in a 2×2 grid:

**Top left — Free Tier per endpoint group:** For each endpoint group: name, route, horizontal fill bar (current req/min ÷ Free ceiling), colour-coded (green < 55%, amber 55–80%, red > 80%), HTTP 429 active badge if at ceiling. Tier-blocked endpoints (Model Output, Alerts) labelled explicitly as blocked.

**Top right — Sharp Tier per endpoint group:** Same structure against Sharp ceilings.

**Bottom left — 429 Throttle Events (24h):** Hourly bar chart of HTTP 429 events (last 24 hours). Below chart: count breakdown by tier (Free / Sharp) and auth lockout count. Top offending endpoint groups listed by 429 event count.

**Bottom right — Global Ceiling Utilisation:** Fill bars for Unauthenticated / Free / Sharp global ceilings (current peak req/min ÷ ceiling). Redis enforcement operational status (per-user and per-IP). Tier access gate verification list: Free model output gate (3/day), Free bet tracker gate (50 bets), HTTP 429 `Retry-After` header confirmed.

Data source: Section 8.7.2 Redis instrumentation.

### Panel 7 — Financial Detail & Affiliates

Two columns.

**Left — YTD Revenue Table:** Month-by-month table from Section 5.1 schema: gross subscription revenue, net subscription revenue, affiliate revenue, total net revenue, EBITDA. Current month row highlighted. FY totals row at bottom. Below table: YTD gross margin, FY target gross margin, current monthly cost of revenue.

**Right — Affiliate Partners:** List of affiliate partners with: name, tier (Tier 1 / Tier 2), status (Active / Pending / Prospecting), CPA rate or revenue share. Alert displayed if Active partner count < 3 (minimum required per Section 11.3).

Below affiliate list: **Active Alerts panel.** Aggregates all active system and business alerts colour-coded by severity: Warning (amber) / Info (cyan) / OK (green). Sources: affiliate agreement count, model SLA breaches, rate limit threshold breaches, DPA signing status, open pre-launch checklist items flagged as Critical.

Data source: Stripe API + internal affiliate ledger (financial), internal affiliate status record (partners), aggregated from Panels 1–6 (alerts).

## 13.4 Wireframe

```
HEADER: [Parallax △ logo] PARALLAX EDGE | Management Console — Internal
        [● LIVE]  [UTC clock — updates every second]

─────────────────────────────────────────────────────────────────────────
SECTION 01 — KEY PERFORMANCE INDICATORS
─────────────────────────────────────────────────────────────────────────
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  MRR     │ │  Paid    │ │  Total   │ │  Affil.  │ │  Churn   │ │  F→P     │
│  $28,455 │ │  Subs    │ │  Reg.    │ │  Rev     │ │  3.9%    │ │  Conv    │
│          │ │  1,514   │ │  6,032   │ │  $977    │ │          │ │  4.1%    │
│ ↑+16.3%  │ │ ↑+208    │ │ ↑+541    │ │ ↑+$196   │ │ — stable │ │ ↑+0.2pt  │
│ Tgt $20k │ │ Tgt 500✓ │ │ Tgt 5k✓  │ │ Tgt $5k  │ │ Max 5.0% │ │ Tgt 5–8% │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘

─────────────────────────────────────────────────────────────────────────
SECTION 02 — REVENUE BUILD (left) | SUBSCRIBER BUILD (right)
─────────────────────────────────────────────────────────────────────────
┌──────────────────────────────────┐ ┌──────────────────────────────────┐
│ Monthly Revenue (Jun 26–May 27)  │ │ Paid Sharp Subscribers EOP       │
│ Stacked bars: sub + affiliate    │ │ Bar per month                    │
│ Projected months: faded          │ │ Projected months: faded/outlined │
│                                  │ ├──────────────┬───────────────────┤
│                                  │ │ Churn  3.9%  │ F→P Conv  4.1%   │
└──────────────────────────────────┘ └──────────────┴───────────────────┘

─────────────────────────────────────────────────────────────────────────
SECTION 03 — MODEL PERFORMANCE
─────────────────────────────────────────────────────────────────────────
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│ Brier NFL  [====] ✓ │ │ DQ Gate — Today     │ │ Active Models       │
│ Brier NBA  [====] ✓ │ │ ┌─────┬──────┬────┐ │ │ nfl_v1.2.1  Active │
│ Brier SOC  [====] ✓ │ │ │ 39  │  8   │  1 │ │ │ nba_v1.1.3  Active │
│ CLV Rate   [====] ✓ │ │ │PASS │FLAG  │BLK │ │ │ soccer_v1.0.8 Actv │
│ Cal. Error [====] ✓ │ │ └─────┴──────┴────┘ │ ├─────────────────────┤
│                     │ │ SLA Compliance:     │ │ Injury Polling      │
│                     │ │ Nightly run    ✓    │ │ NFL game week 5min  │
│                     │ │ Inj. regen     ✓    │ │ NBA game day  5min  │
│                     │ │ Late scratch   ✓    │ │ Soccer 72h    5min  │
│                     │ │ Odds refresh   ⚠    │ │ Feed latency: 52s   │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘

─────────────────────────────────────────────────────────────────────────
SECTION 04 — INFRASTRUCTURE & PIPELINE
─────────────────────────────────────────────────────────────────────────
┌──────────────────────────────────┐ ┌──────────────────────────────────┐
│ Uptime (MTD)  [◎ 99.9%]         │ │ Pipeline Feed                    │
│ API P95: 241ms  Page P95: 1.9s  │ │ 14:32 ● Odds API — refresh ok   │
│ Lighthouse: 94  Model up: 99.7% │ │ 14:28 ◑ NBA Referee missing      │
│                                  │ │ 14:15 ● API-Football — ok        │
│ ● API Gateway      Operational  │ │ 13:58 ✕ NBA suppression DQ 0.62  │
│ ● Supabase         Operational  │ │ 13:45 ● NFL Injury ingested       │
│ ● Cloudflare CDN   Operational  │ │ 13:30 ● Tomorrow.io — ok         │
│ ● AWS/GCP          Operational  │ │ 06:01 ● Nightly run complete      │
│ ● Stripe           Operational  │ │                                   │
│ ◑ MLflow           Degraded     │ │                                   │
└──────────────────────────────────┘ └──────────────────────────────────┘

─────────────────────────────────────────────────────────────────────────
SECTION 05 — SERVICE UPTIME HISTORY — LAST 90 DAYS
─────────────────────────────────────────────────────────────────────────
                [90d ago ←──────────────────────────────────── Today]
API Gateway     [██████████████████████████████████████████▒█] 99.89%
Supabase        [████████████████████████████████████████████] 100.0%
Cloudflare CDN  [████████████████████████████████████████████] 100.0%
AWS/GCP Hosting [████████████████████████████████████████▒██] 99.78%
MLflow          [████████████████████████████████████▒▒▓▒███] 98.89%
Odds Pipeline   [██████████████████████████████████████▒█████] 99.56%
Alert Engine    [████████████████████████████████████████▒███] 99.67%
Stripe          [████████████████████████████████████████████] 100.0%
Legend: █ Operational  ▒ Degraded  ✕ Outage  ▓ Maintenance

─────────────────────────────────────────────────────────────────────────
SECTION 06 — RATE LIMIT MONITORING
─────────────────────────────────────────────────────────────────────────
┌──────────────────────────────────┐ ┌──────────────────────────────────┐
│ FREE TIER  [60 req/min global]   │ │ SHARP TIER [300 req/min global]  │
│                                  │ │                                  │
│ Auth          [=] 1/5            │ │ Auth          [=]   2/5          │
│ Games List    [====] 6/10        │ │ Games List    [===] 11/30        │
│ Live Odds     [=========] 9/10 ⚠│ │ Live Odds     [===] 38/60        │
│ Model Output  BLOCKED            │ │ Model Output  [===] 14/30        │
│ Bet Write     [=] 3/20           │ │ Bet Write     [===] 22/60        │
│ Bet Perf.     [=] 1/5            │ │ Bet Perf.     [==]   6/20        │
│ Alerts        BLOCKED            │ │ Alerts        [==]   8/30        │
│ Track Record  [====] 12/30       │ │ Track Record  [=]    5/30        │
└──────────────────────────────────┘ └──────────────────────────────────┘
┌──────────────────────────────────┐ ┌──────────────────────────────────┐
│ 429 Events — Last 24h            │ │ Global Ceiling Utilisation       │
│ [bar chart: hourly 00:00–now]    │ │ Unauthenticated  [=]   4/20      │
│ Free: 9  Sharp: 5  Lockouts: 0   │ │ Free — Global    [====] 31/60    │
│ Top: GET /games/{id}/odds (Free) │ │ Sharp — Global   [===] 106/300   │
└──────────────────────────────────┘ │ Redis per-user:   ● Active       │
                                     │ Redis per-IP:     ● Active       │
                                     │ Free model gate:  ● Active       │
                                     │ Free bet gate:    ● Active       │
                                     │ 429 Retry-After:  ● Verified     │
                                     └──────────────────────────────────┘

─────────────────────────────────────────────────────────────────────────
SECTION 07 — FINANCIAL DETAIL & AFFILIATES
─────────────────────────────────────────────────────────────────────────
┌──────────────────────────────────┐ ┌──────────────────────────────────┐
│ YTD Revenue (Jun–Dec 2026)       │ │ Affiliate Partners               │
│ Month  GrossSub  NetSub  Aff  Net│ │ FanDuel    Tier1  ● Active $150  │
│ Jun-26  $950  $907   —   $907    │ │ DraftKings Tier1  ● Active $125  │
│ Jul-26  ...                      │ │ BetMGM     Tier1  ◑ Pending      │
│ ...                              │ │ Caesars    Tier2  ○ Prospect     │
│ Dec-26  $28,766 $27,478 $977 ▶   │ │ ESPN Bet   Tier2  ○ Prospect     │
│ YTD Gross Margin: 94.8%          │ ├──────────────────────────────────┤
│ FY Target Margin: 96.1%          │ │ ⚠ BetMGM unsigned — need 3 min  │
│ Monthly CoR: $813                │ │ ⚠ MLflow latency elevated        │
│                                  │ │ ✓ Cookiebot GDPR compliant       │
│                                  │ │ ℹ WC2026 xG source open (item 9) │
└──────────────────────────────────┘ └──────────────────────────────────┘
```

---

# 14. Phase 3 — Commercial API Licensing

*[CHG-44: Section 14 added — Phase 3 commercial API licensing specification.]*

This section defines the requirements, constraints, and legal gates for a commercially licensed external API — the product through which ParallaxEdge model outputs are sold to third parties such as media companies, fantasy platforms, betting operators, and other analytics products. This is a Phase 3 workstream. No engineering, architecture, or pricing work for the commercial API may begin until the hard blocker in Section 14.1 is resolved.

---

## 14.1 Hard Blocker — Data License Audit

> **⛔ DO NOT BEGIN ANY COMMERCIAL API WORK UNTIL THIS IS RESOLVED**
>
> ParallaxEdge ingests data from multiple third-party sources to train and run its models. The license terms governing those inputs determine what can legally appear — directly or in derived form — in a commercially licensed API output. This is not a minor administrative step. It is the foundational legal question on which the entire commercial API product depends.
>
> **Required action:** Legal counsel must complete a full data license audit covering every data source currently in the pipeline. The audit must answer, for each source:
> 1. Does the license permit commercial re-sale or re-distribution of the data or derivatives of it?
> 2. Does the license permit inclusion in a product sold to competitors or companies in adjacent markets?
> 3. Are there attribution, display, or watermarking requirements that would apply to API outputs?
> 4. Does the license require notification to or approval from the data provider before commercial API launch?
>
> **Sources requiring audit (minimum):**
>
> | Source | Current License Classification | Re-sale Risk Assessment |
> |---|---|---|
> | nflfastR / nflreadr | MIT — open source | Low. MIT permits commercial use and re-distribution. Confirm no nflverse contributor agreement conflicts. |
> | Understat | Non-commercial confirmed by Understat support | **High.** Non-commercial classification almost certainly prohibits re-sale of derivatives. Audit required: does the xG model output count as a derivative of Understat data? |
> | FBref / StatsBomb Open Data | StatsBomb Open Data: non-commercial personal use | **High.** StatsBomb Open Data is explicitly non-commercial. FBref scraping terms prohibit commercial use. Both are training inputs — legal must determine whether trained model outputs are legally separable from training data under applicable IP law. |
> | The Odds API | Commercial subscription — usage-based | **High.** Commercial odds API licenses typically prohibit downstream re-sale or re-distribution. Review contract language explicitly for re-distribution restrictions. |
> | SportsDataIO / Sportradar | B2B commercial contract | **High.** Enterprise sports data contracts routinely include strict prohibitions on re-sale, redistribution, and use in competing products. Review contract language before any commercial API scoping. |
> | BALLDONTLIE | Free tier / paid plans | Medium. Review terms for commercial derivative restrictions. |
> | Jeff Sackmann Open Era dataset | MIT — open source | Low. MIT permits commercial use. Confirm no additional terms on the repository. |
> | Retrosheet | Free — attribution required | Low. Free for any use including commercial. Attribution: 'The information used here was obtained free of charge from and is copyrighted by Retrosheet.' Must appear in API documentation. |
> | pybaseball / Statcast | MIT (pybaseball). Statcast: MLB proprietary | **High.** Statcast data is MLB intellectual property accessed via a scraping layer. Commercial API exposure of Statcast-derived features may require MLB licensing. Audit required. |
> | NHL Open API | Undocumented / no formal license | **High.** The NHL API has no published terms of service. No terms means no commercial grant. Any commercial API use of NHL API data is legally unprotected. Formal licensing from NHL required or source must be replaced. |
> | hockeyR / MoneyPuck | Open source / free CSV | Low–Medium. Review repository licenses. MoneyPuck requests credit in published methodology — confirm no commercial restriction. |
> | cfbfastR / collegefootballdata.com | MIT / terms TBD | Medium. collegefootballdata.com terms must be reviewed for commercial derivative restrictions. |
>
> **Audit output required:** A written legal opinion, signed off by counsel, stating:
> - Which sources are cleared for inclusion in commercial API output (directly or as model training inputs whose outputs are legally separable)
> - Which sources are blocked, and what remediation is required (alternative source, paid license, exclusion from commercial API)
> - The permissible product boundary: what the commercial API can and cannot contain
>
> This document must exist before Section 14.2 product boundary decisions are made. Engineering must not begin scoping until this document is received.

---

## 14.2 Permissible Product Boundary

Subject to the data license audit outcome (Section 14.1), the commercial API product operates within one of two permissible boundaries. Legal counsel's audit determines which applies.

**Boundary A — Model outputs only (most defensible)**

The commercial API exposes only ParallaxEdge's proprietary model outputs: fair value probabilities, fair value odds, edge calculations, confidence scores, and data quality scores. No raw data, no odds feeds, no injury data, no weather data. The underlying inputs are retained as internal-only.

This boundary is the most legally defensible position because model outputs — the product of ParallaxEdge's proprietary statistical models applied to licensed inputs — are most likely to be treated as the company's own intellectual property rather than derivatives of the input data. It is also the strongest competitive position, since it exposes the edge without exposing the inputs.

**Boundary B — Model outputs plus enriched context (requires broader audit clearance)**

The commercial API additionally exposes curated contextual data alongside model outputs: game schedules, team/player identifiers, odds at time of model generation, and other display-layer data. This boundary is only permissible if the data license audit confirms each data type is cleared for re-distribution.

In either boundary, the following are **never** included in the commercial API:

- Raw ingested data from any vendor with re-sale restrictions
- Closing line odds (Pinnacle or any other source) where the vendor prohibits redistribution
- Any data element where the audit returns a blocked classification

---

## 14.3 Technical Architecture

The commercial API is a **separate service** from the consumer-facing internal API (Section 6). It must not be implemented as an extension of the existing `/api/v1/` routes. The reasons are architectural, security, and contractual:

- **Authentication model is different.** The consumer API uses Supabase user-session JWTs tied to subscription tier. The commercial API requires API key authentication with per-key usage metering, rate limits negotiated per contract, and key rotation support.
- **Rate limits are contract-defined, not tier-defined.** Commercial API clients will have bespoke QPS limits and monthly call volume caps defined in their commercial agreements. These cannot be managed through the existing Redis per-endpoint-group tier structure.
- **Billing is usage-based, not subscription-based.** Stripe handles consumer subscriptions. Commercial API billing requires a usage metering layer (e.g. Stripe Metered Billing or a dedicated metering service) that tracks API calls per key and invoices against them.
- **SLA obligations are different.** Consumer-facing uptime SLA is 99.9% monthly (Section 8.1). Commercial API clients may negotiate higher SLAs with financial penalties for breach — these cannot be absorbed into the existing infrastructure monitoring setup without explicit design.
- **Data isolation is required.** Commercial API responses must be constructed from a clearly audited data path. Mixing commercial API responses with consumer API infrastructure risks inadvertently exposing data elements that are cleared for consumer use but not for re-sale.

### Minimum technical requirements for Phase 3 commercial API

The following are required before any commercial API can be offered. None of these exist in the current stack and all require greenfield build or integration work:

| Requirement | Description |
|---|---|
| API key management | Issuance, rotation, revocation, per-key metadata (client name, tier, QPS limit, monthly cap) |
| Usage metering | Per-key call counting with granularity sufficient for billing (per endpoint, per sport, per day) |
| Metered billing integration | Stripe Metered Billing or equivalent — automated invoicing against usage |
| Commercial rate limiting | Per-key QPS enforcement independent of the consumer Redis rate limit layer |
| Audit log | Immutable per-request log per API key — required for dispute resolution and compliance |
| Commercial API documentation | Separate developer portal with endpoint reference, authentication guide, schema definitions, SLA terms, and data provenance disclosures |
| Data provenance tagging | Each response field tagged with its source classification (proprietary / licensed / open-source) to support contractual transparency obligations |
| Commercial SLA monitoring | Separate uptime and latency monitoring for commercial API endpoints — consumer dashboard (Section 13) is not sufficient |

---

## 14.4 Endpoint Design Principles

The commercial API endpoint design is deferred to Phase 3 scoping and is contingent on the data license audit outcome. The following principles apply regardless of audit outcome:

**Model outputs are the primary product.** Every endpoint should centre on model output data. Contextual data (schedules, identifiers) is supporting material, not the product.

**No endpoint should expose any field not explicitly cleared by the data license audit.** Each field in every response schema must have a corresponding audit clearance classification. Any field added post-launch must be audited before inclusion.

**Versioning is mandatory from day one.** Commercial API clients build integrations against stable contracts. Breaking changes cannot be deployed without a deprecation notice period (minimum 90 days recommended). Version in the URL path: `/commercial/v1/`.

**Sport slug filtering is required.** Commercial clients may license specific sports only. The API must support per-key sport restrictions enforced at the authentication layer, not at the application layer.

---

## 14.5 Pricing Model (Indicative — Phase 3 Decision)

Pricing decisions are deferred to Phase 3 business planning. The following frameworks are documented for planning context only.

| Model | Structure | Best for |
|---|---|---|
| **Per-call metered** | Fixed price per API call or per 1,000 calls, tiered by volume | Media companies, low-volume integrators |
| **Annual flat licence** | Fixed annual fee for defined call volume and sport scope | Enterprise clients, sportsbook operators |
| **Revenue share** | Percentage of revenue generated by client product using API | Fantasy platforms, analytics products where tracking is feasible |
| **White label** | Full product licence including branding rights | Operators who want ParallaxEdge analytics under their own brand |

Any pricing model that includes usage-based billing requires the metering infrastructure in Section 14.3. Revenue share requires contractual audit rights. White label requires a separate IP licensing agreement reviewed by legal counsel.

---

## 14.6 Legal Requirements Before Commercial API Launch

In addition to the data license audit (Section 14.1), the following legal workstreams must be completed before any commercial API client is onboarded:

| Requirement | Description | Owner |
|---|---|---|
| **Commercial API Terms of Service** | Separate from the consumer ToS. Must cover: permitted use, prohibited downstream redistribution, IP ownership of outputs, data provenance disclosures, SLA terms and remedy, termination rights, audit rights (for revenue share models). Must be reviewed by counsel with commercial IP expertise. | Legal |
| **API Client Agreement template** | Master Service Agreement (MSA) or API Licence Agreement template for B2B clients. Must include: data use restrictions, sport/market scope definition, per-key volume caps, confidentiality, indemnification, governing law. | Legal |
| **IP ownership confirmation** | Formal legal opinion confirming ParallaxEdge LLC owns the commercial API outputs as a work product independent of licensed input data. Requires input from the data license audit. | Legal |
| **Competitor clause review** | Decision on whether to prohibit direct competitors (other sports betting analytics platforms) from licensing the commercial API. If permitted: what restrictions apply? If prohibited: how is 'competitor' defined? | Legal + Product Lead |
| **Export control review** | Confirm whether any data content triggers US export control obligations for commercial API clients in non-US jurisdictions. Relevant given EU, UK, Australian market exposure. | Legal |

---

> **Standing convention: no engineering work begins on the commercial API before Section 14.1 is resolved.**
> This applies to all engineering activity: architecture design, endpoint specification, authentication implementation, pricing integration, and developer portal build. The data license audit outcome determines the product boundary. Building before that boundary is known produces a product that may have to be materially redesigned or partially dismantled. The audit is the gate. Legal owns the gate.
>
> **[CHG-50] Recommended audit start date: no later than 60 days post-Phase-1A launch (approximately August 2026).** Legal review lead times for data licensing opinions are typically 3–6 months. Initiating the audit in August 2026 targets a December 2026 – February 2027 completion window, which aligns with Phase 3 commercial API scoping. Delay beyond August 2026 risks pushing commercial API availability into late 2027. This is a legal workstream only at initiation — no engineering involvement required until audit is complete and product boundary is confirmed.

---

> **STANDING CONVENTION: Document Control — Standing Rules**
> PRD v1.8 supersedes v1.0, v1.1, v1.2, v1.3, v1.4, v1.5, v1.6, and v1.7 in their entirety.
>
> RATE LIMIT RULE: API Requirements v1.0 Section 7 is the single source of truth for per-endpoint-group rate limits. Any change requires simultaneous update to both documents. Changes to either document in isolation are not permitted.
>
> CROSS-REFERENCE LOCK RULE (CHG-21): Any PRD section renumbering or addition triggers a mandatory API Requirements update before the PRD version is published. The API Requirements document must be updated in the same publication cycle. Publishing a PRD version without a corresponding API doc update is not permitted when that version changes section numbers or adds new sections.
>
> Classification: CONFIDENTIAL — Internal use only.
> Distribution: Development Agent Team, Data Science Agent Team, Product Lead, Legal.
