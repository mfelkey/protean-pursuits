"""agents/orchestrator/base_agent.py — Design Team base agent factory"""
import os
from dotenv import load_dotenv
from crewai import Agent, LLM
load_dotenv("config/.env")

DESIGN_STANDARDS = """
OUTPUT STANDARDS (apply to all design outputs):
- Tool-agnostic: use precise values (hex, px/rem, named tokens) — no tool-specific references
- Accessibility: flag any WCAG 2.1 AA concerns in every output
- Annotated: include states (default, hover, focus, disabled, error) and responsive behaviour
- Handoff-ready: complete enough for a developer to implement without follow-up
- Open questions: end every output with decisions requiring human input
"""

def build_design_agent(role: str, goal: str, backstory: str) -> Agent:
    llm = LLM(model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
               base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
               timeout=1800)
    return Agent(role=role, goal=goal,
                 backstory=backstory + "\n\n" + DESIGN_STANDARDS,
                 llm=llm, verbose=True, allow_delegation=False)
