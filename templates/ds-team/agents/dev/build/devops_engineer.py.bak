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
            "Design and implement the complete CI/CD pipeline, containerization, "
            "infrastructure-as-code, and deployment strategy that takes the "
            "application from source code to production reliably, securely, "
            "and repeatably."
        ),
        backstory=(
            "You are a Senior DevOps Engineer with 12 years of experience building "
            "and operating production infrastructure for government and healthcare "
            "systems. You have deep expertise in Azure Government Cloud, Kubernetes, "
            "Docker, Terraform, and GitHub Actions. "
            "You have shepherded multiple federal systems through ATO processes and "
            "know exactly what infrastructure controls, audit trails, and deployment "
            "safeguards are required for FISMA compliance. "
            "You are fluent in: Bash and Python for scripting and automation; "
            "Terraform and Bicep for infrastructure-as-code; Kubernetes and Helm "
            "for container orchestration; Docker for containerization; and GitHub "
            "Actions for CI/CD pipelines. You understand networking, TLS, secrets "
            "management, and zero-trust architecture at a deep level. "
            "You believe infrastructure is code — everything is version controlled, "
            "everything is reproducible, nothing is manually configured in production. "
            "You work from the Technical Implementation Plan, Technical Architecture "
            "Document, and the Security Review Report. You take the SRR findings "
            "seriously — every CRITICAL and HIGH finding from the security reviewer "
            "that has an infrastructure component gets addressed in your implementation. "
            "You produce a DevOps Implementation Report (DIR) that gives the development "
            "team everything they need to build, test, and deploy the application — "
            "from local development setup through production deployment. "
            "Nothing goes to production without passing your pipeline."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_devops_implementation(context: dict, tip_path: str, tad_path: str, srr_path: str) -> dict:
    """
    Reads TIP, TAD, and SRR and produces a DevOps Implementation Report (DIR).
    Returns updated context.
    """

    with open(tip_path) as f:
        tip_content = f.read()[:1500]

    with open(tad_path) as f:
        tad_content = f.read()[:1500]

    with open(srr_path) as f:
        srr_content = f.read()[:1500]

    de = build_devops_engineer()

    dir_task = Task(
        description=f"""
You are the DevOps Engineer for the following project. Using the documents below,
produce a complete DevOps Implementation Report (DIR) with working configuration
files and scripts for all pipeline and infrastructure components.

--- Technical Implementation Plan (excerpt) ---
{tip_content}

--- Technical Architecture Document (excerpt) ---
{tad_content}

--- Security Review Report (excerpt) ---
{srr_content}

Produce a complete DevOps Implementation Report (DIR) with ALL of the following sections:

1. LOCAL DEVELOPMENT ENVIRONMENT
   - docker-compose.yml for full local stack
     (PostgreSQL, backend, frontend, mock Azure services)
   - .env.example with all required variables
   - Makefile with common developer commands
     (make dev, make test, make build, make migrate, make seed)
   - First-time setup instructions (step by step)

2. DOCKERFILE IMPLEMENTATIONS
   - Backend Dockerfile (multi-stage build, non-root user, minimal image)
   - Frontend Dockerfile (multi-stage build, Next.js production build)
   - Data pipeline Dockerfile (Python, Databricks CLI)
   - .dockerignore files
   - Image security hardening notes (from SRR findings)

3. CI/CD PIPELINE (GitHub Actions)
   - Complete workflow file: .github/workflows/ci.yml
     * Triggers (push to main, PR to main)
     * Jobs: lint, test, security-scan, build, deploy
   - Complete workflow file: .github/workflows/cd.yml
     * Staging deployment
     * Production deployment (requires manual approval)
     * Rollback procedure
   - Secrets management in GitHub Actions
   - Branch protection rules specification

4. INFRASTRUCTURE AS CODE (Terraform)
   - Azure Government Cloud provider configuration
   - Resource definitions:
     * Azure Container Registry
     * Azure Kubernetes Service (private cluster)
     * Azure SQL Database (Business Critical)
     * Azure Data Lake Storage Gen2
     * Azure Key Vault
     * Azure Virtual Network with subnets
     * Network Security Groups
     * Private Endpoints
   - Terraform state management (Azure Storage backend)
   - Variable files and tfvars structure

5. KUBERNETES MANIFESTS
   - Namespace definitions
   - Backend deployment and service
   - Frontend deployment and service
   - Horizontal Pod Autoscaler
   - ConfigMaps and Secrets (referencing Key Vault)
   - Ingress controller configuration (with TLS)
   - Pod Security Standards enforcement
   - Resource limits and requests

6. HELM CHART STRUCTURE
   - Chart.yaml
   - values.yaml (with environment overrides)
   - templates/ structure
   - Deployment via Helm commands

7. SECURITY CONTROLS IMPLEMENTATION
   - Addressing CRITICAL findings from SRR:
     * Private endpoints for all Azure services
     * Pod Security Standards (runAsNonRoot, read-only filesystem)
     * Azure Key Vault integration for secrets
     * Network Security Group rules
     * Container image scanning in pipeline
   - TLS certificate management
   - Secrets rotation procedure

8. MONITORING & ALERTING
   - Azure Monitor configuration
   - Log Analytics workspace setup
   - Key alerts to configure
     (pipeline failures, error rates, auth failures, PHI access)
   - Dashboard configuration for operations team

9. DISASTER RECOVERY PROCEDURE
   - Backup strategy for Azure SQL
   - AKS cluster recovery procedure
   - RTO and RPO targets
   - Runbook for common failure scenarios

10. OPERATIONS RUNBOOK
    - How to deploy a new release
    - How to roll back a deployment
    - How to scale the application
    - How to rotate secrets
    - How to access logs
    - How to run database migrations in production

Output the complete DIR as well-formatted markdown with working configuration files.
All infrastructure code must target Azure Government Cloud.
All CRITICAL security findings from the SRR must be addressed explicitly.
""",
        expected_output="A complete DevOps Implementation Report with working infrastructure code.",
        agent=de
    )

    crew = Crew(
        agents=[de],
        tasks=[dir_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🚀 DevOps Engineer implementing CI/CD and infrastructure...\n")
    result = crew.kickoff()

    os.makedirs("dev/build", exist_ok=True)
    dir_path = f"dev/build/{context['project_id']}_DIR.md"
    with open(dir_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 DevOps Implementation Report saved: {dir_path}")

    context["artifacts"].append({
        "name": "DevOps Implementation Report",
        "type": "DIR",
        "path": dir_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "DevOps Engineer"
    })
    context["status"] = "DEVOPS_COMPLETE"
    log_event(context, "DEVOPS_COMPLETE", dir_path)
    save_context(context)

    return context, dir_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    tip_path = tad_path = srr_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "TIP":
            tip_path = artifact["path"]
        if artifact.get("type") == "TAD":
            tad_path = artifact["path"]
        if artifact.get("type") == "SRR":
            srr_path = artifact["path"]

    if not all([tip_path, tad_path, srr_path]):
        print("Missing TIP, TAD, or SRR.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    context, dir_path = run_devops_implementation(context, tip_path, tad_path, srr_path)

    print(f"\n✅ DevOps implementation complete.")
    print(f"📄 DIR: {dir_path}")
    print(f"\nFirst 500 chars:")
    with open(dir_path) as f:
        print(f.read(500))
