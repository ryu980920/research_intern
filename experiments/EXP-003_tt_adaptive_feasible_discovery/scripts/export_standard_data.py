#!/usr/bin/env python3
"""Rebuild the standard EXP-003 design/metric CSVs from the raw TT trajectory.

This never launches SPICE and refuses to overwrite existing research data.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RAW_TRAJECTORY = EXPERIMENT_DIR / "raw" / "trajectory.csv"
DATA_DIR = EXPERIMENT_DIR / "data"

PARAMS = ["wp1", "wn1", "wp3", "wn3", "wn4", "wn5", "cc"]
METRICS = [
    "gain_min", "ibias_max", "phm_min",
    "t_settle_max", "ugbw_min", "vswing_min",
]
CORNER = "TT_3.3V_27C"


def export_tables(source: Path = RAW_TRAJECTORY, output_dir: Path = DATA_DIR):
    """Generate standard linked tables, preserving numerical strings exactly."""
    source = Path(source)
    output_dir = Path(output_dir)

    design_path = output_dir / "design_points.csv"
    metric_path = output_dir / "corner_metrics.csv"

    # Check both outputs BEFORE creating either one. A rerun must not clobber
    # an earlier experiment's already committed measurement tables.
    for path in (design_path, metric_path):
        if path.exists():
            raise FileExistsError(
                f"Refusing to overwrite an existing research dataset: {path}"
            )

    with source.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = set(["iteration", "design_id", "phase", "feasible"]
                       + PARAMS + METRICS)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing trajectory columns: {sorted(missing)}")
        rows = list(reader)

    if not rows:
        raise ValueError("Empty trajectory: no evaluated design to export")

    for i, row in enumerate(rows):
        expected_id = f"D{i:03d}"
        expected_phase = "init" if i < 20 else "adaptive"
        if (row["design_id"] != expected_id
                or int(row["iteration"]) != i
                or row["phase"] != expected_phase):
            raise ValueError(f"Unexpected iteration/design/phase at row {i}")
        if row["feasible"] not in ("True", "False"):
            raise ValueError(f"Invalid feasibility value at {expected_id}")

    output_dir.mkdir(parents=True, exist_ok=True)
    # Separate parameter and metric tables, linked by design_id. TT-only
    # explicitly records its evaluated corner to match EXP-001/002 schema.
    with design_path.open("x", newline="", encoding="utf-8") as f:
        fields = ["design_id", *PARAMS]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row[name] for name in fields})

    with metric_path.open("x", newline="", encoding="utf-8") as f:
        fields = ["design_id", "corner", *METRICS, "feasible"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **{name: row[name] for name in fields if name != "corner"},
                "corner": CORNER,
            })

    print(f"[EXPORT] {len(rows)} designs -> {design_path}", flush=True)
    print(f"[EXPORT] {len(rows)} TT metric rows -> {metric_path}", flush=True)
    return design_path, metric_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=RAW_TRAJECTORY)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    export_tables(args.source, args.output_dir)


if __name__ == "__main__":
    main()
