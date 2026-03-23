import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_qa_lead() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="QA Lead",
        goal=(
            "Revise the existing Master Test Plan to be fully deployment-agnostic — "
            "no Azure Monitor, no AKS-specific commands, no cloud-specific staging "
            "environment assumptions. The revised MTP must work equally well for "
            "cloud and on-premises deployments."
        ),
        backstory=(
            "You are a Senior QA Lead with 12 years of experience testing government "
            "and healthcare applications across cloud and on-premises infrastructure. "
            "You have run test programs on Azure, AWS, and fully air-gapped on-prem "
            "Kubernetes clusters. "
            "Your core principle: test plans must be deployment-agnostic. This means: "
            "- Performance baselines reference application-level metrics (response time, "
            "  throughput, error rate) — not cloud-provider metrics (Azure Monitor, "
            "  CloudWatch, Stackdriver). "
            "- Infrastructure health checks use standard tools: kubectl, Prometheus "
            "  queries, pg_stat_activity — not cloud-specific CLIs or dashboards. "
            "- Environment specifications use generic terms: 'staging cluster', "
            "  'production cluster' — not 'AKS staging', 'EKS production'. "
            "- Test execution commands use Makefile targets — not cloud CLI commands. "
            "- DEPLOY_TARGET env var controls which environment-specific test tags "
            "  are active (@cloud-only vs @onprem-only). "
            "- Monitoring validation uses Prometheus + Grafana queries — not "
            "  Azure Monitor alert rules or CloudWatch metrics. "
            "Cloud-specific test content is labeled 'Cloud Reference' and paired "
            "with on-prem equivalents."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_mtp_retrofit(context: dict, mtp_path: str) -> dict:

    with open(mtp_path) as f:
        mtp_content = f.read()[:4000]

    qa_lead = build_qa_lead()

    retrofit_task = Task(
        description=f"""
You are the QA Lead. The existing Master Test Plan (MTP) below contains
Azure-specific assumptions. Your job is to produce a revised MTP that is
fully deployment-agnostic.

--- EXISTING MTP (excerpt) ---
{mtp_content}

Produce a complete REVISED Master Test Plan (MTP-R).

DEPLOYMENT-AGNOSTIC RULES:
- No Azure Monitor, CloudWatch, or provider-specific monitoring references
- No AKS-specific kubectl commands (kubectl top pod is AKS/metrics-server specific)
- No cloud-specific staging environment names or specs
- Environment specs use generic terms: 2 vCPU / 4GB RAM — not Azure VM SKUs
- Monitoring validation uses Prometheus queries and Grafana dashboards
- Test execution via Makefile targets (make test-smoke, make test-regression)
- DEPLOY_TARGET=cloud activates @cloud-only tests; DEPLOY_TARGET=onprem activates @onprem-only
- Performance thresholds are application-level, not infrastructure-level

SECTIONS REQUIRED:

1. TEST OBJECTIVES & SCOPE
   - Keep existing objectives
   - Add: tests are deployment-agnostic by design
   - DEPLOY_TARGET controls cloud-only vs onprem-only test execution

2. TEST ENVIRONMENTS
   - Local Development: docker-compose stack (any machine)
   - Staging: generic Kubernetes cluster spec (2 nodes, 2 vCPU/4GB each)
     * Cloud Reference: managed K8s service (AKS, EKS, GKE)
     * On-Prem Reference: bare Kubernetes (kubeadm, k3s, RKE2)
   - Production: generic Kubernetes cluster spec (3+ nodes, 4 vCPU/8GB each)
     * Same cloud/on-prem reference pattern
   - Environment variables required per environment (.env.staging, .env.production)
   - No Azure-specific VM SKUs or AKS node pool references

3. TEST TYPES & COVERAGE
   - Unit tests (Jest) — no environment dependency
   - API/Integration tests (Supertest) — no environment dependency
   - E2E tests (Playwright) — reads BASE_URL from env
   - Performance tests (k6) — reads BASE_URL and thresholds from env
   - Security tests (OWASP ZAP + Semgrep) — no environment dependency
   - Accessibility tests (axe-core) — no environment dependency

4. TEST EXECUTION
   - All commands via Makefile targets:
     * make test-unit
     * make test-api
     * make test-e2e
     * make test-smoke (DEPLOY_TARGET-aware)
     * make test-regression (DEPLOY_TARGET-aware)
     * make test-perf
     * make test-security
     * make test-all
   - DEPLOY_TARGET=cloud runs @cloud-only tests, skips @onprem-only
   - DEPLOY_TARGET=onprem runs @onprem-only tests, skips @cloud-only
   - CI/CD: pipeline calls make test-all — no cloud CLI

5. PERFORMANCE TEST PLAN
   - Baselines: application-level metrics only
     * API response time p95 < 500ms (dashboard load)
     * API response time p95 < 1000ms (filtered queries)
     * Error rate < 1% under 100 concurrent users
     * CSV export (10k rows) < 30s
   - Monitoring during perf tests: Prometheus queries
     * rate(http_requests_total[5m]) — request rate
     * histogram_quantile(0.95, http_request_duration_seconds_bucket) — p95
     * pg_stat_activity — DB connection pool
   - NO Azure Monitor metrics, NO kubectl top pod
   - Cloud Reference: same Prometheus queries work on AKS
   - On-Prem Reference: same Prometheus queries work on bare K8s

6. SECURITY TEST PLAN
   - OWASP ZAP dynamic scan against BASE_URL (deployment-agnostic)
   - Semgrep static analysis on codebase
   - RBAC tests: verify role enforcement via API calls
   - OIDC auth tests: verify token validation (OIDC_MOCK=false for security tests)
   - No cloud-specific security tooling required

7. MONITORING VALIDATION TESTS
   - Verify Prometheus is scraping application metrics
   - Verify Grafana dashboards load and display data
   - Verify AlertManager fires on threshold breaches
   - Verify ALERT_WEBHOOK_URL receives notifications
   - Test commands use kubectl and Prometheus HTTP API — not Azure Monitor
   - Cloud Reference: same tests work on AKS with kube-prometheus-stack
   - On-Prem Reference: same tests work on bare K8s with kube-prometheus-stack

8. TEST DATA MANAGEMENT
   - Synthetic data via faker seed scripts (no real PHI)
   - Seed datasets: 1k, 5k, 10k rows
   - Seed command: make seed DATA_VOLUME=5000
   - Data cleanup: make seed-clean
   - No cloud storage dependency for test data

9. DEFECT MANAGEMENT
   - Severity definitions (Critical, High, Medium, Low)
   - Acceptance criteria per severity
   - Tracking via GitHub Issues (deployment-agnostic)

10. EXIT CRITERIA
    - Unit test coverage >= 90%
    - All @smoke tests passing in both DEPLOY_TARGET modes
    - No Critical or High defects open
    - Performance baselines met
    - Zero accessibility violations (axe-core)
    - Security scan: no High or Critical findings

Output the complete revised MTP-R as well-formatted markdown.
Every section must be deployment-agnostic.
Cloud-specific content must be clearly labeled "Cloud Reference".
On-prem equivalents must be provided alongside every cloud-specific section.
""",
        expected_output="A complete revised deployment-agnostic Master Test Plan.",
        agent=qa_lead
    )

    crew = Crew(
        agents=[qa_lead],
        tasks=[retrofit_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔧 QA Lead retrofitting MTP for deployment-agnostic compliance...\n")
    result = crew.kickoff()

    mtp_revised_path = mtp_path.replace("_MTP.md", "_MTP_R.md")
    with open(mtp_revised_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Revised MTP saved: {mtp_revised_path}")

    context["artifacts"].append({
        "name": "Master Test Plan (Revised)",
        "type": "MTP_R",
        "path": mtp_revised_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "QA Lead (retrofit)"
    })
    context["status"] = "MTP_RETROFIT_COMPLETE"
    log_event(context, "MTP_RETROFIT_COMPLETE", mtp_revised_path)
    save_context(context)

    return context, mtp_revised_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    mtp_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "MTP":
            mtp_path = artifact["path"]

    if not mtp_path:
        print("No MTP artifact found in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Retrofitting: {mtp_path}")
    context, mtp_revised_path = run_mtp_retrofit(context, mtp_path)

    print(f"\n✅ MTP retrofit complete.")
    print(f"📄 Revised MTP: {mtp_revised_path}")
    with open(mtp_revised_path) as f:
        print(f.read(500))
