# Protean Pursuits — Lessons Learned

> Platform-level lessons learned across Protean Pursuits. Project-specific
> lessons live in each project's repo (e.g. `~/projects/parallaxedge/docs/LESSONS_LEARNED.md`).
> When a lesson applies to the platform itself — not just a single project —
> it belongs here.

---

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
