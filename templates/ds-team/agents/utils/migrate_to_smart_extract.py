#!/usr/bin/env python3
"""
migrate_to_smart_extract.py — Automated Agent Migration Tool

Migrates all agent files from first-N-characters extraction:
    with open(path) as f:
        content = f.read()[:3000]

To smart section extraction:
    from agents.orchestrator.context_manager import load_agent_context, format_context_for_prompt
    ctx = load_agent_context(context, "agent_id", ["ARTIFACT_TYPE1", ...])
    prompt_context = format_context_for_prompt(ctx)

Usage:
    python agents/utils/migrate_to_smart_extract.py --dry-run   # Preview changes
    python agents/utils/migrate_to_smart_extract.py             # Apply changes
    python agents/utils/migrate_to_smart_extract.py --revert    # Undo (from .bak files)

The script:
  1. Scans all agent .py files
  2. Detects f.read()[:N] patterns in run_* functions
  3. Maps each file to its CONTEXT_MAP agent_id
  4. Determines which artifact types the agent consumes
  5. Replaces the old extraction block with the new API call
  6. Injects the import at the top of the file
  7. Adds on_artifact_saved() after artifact write
"""

import os
import re
import sys
import glob
import shutil
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
#  AGENT REGISTRY — maps file paths to CONTEXT_MAP agent IDs
#  and the artifact types each agent consumes
# ═══════════════════════════════════════════════════════════════════

AGENT_REGISTRY = {
    # ── Planning ─────────────────────────────────────────────────
    "dev/strategy/business_analyst.py": {
        "agent_id": "biz_analyst",
        "consumes": ["PRD"],
        "produces": "BAD",
    },
    "dev/strategy/scrum_master.py": {
        "agent_id": "scrum_master",
        "consumes": ["PRD", "BAD"],
        "produces": "SPRINT_PLAN",
    },
    "dev/strategy/technical_architect.py": {
        "agent_id": "architect",
        "consumes": ["PRD", "BAD", "SPRINT_PLAN"],
        "produces": "TAD",
    },
    "dev/strategy/security_reviewer.py": {
        "agent_id": "security",
        "consumes": ["PRD", "TAD"],
        "produces": "SRR",
    },
    "dev/strategy/ux_designer.py": {
        "agent_id": "ux_designer",
        "consumes": ["PRD", "BAD", "SRR"],
        "produces": "UXD",
    },
    "dev/strategy/ux_content_guide.py": {
        "agent_id": "ux_content",
        "consumes": ["PRD", "UXD"],
        "produces": "CONTENT_GUIDE",
    },

    # ── Test Spec ────────────────────────────────────────────────
    "dev/build/senior_developer.py": {
        "agent_id": "senior_dev",
        "consumes": ["PRD", "TAD", "UXD"],
        "produces": "TIP",
    },
    "dev/performance/performance_planner.py": {
        "agent_id": "perf_plan",
        "consumes": ["PRD", "TAD", "TIP"],
        "produces": "PBD",
    },
    "dev/quality/qa_lead.py": {
        "agent_id": "qa_lead",
        "consumes": ["PRD", "TIP", "TAD", "UXD"],
        "produces": "MTP",
    },
    "dev/quality/test_automation_engineer.py": {
        "agent_id": "test_auto",
        "consumes": ["MTP", "TIP", "TAD"],
        "produces": "TAR",
    },

    # ── Build ────────────────────────────────────────────────────
    "dev/build/backend_developer.py": {
        "agent_id": "backend_dev",
        "consumes": ["TIP", "TAD", "MTP", "TAR"],
        "produces": "BIR",
    },
    "dev/build/frontend_developer.py": {
        "agent_id": "frontend_dev",
        "consumes": ["TIP", "UXD", "MTP", "TAR", "CONTENT_GUIDE", "BIR"],
        "produces": "FIR",
    },
    "dev/build/database_admin.py": {
        "agent_id": "dba",
        "consumes": ["BIR", "TAD", "SRR"],
        "produces": "DBAR",
    },
    "desktop/desktop_developer.py": {
        "agent_id": "desktop_dev",
        "consumes": ["UXD", "TAD", "TIP", "BIR", "FIR"],
        "produces": "DSKR",
    },
    "dev/build/devops_engineer.py": {
        "agent_id": "devops",
        "consumes": ["TIP", "TAD", "SRR", "TAR"],
        "produces": "DIR",
    },
    "docs/devex_writer.py": {
        "agent_id": "devex_writer",
        "consumes": ["PRD", "TAD", "BIR", "FIR", "DIR", "DSKR"],
        "produces": "DXR",
    },

    # ── Verify ───────────────────────────────────────────────────
    "dev/security/penetration_tester.py": {
        "agent_id": "pen_test",
        "consumes": ["SRR", "BIR", "FIR", "DIR", "DBAR"],
        "produces": "PTR",
    },
    "dev/scalability/scalability_architect.py": {
        "agent_id": "scale_arch",
        "consumes": ["TAD", "BIR", "FIR", "DBAR", "DIR"],
        "produces": "SAR",
    },
    "dev/performance/performance_auditor.py": {
        "agent_id": "perf_audit",
        "consumes": ["PBD", "BIR", "FIR", "DIR", "DBAR", "DSKR"],
        "produces": "PAR",
    },
    "dev/accessibility/accessibility_specialist.py": {
        "agent_id": "a11y_audit",
        "consumes": ["UXD", "FIR", "BIR", "IIR", "AIR", "RN_GUIDE", "DSKR"],
        "produces": "AAR",
    },
    "compliance/license_scanner.py": {
        "agent_id": "license_scan",
        "consumes": ["PRD", "BIR", "FIR", "DIR", "DSKR", "IIR", "AIR", "RN_GUIDE"],
        "produces": "LCR",
    },
    "dev/quality/test_verify.py": {
        "agent_id": "verify",
        "consumes": ["TAR", "BIR", "FIR", "DIR"],
        "produces": "VERIFY",
    },

    # ── Mobile ───────────────────────────────────────────────────
    "mobile/qa/mobile_qa_specialist.py": {
        "agent_id": "mobile_qa",
        "consumes": ["MUXD", "PRD", "TAD"],
        "produces": "MOBILE_TEST_PLAN",
    },
    "mobile/ios/ios_developer.py": {
        "agent_id": "ios_dev",
        "consumes": ["MUXD", "PRD", "MOBILE_TEST_PLAN"],
        "produces": "IIR",
    },
    "mobile/android/android_developer.py": {
        "agent_id": "android_dev",
        "consumes": ["MUXD", "PRD", "MOBILE_TEST_PLAN"],
        "produces": "AIR",
    },
    "mobile/rn/react_native_architect_part1.py": {
        "agent_id": "rn_arch_p1",
        "consumes": ["MUXD", "MOBILE_TEST_PLAN"],
        "produces": "RNAD_P1",
    },
    "mobile/rn/react_native_developer.py": {
        "agent_id": "rn_dev",
        "consumes": ["RNAD_P1", "RNAD_P2", "MOBILE_TEST_PLAN"],
        "produces": "RN_GUIDE",
    },
    "mobile/devops/mobile_devops_engineer.py": {
        "agent_id": "mobile_devops",
        "consumes": ["RN_GUIDE", "SRR", "MOBILE_TEST_PLAN"],
        "produces": "MDIR",
    },
    "mobile/security/mobile_penetration_tester.py": {
        "agent_id": "mobile_pen_test",
        "consumes": ["SRR", "IIR", "AIR", "RN_GUIDE", "MDIR"],
        "produces": "MOBILE_PTR",
    },
    "mobile/scalability/mobile_scalability_review.py": {
        "agent_id": "mobile_scale",
        "consumes": ["MUXD", "IIR", "AIR", "RN_GUIDE", "MDIR"],
        "produces": "MOBILE_SAR",
    },
    "mobile/quality/mobile_test_verify.py": {
        "agent_id": "mobile_verify",
        "consumes": ["MOBILE_TEST_PLAN", "IIR", "AIR", "RN_GUIDE", "MDIR"],
        "produces": "MOBILE_VERIFY",
    },
}

# ═══════════════════════════════════════════════════════════════════
#  DETECTION — find f.read()[:N] patterns
# ═══════════════════════════════════════════════════════════════════

# Pattern: matches lines like:
#   content = f.read()[:3000]
#   srr_excerpt = f.read()[:6000]
#   tip_content = f.read()[:3000]
READ_PATTERN = re.compile(
    r'^(\s+)(\w+)\s*=\s*f\.read\(\)\[:(\d+)\]\s*$',
    re.MULTILINE
)

# Pattern: matches the full open-read block:
#   var = ""
#   if path and os.path.exists(path):
#       with open(path) as f:
#           var = f.read()[:N]
OPEN_READ_BLOCK = re.compile(
    r'(\s+)(\w+)\s*=\s*""\s*\n'
    r'\s+if\s+(\w+)\s+and\s+os\.path\.exists\(\3\):\s*\n'
    r'\s+with\s+open\(\3\)\s+as\s+f:\s*\n'
    r'\s+\2\s*=\s*f\.read\(\)\[:(\d+)\]',
    re.MULTILINE
)

# Pattern: simple 2-line open-read
SIMPLE_READ_BLOCK = re.compile(
    r'(\s+)with\s+open\((\w+)\)\s+as\s+f:\s*\n'
    r'\s+(\w+)\s*=\s*f\.read\(\)\[:(\d+)\]',
    re.MULTILINE
)

# Import already present?
SMART_IMPORT = "from agents.orchestrator.context_manager import"


def find_agent_files(base_dir):
    """Find all agent Python files that might need migration."""
    results = []
    for rel_path, info in AGENT_REGISTRY.items():
        full_path = os.path.join(base_dir, "agents", rel_path)
        if os.path.exists(full_path):
            results.append((full_path, rel_path, info))
        else:
            # Try alternate paths
            alt = os.path.join(base_dir, rel_path)
            if os.path.exists(alt):
                results.append((alt, rel_path, info))
    return results


def analyze_file(filepath):
    """Analyze a file for f.read()[:N] patterns. Returns list of findings."""
    with open(filepath) as f:
        content = f.read()

    findings = []

    # Check for 4-line open-read blocks
    for m in OPEN_READ_BLOCK.finditer(content):
        findings.append({
            "type": "open_read_block",
            "var": m.group(2),
            "path_var": m.group(3),
            "chars": int(m.group(4)),
            "match": m.group(0),
            "start": m.start(),
            "end": m.end(),
        })

    # Check for 2-line simple reads (only if not already caught above)
    for m in SIMPLE_READ_BLOCK.finditer(content):
        # Skip if this span overlaps with an already-found block
        overlaps = any(f["start"] <= m.start() <= f["end"] for f in findings)
        if not overlaps:
            findings.append({
                "type": "simple_read",
                "var": m.group(3),
                "path_var": m.group(2),
                "chars": int(m.group(4)),
                "match": m.group(0),
                "start": m.start(),
                "end": m.end(),
            })

    already_migrated = SMART_IMPORT in content
    return findings, already_migrated, content


def generate_replacement(agent_info, findings):
    """Generate the smart extraction replacement code."""
    agent_id = agent_info["agent_id"]
    consumes = agent_info["consumes"]
    produces = agent_info["produces"]

    # Build the import line
    import_line = (
        "from agents.orchestrator.context_manager import "
        "load_agent_context, format_context_for_prompt, on_artifact_saved"
    )

    # Build the context loading block
    types_str = ", ".join(f'"{t}"' for t in consumes)
    context_block = (
        f'    # ── Smart extraction: load relevant sections for {agent_id} ──\n'
        f'    ctx = load_agent_context(\n'
        f'        context=context,\n'
        f'        consumer="{agent_id}",\n'
        f'        artifact_types=[{types_str}],\n'
        f'        max_chars_per_artifact=6000\n'
        f'    )\n'
        f'    prompt_context = format_context_for_prompt(ctx)\n'
    )

    # Build the on_artifact_saved call
    save_hook = (
        f'    on_artifact_saved(context, "{produces}", '
    )

    return import_line, context_block, save_hook


def apply_migration(filepath, agent_info, dry_run=False):
    """Apply the smart extraction migration to a single file."""
    findings, already_migrated, content = analyze_file(filepath)

    if already_migrated:
        return "SKIP", "Already migrated (has smart_extract import)"

    if not findings:
        return "SKIP", "No f.read()[:N] patterns found"

    agent_id = agent_info["agent_id"]
    import_line, context_block, save_hook = generate_replacement(agent_info, findings)

    new_content = content

    # 1. Add import after existing imports
    # Find the last 'from ... import' or 'import ...' line
    import_insertion_point = 0
    for m in re.finditer(r'^(?:from|import)\s+.+$', new_content, re.MULTILINE):
        candidate = m.end()
        # Don't insert after the line if it's inside a try/except
        line_start = new_content.rfind('\n', 0, m.start()) + 1
        indent = len(m.group(0)) - len(m.group(0).lstrip())
        if indent == 0:
            import_insertion_point = candidate

    if import_insertion_point > 0:
        new_content = (
            new_content[:import_insertion_point] +
            f"\n{import_line}\n" +
            new_content[import_insertion_point:]
        )

    # 2. Replace all f.read()[:N] blocks with the smart extraction block
    # We need to rebuild the findings positions since we modified content
    # Strategy: replace ALL read blocks with a single context_block
    # placed where the FIRST read block was

    # Find all variable names that were being read
    var_names = [f["var"] for f in findings]

    # Find the first read block in the NEW content
    first_block = None
    last_block = None
    for pattern in [OPEN_READ_BLOCK, SIMPLE_READ_BLOCK]:
        for m in pattern.finditer(new_content):
            if first_block is None or m.start() < first_block.start():
                first_block = m
            if last_block is None or m.end() > last_block.end():
                last_block = m

    if first_block and last_block:
        # Get the region from first to last read block
        region_start = first_block.start()
        region_end = last_block.end()

        # Check if there's non-read code between blocks that we should preserve
        region_text = new_content[region_start:region_end]

        # Replace the entire region with the context block
        new_content = (
            new_content[:region_start] +
            "\n" + context_block + "\n" +
            new_content[region_end:]
        )

    # 3. Replace variable references in the Task description
    # Find all === HEADER === + {var} blocks and replace with one {prompt_context}
    # Strategy: find the first {old_var}, replace with {prompt_context},
    # remove all subsequent {old_var} references and their headers
    first_replaced = False
    for var in var_names:
        # Pattern: === SOME HEADER ===\n{var_name}
        header_var_pattern = re.compile(
            r'(===\s*[^=]+===\s*\n)\s*\{' + re.escape(var) + r'\}',
            re.IGNORECASE
        )
        # Pattern: just {var_name} on its own line (conditional blocks, etc.)
        bare_var_pattern = re.compile(
            r'\{' + re.escape(var) + r'\}',
        )

        if not first_replaced:
            # Replace the first header+var block with {prompt_context}
            m = header_var_pattern.search(new_content)
            if m:
                new_content = (
                    new_content[:m.start()] +
                    "=== UPSTREAM CONTEXT ===\n{prompt_context}" +
                    new_content[m.end():]
                )
                first_replaced = True
                continue

        # For all subsequent vars, remove the header+var or just the var
        m = header_var_pattern.search(new_content)
        if m:
            new_content = new_content[:m.start()] + new_content[m.end():]
        else:
            # Try bare var replacement (e.g., conditional f-string blocks)
            m = bare_var_pattern.search(new_content)
            if m:
                # Check if it's in a line by itself or part of conditional
                line_start = new_content.rfind('\n', 0, m.start())
                line_end = new_content.find('\n', m.end())
                line = new_content[line_start:line_end] if line_end > 0 else new_content[line_start:]
                # If the line is JUST the variable reference, remove the whole line
                if line.strip() == '{' + var + '}':
                    new_content = new_content[:line_start] + new_content[line_end:]

    # Clean up any double-blank-line runs created by removals
    new_content = re.sub(r'\n{4,}', '\n\n\n', new_content)

    # 4. Add on_artifact_saved after the artifact write
    produces = agent_info["produces"]
    # Find the pattern: context["artifacts"].append(
    artifact_append = re.search(
        r'(    context\["artifacts"\]\.append\(.+?\))\s*\n',
        new_content,
        re.DOTALL
    )
    if artifact_append:
        # Find the variable name used for the output path
        path_pattern = re.search(
            r'"path":\s*(\w+)',
            artifact_append.group(0)
        )
        if path_pattern:
            path_var = path_pattern.group(1)
            insert_after = artifact_append.end()
            hook_line = f'    on_artifact_saved(context, "{produces}", {path_var})\n'
            if hook_line.strip() not in new_content:
                new_content = (
                    new_content[:insert_after] +
                    hook_line +
                    new_content[insert_after:]
                )

    if dry_run:
        return "WOULD_MIGRATE", f"{len(findings)} read blocks → smart extraction"

    # Backup original
    backup_path = filepath + ".bak"
    shutil.copy2(filepath, backup_path)

    # Write migrated file
    with open(filepath, "w") as f:
        f.write(new_content)

    return "MIGRATED", f"{len(findings)} read blocks → smart extraction (backup: {backup_path})"


def revert_migration(base_dir):
    """Revert all migrations from .bak files."""
    count = 0
    for rel_path in AGENT_REGISTRY:
        full_path = os.path.join(base_dir, "agents", rel_path)
        backup = full_path + ".bak"
        if os.path.exists(backup):
            shutil.copy2(backup, full_path)
            os.remove(backup)
            count += 1
            print(f"  ↩️  Reverted: {rel_path}")
    return count


# ═══════════════════════════════════════════════════════════════════
#  MANUAL MIGRATION GENERATOR — for files the regex can't handle
# ═══════════════════════════════════════════════════════════════════

def generate_manual_patch(filepath, rel_path, agent_info):
    """
    For files where automatic regex replacement is too risky,
    generate a .patch file showing exactly what to change.
    """
    findings, already_migrated, content = analyze_file(filepath)
    if already_migrated or not findings:
        return None

    agent_id = agent_info["agent_id"]
    consumes = agent_info["consumes"]
    produces = agent_info["produces"]

    types_str = ", ".join(f'"{t}"' for t in consumes)

    patch = f"""# ═══════════════════════════════════════════════════════════
# MANUAL MIGRATION: {rel_path}
# Agent ID: {agent_id}
# Consumes: {', '.join(consumes)}
# Produces: {produces}
# ═══════════════════════════════════════════════════════════

# STEP 1: Add this import near the top of the file
# (after other imports, before build_* function)

from agents.orchestrator.context_manager import (
    load_agent_context, format_context_for_prompt, on_artifact_saved
)

# STEP 2: Replace the read blocks in the run_* function.
# REMOVE these {len(findings)} blocks:

"""
    for f in findings:
        patch += f"#   {f['var']} = f.read()[:{f['chars']}]  (from {f['path_var']})\n"

    patch += f"""
# REPLACE WITH:

    ctx = load_agent_context(
        context=context,
        consumer="{agent_id}",
        artifact_types=[{types_str}],
        max_chars_per_artifact=6000
    )
    prompt_context = format_context_for_prompt(ctx)

# STEP 3: In the Task description f-string, replace all the individual
# variable blocks with a single {{prompt_context}} reference.
#
# BEFORE:
#   === SOME ARTIFACT ===
#   {{{findings[0]['var'] if findings else 'var'}}}
#
# AFTER:
#   === UPSTREAM CONTEXT ===
#   {{prompt_context}}

# STEP 4: After the artifact save (context["artifacts"].append(...)),
# add:
    on_artifact_saved(context, "{produces}", output_path_variable)
"""
    return patch


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    dry_run = "--dry-run" in sys.argv
    revert = "--revert" in sys.argv
    manual = "--manual" in sys.argv
    base_dir = os.path.expanduser("~/dev-team")

    # Allow override
    for arg in sys.argv[1:]:
        if not arg.startswith("--") and os.path.isdir(arg):
            base_dir = arg

    print(f"\n{'='*60}")
    print(f"  Smart Extraction Migration Tool")
    print(f"  Base: {base_dir}")
    print(f"  Mode: {'DRY RUN' if dry_run else 'REVERT' if revert else 'MANUAL PATCHES' if manual else 'LIVE'}")
    print(f"{'='*60}\n")

    if revert:
        count = revert_migration(base_dir)
        print(f"\n✅ Reverted {count} files")
        return

    # Find agent files
    agents_found = find_agent_files(base_dir)

    if not agents_found:
        print("❌ No agent files found. Check base directory.")
        print(f"   Looking in: {base_dir}/agents/")
        print(f"   Registered: {len(AGENT_REGISTRY)} agents")
        return

    # Categorize files
    results = {
        "MIGRATED": [],
        "WOULD_MIGRATE": [],
        "SKIP": [],
        "ERROR": [],
    }

    if manual:
        # Generate manual patch files
        patch_dir = os.path.join(base_dir, "agents/utils/patches")
        os.makedirs(patch_dir, exist_ok=True)
        count = 0
        for full_path, rel_path, info in agents_found:
            patch = generate_manual_patch(full_path, rel_path, info)
            if patch:
                patch_file = os.path.join(
                    patch_dir,
                    rel_path.replace("/", "_").replace(".py", "_patch.txt")
                )
                with open(patch_file, "w") as f:
                    f.write(patch)
                print(f"  📝 {rel_path} → {os.path.basename(patch_file)}")
                count += 1
            else:
                print(f"  ⏭️  {rel_path} (already migrated or no patterns)")
        print(f"\n✅ Generated {count} patch files in {patch_dir}")
        return

    for full_path, rel_path, info in agents_found:
        try:
            status, message = apply_migration(full_path, info, dry_run=dry_run)
            results[status].append((rel_path, message))
            icon = {"MIGRATED": "✅", "WOULD_MIGRATE": "🔍", "SKIP": "⏭️ ", "ERROR": "❌"}
            print(f"  {icon.get(status, '?')} {rel_path}: {message}")
        except Exception as e:
            results["ERROR"].append((rel_path, str(e)))
            print(f"  ❌ {rel_path}: {e}")

    # Not-found agents
    found_paths = {r for _, r, _ in agents_found}
    not_found = set(AGENT_REGISTRY.keys()) - found_paths
    if not_found:
        print(f"\n  ⚠️  Not found ({len(not_found)} files):")
        for p in sorted(not_found):
            print(f"     {p}")

    # Summary
    print(f"\n{'─'*60}")
    print(f"  Summary:")
    for status, items in results.items():
        if items:
            label = {
                "MIGRATED": "Migrated",
                "WOULD_MIGRATE": "Would migrate",
                "SKIP": "Skipped",
                "ERROR": "Errors",
            }
            print(f"    {label.get(status, status)}: {len(items)}")

    if dry_run and results["WOULD_MIGRATE"]:
        print(f"\n  Run without --dry-run to apply changes.")
        print(f"  Run with --manual to generate patch files instead.")

    if results.get("MIGRATED"):
        print(f"\n  Backup files created (.bak). To revert:")
        print(f"    python {__file__} --revert")


if __name__ == "__main__":
    main()
