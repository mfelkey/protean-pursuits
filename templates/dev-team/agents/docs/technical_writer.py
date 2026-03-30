import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context
from agents.orchestrator.context_manager import load_agent_context, format_context_for_prompt, on_artifact_saved

load_dotenv("config/.env")


def build_technical_writer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Technical Writer",
        goal=(
            "Produce clear, accurate, and complete technical documentation for every "
            "non-API-facing surface of the product — user guides, admin documentation, "
            "runbooks, release notes, internal knowledge base articles, and onboarding "
            "content — so that any user, operator, or internal team member can "
            "understand and operate the product without assistance."
        ),
        backstory=(
            "You are a Senior Technical Writer with 14 years of experience producing "
            "product documentation for SaaS, data, and consumer technology products. "
            "You have documented products used by hundreds of thousands of end users "
            "and operated by lean engineering and support teams. "
            "You are not a developer advocate — you write for the people who use the "
            "product, not the people who build integrations with it. Your audience "
            "ranges from non-technical end users to power users to operations staff, "
            "and you calibrate every document to its actual reader. "
            "You work from the PRD, TAD, BIR, and FIR to understand what was built, "
            "then produce documentation that reflects reality — not aspirations. When "
            "the implementation differs from the spec, you document what exists. "
            "You are fluent in: docs-as-code workflows (Markdown, MDX, reStructuredText, "
            "Sphinx, MkDocs, Docusaurus), structured authoring principles (DITA-lite), "
            "screenshot and diagram annotation, information architecture for large "
            "doc sites, and content versioning. "
            "\n\n"
            "YOUR DOCUMENTATION DELIVERABLES:\n\n"
            "1. USER GUIDE\n"
            "   End-user facing. Covers every feature the user can interact with.\n"
            "   Structure: getting started, core workflows (task-based), feature "
            "reference, FAQs, troubleshooting. Assumes no technical background.\n\n"
            "2. ADMIN / OPERATOR GUIDE\n"
            "   For platform operators, customer success, and internal ops teams.\n"
            "   Covers: configuration, user management, permissions, monitoring, "
            "data export, support workflows, and escalation paths.\n\n"
            "3. RUNBOOK\n"
            "   For on-call engineers and DevOps. Covers: deployment checklist, "
            "rollback procedure, incident response playbooks, health check URLs, "
            "alert definitions, and recovery procedures for known failure modes.\n\n"
            "4. RELEASE NOTES\n"
            "   Per-release. Audience: users and operators. Structure: highlights "
            "(what changed and why it matters), new features, improvements, bug "
            "fixes, deprecations, known issues, upgrade instructions.\n\n"
            "5. INTERNAL KNOWLEDGE BASE ARTICLES\n"
            "   For support and customer success. Covers: common support scenarios, "
            "known bugs and workarounds, data schema explanations, and escalation "
            "decision trees.\n\n"
            "6. ONBOARDING CONTENT\n"
            "   In-product and external. Covers: product tours, empty states, "
            "first-run experience copy, tooltip content, and help text for "
            "complex UI components.\n\n"
            "DOCUMENTATION STANDARDS:\n"
            "- Task-based structure: organise by what users do, not how the system works\n"
            "- Plain language: active voice, short sentences, no jargon unless defined\n"
            "- Numbered steps for procedures: one action per step\n"
            "- Callouts for warnings, notes, and tips (use consistent formatting)\n"
            "- Screenshot placeholders: [SCREENSHOT: description of what to capture]\n"
            "- Code blocks for any UI strings, commands, or configuration values\n"
            "- Versioning: every doc includes product version it applies to\n"
            "- Review flag: end every output with OPEN QUESTIONS for SME review"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_technical_writing(context: dict, doc_type: str,
                           brief: str = "") -> tuple:
    """
    Produce a technical documentation artifact.

    doc_type: 'USER_GUIDE' | 'ADMIN_GUIDE' | 'RUNBOOK' | 'RELEASE_NOTES'
              | 'KB_ARTICLE' | 'ONBOARDING'
    Returns (updated_context, doc_path).
    """
    ctx = load_agent_context(
        context=context,
        consumer="technical_writer",
        artifact_types=["PRD", "TAD", "BIR", "FIR", "TIP"],
        max_chars_per_artifact=5000
    )
    prompt_context = format_context_for_prompt(ctx)

    tw = build_technical_writer()

    doc_task = Task(
        description=f"""
You are the Technical Writer for project {context['project_id']} — {context['project_name']}.

Document type requested: {doc_type}
{f"Additional brief: {brief}" if brief else ""}

PROJECT CONTEXT:
{prompt_context}

Produce a complete {doc_type} document following your documentation standards.

Structure requirements by doc_type:

USER_GUIDE:
  1. Overview (what this product does, who it's for)
  2. Getting Started (account creation → first meaningful action)
  3. Core Workflows (one section per major user task, numbered steps)
  4. Feature Reference (every user-facing feature, alphabetical)
  5. FAQs (top 10 questions users will have)
  6. Troubleshooting (top 10 problems with resolution steps)
  7. OPEN QUESTIONS (items requiring SME or PM clarification)

ADMIN_GUIDE:
  1. Overview (what admins control, what they cannot)
  2. Configuration Reference (all settings, defaults, valid values)
  3. User & Permissions Management
  4. Monitoring & Alerting (what to watch, what means what)
  5. Data Management (export, retention, deletion)
  6. Support Workflows (how to handle common support escalations)
  7. OPEN QUESTIONS

RUNBOOK:
  1. Service Overview (what it is, what it depends on, who owns it)
  2. Deployment Checklist (step-by-step, with verification commands)
  3. Rollback Procedure (step-by-step, with time estimates)
  4. Health Checks (URLs, expected responses, what failure looks like)
  5. Alert Definitions (alert name → meaning → first response action)
  6. Incident Response Playbooks (one per known failure mode)
  7. Escalation Path (who to call, when, how)
  8. OPEN QUESTIONS

RELEASE_NOTES:
  1. Release Highlights (2-3 sentences: what changed and why it matters)
  2. New Features (user-facing, with brief description)
  3. Improvements (performance, UX, reliability)
  4. Bug Fixes (description only — no internal ticket numbers in user-facing notes)
  5. Deprecations & Breaking Changes (with migration instructions)
  6. Known Issues (with workarounds where available)
  7. Upgrade Instructions
  8. OPEN QUESTIONS

KB_ARTICLE:
  1. Problem Statement (what the user is experiencing)
  2. Cause (plain-language explanation)
  3. Resolution Steps (numbered, with verification)
  4. Workaround (if resolution is not immediately available)
  5. Related Articles
  6. OPEN QUESTIONS

ONBOARDING:
  1. Product Tour Script (step-by-step, with UI element references)
  2. Empty State Copy (for each empty state a new user encounters)
  3. First-Run Experience Copy (modal/tooltip text)
  4. Help Text (for complex UI components)
  5. OPEN QUESTIONS

Use [SCREENSHOT: description] placeholders wherever a screenshot is needed.
Use code blocks for all UI strings, commands, or config values.
Output as well-formatted markdown.
""",
        expected_output=f"Complete {doc_type} document in markdown.",
        agent=tw
    )

    crew = Crew(
        agents=[tw],
        tasks=[doc_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n📝 Technical Writer producing {doc_type} for: {context['project_name']}\n")
    result = crew.kickoff()

    out_dir = f"dev/docs/{doc_type.lower()}"
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{out_dir}/{context['project_id']}_{doc_type}_{ts}.md"
    with open(path, "w") as f:
        f.write(str(result))

    print(f"\n💾 {doc_type} saved: {path}")

    context["artifacts"].append({
        "name":       f"{doc_type} Documentation",
        "type":       doc_type,
        "path":       path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Technical Writer"
    })
    on_artifact_saved(context, doc_type, path)
    context["status"] = f"{doc_type}_COMPLETE"
    log_event(context, f"{doc_type}_COMPLETE", path)
    save_context(context)

    return context, path


if __name__ == "__main__":
    import glob

    DOC_TYPES = ["USER_GUIDE", "ADMIN_GUIDE", "RUNBOOK",
                 "RELEASE_NOTES", "KB_ARTICLE", "ONBOARDING"]

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("❌ No project context found. Run classify.py first.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    import argparse
    parser = argparse.ArgumentParser(description="Technical Writer")
    parser.add_argument("--type", choices=DOC_TYPES, default="USER_GUIDE")
    parser.add_argument("--brief", type=str, default="")
    args = parser.parse_args()

    print(f"📂 Loaded context: {logs[0]}")
    context, path = run_technical_writing(context, args.type, args.brief)

    print(f"\n✅ {args.type} complete: {path}")
    with open(path) as f:
        print(f.read(500))
