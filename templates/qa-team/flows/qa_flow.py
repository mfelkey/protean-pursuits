"""
flows/qa_flow.py

Protean Pursuits — QA Team Flows

Run modes:
  TEST_CASES  — develop test cases for a feature or component
  AUDIT       — audit a specific domain (code, data, marketing, legal)
  FULL_QA     — all applicable agents, complete QA package
  SIGN_OFF    — final pre-launch gate (all agents run, sign-off issued)

Target teams: dev, ds, marketing, legal, design (any team's output)

Usage:
  python flows/qa_flow.py --mode test_cases
      --target dev --name "PROJECT_NAME_PLACEHOLDER Bet Tracker" --project-id PROJ-TEMPLATE

  python flows/qa_flow.py --mode audit --agents data_quality,security
      --target ds --name "PROJECT_NAME_PLACEHOLDER xG Model Pipeline"

  python flows/qa_flow.py --mode sign_off
      --target dev --name "PROJECT_NAME_PLACEHOLDER Phase 1A Launch" --project-id PROJ-TEMPLATE
"""

import sys
sys.path.insert(0, "/home/mfelkey/qa-team")

import os
import json
import argparse
from datetime import datetime
from crewai import Task, Crew, Process
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import (
    build_qa_orchestrator, create_qa_context,
    save_context, log_event, save_artifact,
    notify_human, request_human_review, escalate_qa_failure,
    QA_PASS, QA_CONDITIONAL, QA_FAIL, QA_CRITICAL, QA_INSTRUCTION
)
from agents.functional_testing.functional_agent import build_functional_agent
from agents.performance_testing.performance_agent import build_performance_agent
from agents.security_testing.security_agent import build_security_agent
from agents.accessibility_audit.accessibility_audit_agent import build_accessibility_audit_agent
from agents.data_quality.data_quality_agent import build_data_quality_agent
from agents.marketing_compliance.marketing_qa_agent import build_marketing_qa_agent
from agents.legal_completeness.legal_qa_agent import build_legal_qa_agent
from agents.test_case_development.test_case_agent import build_test_case_agent

load_dotenv("config/.env")

AGENT_REGISTRY = {
    "functional":          build_functional_agent,
    "performance":         build_performance_agent,
    "security":            build_security_agent,
    "accessibility_audit": build_accessibility_audit_agent,
    "data_quality":        build_data_quality_agent,
    "marketing_compliance":build_marketing_qa_agent,
    "legal_completeness":  build_legal_qa_agent,
    "test_cases":          build_test_case_agent,
}

# Default agent sets per target team
TEAM_AGENT_SETS = {
    "dev":       ["test_cases", "functional", "performance", "security", "accessibility_audit"],
    "ds":        ["data_quality", "functional", "performance"],
    "marketing": ["marketing_compliance", "accessibility_audit"],
    "legal":     ["legal_completeness"],
    "design":    ["accessibility_audit"],
    "all":       list(AGENT_REGISTRY.keys()),
}


def _detect_verdict(output: str) -> str:
    for v in [QA_CRITICAL, QA_FAIL, QA_CONDITIONAL, QA_PASS]:
        if f"QA VERDICT: {v}" in output.upper():
            return v
    return QA_CONDITIONAL


def _worst_verdict(verdicts: list) -> str:
    order = [QA_PASS, QA_CONDITIONAL, QA_FAIL, QA_CRITICAL]
    return max(verdicts, key=lambda v: order.index(v) if v in order else 0)


def _run_agent(agent_key: str, context: dict, brief: str,
               prior: str = "") -> tuple:
    agent = AGENT_REGISTRY[agent_key]()
    task = Task(
        description=f"""
You are the Protean Pursuits {agent.role}.
QA Target: {context['qa_name']} | Team: {context.get('target_team', 'N/A')}
QA ID: {context['qa_id']}

Brief: {brief}
{f"Prior QA outputs:{chr(10)}{prior}" if prior else ""}

{QA_INSTRUCTION}
""",
        expected_output=f"Complete {agent_key} QA report with verdict block and issue log.",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    print(f"\n🔍 [{agent_key.upper()}] Running QA...\n")
    result = str(crew.kickoff())
    verdict = _detect_verdict(result)
    output_dir = "output/test_cases" if agent_key == "test_cases" else "output/reports"
    path = save_artifact(context, f"{agent_key.upper()} QA Report",
                         agent_key.upper(), result, output_dir, verdict)
    escalate_qa_failure(context, verdict, path, f"{agent_key} QA — {context['qa_name']}")
    return result, path, verdict


def run_test_cases(context: dict, brief: str = "") -> dict:
    context["run_mode"] = "TEST_CASES"
    result, path, verdict = _run_agent("test_cases", context, brief or "Develop comprehensive test cases.")
    approved = request_human_review(path, f"Test Cases — {context['qa_name']}", verdict)
    context["status"] = "TEST_CASES_APPROVED" if approved else "TEST_CASES_REJECTED"
    log_event(context, context["status"], path)
    save_context(context)
    return context


def run_audit(context: dict, agents_to_run: list, brief: str = "") -> dict:
    context["run_mode"] = "AUDIT"
    results = {}
    verdicts = []
    for agent_key in agents_to_run:
        if agent_key not in AGENT_REGISTRY:
            continue
        prior = "\n\n".join([f"--- {k.upper()} ---\n{v[:400]}..." for k, v in results.items()])
        result, path, verdict = _run_agent(agent_key, context, brief, prior)
        results[agent_key] = result
        verdicts.append(verdict)

    overall = _worst_verdict(verdicts) if verdicts else QA_CONDITIONAL
    last_path = context["artifacts"][-1]["path"] if context["artifacts"] else ""
    approved = request_human_review(last_path, f"QA Audit — {context['qa_name']}", overall)
    context["status"] = "AUDIT_APPROVED" if approved else "AUDIT_REJECTED"
    context["verdict"] = overall
    log_event(context, context["status"])
    save_context(context)
    return context


def run_sign_off(context: dict, brief: str = "") -> dict:
    """Full pre-launch QA gate — runs all applicable agents and issues sign-off."""
    context["run_mode"] = "SIGN_OFF"
    target = context.get("target_team", "dev")
    agents_to_run = TEAM_AGENT_SETS.get(target, TEAM_AGENT_SETS["dev"])

    notify_human(
        subject=f"Pre-launch QA sign-off started — {context['qa_name']}",
        message=(
            f"QA ID: {context['qa_id']}\n"
            f"Target: {target}\n"
            f"Agents: {', '.join(agents_to_run)}\n\n"
            f"You will receive a single sign-off request when all agents are complete."
        )
    )

    results = {}
    verdicts = []
    for agent_key in agents_to_run:
        prior = "\n\n".join([f"--- {k.upper()} ---\n{v[:400]}..." for k, v in results.items()])
        result, path, verdict = _run_agent(agent_key, context, brief, prior)
        results[agent_key] = result
        verdicts.append(verdict)

    overall = _worst_verdict(verdicts) if verdicts else QA_CONDITIONAL

    # Synthesise sign-off document
    orch = build_qa_orchestrator()
    synth = Task(
        description=f"""
Produce a Pre-Launch QA Sign-Off Certificate for {context['qa_name']}.
Overall verdict: {overall}
Agent reports: {json.dumps({k: v[:400] for k, v in results.items()}, indent=2)}

Include: executive summary, overall verdict, blocking issues list,
conditional items with owners and deadlines, sign-off statement.
{QA_INSTRUCTION}
""",
        expected_output="Pre-Launch QA Sign-Off Certificate.",
        agent=orch
    )
    crew = Crew(agents=[orch], tasks=[synth], process=Process.sequential, verbose=True)
    cert = str(crew.kickoff())
    cert_path = save_artifact(context, "QA Sign-Off Certificate",
                               "SIGN_OFF_CERT", cert, "output/sign_offs", overall)

    escalate_qa_failure(context, overall, cert_path, f"Pre-launch sign-off — {context['qa_name']}")
    approved = request_human_review(cert_path, f"Pre-Launch Sign-Off — {context['qa_name']}", overall)
    context["status"] = "SIGN_OFF_APPROVED" if approved else "SIGN_OFF_REJECTED"
    context["verdict"] = overall
    log_event(context, context["status"], cert_path)
    save_context(context)
    return context


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protean Pursuits — QA Team")
    parser.add_argument("--mode", choices=["test_cases", "audit", "full_qa", "sign_off"], required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--target", type=str, default="dev",
                        help=f"Target team: {list(TEAM_AGENT_SETS.keys())}")
    parser.add_argument("--project-id", type=str, default=None)
    parser.add_argument("--agents", type=str, default=None,
                        help="Comma-separated agent keys (overrides target defaults)")
    parser.add_argument("--brief", type=str, default="")
    args = parser.parse_args()

    context = create_qa_context(args.name, args.mode.upper(), args.target, args.project_id)
    print(f"\n🔍 Protean Pursuits QA Team | {args.mode.upper()} | {args.name}\n")

    agents = args.agents.split(",") if args.agents else TEAM_AGENT_SETS.get(args.target, ["functional"])

    if args.mode == "test_cases":
        context = run_test_cases(context, args.brief)
    elif args.mode in ("audit", "full_qa"):
        context = run_audit(context, agents, args.brief)
    elif args.mode == "sign_off":
        context = run_sign_off(context, args.brief)

    print(f"\n✅ Done. QA ID: {context['qa_id']} | Verdict: {context.get('verdict', 'N/A')} | Status: {context['status']}")
