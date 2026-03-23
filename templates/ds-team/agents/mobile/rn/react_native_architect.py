"""
React Native Developer Agent
=============================
Generates a complete React Native (Expo) implementation guide in two parts.

Part 1: Sections 1-5 (Project setup, navigation, state management, API layer, shared components)
Part 2: Sections 6-10 (Screens, forms/validation, offline support, testing, build/deploy)

Fix log (2026-02-22):
  - Part 2 now receives Part 1 output as context instead of raw architecture doc
  - TASK_PART2 rewritten to contain zero Section 1-5 references
  - validate_agent_output() now checks section numbers to catch regression/looping
"""

import os
import re
import logging
from datetime import datetime
from textwrap import dedent

from crewai import Agent, Task, Crew, Process, LLM

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("rn_developer")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_NAME = os.getenv("RN_DEV_MODEL", "qwen2.5-coder:32b")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MAX_ITER = int(os.getenv("RN_DEV_MAX_ITER", "30"))
TEMPERATURE = float(os.getenv("RN_DEV_TEMPERATURE", "0.2"))
OUTPUT_DIR = os.getenv("RN_DEV_OUTPUT_DIR", os.path.expanduser("~/dev-team/output/mobile/rn"))

# Langfuse observability (optional)
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
if LANGFUSE_ENABLED:
    try:
        from langfuse import Langfuse
        langfuse = Langfuse()
        logger.info("Langfuse observability enabled")
    except ImportError:
        logger.warning("Langfuse not installed; observability disabled")
        LANGFUSE_ENABLED = False

# ---------------------------------------------------------------------------
# TASK PROMPTS
# ---------------------------------------------------------------------------

TASK_PART1 = dedent("""\
    You are a senior React Native developer creating a comprehensive implementation
    guide for a mobile app using Expo and TypeScript.

    Generate Sections 1 through 5 ONLY. Each section must start with a markdown
    heading like "## 1. ..." through "## 5. ...".

    ## 1. Project Setup & Configuration
    - Expo SDK setup with TypeScript template
    - Directory structure (src/screens, src/components, src/hooks, src/services, src/store, src/types, src/utils)
    - ESLint + Prettier configuration
    - Path aliases via babel-plugin-module-resolver
    - Environment variables with expo-constants

    ## 2. Navigation Architecture
    - React Navigation v6 with native stack
    - Type-safe navigation with RootStackParamList
    - Bottom tab navigator with 4-5 primary tabs
    - Nested stack navigators per tab
    - Deep linking configuration
    - Auth flow (login/register → main app switch)

    ## 3. State Management
    - Zustand stores: useAuthStore, useTripStore, useSettingsStore
    - Async persistence with zustand/middleware and AsyncStorage
    - Selectors for derived state
    - Actions with loading/error state patterns

    ## 4. API Layer
    - Axios instance with baseURL, interceptors for auth token refresh
    - Type-safe API client (api/trips.ts, api/auth.ts, api/users.ts)
    - React Query (TanStack Query) for caching, pagination, optimistic updates
    - Custom hooks: useTrips(), useTrip(id), useCreateTrip(), etc.
    - Error handling and retry strategies

    ## 5. Shared UI Components
    - Design tokens (colors, spacing, typography) in theme.ts
    - Button, Card, Input, Badge, Avatar, LoadingOverlay components
    - Each with TypeScript props interface
    - Accessibility: accessibilityLabel, accessibilityRole on all interactive elements
    - Dark mode support via useColorScheme

    OUTPUT FORMAT:
    - Full TypeScript/TSX code blocks with file paths as comments
    - Explanatory prose between code blocks
    - Every section heading must match "## N. <Title>" format exactly
    - Stop after Section 5. Do NOT write Section 6 or beyond.
""")

# NOTE: TASK_PART2 contains ZERO references to Sections 1-5 content.
# It receives Part 1 output as context prefix at runtime.
TASK_PART2 = dedent("""\
    You are continuing an implementation guide that another developer started.
    The first half (Sections 1-5) is ALREADY COMPLETE and provided above as context.

    YOUR JOB: Write Sections 6 through 10 ONLY.
    DO NOT rewrite, revisit, or regenerate ANY content from Sections 1-5.
    DO NOT write code for files that were already created in the context above.
    START your output directly with "## 6." and continue through "## 10.".

    ## 6. Screen Implementations
    - HomeScreen: trip list with FlatList, pull-to-refresh, infinite scroll
    - TripDetailScreen: route params, data fetching, action buttons
    - CreateTripScreen: multi-step form wizard (3 steps)
    - ProfileScreen: user info, settings toggles, logout
    - SearchScreen: debounced search input, filter chips, results list
    - Each screen imports from the shared components and hooks defined earlier
    - Use the navigation types and store hooks from the earlier sections

    ## 7. Forms & Validation
    - React Hook Form with zodResolver
    - Zod schemas: LoginSchema, RegisterSchema, CreateTripSchema
    - Reusable FormField wrapper component
    - Inline error messages with accessibility announcements
    - Keyboard-aware scroll views for form screens

    ## 8. Offline Support & Data Sync
    - NetInfo listener with useNetworkStatus() hook
    - Offline queue in Zustand: pendingActions array
    - Sync service that drains queue when connectivity returns
    - Optimistic UI updates with rollback on sync failure
    - Cache-first strategy with React Query's staleTime/gcTime

    ## 9. Testing Strategy
    - Jest + React Native Testing Library setup
    - Unit tests for Zustand stores (at least 2 example test files)
    - Component tests for 2 shared components (Button, Card)
    - Screen integration test for HomeScreen (mocked navigation + API)
    - API mock patterns with MSW (Mock Service Worker)
    - Snapshot tests for key UI states

    ## 10. Build & Deployment
    - EAS Build configuration (eas.json) for dev, preview, production profiles
    - app.config.ts with dynamic configuration
    - OTA updates with expo-updates
    - App Store / Google Play submission checklist
    - CI/CD with GitHub Actions: lint → test → build → deploy
    - Environment-specific configs (API URLs, feature flags)

    OUTPUT FORMAT:
    - Full TypeScript/TSX code blocks with file paths as comments
    - Explanatory prose between code blocks
    - Every section heading must match "## N. <Title>" format exactly
    - Start at "## 6." — do NOT output "## 1." through "## 5."
""")

# ---------------------------------------------------------------------------
# Agent Builder
# ---------------------------------------------------------------------------

def build_rn_developer() -> Agent:
    """Create the React Native Developer agent."""
    llm = LLM(
        model=f"ollama/{MODEL_NAME}",
        base_url=BASE_URL,
        temperature=TEMPERATURE,
    )
    logger.info(f"LLM configured: ollama/{MODEL_NAME} @ {BASE_URL}")

    return Agent(
        role="Senior React Native Developer",
        goal=(
            "Produce a complete, production-quality React Native (Expo + TypeScript) "
            "implementation guide with working code for every section."
        ),
        backstory=(
            "You are a staff-level mobile engineer with 8+ years of React Native "
            "experience. You've shipped dozens of apps to both stores. You write "
            "clean, type-safe TypeScript and follow React Native community best "
            "practices. You are meticulous about accessibility and offline support."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=MAX_ITER,
    )


# ---------------------------------------------------------------------------
# Output Validation
# ---------------------------------------------------------------------------

def validate_agent_output(
    output: str,
    expected_sections: list[int],
    forbidden_sections: list[int] | None = None,
    part_label: str = "output",
) -> dict:
    """
    Validate that the agent output contains the expected section headings
    and does NOT contain forbidden section headings.

    Returns:
        {
            "valid": bool,
            "found_expected": [int, ...],
            "missing_expected": [int, ...],
            "found_forbidden": [int, ...],
            "duplicate_sections": {section_num: count},
            "errors": [str, ...],
        }
    """
    result = {
        "valid": True,
        "found_expected": [],
        "missing_expected": [],
        "found_forbidden": [],
        "duplicate_sections": {},
        "errors": [],
    }

    if forbidden_sections is None:
        forbidden_sections = []

    # Find all section headings: "## 1.", "## 2.", etc.
    section_pattern = re.compile(r"^##\s+(\d+)\.", re.MULTILINE)
    found_numbers = [int(m.group(1)) for m in section_pattern.finditer(output)]

    # Check for expected sections
    for s in expected_sections:
        if s in found_numbers:
            result["found_expected"].append(s)
        else:
            result["missing_expected"].append(s)
            result["errors"].append(f"{part_label}: Missing expected section ## {s}.")
            result["valid"] = False

    # Check for forbidden sections (regression detection)
    for s in forbidden_sections:
        if s in found_numbers:
            result["found_forbidden"].append(s)
            result["errors"].append(
                f"{part_label}: Found FORBIDDEN section ## {s}. "
                f"Model regenerated content it should not have."
            )
            result["valid"] = False

    # Check for excessive duplication (looping detection)
    from collections import Counter
    counts = Counter(found_numbers)
    for section_num, count in counts.items():
        if count > 1:
            result["duplicate_sections"][section_num] = count
            result["errors"].append(
                f"{part_label}: Section ## {section_num}. appears {count} times (looping detected)."
            )
            result["valid"] = False

    # Check for useTripList.ts looping specifically (the known failure mode)
    trip_list_mentions = len(re.findall(r"useTripList", output))
    if trip_list_mentions > 10:
        result["errors"].append(
            f"{part_label}: 'useTripList' appears {trip_list_mentions} times — "
            f"probable generation loop."
        )
        result["valid"] = False

    return result


# ---------------------------------------------------------------------------
# File I/O Helpers
# ---------------------------------------------------------------------------

def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _write_output(filename: str, content: str) -> str:
    _ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Wrote {len(content)} chars → {path}")
    return path


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_rn_developer() -> dict:
    """
    Execute the RN Developer agent in two sequential Crew runs.

    Part 1: Sections 1-5 (uses TASK_PART1 as-is)
    Part 2: Sections 6-10 (injects Part 1 output as context, uses rewritten TASK_PART2)

    Returns dict with paths, validation results, and status.
    """
    ts = _timestamp()
    agent = build_rn_developer()
    results = {
        "timestamp": ts,
        "part1_path": None,
        "part2_path": None,
        "combined_path": None,
        "part1_validation": None,
        "part2_validation": None,
        "status": "started",
    }

    # -----------------------------------------------------------------------
    # PART 1: Sections 1-5
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("PART 1: Generating Sections 1-5")
    logger.info("=" * 60)

    task_part1 = Task(
        description=TASK_PART1,
        expected_output="Complete implementation guide Sections 1-5 with TypeScript code blocks.",
        agent=agent,
    )

    crew_part1 = Crew(
        agents=[agent],
        tasks=[task_part1],
        process=Process.sequential,
        verbose=True,
    )

    part1_result = crew_part1.kickoff()
    part1_output = str(part1_result)

    # Validate Part 1
    part1_validation = validate_agent_output(
        output=part1_output,
        expected_sections=[1, 2, 3, 4, 5],
        forbidden_sections=[6, 7, 8, 9, 10],
        part_label="Part1",
    )
    results["part1_validation"] = part1_validation

    if not part1_validation["valid"]:
        for err in part1_validation["errors"]:
            logger.warning(f"Part 1 validation: {err}")
    else:
        logger.info("Part 1 validation: PASSED ✓")

    # Save Part 1
    results["part1_path"] = _write_output(f"rn_guide_part1_{ts}.md", part1_output)

    # -----------------------------------------------------------------------
    # PART 2: Sections 6-10  (KEY FIX: inject Part 1 output as context)
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("PART 2: Generating Sections 6-10 (with Part 1 context)")
    logger.info("=" * 60)

    # Build the Part 2 task description by prepending Part 1 output as context.
    # This replaces the old approach of pointing at the raw architecture doc.
    part2_context_prompt = dedent(f"""\
        =====================================================================
        CONTEXT: The following is the ALREADY-COMPLETED Part 1 (Sections 1-5).
        This is provided for reference only. DO NOT regenerate any of this.
        =====================================================================

        {part1_output}

        =====================================================================
        END OF PART 1 CONTEXT. Now continue with YOUR task below.
        =====================================================================

        {TASK_PART2}
    """)

    task_part2 = Task(
        description=part2_context_prompt,
        expected_output="Implementation guide Sections 6-10 ONLY, continuing from Part 1.",
        agent=agent,
    )

    crew_part2 = Crew(
        agents=[agent],
        tasks=[task_part2],
        process=Process.sequential,
        verbose=True,
    )

    part2_result = crew_part2.kickoff()
    part2_output = str(part2_result)

    # Validate Part 2
    part2_validation = validate_agent_output(
        output=part2_output,
        expected_sections=[6, 7, 8, 9, 10],
        forbidden_sections=[1, 2, 3, 4, 5],
        part_label="Part2",
    )
    results["part2_validation"] = part2_validation

    if not part2_validation["valid"]:
        for err in part2_validation["errors"]:
            logger.error(f"Part 2 validation: {err}")
        results["status"] = "part2_validation_failed"
        # Still save the output so you can inspect what went wrong
        results["part2_path"] = _write_output(f"rn_guide_part2_BAD_{ts}.md", part2_output)
        logger.error(
            "Part 2 FAILED validation — output saved with _BAD_ suffix. "
            "The model likely regressed into Part 1 content or looped."
        )
    else:
        logger.info("Part 2 validation: PASSED ✓")
        results["part2_path"] = _write_output(f"rn_guide_part2_{ts}.md", part2_output)
        results["status"] = "success"

    # -----------------------------------------------------------------------
    # Combine if both parts are valid
    # -----------------------------------------------------------------------
    if results["status"] == "success":
        combined = part1_output.rstrip() + "\n\n---\n\n" + part2_output.lstrip()
        results["combined_path"] = _write_output(f"rn_guide_complete_{ts}.md", combined)
        logger.info(f"Combined guide: {results['combined_path']}")
    else:
        logger.warning("Skipping combined output due to validation failure.")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info(f"RN Developer Agent — Status: {results['status']}")
    logger.info(f"  Part 1: {results['part1_path']}")
    logger.info(f"  Part 2: {results['part2_path']}")
    if results["combined_path"]:
        logger.info(f"  Combined: {results['combined_path']}")
    if results["part1_validation"]["errors"]:
        logger.info(f"  Part 1 issues: {results['part1_validation']['errors']}")
    if results["part2_validation"]["errors"]:
        logger.info(f"  Part 2 issues: {results['part2_validation']['errors']}")
    logger.info("=" * 60)

    return results


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    results = run_rn_developer()

    # Print summary to stdout as JSON for pipeline consumption
    print(json.dumps({
        "status": results["status"],
        "part1_path": results["part1_path"],
        "part2_path": results["part2_path"],
        "combined_path": results["combined_path"],
        "part1_valid": results["part1_validation"]["valid"],
        "part2_valid": results["part2_validation"]["valid"],
        "part2_errors": results["part2_validation"]["errors"],
    }, indent=2))
