"""
GitHub Release Fetcher

Monitors specified repositories for new releases and changelogs.
Returns structured entries ready for evaluation and ingestion.

Tracked repos (configurable via config/knowledge_sources.json):
  - Core AI stack: CrewAI, Ollama, ChromaDB, LiteLLM
  - Languages: Python, TypeScript, Swift, Kotlin
  - Mobile: React Native, Expo, Fastlane, Detox, Sentry, Gradle, CocoaPods
  - Web/Backend: Flask, Pydantic, Node.js
  - Testing: Jest, Playwright, k6
  - DevOps: Docker Compose
  - Security: OWASP MASTG
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict

from dotenv import load_dotenv

logger = logging.getLogger("knowledge_curator.fetchers.github")

# Default repos to monitor — override via config/knowledge_sources.json
DEFAULT_REPOS = [
    "crewAIInc/crewAI",
    "facebook/react-native",
    "expo/expo",
    "python/cpython",
    "nodejs/node",
    "fastlane/fastlane",
    "OWASP/owasp-mastg",
    "microsoft/TypeScript",
    "jestjs/jest",
    "ollama/ollama",
    "chroma-core/chroma",
    "wix/Detox",
    "microsoft/playwright",
    "grafana/k6",
    "getsentry/sentry-react-native",
    "docker/compose",
    "pallets/flask",
    "pydantic/pydantic",
    "BerriAI/litellm",
    "apple/swift",
    "JetBrains/kotlin",
    "gradle/gradle",
    "CocoaPods/CocoaPods",
]


@dataclass
class FetchedRelease:
    """A single release fetched from GitHub."""
    repo: str
    tag: str
    title: str
    body: str
    published_at: str
    url: str
    source_type: str = "github_release"
    target_agents: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def summary_text(self) -> str:
        """Text sent to ChromaDB for embedding."""
        return (
            f"GitHub Release: {self.repo} {self.tag}\n"
            f"Title: {self.title}\n"
            f"Published: {self.published_at}\n\n"
            f"{self.body[:3000]}"
        )


# ── Agent relevance routing ──────────────────────────────────────
REPO_AGENT_MAP = {
    "crewAIInc/crewAI": ["Orchestrator", "all"],
    "facebook/react-native": ["RN Architect", "RN Developer", "Mobile DevOps"],
    "expo/expo": ["RN Architect", "RN Developer", "Mobile DevOps"],
    "python/cpython": ["Backend Developer", "DevOps Engineer", "all"],
    "nodejs/node": ["Frontend Developer", "DevOps Engineer"],
    "fastlane/fastlane": ["Mobile DevOps", "iOS Developer", "Android Developer"],
    "OWASP/owasp-mastg": ["Security Reviewer", "Mobile QA"],
    "microsoft/TypeScript": ["Frontend Developer", "RN Developer"],
    "jestjs/jest": ["Test Automation Engineer", "Mobile QA"],
    "ollama/ollama": ["Orchestrator", "all"],
    "chroma-core/chroma": ["Orchestrator", "Backend Developer", "all"],
    "wix/Detox": ["Mobile QA", "Test Automation Engineer"],
    "microsoft/playwright": ["Test Automation Engineer", "QA Lead"],
    "grafana/k6": ["Test Automation Engineer", "DevOps Engineer"],
    "getsentry/sentry-react-native": ["Mobile DevOps", "RN Developer"],
    "docker/compose": ["DevOps Engineer", "all"],
    "pallets/flask": ["Backend Developer"],
    "pydantic/pydantic": ["Backend Developer", "all"],
    "BerriAI/litellm": ["Orchestrator", "all"],
    "apple/swift": ["iOS Developer"],
    "JetBrains/kotlin": ["Android Developer"],
    "gradle/gradle": ["Android Developer", "Mobile DevOps"],
    "CocoaPods/CocoaPods": ["iOS Developer", "Mobile DevOps"],
}

REPO_TAG_MAP = {
    "crewAIInc/crewAI": ["crewai", "agent-framework", "orchestration"],
    "facebook/react-native": ["react-native", "mobile", "cross-platform"],
    "expo/expo": ["expo", "react-native", "mobile", "eas-build"],
    "python/cpython": ["python", "language", "runtime"],
    "nodejs/node": ["nodejs", "javascript", "runtime"],
    "fastlane/fastlane": ["fastlane", "ci-cd", "mobile", "code-signing"],
    "OWASP/owasp-mastg": ["security", "mobile", "owasp", "testing"],
    "microsoft/TypeScript": ["typescript", "language", "type-safety"],
    "jestjs/jest": ["jest", "testing", "javascript"],
    "ollama/ollama": ["ollama", "llm", "inference", "local-ai"],
    "chroma-core/chroma": ["chromadb", "vector-database", "embeddings", "rag"],
    "wix/Detox": ["detox", "mobile-testing", "e2e", "react-native"],
    "microsoft/playwright": ["playwright", "e2e", "browser-testing", "accessibility"],
    "grafana/k6": ["k6", "performance", "load-testing"],
    "getsentry/sentry-react-native": ["sentry", "crash-reporting", "monitoring"],
    "docker/compose": ["docker", "containers", "devops"],
    "pallets/flask": ["flask", "python", "web-framework"],
    "pydantic/pydantic": ["pydantic", "validation", "python", "typing"],
    "BerriAI/litellm": ["litellm", "llm-proxy", "model-management"],
    "apple/swift": ["swift", "ios", "apple", "language"],
    "JetBrains/kotlin": ["kotlin", "android", "language"],
    "gradle/gradle": ["gradle", "android", "build-tool"],
    "CocoaPods/CocoaPods": ["cocoapods", "ios", "dependency-management"],
}


def fetch_github_releases(
    repos: Optional[list[str]] = None,
    since_days: int = 7,
    max_per_repo: int = 3,
) -> list[FetchedRelease]:
    """
    Fetch recent releases from monitored GitHub repos.

    Uses PyGithub (already in your stack from Phase 6).
    Falls back gracefully if rate-limited or if a repo has no releases.
    """
    from github import Github, Auth

    load_dotenv("config/.env")
    token = os.getenv("GITHUB_TOKEN")
    if not token or token == "your_github_pat_here":
        logger.error("GITHUB_TOKEN not configured in config/.env")
        return []

    auth = Auth.Token(token)
    g = Github(auth=auth)

    if repos is None:
        repos = _load_repo_list()

    since = datetime.now(tz=timezone.utc) - timedelta(days=since_days)
    results = []

    for repo_name in repos:
        try:
            repo = g.get_repo(repo_name)
            releases = repo.get_releases()

            count = 0
            for release in releases:
                if count >= max_per_repo:
                    break
                if release.published_at and release.published_at >= since:
                    entry = FetchedRelease(
                        repo=repo_name,
                        tag=release.tag_name,
                        title=release.title or release.tag_name,
                        body=release.body or "",
                        published_at=release.published_at.isoformat(),
                        url=release.html_url,
                        target_agents=REPO_AGENT_MAP.get(repo_name, ["all"]),
                        tags=REPO_TAG_MAP.get(repo_name, []),
                    )
                    results.append(entry)
                    count += 1

            logger.info(f"  ✅ {repo_name}: {count} releases since {since.date()}")

        except Exception as e:
            logger.warning(f"  ⚠️ {repo_name}: {e}")
            continue

    g.close()
    return results


def _load_repo_list() -> list[str]:
    """Load repo list from config file, fall back to defaults."""
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "knowledge_sources.json"
    )
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        return config.get("github_repos", DEFAULT_REPOS)
    return DEFAULT_REPOS
