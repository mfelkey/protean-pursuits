"""
ArXiv Paper Fetcher

Monitors ArXiv categories for new papers relevant to the agent system:
  - cs.SE   (Software Engineering)
  - cs.AI   (Artificial Intelligence)
  - cs.LG   (Machine Learning — dev + ds overlap)
  - stat.ML (Statistical ML — ds crew)
  - stat.AP (Applications — ds crew)

Uses the ArXiv Atom API (no auth required, no API key).
Filters by relevance keywords to avoid flooding ChromaDB with unrelated papers.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.request import urlopen, Request
from urllib.parse import urlencode

logger = logging.getLogger("knowledge_curator.fetchers.arxiv")

# ── Relevance keywords (paper must match at least one) ────────────
DEV_KEYWORDS = [
    "large language model", "code generation", "software agent",
    "automated software", "multi-agent", "prompt engineering",
    "retrieval augmented", "RAG", "code review", "CI/CD",
    "mobile development", "cross-platform", "react native",
    "software testing", "DevOps", "LLM agent",
]

DS_KEYWORDS = [
    "statistical modeling", "time series", "causal inference",
    "simulation", "healthcare analytics", "clinical data",
    "EHR", "electronic health record", "survival analysis",
    "bayesian", "machine learning pipeline", "AutoML",
]

# ── Category → collection + agent routing ─────────────────────────
CATEGORY_CONFIG = {
    "cs.SE": {
        "source_type": "arxiv_paper_cs",
        "target_agents": ["Technical Architect", "Senior Developer", "Backend Developer"],
        "tags": ["software-engineering", "arxiv"],
        "keywords": DEV_KEYWORDS,
    },
    "cs.AI": {
        "source_type": "arxiv_paper_cs_ai",
        "target_agents": ["Orchestrator", "Technical Architect", "all"],
        "tags": ["artificial-intelligence", "arxiv"],
        "keywords": DEV_KEYWORDS,
    },
    "cs.LG": {
        "source_type": "arxiv_paper_cs_ai",
        "target_agents": ["Technical Architect", "Data Strategist", "all"],
        "tags": ["machine-learning", "arxiv"],
        "keywords": DEV_KEYWORDS + DS_KEYWORDS,
    },
    "stat.ML": {
        "source_type": "arxiv_paper_stat",
        "target_agents": ["Data Strategist", "Statistical Modeler", "ML Engineer"],
        "tags": ["statistical-ml", "arxiv"],
        "keywords": DS_KEYWORDS,
    },
    "stat.AP": {
        "source_type": "arxiv_paper_stat",
        "target_agents": ["Domain Analyst", "Data Strategist"],
        "tags": ["applied-statistics", "arxiv"],
        "keywords": DS_KEYWORDS,
    },
}


@dataclass
class FetchedPaper:
    """A single paper fetched from ArXiv."""
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    published: str
    url: str
    source_type: str = "arxiv_paper_cs"
    target_agents: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def summary_text(self) -> str:
        """Text sent to ChromaDB for embedding."""
        authors_str = ", ".join(self.authors[:5])
        if len(self.authors) > 5:
            authors_str += f" et al. ({len(self.authors)} authors)"
        return (
            f"ArXiv Paper: {self.title}\n"
            f"Authors: {authors_str}\n"
            f"Categories: {', '.join(self.categories)}\n"
            f"Published: {self.published}\n"
            f"URL: {self.url}\n\n"
            f"Abstract:\n{self.abstract}"
        )


def fetch_arxiv_papers(
    categories: Optional[list[str]] = None,
    since_days: int = 7,
    max_per_category: int = 10,
) -> list[FetchedPaper]:
    """
    Fetch recent papers from ArXiv matching relevance keywords.

    Uses the ArXiv Atom API — no authentication required.
    """
    if categories is None:
        categories = list(CATEGORY_CONFIG.keys())

    all_papers = []
    seen_ids = set()

    for category in categories:
        config = CATEGORY_CONFIG.get(category)
        if not config:
            logger.warning(f"  ⚠️ Unknown category: {category}")
            continue

        try:
            papers = _query_arxiv(
                category=category,
                keywords=config["keywords"],
                max_results=max_per_category,
            )

            for paper in papers:
                if paper.arxiv_id in seen_ids:
                    continue
                seen_ids.add(paper.arxiv_id)

                paper.source_type = config["source_type"]
                paper.target_agents = config["target_agents"]
                paper.tags = config["tags"]
                all_papers.append(paper)

            logger.info(f"  ✅ {category}: {len(papers)} relevant papers")

        except Exception as e:
            logger.warning(f"  ⚠️ {category}: {e}")
            continue

    return all_papers


def _query_arxiv(
    category: str,
    keywords: list[str],
    max_results: int = 10,
) -> list[FetchedPaper]:
    """Query ArXiv Atom API for a single category with keyword filtering."""

    # Build query: category AND (keyword1 OR keyword2 OR ...)
    keyword_query = " OR ".join(f'abs:"{kw}"' for kw in keywords[:8])  # API limit
    query = f"cat:{category} AND ({keyword_query})"

    params = urlencode({
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })

    url = f"http://export.arxiv.org/api/query?{params}"
    req = Request(url, headers={"User-Agent": "KnowledgeCurator/1.0"})

    with urlopen(req, timeout=30) as response:
        xml_data = response.read()

    return _parse_atom_feed(xml_data)


def _parse_atom_feed(xml_data: bytes) -> list[FetchedPaper]:
    """Parse ArXiv Atom XML into FetchedPaper objects."""
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    root = ET.fromstring(xml_data)
    papers = []

    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        published_el = entry.find("atom:published", ns)
        id_el = entry.find("atom:id", ns)

        if not all([title_el, summary_el, published_el, id_el]):
            continue

        title = " ".join(title_el.text.strip().split())
        abstract = " ".join(summary_el.text.strip().split())
        published = published_el.text.strip()
        arxiv_url = id_el.text.strip()
        arxiv_id = arxiv_url.split("/abs/")[-1]

        authors = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None:
                authors.append(name_el.text.strip())

        categories = []
        for cat_el in entry.findall("atom:category", ns):
            term = cat_el.get("term", "")
            if term:
                categories.append(term)

        papers.append(FetchedPaper(
            arxiv_id=arxiv_id,
            title=title,
            abstract=abstract,
            authors=authors,
            categories=categories,
            published=published,
            url=arxiv_url,
        ))

    return papers
