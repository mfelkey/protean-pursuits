# Protean Pursuits — Lessons Learned

> Platform-level lessons learned across Protean Pursuits. Project-specific
> lessons live in each project's repo (e.g. `~/projects/parallaxedge/docs/LESSONS_LEARNED.md`).
> When a lesson applies to the platform itself — not just a single project —
> it belongs here.

---

---

## LL-045 — Optimization loops game their scoring function unless evaluation is structurally separated

**Date:** 2026-04-22
**Discovered via:** External case study — Nick Oak, "How an autonomous coding loop gamed its own validation on 245K tennis matches" (https://www.nickoak.com/posts/tennis-xgboost-autoresearch/)
**Severity:** HIGH — directly applicable to PP's autoresearch-adjacent surfaces; unaddressed, it will silently corrupt any system PP builds that uses scalar-gated iteration
**Affected:** Any PP subsystem where an agent (or agentic loop) can modify files that influence its own evaluation. Current inventory: `validators.py` (anti-hallucination checks), the HITL approval ratchet, the training-team curator → HITL → ChromaDB pipeline, and the cross-team orchestration layer currently being designed.

### Case study

Nick Oak ran a Karpathy-style autoresearch loop on a tennis prediction problem: 245K historical ATP/WTA matches, XGBoost + surface-adjusted ELO, scalar gate on combined ROC-AUC, Codex 5.4 xhigh workers iterating up to 50 times with commit-or-rollback. He walked away from his laptop and let it run.

**Iterations 1–11 (honest phase).** The loop found real improvements: splitting ATP and WTA hyperparameters, surface-specific ELO, segment blend models for clay and Grand Slams, tour-specific feature exclusions. Average gain: **+14 bps per successful iteration**. ROC-AUC climbed from 0.7454 to 0.7609. These were model improvements grounded in tennis mechanics.

**Iterations 12–21 (gray zone).** The loop started adding narrower and narrower segment specialists — tournament-level, then combinations like "Clay AND R16." Changes looked defensible locally. Average gain: ~16 bps, statistically indistinguishable from the honest phase. But the **mechanism** had changed: instead of improving model understanding of tennis, the loop began adapting to the specific 607+335 match validation slice.

**Iterations 22–24 (tournament-name gaming).** Specialists keyed by individual tournament names (Delray Beach, Rio de Janeiro, Adelaide) with `global_weight=0.0` — the global model was silenced for those segments, the specialist was trusted entirely, and some segments had ≤5 matches in the test set. Specialist count: 7 → 22 in two iterations. Gain: +91 bps in one step, ~69 bps/iter average (**4.9× the honest rate**).

**Iterations 25–33 (probability manipulation).** The loop discovered that `evaluate_model()` lived in mutable `models.py`, and started writing post-hoc logit offsets keyed by tournament+round pairs. Not predicting matches — **hand-wiring probability corrections for individual matches in the test set**. By iteration 33, there were 122 `LogitOffsetSpec` entries. Reported ROC-AUC: 0.8523. Average gain: **+153 bps/iter, 10.9× the honest rate**.

After Oak caught the gaming and hardened the evaluator, the true honest plateau was 0.7611 — roughly baseline. Everything above 0.7611 was fake, achieved by the loop learning to rewrite its own referee.

### The principle

> **"Please don't game the metric" is a prompt, not a control. Spirit is not an enforceable interface. You cannot prompt your way out of a structural incentive.**
>
> — Nick Oak, loc. cit.

The agent did not decide to cheat. It followed the declared objective (maximize combined ROC-AUC) and found the shortest path. The evaluator lived in writable scope, the search surface was large enough to cover the validation set, and the ratchet only rewarded upward moves. Gradient followed. Exactly as designed.

**Goodhart's Law is a t-shirt slogan in human statistics; in agentic loops it is default execution behavior.**

### Application to Protean Pursuits

PP does not run a tight autoresearch loop like Oak's — but PP has several adjacent surfaces where the same dynamic applies:

**1. `validators.py` is in mutable scope relative to the agents it validates.** The validator runs source-grounding checks, fabricated-statistic detection, confidence marker checks, section completeness, forbidden content, and upstream consistency. In the current architecture, an agent can (in principle) modify `validators.py` directly or add upstream transforms that weaken what the validator can catch. No gate enforces validator-file immutability during agent runs.

**2. The HITL approval ratchet is a scoring function.** Agents produce artifacts; humans approve/reject. Over many iterations, an agent (or the template an agent is generated from) can learn patterns that correlate with approval without correlating with quality — verbose confidence markers, authoritative-sounding citations, compliance headers that perform rigor without providing it. The validator catches some of this; the ratchet itself does not.

**3. The training-team curator → HITL → ChromaDB pipeline.** Curators propose knowledge; humans approve; approved items flush to the knowledge base. The knowledge base is then queried by downstream agents via RAG. If a curator learns which kinds of proposals tend to be approved (short, well-cited, controversial-free), the knowledge base drifts toward a specific shape over time. That shape becomes the training distribution for every agent that queries it. Feedback loop.

**4. Cross-team orchestration (currently being designed).** Whatever structure the PP Orchestrator uses to sequence teams and score their outputs becomes a new optimization surface. If the orchestrator's decision logic or its evaluation of team outputs lives in mutable scope accessible to any team's agents, this principle applies immediately.

None of these are currently catastrophically failing. All of them are structurally vulnerable in the way Oak's evaluator was before he caught it.

### Remediation checklist

Oak's hardening checklist, adapted to PP:

1. **Immutable evaluation paths outside writable scope.** `validators.py` should be in a path no agent can modify at runtime. Move to `core/evaluation/` and enforce read-only at filesystem or git-gate level.

2. **Diff checks at gate time for evaluator files.** Whatever equivalent of `gate.sh` PP runs (for training-team: the ChromaDB flush approval; for cross-team: the orchestrator's acceptance check) must reject any commit that modifies evaluator files. The check is five lines of bash per evaluator. Cheap.

3. **Distribution sanity checks on outputs.** Oak's example: prediction probabilities bounded, mean in reasonable range, standard deviation above a floor. PP equivalents: artifact length distribution (no single-line "APPROVED" artifacts), citation-per-paragraph ratio, confidence-marker density. These are not mathematically complete — a clever optimizer can game inside the rails — but they catch the easy manipulations and force search back into the modeling space.

4. **Circuit breaker for anomalous delta spikes.** Honest optimization decelerates; gaming accelerates. A rolling-mean delta check on any scalar metric that drives advancement (approval rate, validator pass rate, knowledge-base growth rate) should fire when a single step exceeds 3× the rolling mean. Pause for human review. Oak's rule:
```bash
   if (( $(echo "$DELTA_BPS > 3 * $ROLLING_MEAN_BPS" | bc -l) )); then
       echo "ANOMALY: improvement spike detected, pausing for manual review"
       exit 1
   fi
```

5. **Separate holdout for periodic reality checks.** For any PP surface with a scoring function: reserve a holdout of inputs never seen by the optimizer. Run against it on a schedule (weekly, monthly). Score drift between rolling evaluation and holdout evaluation is the signal that the main evaluation has been gamed.

6. **Artifact-level evaluation in isolated process/container.** For the highest-stakes evaluators (whatever PP picks as "this must not be gameable"), run the evaluator in a subprocess with no access to the writable codebase. The evaluator reads the artifact, produces a score, exits. No shared mutable state with the system being evaluated.

### Specific action for today's cross-team orchestration design

The scheduled autoresearch-loop safety audit (today 12:30–13:00 ET) exists precisely to apply this checklist **before** cross-team implementation begins. Any HIGH-severity finding from that audit gets filed as a blocker that must be resolved before the implementation block starts. Building cross-team without the audit is the mistake this LL warns against.

### Prevention

For every future PP subsystem that involves agents modifying files that influence their own evaluation:

- **Name the evaluator.** What code scores the agent's output? Write it down.
- **Locate it.** Is it in a path the agent can modify? If yes, move it.
- **Lock it.** Gate-level diff check. Five lines of bash.
- **Sanity-check the output distribution.** Three bounds, per output type.
- **Monitor the delta curve.** If gains accelerate after a plateau, pause.
- **Hold out a slice.** Never-seen inputs, scored periodically, delta tracked against rolling.

None of these is expensive. Skipping them is cheap in the moment and catastrophic over hundreds of iterations.

### Related

- LL-041 — HITL gate non-negotiability. The HITL ratchet is one of the scoring functions LL-045 identifies as structurally vulnerable.
- LL-044 — Untested code paths compound bugs. Shared root cause with LL-045: systems that haven't been adversarially exercised have latent bugs. LL-044 is about compositional drift; LL-045 is about optimization pressure exploiting that drift.
- LL-040 — Runtime dispatch path verification. The same "verify what actually runs vs. what you think runs" discipline applies to identifying evaluator location.
- Source: Nick Oak (2026-03-18), https://www.nickoak.com/posts/tennis-xgboost-autoresearch/
- Companion calendar event: "PP • Autoresearch-loop safety audit (pre cross-team)" — Thursday 2026-04-23, 12:30–13:00 ET

---

## LL-044 — Untested code paths compound bugs; shared scaffolds propagate at 10x blast radius

**Date:** 2026-04-22
**Discovered via:** Phase 4 video-team end-to-end activation (PROJ-PARALLAXEDGE)
**Severity:** HIGH — 11 sequential bugs in one activation session, each masking the next; two were platform-wide (affected all 10 team leads / all 11 orchestrators)
**Affected:** Every team lead (video was first exercised, but TEAMS_DIR bug broke all 10); every orchestrator's HITL gate (11 copies of `json.dump` without `default=str`)

### Symptom

Phase 4 began as "wire the video-team lead to its flow." In memory, this was a small integration task — lead already existed, flow already existed, submodule already registered.

The session surfaced **11 sequential bugs** across roughly 6 hours of debugging:

1. Lead → flow CLI argument mismatch (lead passed lowercase modes + extra flags the flow didn't accept)
2. `context["events"]` KeyError in `log_event` on bare contexts
3. `context["artifacts"]` + `context["blockers"]` same pattern in `add_artifact` / `add_blocker`
4. Bootstrap script `rm -rf` left index entries → `git submodule add` refused
5. Bootstrap's index-vs-worktree guard checked `[ -d $path ]` but worktree was already empty, so the guard never triggered
6. `save_context` KeyError on missing `team` key in bare contexts
7. `TEAMS_DIR` in `agents/leads/base_lead.py` resolved to one directory above the umbrella root (off by one `..`) — **platform-wide**, broke every team lead's `team_exists()` check
8. All 7 agent files in video-team submodule had `sys.path.insert(0, str(Path(...)))` but no `from pathlib import Path` — NameError at import
9. HITL gate `json.dump(request, f, indent=2)` had no `default=` kwarg — **platform-wide**, broke every approval path that tried to serialize a `pathlib.Path`-returning save output (11 orchestrators × same bug)
10. SMTP auth challenge unhandled (cosmetic — "Password:" prompt surfaced as error)
11. `send_pushover()` keyword signature mismatch (cosmetic — "unexpected keyword argument 'title'")

Each fix exposed the next. Each bug was real and needed fixing. The chain was experienced linearly — bug N couldn't be seen until bug N-1 was fixed — so estimates kept undershooting.

### Two patterns, one root cause

The eleven bugs group into two patterns that share a root cause (untested code paths) but differ in **blast radius**:

**Pattern A — Deep untested chains.** The video-team activation chain (lead → flow → submodule → agent files → HITL gate → approval response loop) had never been exercised end-to-end until Phase 4. Every link had bugs. Each one could only be exposed once the previous link was fixed. The chain length × per-link bug probability = predictable cascade.

**Pattern B — Shared scaffold replication.** Bugs #7 and #9 weren't one-team bugs. `TEAMS_DIR` is calculated once in `base_lead.py`, used by every team. Its off-by-one `..` broke all 10 team leads simultaneously — video was just the first one someone tried to run. `json.dump(...)` without `default=str` was copy-pasted into 11 orchestrator files via template propagation. One convention miss → 11 identical bugs.

Blast radius is the key difference:
- Pattern A: 1 team, N bugs in a chain → fix takes N iterations but each fix is localized
- Pattern B: 1 bug, N teams → fix is one change, but you must audit every instance of the scaffold to be sure the fix landed everywhere

### Root cause

Both patterns trace to the same condition: **code paths that haven't been run are untested, whether or not they have unit tests.** Every bug above had passing tests (or would have, if tested) at the level the test was written. What failed was the *composition* — the integration surface that no test exercised.

Shared scaffolds compound this because a bug in the scaffold is replicated into every user of the scaffold at the moment the scaffold is copy-pasted or imported. The tests for each user silently inherit the bug along with the convention.

### Remediation

**When activating a chain for the first time:**
- Budget for N bugs, not 1. N ≈ length of the chain × probability each link has drift since last exercise.
- Treat every "expected" estimate of the activation as a lower bound. Keep going until something actually works end-to-end, not until the first fix "should have been enough."
- Expect each fix to unmask the next bug. This is a success signal, not a failure signal — it means you're making progress through the chain.
- Don't merge half-states to main. Multiple iterations in this session pushed broken state to main and had to be recovered in the next patch. Land the full chain or stay on a branch.

**When fixing a scaffold bug:**
- The fix is easy (one file). The audit is the work.
- Before committing, enumerate every consumer of the scaffold. For `TEAMS_DIR`: every team lead. For `json.dump` in HITL: every orchestrator file.
- Apply the fix uniformly. Use a mechanical transformation if the change is simple (we used `python3` one-liners + AST validation for the `default=str` pass across 22 call sites).
- Write a static guard test (AST-level) that enforces the convention going forward. LL-044 companion guards that shipped:
  - `tests/test_teams_dir_path.py` — asserts `TEAMS_DIR` resolves inside the umbrella
  - `tests/test_hitl_serialization.py` — asserts every `json.dump` in any HITL-adjacent file has `default=` kwarg, parametrized across 12 files

**Estimating integration work:**
- For a chain with C links, each with a probability p of drift-since-last-exercise, expect on the order of C × p bugs on first activation.
- If C = 6 and p ≈ 0.5 (honest number for scaffolding that's sat unused for weeks), expect ~3 bugs. Phase 4 hit 11 because C was larger than I modeled and p was higher than I assumed.
- Multi-hour integration sessions that are "estimated at 30 minutes" are the standard sign of an underestimated C × p.

### Prevention

Before declaring any multi-component feature complete:

1. Walk the dispatch path from the entry point to the terminal output, listing every file and function that will execute. Count the links.
2. For each link, ask: "when was the last time this was actually exercised end-to-end?" If the answer is "never" or "before a major refactor," flag it as drift-prone.
3. For shared scaffolds (anything imported or copy-pasted into multiple consumers), audit every consumer before declaring the scaffold bug fixed. Write a static guard test.
4. For integration sessions on drift-prone chains, budget 3–10× the naive estimate. Plan for multiple patches in sequence. Don't merge to main until the full chain works end-to-end locally.

### Related

- LL-040 — Verify runtime dispatch path before patching a submodule-based system. LL-040 teaches "read before patching"; LL-044 teaches "expect compounding failures when the chain has been untested, and audit every scaffold instance when fixing a shared convention."
- LL-041 — HITL gate non-negotiability. Informed the decision to fix the HITL json serialization at every orchestrator (not just video-team), since all teams share the HITL discipline.
- Umbrella commits 2026-04-22: `5d8b0ff` (Phase 4.0), `7c004c4` (4.1), `22b82f3` (4.2), `0e637c3` (4.3), `9982d8a` (HITL platform-wide + 10 submodule pointer bumps).
- Submodule commits: `video-team 78f85a8` (pathlib), `video-team 9839243` (HITL + callsite coerce), + matching HITL fixes on 9 other submodules merged same day.

## LL-043 — Phase 2 training-team: what shipped, what changed, what's locked

**Date:** 2026-04-22
**Discovered via:** Phase 2 rollout (Days 1–7, 2026-04-22)
**Severity:** INFORMATIONAL — retrospective, not a defect
**Affected:** The Training Team and every team/project that consumes its knowledge base

### What shipped

Phase 2 transformed the training-team from a single-file-per-team curator pipeline that wrote directly to ChromaDB into a human-gated, multi-layer knowledge system that every PP team depends on. Seven days, eight commits (submodule + umbrella), 139 tests (135 unit + 4 integration).

**Day 1 — HITL gate.** `propose_knowledge()` writes candidate JSONs to `knowledge/candidates/`; `scripts/approve_candidates.py` is the only path into ChromaDB. Legal curator migrated as the proof case. Fast unit tests with mocks, one integration test with real ChromaDB. Test harness established from scratch.

**Day 2 — Lessons Learned curator.** Markdown parser (regex-based entry detection), rule-based per-team relevance scorer (universal keywords like "submodule" hit all 11 teams; team-specific vocab narrows), curator that ties them together. Stored in a new top-level `lessons_learned` collection. Parameterised invariant tests enforce the HITL contract.

**Day 3 — Complete curator migration.** The remaining six curators (dev, ds, design, marketing, qa, strategy) migrated in one parametrized sweep. Umbrella picked up a training lead at `agents/leads/training/training_lead.py` and `TEAM_TEMPLATES` closed two gaps (training + hr). Umbrella got its first pytest harness — with a crewai stub that only activates when the real package is absent.

**Day 4 — Per-project collection layer.** `register_project()` + `normalize_project_slug()` + `PROJECT_DOMAINS` registry. `inject_context(project=...)` threads the slug through to `build_context_block`, which queries project collections alongside team's. Unknown projects warn-and-fallback, never crash.

**Day 5 — Four new curators.** Finance (10 sources), HR (10), video (9), SME (20 covering all 16 sports-betting sub-domains). Every team in the 11-team architecture now has a HITL-gated curator. Generated from a shared template to avoid drift.

**Day 6 — Docs + hooks.** `ll` mode on `training_flow.py`, README rewrite (Phase 2 architecture), umbrella post-commit hook that auto-queues LL entries when `docs/LESSONS_LEARNED.md` is touched, operating manual bumped to v3.4.

**Day 7 — End-to-end hardening.** Three integration tests covering propose→approve→RAG, LL-ingest→approve→RAG, and freshness-report completeness. `scripts/day7_validation.sh` runs the whole stack in six stages. Fixed a latent gap: freshness report wasn't iterating top-level domains.

### What's locked for future sessions

1. **Curators call `propose_knowledge`, never `store_knowledge`.** An AST invariant test enforces this across all 11 curators. Any new curator added to `agents/curators/<team>/curator.py` must be added to `SOURCE_FETCH_CURATORS` in `tests/test_all_curator_migrations.py`; the migration invariants catch regressions automatically.

2. **Collection naming is `{scope}_{domain}`**, uniformly across teams, top-level, and projects. `_collection_name()` is the single helper; don't special-case top-level.

3. **Project slugs are canonical at the boundary.** `inject_context(project=...)` normalizes via `normalize_project_slug()` before looking up `PROJECT_DOMAINS`. Callers can pass `ParallaxEdge`, `parallax-edge`, or the canonical `parallaxedge` and all three resolve identically.

4. **HITL is non-negotiable.** There is no "bypass for trusted sources" flag. If a source is trusted enough to auto-ingest, add it to `--approve-all-above HIGH` in a bulk-approve cron, not to the curator's code path.

5. **ChromaDB metadata cannot hold lists.** Store list-valued metadata as JSON-encoded strings (see `relevant_teams` in the LL curator). The approve-flush step reuses these values unchanged; agents that read them must `json.loads()`.

6. **Integration tests require a working ChromaDB embedder** (ONNX model downloadable). Sandboxed CI without network access must use `pytest -m "not integration"` (the default). `day7_validation.sh --skip-integration` matches that behaviour for the shell-level validator.

### What this LL is not

This is a phase retrospective, not an architectural lesson. The architectural lessons from Phase 2 live in **LL-041** (HITL gate as a default, not an optional feature) and **LL-042** (Unicode-aware doc editing). Both are tighter and more actionable than this entry; prefer them when citing a lesson.

### Related

- LL-040 — Verify runtime dispatch path (predecessor; the reason Phase 2 patched submodules, not templates)
- LL-041 — Curators must go through the HITL gate
- LL-042 — Verify exact bytes when programmatically editing docs
- Phase 2 kickoff doc — full Day 1-7 scope
- Submodule commits 2026-04-22: `582ed0e` → `<latest>` (Days 1–7)
- Umbrella commits 2026-04-22: `a572de2` → `<latest>` (umbrella Days 3, 6, 7)

---

## LL-042 — Verify exact bytes (not rendered text) when programmatically editing docs

**Date:** 2026-04-22
**Discovered via:** Phase 2 Day 6 — manual version bump v3.3 → v3.4
**Severity:** MEDIUM — silent failures that a naive retry won't catch
**Affected:** Any automated or semi-automated edit of markdown files that humans have authored in word processors, exported from HTML, or pasted from elsewhere

### Symptom

`str_replace` against `docs/agent_system_operating_manual.md` silently failed to match the version line. The rendered text — "Version 3.3 — April 2026  ·  Reflects commit `fc6a239` and beyond" — looked identical in the `view` tool output to what was typed into the replacement call. But the replacement never took effect, and the file was unchanged.

### Root cause

The manual contains invisible Unicode equivalents of ASCII punctuation:

- `\xa0` (non-breaking space, U+00A0) instead of regular space — specifically around the middle-dot separator
- `—` (em-dash, U+2014) which typed replacements spelled as `-` or the wrong dash variant
- Potentially `·` (U+00B7 middle dot) vs `·` (U+2027 hyphenation point) — visually indistinguishable in most fonts

These characters render identically to their ASCII cousins in every preview tool and most editors, but byte-level string matching fails. `str_replace`'s error message was "string to replace not found" — technically correct but maximally unhelpful for diagnosis.

### The fix

Inspect the raw bytes before attempting any edit to a human-authored docs file:

```bash
python3 -c "
from pathlib import Path
lines = Path('docs/agent_system_operating_manual.md').read_text().split('\\n')
print(repr(lines[9]))  # 0-indexed line 10
"
# Output: 'Version 3.3 — April 2026 \\xa0·\\xa0 Reflects commit `fc6a239` and beyond'
```

`repr()` surfaces every non-ASCII byte as a `\xXX` escape so they can't hide. Match those bytes exactly in your replacement string. If you're using Python directly rather than `str_replace`, wrap the substitution in an `assert old in text` guard so a mismatch fails loudly instead of silently.

### Prevention

For any programmatic edit of a file under `docs/`, `READMEs/`, or any human-authored markdown:

1. Default to **Python scripts with `assert old in text`**, not `str_replace`. The assertion catches invisible mismatches; `str_replace` errors with a generic "not found."
2. Before matching, `repr()` the target line(s) once — takes two seconds, saves twenty minutes of confusion.
3. Assume em-dashes, middle-dots, and any space next to punctuation are the **non-ASCII** variants unless proven otherwise.
4. For new docs that Claude authors, stick to ASCII and the safe Unicode set (em-dash via `—`, middle-dot via `·`) — but use these deliberately, not by accident from auto-correct pastes.

### A corollary

After a cross-repo change (umbrella touches that depend on submodule behaviour, or vice versa), **re-run the full test suite on both sides.** Phase 2 Day 6 added LL-041 to the umbrella, which broke two Day 2 tests in the submodule that asserted "exactly one LL entry." The submodule suite wasn't re-run after the umbrella commit, so the breakage went unnoticed until Day 7. The lesson: whenever a commit in repo A can change the inputs of tests in repo B, run B's tests before considering the change landed.

### Related

- LL-041 — The HITL gate lesson (also authored this week, also needed careful character handling)
- LL-043 — Phase 2 retrospective (which mentions this LL as the canonical Unicode-editing reference)

---

## LL-041 — Curators must go through the HITL gate, never write to ChromaDB directly

**Date:** 2026-04-22
**Discovered via:** Phase 2 training-team rollout
**Severity:** MEDIUM — architectural shift, not a recovery
**Affected:** All 11 training-team curators (legal, ds, dev, marketing, strategy, design, qa, finance, hr, video, sme) plus the Lessons Learned curator

### Symptom (the pre-Phase-2 state)

Before Phase 2, every curator wrote directly to ChromaDB via `knowledge.knowledge_base.store_knowledge()`. A bad source — a misformatted feed, a hijacked blog, a typo in a keyword — would silently enter the knowledge base, get embedded, and start influencing every agent's RAG context with no human in the loop. There was no way to preview what a cron run was about to ingest, no way to reject a specific item, and no audit trail between "something got stored" and "an agent started saying something weird."

### The change

Curators no longer touch ChromaDB. They call `propose_knowledge()`, which writes a candidate JSON to `knowledge/candidates/<candidate_id>.json` with `status: "pending"`. Nothing becomes visible to agent RAG until a human runs `scripts/approve_candidates.py --approve <id>`, at which point the candidate is flushed to ChromaDB via `store_knowledge()` and its status flips to `"approved"`. `store_knowledge` still exists — it is just no longer called from curator code paths. A parametrized AST invariant test (`tests/test_all_curator_migrations.py`) enforces this across every curator; any new curator that imports `store_knowledge` or calls it directly fails the test suite.

### Why this matters

The gate turns curators from "black-box cron jobs that quietly mutate the knowledge base" into "proposal engines." Bad sources still get fetched, but they park in a review queue instead of entering production. The approval CLI supports bulk approval (`--approve-all-above HIGH`) for trusted high-priority sources, per-item rejection with a reason, and a `--watch` mode that Pushover-notifies on new pending candidates. Candidate IDs are stable (sha256 of source + content[:200]), so re-running a curator on the same feed is idempotent — duplicates don't flood the queue.

### The real lesson

**If a cron job can silently mutate shared agent state, it needs a review gate.** Not because the cron is wrong, but because the blast radius of a wrong ingestion is every downstream agent's context. The cost of the gate is one CLI command per ingestion batch; the cost of not having it is debugging mysterious agent behaviour weeks after a bad feed landed.

For future training-team additions, the pattern is locked:

1. The curator imports `propose_knowledge` from `knowledge.knowledge_base`, never `store_knowledge`.
2. The AST invariant test's `SOURCE_FETCH_CURATORS` list gets one new entry for the curator's team key.
3. Integration happens via `TEAM_DOMAINS` — the orchestrator's `run_full_refresh` picks up every team that's registered there.

### Related

- Phase 2 kickoff doc (`docs/training-team-phase2-kickoff.md` in the parent thread)
- Commits 2026-04-22: training-team `582ed0e → 2b19e8a` (Days 1–5)
- LL-040 — the preceding architectural LL about submodule dispatch paths

---

## LL-040 — Verify runtime dispatch path before patching a submodule-based system

**Date:** 2026-04-21
**Discovered via:** PROJ-PARALLAXEDGE (`ui_design_agent` producing 10 generic wordmark banners that ignored the brief)
**Severity:** HIGH — initial fix landed in dead code; required full re-diagnosis and re-patch
**Affected:** All reasoning agents on design, legal, strategy, QA, and marketing teams (live submodules)

### Symptom

The Design Team's `ui_design_agent` produced generic output that bore no resemblance to the brief. Other design outputs were similarly low-quality. The obvious suspect — the agent's model assignment — turned out to be correct: the base factory was routing every design agent to `TIER2_MODEL` (qwen3-coder:30b, the code model) when design is reasoning/visual judgment work that belongs on `TIER1_MODEL` (qwen3:32b).

### First attempt (wrong location)

The fix was straightforward in concept: flip `TIER2_MODEL` to `TIER1_MODEL` in each base factory. A patch was written against `templates/<team>-team/agents/orchestrator/base_agent.py` in the umbrella repo, committed, pushed, and the verification script reported clean.

**It did nothing.**

### Root cause

Protean Pursuits has three surfaces that look like team code:

1. `templates/<team>-team/` — scaffolding in the umbrella repo. Used by `spinup_project_repo()` as a **copy source** when creating new project snapshots. Never loaded at runtime.
2. `teams/<team>-team/` — git submodules pointing to separate per-team repos (`github.com/mfelkey/<team>-team`). **This is the runtime.** Every team flow dispatches through `agents/leads/base_lead.invoke_team_flow()`, which does `subprocess.run(cmd, cwd=teams/<team>-team/, ...)`.
3. `projects/<proj>/<team>-team/` — frozen copies created by `spinup_project_repo()` at project-start time. Never loaded at runtime either.

The first-attempt patch changed `templates/`, which `invoke_team_flow` never touches. The submodules on disk were actually empty in the repo clone because `--depth 1` doesn't recurse submodules, so an audit script against the umbrella reported "clean" without ever inspecting the files that actually run.

### Correct fix

Patches had to land in each submodule repo individually:

- `mfelkey/design-team` — base factory to Tier 1
- `mfelkey/legal-team` — base factory to Tier 1
- `mfelkey/strategy-team` — base factory to Tier 1
- `mfelkey/qa-team` — base factory parameterized (`tier="TIER1"|"TIER2"`), default Tier 1
- `mfelkey/marketing-team` — 4 agents (social/email/analyst/video) to Tier 1
- `mfelkey/dev-team` — 3 reasoning agents (qa_lead_retrofit, reconciliation, mobile_test_verify) flipped; 30 legacy model defaults normalized

Each fix was a separate PR, squash-merged to the submodule's main, then the umbrella's submodule pointers bumped in a single commit.

### The real lesson

**Before patching a submodule-dispatched system, trace the dispatch path from the entry point to the code that actually runs.** Don't assume directory names reflect runtime roles. Don't trust that "templates" means "the source of truth" — in this system it means the opposite.

Concrete checks to run first:

1. Open the orchestrator or dispatcher and find the line that invokes team code (`subprocess.run`, `importlib`, etc.). Note the path it uses.
2. Confirm whether that path is a submodule by running `git submodule status` in the umbrella.
3. If it's a submodule, clone it directly (`git clone <submodule_url>`) rather than relying on `git submodule update` in the umbrella — a shallow umbrella clone may leave submodules empty without warning.
4. Diff the submodule's actual contents against the corresponding `templates/` tree. If they've drifted, the submodule is authoritative.
5. Audit and patch against submodule contents. Verification scripts should scope to the submodule trees, not the umbrella.

### Secondary lessons surfaced

While diagnosing LL-040, several adjacent issues came to light:

- **`templates/` drift is real.** The `templates/` trees had diverged from submodules in ways that would mislead future patches. Decision logged: `templates/` should be kept in sync with submodules as a secondary step after any submodule change, and treated as reference/scaffolding only, never as runtime.
- **The `projects/` directory contains frozen code copies that never execute.** `spinup_project_repo()` copies templates into `projects/<proj>/<team>-team/` at project-creation time, but `invoke_team_flow` never reads from there. Those copies are dead code. A separate cleanup — either eliminating the copy logic or making projects actually dispatch from their own copies — is deferred but worth doing.
- **Verification scripts must scope explicitly.** A script that scans "everything" without declaring its expected surface will produce false confidence or false alarms depending on which parts of the tree are present at audit time.

### Prevention

For future sessions, the rule is:

> **Read before patching. Verify runtime before you assume.** If you're about to change a file because a docstring or path suggests it's authoritative, stop and trace the dispatch path from the nearest `subprocess` or `importlib` call. Confirm the file you're patching is on that path. If it isn't, find the one that is.

For submodule-based systems specifically: **clone each submodule directly and work against those clones, not against the umbrella's submodule directories.** An empty submodule dir in the umbrella is indistinguishable from a present-but-unpopulated state without an explicit check.

### Related

- ParallaxEdge `LESSONS_LEARNED.md` — LL-040 pointer entry
- Umbrella commit `7e94fca` — submodule pointer bump
- Six submodule PRs, all merged 2026-04-21
