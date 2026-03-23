"""
Security Feed Fetcher

Monitors two sources:
  1. NIST NVD (National Vulnerability Database) — CVE advisories
  2. OWASP feeds — mobile and web security updates

CVEs are filtered by:
  - Keywords relevant to the tech stack (python, node, react-native, expo, etc.)
  - Severity (CRITICAL and HIGH only — no noise from LOW/MEDIUM)

This ensures the Security Reviewer and DevOps agents always have
current vulnerability context when producing SRR and DIR artifacts.
"""

import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.request import urlopen, Request

logger = logging.getLogger("knowledge_curator.fetchers.security")

# ── Stack-relevant keywords for CVE filtering ─────────────────────
STACK_KEYWORDS = [
    "python", "node", "nodejs", "npm", "react", "react-native",
    "expo", "swift", "kotlin", "android", "ios", "docker",
    "postgresql", "redis", "nginx", "fastlane", "gradle",
    "typescript", "javascript", "chromadb", "ollama", "flask",
    "jwt", "oauth", "tls", "ssl", "xss", "csrf", "sqli",
    "injection", "authentication", "authorization", "encryption",
    "keychain", "keystore", "certificate", "code signing",
]

# ── Severity filter ───────────────────────────────────────────────
SEVERITY_THRESHOLD = ["CRITICAL", "HIGH"]


@dataclass
class FetchedCVE:
    """A single CVE advisory."""
    cve_id: str
    description: str
    severity: str
    score: float
    published: str
    url: str
    affected_products: list[str] = field(default_factory=list)
    source_type: str = "cve_advisory"
    target_agents: list[str] = field(default_factory=lambda: [
        "Security Reviewer", "DevOps Engineer", "Mobile DevOps",
        "Backend Developer", "Frontend Developer",
    ])
    tags: list[str] = field(default_factory=lambda: ["security", "cve"])

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def summary_text(self) -> str:
        return (
            f"CVE Advisory: {self.cve_id} [{self.severity}] (Score: {self.score})\n"
            f"Published: {self.published}\n"
            f"Affected: {', '.join(self.affected_products[:10])}\n"
            f"URL: {self.url}\n\n"
            f"{self.description[:2000]}"
        )


@dataclass
class FetchedOWASPUpdate:
    """An OWASP resource update."""
    title: str
    description: str
    url: str
    published: str
    source_type: str = "owasp_update"
    target_agents: list[str] = field(default_factory=lambda: [
        "Security Reviewer", "Mobile QA",
    ])
    tags: list[str] = field(default_factory=lambda: ["security", "owasp"])

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def summary_text(self) -> str:
        return (
            f"OWASP Update: {self.title}\n"
            f"Published: {self.published}\n"
            f"URL: {self.url}\n\n"
            f"{self.description[:2000]}"
        )


def fetch_cve_advisories(
    since_days: int = 7,
    max_results: int = 20,
) -> list[FetchedCVE]:
    """
    Fetch recent CVEs from NIST NVD API 2.0.

    Filters by stack-relevant keywords and severity threshold.
    NVD API 2.0 is public, no API key required (rate limited to 5 req/30s).
    """
    end = datetime.utcnow()
    start = end - timedelta(days=since_days)

    # NVD API 2.0 date format
    start_str = start.strftime("%Y-%m-%dT00:00:00.000")
    end_str = end.strftime("%Y-%m-%dT23:59:59.999")

    results = []

    for keyword in ["python", "react-native", "node.js", "docker", "android", "ios", "swift"]:
        if len(results) >= max_results:
            break

        url = (
            f"https://services.nvd.nist.gov/rest/json/cves/2.0"
            f"?pubStartDate={start_str}"
            f"&pubEndDate={end_str}"
            f"&keywordSearch={keyword}"
            f"&resultsPerPage=10"
        )

        try:
            req = Request(url, headers={
                "User-Agent": "KnowledgeCurator/1.0",
                "Accept": "application/json",
            })
            with urlopen(req, timeout=30) as response:
                data = json.loads(response.read())

            for vuln in data.get("vulnerabilities", []):
                cve = _parse_nvd_entry(vuln)
                if cve and cve.severity in SEVERITY_THRESHOLD:
                    results.append(cve)

            logger.info(f"  ✅ NVD '{keyword}': {len(data.get('vulnerabilities', []))} CVEs checked")

        except Exception as e:
            logger.warning(f"  ⚠️ NVD '{keyword}': {e}")
            continue

        # Respect rate limit (5 requests per 30 seconds without API key)
        import time
        time.sleep(6)

    # Deduplicate by CVE ID
    seen = set()
    unique = []
    for cve in results:
        if cve.cve_id not in seen:
            seen.add(cve.cve_id)
            unique.append(cve)

    logger.info(f"  📊 Total unique CVEs: {len(unique)}")
    return unique[:max_results]


def _parse_nvd_entry(vuln: dict) -> Optional[FetchedCVE]:
    """Parse a single NVD vulnerability entry."""
    try:
        cve_data = vuln.get("cve", {})
        cve_id = cve_data.get("id", "")

        # Get English description
        descriptions = cve_data.get("descriptions", [])
        desc = ""
        for d in descriptions:
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break

        if not desc:
            return None

        # Check keyword relevance
        desc_lower = desc.lower()
        if not any(kw in desc_lower for kw in STACK_KEYWORDS):
            return None

        # Get severity from CVSS metrics
        metrics = cve_data.get("metrics", {})
        severity = "UNKNOWN"
        score = 0.0

        for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if version in metrics:
                cvss = metrics[version][0].get("cvssData", {})
                severity = cvss.get("baseSeverity", "UNKNOWN")
                score = cvss.get("baseScore", 0.0)
                break

        published = cve_data.get("published", "")
        url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"

        return FetchedCVE(
            cve_id=cve_id,
            description=desc,
            severity=severity,
            score=score,
            published=published,
            url=url,
        )

    except Exception as e:
        logger.debug(f"  Parse error: {e}")
        return None


def fetch_owasp_updates() -> list[FetchedOWASPUpdate]:
    """
    Return curated OWASP resource references.

    OWASP doesn't have a structured API, so we maintain a curated list
    of key resources and their known-good URLs. The evaluator agent
    can check these periodically for updates.
    """
    # These are stable OWASP resources — the evaluator checks for content changes
    resources = [
        FetchedOWASPUpdate(
            title="OWASP Mobile Application Security Testing Guide (MASTG)",
            description=(
                "Comprehensive guide for mobile application security testing. "
                "Covers iOS and Android security testing methodology, tools, "
                "and test cases for authentication, data storage, cryptography, "
                "network communication, and platform interaction."
            ),
            url="https://mas.owasp.org/MASTG/",
            published=datetime.utcnow().isoformat(),
        ),
        FetchedOWASPUpdate(
            title="OWASP Mobile Application Security Verification Standard (MASVS)",
            description=(
                "Security standard for mobile applications. Defines security "
                "requirements organized by: architecture/design, data storage, "
                "cryptography, authentication, network communication, platform "
                "interaction, code quality, and resilience."
            ),
            url="https://mas.owasp.org/MASVS/",
            published=datetime.utcnow().isoformat(),
        ),
        FetchedOWASPUpdate(
            title="OWASP Top 10 for Web Applications",
            description=(
                "The standard awareness document for web application security. "
                "Covers: broken access control, cryptographic failures, injection, "
                "insecure design, security misconfiguration, vulnerable components, "
                "identification failures, integrity failures, logging failures, SSRF."
            ),
            url="https://owasp.org/www-project-top-ten/",
            published=datetime.utcnow().isoformat(),
        ),
    ]

    return resources
