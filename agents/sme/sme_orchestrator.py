"""
agents/sme/sme_orchestrator.py

Protean Pursuits — SME Orchestrator

Project-agnostic. Routes domain questions to the appropriate SME specialist(s),
synthesises their outputs, and fires a HITL review gate.

Invocation patterns:
  1. Single-SME (direct):
       from agents.sme.sports_betting_expert import build_sports_betting_expert, run_sme_consult
       result, context = run_sme_consult(context, "sports_betting", question)

  2. Multi-SME (via orchestrator):
       from agents.sme.sme_orchestrator import run_sme_crew
       context = run_sme_crew(context, ["sports_betting", "world_football"], question)

  3. Auto-route (orchestrator picks specialists from question):
       context = run_sme_crew(context, [], question)   # empty list = auto-detect

SME registry keys:
  sports_betting          world_football          nba_ncaa_basketball
  nfl_ncaa_football       mlb                     nhl_ncaa_hockey
  mma                     tennis                  world_rugby
  cricket                 wnba_ncaa_womens_basketball
  thoroughbred_horse_racing  harness_racing        mens_boxing
  pga                     lpga
"""

import os
import json
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv("config/.env")

# ── SME registry ───────────────────────────────────────────────────────────────

def _get_registry():
    """Lazy import to avoid circular dependencies."""
    from agents.sme.sports_betting_expert           import build_sports_betting_expert
    from agents.sme.world_football_expert           import build_world_football_expert
    from agents.sme.nba_ncaa_basketball_expert      import build_nba_ncaa_basketball_expert
    from agents.sme.nfl_ncaa_football_expert        import build_nfl_ncaa_football_expert
    from agents.sme.mlb_expert                      import build_mlb_expert
    from agents.sme.nhl_ncaa_hockey_expert          import build_nhl_ncaa_hockey_expert
    from agents.sme.mma_expert                      import build_mma_expert
    from agents.sme.tennis_expert                   import build_tennis_expert
    from agents.sme.world_rugby_expert              import build_world_rugby_expert
    from agents.sme.cricket_expert                  import build_cricket_expert
    from agents.sme.wnba_ncaa_womens_basketball_expert import build_wnba_ncaa_womens_basketball_expert
    from agents.sme.thoroughbred_horse_racing_expert import build_thoroughbred_horse_racing_expert
    from agents.sme.harness_racing_expert           import build_harness_racing_expert
    from agents.sme.mens_boxing_expert              import build_mens_boxing_expert
    from agents.sme.pga_expert                      import build_pga_expert
    from agents.sme.lpga_expert                     import build_lpga_expert
    return {
        "sports_betting":              build_sports_betting_expert,
        "world_football":              build_world_football_expert,
        "nba_ncaa_basketball":         build_nba_ncaa_basketball_expert,
        "nfl_ncaa_football":           build_nfl_ncaa_football_expert,
        "mlb":                         build_mlb_expert,
        "nhl_ncaa_hockey":             build_nhl_ncaa_hockey_expert,
        "mma":                         build_mma_expert,
        "tennis":                      build_tennis_expert,
        "world_rugby":                 build_world_rugby_expert,
        "cricket":                     build_cricket_expert,
        "wnba_ncaa_womens_basketball":  build_wnba_ncaa_womens_basketball_expert,
        "thoroughbred_horse_racing":   build_thoroughbred_horse_racing_expert,
        "harness_racing":              build_harness_racing_expert,
        "mens_boxing":                 build_mens_boxing_expert,
        "pga":                         build_pga_expert,
        "lpga":                        build_lpga_expert,
    }

# ── Authorised callers ─────────────────────────────────────────────────────────

# Only these caller identifiers may invoke SME agents.
# Dev-team agents are explicitly excluded.
AUTHORISED_CALLERS = {
    "pp_orchestrator",
    "project_manager",
    "strategy",
    "strategy_team",
    "legal",
    "legal_team",
}

# Dev-team caller identifiers — always rejected
DEV_TEAM_CALLERS = {
    "dev_team", "dev-team", "backend_developer", "frontend_developer",
    "senior_developer", "devops_engineer", "database_admin",
    "qa_lead", "test_automation_engineer", "test_verify",
    "technical_architect", "scalability_architect", "performance_auditor",
    "performance_planner", "penetration_tester", "accessibility_specialist",
    "scrum_master", "ux_designer", "ux_content_guide", "business_analyst",
    "security_reviewer", "mobile_ios", "mobile_android", "mobile_react_native",

AUTHORISED_CALLERS = {
    "pp_orchestrator",
    "project_manager",
    "strategy",
    "strategy_team",
    "legal",
    "legal_team",
    "ds_orchestrator",
    "sme_flow",

}    "mobile_devops", "mobile_qa",
}


def validate_caller(caller: str) -> None:
    """
    Raise PermissionError if the caller is a dev-team agent or not authorised.
    caller should be a snake_case identifier matching AUTHORISED_CALLERS.
    Pass caller=None to skip the check (e.g. direct human invocation from CLI).
    """
    if caller is None:
        return
    caller_lower = caller.lower().replace("-", "_")
    if caller_lower in DEV_TEAM_CALLERS:
        raise PermissionError(
            f"SME agents are not available to dev-team agents (caller: '{caller}'). "
            f"SME consultations must be requested through the PP Orchestrator, "
            f"Project Manager, Strategy, or Legal."
        )
    if caller_lower not in AUTHORISED_CALLERS:
 
       raise PermissionError(
            f"Unauthorised SME caller: '{caller}'. "
            f"Authorised callers: {sorted(AUTHORISED_CALLERS)}."
        )


# Keywords used for auto-routing when no sme_keys are specified
_ROUTING_KEYWORDS = {
    "sports_betting":              ["sportsbook", "operator economics", "wagering industry",
                                    "odds compilation", "trading floor", "betting regulation",
                                    "responsible gambling", "overround", "margin"],
    "world_football":              ["soccer", "football", "premier league", "champions league",
                                    "la liga", "serie a", "bundesliga", "ligue 1", "mls",
                                    "world cup", "fifa", "uefa", "epl"],
    "nba_ncaa_basketball":         ["nba", "ncaa basketball", "march madness", "college basketball",
                                    "nba finals", "point spread basketball"],
    "nfl_ncaa_football":           ["nfl", "ncaa football", "super bowl", "college football",
                                    "cfp", "spread football", "american football"],
    "mlb":                         ["mlb", "baseball", "world series", "run line",
                                    "moneyline baseball", "over under baseball"],
    "nhl_ncaa_hockey":             ["nhl", "ncaa hockey", "stanley cup", "hockey",
                                    "puck line", "ice hockey"],
    "mma":                         ["mma", "ufc", "bellator", "mixed martial arts",
                                    "fight odds", "method of victory"],
    "tennis":                      ["tennis", "wimbledon", "us open", "french open",
                                    "australian open", "atp", "wta", "grand slam"],
    "world_rugby":                 ["rugby", "six nations", "rugby world cup", "super rugby",
                                    "premiership rugby", "rugby union", "rugby league"],
    "cricket":                     ["cricket", "test cricket", "odi", "ipl", "the ashes",
                                    "t20", "cricket betting"],
    "wnba_ncaa_womens_basketball":  ["wnba", "ncaa women", "women's basketball",
                                    "women's college basketball"],
    "thoroughbred_horse_racing":   ["thoroughbred", "horse racing", "kentucky derby",
                                    "triple crown", "flat racing", "handicap racing"],
    "harness_racing":              ["harness racing", "standardbred", "trotting",
                                    "pacing", "sulky"],
    "mens_boxing":                 ["boxing", "prizefighting", "heavyweight", "wbc", "wba",
                                    "ibf", "wbo", "title fight", "boxing odds"],
    "pga":                         ["pga tour", "masters", "us open golf", "the open",
                                    "pga championship", "ryder cup", "fedex cup",
                                    "men's golf", "golf betting", "golf outright",
                                    "players championship", "liv golf"],
    "lpga":                        ["lpga", "women's golf", "solheim cup", "us women's open",
                                    "women's pga", "evian championship", "aig women's open",
                                    "ladies european tour", "lpga tour"],
}


# ── Notification helpers ───────────────────────────────────────────────────────

def _notify(subject: str, message: str) -> None:
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg["From"]    = os.getenv("OUTLOOK_ADDRESS")
        msg["To"]      = os.getenv("HUMAN_EMAIL")
        msg["Subject"] = f"[SME] {subject}"
        msg.attach(MIMEText(message, "plain"))
        with smtplib.SMTP("smtp.office365.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(msg)
    except Exception as e:
        print(f"⚠️  Notify failed: {e}")

    try:
        import smtplib
        from email.mime.text import MIMEText
        sms = os.getenv("HUMAN_PHONE_NUMBER", "").replace("+1", "") + "@txt.att.net"
        m = MIMEText(f"[SME] {subject}\n{message}"[:160])
        m["From"] = os.getenv("OUTLOOK_ADDRESS"); m["To"] = sms; m["Subject"] = ""
        with smtplib.SMTP("smtp.office365.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(os.getenv("OUTLOOK_ADDRESS"), os.getenv("OUTLOOK_PASSWORD"))
            s.send_message(m)
    except Exception as e:
        print(f"⚠️  SMS failed: {e}")


# ── HITL gate ──────────────────────────────────────────────────────────────────

def request_sme_review(artifact_path: str, summary: str,
                        timeout_hours: int = 48) -> bool:
    approval_dir  = "logs/approvals"
    os.makedirs(approval_dir, exist_ok=True)
    review_id     = f"SME-{uuid.uuid4().hex[:8].upper()}"
    response_file = f"{approval_dir}/{review_id}.response.json"

    with open(f"{approval_dir}/{review_id}.json", "w") as f:
        json.dump({
            "review_id":     review_id,
            "artifact_path": artifact_path,
            "summary":       summary,
            "requested_at":  datetime.utcnow().isoformat(),
            "status":        "PENDING"
        }, f, indent=2)

    _notify(
        subject=f"[SME REVIEW] {review_id}",
        message=(
            f"Summary: {summary}\nArtifact: {artifact_path}\n\n"
            f"Approve: write to {response_file}:\n"
            f'  {{"decision": "APPROVED"}}\n'
            f"Reject:  {{\"decision\": \"REJECTED\", \"reason\": \"...\"}}\n"
            f"Timeout: {timeout_hours}h"
        )
    )
    print(f"\n⏸️  [SME REVIEW] {review_id} — {summary}")

    elapsed = 0
    while elapsed < timeout_hours * 3600:
        if os.path.exists(response_file):
            with open(response_file) as f:
                resp = json.load(f)
            decision = resp.get("decision", "").upper()
            if decision == "APPROVED":
                print(f"✅ Approved — {review_id}")
                return True
            elif decision == "REJECTED":
                print(f"❌ Rejected — {review_id}: {resp.get('reason', '')}")
                return False
        time.sleep(30)
        elapsed += 30

    print(f"⏰ Timed out — {review_id}")
    return False


# ── Context helpers ────────────────────────────────────────────────────────────

def _save_sme_artifact(context: dict, sme_key: str, content: str) -> str:
    out_dir = context.get("sme_output_dir", "logs/sme")
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    pid  = context.get("project_id", "NOPROJ")
    path = f"{out_dir}/{pid}_SME_{sme_key.upper()}_{ts}.md"
    with open(path, "w") as f:
        f.write(content)
    context.setdefault("artifacts", []).append({
        "name":       f"SME — {sme_key}",
        "type":       f"SME_{sme_key.upper()}",
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": f"SME:{sme_key}"
    })
    print(f"\n💾 [SME:{sme_key}] Saved: {path}")
    return path


def _save_context(context: dict) -> None:
    pid = context.get("project_id")
    if not pid:
        return
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{pid}.json"
    if os.path.exists(path):
        with open(path, "w") as f:
            json.dump(context, f, indent=2)


# ── Auto-routing ───────────────────────────────────────────────────────────────

def _auto_detect_smes(question: str) -> list:
    """Return SME keys whose keywords appear in the question."""
    q = question.lower()
    matched = [key for key, kws in _ROUTING_KEYWORDS.items()
               if any(kw.lower() in q for kw in kws)]
    # Always include sports_betting for general industry questions if nothing else matched
    if not matched:
        matched = ["sports_betting"]
    return matched


# ── SME Orchestrator agent ─────────────────────────────────────────────────────

def build_sme_orchestrator() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )
    return Agent(
        role="SME Orchestrator",
        goal=(
            "Route domain questions to the appropriate SME specialist(s), "
            "synthesise their outputs into a unified Domain Intelligence Brief, "
            "and surface cross-team flags and open questions for the calling agent "
            "or human reviewer."
        ),
        backstory=(
            "You are the SME Orchestrator at Protean Pursuits LLC — a domain "
            "intelligence coordinator who bridges specialist knowledge and project "
            "needs. You do not produce domain analysis yourself; your job is to "
            "select the right specialist(s) for a given question, brief them "
            "precisely, cross-check their outputs for consistency, and synthesise "
            "a unified Domain Intelligence Brief that a project team can act on. "
            "You are project-agnostic: you serve any current or future Protean "
            "Pursuits project that needs domain expertise. You keep your synthesis "
            "clean and free of contradictions — if two specialists disagree, you "
            "surface the disagreement explicitly rather than papering over it. "
            "You always end your synthesis with consolidated cross-team flags "
            "and a single prioritised list of open questions."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True
    )


# ── Single-SME direct call ─────────────────────────────────────────────────────

def run_sme_consult(context: dict, sme_key: str, question: str,
                    caller: str = None) -> tuple:
    """
    Call a single SME directly. Returns (result_text, updated_context).
    Use this when the calling agent knows exactly which SME it needs.

    caller — snake_case identifier of the invoking agent/team, e.g.
             'pp_orchestrator', 'project_manager', 'strategy', 'legal'.
             Dev-team callers are rejected with PermissionError.
    """
    validate_caller(caller)
    from agents.sme.base_sme import SME_STANDARDS

    registry = _get_registry()
    if sme_key not in registry:
        raise ValueError(f"Unknown SME key '{sme_key}'. "
                         f"Available: {list(registry.keys())}")

    agent = registry[sme_key]()
    task  = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.
Project: {context.get('project_name', 'N/A')} ({context.get('project_id', 'N/A')})

Question / brief from calling agent:
{question}

{SME_STANDARDS}
""",
        expected_output=(
            "Complete SME analysis opening with DOMAIN ASSESSMENT and ending "
            "with CROSS-TEAM FLAGS and OPEN QUESTIONS sections."
        ),
        agent=agent
    )
    crew   = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n🎓 [SME:{sme_key}] Running...\n")
    result = str(crew.kickoff())
    path   = _save_sme_artifact(context, sme_key, result)
    _save_context(context)
    return result, context


# ── Multi-SME orchestrated call ────────────────────────────────────────────────

def run_sme_crew(context: dict, sme_keys: list, question: str,
                 caller: str = None, timeout_hours: int = 48) -> dict:
    """
    Route to one or more SMEs, synthesise, fire HITL review.

    sme_keys — list of SME registry keys to call.
                Pass [] to auto-detect from question keywords.
    caller   — snake_case identifier of the invoking agent/team.
                Dev-team callers are rejected with PermissionError.
    """
    validate_caller(caller)
    from agents.sme.base_sme import SME_STANDARDS

    registry = _get_registry()

    # Auto-detect if no keys provided
    if not sme_keys:
        sme_keys = _auto_detect_smes(question)
        print(f"\n🔍 SME auto-detected: {sme_keys}")

    # Validate
    unknown = [k for k in sme_keys if k not in registry]
    if unknown:
        raise ValueError(f"Unknown SME key(s): {unknown}. "
                         f"Available: {list(registry.keys())}")

    print(f"\n🎓 SME Orchestrator — routing to: {sme_keys}\n")

    # Run each specialist
    results = {}
    for key in sme_keys:
        agent = registry[key]()
        task  = Task(
            description=f"""
You are the Protean Pursuits {agent.role}.
Project: {context.get('project_name', 'N/A')} ({context.get('project_id', 'N/A')})

Question / brief:
{question}

{SME_STANDARDS}
""",
            expected_output=(
                "Complete SME analysis opening with DOMAIN ASSESSMENT and ending "
                "with CROSS-TEAM FLAGS and OPEN QUESTIONS."
            ),
            agent=agent
        )
        crew   = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        print(f"\n🎓 [SME:{key}] Running...\n")
        result = str(crew.kickoff())
        _save_sme_artifact(context, key, result)
        results[key] = result

    # Synthesise
    orch  = build_sme_orchestrator()
    excerpts = {k: v[:600] + "..." for k, v in results.items()}
    synth = Task(
        description=f"""
You are the SME Orchestrator. Synthesise the following specialist outputs
into a unified Domain Intelligence Brief for:

Project: {context.get('project_name', 'N/A')} ({context.get('project_id', 'N/A')})
Original question: {question}

SPECIALIST OUTPUTS:
{json.dumps(excerpts, indent=2)}

Your Domain Intelligence Brief must include:

1. SYNTHESIS SUMMARY
   2-3 paragraph unified answer to the original question, drawing on all
   specialist inputs. Surface any disagreements explicitly.

2. DOMAIN ASSESSMENT (OVERALL)
   HIGH / MEDIUM / LOW — synthesising the confidence levels from all specialists.
   Justify in 1-2 sentences.

3. KEY FINDINGS BY SPECIALIST
   | SME | Headline finding | Confidence | Critical flag |
   One row per specialist that ran.

4. CONSOLIDATED CROSS-TEAM FLAGS
   All flags from all specialists, deduplicated and prioritised.
   Format: [Team — description — source SME]

5. OPEN QUESTIONS (PRIORITISED)
   All open questions from all specialists, deduplicated and ranked by urgency.

6. RECOMMENDED NEXT STEPS
   What the calling team or human should do with this intelligence.
""",
        expected_output="Complete Domain Intelligence Brief in markdown.",
        agent=orch
    )
    crew   = Crew(agents=[orch], tasks=[synth], process=Process.sequential, verbose=True)
    brief  = str(crew.kickoff())
    path   = _save_sme_artifact(context, "BRIEF", brief)

    context.setdefault("sme_crew", {
        "sme_keys":    sme_keys,
        "question":    question,
        "brief_path":  path,
        "status":      "COMPLETE"
    })
    _save_context(context)

    # HITL
    approved = request_sme_review(
        path,
        f"SME Domain Brief — {', '.join(sme_keys)} — "
        f"{context.get('project_name', 'N/A')}"
    )
    context["sme_crew"]["approved"] = approved
    _save_context(context)
    return context


# ── Standalone entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, glob

    parser = argparse.ArgumentParser(description="Protean Pursuits — SME Orchestrator")
    parser.add_argument("--sme",      type=str, default="",
                        help="Comma-separated SME keys, or empty to auto-detect")
    parser.add_argument("--question", type=str, required=True)
    parser.add_argument("--project-id", type=str, default=None)
    parser.add_argument("--name",     type=str, default="Ad-hoc SME Consult")
    args = parser.parse_args()

    # Load context if project-id provided, else create minimal context
    context = {"project_name": args.name, "project_id": args.project_id,
               "artifacts": [], "sme_output_dir": "logs/sme"}
    if args.project_id:
        logs = sorted(glob.glob(f"logs/{args.project_id}*.json"),
                      key=os.path.getmtime, reverse=True)
        if logs:
            with open(logs[0]) as f:
                context = json.load(f)
            print(f"📂 Loaded context: {logs[0]}")

    sme_keys = [k.strip() for k in args.sme.split(",") if k.strip()]

    context = run_sme_crew(context, sme_keys, args.question)
    brief   = context.get("sme_crew", {})
    print(f"\n✅ SME crew complete. Brief: {brief.get('brief_path', 'N/A')}")
    print(f"   Approved: {brief.get('approved', 'N/A')}")
