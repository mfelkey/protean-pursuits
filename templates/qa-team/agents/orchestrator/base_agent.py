"""agents/orchestrator/base_agent.py — QA Team base agent factory"""
import os
from dotenv import load_dotenv
from crewai import Agent, LLM
load_dotenv("config/.env")

QA_STANDARDS = """
QA STANDARDS (apply to all outputs):
- Verdict block required: PASS / CONDITIONAL / FAIL / CRITICAL
- Every issue: ID, severity, category, description, expected vs actual, remediation, blocking Y/N
- No vague findings: be precise, reproducible, and actionable
- FAIL/CRITICAL: specify retest requirements and evidence needed for sign-off
"""

def build_qa_agent(role: str, goal: str, backstory: str) -> Agent:
    llm = LLM(model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
               base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
               timeout=1800)
    return Agent(role=role, goal=goal,
                 backstory=backstory + "\n\n" + QA_STANDARDS,
                 llm=llm, verbose=True, allow_delegation=False)
