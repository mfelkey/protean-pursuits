"""
agents/orchestrator/base_agent.py

Generic strategy agent factory. All 11 agents use this.
"""
import os
from dotenv import load_dotenv
from crewai import Agent, LLM
load_dotenv("config/.env")

CONFIDENCE_INSTRUCTION = """
CONFIDENCE LEVEL REQUIREMENT — MANDATORY ON ALL RECOMMENDATIONS:
Tag every recommendation, finding, or strategic assertion with:
  [CONFIDENCE: HIGH | Supporting evidence: ...]
  [CONFIDENCE: MEDIUM | Key assumption: ...]
  [CONFIDENCE: LOW | Primary uncertainty: ...]
Never omit confidence tags. Every untagged recommendation is incomplete.
"""

def build_strategy_agent(role: str, goal: str, backstory: str) -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role=role, goal=goal,
        backstory=backstory + "\n\n" + CONFIDENCE_INSTRUCTION,
        llm=llm, verbose=True, allow_delegation=False
    )
