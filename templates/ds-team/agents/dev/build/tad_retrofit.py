import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_architect() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Solutions Architect",
        goal=(
            "Revise the existing Technical Architecture Document to be fully "
            "deployment-agnostic — no Azure-specific services, no cloud provider "
            "assumptions in architecture diagrams or stack decisions. The revised "
            "TAD must describe an architecture that runs identically on cloud or "
            "on-premises infrastructure through configuration alone."
        ),
        backstory=(
            "You are a Senior Solutions Architect with 15 years of experience "
            "designing government and healthcare systems across cloud and on-premises "
            "infrastructure. You have architected systems on Azure Government, "
            "AWS GovCloud, and fully air-gapped on-prem data centers. "
            "Your core principle: architecture documents must describe the system "
            "in terms of capabilities and interfaces — not provider implementations. "
            "This means: "
            "- Infrastructure components are described generically: "
            "  'Kubernetes cluster' not 'AKS', 'container registry' not 'ACR', "
            "  'managed PostgreSQL' not 'Azure Database for PostgreSQL'. "
            "- Authentication is described as 'OIDC-compliant identity provider' "
            "  not 'Auth0' or 'Azure AD'. "
            "- Secrets management is described as 'secrets management service' "
            "  not 'Azure Key Vault'. "
            "- Monitoring is described as 'Prometheus + Grafana' (provider-agnostic) "
            "  not 'Azure Monitor'. "
            "- Object storage is described as 'S3-compatible object storage' "
            "  not 'Azure Blob Storage'. "
            "- Architecture diagrams use generic component names with provider "
            "  examples listed separately as 'Provider Reference Implementations'. "
            "- DEPLOY_TARGET env var (cloud | onprem) controls which provider "
            "  implementations are active at runtime. "
            "You produce architecture documents that a team could implement on "
            "any compliant infrastructure without rewriting application code."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_tad_retrofit(context: dict, tad_path: str) -> dict:

    with open(tad_path) as f:
        tad_content = f.read()[:4000]

    architect = build_architect()

    retrofit_task = Task(
        description=f"""
You are the Solutions Architect. The existing Technical Architecture Document (TAD)
below contains Azure-specific service references throughout. Your job is to produce
a revised TAD that is fully deployment-agnostic.

--- EXISTING TAD (excerpt) ---
{tad_content}

Produce a complete REVISED Technical Architecture Document (TAD-R).

DEPLOYMENT-AGNOSTIC RULES:
- Replace all Azure-specific service names with generic capability descriptions
- Provider Reference Implementations listed separately, clearly labeled
- DEPLOY_TARGET=cloud or DEPLOY_TARGET=onprem controls active implementations
- All external service references use env vars (no hardcoded endpoints)
- Authentication: "OIDC-compliant identity provider" (not Auth0 or Azure AD)
- Secrets: "secrets management service" (not Azure Key Vault)
- Registry: "container registry" referenced via CONTAINER_REGISTRY env var
- Database: "PostgreSQL" (not Azure Database for PostgreSQL)
- Monitoring: "Prometheus + Grafana" (not Azure Monitor)
- Storage: "S3-compatible object storage" (not Azure Blob)
- Kubernetes: "Kubernetes cluster" (not AKS)
- CI/CD: "pipeline" calling Makefile targets (not Azure DevOps or GitHub Actions-specific)

SECTIONS REQUIRED:

1. SYSTEM OVERVIEW
   - Purpose and scope
   - Key design principles (deployment-agnostic, 12-factor app, OIDC-native)
   - Technology stack summary — all generic capability descriptions
   - Provider Reference Implementations table (Azure, AWS, on-prem equivalents)

2. ARCHITECTURE DIAGRAM (text/ASCII)
   - Show components and their relationships
   - Use generic names: "K8s Cluster", "Container Registry", "Identity Provider",
     "Secrets Service", "PostgreSQL", "Prometheus/Grafana", "Ingress/TLS"
   - No cloud provider logos or service names in the diagram

3. COMPONENT DESCRIPTIONS
   For each component, describe:
   - Purpose and responsibility
   - Interface (what it exposes/consumes)
   - Configuration (env vars that configure it)
   - Provider Reference: cloud implementation + on-prem implementation

   Components to cover:
   - Frontend (Next.js) — static assets, SSR, talks to backend via BASE_URL
   - Backend API (Node.js/Express) — REST API, OIDC JWT auth, Prisma ORM
   - PostgreSQL Database — primary data store, connection via DATABASE_URL
   - Identity Provider — OIDC/OAuth2, configured via OIDC_* env vars
   - Secrets Management Service — generic interface, SECRETS_BACKEND env var
   - Container Registry — CONTAINER_REGISTRY env var
   - Kubernetes Cluster — orchestration, DEPLOY_TARGET controls cluster type
   - Ingress / TLS — cert-manager (works on any K8s)
   - Prometheus + Grafana — monitoring stack (kube-prometheus-stack)
   - CI/CD Pipeline — calls Makefile targets, DEPLOY_TARGET from secret

4. DATA FLOW
   - User authentication flow (OIDC — provider-agnostic)
   - Trip data query flow
   - Export flow
   - Audit logging flow
   - No provider-specific SDK calls in any flow

5. SECURITY ARCHITECTURE
   - Authentication: OIDC discovery, JWT validation via JWKS endpoint
   - Authorization: RBAC via configurable JWT roles claim (OIDC_ROLES_CLAIM)
   - Secrets: generic /secrets/ mount, SECRETS_BACKEND controls provider
   - Network: TLS everywhere, cert-manager (works on any K8s)
   - PHI protection: column-level masking, audit logs use sub claim only
   - Provider Reference: Azure Key Vault vs HashiCorp Vault vs env-file

6. DEPLOYMENT ARCHITECTURE
   - DEPLOY_TARGET=cloud: managed K8s + managed registry + cloud secrets
   - DEPLOY_TARGET=onprem: bare K8s (kubeadm/k3s/RKE2) + local registry + Vault
   - Helm chart with values.cloud.yaml and values.onprem.yaml
   - Same application image deployed to either target — no code changes
   - Environment variable table: all variables with cloud and on-prem example values

7. SCALABILITY & RELIABILITY
   - Horizontal Pod Autoscaler (standard K8s — works anywhere)
   - PostgreSQL connection pooling (PgBouncer — works anywhere)
   - Health check endpoints (/health, /ready)
   - Graceful shutdown handling
   - No cloud-specific autoscaling services

8. TECHNOLOGY DECISIONS
   - For each major technology choice, explain:
     * What was chosen and why
     * Why it is deployment-agnostic
     * Provider Reference Implementations

Output the complete revised TAD-R as well-formatted markdown.
Every component must be described generically.
Provider-specific content must be clearly labeled "Provider Reference Implementation".
All configuration must reference environment variables.
""",
        expected_output="A complete revised deployment-agnostic Technical Architecture Document.",
        agent=architect
    )

    crew = Crew(
        agents=[architect],
        tasks=[retrofit_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔧 Solutions Architect retrofitting TAD for deployment-agnostic compliance...\n")
    result = crew.kickoff()

    tad_revised_path = tad_path.replace("_TAD.md", "_TAD_R.md")
    with open(tad_revised_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Revised TAD saved: {tad_revised_path}")

    context["artifacts"].append({
        "name": "Technical Architecture Document (Revised)",
        "type": "TAD_R",
        "path": tad_revised_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Solutions Architect (retrofit)"
    })
    context["status"] = "TAD_RETROFIT_COMPLETE"
    log_event(context, "TAD_RETROFIT_COMPLETE", tad_revised_path)
    save_context(context)

    return context, tad_revised_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    tad_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "TAD":
            tad_path = artifact["path"]

    if not tad_path:
        print("No TAD artifact found in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Retrofitting: {tad_path}")
    context, tad_revised_path = run_tad_retrofit(context, tad_path)

    print(f"\n✅ TAD retrofit complete.")
    print(f"📄 Revised TAD: {tad_revised_path}")
    with open(tad_revised_path) as f:
        print(f.read(500))
