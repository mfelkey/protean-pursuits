"""
teams/sme-team/agents/orchestrator/orchestrator.py

Protean Pursuits — SME Group Orchestrator

Project-agnostic domain specialists callable from any PP project.

Authorised callers only:
  pp_orchestrator, project_manager, strategy, legal, sme_flow

Dev-team agents are explicitly blocked — raises PermissionError if attempted.

Invocation patterns:
  1. Single SME direct:    run_sme_consult(context, "pga", question, caller="project_manager")
  2. Multi-SME orchestrated: run_sme_crew(context, ["pga", "lpga"], question, caller="strategy")
  3. Auto-detect from keywords: run_sme_crew(context, [], question, caller="pp_orchestrator")

All multi-SME calls fire a HITL review gate on the synthesised Domain Intelligence Brief.

Every SME output opens with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW
and ends with CROSS-TEAM FLAGS and OPEN QUESTIONS.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

load_dotenv("config/.env")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
import sys
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ── Access control ────────────────────────────────────────────────────────────

AUTHORISED_CALLERS = {
    "pp_orchestrator",
    "project_manager",
    "strategy",
    "legal",
    "sme_flow",
}

BLOCKED_CALLERS_PREFIX = {
    "dev_",
    "backend_",
    "frontend_",
    "mobile_",
    "devops_",
}


def validate_caller(caller: str) -> None:
    """Raise PermissionError if caller is not authorised."""
    if caller not in AUTHORISED_CALLERS:
        # Check blocked prefixes
        for prefix in BLOCKED_CALLERS_PREFIX:
            if caller.startswith(prefix):
                raise PermissionError(
                    f"[SME Group] Caller '{caller}' is a dev-team agent and is "
                    f"explicitly blocked from accessing the SME Group. "
                    f"Authorised callers: {sorted(AUTHORISED_CALLERS)}"
                )
        raise PermissionError(
            f"[SME Group] Caller '{caller}' is not authorised to invoke the SME Group. "
            f"Authorised callers: {sorted(AUTHORISED_CALLERS)}"
        )


# ── SME registry ──────────────────────────────────────────────────────────────

SME_REGISTRY = {
    "sports_betting":               "Cross-sport industry authority — all regulated markets worldwide",
    "world_football":               "All global leagues, confederations, Asian handicap",
    "nba_ncaa_basketball":          "NBA + March Madness",
    "nfl_ncaa_football":            "NFL + CFP, college football",
    "mlb":                          "MLB + NPB + KBO + CPBL",
    "nhl_ncaa_hockey":              "NHL + NCAA + KHL + Euro leagues",
    "mma":                          "UFC + Bellator + ONE + Rizin",
    "tennis":                       "ATP + WTA + Challengers + ITF",
    "world_rugby":                  "Union + League — Six Nations, NRL, State of Origin",
    "cricket":                      "Test + ODI + T20 + IPL — all formats, all nations",
    "wnba_ncaa_womens_basketball":  "WNBA + NCAA women's",
    "thoroughbred_horse_racing":    "US + UK/IRE + AUS + HK + JPN + FR + DXB",
    "harness_racing":               "Standardbred worldwide — Hambletonian, V75, PMU",
    "mens_boxing":                  "All four sanctioning bodies, all 17 weight classes",
    "pga":                          "PGA Tour + DP World Tour + LIV + all majors + Ryder Cup",
    "lpga":                         "LPGA + JLPGA + KLPGA + women's majors + Solheim Cup",
}

# Keywords used for auto-detection
SME_KEYWORDS = {
    "sports_betting":               ["betting", "sportsbook", "wagering", "odds", "lines", "spread", "juice", "vig"],
    "world_football":               ["soccer", "football", "premier league", "la liga", "bundesliga", "serie a", "champions league", "asian handicap"],
    "nba_ncaa_basketball":          ["nba", "basketball", "march madness", "ncaa basketball", "college basketball"],
    "nfl_ncaa_football":            ["nfl", "american football", "cfp", "college football", "super bowl"],
    "mlb":                          ["mlb", "baseball", "npb", "kbo", "cpbl"],
    "nhl_ncaa_hockey":              ["nhl", "hockey", "khl", "ice hockey"],
    "mma":                          ["mma", "ufc", "bellator", "one fc", "rizin", "mixed martial arts"],
    "tennis":                       ["tennis", "atp", "wta", "wimbledon", "us open", "french open", "australian open"],
    "world_rugby":                  ["rugby", "six nations", "nrl", "state of origin", "super rugby", "rugby league"],
    "cricket":                      ["cricket", "ipl", "test match", "odi", "t20", "bbl"],
    "wnba_ncaa_womens_basketball":  ["wnba", "women's basketball", "ncaa women"],
    "thoroughbred_horse_racing":    ["horse racing", "thoroughbred", "kentucky derby", "cheltenham", "royal ascot", "hong kong racing"],
    "harness_racing":               ["harness racing", "standardbred", "hambletonian", "v75", "pmu trot"],
    "mens_boxing":                  ["boxing", "wbc", "wba", "ibf", "wbo", "heavyweight", "prizefight"],
    "pga":                          ["pga", "golf", "masters", "us open golf", "open championship", "ryder cup", "liv golf", "dp world tour"],
    "lpga":                         ["lpga", "women's golf", "solheim cup", "ais", "jlpga", "klpga"],
}


def auto_detect_smes(question: str) -> list:
    """Return SME keys whose keywords appear in the question."""
    q = question.lower()
    matched = []
    for key, kws in SME_KEYWORDS.items():
        if any(kw in q for kw in kws):
            matched.append(key)
    return matched or ["sports_betting"]  # fallback to general sports betting expert


# ── Notification helpers ──────────────────────────────────────────────────────

def send_pushover(subject: str, message: str, priority: int = 1) -> bool:
    import urllib.request, urllib.parse, json
    user_key  = os.getenv("PUSHOVER_USER_KEY", "")
    api_token = os.getenv("PUSHOVER_API_TOKEN", "")
    if not user_key or not api_token:
        print("⚠️  Pushover credentials not set")
        return False
    try:
        data = urllib.parse.urlencode({
            "token": api_token, "user": user_key,
            "title": subject[:250], "message": message[:1024],
            "priority": priority,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.pushover.net/1/messages.json",
            data=data, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("status") == 1
    except Exception as e:
        print(f"⚠️  Pushover failed: {e}")
        return False


def notify_human(subject: str, message: str) -> None:
    send_pushover(f"[SME] {subject}", message, priority=1)
    send_pushover(f"[SME] {subject}", message, priority=0)


# ── HITL gate for multi-SME crew outputs ─────────────────────────────────────

def request_hitl_review(artifact_path: str, summary: str,
                         timeout_hours: int = 48) -> bool:
    """HITL gate fires on every synthesised Domain Intelligence Brief."""
    import time as _t

    approval_dir = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    review_id = f"SME-{uuid.uuid4().hex[:8].upper()}"
    response_file = f"{approval_dir}/{review_id}.response.json"

    with open(f"{approval_dir}/{review_id}.json", "w") as f:
        json.dump({
            "review_id": review_id,
            "gate": "SME_DOMAIN_INTELLIGENCE_BRIEF",
            "artifact_path": artifact_path,
            "summary": summary,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "PENDING"
        }, f, indent=2)

    notify_human(
        subject=f"[SME REVIEW] Domain Intelligence Brief — {review_id}",
        message=(
            f"Summary: {summary}\n"
            f"Brief: {artifact_path}\n\n"
            f"Approve: {{'decision': 'APPROVED'}}\n"
            f"Reject: {{'decision': 'REJECTED', 'reason': '...'}}\n"
            f"Write to: {response_file}\nTimeout: {timeout_hours}h"
        )
    )
    print(f"\n⏸️  [SME HITL] Domain Intelligence Brief review — {review_id}")

    elapsed = 0
    while elapsed < timeout_hours * 3600:
        if os.path.exists(response_file):
            with open(response_file) as f:
                resp = json.load(f)
            decision = resp.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ SME brief approved — {review_id}")
                return True
            elif decision == "REJECTED":
                print(f"❌ SME brief rejected — {review_id}: {resp.get('reason', '')}")
                return False
        _t.sleep(30)
        elapsed += 30

    print(f"⏰ SME review timed out — {review_id}.")
    return False


# ── SME agent factory ─────────────────────────────────────────────────────────

def build_sme_agent(sme_key: str) -> Agent:
    """Build a single SME agent for the given registry key."""
    if sme_key not in SME_REGISTRY:
        raise ValueError(
            f"Unknown SME key '{sme_key}'. "
            f"Valid keys: {sorted(SME_REGISTRY.keys())}"
        )

    domain = SME_REGISTRY[sme_key]
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800,
    )

    return Agent(
        role=f"SME — {domain}",
        goal=(
            f"Provide authoritative, actionable domain intelligence on {domain} "
            f"for Protean Pursuits projects. Every output opens with "
            f"DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW confidence rating and ends with "
            f"CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        backstory=(
            f"You are a world-class domain expert specialising in {domain}. "
            f"You have deep, current knowledge of markets, regulations, competitive "
            f"dynamics, data sources, and operational realities in your domain. "
            f"You are project-agnostic — you bring domain expertise to whatever "
            f"project Protean Pursuits is building. You give direct, specific, "
            f"actionable intelligence — never vague generalities. "
            f"You always open your output with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW "
            f"(your confidence in the completeness and accuracy of your analysis). "
            f"You always end with CROSS-TEAM FLAGS (items requiring Legal, Finance, "
            f"Strategy, QA input) and OPEN QUESTIONS (gaps you cannot fill without "
            f"additional information from the human)."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def build_sme_synthesis_agent() -> Agent:
    """Build the SME Orchestrator agent that synthesises multi-SME outputs."""
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800,
    )

    return Agent(
        role="SME Orchestrator",
        goal=(
            "Synthesise outputs from multiple domain SMEs into a coherent Domain "
            "Intelligence Brief (DIB) that gives the project team a unified, "
            "cross-domain view of the market, regulatory, and operational landscape."
        ),
        backstory=(
            "You are the SME Group Lead at Protean Pursuits LLC — a senior analyst "
            "with experience synthesising intelligence across multiple domains into "
            "coherent strategic briefs. You receive individual SME analyses and "
            "combine them into a single Domain Intelligence Brief that identifies "
            "cross-domain patterns, conflicts, and opportunities. You never invent "
            "domain knowledge — you synthesise only what the SMEs have provided. "
            "Your DIB opens with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW and ends with "
            "CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def run_sme_consult(context: dict, sme_key: str, question: str,
                    caller: str) -> str:
    """
    Single SME direct consult.

    Args:
        context:  Project context dict (or raw string in context['raw'])
        sme_key:  Registry key for the SME to consult
        question: The domain question or task
        caller:   Caller identifier — must be in AUTHORISED_CALLERS

    Returns:
        SME output as string

    Raises:
        PermissionError: if caller is not authorised
        ValueError: if sme_key is not in SME_REGISTRY
    """
    validate_caller(caller)

    context_block = (
        context.get("raw", "")
        or (json.dumps(context, indent=2) if context else "No context provided.")
    )

    agent = build_sme_agent(sme_key)

    task = Task(
        description=(
            f"Question: {question}\n\n"
            f"Project context:\n{context_block}\n\n"
            f"Provide authoritative domain intelligence on {SME_REGISTRY[sme_key]}. "
            f"Open with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW. "
            f"End with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        expected_output=(
            f"Complete SME analysis from {SME_REGISTRY[sme_key]} expert. "
            f"Opens with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW. "
            f"No placeholders. Ends with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    return str(result)


def run_sme_crew(context: dict, sme_keys: list, question: str,
                 caller: str) -> str:
    """
    Multi-SME orchestrated crew. SME Orchestrator synthesises all outputs
    into a Domain Intelligence Brief and fires HITL review gate.

    Args:
        context:  Project context dict
        sme_keys: List of registry keys. Empty list = auto-detect from question.
        question: The domain question or task
        caller:   Caller identifier — must be in AUTHORISED_CALLERS

    Returns:
        Synthesised Domain Intelligence Brief as string

    Raises:
        PermissionError: if caller is not authorised
    """
    validate_caller(caller)

    if not sme_keys:
        sme_keys = auto_detect_smes(question)

    context_block = (
        context.get("raw", "")
        or (json.dumps(context, indent=2) if context else "No context provided.")
    )

    # Build individual SME agents and tasks
    agents = []
    tasks = []
    for key in sme_keys:
        if key not in SME_REGISTRY:
            print(f"⚠️  Unknown SME key '{key}' — skipping.")
            continue
        agent = build_sme_agent(key)
        agents.append(agent)
        tasks.append(Task(
            description=(
                f"Question: {question}\n\n"
                f"Project context:\n{context_block}\n\n"
                f"Provide authoritative domain intelligence on {SME_REGISTRY[key]}. "
                f"Open with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW. "
                f"End with CROSS-TEAM FLAGS and OPEN QUESTIONS."
            ),
            expected_output=(
                f"Complete SME analysis from {SME_REGISTRY[key]} expert. "
                f"Opens with DOMAIN ASSESSMENT. Ends with CROSS-TEAM FLAGS and OPEN QUESTIONS."
            ),
            agent=agent,
        ))

    if not agents:
        return "[SME crew] No valid SME keys — no output produced."

    # Add synthesis agent
    synth = build_sme_synthesis_agent()
    agents.append(synth)
    tasks.append(Task(
        description=(
            f"Synthesise the outputs from the {len(sme_keys)} domain SME(s) above "
            f"into a single Domain Intelligence Brief (DIB) for this question:\n\n"
            f"Question: {question}\n\n"
            f"The DIB must:\n"
            f"1. Open with DOMAIN ASSESSMENT: HIGH/MEDIUM/LOW\n"
            f"2. Identify cross-domain patterns, conflicts, and opportunities\n"
            f"3. Never add domain knowledge not present in the SME outputs\n"
            f"4. End with CROSS-TEAM FLAGS and OPEN QUESTIONS"
        ),
        expected_output=(
            "Domain Intelligence Brief synthesising all SME inputs. "
            "Opens with DOMAIN ASSESSMENT. Ends with CROSS-TEAM FLAGS and OPEN QUESTIONS."
        ),
        agent=synth,
    ))

    crew = Crew(agents=agents, tasks=tasks, verbose=True)
    result = crew.kickoff()
    output_str = str(result)

    # Fire HITL on synthesised DIB
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    artifact_path = f"output/sme/dib_{ts}.md"
    os.makedirs("output/sme", exist_ok=True)
    with open(artifact_path, "w") as f:
        f.write(output_str)

    request_hitl_review(
        artifact_path=artifact_path,
        summary=f"Domain Intelligence Brief — {', '.join(sme_keys)} — {question[:80]}",
    )

    return output_str


def run_sme_orchestrator(brief: str, context: dict) -> str:
    """
    Entry point for flows/sme_intake_flow.py.
    Auto-detects relevant SMEs from the brief and runs the crew.

    Called via:
        run_sme_orchestrator = _import_orchestrator()
        result = run_sme_orchestrator(brief=brief_text, context=project_context)
    """
    return run_sme_crew(
        context=context,
        sme_keys=[],          # auto-detect
        question=brief,
        caller="pp_orchestrator",
    )
