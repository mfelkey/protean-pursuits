#!/usr/bin/env bash
#
# scripts/install_post_commit_hook.sh
#
# Installs a git post-commit hook that auto-queues Lessons Learned
# entries for HITL review whenever a commit touches
# docs/LESSONS_LEARNED.md.
#
# The hook parses the file via the training-team's LL curator, which
# writes candidate JSONs to knowledge/candidates/ (pending HITL
# approval). It does NOT auto-approve — run scripts/approve_candidates.py
# afterwards to flush approved entries to ChromaDB.
#
# Run once from the umbrella repo root:
#
#     bash scripts/install_post_commit_hook.sh
#
# Per Phase 2 Day 6 decision 1a: umbrella-only installation for now.
# The ParallaxEdge project LL file is out of scope until/unless it
# gets re-uploaded to the Protean Pursuits project knowledge.
#
# Idempotent: safe to run multiple times. Overwrites the hook file
# each time; backs up any existing hook to post-commit.bak first.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '')"
if [ -z "$REPO_ROOT" ]; then
    echo "❌ not inside a git repository" >&2
    exit 1
fi

HOOK_DIR="$REPO_ROOT/.git/hooks"
HOOK_FILE="$HOOK_DIR/post-commit"
LL_FILE_REL="docs/LESSONS_LEARNED.md"
SUBMODULE="$REPO_ROOT/teams/training-team"
FLOW="$SUBMODULE/flows/training_flow.py"

mkdir -p "$HOOK_DIR"

if [ -f "$HOOK_FILE" ]; then
    cp -f "$HOOK_FILE" "$HOOK_FILE.bak"
    echo "ℹ️  existing hook backed up to $HOOK_FILE.bak"
fi

cat > "$HOOK_FILE" << 'HOOKEOF'
#!/usr/bin/env bash
#
# Auto-installed by scripts/install_post_commit_hook.sh.
# Queues new Lessons Learned entries for HITL review when
# docs/LESSONS_LEARNED.md is touched in the last commit.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
LL_REL="docs/LESSONS_LEARNED.md"
SUBMODULE="$REPO_ROOT/teams/training-team"
FLOW="$SUBMODULE/flows/training_flow.py"
LL_ABS="$REPO_ROOT/$LL_REL"

# Only fire if the LL file was in the last commit.
if ! git diff-tree --no-commit-id --name-only -r HEAD | grep -qx "$LL_REL"; then
    exit 0
fi

if [ ! -f "$FLOW" ]; then
    echo "⚠️  training-team flow not found at $FLOW — skipping LL auto-queue" >&2
    exit 0
fi

if [ ! -f "$LL_ABS" ]; then
    echo "⚠️  LL file missing at $LL_ABS — skipping" >&2
    exit 0
fi

echo "🎓 post-commit: queueing LL entries from $LL_REL"
# Run in the background with output redirected so the commit returns
# immediately; HITL approval is async anyway via approve_candidates.py.
(
    cd "$SUBMODULE"
    python3.11 "$FLOW" --mode ll \
        --ll-path "$LL_ABS" \
        --source-type platform \
        >> "$REPO_ROOT/.git/ll-post-commit.log" 2>&1 || \
        echo "⚠️  LL auto-queue failed; see .git/ll-post-commit.log" >&2
) &

exit 0
HOOKEOF

chmod +x "$HOOK_FILE"

echo "✅ post-commit hook installed at $HOOK_FILE"
echo "   Trigger: commits touching $LL_FILE_REL"
echo "   Action:  queues LL entries as HITL candidates"
echo "   Review:  python3.11 $SUBMODULE/scripts/approve_candidates.py --list"
