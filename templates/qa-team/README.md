# qa-team — Template

> **This is a Protean Pursuits team template.**
> Instantiated by `scripts/refresh_templates.py` from `teams/qa-team/`.
> Last refreshed: 2026-03-23 21:18 UTC
> Replace all `PROJECT_NAME_PLACEHOLDER` and `PROJ-TEMPLATE` tokens.

---

# Protean Pursuits — QA Team

**Version:** 1.0 | **Scope:** Portfolio-wide (Dev, DS, Marketing, Legal, Design)

Nothing ships without QA sign-off. Verdicts: PASS | CONDITIONAL | FAIL | CRITICAL

## 8 Agents
| Agent | Covers |
|---|---|
| Test Case Development | Test suites from user stories and acceptance criteria |
| Functional / Integration | Feature correctness, API contracts, integration flows |
| Performance & Load | Response times, throughput, scalability under load |
| Security & Penetration | OWASP Top 10, API security, auth/authz, injection |
| Accessibility Auditing | WCAG 2.1 AA, Section 508, EN 301 549 |
| Data Quality & Pipeline | Pipeline completeness, model output validation, data freshness |
| Marketing & Content Compliance | Brand compliance, gambling ad rules, financial promotions |
| Legal Document Completeness | Placeholder resolution, clause coverage, document readiness |

## Run Modes
```bash
# Develop test cases
python flows/qa_flow.py --mode test_cases --target dev --name "Bet Tracker" --project-id PROJ-TEMPLATE

# Targeted audit
python flows/qa_flow.py --mode audit --agents security,performance --target dev --name "API Security Audit"

# Pre-launch sign-off (all applicable agents + certificate)
python flows/qa_flow.py --mode sign_off --target dev --name "PROJECT_NAME_PLACEHOLDER Phase 1A Launch"
```

FAIL/CRITICAL verdicts trigger immediate human notification. Nothing ships on a FAIL.
