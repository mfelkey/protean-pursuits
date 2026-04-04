"""
Protean Pursuits — Mission Control
====================================
Flask backend for the PP vibe-coder dashboard.

Covers all 8 teams + Finance Group + SME Group.
Routes agent execution through pp_flow.py (team mode or agent direct).

Phase 1: Project viewer, pipeline reference, command generation
Phase 2: Live agent execution via pp_flow.py subprocess (enabled)

Run:
    cd ~/projects/protean-pursuits
    python dev-team-gui/app.py
    # or:
    FLASK_ENV=development python dev-team-gui/app.py

Open: http://localhost:5000
"""

import glob
import hashlib
import json
import os
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

PP_ROOT    = os.environ.get("PP_ROOT",    os.path.expanduser("~/projects/protean-pursuits"))
LOGS_DIR   = os.environ.get("PP_LOGS",   os.path.join(PP_ROOT, "logs"))
OUTPUT_DIR = os.environ.get("PP_OUTPUT", os.path.join(PP_ROOT, "output"))

PP_FLOW    = os.path.join(PP_ROOT, "flows", "pp_flow.py")
PYTHON     = os.environ.get("PP_PYTHON", "python3.11")

# In-memory run log (process_id → status dict)
_run_log: dict = {}
_run_lock = threading.Lock()

# ── PP Flow pipeline definition ────────────────────────────────────────────────
# Source of truth for the UI. Each team has:
#   - modes:  list of {id, name, phase, produces, checkpoint, icon, description}
#   - agents: list of {id, name, tier, produces, description, file}

TEAMS = {
    "dev": {
        "label":   "Dev Team",
        "icon":    "⚙️",
        "color":   "#4d7fff",
        "modes": [
            {"id": "plan",    "name": "Plan",    "phase": "plan",    "produces": "PRD+TAD+SRR+UXD", "checkpoint": True,  "icon": "📋", "description": "Full planning pipeline — PM → BA → Scrum → Architect → Security → UX → Content Guide"},
            {"id": "build",   "name": "Build",   "phase": "build",   "produces": "TIP+BIR+FIR+DBAR+DIR", "checkpoint": True, "icon": "🔨", "description": "Full build pipeline — Senior Dev → Backend → Frontend → DBA → DevOps. Requires TAD in context."},
            {"id": "quality", "name": "Quality", "phase": "quality", "produces": "MTP+TAR", "checkpoint": True,  "icon": "🧪", "description": "QA phase — QA Lead → Test Automation Engineer"},
            {"id": "finance", "name": "Finance", "phase": "finance", "produces": "FSP",     "checkpoint": True,  "icon": "💰", "description": "Finance Group sub-crew — full FSP with CEA, ROI, ICM, BPS, PRI, FSR, SCF"},
            {"id": "mobile",  "name": "Mobile",  "phase": "mobile",  "produces": "MUXD+IIR+AIR+RNAD+MDIR", "checkpoint": True, "icon": "📱", "description": "Mobile pipeline — Mobile UX → iOS → Android → RN → Mobile DevOps → Mobile QA. Requires UXD in context."},
            {"id": "full",    "name": "Full",    "phase": "full",    "produces": "All",    "checkpoint": True,  "icon": "🚀", "description": "Complete pipeline: plan → finance → build → quality in sequence"},
        ],
        "agents": [
            {"id": "product_manager",       "name": "Product Manager",        "tier": "T1", "produces": "PRD",          "file": "agents/dev/strategy/product_manager.py",           "description": "User stories, acceptance criteria, scope boundaries"},
            {"id": "business_analyst",      "name": "Business Analyst",       "tier": "T1", "produces": "BAD",          "file": "agents/dev/strategy/business_analyst.py",          "description": "Stakeholder map, process flows, data dictionaries"},
            {"id": "scrum_master",          "name": "Scrum Master",           "tier": "T1", "produces": "Sprint Plan",  "file": "agents/dev/strategy/scrum_master.py",              "description": "Prioritized backlog, story points, sprint sequencing"},
            {"id": "technical_architect",   "name": "Technical Architect",    "tier": "T1", "produces": "TAD",          "file": "agents/dev/strategy/technical_architect.py",       "description": "System design, tech stack, data flows, deployment model"},
            {"id": "security_reviewer",     "name": "Security Reviewer",      "tier": "T1", "produces": "SRR 🟢/🟡/🔴","file": "agents/dev/strategy/security_reviewer.py",         "description": "Security audit — RED rating blocks the pipeline"},
            {"id": "ux_designer",           "name": "UX/UI Designer",         "tier": "T1", "produces": "UXD",          "file": "agents/dev/strategy/ux_designer.py",               "description": "Every screen, interaction, label, and error message"},
            {"id": "ux_content_guide",      "name": "UX Content Guide",       "tier": "T1", "produces": "UI Content Guide","file": "agents/dev/strategy/ux_content_guide.py",      "description": "Definitive guide for every label, button, tooltip, error"},
            {"id": "senior_developer",      "name": "Senior Developer",       "tier": "T2", "produces": "TIP",          "file": "agents/dev/build/senior_developer.py",             "description": "Technical implementation plan, project structure, coding standards"},
            {"id": "backend_developer",     "name": "Backend Developer",      "tier": "T2", "produces": "BIR",          "file": "agents/dev/build/backend_developer.py",            "description": "Server-side implementation — APIs, auth, business logic"},
            {"id": "frontend_developer",    "name": "Frontend Developer",     "tier": "T2", "produces": "FIR",          "file": "agents/dev/build/frontend_developer.py",           "description": "Client-side implementation — pages, components, state"},
            {"id": "dba",                   "name": "Database Administrator", "tier": "T2", "produces": "DBAR",         "file": "agents/dev/build/database_admin.py",               "description": "Schema, queries, indexes, migrations, backups"},
            {"id": "devops_engineer",       "name": "DevOps Engineer",        "tier": "T2", "produces": "DIR",          "file": "agents/dev/build/devops_engineer.py",              "description": "CI/CD pipelines, infrastructure-as-code, secrets management"},
            {"id": "qa_lead",               "name": "QA Lead",                "tier": "T1", "produces": "MTP",          "file": "agents/dev/quality/qa_lead.py",                    "description": "Master test plan — what to test, how, and what done means"},
            {"id": "test_automation_engineer","name": "Test Automation Engineer","tier": "T2","produces": "TAR",         "file": "agents/dev/quality/test_automation_engineer.py",   "description": "Runnable test suite — Jest, Playwright, axe-core, k6"},
            {"id": "devex_writer",          "name": "DevEx Writer",           "tier": "T1", "produces": "API Docs",     "file": "agents/dev/docs/devex_writer.py",                  "description": "API docs, README, developer guides, onboarding content"},
            {"id": "technical_writer",      "name": "Technical Writer",       "tier": "T1", "produces": "User Guides",  "file": "agents/dev/docs/technical_writer.py",              "description": "User guides, admin guides, runbooks, release notes, KB articles"},
        ],
    },
    "ds": {
        "label":   "DS Team",
        "icon":    "🔬",
        "color":   "#8b5cf6",
        "modes": [
            {"id": "brief",      "name": "Brief",      "phase": "brief",      "produces": "Brief",     "checkpoint": False, "icon": "📝", "description": "DS Orchestrator — on-demand scoping or quick analysis"},
            {"id": "evaluation", "name": "Evaluation", "phase": "evaluation", "produces": "GO/NO-GO",  "checkpoint": False, "icon": "🔍", "description": "Data Evaluator → Reporting Analyst → DS Orchestrator — scored tool/source comparison"},
            {"id": "analysis",   "name": "Analysis",   "phase": "analysis",   "produces": "Report",    "checkpoint": False, "icon": "📊", "description": "Data Framer → EDA Analyst → Statistical Analyst → Reporting Analyst → DS Orchestrator"},
            {"id": "model",      "name": "Model",      "phase": "model",      "produces": "Model Plan","checkpoint": False, "icon": "🤖", "description": "Data Framer → EDA Analyst → ML Engineer → Reporting Analyst → DS Orchestrator"},
            {"id": "pipeline",   "name": "Pipeline",   "phase": "pipeline",   "produces": "Pipeline Design","checkpoint": False, "icon": "🔄", "description": "Data Framer → Pipeline Engineer → ML Engineer → Reporting Analyst → DS Orchestrator"},
        ],
        "agents": [
            {"id": "ds_orchestrator",    "name": "DS Orchestrator",    "tier": "T1", "produces": "Synthesis",       "file": "agents/ds/ds_orchestrator.py",    "description": "Scoping, crew sequencing, synthesis, authorized SME caller"},
            {"id": "data_evaluator",     "name": "Data Evaluator",     "tier": "T1", "produces": "GO/NO-GO",        "file": "agents/ds/data_evaluator.py",     "description": "Data source / API / tool evaluation with scored comparison matrix"},
            {"id": "data_framer",        "name": "Data Framer",        "tier": "T1", "produces": "Problem Frame",   "file": "agents/ds/data_framer.py",        "description": "Problem framing, complexity classification, feature requirements"},
            {"id": "eda_analyst",        "name": "EDA Analyst",        "tier": "T1", "produces": "EDA Report",      "file": "agents/ds/eda_analyst.py",        "description": "Distributions, data quality flags, feature signal assessment"},
            {"id": "statistical_analyst","name": "Statistical Analyst","tier": "T1", "produces": "Stats Report",    "file": "agents/ds/statistical_analyst.py","description": "Hypothesis tests, credible intervals, uncertainty quantification"},
            {"id": "ml_engineer",        "name": "ML Engineer",        "tier": "T1", "produces": "Model Dev Plan",  "file": "agents/ds/ml_engineer.py",        "description": "Algorithm selection, feature engineering, training strategy, eval framework"},
            {"id": "pipeline_engineer",  "name": "Pipeline Engineer",  "tier": "T1", "produces": "Pipeline Design", "file": "agents/ds/pipeline_engineer.py",  "description": "ETL architecture, orchestration, error handling, observability"},
            {"id": "reporting_analyst",  "name": "Reporting Analyst",  "tier": "T1", "produces": "Final Report",    "file": "agents/ds/reporting_analyst.py",  "description": "Six-section final reports — Executive Summary through PRD Impact"},
        ],
    },
    "design": {
        "label":   "Design Team",
        "icon":    "🎨",
        "color":   "#ec4899",
        "modes": [
            {"id": "research",     "name": "Research",     "phase": "research",     "produces": "User Research",    "checkpoint": True, "icon": "🔍", "description": "UX Researcher — user research report, journey maps"},
            {"id": "wireframe",    "name": "Wireframe",    "phase": "wireframe",    "produces": "Wireframes",       "checkpoint": True, "icon": "✏️", "description": "UX Researcher → Wireframing Specialist"},
            {"id": "visual",       "name": "Visual",       "phase": "visual",       "produces": "UI + Design System","checkpoint": True,"icon": "🖼️","description": "UI Designer → Brand Identity → Design System Architect"},
            {"id": "motion",       "name": "Motion",       "phase": "motion",       "produces": "Motion Spec",      "checkpoint": True, "icon": "🎬", "description": "Motion & Animation Designer — motion spec, animation briefs"},
            {"id": "accessibility","name": "Accessibility","phase": "accessibility","produces": "A11y Audit",       "checkpoint": True, "icon": "♿", "description": "Accessibility Specialist → Usability Analyst — WCAG 2.1 AA"},
            {"id": "full",         "name": "Full",         "phase": "full",         "produces": "Design Package",   "checkpoint": True, "icon": "📦", "description": "All design agents in sequence. DESIGN_REVIEW gate on every mode."},
        ],
        "agents": [
            {"id": "ux_researcher",           "name": "UX Researcher",           "tier": "T1", "produces": "Research Report",  "file": "agents/ux_research/ux_research_agent.py",       "description": "User research, journey maps"},
            {"id": "wireframing_specialist",  "name": "Wireframing Specialist",  "tier": "T1", "produces": "Wireframes",       "file": "agents/wireframing/wireframing_agent.py",       "description": "Lo-fi wireframes, interaction flows"},
            {"id": "ui_designer",             "name": "UI Designer",             "tier": "T1", "produces": "UI Designs",       "file": "agents/ui_design/ui_design_agent.py",           "description": "High-fidelity UI designs"},
            {"id": "brand_identity_specialist","name": "Brand Identity",         "tier": "T1", "produces": "Brand Guide",      "file": "agents/brand_identity/brand_identity_agent.py", "description": "Brand guide, visual language"},
            {"id": "design_system_architect", "name": "Design System Architect", "tier": "T1", "produces": "Design System",    "file": "agents/design_system/design_system_agent.py",   "description": "Component library, design tokens"},
            {"id": "motion_designer",         "name": "Motion Designer",         "tier": "T1", "produces": "Motion Spec",      "file": "agents/motion_animation/motion_agent.py",       "description": "Motion spec, animation briefs"},
            {"id": "accessibility_specialist","name": "Accessibility Specialist","tier": "T1", "produces": "A11y Audit",       "file": "agents/accessibility/accessibility_agent.py",   "description": "WCAG 2.1 AA audit"},
            {"id": "usability_analyst",       "name": "Usability Analyst",       "tier": "T1", "produces": "Usability Report", "file": "agents/usability/usability_agent.py",           "description": "Usability report, recommendations"},
        ],
    },
    "legal": {
        "label":   "Legal Team",
        "icon":    "⚖️",
        "color":   "#f59e0b",
        "modes": [
            {"id": "contract",   "name": "Contract",   "phase": "contract",   "produces": "Draft Contract", "checkpoint": True, "icon": "📄", "description": "Contract Drafter — agreements, NDAs, service contracts"},
            {"id": "review",     "name": "Review",     "phase": "review",     "produces": "Redline + Risk Memo", "checkpoint": True, "icon": "🔍", "description": "Document Reviewer — redlined documents, risk memos"},
            {"id": "ip",         "name": "IP",         "phase": "ip",         "produces": "IP Assessment",  "checkpoint": True, "icon": "💡", "description": "IP & Licensing Specialist — IP assessment, licensing framework"},
            {"id": "privacy",    "name": "Privacy",    "phase": "privacy",    "produces": "Privacy Analysis","checkpoint": True, "icon": "🔒", "description": "Privacy & Data Counsel — GDPR, CCPA, privacy impact assessment"},
            {"id": "regulatory", "name": "Regulatory", "phase": "regulatory", "produces": "Compliance Gap", "checkpoint": True, "icon": "📋", "description": "Regulatory Compliance Specialist — compliance gap report"},
            {"id": "employment", "name": "Employment", "phase": "employment", "produces": "Employment Docs","checkpoint": True, "icon": "👥", "description": "Employment & Contractor Counsel — agreements, contractor frameworks"},
            {"id": "corporate",  "name": "Corporate",  "phase": "corporate",  "produces": "Entity Rec",    "checkpoint": True, "icon": "🏢", "description": "Corporate Entity Specialist — entity structure recommendation"},
            {"id": "dispute",    "name": "Dispute",    "phase": "dispute",    "produces": "Strategy Memo", "checkpoint": True, "icon": "⚡", "description": "Litigation & Dispute Specialist — dispute assessment, strategy memo"},
            {"id": "full",       "name": "Full",       "phase": "full",       "produces": "Legal Package", "checkpoint": True, "icon": "📦", "description": "All legal agents in sequence. LEGAL_REVIEW gate on every mode."},
        ],
        "agents": [
            {"id": "contract_drafter",               "name": "Contract Drafter",             "tier": "T1", "produces": "Draft Contract",     "file": "agents/contract_drafting/contract_agent.py",           "description": "Agreements, NDAs, service contracts"},
            {"id": "document_reviewer",              "name": "Document Reviewer",            "tier": "T1", "produces": "Redline + Risk Memo", "file": "agents/document_review/review_agent.py",               "description": "Redlined documents, risk memos"},
            {"id": "corporate_entity_specialist",    "name": "Corporate Entity",             "tier": "T1", "produces": "Entity Rec",          "file": "agents/corporate_entity/corporate_agent.py",           "description": "Entity structure, governance"},
            {"id": "ip_licensing_specialist",        "name": "IP & Licensing",               "tier": "T1", "produces": "IP Assessment",       "file": "agents/ip_licensing/ip_agent.py",                      "description": "IP assessment, licensing framework"},
            {"id": "privacy_data_counsel",           "name": "Privacy & Data Counsel",       "tier": "T1", "produces": "Privacy Analysis",    "file": "agents/privacy_data/privacy_agent.py",                 "description": "GDPR, CCPA, privacy impact assessments"},
            {"id": "regulatory_compliance_specialist","name": "Regulatory Compliance",       "tier": "T1", "produces": "Compliance Gap",      "file": "agents/regulatory_compliance/compliance_agent.py",     "description": "Compliance gap reports"},
            {"id": "employment_contractor_counsel",  "name": "Employment & Contractor",      "tier": "T1", "produces": "Employment Docs",     "file": "agents/employment_contractor/employment_agent.py",     "description": "Employment agreements, contractor frameworks"},
            {"id": "litigation_dispute_specialist",  "name": "Litigation & Dispute",         "tier": "T1", "produces": "Strategy Memo",       "file": "agents/litigation_dispute/litigation_agent.py",        "description": "Dispute assessment, strategy memos"},
        ],
    },
    "marketing": {
        "label":   "Marketing Team",
        "icon":    "📣",
        "color":   "#10b981",
        "modes": [
            {"id": "brief",     "name": "Brief",     "phase": "brief",     "produces": "Campaign Brief", "checkpoint": False, "icon": "📋", "description": "Marketing Orchestrator — campaign brief, channel plan"},
            {"id": "copy",      "name": "Copy",      "phase": "copy",      "produces": "Copy Package",   "checkpoint": False, "icon": "✍️", "description": "Copywriter — landing pages, ads, app store listings, push copy"},
            {"id": "email",     "name": "Email",     "phase": "email",     "produces": "Email Sequences","checkpoint": True,  "icon": "📧", "description": "Email Specialist — sequences, drip campaigns, transactional templates. EMAIL gate."},
            {"id": "social",    "name": "Social",    "phase": "social",    "produces": "Post Drafts",    "checkpoint": True,  "icon": "📱", "description": "Social Media Specialist — post drafts, visual briefs. POST gate."},
            {"id": "video",     "name": "Video",     "phase": "video",     "produces": "Video Briefs",   "checkpoint": True,  "icon": "🎥", "description": "Video Producer — scripts, visual direction briefs, music briefs. VIDEO gate."},
            {"id": "analytics", "name": "Analytics", "phase": "analytics", "produces": "KPI Report",     "checkpoint": False, "icon": "📊", "description": "Marketing Analyst — channel performance reports, KPI dashboards"},
            {"id": "campaign",  "name": "Campaign",  "phase": "campaign",  "produces": "Campaign Package","checkpoint": True, "icon": "🚀", "description": "Full campaign — Orchestrator → all specialists. POST/EMAIL/VIDEO gates."},
        ],
        "agents": [
            {"id": "marketing_analyst",      "name": "Marketing Analyst",       "tier": "T1", "produces": "KPI Report",        "file": "agents/analyst/analyst_agent.py",          "description": "Channel performance, KPI dashboards"},
            {"id": "copywriter",             "name": "Copywriter",              "tier": "T1", "produces": "Copy Package",       "file": "agents/copywriter/copywriter_agent.py",    "description": "Landing pages, ads, app store listings, push copy, campaign messaging"},
            {"id": "email_specialist",       "name": "Email Specialist",        "tier": "T1", "produces": "Email Sequences",    "file": "agents/email/email_agent.py",              "description": "Sequences, drip campaigns, transactional templates"},
            {"id": "social_media_specialist","name": "Social Media Specialist", "tier": "T1", "produces": "Post Drafts",        "file": "agents/social/social_agent.py",            "description": "Post drafts, visual briefs for X, Instagram, TikTok, Discord"},
            {"id": "video_producer",         "name": "Video Producer",          "tier": "T1", "produces": "Video Briefs",       "file": "agents/video/video_agent.py",              "description": "Scripts, visual direction briefs, music briefs"},
        ],
    },
    "strategy": {
        "label":   "Strategy Team",
        "icon":    "♟️",
        "color":   "#06b6d4",
        "modes": [
            {"id": "positioning",    "name": "Positioning",    "phase": "positioning",    "produces": "Brand Positioning", "checkpoint": True, "icon": "🎯", "description": "Brand Positioning Strategist"},
            {"id": "business_model", "name": "Business Model", "phase": "business_model", "produces": "Business Model",    "checkpoint": True, "icon": "🏗️", "description": "Business Model Designer — canvas + narrative"},
            {"id": "competitive",    "name": "Competitive",    "phase": "competitive",    "produces": "Competitive Intel", "checkpoint": True, "icon": "🔍", "description": "Competitive Intelligence Analyst — landscape, positioning gaps"},
            {"id": "gtm",            "name": "GTM",            "phase": "gtm",            "produces": "GTM Plan",          "checkpoint": True, "icon": "🚀", "description": "GTM Strategist — plan, channel strategy, launch sequencing"},
            {"id": "okr",            "name": "OKR",            "phase": "okr",            "produces": "OKR Framework",     "checkpoint": True, "icon": "🎯", "description": "OKR Planner — framework, measurement plan"},
            {"id": "financial",      "name": "Financial",      "phase": "financial",      "produces": "Financial Strategy","checkpoint": True, "icon": "💰", "description": "Financial Strategist — financial strategy, funding roadmap"},
            {"id": "partnership",    "name": "Partnership",    "phase": "partnership",    "produces": "Partnership Framework","checkpoint": True,"icon": "🤝","description": "Partnership Strategist — framework, target list"},
            {"id": "product",        "name": "Product",        "phase": "product",        "produces": "Product Strategy",  "checkpoint": True, "icon": "📦", "description": "Product Strategist — product strategy, roadmap"},
            {"id": "risk",           "name": "Risk",           "phase": "risk",           "produces": "Risk Register",     "checkpoint": True, "icon": "⚠️", "description": "Risk & Scenario Planner — risk register, scenario analysis"},
            {"id": "talent",         "name": "Talent",         "phase": "talent",         "produces": "Org Design",        "checkpoint": True, "icon": "👥", "description": "Talent & Org Designer — org design, hiring plan"},
            {"id": "technology",     "name": "Technology",     "phase": "technology",     "produces": "Tech Strategy",     "checkpoint": True, "icon": "💻", "description": "Technology Strategist — build/buy/partner recommendation"},
            {"id": "full",           "name": "Full",           "phase": "full",           "produces": "Strategy Package",  "checkpoint": True, "icon": "📦", "description": "All strategy agents in sequence. STRATEGY/OKR_CYCLE/COMPETITIVE gates."},
        ],
        "agents": [
            {"id": "brand_positioning_strategist","name": "Brand Positioning",   "tier": "T1", "produces": "Brand Framework",    "file": "agents/brand_positioning/brand_agent.py",             "description": "Brand positioning framework"},
            {"id": "business_model_designer",    "name": "Business Model",       "tier": "T1", "produces": "Business Model",     "file": "agents/business_model/business_model_agent.py",       "description": "Business model canvas + narrative"},
            {"id": "competitive_intel_analyst",  "name": "Competitive Intel",    "tier": "T1", "produces": "Competitive Landscape","file": "agents/competitive_intel/competitive_intel_agent.py","description": "Competitive landscape, positioning gaps"},
            {"id": "financial_strategist",       "name": "Financial Strategist", "tier": "T1", "produces": "Financial Strategy", "file": "agents/financial_strategy/financial_strategy_agent.py","description": "Financial strategy, funding roadmap"},
            {"id": "gtm_strategist",             "name": "GTM Strategist",       "tier": "T1", "produces": "GTM Plan",           "file": "agents/gtm/gtm_agent.py",                             "description": "GTM plan, channel strategy, launch sequencing"},
            {"id": "okr_planner",                "name": "OKR Planner",          "tier": "T1", "produces": "OKR Framework",     "file": "agents/okr_planning/okr_agent.py",                    "description": "OKR framework, measurement plan"},
            {"id": "partnership_strategist",     "name": "Partnership",          "tier": "T1", "produces": "Partnership Plan",  "file": "agents/partnership/partnership_agent.py",             "description": "Partnership framework, target list"},
            {"id": "product_strategist",         "name": "Product Strategist",   "tier": "T1", "produces": "Product Strategy",  "file": "agents/product_strategy/product_strategy_agent.py",  "description": "Product strategy, roadmap"},
            {"id": "risk_scenario_planner",      "name": "Risk & Scenario",      "tier": "T1", "produces": "Risk Register",     "file": "agents/risk_scenario/risk_agent.py",                  "description": "Risk register, scenario analysis"},
            {"id": "talent_org_designer",        "name": "Talent & Org",         "tier": "T1", "produces": "Org Design",        "file": "agents/talent_org/talent_agent.py",                   "description": "Org design, hiring plan"},
            {"id": "technology_strategist",      "name": "Technology Strategist","tier": "T1", "produces": "Tech Strategy",     "file": "agents/technology_strategy/tech_strategy_agent.py",  "description": "Technology strategy, build/buy/partner rec"},
        ],
    },
    "qa": {
        "label":   "QA Team",
        "icon":    "✅",
        "color":   "#f97316",
        "modes": [
            {"id": "functional",       "name": "Functional",       "phase": "functional",       "produces": "Test Results",    "checkpoint": True, "icon": "🧪", "description": "Functional Testing Specialist — functional tests, bug report"},
            {"id": "performance",      "name": "Performance",      "phase": "performance",      "produces": "Benchmarks",      "checkpoint": True, "icon": "⚡", "description": "Performance Testing Specialist — benchmarks, bottleneck analysis"},
            {"id": "security",         "name": "Security",         "phase": "security",         "produces": "Security Report 🟢/🟡/🔴", "checkpoint": True, "icon": "🔒", "description": "Security Testing Specialist — OWASP audit"},
            {"id": "accessibility",    "name": "Accessibility",    "phase": "accessibility",    "produces": "A11y Audit",      "checkpoint": True, "icon": "♿", "description": "Accessibility Auditor — WCAG 2.1 AA"},
            {"id": "data_quality",     "name": "Data Quality",     "phase": "data_quality",     "produces": "Data Scorecard",  "checkpoint": True, "icon": "📊", "description": "Data Quality Analyst — data quality scorecard"},
            {"id": "legal_review",     "name": "Legal Review",     "phase": "legal_review",     "produces": "Legal Completeness","checkpoint": True,"icon": "⚖️", "description": "Legal Completeness Reviewer"},
            {"id": "marketing_review", "name": "Marketing Review", "phase": "marketing_review", "produces": "Marketing Compliance","checkpoint": True,"icon": "📣","description": "Marketing Compliance Reviewer"},
            {"id": "test_cases",       "name": "Test Cases",       "phase": "test_cases",       "produces": "Test Case Library","checkpoint": True, "icon": "📋", "description": "Test Case Developer — test case library"},
            {"id": "full",             "name": "Full Audit",       "phase": "full",             "produces": "Full QA Package", "checkpoint": True, "icon": "📦", "description": "All QA agents in sequence. QA_SIGN_OFF gate."},
        ],
        "agents": [
            {"id": "functional_testing_specialist",  "name": "Functional Testing",    "tier": "T1", "produces": "Test Results",        "file": "agents/functional_testing/functional_agent.py",           "description": "Functional test results, bug reports"},
            {"id": "performance_testing_specialist", "name": "Performance Testing",   "tier": "T1", "produces": "Benchmarks",          "file": "agents/performance_testing/performance_agent.py",         "description": "Performance benchmarks, bottleneck analysis"},
            {"id": "security_testing_specialist",    "name": "Security Testing",      "tier": "T1", "produces": "Security Report",     "file": "agents/security_testing/security_agent.py",               "description": "Security test report 🟢/🟡/🔴"},
            {"id": "accessibility_auditor",          "name": "Accessibility Auditor", "tier": "T1", "produces": "A11y Audit",          "file": "agents/accessibility_audit/accessibility_audit_agent.py", "description": "WCAG 2.1 AA audit"},
            {"id": "data_quality_analyst",           "name": "Data Quality Analyst",  "tier": "T1", "produces": "Data Scorecard",      "file": "agents/data_quality/data_quality_agent.py",               "description": "Data quality scorecard"},
            {"id": "legal_completeness_reviewer",    "name": "Legal Completeness",    "tier": "T1", "produces": "Legal Report",        "file": "agents/legal_completeness/legal_qa_agent.py",             "description": "Legal completeness report"},
            {"id": "marketing_compliance_reviewer",  "name": "Marketing Compliance",  "tier": "T1", "produces": "Compliance Report",   "file": "agents/marketing_compliance/marketing_qa_agent.py",       "description": "Marketing compliance report"},
            {"id": "test_case_developer",            "name": "Test Case Developer",   "tier": "T1", "produces": "Test Case Library",   "file": "agents/test_case_development/test_case_agent.py",         "description": "Test case library"},
        ],
    },
    "hr": {
        "label":   "HR Team",
        "icon":    "👥",
        "color":   "#a78bfa",
        "modes": [
            {"id": "RECRUIT",    "name": "Recruit",    "phase": "recruit",    "produces": "JD + Interview Guide", "checkpoint": True, "icon": "🔍", "description": "Recruiting Specialist — job descriptions, sourcing plan, interview guide"},
            {"id": "ONBOARD",    "name": "Onboard",    "phase": "onboard",    "produces": "Onboarding Plan",      "checkpoint": True, "icon": "🎉", "description": "Onboarding Specialist — onboarding plans, day-one checklists"},
            {"id": "REVIEW",     "name": "Review",     "phase": "review",     "produces": "Review Framework",     "checkpoint": True, "icon": "📋", "description": "Performance & Comp Specialist — review frameworks, comp analysis"},
            {"id": "POLICY",     "name": "Policy",     "phase": "policy",     "produces": "HR Policies",          "checkpoint": True, "icon": "📄", "description": "Policy & Compliance Specialist — HR policies, compliance audits"},
            {"id": "CULTURE",    "name": "Culture",    "phase": "culture",    "produces": "Engagement Plan",      "checkpoint": True, "icon": "❤️", "description": "Culture & Engagement Specialist — engagement surveys, culture programs"},
            {"id": "BENEFITS",   "name": "Benefits",   "phase": "benefits",   "produces": "Benefits Analysis",    "checkpoint": True, "icon": "💊", "description": "Benefits Specialist — benefits analysis, total compensation"},
            {"id": "FULL_CYCLE", "name": "Full Cycle", "phase": "full_cycle", "produces": "Full HR Package",      "checkpoint": True, "icon": "📦", "description": "Full HR pipeline. Humans-only model. HR action gate on every output."},
        ],
        "agents": [
            {"id": "recruiting_specialist",       "name": "Recruiting Specialist",        "tier": "T1", "produces": "JD + Sourcing Plan",  "file": "agents/hr/recruiting/recruiting_agent.py",               "description": "Job descriptions, sourcing plan, interview guide"},
            {"id": "onboarding_specialist",       "name": "Onboarding Specialist",        "tier": "T1", "produces": "Onboarding Plan",     "file": "agents/hr/onboarding/onboarding_agent.py",               "description": "Onboarding plans, day-one checklists"},
            {"id": "performance_comp_specialist", "name": "Performance & Comp",           "tier": "T1", "produces": "Review Framework",    "file": "agents/hr/performance_comp/performance_comp_agent.py",   "description": "Review framework, comp analysis"},
            {"id": "policy_compliance_specialist","name": "Policy & Compliance",          "tier": "T1", "produces": "HR Policies",         "file": "agents/hr/policy_compliance/policy_compliance_agent.py", "description": "HR policies, compliance audits"},
            {"id": "culture_engagement_specialist","name": "Culture & Engagement",        "tier": "T1", "produces": "Engagement Plan",     "file": "agents/hr/culture_engagement/culture_engagement_agent.py","description": "Engagement surveys, culture programs"},
            {"id": "benefits_specialist",         "name": "Benefits Specialist",          "tier": "T1", "produces": "Benefits Analysis",   "file": "agents/hr/benefits/benefits_agent.py",                   "description": "Benefits analysis, total compensation"},
        ],
    },
    "sme": {
        "label":   "SME Group",
        "icon":    "🎓",
        "color":   "#f59e0b",
        "modes": [
            {"id": "consult", "name": "Consult",  "phase": "consult", "produces": "Domain Assessment", "checkpoint": False, "icon": "🎓", "description": "Single SME direct — one domain expert answers the question. Requires --agent <sme_key>."},
            {"id": "crew",    "name": "Crew",     "phase": "crew",    "produces": "Domain Intelligence Brief", "checkpoint": True, "icon": "👥", "description": "Multi-SME synthesized — named experts collaborate. HITL gate fires on Domain Intelligence Brief."},
            {"id": "auto",    "name": "Auto",     "phase": "auto",    "produces": "Domain Intelligence Brief", "checkpoint": True, "icon": "🔍", "description": "Auto-detect experts from question keywords. SME Orchestrator selects and synthesizes. HITL gate fires."},
        ],
        "agents": [
            {"id": "sports_betting",            "name": "Sports Betting Expert",           "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/sports_betting_expert.py",              "description": "Cross-sport industry authority — all regulated markets worldwide"},
            {"id": "world_football",            "name": "World Football & Soccer",         "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/world_football_expert.py",              "description": "All global leagues, confederations, Asian handicap"},
            {"id": "nba_ncaa_basketball",       "name": "NBA & NCAA Basketball",           "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/nba_ncaa_basketball_expert.py",         "description": "NBA + March Madness"},
            {"id": "nfl_ncaa_football",         "name": "NFL & NCAA Football",             "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/nfl_ncaa_football_expert.py",           "description": "NFL + CFP, college football"},
            {"id": "mlb",                       "name": "MLB Expert",                      "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/mlb_expert.py",                        "description": "MLB + NPB + KBO + CPBL"},
            {"id": "nhl_ncaa_hockey",           "name": "NHL & NCAA Hockey",               "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/nhl_ncaa_hockey_expert.py",            "description": "NHL + NCAA + KHL + Euro leagues"},
            {"id": "mma",                       "name": "MMA Expert",                      "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/mma_expert.py",                        "description": "UFC + Bellator + ONE + Rizin"},
            {"id": "tennis",                    "name": "Tennis Expert",                   "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/tennis_expert.py",                     "description": "ATP + WTA + Challengers + ITF"},
            {"id": "world_rugby",               "name": "World Rugby Expert",              "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/world_rugby_expert.py",                "description": "Union + League — Six Nations, NRL, State of Origin"},
            {"id": "cricket",                   "name": "Cricket Expert",                  "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/cricket_expert.py",                    "description": "Test + ODI + T20 + IPL — all formats, all nations"},
            {"id": "wnba_ncaa_womens_basketball","name": "WNBA & NCAA Women's Basketball", "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/wnba_ncaa_womens_basketball_expert.py","description": "WNBA + NCAA women's"},
            {"id": "thoroughbred_horse_racing", "name": "Thoroughbred Horse Racing",       "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/thoroughbred_horse_racing_expert.py",  "description": "US + UK/IRE + AUS + HK + JPN + FR + DXB"},
            {"id": "harness_racing",            "name": "Harness Racing Expert",           "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/harness_racing_expert.py",             "description": "Standardbred worldwide — Hambletonian, V75, PMU"},
            {"id": "mens_boxing",               "name": "Men's Boxing Expert",             "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/mens_boxing_expert.py",                "description": "All four sanctioning bodies, all 17 weight classes"},
            {"id": "pga",                       "name": "PGA Tour Expert",                 "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/pga_expert.py",                        "description": "PGA Tour + DP World Tour + LIV + all majors + Ryder Cup"},
            {"id": "lpga",                      "name": "LPGA Tour Expert",                "tier": "T1", "produces": "Domain Assessment", "file": "agents/sme/lpga_expert.py",                       "description": "LPGA + JLPGA + KLPGA + women's majors + Solheim Cup"},
        ],
    },
    "video": {
        "label":   "Video Team",
        "icon":    "🎬",
        "color":   "#ef4444",
        "modes": [
            {"id": "BRIEF_ONLY",  "name": "Brief Only",  "phase": "brief",      "produces": "TRR+Script+VDB+AUB", "checkpoint": True, "icon": "📝", "description": "Tool Analyst → Script → Visual → Audio. No API calls. TOOL_SELECTION + SCRIPT_REVIEW gates."},
            {"id": "SHORT_FORM",  "name": "Short Form",  "phase": "short_form", "produces": "Social Video Package","checkpoint": True, "icon": "📱", "description": "Full pipeline for <60s social content (TikTok, Reels, Shorts). Three HITL gates."},
            {"id": "LONG_FORM",   "name": "Long Form",   "phase": "long_form",  "produces": "Long Video Package",  "checkpoint": True, "icon": "📺", "description": "Full pipeline for 2–10min content (YouTube, website). Three HITL gates."},
            {"id": "AVATAR",      "name": "Avatar",      "phase": "avatar",     "produces": "Avatar Package",      "checkpoint": True, "icon": "🤖", "description": "Avatar/spokesperson pipeline. Requires avatar_config in context. Three HITL gates."},
            {"id": "DEMO",        "name": "Demo",        "phase": "demo",       "produces": "Demo Package",        "checkpoint": True, "icon": "🖥️", "description": "Screen recording wrapper — Script + Audio + API + Compliance. SCRIPT_REVIEW + VIDEO_FINAL."},
            {"id": "EXPLAINER",   "name": "Explainer",   "phase": "explainer",  "produces": "Explainer Package",   "checkpoint": True, "icon": "💡", "description": "Animated explainer / motion graphics. Three HITL gates."},
            {"id": "VOICEOVER",   "name": "Voiceover",   "phase": "voiceover",  "produces": "Voiceover Package",   "checkpoint": True, "icon": "🎙️", "description": "Voiceover-only — no visual generation. SCRIPT_REVIEW + VIDEO_FINAL."},
            {"id": "FULL",        "name": "Full Campaign","phase": "full",      "produces": "Campaign Package",    "checkpoint": True, "icon": "📦", "description": "BRIEF_ONLY → SHORT_FORM → LONG_FORM → AVATAR in sequence."},
        ],
        "agents": [
            {"id": "script_writer",       "name": "Script Writer",        "tier": "T1", "produces": "Script Package",   "file": "agents/script/script_writer.py",               "description": "Scripts, voiceovers, on-screen copy, compliance checklist"},
            {"id": "visual_director",     "name": "Visual Director",      "tier": "T1", "produces": "Visual Direction Brief","file": "agents/visual/visual_director.py",          "description": "Shot types, motion direction, colour grading, AI prompt strings"},
            {"id": "audio_producer",      "name": "Audio Producer",       "tier": "T1", "produces": "Audio Brief",      "file": "agents/audio/audio_producer.py",               "description": "Music prompts, TTS direction, SFX cue sheet, mix guide"},
            {"id": "avatar_producer",     "name": "Avatar Producer",      "tier": "T1", "produces": "Avatar Brief",     "file": "agents/avatar/avatar_producer.py",             "description": "HeyGen/Synthesia execution params, dialogue segmentation"},
            {"id": "tool_analyst",        "name": "Tool Intelligence",    "tier": "T1", "produces": "Tool Recommendation","file": "agents/tool_intelligence/tool_analyst.py",   "description": "Scored tool rankings, API signatures, web search at runtime"},
            {"id": "compliance_reviewer", "name": "Compliance Reviewer",  "tier": "T1", "produces": "COR PASS/FAIL",    "file": "agents/compliance/compliance_reviewer.py",     "description": "PASS/CONDITIONAL/FAIL across brand, platform policy, legal, tech spec"},
            {"id": "api_engineer",        "name": "API Production Engineer","tier": "T2","produces": "Assembly Manifest","file": "agents/production/api_engineer.py",            "description": "Executes approved APIs, saves raw assets, produces assembly manifest"},
        ],
    },
}

# ── Checkpoint definitions ─────────────────────────────────────────────────────

CHECKPOINTS = [
    {"id": "CP-1",  "name": "Requirements Review", "team": "dev",      "check": "User stories right? Scope correct? Right things out of scope?"},
    {"id": "CP-2",  "name": "Architecture Review",  "team": "dev",      "check": "Tech stack makes sense? Achievable? Fits your infrastructure?"},
    {"id": "CP-3",  "name": "Security Gate",        "team": "dev",      "check": "Rating acceptable 🟢/🟡/🔴? RED must be resolved before build."},
    {"id": "CP-4",  "name": "UX Review",            "team": "dev",      "check": "UI make sense? Language clear? All screens covered?"},
    {"id": "CP-4.5","name": "Finance Gate",         "team": "dev",      "check": "Financials make sense? All 🟢/🟡/🔴 ratings reviewed? Open Questions addressed?"},
    {"id": "CP-5",  "name": "Build Complete",       "team": "dev",      "check": "Spot-check the code. Grep for TODO/placeholder. Does it look complete?"},
    {"id": "CP-6",  "name": "Release Gate",         "team": "dev",      "check": "Tests pass? No open critical issues? Confident this is done?"},
    {"id": "DESIGN","name": "Design Review",        "team": "design",   "check": "Design assets approved before handoff to Dev."},
    {"id": "LEGAL", "name": "Legal Review",         "team": "legal",    "check": "Legal deliverables approved before any action is taken."},
    {"id": "QA",    "name": "QA Sign-off",          "team": "qa",       "check": "Cross-team quality audit results reviewed and signed off."},
    {"id": "STRAT", "name": "Strategy Review",      "team": "strategy", "check": "Strategic outputs reviewed before execution."},
    {"id": "OKR",   "name": "OKR Cycle",            "team": "strategy", "check": "OKR framework approved before adoption."},
    {"id": "COMP",  "name": "Competitive Review",   "team": "strategy", "check": "Competitive brief reviewed before it informs decisions."},
    {"id": "POST",  "name": "Post Approval",        "team": "marketing","check": "Posts approved before scheduling or publishing."},
    {"id": "EMAIL", "name": "Email Approval",       "team": "marketing","check": "Email sends approved before execution."},
    {"id": "VIDEO_TOOL","name": "Tool Selection",   "team": "video",    "check": "Tool stack approved before any creative work begins."},
    {"id": "SCRIPT","name": "Script Review",        "team": "video",    "check": "Script approved before any API calls are made."},
    {"id": "VIDEO", "name": "Video Final",          "team": "video",    "check": "Full package approved before any publish action."},
    {"id": "HR",    "name": "HR Action Gate",       "team": "hr",       "check": "Human must approve — no exceptions, no automation bypass."},
    {"id": "MULTI_SME","name": "Multi-SME Gate",    "team": "sme",      "check": "Domain Intelligence Brief reviewed before it is acted on."},
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _find_projects():
    """Find all project context JSON files in logs/ and output/."""
    projects = []
    # logs/ — PROJ-*.json
    for f in glob.glob(os.path.join(LOGS_DIR, "PROJ-*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            projects.append({
                "id":             d.get("project_id", os.path.basename(f)),
                "title":          d.get("structured_spec", {}).get("title", "Untitled"),
                "status":         d.get("status", "UNKNOWN"),
                "classification": d.get("classification", "?"),
                "created_at":     d.get("created_at", ""),
                "artifact_count": len(d.get("artifacts", [])),
                "path": f,
                "source": "logs",
            })
        except Exception:
            continue
    # output/<project>/context.json
    for f in glob.glob(os.path.join(OUTPUT_DIR, "*/context.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            projects.append({
                "id":             d.get("project_id", os.path.basename(os.path.dirname(f))),
                "title":          d.get("structured_spec", {}).get("title", os.path.basename(os.path.dirname(f))),
                "status":         d.get("status", "ACTIVE"),
                "classification": d.get("classification", "?"),
                "created_at":     d.get("created_at", ""),
                "artifact_count": len(d.get("artifacts", [])),
                "path": f,
                "source": "output",
            })
        except Exception:
            continue
    projects.sort(key=lambda p: p["created_at"], reverse=True)
    return projects


def _load_project(project_id):
    for f in glob.glob(os.path.join(LOGS_DIR, f"*{project_id}*.json")):
        try:
            with open(f) as fh:
                return json.load(fh)
        except Exception:
            continue
    for f in glob.glob(os.path.join(OUTPUT_DIR, f"*{project_id}*/context.json")):
        try:
            with open(f) as fh:
                return json.load(fh)
        except Exception:
            continue
    return None


def _build_pp_flow_cmd(team: str, mode: str = None, agent: str = None,
                       task: str = "", project: str = None,
                       context_str: str = None) -> list:
    """Build the pp_flow.py subprocess command list."""
    cmd = [PYTHON, PP_FLOW, "--team", team]
    if mode:
        cmd += ["--mode", mode]
    elif agent:
        cmd += ["--agent", agent]
    cmd += ["--task", task or f"Run {team} {mode or agent}"]
    if project:
        cmd += ["--project", project, "--save"]
    elif context_str:
        cmd += ["--context", context_str[:2000]]
    return cmd


# ── Routes — Data ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/teams")
def api_teams():
    """Return all team definitions (modes + agents)."""
    return jsonify(TEAMS)


@app.route("/api/teams/<team_id>")
def api_team(team_id):
    t = TEAMS.get(team_id)
    if t:
        return jsonify(t)
    return jsonify({"error": "Team not found"}), 404


@app.route("/api/checkpoints")
def api_checkpoints():
    return jsonify(CHECKPOINTS)


@app.route("/api/projects")
def api_projects():
    return jsonify(_find_projects())


@app.route("/api/projects/<project_id>")
def api_project(project_id):
    d = _load_project(project_id)
    if d:
        return jsonify(d)
    return jsonify({"error": "Project not found"}), 404


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    """Create a new project context JSON."""
    data = request.json or {}
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400

    hash_input = f"{description}{datetime.now().isoformat()}"
    project_id = "PROJ-" + hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
    now = datetime.now().isoformat() + "Z"

    ctx = {
        "project_id": project_id,
        "created_at": now,
        "status": "INITIATED",
        "classification": "UNKNOWN",
        "original_request": description,
        "structured_spec": {
            "title": (data.get("title") or description[:80]),
            "description": description,
            "estimated_complexity": data.get("complexity", "MEDIUM"),
            "data_required": data.get("data_required", False),
            "primary_crew": "DEV",
            "deliverables": [],
            "success_criteria": [],
        },
        "assigned_crew": None,
        "artifacts": [],
        "checkpoints": [],
        "handoffs": [],
        "audit_log": [{"timestamp": now, "event": "PROJECT_CREATED",
                        "detail": "Created via PP Mission Control"}],
    }

    os.makedirs(LOGS_DIR, exist_ok=True)
    path = os.path.join(LOGS_DIR, f"{project_id}.json")
    with open(path, "w") as f:
        json.dump(ctx, f, indent=2)

    return jsonify({
        "status": "created",
        "project_id": project_id,
        "path": path,
        "message": f"Project {project_id} created.",
    }), 201


# ── Routes — Execution ─────────────────────────────────────────────────────────

@app.route("/api/run", methods=["POST"])
def api_run():
    """
    Execute via pp_flow.py.
    Body: {
      team:       str,
      mode:       str | null,   # mutually exclusive with agent
      agent:      str | null,
      task:       str,
      project:    str | null,
      context:    str | null,   # inline context
    }
    Returns immediately with a run_id. Poll /api/run/<run_id> for status.
    """
    data = request.json or {}
    team    = (data.get("team") or "").strip()
    mode    = (data.get("mode") or "").strip() or None
    agent   = (data.get("agent") or "").strip() or None
    task    = (data.get("task") or "").strip()
    project = (data.get("project") or "").strip() or None
    context_str = (data.get("context") or "").strip() or None

    if not team:
        return jsonify({"error": "team is required"}), 400
    if not mode and not agent:
        return jsonify({"error": "mode or agent is required"}), 400
    if team not in TEAMS:
        return jsonify({"error": f"Unknown team: {team}"}), 400

    cmd = _build_pp_flow_cmd(team, mode=mode, agent=agent,
                             task=task, project=project, context_str=context_str)

    run_id = "RUN-" + uuid.uuid4().hex[:8].upper()
    with _run_lock:
        _run_log[run_id] = {
            "run_id":   run_id,
            "status":   "running",
            "team":     team,
            "mode":     mode,
            "agent":    agent,
            "task":     task,
            "project":  project,
            "cmd":      " ".join(cmd),
            "started_at": datetime.now().isoformat(),
            "finished_at": None,
            "returncode": None,
            "stdout":   "",
            "stderr":   "",
        }

    def _run():
        try:
            proc = subprocess.run(
                cmd,
                cwd=PP_ROOT,
                capture_output=True,
                text=True,
                timeout=7200,  # 2 hours
            )
            with _run_lock:
                _run_log[run_id].update({
                    "status":      "completed" if proc.returncode == 0 else "failed",
                    "returncode":  proc.returncode,
                    "stdout":      proc.stdout[-8000:],
                    "stderr":      proc.stderr[-2000:],
                    "finished_at": datetime.now().isoformat(),
                })
        except subprocess.TimeoutExpired:
            with _run_lock:
                _run_log[run_id].update({
                    "status":      "timeout",
                    "finished_at": datetime.now().isoformat(),
                })
        except Exception as e:
            with _run_lock:
                _run_log[run_id].update({
                    "status":      "error",
                    "stderr":      str(e),
                    "finished_at": datetime.now().isoformat(),
                })

    threading.Thread(target=_run, daemon=True).start()

    return jsonify({
        "run_id":  run_id,
        "status":  "running",
        "cmd":     " ".join(cmd),
        "message": f"Run {run_id} started. Poll /api/run/{run_id} for status.",
    }), 202


@app.route("/api/run/<run_id>")
def api_run_status(run_id):
    """Poll for run status."""
    with _run_lock:
        entry = _run_log.get(run_id)
    if not entry:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(entry)


@app.route("/api/runs")
def api_runs():
    """List recent runs (most recent first, max 50)."""
    with _run_lock:
        runs = list(_run_log.values())
    runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)
    return jsonify(runs[:50])


@app.route("/api/checkpoint/<project_id>", methods=["POST"])
def api_checkpoint(project_id):
    """
    Write checkpoint approval to logs/approvals/<approval_id>.response.json.
    Body: { action: "APPROVE"|"REJECT", reason: str, approval_id: str }
    """
    data   = request.json or {}
    action = (data.get("action") or "").upper()
    reason = data.get("reason", "")
    appr_id = data.get("approval_id", "")

    if action not in ("APPROVE", "REJECT"):
        return jsonify({"error": "action must be APPROVE or REJECT"}), 400

    approvals_dir = os.path.join(PP_ROOT, "logs", "approvals")
    os.makedirs(approvals_dir, exist_ok=True)

    # If a specific approval_id was provided, write the response file
    if appr_id:
        resp_path = os.path.join(approvals_dir, f"{appr_id}.response.json")
        with open(resp_path, "w") as f:
            json.dump({"decision": action, "reason": reason,
                       "timestamp": datetime.now().isoformat()}, f)
        return jsonify({
            "status": "written",
            "decision": action,
            "path": resp_path,
            "message": f"Checkpoint {action} written to {resp_path}",
        })

    # No approval_id — scan for pending approvals for this project
    pending = []
    for req_file in glob.glob(os.path.join(approvals_dir, "APPROVAL-*.json")):
        resp_file = req_file.replace(".json", ".response.json")
        if os.path.exists(resp_file):
            continue
        try:
            with open(req_file) as f:
                req = json.load(f)
            if project_id in req.get("artifact_path", "") or not project_id:
                pending.append(req)
        except Exception:
            continue

    if not pending:
        return jsonify({"status": "no_pending",
                        "message": "No pending approvals found for this project."})

    # Write response to most recent pending approval
    latest = sorted(pending, key=lambda r: r.get("requested_at", ""))[-1]
    resp_path = os.path.join(approvals_dir, f"{latest['approval_id']}.response.json")
    with open(resp_path, "w") as f:
        json.dump({"decision": action, "reason": reason,
                   "timestamp": datetime.now().isoformat()}, f)

    return jsonify({
        "status":   "written",
        "decision": action,
        "approval_id": latest["approval_id"],
        "gate_type": latest.get("gate_type", ""),
        "path": resp_path,
        "message": f"Checkpoint {action} written for {latest['approval_id']}",
    })


@app.route("/api/approvals/pending")
def api_pending_approvals():
    """Return all pending approval requests (no response file yet)."""
    approvals_dir = os.path.join(PP_ROOT, "logs", "approvals")
    if not os.path.exists(approvals_dir):
        return jsonify([])

    pending = []
    for req_file in glob.glob(os.path.join(approvals_dir, "APPROVAL-*.json")):
        resp_file = req_file.replace(".json", ".response.json")
        if os.path.exists(resp_file):
            continue
        try:
            with open(req_file) as f:
                pending.append(json.load(f))
        except Exception:
            continue

    pending.sort(key=lambda r: r.get("requested_at", ""), reverse=True)
    return jsonify(pending)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  🚀 Protean Pursuits — Mission Control")
    print(f"  📂 PP Root:  {PP_ROOT}")
    print(f"  📂 Logs:     {LOGS_DIR}")
    print(f"  🌐 Open:     http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
