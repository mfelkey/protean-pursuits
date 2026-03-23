# legal-team — Template

> **This is a Protean Pursuits team template.**
> Instantiated by `scripts/refresh_templates.py` from `teams/legal-team/`.
> Last refreshed: 2026-03-23 21:18 UTC
> Replace all `PROJECT_NAME_PLACEHOLDER` and `PROJ-TEMPLATE` tokens.

---

# Protean Pursuits — Legal Team

**Version:** 1.0  
**Status:** Active  
**Professional posture:** In-house counsel equivalent  

> *Every output carries a risk level. HIGH and CRITICAL risk matters are escalated immediately. No document is used without human review.*

---

## Overview

The Legal Team operates as in-house counsel equivalent for Protean Pursuits LLC. It drafts legal documents, reviews external documents for risk, produces compliance analyses, and handles complex multi-specialist matters — across six industries and six jurisdiction groups.

**This team does not give legal advice from licensed attorneys.** All outputs carry the standard paraprofessional disclaimer. Documents flagged EXTERNAL COUNSEL REQUIRED or RECOMMENDED must be reviewed by qualified legal counsel before use or execution.

---

## The Team — 8 Specialist Agents

| Agent | Domain |
|---|---|
| **Contract Drafting** | NDA, MSA, SOW, SaaS agreements, API licences, affiliate agreements, DPAs, ToS |
| **Document Review & Risk** | External contract review, risk register, GO/PROCEED/DO NOT SIGN recommendation |
| **Privacy & Data Protection** | GDPR, UK GDPR, CCPA/CPRA, PDPA, Privacy Act AU, India DPDP, DPAs, DPIAs |
| **IP & Licensing** | Software copyright, data rights, AI output ownership, training data analysis, open source compliance |
| **Corporate & Entity** | Entity formation, operating agreements, governance, jurisdictional expansion |
| **Employment & Contractor** | Employment agreements, contractor/consulting agreements, worker classification, IP assignment |
| **Regulatory Compliance** | Gambling regulation, EU AI Act, HIPAA, financial services licensing, AI content law |
| **Litigation & Dispute Risk** | Litigation risk assessment, pre-litigation strategy, C&D letters, demand letters |

---

## Jurisdictions

| Code | Coverage |
|---|---|
| `US` | United States — federal + all 50 states |
| `EU` | European Union — GDPR, EU commercial law, AI Act |
| `UK` | United Kingdom — post-Brexit, English law, UK GDPR, UK Gambling Act |
| `AU` | Australia — federal + state/territory, Privacy Act, IGA |
| `IN` | India — Indian Contract Act, IT Act, DPDP Act 2023 |
| `SG` | Singapore — Companies Act, PDPA |
| `HK` | Hong Kong — common law, PDPO |

---

## Industries

| Code | Coverage |
|---|---|
| `SAAS` | SaaS / software — ToS, SLAs, acceptable use, IP ownership |
| `DATA` | Data products & analytics — licensing, resale, provenance, output ownership |
| `GAMBLING` | Sports betting / gambling — UK GC, US state regs, AU IGA |
| `FINANCIAL` | Financial services — SEC, FCA, ASIC, MAS |
| `HEALTHCARE` | Healthcare / HIPAA — PHI, BAAs, HITECH, state health privacy |
| `ECOMMERCE` | E-commerce / consumer — consumer protection, distance selling |
| `PUBLISHING_AI` | Publishing & AI — AI content ownership, training data, copyright, output liability |

---

## Risk Levels

Every output opens with a mandatory risk assessment block:

| Level | Meaning |
|---|---|
| `LOW` | Standard matter, low exposure. No external counsel needed. |
| `MEDIUM` | Moderate complexity or exposure. Internal review sufficient. |
| `HIGH` | Significant exposure. External counsel recommended. Human notified immediately. |
| `CRITICAL` | Immediate legal risk. Do NOT proceed without external counsel. Human notified immediately. |

---

## Run Modes

### Draft — produce a legal document
```bash
# NDA
python flows/legal_flow.py --mode draft --type NDA \
  --jurisdiction US --industry SAAS --name "Vendor NDA — Acme Corp"

# Privacy Policy (multi-jurisdiction)
python flows/legal_flow.py --mode draft --type PRIVACY_POLICY \
  --jurisdiction US,UK,EU,AU --industry GAMBLING,DATA \
  --name "PROJECT_NAME_PLACEHOLDER Privacy Policy" --project-id PROJ-TEMPLATE

# Terms of Service
python flows/legal_flow.py --mode draft --type TERMS_OF_SERVICE \
  --jurisdiction US,UK,EU,AU --industry GAMBLING,SAAS \
  --name "PROJECT_NAME_PLACEHOLDER Terms of Service" --project-id PROJ-TEMPLATE
```

Available document types: `NDA MSA SOW SAAS_AGREEMENT API_LICENCE DPA PRIVACY_POLICY COOKIE_POLICY TERMS_OF_SERVICE AFFILIATE CONTRACTOR EMPLOYMENT IP_ASSIGNMENT DATA_LICENCE OPERATING_AGREEMENT CEASE_DESIST DEMAND_LETTER`

### Review — review an external document
```bash
python flows/legal_flow.py --mode review \
  --file docs/vendor_contract.md \
  --jurisdiction UK --name "Vendor Agreement Review — DataCo"
```

### Compliance — regulatory compliance analysis
```bash
python flows/legal_flow.py --mode compliance \
  --jurisdiction US,UK,AU --industry GAMBLING,DATA,SAAS \
  --name "PROJECT_NAME_PLACEHOLDER Pre-Launch Compliance" \
  --project-id PROJ-TEMPLATE
```

### Matter — multi-agent complex matter
```bash
python flows/legal_flow.py --mode matter \
  --name "PROJECT_NAME_PLACEHOLDER Full Launch Legal Package" \
  --jurisdiction US,UK,EU,AU --industry GAMBLING,DATA,SAAS \
  --project-id PROJ-TEMPLATE \
  --agents privacy,compliance,ip,contract,litigation
```

---

## Human-in-the-Loop

**All outputs require human review before use.** HIGH and CRITICAL risk outputs trigger immediate SMS + email notification.

Approve via JSON response file:
```json
{ "decision": "APPROVED" }
```
or reject:
```json
{ "decision": "REJECTED", "reason": "Section 3 indemnity is too broad" }
```

---

## Repo Structure

```
legal-team/
├── agents/
│   ├── orchestrator/         orchestrator.py, base_agent.py
│   ├── contract_drafting/    contract_agent.py
│   ├── document_review/      review_agent.py
│   ├── privacy_data/         privacy_agent.py
│   ├── ip_licensing/         ip_agent.py
│   ├── corporate_entity/     corporate_agent.py
│   ├── employment_contractor/ employment_agent.py
│   ├── regulatory_compliance/ compliance_agent.py
│   └── litigation_dispute/   litigation_agent.py
├── flows/
│   └── legal_flow.py         all four run modes
├── config/
│   └── .env.template
├── docs/
│   └── templates/            blank document templates
├── logs/                     matter contexts + approval records
├── memory/                   cross-matter legal memory
└── output/
    ├── drafts/               drafted documents
    ├── reviews/              document review reports
    ├── compliance/           compliance analyses
    └── memos/                multi-agent matter outputs
```

---

## Standard Disclaimer

*All outputs from the Protean Pursuits Legal Team were produced by a paraprofessional legal team operating as in-house counsel equivalent. They do not constitute legal advice from a licensed attorney in any jurisdiction. Documents marked EXTERNAL COUNSEL REQUIRED or RECOMMENDED must be reviewed by qualified legal counsel before use or execution. Protean Pursuits LLC assumes no liability for reliance on these outputs without appropriate legal review.*
