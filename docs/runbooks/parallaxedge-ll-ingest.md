# Runbook — Ingesting ParallaxEdge Lessons Learned

Short, specific runbook for the day the ParallaxEdge
`docs/LESSONS_LEARNED.md` file is recovered or rebuilt. The
training-team infrastructure is already in place — this is just the
invocation sequence.

## Prerequisites

- ParallaxEdge `LESSONS_LEARNED.md` is on disk somewhere. Assumed path
  below is `~/projects/parallaxedge/docs/LESSONS_LEARNED.md`; adjust
  if yours is elsewhere.
- The training-team submodule is initialized at
  `teams/training-team/` (it is, per Phase 2 Day 7).
- You have shell access to the umbrella repo root
  (`~/projects/protean-pursuits`).

## Steps

### 1. Register ParallaxEdge as a project

Already done if any project has been spun up via the orchestrator
since Phase 3 landed. To confirm:

```bash
cd ~/projects/protean-pursuits/teams/training-team
python3.11 -c "
from knowledge.knowledge_base import PROJECT_DOMAINS, register_project
print('parallaxedge' in PROJECT_DOMAINS)
"
```

If `False`, register it now:

```bash
python3.11 -c "
from knowledge.knowledge_base import register_project
slug = register_project('ParallaxEdge')
print(f'Registered: {slug}')
"
```

Expected output: `Registered: parallaxedge`

### 2. Queue the LL entries as HITL candidates

```bash
cd ~/projects/protean-pursuits/teams/training-team
python3.11 flows/training_flow.py --mode ll \
    --ll-path ~/projects/parallaxedge/docs/LESSONS_LEARNED.md \
    --source-type project
```

What happens:
- Parser reads every `## LL-NNN — title` block in the file.
- One candidate JSON per entry is written to
  `knowledge/candidates/<sha256>.json` with `status: pending`.
- Metadata tags `source_type: project`, so when approved these go to
  `lessons_learned_project` rather than `lessons_learned_platform`.

### 3. Review pending candidates

```bash
python3.11 scripts/approve_candidates.py --list
```

Each candidate shows ID, priority, title, and the teams the LL
parser scored as relevant. You'll see one candidate per LL entry in
the ParallaxEdge file.

### 4. Approve candidates

Two ways — pick based on trust level:

**Bulk approve (fastest):**

```bash
python3.11 scripts/approve_candidates.py --approve-all-above MEDIUM
```

Flushes every pending candidate at priority MEDIUM or higher into
ChromaDB. Use when you've reviewed the file and trust its contents
wholesale.

**Per-item review (most careful):**

```bash
# Approve one
python3.11 scripts/approve_candidates.py --approve <candidate_id>

# Reject one with reason
python3.11 scripts/approve_candidates.py --reject <candidate_id> \
    --reason "already documented in LL-043"
```

### 5. Confirm ingestion

```bash
python3.11 flows/training_flow.py --mode status | grep -i parallax
```

You should see `parallaxedge domain` and `parallaxedge market`
collections with counts > 0.

Alternatively, run a RAG query to pull the ParallaxEdge lessons into
an agent's context:

```bash
python3.11 -c "
import sys
sys.path.insert(0, '.')
from knowledge.rag_inject import get_latest_context
latest = get_latest_context(
    team='lessons_learned',
    query='ParallaxEdge',
    domains=['project'],
)
print(latest[:1000])
"
```

## Troubleshooting

**Parser returns 0 entries.** Check heading format: must be exactly
`## LL-NNN — title` (em-dash, not hyphen). Also see LL-042 about
Unicode character pitfalls.

**`--mode ll` errors with "No such file".** The `--ll-path` flag
accepts absolute and relative paths. If you're outside the umbrella
repo root, use an absolute path.

**Candidate count unexpected.** Run the parser directly to inspect:

```bash
python3.11 -c "
import sys
sys.path.insert(0, 'teams/training-team')
from agents.curators.lessons_learned.parser import parse_ll_file
for e in parse_ll_file('<path>'):
    print(e['ll_id'], e['title'][:60])
"
```

## Post-ingest

Consider writing a new umbrella LL (LL-044+) noting that
ParallaxEdge lessons were pulled in on `<date>`, how many, and
whether any surfaced architectural patterns worth promoting to
platform-level LLs. Platform LLs (shared across all PP projects)
live in the umbrella's `docs/LESSONS_LEARNED.md`; project-scoped
lessons stay in ParallaxEdge.

## Related

- LL-041 — HITL gate (why this ingest isn't auto-approved)
- LL-043 — Phase 2 retrospective (covers the per-project layer)
- `teams/training-team/README.md` — full training-team capability surface
