"""
templates/ds-team/agents/ds/ml_engineer.py

ML Engineer — model selection, architecture, training approach, evaluation framework.
Runs in MODEL mode after EDA Analyst, and in PIPELINE mode after Pipeline Engineer.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv("config/.env")

try:
    from agents.shared.knowledge_curator.rag_inject import get_knowledge_context
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


def _rag_context(query: str) -> str:
    if not RAG_AVAILABLE:
        return ""
    try:
        return get_knowledge_context(query)
    except Exception:
        return ""


def build_ml_engineer() -> Agent:
    llm = LLM(
        model=os.getenv("TIER1_MODEL", "ollama/qwen3:32b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=3600,
        num_ctx=8192,
    )
    rag = _rag_context("machine learning model selection architecture training evaluation cross-validation")
    return Agent(
        role="ML Engineer",
        goal=(
            "Design the complete model development approach — selecting algorithms, "
            "defining the feature engineering pipeline, specifying training and "
            "validation strategy, establishing evaluation metrics, and producing "
            "a Model Development Plan ready for implementation."
        ),
        backstory=(
            "You are a senior ML engineer with 13 years of experience designing "
            "and shipping production ML systems across regression, classification, "
            "ranking, and time-series forecasting domains. You are framework-agnostic "
            "and always recommend the simplest model that meets the project's "
            "accuracy and latency requirements — you resist unnecessary complexity. "
            "You work from the Problem Frame and EDA report. "
            "Your Model Development Plan covers: "
            "ALGORITHM SELECTION — primary and fallback algorithms with explicit "
            "justification against the target variable type, data volume, feature "
            "types, interpretability requirements, and inference latency budget. "
            "Candidate shortlist with pros/cons table. "
            "FEATURE ENGINEERING PIPELINE — transformations for each feature class: "
            "numerical (scaling, binning, interaction terms), categorical (encoding "
            "strategy), temporal (lag features, rolling windows, cyclical encoding), "
            "and any domain-specific feature construction. "
            "TRAINING STRATEGY — train/validation/test split approach (temporal "
            "splits for time-series data, stratified for imbalanced classification), "
            "cross-validation scheme, hyperparameter search space and method "
            "(grid, random, Bayesian), early stopping criteria. "
            "EVALUATION FRAMEWORK — primary metric with justification, secondary "
            "metrics, baseline comparisons (naive, random, simple heuristic), "
            "acceptable performance thresholds for production deployment. "
            "REGULARISATION & OVERFITTING CONTROLS — L1/L2, dropout, ensemble "
            "methods, or data augmentation as appropriate. "
            "RETRAINING STRATEGY — trigger conditions (drift detection, scheduled, "
            "performance degradation), retraining cadence, and model versioning approach. "
            "IMPLEMENTATION STACK — recommended libraries, compute requirements, "
            "serialisation format, and serving approach. "
            "All uncertain recommendations tagged [ASSUMPTION] or [VERIFY]. "
            f"{rag}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
