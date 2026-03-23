"""
Migration Example: backend_developer.py

This file shows exactly how to convert an existing agent from
first-N-characters extraction to smart extraction.

Only the run_* function changes. The build_* function stays the same.
"""

# ══════════════════════════════════════════════════════════════
#  BEFORE — first-N-characters
# ══════════════════════════════════════════════════════════════

def run_backend_implementation_OLD(context, tip_path, tad_path):
    """OLD: reads first 3000/2000 chars regardless of content."""

    with open(tip_path) as f:
        tip_content = f.read()[:3000]  # might be TOC + intro, misses API contracts

    with open(tad_path) as f:
        tad_content = f.read()[:2000]  # might be system overview, misses data architecture

    bd = build_backend_developer()

    task_description = f"""
... {tip_content} ...
... {tad_content} ...
"""
    # The agent gets:
    #   - TIP: Table of contents + project structure (first 3000 chars)
    #   - TAD: System overview + technology stack (first 2000 chars)
    #
    # The agent MISSES:
    #   - TIP: API contracts (char ~4000), module boundaries (char ~5000)
    #   - TAD: Data architecture (char ~6000), security controls (char ~8000)
    #   - MTP: Test cases it should code against (not loaded at all)
    #   - TAR: Pre-written tests (not loaded at all)


# ══════════════════════════════════════════════════════════════
#  AFTER — smart extraction
# ══════════════════════════════════════════════════════════════

def run_backend_implementation_NEW(context, tip_path, tad_path):
    """NEW: extracts exactly the sections the backend dev needs."""

    from agents.orchestrator.context_manager import (
        load_agent_context,
        format_context_for_prompt
    )

    # One call loads everything with smart section extraction
    ctx = load_agent_context(
        context=context,
        consumer="backend_dev",           # looks up CONTEXT_MAP["backend_dev"]
        artifact_types=["TIP", "TAD", "MTP", "TAR"],
        max_chars_per_artifact=6000
    )

    # Format for prompt insertion
    prompt_context = format_context_for_prompt(ctx)

    bd = build_backend_developer()

    task_description = f"""
{prompt_context}
"""
    # The agent now gets:
    #   FROM TIP: api contracts, project structure, module boundaries,
    #             coding standards, implementation sequence, dependencies
    #   FROM TAD: api specifications, data architecture, authentication,
    #             authorization, component descriptions
    #   FROM MTP: api test cases, backend test cases, integration tests
    #   FROM TAR: unit tests, api tests, integration tests
    #
    # Total: ~24,000 chars of RELEVANT content vs 5,000 chars of RANDOM content


# ══════════════════════════════════════════════════════════════
#  STEP-BY-STEP MIGRATION FOR ANY AGENT
# ══════════════════════════════════════════════════════════════
#
#  1. Add import at top of file:
#
#       from agents.orchestrator.context_manager import (
#           load_agent_context,
#           format_context_for_prompt
#       )
#
#  2. In the run_* function, replace:
#
#       with open(tip_path) as f:
#           tip_content = f.read()[:3000]
#       with open(tad_path) as f:
#           tad_content = f.read()[:2000]
#
#     With:
#
#       ctx = load_agent_context(
#           context=context,
#           consumer="THIS_AGENT_ID",    # e.g., "backend_dev"
#           artifact_types=["TIP", "TAD"],
#           max_chars_per_artifact=6000
#       )
#       prompt_context = format_context_for_prompt(ctx)
#
#  3. In the Task description, replace individual variables:
#
#       {tip_content}
#       {tad_content}
#
#     With the single formatted context:
#
#       {prompt_context}
#
#  4. Remove unused path parameters from function signature
#     (or keep them for backwards compatibility).
#
#  5. Optionally add indexing after artifact save:
#
#       from agents.orchestrator.context_manager import on_artifact_saved
#       on_artifact_saved(context, "BIR", bir_path)
#
#  That's it. No changes to build_* function, Agent definition,
#  backstory, or task expected_output.
#
# ══════════════════════════════════════════════════════════════
#  AGENT ID REFERENCE (for consumer parameter)
# ══════════════════════════════════════════════════════════════
#
#  Planning:     biz_analyst, scrum_master, architect, security,
#                ux_designer, ux_content
#  Test Spec:    senior_dev, perf_plan, qa_lead, test_auto
#  Build:        backend_dev, frontend_dev, dba, desktop_dev,
#                devops, devex_writer
#  Verify:       pen_test, scale_arch, perf_audit, a11y_audit,
#                license_scan, verify
#  Mobile:       mobile_qa, ios_dev, android_dev, rn_arch_p1,
#                rn_dev, mobile_devops, mobile_pen_test,
#                mobile_scale, mobile_verify
