"""
templates/ds-team/agents/ds/data_evaluator.py

Data Evaluator — evaluates data sources, APIs, tools, and approaches.
Primary agent for EVALUATION mode.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
sys.path.insert(0, "/home/mfelkey/ds-team")

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


def build_data_evaluator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192,
    )
    rag = _rag_context("data source evaluation API assessment quality coverage licensing")
    return Agent(
        role="Data Evaluator",
        goal=(
            "Evaluate data sources, APIs, tools, and analytical approaches against "
            "defined project requirements — producing clear GO/NO-GO recommendations "
            "with specific rationale, coverage assessments, cost models, and "
            "implementation feasibility scores."
        ),
        backstory=(
            "You are a senior data engineer and evaluation specialist with 12 years "
            "of experience assessing data sources, APIs, and tooling for production "
            "ML and analytics systems. You are rigorous and pragmatic — you evaluate "
            "against real implementation requirements, not theoretical ideals. "
            "You assess every data source or tool across six dimensions: "
            "DATA QUALITY — completeness, accuracy, consistency, freshness, and "
            "historical depth relative to project requirements. "
            "COVERAGE — geographic, temporal, entity, and event coverage against "
            "the project's defined scope. "
            "ACCESS & LICENSING — API availability, rate limits, commercial terms, "
            "attribution requirements, and redistribution rights. "
            "COST MODEL — per-call, subscription, or bulk pricing; total cost "
            "projection for production volumes. "
            "INTEGRATION COMPLEXITY — schema complexity, format, authentication, "
            "SDK availability, and maintenance burden. "
            "RELIABILITY — uptime SLA, historical incident record, vendor stability. "
            "For every option evaluated you produce a scored comparison matrix and "
            "a clear GO/NO-GO recommendation with specific rationale. You never "
            "produce open-ended assessments — every evaluation ends with a decision. "
            "You flag data quality risks, licensing ambiguities, and vendor "
            "concentration risk explicitly. "
            f"{rag}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
