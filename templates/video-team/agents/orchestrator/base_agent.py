"""agents/orchestrator/base_agent.py — Video Team base agent factory"""
import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")

VIDEO_STANDARDS = """
OUTPUT STANDARDS (apply to all video team outputs):
- Brand-agnostic: use PROJECT_NAME_PLACEHOLDER for all brand references. Actual
  brand voice, colors, and tone come from the project brief — never assume.
- Platform-specific: tailor every output to the target platform's specs,
  algorithm behavior, and audience expectations.
- Compliance first: no guaranteed outcomes, no misleading claims, no copyright
  violations. Flag any risk in an OPEN ISSUES section.
- Handoff-ready: every brief must be complete enough for an API or human
  executor to proceed without follow-up questions.
- Open questions: end every output with a numbered list of decisions or
  assets still required from the human before execution.
"""


def build_video_agent(role: str, goal: str, backstory: str,
                      tier: str = "TIER1") -> Agent:
    """
    tier: "TIER1" for reasoning/planning agents (default)
          "TIER2" for production/code agents
    """
    model_key = "TIER1_MODEL" if tier == "TIER1" else "TIER2_MODEL"
    llm = LLM(
        model=os.getenv(model_key, "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800,
    )
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory + "\n\n" + VIDEO_STANDARDS,
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
