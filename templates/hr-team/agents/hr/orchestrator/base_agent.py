"""agents/orchestrator/base_agent.py — HR Team base agent factory"""
import os
from dotenv import load_dotenv
from crewai import Agent, LLM
load_dotenv("config/.env")

HR_STANDARDS = """
OUTPUT STANDARDS (apply to all HR outputs):
- Humans only: never recommend replacing a human role with AI, automation, or a bot
- Cross-team flags: end every output with [Legal / Finance / Strategy / QA] flags
- Confidential: never include individual names in file titles or document headings
- Approval required: mark every compensation figure and disciplinary action with ⚠️ REQUIRES HUMAN APPROVAL
- Legal disclaimer: internal guidance only — not legal advice
- Open questions: end every output with decisions requiring human input
"""


def build_hr_agent(role: str, goal: str, backstory: str) -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role=role, goal=goal,
        backstory=backstory + "\n\n" + HR_STANDARDS,
        llm=llm, verbose=True, allow_delegation=False
    )
