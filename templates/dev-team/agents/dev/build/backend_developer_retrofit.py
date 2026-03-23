import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from agents.orchestrator.orchestrator import log_event, save_context

load_dotenv("config/.env")

def build_backend_developer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER2_MODEL", "ollama/qwen3-coder:30b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=1800
    )

    return Agent(
        role="Backend Developer",
        goal=(
            "Revise the existing Backend Implementation Report to replace all "
            "hardcoded Auth0 references with a generic OIDC/OAuth2 authentication "
            "interface that works with any compliant identity provider through "
            "environment variable configuration alone."
        ),
        backstory=(
            "You are a Senior Backend Engineer with 12 years of experience building "
            "authentication and authorization systems for government and healthcare "
            "applications. You have implemented identity solutions against Auth0, "
            "Keycloak, Okta, Microsoft Entra ID (Azure AD), AWS Cognito, Ping Identity, "
            "and custom OIDC providers. "
            "You know that for government systems, the identity provider is rarely "
            "the developer's choice — it is dictated by the agency's existing "
            "infrastructure. A VA system might use PIV card authentication via a "
            "government OIDC broker. An on-prem deployment might use Keycloak. "
            "A cloud deployment might use Auth0 or Entra ID. "
            "Your core principle: authentication code must be provider-agnostic. "
            "The application talks to a standard OIDC/OAuth2 interface. The provider "
            "is configured entirely through environment variables: "
            "- OIDC_ISSUER_URL: the provider's discovery endpoint base URL "
            "- OIDC_CLIENT_ID: the application's client ID "
            "- OIDC_CLIENT_SECRET: the application's client secret "
            "- OIDC_REDIRECT_URI: the callback URL after authentication "
            "- OIDC_SCOPES: space-separated scopes (e.g., 'openid profile email') "
            "- OIDC_AUDIENCE: optional audience claim for token validation "
            "The application uses the OIDC discovery document "
            "($OIDC_ISSUER_URL/.well-known/openid-configuration) to find all "
            "provider endpoints automatically — no hardcoded Auth0 domains, "
            "no hardcoded token URLs, no hardcoded JWKS endpoints. "
            "Provider-specific content (Auth0 management API calls, Keycloak "
            "admin REST API, Entra ID graph API) is labeled as "
            "'Provider Reference Implementation' and isolated in separate modules "
            "that are only loaded when the corresponding provider is configured. "
            "You produce clean, working Node.js/Express code that uses standard "
            "libraries (passport-openidconnect, openid-client, or jose) rather "
            "than provider-specific SDKs in the application core."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def run_bir_retrofit(context: dict, bir_path: str) -> dict:

    with open(bir_path) as f:
        bir_content = f.read()[:4000]

    backend = build_backend_developer()

    retrofit_task = Task(
        description=f"""
You are the Backend Developer. The existing Backend Implementation Report (BIR)
below has Auth0 hardcoded as the authentication provider throughout. Your job
is to produce a revised BIR where authentication is fully provider-agnostic.

--- EXISTING BIR (excerpt) ---
{bir_content}

Produce a complete REVISED Backend Implementation Report (BIR-R).

AUTHENTICATION RETROFIT RULES:
- Replace all Auth0-specific code with generic OIDC/OAuth2 interface
- Use openid-client (Node.js) as the OIDC library — it is spec-compliant
  and works with ANY OIDC provider (Auth0, Keycloak, Okta, Entra ID, etc.)
- All provider configuration comes from environment variables:
  * OIDC_ISSUER_URL — provider base URL (e.g., https://accounts.google.com)
  * OIDC_CLIENT_ID — application client ID
  * OIDC_CLIENT_SECRET — application client secret
  * OIDC_REDIRECT_URI — callback URL after login
  * OIDC_SCOPES — requested scopes (default: "openid profile email")
  * OIDC_AUDIENCE — optional audience for token validation
- Use OIDC discovery: Issuer.discover(process.env.OIDC_ISSUER_URL)
  This fetches the provider's .well-known/openid-configuration automatically
- JWT validation uses the provider's JWKS endpoint (from discovery)
  — no hardcoded public keys, no provider-specific JWT libraries
- RBAC roles come from the JWT claims — the claim name is configurable:
  * OIDC_ROLES_CLAIM env var (default: "roles")
  * Different providers put roles in different claims
- Mock/stub for local development: OIDC_MOCK=true bypasses real OIDC
  and uses a local mock identity server (useful for dev without internet)

DEPLOYMENT-AGNOSTIC RULES (same as DIR retrofit):
- No provider SDK imports in application core (no auth0, no @azure/msal-node)
- Provider-specific code isolated in adapters/ directory
- DEPLOY_TARGET and SECRETS_BACKEND env vars used consistently
- All secrets read from environment variables or /secrets/ mount path

SECTIONS REQUIRED IN THE REVISED BIR-R:

1. DATABASE SCHEMA
   - Keep existing schema from BIR
   - Apply DBA corrections (UUID for patient_id, TIMESTAMP WITH TIME ZONE,
     CHECK constraints) per the DBAR
   - No changes needed for auth-agnostic retrofit here

2. API ENDPOINTS
   - Keep all existing endpoints
   - Auth middleware now uses generic OIDC JWT validation
   - No Auth0-specific decorators or middleware

3. AUTHENTICATION & AUTHORIZATION (FULLY REVISED)
   - OIDC configuration module (reads from env vars, uses discovery)
   - JWT middleware using openid-client + jose for token validation
   - RBAC middleware using configurable roles claim
   - Login flow: redirect to OIDC provider, callback handler, session creation
   - Logout flow: clear session, redirect to OIDC end_session_endpoint
   - Local dev mock: OIDC_MOCK=true mode with mock token generation
   - Provider Reference Implementations (labeled clearly):
     * Auth0: OIDC_ISSUER_URL=https://your-tenant.auth0.com/
     * Keycloak: OIDC_ISSUER_URL=https://keycloak.example.com/realms/va
     * Entra ID: OIDC_ISSUER_URL=https://login.microsoftonline.com/{{tenant}}/v2.0
     * Okta: OIDC_ISSUER_URL=https://your-org.okta.com/oauth2/default
   - .env.example entries for auth configuration

4. DATA ACCESS LAYER
   - Keep existing Prisma/repository pattern
   - No changes needed for auth retrofit

5. BUSINESS LOGIC SERVICES
   - Keep existing services
   - Audit logging: replace Auth0 user ID with generic sub claim from JWT

6. ERROR HANDLING
   - Add OIDC-specific error handling:
     * Token expired (401)
     * Insufficient scope (403)
     * Provider unreachable (503 with retry guidance)

7. LOGGING
   - Keep existing Winston config
   - PHI-safe: log sub claim (not email or name) for audit trail
   - Never log JWT tokens or client secrets

8. UNIT TESTS
   - Mock OIDC provider for all auth tests
   - Test JWT validation with mock JWKS
   - Test RBAC with different roles claims
   - Test OIDC_MOCK=true mode

9. INTEGRATION TESTS
   - Test full login/callback flow against mock OIDC server
   - Test token refresh
   - Test logout and session clearing

10. ENVIRONMENT CONFIGURATION
    - Complete .env.example with all OIDC_ variables
    - Per-provider example configurations
    - OIDC_MOCK=true configuration for local development
    - Notes on required OIDC provider configuration
      (what redirect URIs to register, what scopes to enable)

Output the complete revised BIR-R as well-formatted markdown with working code.
Authentication must be fully provider-agnostic.
Provider-specific examples must be clearly labeled "Provider Reference Implementation".
All auth configuration must come from environment variables.
""",
        expected_output="A complete revised deployment-agnostic Backend Implementation Report.",
        agent=backend
    )

    crew = Crew(
        agents=[backend],
        tasks=[retrofit_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔧 Backend Developer retrofitting BIR for OIDC-agnostic auth...\n")
    result = crew.kickoff()

    bir_revised_path = bir_path.replace("_BIR.md", "_BIR_R.md")
    with open(bir_revised_path, "w") as f:
        f.write(str(result))

    print(f"\n💾 Revised BIR saved: {bir_revised_path}")

    context["artifacts"].append({
        "name": "Backend Implementation Report (Revised)",
        "type": "BIR_R",
        "path": bir_revised_path,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "Backend Developer (retrofit)"
    })
    context["status"] = "BIR_RETROFIT_COMPLETE"
    log_event(context, "BIR_RETROFIT_COMPLETE", bir_revised_path)
    save_context(context)

    return context, bir_revised_path


if __name__ == "__main__":
    import glob

    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    bir_path = None
    for artifact in context.get("artifacts", []):
        if artifact.get("type") == "BIR":
            bir_path = artifact["path"]

    if not bir_path:
        print("No BIR artifact found in context.")
        exit(1)

    print(f"📂 Loaded context: {logs[0]}")
    print(f"📄 Retrofitting: {bir_path}")
    context, bir_revised_path = run_bir_retrofit(context, bir_path)

    print(f"\n✅ BIR retrofit complete.")
    print(f"📄 Revised BIR: {bir_revised_path}")
    with open(bir_revised_path) as f:
        print(f.read(500))
