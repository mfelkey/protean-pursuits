#!/usr/bin/env python3
"""
scripts/publish.py

Protean Pursuits — Document publish utility

Scans all team output directories and publishes any new .md files
to ~/projects/parallaxedge/docs/ as PDF + .md.

Usage:
    python3.11 scripts/publish.py              # publish all pending
    python3.11 scripts/publish.py --file path/to/doc.md --team legal --title "My Doc"
    python3.11 scripts/publish.py --list       # show what's in docs/
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.doc_publisher import publish_document, publish_all_pending, PARALLAXEDGE_DOCS


def list_docs() -> None:
    """List all documents currently in parallaxedge/docs/."""
    PARALLAXEDGE_DOCS.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PARALLAXEDGE_DOCS.glob("*.pdf"))

    if not pdfs:
        print("\n  No documents published yet.\n")
        return

    print(f"\n  {'─'*70}")
    print(f"  {'DATE':<12} {'TEAM':<12} {'DOCUMENT':<40} SIZE")
    print(f"  {'─'*70}")

    for pdf in pdfs:
        parts = pdf.stem.split('_', 3)
        date_str  = parts[0] if len(parts) > 0 else "—"
        team_str  = parts[1] if len(parts) > 1 else "—"
        title_str = parts[2].replace('-', ' ').title() if len(parts) > 2 else pdf.stem
        size_kb   = pdf.stat().st_size // 1024
        print(f"  {date_str:<12} {team_str:<12} {title_str[:40]:<40} {size_kb}KB")

    print(f"  {'─'*70}")
    print(f"  {len(pdfs)} document(s) in {PARALLAXEDGE_DOCS}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Protean Pursuits document publisher"
    )
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--team", type=str, default="protean")
    parser.add_argument("--title", type=str, default=None)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        list_docs()
    elif args.file:
        title = args.title or Path(args.file).stem.replace('_', ' ')
        publish_document(args.file, args.team, title, args.run_id)
    else:
        publish_all_pending()
