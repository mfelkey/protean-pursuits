import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_devops_engineer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="DevOps Engineer",
        goal=(
            "Revise the existing DevOps Implementation Report to be fully "
            "deployment-agnostic — no cloud provider assumptions, no hardcoded "
            "infrastructure references. The revised DIR must work equally well "
            "for cloud and on-premises deployments through configuration alone."
        ),
        backstory=(
            "You are a Senior DevOps Engineer with 12 years of experience across "
            "cloud and on-premises government deployments. You have run federal "
            "systems on Azure Government, AWS GovCloud, and fully air-gapped "
            "on-premises Kubernetes clusters. You know that infrastructure decisions "
            "change — a system designed for Azure today may need to run on-prem "
            "tomorrow, or vice versa. "
            "Your core principle: infrastructure code and CI/CD pipelines must be "
            "deployment-agnostic. This means: "
            "- No cloud provider SDKs or CLIs hardcoded into application pipelines. "
            "- No provider-specific service names (Azure Key Vault, AWS Secrets "
            "  Manager, GCP Secret Manager) in application config — use a generic "
            "  secrets interface configured via SECRETS_BACKEND env var. "
            "- Container orchestration via standard Kubernetes manifests and Helm "
            "  charts — not AKS-specific, EKS-specific, or GKE-specific addons. "
            "- Monitoring via provider-agnostic stack (Prometheus + Grafana) — "
            "  not Azure Monitor, CloudWatch, or Stackdriver. "
            "- CI/CD pipeline calls Makefile targets, not cloud-specific CLI commands. "
            "- Infrastructure-as-code uses modules that abstract the provider — "
            "  a cloud module and an on-prem module implement the same interface. "
            "- DEPLOY_TARGET env var (cloud | onprem) controls which modules activate. "
            "You label Azure-specific content clearly as 'Cloud Reference Implementation' "
            "and provide parallel on-prem equivalents for every cloud-specific section."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_dir_retrofit(context: dict, dir_path: str) -> dict:

    with open(dir_path) as f:
        dir_content = f.read()[:4000]

    devops = build_devops_engineer()

    retrofit_task = Task(
        description=f"""
You are the DevOps Engineer. The existing DevOps Implementation Report (DIR)
below was written with Azure-specific assumptions throughout. Your job is to
produce a revised DIR that is fully deployment-agnostic.

--- EXISTING DIR (excerpt) ---
{dir_content}

Produce a complete REVISED DevOps Implementation Report (DIR-R) with ALL
of the following sections. Every section must follow the deployment-agnostic
principles — no Azure, AWS, or GCP assumptions in application-level config.

DEPLOYMENT-AGNOSTIC RULES (apply to every section):
- All environment-specific values come from environment variables
- DEPLOY_TARGET=cloud or DEPLOY_TARGET=onprem controls behavior
- Cloud-specific content is labeled "Cloud Reference Implementation"
- On-prem equivalents are provided for every cloud-specific section
- CI/CD pipeline calls Makefile targets only — no cloud CLI commands
- Secrets management uses a generic interface (SECRETS_BACKEND env var)
  with pluggable backends (Vault, Azure Key Vault, AWS Secrets Manager,
  environment files for local/on-prem)
- Monitoring uses Prometheus + Grafana (runs anywhere) not Azure Monitor
- Container registry referenced via CONTAINER_REGISTRY env var
- Kubernetes manifests use standard K8s — no cloud-specific addons

SECTIONS REQUIRED:

1. LOCAL DEVELOPMENT ENVIRONMENT
   - docker-compose.yml (PostgreSQL, backend, frontend, mock secrets service)
   - .env.example with ALL variables including DEPLOY_TARGET, SECRETS_BACKEND,
     CONTAINER_REGISTRY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
   - Makefile (dev, test, build, migrate, seed, deploy — all deployment-agnostic)
   - First-time setup instructions that work on any Linux/Mac machine

2. DOCKERFILE IMPLEMENTATIONS
   - Backend Dockerfile (multi-stage, non-root, minimal image)
   - Frontend Dockerfile (multi-stage, non-root, minimal image)
   - .dockerignore
   - Images tagged as $CONTAINER_REGISTRY/backend:$VERSION (no registry hardcoded)

3. CI/CD PIPELINE
   - .github/workflows/ci.yml (lint, test, security scan, build)
     * Uses: make lint, make test, make build — no cloud CLI
     * DEPLOY_TARGET read from GitHub secret
   - .github/workflows/cd.yml (deploy to staging, deploy to production)
     * Uses: make deploy ENV=staging, make deploy ENV=production
     * No Azure CLI, AWS CLI, or GCP CLI commands
     * Cloud-specific deployment steps isolated in Makefile targets
   - Makefile deploy targets:
     * deploy-cloud: calls Helm + cloud-specific registry auth
     * deploy-onprem: calls Helm + on-prem registry auth
     * deploy: delegates to deploy-cloud or deploy-onprem based on DEPLOY_TARGET

4. INFRASTRUCTURE AS CODE
   - Module structure:
     * infra/modules/kubernetes/ — provider-agnostic K8s config
     * infra/modules/database/ — provider-agnostic PostgreSQL config
     * infra/modules/secrets/ — provider-agnostic secrets config
     * infra/cloud/ — Cloud Reference Implementation (Terraform, Azure example)
     * infra/onprem/ — On-Prem Implementation (Ansible, bare K8s example)
   - Variables file: infra/variables.tf or infra/vars.yml
     (all provider-specific values injected, nothing hardcoded)
   - README explaining how to use cloud vs onprem modules

5. KUBERNETES MANIFESTS
   - Standard K8s manifests (no cloud-specific annotations unless tagged @cloud-only)
   - Namespaces, Deployments, Services, HPA, ConfigMaps
   - Secrets via generic volume mount — backend reads from mounted path,
     not from cloud SDK. SECRETS_BACKEND controls the provider.
   - Ingress with TLS (cert-manager for both cloud and on-prem)
   - Pod Security Standards (runAsNonRoot, readOnlyRootFilesystem)
   - Resource limits and requests

6. HELM CHART
   - Chart.yaml, values.yaml
   - values.cloud.yaml (cloud overrides)
   - values.onprem.yaml (on-prem overrides)
   - Deploy command: helm upgrade --install -f values.$DEPLOY_TARGET.yaml
   - No cloud-specific chart dependencies

7. SECRETS MANAGEMENT (DEPLOYMENT-AGNOSTIC)
   - Generic secrets interface: app reads from /secrets/ mount path
   - SECRETS_BACKEND options:
     * vault: HashiCorp Vault (on-prem or self-hosted)
     * azure-keyvault: Azure Key Vault (cloud reference)
     * aws-secrets-manager: AWS (cloud reference)
     * env-file: .env file (local development)
   - Kubernetes secret injection via init container pattern
     (works with any backend — no cloud CSI driver required)
   - Example init container that fetches secrets from Vault

8. MONITORING & ALERTING (DEPLOYMENT-AGNOSTIC)
   - Prometheus + Grafana stack (runs on any K8s cluster)
   - prometheus.yml scrape config
   - Grafana dashboard JSON for application metrics
   - Alert rules (Prometheus AlertManager):
     * API error rate > 5%
     * Response time p95 > 2s
     * Pod restart count > 3
     * Database connection pool exhausted
   - Notification via AlertManager webhook (deployment-agnostic)
     * ALERT_WEBHOOK_URL env var — can point to Slack, Teams, PagerDuty, email relay

9. DISASTER RECOVERY
   - Database backup strategy (pg_dump — works on any PostgreSQL)
   - Backup storage: BACKUP_STORAGE_PATH env var
     * Cloud: object storage bucket URL
     * On-prem: NFS mount path or local path
   - Restore procedure
   - RTO/RPO targets (30min RTO, 1hr RPO)
   - Backup verification cron job

10. OPERATIONS RUNBOOK
    - Deploy new release (make deploy ENV=production)
    - Rollback (helm rollback)
    - Scale application (kubectl scale)
    - Rotate secrets (SECRETS_BACKEND-aware procedure)
    - Access logs (kubectl logs — works anywhere)
    - Run database migrations in production
    - Health check endpoints

Output the complete revised DIR as well-formatted markdown.
Every section must be deployment-agnostic.
Cloud-specific content must be clearly labeled "Cloud Reference Implementation".
On-prem equivalents must be provided alongside every cloud-specific section.
""",
        expected_output="A complete revised deployment-agnostic DevOps Implementation Report.",
        agent=devops
    )

    crew = Crew(
        agents=[devops],
        tasks=[retrofit_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔧 DevOps Engineer retrofitting DIR for deployment-agnostic compliance...\n")
    result = crew.kickoff()

    dir_revised_path = dir_path.replace("_DIR.md", "_DIR_R.md")
    with open(dir_revised_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Revised DIR saved: {dir_revised_path}")

    context["artifacts"].append({
        "name": "DevOps Implementation Report (Revised)",
        "type": "DIR_R",
        "path": dir_revised_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "DevOps Engineer (retrofit)"
    })
    context["status"] = "DIR_RETROFIT_COMPLETE"
    log_event(context, "DIR_RETROFIT_COMPLETE", dir_revised_path)
    save_context(context)

    return context, dir_revised_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    dir_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "DIR":
            dir_path = artifact["path"]

    if not dir_path:
        print("No DIR artifact found in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Retrofitting: {dir_path}")
    context, dir_revised_path = run_dir_retrofit(context, dir_path)

    print(f"\n✅ DIR retrofit complete.")
    print(f"📄 Revised DIR: {dir_revised_path}")
    with open(dir_revised_path) as f:
        print(f.read(500))
