import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

FLAGS_PATH = "FLAGS.md"

def append_srr_flags(new_flags: str):
    with open(FLAGS_PATH, "r") as f:
        content = f.read()

    # Replace the SRR pending placeholder
    content = content.replace(
        "## SRR-R (Security Review Report) — pending retrofit",
        new_flags
    )

    # Update the last updated date
    content = content.replace(
        "*Last updated: 2026-02-20*",
        f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d')}*"
    )

    with open(FLAGS_PATH, "w") as f:
        f.write(content)

    print(f"💾 FLAGS.md updated with SRR flags")


def build_security_engineer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Security Engineer",
        goal=(
            "Revise the existing Security Review Report to be fully "
            "deployment-agnostic — no Azure-specific security services, "
            "no cloud provider assumptions in threat models, controls, or "
            "compliance references. The revised SRR must describe a security "
            "posture that is implementable on cloud or on-premises infrastructure "
            "through configuration alone."
        ),
        backstory=(
            "You are a Senior Security Engineer with 12 years of experience "
            "securing government and healthcare systems across cloud and on-premises "
            "environments. You hold CISSP and have worked on ATO packages for "
            "VA, DoD, and civilian agency systems on Azure Government, AWS GovCloud, "
            "and fully air-gapped on-prem data centers. "
            "Your core principle: security controls must be described in terms of "
            "capabilities and standards — not provider implementations. "
            "This means: "
            "- Identity and access management references OIDC/OAuth2 standards, "
            "  not Azure AD or specific cloud IAM services. "
            "- Secrets management references generic patterns (secrets mounted at "
            "  /secrets/, SECRETS_BACKEND env var) not Azure Key Vault specifically. "
            "- Network security references standard K8s network policies and "
            "  cert-manager TLS — not Azure-specific network controls. "
            "- Audit logging references application-level audit logs using sub claim "
            "  — not Azure Monitor or cloud-specific SIEM. "
            "- Compliance controls (HIPAA, FedRAMP, FISMA) are described as "
            "  requirements — not tied to specific cloud compliance programs. "
            "- Vulnerability scanning uses open tools (Semgrep, OWASP ZAP, Trivy) "
            "  — not cloud-native scanning services. "
            "- Provider Reference Implementations are listed separately and clearly "
            "  labeled for each control. "
            "You produce security review documents that a team could implement on "
            "any compliant infrastructure without rewriting security controls."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_srr_retrofit(context: dict, srr_path: str) -> tuple:

    with open(srr_path) as f:
        srr_content = f.read()[:4000]

    security_engineer = build_security_engineer()

    retrofit_task = Task(
        description=f"""
You are the Security Engineer. The existing Security Review Report (SRR) below
contains Azure-specific security service references. Your job is to produce a
revised SRR that is fully deployment-agnostic.

--- EXISTING SRR (excerpt) ---
{srr_content}

Produce a complete REVISED Security Review Report (SRR-R).

DEPLOYMENT-AGNOSTIC RULES:
- No Azure AD, Azure Security Center, Azure Defender, Azure Policy references
- No Azure Key Vault as the only secrets option — use SECRETS_BACKEND pattern
- No Azure Monitor or Log Analytics for audit/SIEM — use generic log aggregation
- No cloud-specific compliance program references (e.g., "Azure FedRAMP High")
- Authentication controls reference OIDC/JWT standards, not specific providers
- Network controls reference K8s NetworkPolicy and cert-manager, not cloud VNets
- Vulnerability scanning uses Semgrep, OWASP ZAP, Trivy (all open source)
- All provider-specific controls labeled "Provider Reference Implementation"
- SECRETS_BACKEND env var controls which secrets provider is active
- OIDC_* env vars configure identity provider — no hardcoded provider

SECTIONS REQUIRED:

1. SECURITY OVERVIEW
   - Scope and objectives
   - Security design principles (defense in depth, least privilege, zero trust)
   - Compliance requirements: HIPAA, FedRAMP Moderate, FISMA
     * Described as requirements — not tied to cloud compliance programs
   - PHI handling summary

2. IDENTITY & ACCESS MANAGEMENT
   - Authentication: OIDC discovery + JWT validation via JWKS endpoint
     * No hardcoded provider — OIDC_ISSUER_URL configures provider
     * OIDC_MOCK=false required in all non-dev environments
   - Authorization: RBAC via configurable JWT roles claim (OIDC_ROLES_CLAIM)
   - Session management: short-lived JWTs, refresh token rotation
   - MFA: required by OIDC provider configuration (provider-agnostic requirement)
   - Provider Reference: Azure AD / Entra ID, Keycloak, Okta

3. SECRETS MANAGEMENT
   - Generic interface: app reads from /secrets/ mount path
   - SECRETS_BACKEND options: vault, azure-keyvault, aws-secrets-manager, env-file
   - Rotation: provider-agnostic rotation procedure
   - Never log secrets; never commit secrets to version control
   - Provider Reference: HashiCorp Vault (on-prem), Azure Key Vault (cloud), env-file (dev only)

4. NETWORK SECURITY
   - TLS everywhere: cert-manager issues certificates on any K8s cluster
   - K8s NetworkPolicy: restrict pod-to-pod communication
   - Ingress: NGINX or Traefik (works on any K8s)
   - No direct database exposure outside cluster
   - Provider Reference: cloud managed TLS vs cert-manager on-prem

5. DATA SECURITY
   - PHI masking: column-level masking in database views
   - Audit logging: records sub claim, action, resource, IP, user agent
   - Audit logs: never contain tokens, secrets, or full JWT payloads
   - Data in transit: TLS 1.2+ enforced at ingress
   - Data at rest: database encryption (provider-configurable)
   - Provider Reference: cloud managed encryption vs on-prem LUKS/filesystem encryption

6. APPLICATION SECURITY
   - Static analysis: Semgrep (runs in CI — no cloud dependency)
   - Dependency scanning: npm audit (runs in CI — no cloud dependency)
   - Dynamic analysis: OWASP ZAP against BASE_URL (deployment-agnostic)
   - Container scanning: Trivy (runs in CI — no cloud dependency)
   - OWASP Top 10 controls mapped to implementation
   - No provider-specific application security services

7. VULNERABILITY MANAGEMENT
   - All scanning tools: Semgrep, npm audit, OWASP ZAP, Trivy
   - Scan execution: make test-security (Makefile target — CI/CD agnostic)
   - Severity triage: Critical/High must be resolved before release
   - Provider Reference: cloud-native scanners (Defender for DevOps, Inspector) as alternatives

8. INCIDENT RESPONSE
   - Detection: AlertManager fires on Prometheus threshold breaches
   - Notification: ALERT_WEBHOOK_URL (Slack, Teams, PagerDuty — configurable)
   - Audit trail: application audit_log table + structured logs
   - Forensics: kubectl logs, Prometheus metrics, Grafana dashboards
   - No cloud-specific SIEM required
   - Provider Reference: Splunk, Azure Sentinel, AWS Security Hub as optional additions

9. COMPLIANCE MAPPING
   - HIPAA controls mapped to implementation (generic)
   - FedRAMP Moderate controls mapped to implementation (generic)
   - FISMA controls mapped to implementation (generic)
   - Each control: requirement + generic implementation + Provider Reference
   - No "covered by Azure compliance" shortcuts

10. RISK REGISTER
    - Risks identified with likelihood, impact, mitigation
    - Mitigations described generically
    - Residual risk assessment
    - No cloud-specific risk items unless paired with on-prem equivalent

Output the complete revised SRR-R as well-formatted markdown.
Every security control must be described generically.
Provider-specific content must be clearly labeled "Provider Reference Implementation".
All configuration must reference environment variables.
Flag any remaining Azure-specific references that could not be fully removed,
using this exact format at the end of your response:

## RETROFIT FLAGS
- FLAG: [location] | [issue] | [recommended fix]
""",
        expected_output="A complete revised deployment-agnostic Security Review Report, with any remaining flags listed at the end.",
        agent=security_engineer
    )

    crew = Crew(
        agents=[security_engineer],
        tasks=[retrofit_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔧 Security Engineer retrofitting SRR for deployment-agnostic compliance...\n")
    result = crew.kickoff()
    result_str = str(result)

    # Split out any flags the agent reported
    srr_body = result_str
    srr_flags_section = ""
    if "## RETROFIT FLAGS" in result_str:
        parts = result_str.split("## RETROFIT FLAGS")
        srr_body = parts[0]
        srr_flags_section = parts[1].strip()

    srr_revised_path = srr_path.replace("_SRR.md", "_SRR_R.md")
    with open(srr_revised_path, "w") as f:
        f.write(srr_body)

    print(f"\n💾 Revised SRR saved: {srr_revised_path}")

    # Build FLAGS.md entries from agent-reported flags
    next_flag_num = 5  # FLAG-001 through FLAG-004 already exist
    flags_to_append = "## SRR-R (Security Review Report)\n\n"

    if srr_flags_section:
        for line in srr_flags_section.splitlines():
            line = line.strip()
            if line.startswith("- FLAG:"):
                parts = line.replace("- FLAG:", "").split("|")
                if len(parts) == 3:
                    location = parts[0].strip()
                    issue = parts[1].strip()
                    fix = parts[2].strip()
                    flags_to_append += f"### FLAG-{next_flag_num:03d}\n"
                    flags_to_append += f"- **Severity:** Low\n"
                    flags_to_append += f"- **Location:** {location}\n"
                    flags_to_append += f"- **Issue:** {issue}\n"
                    flags_to_append += f"- **Should Be:** {fix}\n"
                    flags_to_append += f"- **Status:** Open\n\n"
                    next_flag_num += 1

    if flags_to_append == "## SRR-R (Security Review Report)\n\n":
        flags_to_append += "_No flags identified._\n"

    append_srr_flags(flags_to_append)

    context["artifacts"].append({
        "name": "Security Review Report (Revised)",
        "type": "SRR_R",
        "path": srr_revised_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Security Engineer (retrofit)"
    })
    context["status"] = "SRR_RETROFIT_COMPLETE"
    log_event(context, "SRR_RETROFIT_COMPLETE", srr_revised_path)
    save_context(context)

    return context, srr_revised_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    srr_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "SRR":
            srr_path = artifact["path"]

    if not srr_path:
        print("No SRR artifact found in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Retrofitting: {srr_path}")
    context, srr_revised_path = run_srr_retrofit(context, srr_path)

    print(f"\n✅ SRR retrofit complete.")
    print(f"📄 Revised SRR: {srr_revised_path}")
    print(f"📄 FLAGS.md updated.")
    with open(srr_revised_path) as f:
        print(f.read(500))
