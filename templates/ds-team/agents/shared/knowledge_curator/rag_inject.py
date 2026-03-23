"""
RAG Knowledge Injection

Queries ChromaDB knowledge collections and returns formatted context
to inject into agent task descriptions. This is the bridge between
the Knowledge Curator (which feeds ChromaDB) and the working agents
(which consume the knowledge).

Usage in any agent:

    from agents.shared.knowledge_curator.rag_inject import get_knowledge_context

    # In your run_* function, before building the Task:
    knowledge = get_knowledge_context(
        agent_role="Backend Developer",
        task_summary="Build REST API endpoints for project data",
        collections=["dev_practices", "system_updates"],
    )

    # Then include it in the task description:
    task = Task(
        description=f'''
        {your_existing_task_description}

        CURRENT KNOWLEDGE (from knowledge base — use if relevant):
        {knowledge}
        ''',
        ...
    )

The function is designed to be:
  - Zero-impact if ChromaDB is empty or unavailable (returns empty string)
  - Lightweight (single query per collection, ~100ms total)
  - Conservative (returns top 3 results by default to avoid context bloat)
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger("knowledge_curator.rag_inject")

# ── Agent Role → Collection Mapping ──────────────────────────────
# Determines which collections each agent queries.
# Agents not listed here get ["dev_practices", "system_updates"] by default.

AGENT_COLLECTION_MAP = {
    # Strategy layer
    "Product Manager": ["dev_practices", "domain_va", "domain_healthcare"],
    "Business Analyst": ["dev_practices", "domain_va", "domain_healthcare"],
    "Scrum Master": ["dev_practices"],
    "Technical Architect": ["dev_practices", "system_updates"],
    "Security Reviewer": ["dev_practices", "system_updates", "domain_healthcare"],
    "UX/UI Designer": ["dev_practices", "domain_healthcare"],
    "UX Content Guide": ["dev_practices", "domain_healthcare"],

    # Build layer
    "Senior Developer": ["dev_practices", "system_updates"],
    "Backend Developer": ["dev_practices", "system_updates"],
    "Frontend Developer": ["dev_practices", "system_updates"],
    "Database Administrator": ["dev_practices", "system_updates"],
    "DevOps Engineer": ["dev_practices", "system_updates"],

    # Quality layer
    "QA Lead": ["dev_practices", "system_updates"],
    "Test Automation Engineer": ["dev_practices", "system_updates"],

    # Mobile layer
    "Mobile UX Designer": ["dev_practices", "domain_healthcare"],
    "iOS Developer": ["dev_practices", "system_updates"],
    "Android Developer": ["dev_practices", "system_updates"],
    "RN Architect": ["dev_practices", "system_updates"],
    "RN Developer": ["dev_practices", "system_updates"],
    "Mobile DevOps": ["dev_practices", "system_updates"],
    "Mobile QA": ["dev_practices", "system_updates"],

    # DS layer
    "Data Strategist": ["ds_methods", "domain_va", "domain_healthcare"],
    "Domain Analyst": ["domain_va", "domain_healthcare"],
    "Data Engineer": ["ds_methods", "dev_practices"],
    "Statistical Modeler": ["ds_methods"],
    "ML Engineer": ["ds_methods", "dev_practices"],
    "Simulation Engineer": ["ds_methods"],

    # Orchestration
    "Orchestrator": ["system_updates", "dev_practices", "ds_methods"],
    "Dev-Team Orchestrator": ["system_updates", "dev_practices"],
}


def get_knowledge_context(
    agent_role: str,
    task_summary: str,
    collections: Optional[list[str]] = None,
    n_results: int = 3,
    max_chars_per_result: int = 500,
    filter_by_agent: bool = True,
) -> str:
    """
    Query ChromaDB for knowledge relevant to the agent's current task.

    Args:
        agent_role: The agent's role name (e.g., "Backend Developer")
        task_summary: Brief description of the task (used as semantic query)
        collections: Override which collections to query. If None, uses AGENT_COLLECTION_MAP.
        n_results: Number of results per collection (default 3)
        max_chars_per_result: Truncate each result to this many chars
        filter_by_agent: If True, filter results by target_agents metadata

    Returns:
        Formatted string of relevant knowledge, or empty string if none found.
    """
    try:
        load_dotenv("config/.env")

        # Import here to avoid circular deps and allow graceful failure
        from agents.shared.knowledge_curator.ingestion.chroma_manager import (
            get_client,
            embed_text,
        )

        client = get_client()

        # Determine which collections to query
        if collections is None:
            collections = AGENT_COLLECTION_MAP.get(
                agent_role, ["dev_practices", "system_updates"]
            )

        all_results = []

        for coll_name in collections:
            try:
                collection = client.get_or_create_collection(name=coll_name)

                if collection.count() == 0:
                    continue

                # Build query
                query_embedding = embed_text(task_summary[:500])

                kwargs = {
                    "query_embeddings": [query_embedding],
                    "n_results": min(n_results, collection.count()),
                }

                # Optionally filter by agent role
                if filter_by_agent:
                    kwargs["where"] = {
                        "$or": [
                            {"target_agents": {"$contains": agent_role}},
                            {"target_agents": {"$contains": "all"}},
                        ]
                    }

                try:
                    results = collection.query(**kwargs)
                except Exception:
                    # Fall back without filter if metadata filtering fails
                    kwargs.pop("where", None)
                    results = collection.query(**kwargs)

                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = {}
                        if results["metadatas"] and results["metadatas"][0]:
                            metadata = results["metadatas"][0][i]

                        all_results.append({
                            "collection": coll_name,
                            "title": metadata.get("title", ""),
                            "source_type": metadata.get("source_type", ""),
                            "score": metadata.get("relevance_score", 0),
                            "text": doc[:max_chars_per_result],
                        })

            except Exception as e:
                logger.debug(f"  Collection {coll_name} query failed: {e}")
                continue

        if not all_results:
            return ""

        # Format results
        return _format_results(all_results)

    except ImportError:
        logger.debug("ChromaDB not available — skipping RAG injection")
        return ""
    except Exception as e:
        logger.debug(f"RAG injection failed (non-fatal): {e}")
        return ""


def _format_results(results: list[dict]) -> str:
    """Format query results into a clean context block for the agent."""
    if not results:
        return ""

    lines = []
    lines.append("─" * 50)

    seen_titles = set()
    for r in results:
        title = r.get("title", "")
        if title in seen_titles:
            continue
        seen_titles.add(title)

        source_label = _source_label(r.get("source_type", ""))
        lines.append(f"[{source_label}] {title}")
        lines.append(r["text"])
        lines.append("")

    lines.append("─" * 50)
    return "\n".join(lines)


def _source_label(source_type: str) -> str:
    """Human-readable label for source types."""
    labels = {
        "github_release": "RELEASE",
        "arxiv_paper_cs": "PAPER",
        "arxiv_paper_stat": "PAPER",
        "arxiv_paper_cs_ai": "PAPER",
        "cve_advisory": "SECURITY",
        "owasp_update": "SECURITY",
        "va_bulletin": "VA/POLICY",
        "cms_bulletin": "CMS/POLICY",
    }
    return labels.get(source_type, "INFO")


# ── Convenience wrapper for common patterns ───────────────────────

def inject_for_agent(
    agent_role: str,
    project_spec: str,
    extra_context: str = "",
) -> str:
    """
    High-level wrapper: builds a task summary from the project spec
    and returns formatted knowledge context.

    Usage:
        knowledge = inject_for_agent("Backend Developer", spec_text)
    """
    # Use first 200 chars of project spec + agent role as the semantic query
    task_summary = f"{agent_role} task for: {project_spec[:200]}"
    if extra_context:
        task_summary += f" {extra_context[:100]}"

    return get_knowledge_context(
        agent_role=agent_role,
        task_summary=task_summary,
    )
