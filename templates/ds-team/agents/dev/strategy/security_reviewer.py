import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context
from agents.orchestrator.context_manager import load_agent_context, format_context_for_prompt, on_artifact_saved
from agents.shared.knowledge_curator.rag_inject import get_knowledge_context


load_dotenv("config/.env")

def build_security_reviewer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/gpt-oss:120b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Security Reviewer",
        goal=(
            "Identify security vulnerabilities, compliance gaps, and privacy risks "
            "in the proposed architecture and deliver a Security Review Report with "
            "actionable remediation guidance before any code is written."
        ),
        backstory=(
            "You are a Senior Information Security Engineer with 12 years of experience "
            "in federal IT security, specializing in VA and DoD systems. You hold CISSP, "
            "CISM, and AWS/Azure security certifications. You have conducted dozens of "
            "Authority to Operate (ATO) reviews under NIST 800-53 and FISMA, and you "
            "know exactly where architects cut corners that later become audit findings. "
            "You review systems through three lenses: confidentiality (PHI protection, "
            "access control), integrity (data validation, audit trails, tamper prevention), "
            "and availability (resilience, failover, DoS protection). "
            "You are not a rubber stamp — you flag real issues with specific remediation "
            "steps. You also understand AI/ML-specific security risks including model "
            "poisoning, adversarial inputs, prompt injection in LLM systems, training "
            "data exposure, and the unique audit requirements for automated decision systems. "
            "Your Security Review Report is the final gate before the development team "
            "begins implementation. Nothing gets built until your findings are addressed."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_security_review(context: dict, prd_path: str, tad_path: str) -> dict:
    """
    Reviews PRD and TAD and produces a Security Review Report (SRR).
    Returns updated context.
    """
    # ── Smart extraction: load relevant sections for security ──
    ctx = load_agent_context(
        context=context,
        consumer="security",
        artifact_types=["PRD", "TAD"],
        max_chars_per_artifact=6000
    )
    prompt_context = format_context_for_prompt(ctx)

    # ── RAG: inject current security knowledge (CVEs, OWASP, VA policy) ──
    knowledge = get_knowledge_context(
        agent_role="Security Reviewer",
        task_summary=f"Security review for {context.get('structured_spec', {}).get('title', 'project')}",
    )

    sr = build_security_reviewer()

    review_task = Task(
        description=f"""
You are conducting a pre-implementation security review of the following project:

{prompt_context}

CURRENT SECURITY INTELLIGENCE (from knowledge base — reference in your findings where relevant):
{knowledge}

Produce a complete Security Review Report (SRR) with ALL of the following sections:

1. EXECUTIVE SUMMARY
   - Overall security posture rating (RED/AMBER/GREEN)
   - Top 3 critical findings requiring immediate action
   - Recommendation: Approved / Approved with Conditions / Not Approved

2. THREAT MODEL
   - Identify the top 8 threats using STRIDE methodology
     (Spoofing, Tampering, Repudiation, Information Disclosure,
      Denial of Service, Elevation of Privilege)
   - For each threat: description, affected component, likelihood, impact, risk rating

3. VULNERABILITY ASSESSMENT
   - Review each architecture component for security weaknesses
   - Flag any findings as: CRITICAL / HIGH / MEDIUM / LOW
   - Include specific remediation for each finding
   - Cross-reference with any relevant CVEs from the security intelligence above

4. COMPLIANCE GAP ANALYSIS
   - HIPAA Security Rule gaps
   - NIST 800-53 control gaps (focus on AC, AU, SC, SI control families)
   - VA Handbook 6500 gaps
   - Section 508 security considerations

5. PHI & DATA PRIVACY REVIEW
   - PHI data flow analysis (where does PHI touch the system?)
   - Tokenization/masking adequacy assessment
   - Data minimization review
   - Privacy Impact Assessment (PIA) readiness

6. AI/ML SECURITY CONSIDERATIONS
   - Model integrity risks
   - Training data security
   - Inference API attack surface
   - Audit requirements for automated classification decisions

7. SECURITY CONTROLS MATRIX
   - Map required controls to implementation status
   - Status: IMPLEMENTED / PLANNED / GAP / NOT APPLICABLE
   - Priority for each gap

8. REMEDIATION ROADMAP
   - Prioritized list of all findings
   - Owner assignment (which team role fixes it)
   - Target sprint for remediation
   - Verification method

Output the complete Security Review Report as well-formatted markdown.
""",
        expected_output="A complete Security Review Report in markdown format.",
        agent=sr
    )

    crew = Crew(
        agents=[sr],
        tasks=[review_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔒 Security Reviewer conducting security review...\n")
    result = crew.kickoff()

    os.makedirs("dev/security", exist_ok=True)
    srr_path = f"dev/security/{context['project_id']}_SRR.md"
    with open(srr_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Security Review Report saved: {srr_path}")

    context["artifacts"].append({
        "name": "Security Review Report",
        "type": "SRR",
        "path": srr_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Security Reviewer"
    })
    on_artifact_saved(context, "SRR", srr_path)
    context["status"] = "SECURITY_REVIEW_COMPLETE"
    log_event(context, "SECURITY_REVIEW_COMPLETE", srr_path)
    save_context(context)

    return context, srr_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    prd_path = tad_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "PRD":
            prd_path = artifact["path"]
        if artifact.get("type") == "TAD":
            tad_path = artifact["path"]

    if not all([prd_path, tad_path]):
        print("Missing PRD or TAD.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, srr_path = run_security_review(context, prd_path, tad_path)

    print(f"\n✅ Security review complete.")
    print(f"📄 SRR: {srr_path}")
    print(f"\nFirst 500 chars:")
    with open(srr_path) as f:
        print(f.read(500))
