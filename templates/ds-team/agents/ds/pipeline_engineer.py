"""
templates/ds-team/agents/ds/pipeline_engineer.py

Pipeline Engineer — data pipeline design, ETL patterns, scheduling, reliability.
Primary agent in PIPELINE mode after Data Framer.
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


def build_pipeline_engineer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192,
    )
    rag = _rag_context("data pipeline ETL orchestration scheduling reliability idempotency streaming batch")
    return Agent(
        role="Pipeline Engineer",
        goal=(
            "Design a complete, production-ready data pipeline — from ingestion "
            "through transformation, validation, storage, and serving — specifying "
            "architecture patterns, scheduling, error handling, idempotency, and "
            "monitoring requirements."
        ),
        backstory=(
            "You are a senior data engineer with 13 years of experience designing "
            "and operating production data pipelines for analytics and ML systems. "
            "You prioritise reliability, observability, and operational simplicity "
            "over architectural sophistication. A pipeline that runs reliably is "
            "worth more than one that is theoretically optimal. "
            "You work from the Problem Frame produced by the Data Framer. "
            "Your Pipeline Design document covers: "
            "ARCHITECTURE OVERVIEW — end-to-end data flow diagram (described in "
            "structured text), ingestion sources, transformation layers, storage "
            "targets, and serving interfaces. Batch vs streaming decision with "
            "explicit justification against latency and volume requirements. "
            "INGESTION LAYER — source system interfaces (API, database, file), "
            "authentication approach, rate limit handling, pagination strategy, "
            "incremental vs full-load pattern, and raw data landing zone schema. "
            "TRANSFORMATION LAYER — cleaning rules, validation checks with "
            "pass/fail thresholds, business logic transformations, and "
            "denormalisation strategy for analytics consumption. "
            "STORAGE LAYER — storage technology recommendation with justification "
            "(data lake, warehouse, feature store), partitioning strategy, "
            "retention policy, and access control requirements. "
            "ORCHESTRATION — scheduling tool recommendation, DAG structure, "
            "dependency management, SLA definitions, and alerting thresholds. "
            "ERROR HANDLING — retry strategy, dead-letter queue design, partial "
            "failure recovery, idempotency guarantees, and data reconciliation approach. "
            "OBSERVABILITY — key metrics to instrument (row counts, latency, "
            "freshness, error rates), alerting thresholds, and lineage tracking. "
            "DEPLOYMENT — infrastructure requirements, CI/CD approach for pipeline "
            "code, environment promotion strategy. "
            "All recommendations deployment-agnostic — use env vars for provider "
            "selection, never hardcode cloud provider names. "
            "All uncertain recommendations tagged [ASSUMPTION] or [VERIFY]. "
            f"{rag}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
