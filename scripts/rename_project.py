#!/usr/bin/env python3
"""
scripts/rename_project.py

Rename a project ID across all log files and context JSON.

Usage:
    python3.11 scripts/rename_project.py PROJ-5F960CD7 PROJ-PARALLAXEDGE
"""

import os
import sys
import json
import glob
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def rename_project(old_id: str, new_id: str) -> None:
    logs_dir = REPO_ROOT / "logs"
    renamed = []
    updated = []

    # 1. Rename files containing old_id
    for path in sorted(logs_dir.rglob("*")):
        if old_id in path.name:
            new_path = path.parent / path.name.replace(old_id, new_id)
            path.rename(new_path)
            renamed.append(f"{path.name} → {new_path.name}")

    # 2. Update content inside JSON/MD files
    for path in sorted(logs_dir.rglob("*")):
        if path.is_file() and path.suffix in (".json", ".md"):
            try:
                content = path.read_text()
                if old_id in content:
                    path.write_text(content.replace(old_id, new_id))
                    updated.append(str(path.relative_to(REPO_ROOT)))
            except Exception as e:
                print(f"⚠️  Could not update {path}: {e}")

    print(f"\n✅ Project renamed: {old_id} → {new_id}")
    if renamed:
        print(f"\nRenamed files ({len(renamed)}):")
        for r in renamed:
            print(f"  {r}")
    if updated:
        print(f"\nUpdated content ({len(updated)}):")
        for u in updated:
            print(f"  {u}")
    if not renamed and not updated:
        print("  Nothing to rename — old ID not found in logs/")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    rename_project(sys.argv[1], sys.argv[2])
