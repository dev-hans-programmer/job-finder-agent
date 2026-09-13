import csv
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: check_load_test.py STATS_CSV MAX_FAILURE_PERCENT MAX_P95_MS")
        return 2
    stats_path = Path(sys.argv[1])
    max_failures = float(sys.argv[2])
    max_p95 = float(sys.argv[3])
    rows = list(csv.DictReader(stats_path.open(newline="")))
    total = next((row for row in rows if row.get("Name") == "Aggregated"), None)
    if total is None:
        print("Aggregated row not found in load-test statistics")
        return 2
    failures = float(total["Failure%"])
    p95 = float(total["95%"])
    print(f"load-test thresholds: failure={failures:.2f}% p95={p95:.0f}ms")
    if failures > max_failures or p95 > max_p95:
        print("Load-test thresholds failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
