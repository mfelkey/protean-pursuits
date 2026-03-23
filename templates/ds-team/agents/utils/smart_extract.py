"""
Smart Artifact Extraction — agents/utils/smart_extract.py

Two-tier extraction strategy:
  1. SECTION EXTRACTION (primary): Parse markdown headings, pull only the
     sections each downstream agent needs. Fast, deterministic, no GPU.
  2. SEMANTIC SEARCH (fallback): Embed artifact chunks in ChromaDB, query
     by relevance when content isn't under clean headings.

Every agent calls:
    from agents.utils.smart_extract import get_context
    context_text = get_context(artifact_path, consumer="backend_dev")

The module uses CONTEXT_MAP to know which sections each agent needs from
each artifact type, and falls back to ChromaDB when sections aren't found.
"""

import os
import re
import hashlib
import json
from typing import Optional

# ── Optional ChromaDB import ──────────────────────────────────────
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════
#  SECTION EXTRACTION (Tier 1 — Primary)
# ══════════════════════════════════════════════════════════════════

def parse_sections(text: str) -> dict:
    """
    Parse a markdown document into a dict of {heading: content}.

    Keys are normalized lowercase heading text.
    Values include everything from that heading to the next heading of
    equal or higher level.

    Example:
        "## API Endpoints"  →  key: "api endpoints"
        "### Authentication" →  key: "authentication"
        "# 3. SECURITY"     →  key: "3. security"  AND  "security"

    We store both the raw heading and a cleaned version (stripped of
    leading numbers/punctuation) so lookups are flexible.

    Parent sections include their children's content, so searching for
    "api endpoints" returns the parent heading's content plus all
    subsections (GET /api/trips, POST /api/trips, etc.).
    """
    lines = text.split("\n")
    heading_re = re.compile(r"^(#{1,6})\s+(.+)$")

    # First pass: identify all headings with their line numbers and levels
    headings = []
    for i, line in enumerate(lines):
        m = heading_re.match(line.strip())
        if m:
            level = len(m.group(1))
            raw_heading = m.group(2).strip()
            headings.append((i, level, raw_heading))

    if not headings:
        return {}

    sections = {}

    for idx, (line_num, level, raw_heading) in enumerate(headings):
        # Find where this section ends:
        # At the next heading of equal or higher (lower number) level
        end_line = len(lines)
        for next_idx in range(idx + 1, len(headings)):
            next_line, next_level, _ = headings[next_idx]
            if next_level <= level:
                end_line = next_line
                break

        # Content from this heading to its end (includes children)
        content = "\n".join(lines[line_num + 1:end_line]).strip()

        # Generate lookup keys
        normalized = raw_heading.lower()
        cleaned = re.sub(r"^[\d\.\-\)\s]+", "", normalized).strip()

        if content:
            sections[normalized] = content
            if cleaned and cleaned != normalized:
                sections[cleaned] = content

    return sections


def find_section(sections: dict, wanted: str) -> Optional[str]:
    """
    Find a section by flexible matching.

    Tries in order:
      1. Exact match on normalized key
      2. Substring match (wanted appears in key)
      3. Key appears in wanted
      4. Word overlap scoring (best match with >50% overlap)
    """
    wanted_lower = wanted.lower().strip()
    wanted_words = set(wanted_lower.split())

    # 1. Exact
    if wanted_lower in sections:
        return sections[wanted_lower]

    # 2. Substring: wanted in key
    for key, content in sections.items():
        if wanted_lower in key:
            return content

    # 3. Substring: key in wanted
    for key, content in sections.items():
        if key in wanted_lower:
            return content

    # 4. Word overlap
    best_score = 0.0
    best_content = None
    for key, content in sections.items():
        key_words = set(key.split())
        if not key_words or not wanted_words:
            continue
        overlap = len(wanted_words & key_words)
        score = overlap / max(len(wanted_words), len(key_words))
        if score > best_score and score > 0.5:
            best_score = score
            best_content = content

    return best_content


def extract_sections(text: str, wanted_sections: list, max_chars: int = 0) -> str:
    """
    Extract specific sections from a markdown document.

    Args:
        text: Full markdown document
        wanted_sections: List of section names to extract (flexible matching)
        max_chars: Max total characters (0 = no limit)

    Returns:
        Concatenated content of matching sections, separated by headers.
    """
    sections = parse_sections(text)
    parts = []
    total = 0

    for wanted in wanted_sections:
        content = find_section(sections, wanted)
        if content:
            header = f"\n--- {wanted.upper()} ---\n"
            chunk = header + content
            if max_chars and total + len(chunk) > max_chars:
                remaining = max_chars - total
                if remaining > 200:  # worth including a truncated section
                    parts.append(chunk[:remaining] + "\n[...truncated]")
                break
            parts.append(chunk)
            total += len(chunk)

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════
#  CONTEXT MAP — which sections each agent needs from each artifact
# ══════════════════════════════════════════════════════════════════

# Format: CONTEXT_MAP[consumer_agent_id][artifact_type] = [section_names]
# Section names use flexible matching — exact heading not required.

CONTEXT_MAP = {
    # ── Planning agents ────────────────────────────────────────
    "biz_analyst": {
        "PRD": ["user stories", "scope", "success criteria", "stakeholders",
                "functional requirements", "non-functional requirements"],
    },
    "scrum_master": {
        "PRD": ["user stories", "scope", "deliverables", "success criteria"],
        "BAD": ["process flows", "stakeholder", "data dictionary", "requirements traceability"],
    },
    "architect": {
        "PRD": ["functional requirements", "non-functional requirements",
                "scope", "constraints", "deliverables"],
        "BAD": ["data dictionary", "process flows", "integration points"],
        "SPRINT_PLAN": ["sprint breakdown", "dependencies", "milestones"],
    },
    "security": {
        "PRD": ["non-functional requirements", "compliance", "data classification",
                "user roles", "authentication"],
        "TAD": ["security", "authentication", "authorization", "data architecture",
                "api specifications", "deployment", "infrastructure"],
    },
    "ux_designer": {
        "PRD": ["user stories", "user roles", "functional requirements", "scope"],
        "BAD": ["process flows", "stakeholder", "user journey"],
        "SRR": ["findings", "recommendations", "authentication requirements"],
    },
    "ux_content": {
        "PRD": ["user stories", "user roles"],
        "UXD": ["screens", "components", "navigation", "interactions",
                "error states", "user flows"],
    },

    # ── Test Spec agents ───────────────────────────────────────
    "senior_dev": {
        "PRD": ["functional requirements", "non-functional requirements",
                "deliverables", "constraints"],
        "TAD": ["component", "api specifications", "data architecture",
                "technology stack", "infrastructure", "security"],
        "UXD": ["screens", "components", "navigation"],
    },
    "perf_plan": {
        "PRD": ["non-functional requirements", "success criteria", "constraints"],
        "TAD": ["infrastructure", "scalability", "api specifications",
                "data architecture", "deployment", "component"],
        "TIP": ["api contracts", "project structure", "coding standards",
                "implementation sequence"],
    },
    "qa_lead": {
        "PRD": ["user stories", "acceptance criteria", "scope",
                "functional requirements", "non-functional requirements"],
        "TIP": ["api contracts", "project structure", "module boundaries",
                "coding standards"],
        "TAD": ["component", "api specifications", "security"],
        "UXD": ["screens", "interactions", "error states", "accessibility"],
    },
    "test_auto": {
        "MTP": ["test cases", "test strategy", "coverage targets",
                "acceptance criteria", "test data"],
        "TIP": ["api contracts", "project structure", "module boundaries"],
        "TAD": ["api specifications", "data architecture"],
    },

    # ── Build agents ───────────────────────────────────────────
    "backend_dev": {
        "TIP": ["api contracts", "project structure", "module boundaries",
                "coding standards", "implementation sequence", "dependencies"],
        "TAD": ["api specifications", "data architecture", "authentication",
                "authorization", "component"],
        "MTP": ["api test cases", "backend test cases", "integration tests"],
        "TAR": ["unit test", "api test", "integration test"],
    },
    "frontend_dev": {
        "TIP": ["project structure", "frontend", "component", "coding standards"],
        "UXD": ["screens", "components", "navigation", "interactions",
                "responsive", "accessibility"],
        "MTP": ["frontend test cases", "component test", "e2e test",
                "accessibility test"],
        "TAR": ["component test", "e2e test", "accessibility test"],
        "CONTENT_GUIDE": ["labels", "buttons", "messages", "errors",
                          "tooltips", "navigation text"],
        "BIR": ["api endpoints", "authentication", "response format"],
    },
    "dba": {
        "BIR": ["database schema", "sql", "migrations", "indexes",
                "queries", "data access"],
        "TAD": ["data architecture", "database", "scalability"],
        "SRR": ["data protection", "encryption", "audit", "compliance"],
    },
    "desktop_dev": {
        "UXD": ["screens", "components", "navigation", "interactions",
                "accessibility"],
        "TAD": ["component", "api specifications", "security",
                "deployment", "technology stack"],
        "TIP": ["project structure", "coding standards", "dependencies",
                "implementation sequence"],
        "BIR": ["api endpoints", "authentication", "response format"],
        "FIR": ["component", "state management", "routing"],
    },
    "devops": {
        "TIP": ["project structure", "dependencies", "deployment",
                "environment variables"],
        "TAD": ["infrastructure", "deployment", "scalability",
                "security", "monitoring"],
        "SRR": ["infrastructure", "secrets", "network", "compliance",
                "vulnerability"],
        "TAR": ["ci integration", "test execution", "coverage"],
    },
    "devex_writer": {
        "PRD": ["scope", "deliverables", "success criteria", "user stories"],
        "TAD": ["component", "api specifications", "deployment",
                "technology stack", "architecture"],
        "BIR": ["api endpoints", "authentication", "response format",
                "error handling", "database schema", "webhooks"],
        "FIR": ["component", "routing", "state management"],
        "DIR": ["docker", "deployment", "environment variables",
                "ci/cd", "monitoring", "health check"],
        "DSKR": ["installation", "configuration", "packaging"],
    },

    # ── Verify agents ──────────────────────────────────────────
    "pen_test": {
        "SRR": ["threat model", "findings", "attack surface",
                "authentication", "authorization", "compliance"],
        "BIR": ["api endpoints", "authentication", "authorization",
                "database", "input validation", "error handling",
                "middleware", "secrets", "cors"],
        "FIR": ["api integration", "authentication", "input handling",
                "state management", "routing"],
        "DIR": ["docker", "secrets", "environment variables",
                "network", "ci/cd", "tls"],
        "DBAR": ["permissions", "encryption", "audit", "backup",
                 "access control"],
    },
    "scale_arch": {
        "TAD": ["scalability", "infrastructure", "deployment",
                "data architecture", "component", "caching"],
        "BIR": ["database schema", "api endpoints", "caching",
                "connection pool", "pagination", "background jobs",
                "rate limiting", "queries"],
        "FIR": ["bundle", "code splitting", "lazy loading",
                "caching", "cdn", "images", "performance"],
        "DBAR": ["indexes", "partitioning", "replication",
                 "materialized views", "query optimization"],
        "DIR": ["autoscaling", "load balancer", "cdn",
                "multi-region", "health check", "resource limits"],
    },
    "perf_audit": {
        "PBD": ["api latency", "frontend performance", "database performance",
                "infrastructure", "load testing", "benchmarking",
                "mobile performance", "desktop performance"],
        "BIR": ["api endpoints", "database", "queries", "caching",
                "connection pool", "middleware", "background",
                "pagination", "serialization"],
        "FIR": ["bundle", "code splitting", "images", "lazy loading",
                "rendering", "state management", "performance"],
        "DIR": ["container", "resource limits", "autoscaling",
                "health check", "caching"],
        "DBAR": ["indexes", "query optimization", "partitioning",
                 "connection pool", "explain"],
        "DSKR": ["ipc", "main process", "renderer", "memory",
                 "startup", "performance"],
    },
    "a11y_audit": {
        "UXD": ["accessibility", "screens", "components", "navigation",
                "interactions", "color", "contrast", "focus"],
        "FIR": ["accessibility", "aria", "semantic", "keyboard",
                "focus", "alt text", "components", "forms"],
        "BIR": ["error handling", "response format", "validation messages"],
        "IIR": ["voiceover", "accessibility", "dynamic type",
                "reduce motion", "labels"],
        "AIR": ["talkback", "accessibility", "content description",
                "font scaling", "labels"],
        "RN_GUIDE": ["accessibility", "accessible", "accessibilityLabel",
                     "accessibilityRole", "live region"],
        "DSKR": ["accessibility", "keyboard", "screen reader",
                 "focus", "high contrast", "zoom"],
    },
    "license_scan": {
        "PRD": ["scope", "deliverables", "constraints", "business goal"],
        "BIR": ["dependencies", "package", "libraries", "imports"],
        "FIR": ["dependencies", "package", "libraries", "imports"],
        "DIR": ["docker", "base image", "tools", "dependencies"],
        "DSKR": ["dependencies", "package", "framework", "libraries"],
        "IIR": ["dependencies", "cocoapods", "swift package", "libraries"],
        "AIR": ["dependencies", "gradle", "libraries", "imports"],
        "RN_GUIDE": ["dependencies", "package", "libraries", "imports"],
    },
    "verify": {
        "TAR": ["test cases", "test results", "coverage", "pass",
                "fail", "skip", "assertions"],
        "BIR": ["api endpoints", "database schema", "authentication",
                "implementation"],
        "FIR": ["components", "routing", "state management",
                "implementation"],
        "DIR": ["ci/cd", "test execution", "deployment"],
    },

    # ── Mobile agents ──────────────────────────────────────────
    "mobile_qa": {
        "MUXD": ["screens", "navigation", "gestures", "interactions",
                 "accessibility", "platforms"],
        "PRD": ["user stories", "acceptance criteria", "mobile requirements"],
        "TAD": ["api specifications", "authentication", "mobile"],
    },
    "ios_dev": {
        "MUXD": ["ios", "screens", "navigation", "gestures",
                 "accessibility", "components"],
        "PRD": ["user stories", "mobile requirements"],
        "MOBILE_TEST_PLAN": ["ios test", "xctest", "xcuitest",
                             "voiceover test", "accessibility test"],
    },
    "android_dev": {
        "MUXD": ["android", "screens", "navigation", "gestures",
                 "accessibility", "components"],
        "PRD": ["user stories", "mobile requirements"],
        "MOBILE_TEST_PLAN": ["android test", "junit", "espresso",
                             "talkback test", "accessibility test"],
    },
    "rn_arch_p1": {
        "MUXD": ["screens", "navigation", "components", "gestures",
                 "accessibility", "platforms"],
        "MOBILE_TEST_PLAN": ["react native test", "jest", "rntl",
                             "detox", "accessibility test"],
    },
    "rn_dev": {
        "RNAD_P1": ["architecture", "navigation", "state management",
                    "api layer", "component hierarchy"],
        "RNAD_P2": ["testing", "deployment", "performance",
                    "optimization"],
        "MOBILE_TEST_PLAN": ["react native test", "jest", "rntl",
                             "detox", "component test"],
    },
    "mobile_devops": {
        "RN_GUIDE": ["deployment", "configuration", "dependencies",
                     "environment", "build"],
        "SRR": ["mobile security", "code signing", "certificate",
                "secrets", "compliance"],
        "MOBILE_TEST_PLAN": ["ci integration", "test execution",
                             "automation"],
    },
    "mobile_pen_test": {
        "SRR": ["mobile security", "threat model", "authentication",
                "data protection"],
        "IIR": ["keychain", "security", "networking", "storage",
                "authentication", "permissions"],
        "AIR": ["keystore", "security", "networking", "storage",
                "authentication", "permissions", "exported"],
        "RN_GUIDE": ["security", "storage", "authentication",
                     "bridge", "hermes", "async storage"],
        "MDIR": ["code signing", "secrets", "ci/cd", "build",
                 "certificate"],
    },
    "mobile_scale": {
        "MUXD": ["screens", "data", "offline", "sync"],
        "IIR": ["networking", "caching", "storage", "database",
                "background", "performance", "images"],
        "AIR": ["networking", "caching", "storage", "database",
                "background", "performance", "images"],
        "RN_GUIDE": ["networking", "caching", "storage", "database",
                     "background", "performance", "images", "bundle",
                     "lazy loading", "flatlist"],
        "MDIR": ["ci/cd", "ota", "update", "distribution"],
    },
    "mobile_verify": {
        "MOBILE_TEST_PLAN": ["test cases", "acceptance criteria",
                             "coverage", "platforms"],
        "IIR": ["implementation", "screens", "features"],
        "AIR": ["implementation", "screens", "features"],
        "RN_GUIDE": ["implementation", "screens", "features"],
        "MDIR": ["ci/cd", "test execution"],
    },
}


# ══════════════════════════════════════════════════════════════════
#  CHROMADB SEMANTIC SEARCH (Tier 2 — Fallback)
# ══════════════════════════════════════════════════════════════════

CHROMA_DIR = os.path.expanduser("~/dev-team/data/chromadb")
COLLECTION_NAME = "artifact_chunks"


def _get_chroma_collection():
    """Get or create the ChromaDB collection for artifact chunks."""
    if not CHROMA_AVAILABLE:
        return None

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Use the nomic-embed-text model via Ollama
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embed_fn = embedding_functions.OllamaEmbeddingFunction(
        model_name="nomic-embed-text",
        url=f"{ollama_url}/api/embeddings"
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def _chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list:
    """
    Split text into overlapping chunks at paragraph boundaries.
    Prefers splitting at double-newlines (paragraph breaks).
    """
    paragraphs = re.split(r"\n\n+", text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Overlap: keep last N characters
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + "\n\n" + para
            else:
                current_chunk = para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _file_hash(filepath: str) -> str:
    """Hash of file content + mtime for change detection."""
    stat = os.stat(filepath)
    with open(filepath) as f:
        content_hash = hashlib.md5(f.read().encode()).hexdigest()
    return f"{content_hash}_{int(stat.st_mtime)}"


def index_artifact(filepath: str, artifact_type: str, project_id: str):
    """
    Index an artifact's content into ChromaDB for semantic search.

    Called by the orchestrator after each agent saves an artifact.
    Idempotent — re-indexes only if file has changed.
    """
    collection = _get_chroma_collection()
    if collection is None:
        return  # ChromaDB not available, silently skip

    file_hash = _file_hash(filepath)
    prefix = f"{project_id}_{artifact_type}"

    # Check if already indexed with same hash
    existing = collection.get(
        where={"source_prefix": prefix},
        limit=1
    )
    if existing and existing.get("metadatas"):
        if existing["metadatas"][0].get("file_hash") == file_hash:
            return  # Already indexed, no change

    # Delete old chunks for this artifact
    try:
        old_ids = collection.get(where={"source_prefix": prefix})
        if old_ids and old_ids.get("ids"):
            collection.delete(ids=old_ids["ids"])
    except Exception:
        pass  # Collection may be empty

    # Chunk and index
    with open(filepath) as f:
        text = f.read()

    chunks = _chunk_text(text)

    if not chunks:
        return

    ids = [f"{prefix}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "project_id": project_id,
            "artifact_type": artifact_type,
            "source_prefix": prefix,
            "filepath": filepath,
            "file_hash": file_hash,
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas
    )


def semantic_search(query: str, artifact_type: str = None,
                    project_id: str = None, n_results: int = 5) -> str:
    """
    Search ChromaDB for relevant chunks.

    Args:
        query: What the agent is looking for (e.g., "caching strategy and TTLs")
        artifact_type: Filter to specific artifact (e.g., "BIR")
        project_id: Filter to specific project
        n_results: Max chunks to return

    Returns:
        Concatenated relevant chunks, or empty string if ChromaDB unavailable.
    """
    collection = _get_chroma_collection()
    if collection is None:
        return ""

    where_filter = {}
    if artifact_type and project_id:
        where_filter = {
            "$and": [
                {"artifact_type": artifact_type},
                {"project_id": project_id}
            ]
        }
    elif artifact_type:
        where_filter = {"artifact_type": artifact_type}
    elif project_id:
        where_filter = {"project_id": project_id}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None
        )
    except Exception:
        return ""

    if not results or not results.get("documents"):
        return ""

    chunks = results["documents"][0]  # First query's results
    return "\n\n---\n\n".join(chunks)


# ══════════════════════════════════════════════════════════════════
#  UNIFIED API — what agents actually call
# ══════════════════════════════════════════════════════════════════

def get_context(filepath: str, artifact_type: str, consumer: str,
                project_id: str = None, max_chars: int = 8000,
                semantic_queries: list = None) -> str:
    """
    Smart extraction: get the right content for a specific agent.

    Strategy:
      1. Look up CONTEXT_MAP for consumer → artifact_type → sections
      2. Parse the artifact and extract those sections
      3. If sections found < 500 chars, fall back to semantic search
      4. If semantic search unavailable, fall back to first-N-chars

    Args:
        filepath: Path to the artifact markdown file
        artifact_type: Type code (e.g., "BIR", "TAD", "FIR")
        consumer: Agent ID of the consuming agent (e.g., "backend_dev")
        project_id: Project ID for ChromaDB scoping (optional)
        max_chars: Maximum characters to return
        semantic_queries: Optional override queries for ChromaDB search

    Returns:
        Extracted context string, optimized for the consuming agent.
    """
    if not filepath or not os.path.exists(filepath):
        return ""

    with open(filepath) as f:
        full_text = f.read()

    # ── Tier 1: Section extraction ────────────────────────────
    wanted = []
    agent_map = CONTEXT_MAP.get(consumer, {})
    wanted = agent_map.get(artifact_type, [])

    extracted = ""
    if wanted:
        extracted = extract_sections(full_text, wanted, max_chars=max_chars)

    # If we got meaningful content (>500 chars), use it
    if len(extracted) > 500:
        return extracted[:max_chars]

    # ── Tier 2: Semantic search (ChromaDB) ────────────────────
    if CHROMA_AVAILABLE and project_id:
        queries = semantic_queries or wanted
        if queries:
            # Build a natural language query from section names
            query_text = f"Sections about: {', '.join(queries[:5])}"
            semantic_result = semantic_search(
                query=query_text,
                artifact_type=artifact_type,
                project_id=project_id,
                n_results=5
            )
            if len(semantic_result) > 500:
                return semantic_result[:max_chars]

    # ── Tier 3: Fallback to first-N-chars ─────────────────────
    # Still better than nothing — but log a warning
    if len(full_text) > max_chars:
        return full_text[:max_chars] + "\n\n[...truncated — section extraction found no matching headings]"
    return full_text


def get_multi_context(artifacts: dict, consumer: str,
                       project_id: str = None,
                       max_chars_per_artifact: int = 6000) -> dict:
    """
    Extract context from multiple artifacts for one agent.

    Args:
        artifacts: Dict of {artifact_type: filepath}
                   e.g., {"BIR": "/path/to/BIR.md", "TAD": "/path/to/TAD.md"}
        consumer: Agent ID
        project_id: For ChromaDB scoping
        max_chars_per_artifact: Max chars per artifact

    Returns:
        Dict of {artifact_type: extracted_text}
    """
    result = {}
    for atype, path in artifacts.items():
        if path:
            result[atype] = get_context(
                filepath=path,
                artifact_type=atype,
                consumer=consumer,
                project_id=project_id,
                max_chars=max_chars_per_artifact
            )
    return result


# ══════════════════════════════════════════════════════════════════
#  DIAGNOSTIC / CLI
# ══════════════════════════════════════════════════════════════════

def diagnose(filepath: str, consumer: str = None):
    """
    Print diagnostic info about an artifact's sections and what
    each agent would extract from it.
    """
    with open(filepath) as f:
        text = f.read()

    sections = parse_sections(text)
    print(f"\n📄 Artifact: {filepath}")
    print(f"   Total length: {len(text):,} chars")
    print(f"   Sections found: {len(sections)}")
    print()

    for key in sorted(sections.keys()):
        preview = sections[key][:80].replace("\n", " ")
        print(f"   [{len(sections[key]):>5} chars]  {key}")

    if consumer:
        print(f"\n🤖 Extraction for consumer '{consumer}':")
        # Guess artifact type from filename
        fname = os.path.basename(filepath).upper()
        for atype in ["PRD", "BAD", "TAD", "SRR", "UXD", "TIP", "BIR",
                       "FIR", "DBAR", "DIR", "MTP", "TAR", "PBD",
                       "MUXD", "IIR", "AIR", "RNAD", "MDIR", "DSKR"]:
            if atype in fname:
                wanted = CONTEXT_MAP.get(consumer, {}).get(atype, [])
                if wanted:
                    print(f"   Wants from {atype}: {wanted}")
                    extracted = extract_sections(text, wanted, max_chars=6000)
                    print(f"   Extracted: {len(extracted):,} chars")
                break


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python smart_extract.py <artifact.md> [consumer_agent_id]")
        print("\nExamples:")
        print("  python smart_extract.py dev/build/PROJ-XXX_BIR.md pen_test")
        print("  python smart_extract.py dev/requirements/PROJ-XXX_PRD.md architect")
        sys.exit(1)

    filepath = sys.argv[1]
    consumer = sys.argv[2] if len(sys.argv) > 2 else None
    diagnose(filepath, consumer)
