"""
Knowledge Evaluator Agent

A CrewAI agent that evaluates fetched content for relevance before
it gets ingested into ChromaDB. This prevents low-quality or
irrelevant material from polluting the knowledge base.

The evaluator scores each item 0.0–1.0 and only items above the
configured threshold (default 0.6) get ingested.

Uses Tier 1 model (the thinker) since this is an analytical task.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

logger = logging.getLogger("knowledge_curator.evaluator")


def build_evaluator_agent() -> Agent:
    """Build the Knowledge Evaluator agent."""
    load_dotenv("config/.env")

    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen2.5:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=600,
    )

    return Agent(
        role="Knowledge Evaluator",
        goal=(
            "Evaluate incoming knowledge items for relevance, quality, and "
            "actionability to the AI development agent system. Score each item "
            "and determine which ChromaDB collections and agents it serves."
        ),
        backstory=(
            "You are the Knowledge Evaluator for a federated AI agent system that "
            "builds software (Dev crew) and performs data analysis (DS crew). The "
            "system builds mobile and web applications, with a focus on VA/healthcare "
            "domain projects.\n\n"
            "Your job is to evaluate incoming knowledge items — GitHub releases, ArXiv "
            "papers, CVE advisories, and government bulletins — and determine:\n"
            "1. RELEVANCE SCORE (0.0–1.0): How useful is this to the agent system?\n"
            "2. TARGET AGENTS: Which specific agents benefit from this knowledge?\n"
            "3. KEY TAKEAWAY: A 1–2 sentence summary of what matters.\n"
            "4. EXPIRATION: Should this knowledge expire? When?\n\n"
            "Score HIGH (0.8–1.0) for:\n"
            "- Breaking changes in frameworks the system uses (CrewAI, React Native, Expo)\n"
            "- Critical security vulnerabilities in the stack\n"
            "- VA/CMS policy changes affecting healthcare app development\n"
            "- New techniques directly applicable to agent orchestration or mobile dev\n\n"
            "Score MEDIUM (0.5–0.7) for:\n"
            "- Minor version updates with useful new features\n"
            "- Research papers with interesting but not immediately actionable ideas\n"
            "- General security best practice updates\n\n"
            "Score LOW (0.0–0.4) for:\n"
            "- Unrelated research (e.g., robotics papers in cs.AI)\n"
            "- CVEs for software not in the stack\n"
            "- Routine maintenance releases with no breaking changes\n\n"
            "OUTPUT FORMAT: Respond ONLY with valid JSON. No preamble, no markdown fences.\n"
            "{\n"
            '  "score": 0.85,\n'
            '  "target_agents": ["Security Reviewer", "DevOps Engineer"],\n'
            '  "key_takeaway": "Critical RCE in Node.js 20.x affects backend services.",\n'
            '  "expires_days": 90,\n'
            '  "ingest": true\n'
            "}"
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def evaluate_item(
    agent: Agent,
    title: str,
    content: str,
    source_type: str,
    threshold: float = 0.6,
) -> dict:
    """
    Evaluate a single knowledge item.

    Returns dict with: score, target_agents, key_takeaway, expires_days, ingest (bool).
    Falls back to keyword-based scoring if LLM evaluation fails.
    """
    task = Task(
        description=(
            f"Evaluate this {source_type} for the AI agent development system.\n\n"
            f"TITLE: {title}\n\n"
            f"CONTENT:\n{content[:2000]}\n\n"
            "Respond with JSON only: score (0.0-1.0), target_agents (list), "
            "key_takeaway (string), expires_days (int), ingest (bool)."
        ),
        expected_output="JSON evaluation object",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    try:
        result = crew.kickoff()
        raw = str(result).strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        evaluation = json.loads(raw)

        # Enforce threshold
        if evaluation.get("score", 0) < threshold:
            evaluation["ingest"] = False

        return evaluation

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"  ⚠️ LLM evaluation failed for '{title}': {e}")
        return _fallback_evaluation(title, content, source_type, threshold)


def _fallback_evaluation(
    title: str,
    content: str,
    source_type: str,
    threshold: float,
) -> dict:
    """
    Keyword-based fallback when LLM evaluation fails.
    Ensures the pipeline doesn't stall on LLM errors.
    """
    text = f"{title} {content}".lower()

    # High-value keywords
    high_keywords = [
        "breaking change", "critical", "vulnerability", "security",
        "react-native", "crewai", "expo", "hipaa", "phi",
        "deprecat", "removed", "migration required",
    ]
    medium_keywords = [
        "new feature", "performance", "update", "release",
        "python", "typescript", "mobile", "healthcare", "va ",
    ]

    high_hits = sum(1 for kw in high_keywords if kw in text)
    medium_hits = sum(1 for kw in medium_keywords if kw in text)

    if high_hits >= 2:
        score = 0.85
    elif high_hits >= 1:
        score = 0.7
    elif medium_hits >= 2:
        score = 0.55
    else:
        score = 0.3

    return {
        "score": score,
        "target_agents": ["all"],
        "key_takeaway": f"Auto-scored {source_type}: {title[:100]}",
        "expires_days": 180,
        "ingest": score >= threshold,
        "fallback": True,
    }


def evaluate_batch(
    items: list[dict],
    threshold: float = 0.6,
) -> list[dict]:
    """
    Evaluate a batch of items. Builds the agent once and reuses it.

    Each item dict must have: title, content, source_type.
    Returns list of items with evaluation results attached.
    """
    agent = build_evaluator_agent()

    results = []
    for item in items:
        evaluation = evaluate_item(
            agent=agent,
            title=item["title"],
            content=item["content"],
            source_type=item["source_type"],
            threshold=threshold,
        )
        item["evaluation"] = evaluation
        results.append(item)

        status = "✅ INGEST" if evaluation.get("ingest") else "⏭️ SKIP"
        score = evaluation.get("score", 0)
        logger.info(f"  {status} [{score:.2f}] {item['title'][:60]}")

    ingested = sum(1 for r in results if r["evaluation"].get("ingest"))
    logger.info(f"  📊 Batch: {ingested}/{len(results)} items above threshold ({threshold})")

    return results
