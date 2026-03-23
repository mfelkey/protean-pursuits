#!/usr/bin/env python3
"""
RAG Injection Test

Verifies that the RAG injection module correctly queries ChromaDB
and returns formatted context for different agent roles.

Usage:
    cd ~/dev-team
    source .venv/bin/activate
    python agents/shared/knowledge_curator/test_rag.py
"""

import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
from dotenv import load_dotenv

load_dotenv("config/.env")

from agents.shared.knowledge_curator.rag_inject import (
    get_knowledge_context,
    inject_for_agent,
)


def test_agent(role: str, task: str):
    """Test RAG injection for a single agent role."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {role}")
    print(f"   Task: {task[:80]}")
    print(f"{'='*60}")

    result = get_knowledge_context(
        agent_role=role,
        task_summary=task,
        n_results=3,
    )

    if result:
        # Show first 500 chars of results
        preview = result[:500]
        if len(result) > 500:
            preview += f"\n... ({len(result)} chars total)"
        print(preview)
    else:
        print("  (no results — collection may be empty for this role)")


def main():
    print("🧠 RAG Injection Test Suite")
    print("=" * 60)

    # Test dev agents against dev_practices + system_updates
    test_agent(
        "Backend Developer",
        "Build REST API endpoints for project data with authentication"
    )

    test_agent(
        "Security Reviewer",
        "Review architecture for PHI data handling and HIPAA compliance"
    )

    test_agent(
        "DevOps Engineer",
        "Set up Docker Compose deployment with CI/CD pipeline"
    )

    # Test mobile agents
    test_agent(
        "RN Developer",
        "Implement React Native screens for trip tracking with Expo"
    )

    test_agent(
        "Mobile DevOps",
        "Configure EAS Build and Fastlane for app store deployment"
    )

    # Test domain-specific agents against VA/healthcare collections
    test_agent(
        "Product Manager",
        "Define requirements for the project scheduling system"
    )

    test_agent(
        "Business Analyst",
        "Map stakeholders and process flows for the project domain"
    )

    # Test the convenience wrapper
    print(f"\n{'='*60}")
    print("🧪 Testing inject_for_agent() convenience wrapper")
    print(f"{'='*60}")

    result = inject_for_agent(
        "Security Reviewer",
        "Build a mobile app for project data analysis",
    )
    if result:
        print(f"  ✅ inject_for_agent returned {len(result)} chars")
    else:
        print("  (no results)")

    print(f"\n{'='*60}")
    print("✅ RAG Injection tests complete")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
