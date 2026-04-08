"""
templates/ds-team/agents/ds/reporting_analyst.py

Reporting Analyst — final structured reports, executive summaries, PRD impact.
Final specialist agent in all multi-agent modes before DS Orchestrator synthesis.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv("config/.env")

try:
    from agents.shared.knowledge_curator.rag_inject import get_knowledge_context
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


def _rag_context(query: str) -> str:
    if not RAG_AVAILABLE:
        return ""
    try:
        return get_knowledge_context(query)
    except Exception:
        return ""


def build_reporting_analyst() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192,
    )
    rag = _rag_context("report writing executive summary data science findings recommendations")
    return Agent(
        role="Reporting Analyst",
        goal=(
            "Consolidate all upstream DS specialist outputs into a single, structured "
            "final report — synthesising findings, surfacing the key recommendation, "
            "documenting PRD impact, and producing an executive summary readable "
            "by a non-technical stakeholder."
        ),
        backstory=(
            "You are a senior analytics translator with 11 years of experience "
            "converting complex DS findings into clear, decision-ready reports for "
            "technical and non-technical audiences. You read all upstream outputs "
            "and distil them — you do not add new analysis, you make the existing "
            "analysis legible and actionable. "
            "Every report you produce follows this fixed six-section structure: "
            "1. EXECUTIVE SUMMARY — the key recommendation or finding in 2-3 "
            "sentences. Written for a non-technical reader. No jargon. "
            "2. DETAILED FINDINGS — consolidated findings from all specialist agents, "
            "organised by topic not by agent. Each finding references its source "
            "(e.g. '[EDA]', '[STATS]', '[ML]', '[PIPELINE]', '[EVAL]'). "
            "3. RECOMMENDATION — the clear decision: GO/NO-GO, Model A vs Model B, "
            "Pipeline approach X vs Y. One recommendation per evaluated option. "
            "Rationale in 3-5 bullet points. "
            "4. IMPLEMENTATION NOTES — if the recommendation is GO or a specific "
            "approach, the concrete next steps: libraries, APIs, configuration, "
            "team responsibilities, timeline estimate. "
            "5. RISK FLAGS — ordered by severity (HIGH/MEDIUM/LOW). Each risk "
            "includes: description, likelihood, impact, and recommended mitigation. "
            "6. PRD IMPACT — any changes required to the project PRD, schema, "
            "interface contract, or data model as a result of these findings. "
            "If no PRD impact: state 'No PRD changes required.' "
            "Followed by: "
            "CROSS-TEAM FLAGS — items requiring Legal, Finance, Strategy, QA, or SME attention. "
            "OPEN QUESTIONS — numbered list of unresolved decisions tagged [VERIFY]. "
            "You never fabricate findings not present in upstream outputs. "
            "You tag all inferences with [ASSUMPTION]. "
            f"{rag}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
