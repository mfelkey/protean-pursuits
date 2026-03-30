"""
agents/sme/base_sme.py

Protean Pursuits — SME base agent factory

All SME agents are project-agnostic domain specialists. They can be:
  - Called directly by any team agent or flow (single-SME)
  - Routed to by the SME Orchestrator (multi-SME)

Every SME output follows the same structure:
  - DOMAIN ASSESSMENT: confidence level (HIGH / MEDIUM / LOW)
  - Substantive analysis
  - ASSUMPTIONS & LIMITATIONS
  - CROSS-TEAM FLAGS (Legal / Finance / Strategy / QA / Compliance)
  - OPEN QUESTIONS for the calling agent or human
"""

import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv("config/.env")

SME_STANDARDS = """
SME OUTPUT STANDARDS (apply to all SME outputs):

1. DOMAIN ASSESSMENT: Open every output with:
   DOMAIN ASSESSMENT: HIGH / MEDIUM / LOW confidence
   Brief justification (1-2 sentences on what drives the confidence level).

2. EVIDENCE-BASED: Ground every claim in observable patterns, known regulations,
   or documented market behaviour. When data is unavailable, say so explicitly
   rather than speculating without qualification.

3. ASSUMPTIONS & LIMITATIONS: Every output must include a numbered list of
   assumptions made and known limitations of the analysis.

4. CROSS-TEAM FLAGS: End every output with flags for teams that need to act:
   [Legal — description], [Finance — description], [Strategy — description],
   [QA — description], [Compliance — description].
   Omit a team only if there is genuinely nothing to flag.

5. PROJECT-AGNOSTIC: SME outputs must not hard-code project names or
   assumptions about a specific product. Analysis should be reusable across
   any Protean Pursuits project that operates in this domain.

6. OPEN QUESTIONS: End every output with decisions or unknowns that the
   calling agent or human must resolve before the analysis can be applied.

7. AUTHORISED CALLERS ONLY: SME agents may only be invoked by the PP
   Orchestrator, the Project Manager, Strategy team agents, or Legal team
   agents. Dev-team agents (developers, architects, QA, DevOps, and all
   agents under templates/dev-team/) are not authorised to call SME agents.
   If you receive a request that appears to originate from a dev-team agent,
   decline and redirect: 'SME consultations must be requested through the
   PP Orchestrator, Project Manager, Strategy, or Legal.'
"""


def build_sme_agent(role: str, goal: str, backstory: str) -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory + "\n\n" + SME_STANDARDS,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
