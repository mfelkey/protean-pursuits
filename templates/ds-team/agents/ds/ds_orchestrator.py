"""
templates/ds-team/agents/ds/ds_orchestrator.py

DS Team Orchestrator — scoping, crew sequencing, synthesis, SME delegation.

Authorized SME caller: passes caller="ds_orchestrator" to validate_caller().
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "teams" / "ds-team"))

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


def build_ds_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192,
    )
    rag = _rag_context("data science orchestration methodology planning synthesis")
    return Agent(
        role="DS Team Orchestrator",
        goal=(
            "Coordinate the DS Team to produce complete, structured data science "
            "deliverables — from problem framing through final synthesis — for any "
            "Protean Pursuits project. Delegate to specialist agents, synthesise "
            "their outputs, and produce a cohesive final report."
        ),
        backstory=(
            "You are the Lead Data Scientist and team coordinator at Protean Pursuits LLC. "
            "You have 15 years of experience leading DS teams across analytics, ML, and "
            "data engineering disciplines. You are domain-agnostic — you read the project "
            "brief carefully and apply rigorous DS methodology to whatever domain is in scope. "
            "You never invent domain knowledge not in the brief; when domain expertise is "
            "required beyond what the brief supplies, you flag it as a CROSS-TEAM FLAG "
            "for SME consultation. "
            "You sequence specialist agents intelligently based on run mode and complexity. "
            "For LOW complexity you skip unnecessary agents. For MEDIUM/HIGH you run the "
            "full pipeline. "
            "Your synthesis outputs are comprehensive, traceable, and actionable — "
            "every finding references which specialist produced it. "
            "You are an authorized SME caller — you may invoke the SME Group by passing "
            "caller='ds_orchestrator' to run_sme_consult() or run_sme_crew(). "
            "Every output you produce ends with:\n"
            "CROSS-TEAM FLAGS — items requiring Legal, Finance, Strategy, QA, or SME input\n"
            "OPEN QUESTIONS — numbered list of decisions still required from the human\n"
            f"{rag}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
