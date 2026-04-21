# Protean Pursuits — Lessons Learned

> Platform-level lessons learned across Protean Pursuits. Project-specific
> lessons live in each project's repo (e.g. `~/projects/parallaxedge/docs/LESSONS_LEARNED.md`).
> When a lesson applies to the platform itself — not just a single project —
> it belongs here.

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
