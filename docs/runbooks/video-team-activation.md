# Runbook — Activating the Video Team (Phase 4)

One-time activation sequence for the Video Team: promotes the
pre-seeded repo from a scaffold-only directory into a fully-wired
submodule with a working lead ↔ flow contract. After this runs,
`run_video_deliverable(...)` produces valid flow invocations and
Ollama can actually take a crack at generating video deliverables.

## Prerequisites

- `mfelkey/video-team` exists on GitHub as a public, empty repo
  (confirmed 2026-04-22).
- Umbrella patch `umbrella-phase4-video-team-wiring.patch` is in
  `~/Downloads/`.
- You have SSH access to `github.com:mfelkey/*` (the other 8 team
  submodules already use SSH remotes).
- Ollama + qwen3 models are running on localhost for the final
  end-to-end test (skip that step otherwise).

## Step 1 — Apply the umbrella patch

```bash
cd ~/projects/protean-pursuits
git checkout main
git fetch origin && git reset --hard origin/main

git checkout -b phase4-video-team-wiring
git am ~/Downloads/umbrella-phase4-video-team-wiring.patch
# Expected: "Applying: feat: Phase 4 — video-team lead + bootstrap script"

python3.11 -m pytest tests/                       # expect 53 passed, 2 skipped
```

## Step 2 — Run the bootstrap script

This seeds the empty `mfelkey/video-team` repo from the template,
pushes an initial commit, removes the placeholder `teams/video-team/`,
and registers the new submodule.

```bash
bash scripts/bootstrap_video_team_submodule.sh
```

Expected output structure:

```
━━━ Bootstrapping video-team submodule ━━━
  Template dir: .../templates/video-team
  Live target:  .../teams/video-team
  Remote URL:   git@github.com:mfelkey/video-team.git
  ...
[main (root-commit) xxxxxxx] init: seed video-team from templates/...
...
━━━ Bootstrap complete ━━━

Staged changes in umbrella:
  A  .gitmodules
  A  teams/video-team
```

If it refuses with "Remote repo already has commits" — your repo
isn't empty. Either delete its default branch on GitHub and retry,
or skip the script and register the submodule manually.

If you don't have SSH access set up, override with HTTPS:

```bash
VIDEO_REMOTE_URL=https://github.com/mfelkey/video-team.git \
    bash scripts/bootstrap_video_team_submodule.sh
```

## Step 3 — Verify submodule contents

```bash
cd teams/video-team
git log --oneline                       # one "init: seed..." commit
ls flows/ agents/                       # flows/video_flow.py + all 7 agents
cd ../..
```

## Step 4 — Commit the submodule registration

```bash
git commit -m "feat: promote video-team to live submodule (Phase 4)"
```

This commit stages:
- New `.gitmodules` entry for `teams/video-team`
- New submodule pointer at `teams/video-team`

## Step 5 — The real end-to-end test

This is the test Mike wanted to run manually. First, a dry test with
no project (brief-only, no HITL gates):

```bash
cd ~/projects/protean-pursuits

python3.11 -c "
import sys
sys.path.insert(0, '.')
from agents.leads.video.video_lead import run_video_deliverable

ctx = {'project_name': 'ParallaxEdge', 'project_id': 'PROJ-PARALLAXEDGE'}
result = run_video_deliverable(
    context=ctx,
    mode='BRIEF_ONLY',
    video_format='TIKTOK',
    topic='ParallaxEdge launch — brief sanity test',
    duration=30,
)
print('--- Result ---')
print(type(result), list(result.keys())[:10])
"
```

Expected flow:
1. Lead normalizes `'BRIEF_ONLY'` and builds context JSON
2. Lead invokes `teams/video-team/flows/video_flow.py --mode BRIEF_ONLY ...`
3. Flow dispatches to `run_BRIEF_ONLY(...)`
4. Four agents run: Tool Analyst → Script Writer → Visual Director → Audio Producer
5. Two HITL gates fire (VIDEO_TOOL_SELECTION, SCRIPT_REVIEW) — **you'll need to approve these via the approval mechanism** (check `scripts/approve.py --watch` in another terminal, or answer the prompts inline)
6. Result: context dict returned, outputs saved to `teams/video-team/output/briefs/`

If this works, try a mode that exercises more agents:

```bash
python3.11 -c "
import sys
sys.path.insert(0, '.')
from agents.leads.video.video_lead import run_video_deliverable

ctx = {'project_name': 'ParallaxEdge', 'project_id': 'PROJ-PARALLAXEDGE'}
result = run_video_deliverable(
    context=ctx,
    mode='SHORT_FORM',
    video_format='TIKTOK',
    topic='ParallaxEdge launch',
    duration=45,
    brand_brief='45s TikTok for the ParallaxEdge sports betting app launch. Young adult audience, hype energy, emphasis on edge-finding analytics.',
)
"
```

## Step 6 — Push everything

Once you're happy with the end-to-end result:

```bash
git push origin phase4-video-team-wiring
git checkout main
git merge --no-ff phase4-video-team-wiring -m "merge: Phase 4 — video-team wiring"
git push origin main
```

## Troubleshooting

**Lead raises `ValueError: unknown video mode`.** Pass one of:
BRIEF_ONLY, SHORT_FORM, LONG_FORM, AVATAR, DEMO, EXPLAINER, VOICEOVER,
FULL. Case-insensitive.

**Flow complains about `--context`.** The lead serializes extras as
JSON into `--context`. If you see argparse errors, the lead may have
a downstream bug — run `pytest tests/test_video_lead.py` to catch it.

**HITL gate never prompts.** The flow writes approval requests to
`logs/approvals/` and polls for responses. Start an approval watcher:
`python3.11 scripts/approve.py --watch` in a separate terminal.

**Ollama connection refused.** Confirm `ollama serve` is running and
`qwen3:32b` / `qwen3-coder:30b` are pulled (or override via TIER1_MODEL
/ TIER2_MODEL env vars).

**The submodule won't clone.** The `mfelkey/video-team` repo is
public, so HTTPS should work even without auth. If SSH is failing,
re-run the bootstrap with `VIDEO_REMOTE_URL=https://...` as shown.

## Related

- `scripts/bootstrap_video_team_submodule.sh` — the automation
- `agents/leads/video/video_lead.py` — the rewired lead
- `templates/video-team/flows/video_flow.py` — the flow (unchanged —
  the whole wiring fix is lead-side)
- `tests/test_video_lead.py` — lead contract tests
- LL-041 — HITL gate pattern (applies to video gates too)
- LL-043 invariant 4: HITL is non-negotiable
