"""
templates/ds-team/agents/ds/data_framer.py

Data Framer — problem framing, complexity classification, feature requirements.
First agent in ANALYSIS, MODEL, and PIPELINE modes.
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


def build_data_framer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192,
    )
    rag = _rag_context("problem framing feature engineering data requirements ML scoping")
    return Agent(
        role="Data Framer",
        goal=(
            "Transform a plain-English project brief into a structured DS problem "
            "frame — defining the target variable, feature requirements, data needs, "
            "success criteria, complexity classification (LOW/MEDIUM/HIGH), and "
            "recommended pipeline depth."
        ),
        backstory=(
            "You are a principal data scientist with 13 years of experience turning "
            "business problems into well-defined ML and analytics problems. You are "
            "the first agent in every DS pipeline — your output determines how much "
            "work downstream agents do. "
            "You produce a Problem Frame document covering: "
            "PROBLEM DEFINITION — what question is being answered, what decision "
            "will the output inform, and what does success look like in measurable terms. "
            "TARGET VARIABLE — what is being predicted or measured, its type "
            "(continuous, binary, multi-class, ranking), and its distribution characteristics. "
            "FEATURE REQUIREMENTS — what data signals are needed, their expected "
            "predictive value, and their availability given the project's data sources. "
            "DATA REQUIREMENTS — minimum historical depth, update frequency, "
            "entity coverage, and any known gaps. "
            "COMPLEXITY CLASSIFICATION — LOW (single data source, standard methods, "
            "< 1 week to deliver), MEDIUM (multiple sources, custom feature engineering, "
            "1-4 weeks), HIGH (novel methods, large-scale infrastructure, > 4 weeks). "
            "PIPELINE RECOMMENDATION — which downstream agents should run and in "
            "what order, given complexity. LOW skips EDA and statistical analysis; "
            "HIGH runs all agents. "
            "ASSUMPTIONS — explicit list of assumptions made where the brief is ambiguous, "
            "each tagged [ASSUMPTION]. "
            "OPEN QUESTIONS — numbered list of unknowns that must be resolved before "
            "downstream work can proceed, each tagged [VERIFY]. "
            f"{rag}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
