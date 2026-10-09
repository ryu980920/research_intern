#!/usr/bin/env python3
"""EXP-005 stage 1: audit the 60 historical TT observations, NO SPICE/GP.

Run:
  python experiments/EXP-005_gp_surrogate_reliability/scripts/audit_tt_dataset.py
  python experiments/EXP-005_gp_surrogate_reliability/scripts/audit_tt_dataset.py --save
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parents[1]
SOURCE = EXP_DIR.parent / "EXP-003_tt_adaptive_feasible_discovery" / "raw" / "trajectory.csv"
ANALYSIS = EXP_DIR / "data" / "analysis"

PARAMS = ("wp1", "wn1", "wp3", "wn3", "wn4", "wn5", "cc")
METRICS = ("gain_min", "ibias_max", "phm_min", "t_settle_max", "ugbw_min", "vswing_min")
N_SAMPLES = 60
SETTLING_SPEC_S = 6e-6
# Diagnostic thresholds, NOT proof of broken SPICE or a particular failure cause.
LONG_SETTLING_S = 100 * SETTLING_SPEC_S


def read_source():
    if not SOURCE.is_file():
        raise FileNotFoundError(f"EXP-003 source CSV is missing: {SOURCE}")
    with SOURCE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"iteration", "design_id", "phase", "feasible", *PARAMS, *METRICS}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Source CSV is missing columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) != N_SAMPLES:
        raise ValueError(f"Expected 60 observations, found {len(rows)}")
    for i, r in enumerate(rows):
        if (r["design_id"] != f"D{i:03d}" or
                int(r["iteration"]) != i or
                r["phase"] != ("init" if i < 20 else "adaptive")):
            raise ValueError(f"EXP-003 order/phase mismatch at line {i+2}")
        if r["feasible"] not in ("True", "False"):
            raise ValueError(f"Invalid feasible flag: {r['design_id']}")
        for key in (*PARAMS, *METRICS):
            value = float(r[key])
            if not math.isfinite(value):
                raise ValueError(f"Non-finite {key} for {r['design_id']}")
            r[key] = value
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    return rows, sha


def identify_flags(r):
    flags = []
    if r["phm_min"] <= -179.0:
        flags.append("PM_NEAR_MINUS_180_DEG")
    if r["ugbw_min"] <= 1.0:
        flags.append("UGBW_AT_OR_BELOW_1_HZ")
    if r["t_settle_max"] > LONG_SETTLING_S:
        flags.append("SETTLING_ABOVE_100X_SPEC")
    if r["t_settle_max"] <= 0:
        flags.append("NONPOSITIVE_SETTLING")
    if r["ibias_max"] < 0:
        flags.append("NEGATIVE_BIAS_CURRENT")
    if r["vswing_min"] < 0:
        flags.append("NEGATIVE_SWING")
    return flags


def audit():
    rows, sha = read_source()
    flagged = []
    for row in rows:
        flags = identify_flags(row)
        if flags:
            flagged.append({"design_id": row["design_id"], "flags": "|".join(flags)})

    stats = {}
    for metric in METRICS:
        values = sorted(float(r[metric]) for r in rows)
        stats[metric] = {
            "min": min(values),
            "median": statistics.median(values),
            "max": max(values),
        }

    physical_vectors = [tuple(r[p] for p in PARAMS) for r in rows]
    duplicates = len(physical_vectors) - len(set(physical_vectors))
    summary = {
        "experiment": "EXP-005",
        "status": "dataset audit only; GP and SPICE not run",
        "source": str(SOURCE),
        "source_sha256": sha,
        "n_total": N_SAMPLES,
        "n_initial": 20,
        "n_adaptive": 40,
        "n_feasible_in_history": sum(r["feasible"] == "True" for r in rows),
        "n_duplicate_parameter_vectors": duplicates,
        "n_flagged_designs": len(flagged),
        "flag_counts": dict(Counter(flag for entry in flagged
                                    for flag in entry["flags"].split("|"))),
        "diagnostic_thresholds": {
            "settling_spec_s": SETTLING_SPEC_S,
            "settling_long_s": LONG_SETTLING_S,
            "pm_flag_below_or_equal_deg": -179.0,
            "ugbw_flag_below_or_equal_hz": 1.0,
        },
        "metric_summary": stats,
        "interpretation_warning": (
            "Flags identify values worth investigating, not confirmed "
            "simulator, measurement, or device failures."
        ),
        "planned_split": {
            "train": "D000-D039 (40)",
            "holdout": "D040-D059 (20)",
            "note": (
                "Chronological exploration-based split. Samples are adaptively "
                "selected, so validation is not an iid population estimate."
            ),
        },
    }
    return summary, flagged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--save", action="store_true",
        help="Save audited summary and flags once under data/analysis/; refuse overwrite.",
    )
    args = parser.parse_args()

    summary, flagged = audit()
    print(f"[EXP-005] Source: {summary['source']}")
    print(f"[CHECK] Rows: {summary['n_total']} | historical feasible: {summary['n_feasible_in_history']}")
    print(f"[CHECK] Duplicate design vectors: {summary['n_duplicate_parameter_vectors']}")
    print(f"[AUDIT] Flagged designs: {summary['n_flagged_designs']}")
    for key, value in sorted(summary["flag_counts"].items()):
        print(f"[AUDIT] {key}: {value}")
    for name, vals in summary["metric_summary"].items():
        print(f"[SUMMARY] {name}: min={vals['min']:.7g}, median={vals['median']:.7g}, max={vals['max']:.7g}")
    print("[NOTE] A flag is an investigation target, not proof of a simulator error.")
    print("[BUDGET] Newly simulated designs: 0; GP fits: 0")

    if args.save:
        json_path = ANALYSIS / "dataset_audit.json"
        csv_path = ANALYSIS / "anomaly_flags.csv"
        if json_path.exists() or csv_path.exists():
            raise FileExistsError(
                "EXP-005 audit outputs already exist. Preserve them; do not overwrite."
            )
        ANALYSIS.mkdir(parents=True, exist_ok=True)
        with json_path.open("x", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
            f.write("\n")
        with csv_path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["design_id", "flags"])
            writer.writeheader()
            writer.writerows(flagged)
        print(f"[CSV] Saved flagged observations -> {csv_path}")
        print(f"[JSON] Saved audit/provenance -> {json_path}")


if __name__ == "__main__":
    main()
