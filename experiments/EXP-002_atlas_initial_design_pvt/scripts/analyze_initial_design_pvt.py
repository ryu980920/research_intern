#!/usr/bin/env python3
"""Analyze the combined EXP-001 + EXP-002 PVT baseline dataset.

Reads the committed corner-wise metric CSVs and regenerates the compact
analysis tables stored under EXP-002/data/analysis/.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

EXP2_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EXP2_DIR.parents[1]
EXP1_METRICS = REPO_ROOT / "experiments" / "EXP-001_pvt_init_params_baseline" / "data" / "corner_metrics.csv"
EXP2_METRICS = EXP2_DIR / "data" / "corner_metrics.csv"
OUT_DIR = EXP2_DIR / "data" / "analysis"

CONSTRAINTS = {
    "gain_min": ("min", 300.0),
    "ibias_max": ("max", 1e-3),
    "phm_min": ("min", 60.0),
    "t_settle_max": ("max", 6e-6),
    "ugbw_min": ("min", 2e7),
    "vswing_min": ("min", 0.3),
}
METRICS = list(CONSTRAINTS)


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for metric in METRICS:
            row[metric] = float(row[metric])
        row["feasible"] = row["feasible"].strip().lower() == "true"
    return rows


def passes(row: dict, metric: str) -> bool:
    direction, target = CONSTRAINTS[metric]
    value = row[metric]
    return value >= target if direction == "min" else value <= target


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = read_rows(EXP1_METRICS) + read_rows(EXP2_METRICS)

    design_ids = sorted({row["design_id"] for row in rows})
    corners = list(dict.fromkeys(row["corner"] for row in rows))

    if len(rows) != 340 or len(design_ids) != 20 or len(corners) != 17:
        raise RuntimeError(
            f"Expected 340 rows / 20 designs / 17 corners, got "
            f"{len(rows)} / {len(design_ids)} / {len(corners)}"
        )

    by_design = defaultdict(list)
    by_corner = defaultdict(list)
    for row in rows:
        by_design[row["design_id"]].append(row)
        by_corner[row["corner"]].append(row)

    design_summary = []
    for design_id in design_ids:
        drows = by_design[design_id]
        passed_counts = [
            sum(passes(row, metric) for metric in METRICS)
            for row in drows
        ]
        design_summary.append({
            "design_id": design_id,
            "n_feasible_corners": sum(row["feasible"] for row in drows),
            "n_corners": len(drows),
            "avg_specs_passed": f"{sum(passed_counts) / len(passed_counts):.4f}",
            "max_specs_passed": max(passed_counts),
        })

    corner_summary = []
    for corner in corners:
        crows = by_corner[corner]
        corner_summary.append({
            "corner": corner,
            "n_feasible_designs": sum(row["feasible"] for row in crows),
            "n_designs": len(crows),
            "gain_pass": sum(passes(row, "gain_min") for row in crows),
            "ibias_pass": sum(passes(row, "ibias_max") for row in crows),
            "phm_pass": sum(passes(row, "phm_min") for row in crows),
            "t_settle_pass": sum(passes(row, "t_settle_max") for row in crows),
            "ugbw_pass": sum(passes(row, "ugbw_min") for row in crows),
            "vswing_pass": sum(passes(row, "vswing_min") for row in crows),
        })

    failure_summary = []
    for metric in METRICS:
        fail_count = sum(not passes(row, metric) for row in rows)
        failure_summary.append({
            "metric": metric,
            "fail_count": fail_count,
            "fail_rate": f"{fail_count / len(rows):.6f}",
        })

    worst_rows = []
    for metric in METRICS:
        direction, _ = CONSTRAINTS[metric]
        counts = Counter()
        for design_id in design_ids:
            drows = by_design[design_id]
            key = lambda row: row[metric]
            worst = min(drows, key=key) if direction == "min" else max(drows, key=key)
            counts[worst["corner"]] += 1
        for corner, frequency in counts.most_common():
            worst_rows.append({
                "metric": metric,
                "corner": corner,
                "frequency": frequency,
            })

    near_feasible_tt = []
    for row in by_corner["TT_3.3V_27C"]:
        failed = [metric for metric in METRICS if not passes(row, metric)]
        n_passed = len(METRICS) - len(failed)
        if n_passed >= 5:
            near_feasible_tt.append({
                "design_id": row["design_id"],
                "corner": row["corner"],
                "n_specs_passed": n_passed,
                "failed_specs": ";".join(failed),
            })

    write_csv(
        OUT_DIR / "design_summary.csv",
        ["design_id", "n_feasible_corners", "n_corners", "avg_specs_passed", "max_specs_passed"],
        design_summary,
    )
    write_csv(
        OUT_DIR / "corner_summary.csv",
        ["corner", "n_feasible_designs", "n_designs", "gain_pass", "ibias_pass",
         "phm_pass", "t_settle_pass", "ugbw_pass", "vswing_pass"],
        corner_summary,
    )
    write_csv(
        OUT_DIR / "constraint_failure_summary.csv",
        ["metric", "fail_count", "fail_rate"],
        failure_summary,
    )
    write_csv(
        OUT_DIR / "worst_corner_frequency.csv",
        ["metric", "corner", "frequency"],
        worst_rows,
    )
    write_csv(
        OUT_DIR / "near_feasible_tt.csv",
        ["design_id", "corner", "n_specs_passed", "failed_specs"],
        near_feasible_tt,
    )

    print(f"Analyzed {len(rows)} corner evaluations.")
    print(f"Feasible evaluations: {sum(row['feasible'] for row in rows)} / {len(rows)}")
    print(f"Analysis tables written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
