import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
import glob
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

DOCUMENT_PAIRS = [
    {
        "label": "DIR",
        "original_type": "DIR",
        "revised_type": "DIR_R",
    },
    {
        "label": "BIR",
        "original_type": "BIR",
        "revised_type": "BIR_R",
    },
    {
        "label": "MTP",
        "original_type": "MTP",
        "revised_type": "MTP_R",
    },
    {
        "label": "TAD",
        "original_type": "TAD",
        "revised_type": "TAD_R",
    },
    {
        "label": "SRR",
        "original_type": "SRR",
        "revised_type": "SRR_R",
    },
]


def build_reconciliation_agent() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Technical Document Reviewer",
        goal=(
            "Compare an original document against its revised version and produce "
            "a precise gap report identifying: sections dropped, content thinned, "
            "and detail missing from the revised version that was present in the original."
        ),
        backstory=(
            "You are a meticulous Technical Document Reviewer with experience auditing "
            "government system documentation for completeness and accuracy. "
            "You compare documents section by section, identifying exactly what was "
            "lost in revision. You do not evaluate quality or style — only completeness. "
            "Your output is always a structured gap report, never prose."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def reconcile_pair(agent, label: str, original_path: str, revised_path: str) -> str:
    with open(original_path) as f:
        original = f.read()
    with open(revised_path) as f:
        revised = f.read()

    task = Task(
        description=f"""
You are comparing the ORIGINAL {label} document against its REVISED {label}-R version.

Your job is to produce a structured gap report identifying content present in the
original that is missing or significantly reduced in the revised version.

--- ORIGINAL {label} ---
{original}

--- REVISED {label}-R ---
{revised}

Produce a gap report in this exact format:

## {label} Reconciliation Report

### Sections in Original
List every top-level section heading found in the original document.

### Sections in Revised
List every top-level section heading found in the revised document.

### Dropped Sections
List any sections present in the original but completely absent from the revised.
If none, write: None.

### Thinned Sections
List sections present in both but where the revised version has significantly less
detail, fewer subsections, or missing specific content items.
For each, note specifically what was removed or reduced.
If none, write: None.

### New Sections in Revised
List any sections added in the revised version not present in the original.
If none, write: None.

### Summary
One paragraph summarizing the overall completeness of the revised document
relative to the original. Note whether the revision is safe to use as a
replacement or requires a merge pass.
""",
        expected_output=f"A structured gap report for the {label} document pair.",
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔍 Reconciling {label}...\n")
    result = crew.kickoff()
    return str(result)


if __name__ == "__main__":
    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    # Build path lookup from context artifacts
    path_lookup = {}
    for artifact in context.get("artifacts", []):
        path_lookup[artifact["type"]] = artifact["path"]

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Artifacts found: {list(path_lookup.keys())}")

    report_sections = [
        f"# Reconciliation Report — PROJ-TEMPLATE\n",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"**Purpose:** Gap analysis comparing original documents against retrofit-revised versions.\n",
        f"\n---\n",
    ]

    for pair in DOCUMENT_PAIRS:
        label = pair["label"]
        orig_type = pair["original_type"]
        rev_type = pair["revised_type"]

        orig_path = path_lookup.get(orig_type)
        rev_path = path_lookup.get(rev_type)

        if not orig_path or not os.path.exists(orig_path):
            print(f"⚠️  Original {label} not found in context or on disk. Skipping.")
            report_sections.append(f"## {label} — SKIPPED (original not found)\n\n---\n")
            continue

        if not rev_path or not os.path.exists(rev_path):
            print(f"⚠️  Revised {label}-R not found in context or on disk. Skipping.")
            report_sections.append(f"## {label} — SKIPPED (revised not found)\n\n---\n")
            continue

        agent = build_reconciliation_agent()
        gap_report = reconcile_pair(agent, label, orig_path, rev_path)
        report_sections.append(gap_report)
        report_sections.append("\n---\n")

    full_report = "\n".join(report_sections)
    report_path = "RECONCILIATION.md"
    with open(report_path, "w") as f:
        f.write(full_report)

    print(f"\n✅ Reconciliation complete.")
    print(f"📄 Report: {report_path}")

    log_event(context, "RECONCILIATION_COMPLETE", report_path)
    save_context(context)
