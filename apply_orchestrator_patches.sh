#!/usr/bin/env bash
# apply_orchestrator_patches.sh
#
# Applies all missing run_*() orchestrator patches to the Protean Pursuits repo.
# Run from: ~/projects/protean-pursuits
#
# What this does:
#   1. Appends run_marketing_orchestrator() to marketing orchestrator
#   2. Appends run_legal_orchestrator()    to legal orchestrator
#   3. Appends run_design_orchestrator()   to design orchestrator
#   4. Appends run_qa_orchestrator()       to qa orchestrator
#   5. Appends run_strategy_orchestrator() to strategy orchestrator
#   6. Fixes Path import bug + appends run_video_orchestrator() to video orchestrator
#   7. Creates hr-team/agents/orchestrator/ directory + full orchestrator.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Protean Pursuits — Orchestrator Patch Installer ==="
echo "Repo: $REPO_ROOT"
echo ""

# ── Helper: append patch (strip module docstring at top) ─────────────────────
append_run_function() {
    local target="$1"
    local patch="$2"
    local team="$3"

    if ! grep -q "^def run_${team}_orchestrator" "$target"; then
        echo "  Appending run_${team}_orchestrator() → $target"
        # Strip everything above the first import statement in the patch
        # (the triple-quoted module docstring). We only want the function body.
        python3 -c "
import re, sys
text = open('$patch').read()
# Find the first 'import' or 'from' line after the docstring
idx = text.find('\ndef run_')
if idx == -1:
    sys.exit('ERROR: run_ function not found in patch $patch')
print(text[idx:])
" >> "$target"
        echo "  ✅ run_${team}_orchestrator() added"
    else
        echo "  ⏭️  run_${team}_orchestrator() already exists — skipping"
    fi
}

# ── 1. Marketing ──────────────────────────────────────────────────────────────
echo "── Marketing ────────────────────────────────────────────"
MARKETING="$REPO_ROOT/templates/marketing-team/agents/orchestrator/orchestrator.py"
append_run_function "$MARKETING" "$PATCHES_DIR/marketing_orchestrator_patch.py" "marketing"

# ── 2. Legal ─────────────────────────────────────────────────────────────────
echo "── Legal ────────────────────────────────────────────────"
LEGAL="$REPO_ROOT/templates/legal-team/agents/orchestrator/orchestrator.py"
append_run_function "$LEGAL" "$PATCHES_DIR/legal_orchestrator_patch.py" "legal"

# ── 3. Design ────────────────────────────────────────────────────────────────
echo "── Design ───────────────────────────────────────────────"
DESIGN="$REPO_ROOT/templates/design-team/agents/orchestrator/orchestrator.py"
append_run_function "$DESIGN" "$PATCHES_DIR/design_orchestrator_patch.py" "design"

# ── 4. QA ─────────────────────────────────────────────────────────────────────
echo "── QA ───────────────────────────────────────────────────"
QA="$REPO_ROOT/templates/qa-team/agents/orchestrator/orchestrator.py"
append_run_function "$QA" "$PATCHES_DIR/qa_orchestrator_patch.py" "qa"

# ── 5. Strategy ──────────────────────────────────────────────────────────────
echo "── Strategy ─────────────────────────────────────────────"
STRATEGY="$REPO_ROOT/templates/strategy-team/agents/orchestrator/orchestrator.py"
append_run_function "$STRATEGY" "$PATCHES_DIR/strategy_orchestrator_patch.py" "strategy"

# ── 6. Video — fix Path import bug + add run_ ────────────────────────────────
echo "── Video ────────────────────────────────────────────────"
VIDEO="$REPO_ROOT/templates/video-team/agents/orchestrator/orchestrator.py"

# Fix the Path import bug (import sys / sys.path.insert BEFORE from pathlib)
if grep -q "^sys.path.insert.*Path" "$VIDEO" 2>/dev/null; then
    # Check if Path is not yet imported when sys.path.insert happens
    FIRSTLINES=$(head -3 "$VIDEO")
    if echo "$FIRSTLINES" | grep -q "sys.path.insert"; then
        echo "  Fixing Path import NameError in video orchestrator..."
        python3 -c "
text = open('$VIDEO').read()
# Replace the broken header pattern
old = 'import sys\nsys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))'
new = 'import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))'
if old in text:
    open('$VIDEO', 'w').write(text.replace(old, new, 1))
    print('  ✅ Path import bug fixed')
else:
    print('  ⚠️  Pattern not found — manual inspection needed for video Path import')
"
    fi
fi

# Also remove the duplicate 'from pathlib import Path' if it appears later
python3 -c "
import re
text = open('$VIDEO').read()
lines = text.split('\n')
seen_pathlib = False
out = []
for line in lines:
    if line.strip() == 'from pathlib import Path':
        if seen_pathlib:
            continue  # drop duplicate
        seen_pathlib = True
    out.append(line)
open('$VIDEO', 'w').write('\n'.join(out))
print('  ✅ Duplicate pathlib import cleaned (if any)')
"

append_run_function "$VIDEO" "$PATCHES_DIR/video_orchestrator_patch.py" "video"

# ── 7. HR — create dir + full orchestrator.py ────────────────────────────────
echo "── HR ───────────────────────────────────────────────────"
HR_DIR="$REPO_ROOT/templates/hr-team/agents/orchestrator"
HR_ORCH="$HR_DIR/orchestrator.py"
HR_INIT="$HR_DIR/__init__.py"

if [ ! -d "$HR_DIR" ]; then
    echo "  Creating $HR_DIR"
    mkdir -p "$HR_DIR"
fi

if [ ! -f "$HR_ORCH" ]; then
    echo "  Installing orchestrator.py → $HR_ORCH"
    cp "$PATCHES_DIR/hr_orchestrator_dir/orchestrator.py" "$HR_ORCH"
    echo "  ✅ HR orchestrator.py installed"
else
    echo "  ⏭️  HR orchestrator.py already exists — skipping"
fi

if [ ! -f "$HR_INIT" ]; then
    touch "$HR_INIT"
    echo "  ✅ HR __init__.py created"
fi

# ── Verification ──────────────────────────────────────────────────────────────
echo ""
echo "=== Verification ==="
for team in marketing legal design qa strategy video; do
    FILE="$REPO_ROOT/templates/${team}-team/agents/orchestrator/orchestrator.py"
    if grep -q "^def run_${team}_orchestrator" "$FILE" 2>/dev/null; then
        echo "  ✅ $team: run_${team}_orchestrator() present"
    else
        echo "  ❌ $team: run_${team}_orchestrator() MISSING — check patch"
    fi
done

HR_FILE="$REPO_ROOT/templates/hr-team/agents/orchestrator/orchestrator.py"
if grep -q "^def run_hr_orchestrator" "$HR_FILE" 2>/dev/null; then
    echo "  ✅ hr: run_hr_orchestrator() present"
else
    echo "  ❌ hr: run_hr_orchestrator() MISSING — check patch"
fi

# Video Path bug check
if python3 -c "
import ast, sys
try:
    ast.parse(open('$VIDEO').read())
    print('  ✅ video: orchestrator.py parses cleanly (no NameError)')
except SyntaxError as e:
    print(f'  ❌ video: SyntaxError — {e}')
    sys.exit(1)
"; then
    :
fi

echo ""
echo "=== Patch complete ==="
echo "Commit with:"
echo "  cd $REPO_ROOT && git add -A && git commit -m 'fix: add run_*() orchestrator runners for all 7 teams (marketing/legal/design/qa/strategy/video/hr)'"
