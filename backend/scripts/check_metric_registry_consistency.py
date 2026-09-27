"""Architecture v2 Stage 5 consistency check: every metric_id every sector
framework's key_metrics() declares should have a matching entry in
app/metrics/registry.py (built in Stage 0 by walking these same files'
ASTs). If this ever reports a gap, either a sector file added a new
SectorMetric since Stage 0's registry was generated, or a typo diverged the
two. Not run automatically (no startup-time cost/risk added to the app) —
run manually after touching any app/sectors/*.py file.

Usage: cd backend && .venv/bin/python scripts/check_metric_registry_consistency.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.metrics.registry import METRIC_REGISTRY
from app.sectors.registry import list_frameworks, get_framework


def main() -> int:
    gaps = []
    for entry in list_frameworks():
        sector_name = entry["sector_name"]
        framework = get_framework(sector_name)
        required = framework.required_metric_ids()
        unregistered = required.get("unregistered", [])
        for metric_id in unregistered:
            gaps.append((sector_name, metric_id))

    if not gaps:
        print(f"OK — every metric across {len(list_frameworks())} sector frameworks "
              f"is present in METRIC_REGISTRY ({len(METRIC_REGISTRY)} entries).")
        return 0

    print(f"FOUND {len(gaps)} metric(s) not in app/metrics/registry.py:")
    for sector_name, metric_id in gaps:
        print(f"  {sector_name:20s} -> '{metric_id}'")
    print("\nAdd these to METRIC_REGISTRY (app/metrics/registry.py) or fix the typo in the sector file.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
