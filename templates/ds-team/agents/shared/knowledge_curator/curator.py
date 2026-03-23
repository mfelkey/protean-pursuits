#!/usr/bin/env python3
"""
Knowledge Curator Agent — Main Runner

A shared-service agent that feeds both Dev and DS crews by:
  1. Fetching from all configured sources
  2. Evaluating each item for relevance (via LLM)
  3. Ingesting approved items into ChromaDB collections
  4. Purging expired documents
  5. Logging a run report

Usage:
  # Manual run (all sources)
  python agents/shared/knowledge_curator/curator.py

  # Manual run (specific source)
  python agents/shared/knowledge_curator/curator.py --source github
  python agents/shared/knowledge_curator/curator.py --source arxiv
  python agents/shared/knowledge_curator/curator.py --source security
  python agents/shared/knowledge_curator/curator.py --source va_cms

  # Dry run (fetch + evaluate, no ingestion)
  python agents/shared/knowledge_curator/curator.py --dry-run

  # Stats only
  python agents/shared/knowledge_curator/curator.py --stats

Cron setup (see install instructions at bottom of file).
"""

import sys
sys.path.insert(0, "/home/mfelkey/dev-team")

import os
import json
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("config/.env")

# ── Logging ───────────────────────────────────────────────────────
LOG_DIR = "logs/curator"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(LOG_DIR, f"curator_{datetime.utcnow().strftime('%Y%m%d')}.log")
        ),
    ],
)
logger = logging.getLogger("knowledge_curator")

# ── Imports (after path setup) ────────────────────────────────────
from agents.shared.knowledge_curator.fetchers.github_releases import (
    fetch_github_releases,
)
from agents.shared.knowledge_curator.fetchers.arxiv_papers import (
    fetch_arxiv_papers,
)
from agents.shared.knowledge_curator.fetchers.security_feeds import (
    fetch_cve_advisories,
    fetch_owasp_updates,
)
from agents.shared.knowledge_curator.fetchers.va_cms_bulletins import (
    fetch_all_va_cms,
)
from agents.shared.knowledge_curator.evaluator import evaluate_batch
from agents.shared.knowledge_curator.ingestion.chroma_manager import (
    get_client,
    init_collections,
    ingest_document,
    purge_expired,
    get_collection_stats,
)


def load_config() -> dict:
    """Load knowledge sources configuration."""
    config_path = os.path.join(
        os.path.dirname(__file__), "config", "knowledge_sources.json"
    )
    with open(config_path) as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════
# FETCH PHASE
# ═══════════════════════════════════════════════════════════════════

def fetch_all(source_filter: str = "all") -> list[dict]:
    """
    Fetch from all (or specified) sources.
    Returns a unified list of dicts with: title, content, source_type, url, metadata.
    """
    config = load_config()
    items = []

    # ── GitHub Releases ───────────────────────────────────────────
    if source_filter in ("all", "github"):
        logger.info("📦 Fetching GitHub releases...")
        gh_config = config["schedule"]["github_releases"]
        releases = fetch_github_releases(
            since_days=gh_config["since_days"],
            max_per_repo=gh_config["max_per_repo"],
        )
        for r in releases:
            items.append({
                "title": f"{r.repo} {r.tag}",
                "content": r.summary_text,
                "source_type": r.source_type,
                "url": r.url,
                "target_agents": r.target_agents,
                "tags": r.tags,
                "raw": r.to_dict(),
            })
        logger.info(f"  📊 GitHub: {len(releases)} releases fetched")

    # ── ArXiv Papers ──────────────────────────────────────────────
    if source_filter in ("all", "arxiv"):
        logger.info("📄 Fetching ArXiv papers...")
        papers = fetch_arxiv_papers(
            categories=config["arxiv_categories"],
            max_per_category=config["schedule"]["arxiv_papers"]["max_per_category"],
        )
        for p in papers:
            items.append({
                "title": p.title,
                "content": p.summary_text,
                "source_type": p.source_type,
                "url": p.url,
                "target_agents": p.target_agents,
                "tags": p.tags,
                "raw": p.to_dict(),
            })
        logger.info(f"  📊 ArXiv: {len(papers)} papers fetched")

    # ── Security Feeds ────────────────────────────────────────────
    if source_filter in ("all", "security"):
        logger.info("🔒 Fetching security advisories...")
        cves = fetch_cve_advisories(
            since_days=config["schedule"]["security_feeds"]["since_days"],
            max_results=config["schedule"]["security_feeds"]["max_results"],
        )
        for c in cves:
            items.append({
                "title": c.cve_id,
                "content": c.summary_text,
                "source_type": c.source_type,
                "url": c.url,
                "target_agents": c.target_agents,
                "tags": c.tags,
                "raw": c.to_dict(),
            })

        owasp = fetch_owasp_updates()
        for o in owasp:
            items.append({
                "title": o.title,
                "content": o.summary_text,
                "source_type": o.source_type,
                "url": o.url,
                "target_agents": o.target_agents,
                "tags": o.tags,
                "raw": o.to_dict(),
            })
        logger.info(f"  📊 Security: {len(cves)} CVEs + {len(owasp)} OWASP updates")

    # ── VA/CMS Bulletins ──────────────────────────────────────────
    if source_filter in ("all", "va_cms"):
        logger.info("🏥 Fetching VA/CMS bulletins...")
        bulletins = fetch_all_va_cms()
        for b in bulletins:
            items.append({
                "title": b.title,
                "content": b.summary_text,
                "source_type": b.source_type,
                "url": b.url,
                "target_agents": b.target_agents,
                "tags": b.tags,
                "raw": b.to_dict(),
            })
        logger.info(f"  📊 VA/CMS: {len(bulletins)} bulletins fetched")

    logger.info(f"📊 TOTAL FETCHED: {len(items)} items")
    return items


# ═══════════════════════════════════════════════════════════════════
# EVALUATE PHASE
# ═══════════════════════════════════════════════════════════════════

def evaluate_all(items: list[dict]) -> list[dict]:
    """Run all items through the evaluator agent."""
    config = load_config()
    threshold = config.get("relevance_threshold", 0.6)

    logger.info(f"🧠 Evaluating {len(items)} items (threshold: {threshold})...")
    evaluated = evaluate_batch(items, threshold=threshold)

    approved = [i for i in evaluated if i.get("evaluation", {}).get("ingest")]
    logger.info(f"  ✅ Approved for ingestion: {len(approved)}/{len(evaluated)}")

    return evaluated


# ═══════════════════════════════════════════════════════════════════
# INGEST PHASE
# ═══════════════════════════════════════════════════════════════════

def ingest_approved(evaluated_items: list[dict]) -> dict:
    """Ingest approved items into ChromaDB collections."""
    config = load_config()
    client = get_client()
    collections = init_collections(client)

    ingested_count = 0
    collection_counts = {}

    for item in evaluated_items:
        eval_result = item.get("evaluation", {})
        if not eval_result.get("ingest"):
            continue

        expires_days = (
            eval_result.get("expires_days")
            or config["expiration_days"].get(item["source_type"], 180)
        )

        target_agents = (
            eval_result.get("target_agents")
            or item.get("target_agents", ["all"])
        )

        result = ingest_document(
            collections=collections,
            text=item["content"],
            source_type=item["source_type"],
            source_url=item["url"],
            relevance_score=eval_result.get("score", 0.5),
            target_agents=target_agents,
            tags=item.get("tags", []),
            title=item["title"],
            expires_days=expires_days,
        )

        ingested_count += 1
        for coll_name in result:
            collection_counts[coll_name] = collection_counts.get(coll_name, 0) + 1

    logger.info(f"  💾 Ingested {ingested_count} documents into ChromaDB")
    for name, count in collection_counts.items():
        logger.info(f"     {name}: +{count}")

    return {"ingested": ingested_count, "by_collection": collection_counts}


# ═══════════════════════════════════════════════════════════════════
# MAINTENANCE
# ═══════════════════════════════════════════════════════════════════

def run_maintenance() -> dict:
    """Purge expired documents and return stats."""
    logger.info("🧹 Purging expired documents...")
    removed = purge_expired()
    total_removed = sum(removed.values())
    if total_removed > 0:
        logger.info(f"  🗑️ Removed {total_removed} expired documents")
        for name, count in removed.items():
            if count > 0:
                logger.info(f"     {name}: -{count}")
    else:
        logger.info("  ✅ No expired documents found")

    return removed


# ═══════════════════════════════════════════════════════════════════
# RUN REPORT
# ═══════════════════════════════════════════════════════════════════

def save_run_report(
    fetched: list[dict],
    ingestion_result: dict,
    maintenance_result: dict,
    stats: dict,
    dry_run: bool = False,
) -> str:
    """Save a JSON run report to logs/curator/."""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "dry_run": dry_run,
        "fetched_count": len(fetched),
        "evaluated_count": len(fetched),
        "approved_count": sum(
            1 for i in fetched if i.get("evaluation", {}).get("ingest")
        ),
        "rejected_count": sum(
            1 for i in fetched if not i.get("evaluation", {}).get("ingest")
        ),
        "ingestion": ingestion_result,
        "expired_removed": maintenance_result,
        "collection_stats": stats,
        "items": [
            {
                "title": i["title"],
                "source_type": i["source_type"],
                "url": i["url"],
                "score": i.get("evaluation", {}).get("score", 0),
                "ingested": i.get("evaluation", {}).get("ingest", False),
                "key_takeaway": i.get("evaluation", {}).get("key_takeaway", ""),
            }
            for i in fetched
        ],
    }

    filename = f"curator_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(LOG_DIR, filename)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"📋 Run report saved: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Knowledge Curator Agent")
    parser.add_argument(
        "--source",
        choices=["all", "github", "arxiv", "security", "va_cms"],
        default="all",
        help="Which source(s) to fetch from (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and evaluate only — don't ingest into ChromaDB",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print collection stats and exit",
    )
    parser.add_argument(
        "--purge-only",
        action="store_true",
        help="Only run expiration purge, no fetching",
    )
    args = parser.parse_args()

    # ── Stats only ────────────────────────────────────────────────
    if args.stats:
        stats = get_collection_stats()
        print("\n📊 ChromaDB Knowledge Collections:")
        print("─" * 40)
        total = 0
        for name, count in stats.items():
            print(f"  {name:.<30} {count:>5} docs")
            total += count
        print("─" * 40)
        print(f"  {'TOTAL':.<30} {total:>5} docs")
        return

    # ── Purge only ────────────────────────────────────────────────
    if args.purge_only:
        run_maintenance()
        return

    # ── Full run ──────────────────────────────────────────────────
    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("🧠 KNOWLEDGE CURATOR — Starting run")
    logger.info(f"   Source: {args.source}")
    logger.info(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info("=" * 60)

    # 1. Fetch
    items = fetch_all(source_filter=args.source)
    if not items:
        logger.info("  ℹ️ No new items fetched. Done.")
        return

    # 2. Evaluate
    evaluated = evaluate_all(items)

    # 3. Ingest (unless dry run)
    ingestion_result = {"ingested": 0, "by_collection": {}}
    if not args.dry_run:
        ingestion_result = ingest_approved(evaluated)

    # 4. Maintenance
    maintenance_result = {}
    if not args.dry_run:
        maintenance_result = run_maintenance()

    # 5. Stats
    stats = get_collection_stats()

    # 6. Report
    report_path = save_run_report(
        fetched=evaluated,
        ingestion_result=ingestion_result,
        maintenance_result=maintenance_result,
        stats=stats,
        dry_run=args.dry_run,
    )

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"🧠 KNOWLEDGE CURATOR — Complete ({elapsed:.0f}s)")
    logger.info(f"   Fetched: {len(items)}")
    approved = sum(1 for i in evaluated if i.get("evaluation", {}).get("ingest"))
    logger.info(f"   Approved: {approved}")
    logger.info(f"   Ingested: {ingestion_result['ingested']}")
    logger.info(f"   Report: {report_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()


# ═══════════════════════════════════════════════════════════════════
# CRON SETUP
# ═══════════════════════════════════════════════════════════════════
#
# To install the cron jobs, run:
#
#   crontab -e
#
# Then add these lines:
#
#   # Knowledge Curator — daily GitHub + security feeds (6 AM)
#   0 6 * * * cd /home/mfelkey/dev-team && /home/mfelkey/dev-team/.venv/bin/python agents/shared/knowledge_curator/curator.py --source github >> logs/curator/cron.log 2>&1
#   30 6 * * * cd /home/mfelkey/dev-team && /home/mfelkey/dev-team/.venv/bin/python agents/shared/knowledge_curator/curator.py --source security >> logs/curator/cron.log 2>&1
#
#   # Knowledge Curator — weekly ArXiv + VA/CMS (Sunday 7 AM)
#   0 7 * * 0 cd /home/mfelkey/dev-team && /home/mfelkey/dev-team/.venv/bin/python agents/shared/knowledge_curator/curator.py --source arxiv >> logs/curator/cron.log 2>&1
#   30 7 * * 0 cd /home/mfelkey/dev-team && /home/mfelkey/dev-team/.venv/bin/python agents/shared/knowledge_curator/curator.py --source va_cms >> logs/curator/cron.log 2>&1
#
#   # Knowledge Curator — weekly purge of expired docs (Sunday 8 AM)
#   0 8 * * 0 cd /home/mfelkey/dev-team && /home/mfelkey/dev-team/.venv/bin/python agents/shared/knowledge_curator/curator.py --purge-only >> logs/curator/cron.log 2>&1
#
# ═══════════════════════════════════════════════════════════════════
