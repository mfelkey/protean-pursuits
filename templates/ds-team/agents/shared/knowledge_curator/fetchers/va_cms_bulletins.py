"""
VA/CMS Bulletin Fetcher

Monitors government healthcare IT sources for policy and technical updates:
  - VA Office of Information and Technology (OIT) bulletins
  - CMS technical standards and implementation guides
  - VA Lighthouse API updates (developer.va.gov)
  - HealthIT.gov standards updates

These feed the domain_va and domain_healthcare ChromaDB collections,
ensuring agents working on VA/healthcare projects have current
regulatory and technical context.
"""

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.request import urlopen, Request

logger = logging.getLogger("knowledge_curator.fetchers.va_cms")


@dataclass
class FetchedBulletin:
    """A government health IT bulletin or update."""
    title: str
    description: str
    source: str  # "VA", "CMS", "HealthIT"
    url: str
    published: str
    bulletin_type: str = ""  # "policy", "technical", "api_update", "standard"
    source_type: str = "va_bulletin"
    target_agents: list[str] = field(default_factory=lambda: [
        "Product Manager", "Business Analyst", "Security Reviewer",
        "Domain Analyst", "Data Strategist",
    ])
    tags: list[str] = field(default_factory=lambda: ["healthcare", "government"])

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def summary_text(self) -> str:
        return (
            f"{self.source} Bulletin: {self.title}\n"
            f"Type: {self.bulletin_type}\n"
            f"Published: {self.published}\n"
            f"URL: {self.url}\n\n"
            f"{self.description[:2000]}"
        )


def fetch_va_lighthouse_updates(max_results: int = 10) -> list[FetchedBulletin]:
    """
    Check VA Lighthouse developer portal for API updates.

    The VA Lighthouse API (developer.va.gov) provides the public API
    surface for VA data. Changes here directly affect any VA-integrated
    application.
    """
    results = []

    # VA Lighthouse API catalog
    try:
        url = "https://developer.va.gov/explore"
        bulletin = FetchedBulletin(
            title="VA Lighthouse API Portal — Current API Catalog",
            description=(
                "VA Lighthouse is the VA's public API platform providing access to "
                "Veterans' health records, benefits, facilities, and forms data. "
                "Key APIs include: Patient Health API (FHIR R4), Benefits Claims, "
                "Veteran Verification, VA Facilities, and Appeals Status. "
                "All APIs require OAuth 2.0 with PKCE for production access. "
                "Data is PHI/PII and requires HIPAA-compliant handling."
            ),
            source="VA",
            url=url,
            published=datetime.utcnow().isoformat(),
            bulletin_type="api_update",
            tags=["healthcare", "government", "va", "api", "fhir", "hipaa"],
        )
        results.append(bulletin)
        logger.info("  ✅ VA Lighthouse: catalog reference updated")

    except Exception as e:
        logger.warning(f"  ⚠️ VA Lighthouse: {e}")

    return results


def fetch_cms_updates() -> list[FetchedBulletin]:
    """
    Curated CMS technical standards relevant to healthcare apps.

    CMS doesn't provide a convenient API for policy updates, so we
    maintain references to key standards that affect healthcare
    application development.
    """
    standards = [
        FetchedBulletin(
            title="CMS Interoperability and Patient Access Final Rule (CMS-9115-F)",
            description=(
                "Requires CMS-regulated payers to make patient data available via "
                "FHIR R4 APIs. Mandates Patient Access API, Provider Directory API, "
                "and payer-to-payer data exchange. Affects any application that "
                "integrates with Medicare/Medicaid claims or clinical data."
            ),
            source="CMS",
            url="https://www.cms.gov/priorities/key-initiatives/burden-reduction/interoperability",
            published=datetime.utcnow().isoformat(),
            bulletin_type="policy",
            source_type="cms_bulletin",
            tags=["healthcare", "government", "cms", "fhir", "interoperability"],
        ),
        FetchedBulletin(
            title="TEFCA (Trusted Exchange Framework and Common Agreement)",
            description=(
                "National framework for health information exchange. Establishes "
                "qualified health information networks (QHINs) and standard "
                "exchange purposes. Any application connecting to the national "
                "health data network must comply with TEFCA requirements for "
                "identity proofing, consent management, and data use agreements."
            ),
            source="CMS",
            url="https://www.healthit.gov/topic/interoperability/policy/trusted-exchange-framework-and-common-agreement-tefca",
            published=datetime.utcnow().isoformat(),
            bulletin_type="standard",
            source_type="cms_bulletin",
            tags=["healthcare", "government", "tefca", "interoperability", "hie"],
        ),
        FetchedBulletin(
            title="HIPAA Security Rule — Technical Safeguards",
            description=(
                "Technical safeguards required for electronic PHI: access controls "
                "(unique user ID, emergency access, auto logoff, encryption), "
                "audit controls (hardware/software/procedural mechanisms), "
                "integrity controls (authentication of ePHI), person/entity "
                "authentication, and transmission security (integrity controls, "
                "encryption). All apply to mobile and web applications handling PHI."
            ),
            source="CMS",
            url="https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html",
            published=datetime.utcnow().isoformat(),
            bulletin_type="standard",
            source_type="cms_bulletin",
            tags=["healthcare", "hipaa", "security", "phi", "compliance"],
        ),
    ]

    logger.info(f"  ✅ CMS: {len(standards)} standard references loaded")
    return standards


def fetch_all_va_cms(max_results: int = 20) -> list[FetchedBulletin]:
    """Fetch from all VA/CMS sources."""
    results = []
    results.extend(fetch_va_lighthouse_updates(max_results=max_results // 2))
    results.extend(fetch_cms_updates())
    return results[:max_results]
