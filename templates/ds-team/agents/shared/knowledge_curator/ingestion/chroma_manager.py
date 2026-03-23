"""
ChromaDB Knowledge Collection Manager

Manages the five knowledge collections that feed both Dev and DS crews:
  - dev_practices      → Dev crew agents
  - ds_methods         → DS crew agents
  - domain_healthcare  → Shared (both crews)
  - domain_va          → Shared (both crews)
  - system_updates     → Shared (both crews)

Each document stored includes metadata for filtering:
  - source_type: github_release | arxiv_paper | cve_advisory | va_bulletin
  - source_url:  original URL
  - ingested_at: ISO timestamp
  - relevance_score: 0.0–1.0 (from evaluator agent)
  - target_agents: comma-separated agent roles this is relevant to
  - expires_at: ISO timestamp for expiration (nullable)
  - tags: comma-separated domain tags
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional

import chromadb
import ollama
from dotenv import load_dotenv


def _get_chroma_path() -> str:
    """Resolve ChromaDB path relative to dev-team root."""
    return os.getenv("CHROMA_PERSIST_DIR", "./memory/chroma_db")


def get_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=_get_chroma_path())


def get_embed_model() -> str:
    """Return the embedding model name from env."""
    return os.getenv("EMBED_MODEL", "nomic-embed-text").replace("ollama/", "")


def embed_text(text: str) -> list[float]:
    """Generate an embedding vector via Ollama."""
    model = get_embed_model()
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]


def doc_id(source_url: str, chunk_index: int = 0) -> str:
    """Deterministic document ID from source URL + chunk index."""
    raw = f"{source_url}::chunk_{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Collection Names ──────────────────────────────────────────────
COLLECTIONS = [
    "dev_practices",
    "ds_methods",
    "domain_healthcare",
    "domain_va",
    "system_updates",
]

# ── Source → Collection Routing ───────────────────────────────────
SOURCE_COLLECTION_MAP = {
    "github_release": ["dev_practices", "system_updates"],
    "arxiv_paper_cs": ["dev_practices"],
    "arxiv_paper_stat": ["ds_methods"],
    "arxiv_paper_cs_ai": ["dev_practices", "ds_methods"],
    "cve_advisory": ["dev_practices", "system_updates"],
    "owasp_update": ["dev_practices", "system_updates"],
    "va_bulletin": ["domain_va", "domain_healthcare"],
    "cms_bulletin": ["domain_healthcare", "domain_va"],
}


def init_collections(client: Optional[chromadb.PersistentClient] = None) -> dict:
    """Create or retrieve all five knowledge collections. Returns name→collection map."""
    if client is None:
        client = get_client()
    return {
        name: client.get_or_create_collection(name=name)
        for name in COLLECTIONS
    }


def ingest_document(
    collections: dict,
    text: str,
    source_type: str,
    source_url: str,
    relevance_score: float,
    target_agents: list[str],
    tags: list[str],
    title: str = "",
    expires_days: Optional[int] = None,
    chunk_index: int = 0,
) -> dict:
    """
    Embed and store a document in the appropriate collection(s).

    Returns a summary dict with collection names and doc IDs written.
    """
    now = datetime.utcnow()
    expires_at = (
        (now + timedelta(days=expires_days)).isoformat()
        if expires_days
        else ""
    )

    embedding = embed_text(text)
    did = doc_id(source_url, chunk_index)

    metadata = {
        "source_type": source_type,
        "source_url": source_url,
        "title": title,
        "ingested_at": now.isoformat(),
        "relevance_score": relevance_score,
        "target_agents": ",".join(target_agents),
        "expires_at": expires_at,
        "tags": ",".join(tags),
    }

    target_collections = SOURCE_COLLECTION_MAP.get(source_type, ["system_updates"])
    results = {}

    for coll_name in target_collections:
        if coll_name not in collections:
            continue
        coll = collections[coll_name]
        # Upsert to handle re-ingestion gracefully
        coll.upsert(
            ids=[did],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
        )
        results[coll_name] = did

    return results


def query_collection(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
    where_filter: Optional[dict] = None,
    client: Optional[chromadb.PersistentClient] = None,
) -> dict:
    """
    Query a knowledge collection by semantic similarity.

    This is the function the Orchestrator will call before each agent task
    to inject relevant knowledge into the agent's context.
    """
    if client is None:
        client = get_client()
    collection = client.get_or_create_collection(name=collection_name)
    embedding = embed_text(query_text)

    kwargs = {
        "query_embeddings": [embedding],
        "n_results": n_results,
    }
    if where_filter:
        kwargs["where"] = where_filter

    return collection.query(**kwargs)


def purge_expired(client: Optional[chromadb.PersistentClient] = None) -> dict:
    """
    Remove documents past their expires_at date.

    Returns {collection_name: count_removed}.
    """
    if client is None:
        client = get_client()

    now = datetime.utcnow().isoformat()
    removed = {}

    for name in COLLECTIONS:
        coll = client.get_or_create_collection(name=name)
        # Get all docs with an expiration set
        all_docs = coll.get(where={"expires_at": {"$ne": ""}})

        expired_ids = []
        if all_docs and all_docs["ids"]:
            for i, doc_id_val in enumerate(all_docs["ids"]):
                meta = all_docs["metadatas"][i]
                if meta.get("expires_at") and meta["expires_at"] < now:
                    expired_ids.append(doc_id_val)

        if expired_ids:
            coll.delete(ids=expired_ids)
        removed[name] = len(expired_ids)

    return removed


def get_collection_stats(client: Optional[chromadb.PersistentClient] = None) -> dict:
    """Return document counts for all collections."""
    if client is None:
        client = get_client()
    stats = {}
    for name in COLLECTIONS:
        coll = client.get_or_create_collection(name=name)
        stats[name] = coll.count()
    return stats
