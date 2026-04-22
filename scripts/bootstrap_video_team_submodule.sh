#!/usr/bin/env bash
#
# scripts/bootstrap_video_team_submodule.sh
#
# Promotes templates/video-team/ to a live submodule at teams/video-team/
# backed by the pre-existing github.com/mfelkey/video-team repo.
#
# What this does:
#   1. Creates a scratch working copy at /tmp/video-team-init seeded
#      with the template contents
#   2. Pushes to github.com:mfelkey/video-team as the initial commit
#   3. Removes the placeholder teams/video-team/ in the umbrella
#   4. Registers the submodule in .gitmodules + clones it in
#   5. Stages the pointer bump for you to commit
#
# Preconditions:
#   - github.com/mfelkey/video-team exists (it does, per Mike 2026-04-22)
#   - You have SSH or HTTPS push access to it
#   - You're at the umbrella repo root when you run this
#
# Designed to be idempotent-ish: if the submodule is already registered,
# the script refuses and tells you what to do. Does NOT force-push.
#
# Run from repo root:
#     bash scripts/bootstrap_video_team_submodule.sh
#
# Optional env vars:
#     VIDEO_REMOTE_URL  — override the default SSH URL with HTTPS or
#                         a fork (default: git@github.com:mfelkey/video-team.git)
#     PY                — python interpreter (default: python3.11 or
#                         python3 if 3.11 absent)

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
UMBRELLA="$PWD"
TEMPLATE="$UMBRELLA/templates/video-team"
LIVE="$UMBRELLA/teams/video-team"
SCRATCH="/tmp/video-team-init"
REMOTE_URL="${VIDEO_REMOTE_URL:-git@github.com:mfelkey/video-team.git}"

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

if [ ! -d "$TEMPLATE" ]; then
    echo "❌ Missing template: $TEMPLATE" >&2
    exit 1
fi

if grep -q 'path = teams/video-team' .gitmodules 2>/dev/null; then
    echo "ℹ️  teams/video-team is already a registered submodule."
    echo "    If you want to redo the bootstrap, remove the entry from"
    echo "    .gitmodules and .git/config first, then rerun."
    exit 0
fi

echo "━━━ Bootstrapping video-team submodule ━━━"
echo "  Template dir: $TEMPLATE"
echo "  Live target:  $LIVE"
echo "  Remote URL:   $REMOTE_URL"
echo "  Scratch:      $SCRATCH"
echo ""

# ---------------------------------------------------------------------------
# 1. Scratch clone / init / detect retry
# ---------------------------------------------------------------------------

rm -rf "$SCRATCH"
mkdir -p "$SCRATCH"

# Try to clone first — if the repo has anything on main already, decide
# whether we're retrying (skip the push) or hitting a pre-existing
# conflict (bail).
SKIP_PUSH=0
if git clone "$REMOTE_URL" "$SCRATCH" 2>/dev/null; then
    cd "$SCRATCH"
    if git log -1 >/dev/null 2>&1; then
        # Remote already populated. If it looks like a prior seed
        # (has flows/video_flow.py from our init commit), treat as
        # retry: skip re-pushing, jump to submodule registration.
        if [ -f "$SCRATCH/flows/video_flow.py" ] && \
           [ -f "$SCRATCH/agents/orchestrator/orchestrator.py" ]; then
            echo "ℹ️  Remote repo already seeded (looks like a prior"
            echo "    bootstrap attempt). Skipping push, reusing existing"
            echo "    commit: $(git log -1 --oneline)"
            SKIP_PUSH=1
        else
            echo "❌ Remote repo has commits that don't look like our seed."
            echo "   Inspect $REMOTE_URL and either:"
            echo "   - delete its contents first, or"
            echo "   - skip this script and register the submodule manually"
            exit 1
        fi
    fi
else
    # Empty repo — clone warns and leaves the dir empty. Init ours.
    cd "$SCRATCH"
    git init -b main
    git remote add origin "$REMOTE_URL"
fi

# ---------------------------------------------------------------------------
# 2. Seed from template + commit
# ---------------------------------------------------------------------------

# Copy everything except __pycache__, output/, memory/ artifacts
rsync -a --exclude='__pycache__' --exclude='output/*' --exclude='memory/*' \
      "$TEMPLATE"/ "$SCRATCH"/

# Keep empty placeholder dirs so the runtime doesn't break
mkdir -p "$SCRATCH/output/briefs" "$SCRATCH/output/compliance" \
         "$SCRATCH/output/renders" "$SCRATCH/memory"
touch "$SCRATCH/output/briefs/.gitkeep" \
      "$SCRATCH/output/compliance/.gitkeep" \
      "$SCRATCH/output/renders/.gitkeep" \
      "$SCRATCH/memory/.gitkeep"

cat > "$SCRATCH/README.md" <<'READMEEOF'
# video-team

Live submodule for the Protean Pursuits Video Team. Runs the video
production pipeline: tool selection → script → visual direction →
audio → (optional avatar) → compliance → render.

Seeded from `templates/video-team/` in the
[protean-pursuits](https://github.com/mfelkey/protean-pursuits) umbrella
on 2026-04-22.

## Run modes

- **BRIEF_ONLY** — Tool Analyst → Script → Visual → Audio (no API calls)
- **SHORT_FORM** — <60s social (TikTok, Reels, Shorts)
- **LONG_FORM** — 2–10min (YouTube, website)
- **AVATAR** — avatar/spokesperson foregrounded
- **DEMO** — screen recording wrapper
- **EXPLAINER** — animated explainer / motion graphics
- **VOICEOVER** — voiceover-only, no visual generation
- **FULL** — campaign package (all modes sequenced)

## HITL gates

- `VIDEO_TOOL_SELECTION` — after Tool Analyst, before creative work
- `SCRIPT_REVIEW` — after Script Writer, before API calls
- `VIDEO_FINAL` — after Compliance Reviewer, before publish

## Invocation

Usually via the lead in the umbrella:

```python
from agents.leads.video.video_lead import run_video_deliverable
run_video_deliverable(
    context={"project_name": "ParallaxEdge", "project_id": "PROJ-PARALLAXEDGE"},
    mode="SHORT_FORM",
    video_format="TIKTOK",
    topic="launch announcement",
    duration=45,
)
```

Direct invocation from this submodule:

```bash
python3.11 flows/video_flow.py \
    --mode SHORT_FORM \
    --project parallaxedge \
    --task "60s TikTok ad — launch" \
    --save
```
READMEEOF

if [ "$SKIP_PUSH" -eq 0 ]; then
    git add -A
    git -c "user.email=mfelkey@gmail.com" -c "user.name=Mike Felkey" \
        commit -m "init: seed video-team from templates/video-team/ (Phase 4)"
    git branch -M main
    git push -u origin main
else
    echo "ℹ️  Skipped seed/commit/push (reusing existing remote content)."
fi

# ---------------------------------------------------------------------------
# 3. Remove placeholder + register submodule in umbrella
# ---------------------------------------------------------------------------

cd "$UMBRELLA"
# Use 'git rm -r' not 'rm -rf' — git submodule add refuses if the
# target path has files in the umbrella's index. 'git rm -r' removes
# both the working tree AND the index entry. Fixes the Phase 4
# bootstrap failure we hit on 2026-04-22: "fatal: 'teams/video-team'
# already exists in the index".
if [ -d "$LIVE" ] && git ls-files --error-unmatch "$LIVE" >/dev/null 2>&1; then
    git rm -rf "$LIVE"
else
    rm -rf "$LIVE"
fi
git submodule add -b main "$REMOTE_URL" teams/video-team

# Verify it landed
if [ ! -f "$LIVE/flows/video_flow.py" ]; then
    echo "❌ Submodule registration succeeded but flow file missing." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 4. Done — leave the commit to the human
# ---------------------------------------------------------------------------

echo ""
echo "━━━ Bootstrap complete ━━━"
echo ""
echo "Staged changes in umbrella:"
git status --short | sed 's/^/  /'
echo ""
echo "Next steps:"
echo "  1. Verify the video-team remote looks right:"
echo "       cd teams/video-team && git log --oneline"
echo "       cd $UMBRELLA"
echo ""
echo "  2. Commit the submodule registration:"
echo "       git commit -m \"feat: promote video-team to live submodule (Phase 4)\""
echo ""
echo "  3. Then push the umbrella:"
echo "       git push origin HEAD"
