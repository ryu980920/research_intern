#!/usr/bin/env python3
"""EXP-005 Stage 3A: compare original GP (A) vs confirmed-fallback-filtered GP (B).

No SPICE, no changes to pinned ATLAS or EXP-003 data.
- A: read the already-fitted original-GP holdout predictions (Stage 2).
- B: fit an original ATLAS GPSurrogate independently for each affected spec,
     dropping *only confirmed* invalid labels from that spec's training data.
- Compare A/B on the SAME holdout rows, excluding confirmed-invalid targets.
Other three metrics remain unchanged and are not refitted.

Run in the atlas conda environment, from ~/research_intern:
  python experiments/EXP-005_gp_surrogate_reliability/scripts/compare_validity_aware_gp.py
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

from audit_tt_dataset import EXP_DIR, METRICS, PARAMS, read_source
from evaluate_gp_baseline import (
    N_TRAIN, N_TEST, PRED_PATH as BASELINE_PRED, SUMMARY_PATH as BASELINE_SUMMARY,
    SEED, Z_95, check_config,
)
from diagnose_metric_semantics import (
    OUTPUT_CSV as FLAGS_CSV, OUTPUT_JSON as FLAGS_JSON, get_codes_and_horizons,
)

TARGET_METRICS = ("phm_min", "ugbw_min", "t_settle_max")
UNITS = {"phm_min": ("deg", 1.0), "ugbw_min": ("MHz", 1e-6),
         "t_settle_max": ("us", 1e6)}
OUT_DIR = EXP_DIR / "data" / "analysis"
RESULT_CSV = OUT_DIR / "validity_aware_gp_comparison.csv"
RESULT_JSON = OUT_DIR / "validity_aware_gp_summary.json"


def load_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"Missing prerequisite: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_flags(rows, source_sha, semantic_meta):
    saved = load_json(FLAGS_JSON)
    for key in ("atlas_sha", "extractor_sha256", "netlist_sha256", "source_sha256"):
        expected = source_sha if key == "source_sha256" else semantic_meta[key]
        if saved.get(key) != expected:
            raise RuntimeError(f"Metric semantics audit provenance mismatch: {key}")
    if abs(float(saved["transient_stop_s"]) - semantic_meta["transient_stop_s"]) > 1e-15:
        raise RuntimeError("Transient simulation stop differs from the checked source")
    with FLAGS_CSV.open(newline="", encoding="utf-8") as f:
        flags = list(csv.DictReader(f))
    if len(flags) != len(rows):
        raise ValueError("Metric semantics flag table has the wrong number of rows")

    mapping = {}
    tstop, fstart = semantic_meta["transient_stop_s"], semantic_meta["ac_start_hz"]
    for i, (r, flag) in enumerate(zip(rows, flags)):
        uid = r["design_id"]
        expected_split = "train" if i < N_TRAIN else "holdout"
        if flag["design_id"] != uid or flag["split"] != expected_split:
            raise ValueError(f"Row order or split mismatch for {uid}")
        valid_truth = {"True": True, "False": False}
        try:
            settle_bad = valid_truth[flag["settling_exceeds_transient_window"]]
            ac_bad = valid_truth[flag["ac_missing_crossing_sentinel_pair"]]
        except KeyError:
            raise ValueError(f"Invalid flags for {uid}") from None
        if settle_bad != (r["t_settle_max"] > tstop + 1e-12):
            raise RuntimeError(f"Settling flag does not match original observation for {uid}")
        if ac_bad != (r["ugbw_min"] == fstart and r["phm_min"] == -180.0):
            raise RuntimeError(f"AC flag does not match original observation for {uid}")
        mapping[uid] = {"phm_min": ac_bad, "ugbw_min": ac_bad,
                        "t_settle_max": settle_bad}
    return mapping, saved


def read_baseline(rows, source_sha, atlas_sha):
    saved = load_json(BASELINE_SUMMARY)
    if saved.get("source_sha256") != source_sha or saved.get("atlas_sha") != atlas_sha:
        raise RuntimeError("Original GP baseline was fit against different data/code")
    if (saved.get("n_train") != N_TRAIN or saved.get("n_holdout") != N_TEST
            or saved.get("holdout_ids") != "D040-D059"):
        raise RuntimeError("Original GP baseline used a different train/test split")
    with BASELINE_PRED.open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    if len(data) != N_TEST * len(METRICS):
        raise RuntimeError("Original GP prediction table does not contain 120 rows")
    ids = {r["design_id"]: r for r in rows[N_TRAIN:]}
    baseline = {}
    for r in data:
        metric, uid = r["metric"], r["design_id"]
        if uid not in ids or metric not in METRICS or (uid, metric) in baseline:
            raise RuntimeError(f"Duplicate/unexpected baseline prediction for {uid}/{metric}")
        obs = float(r["observed"])
        if not math.isclose(obs, ids[uid][metric], rel_tol=1e-10, abs_tol=1e-14):
            raise RuntimeError(f"Baseline observation mismatch for {uid}/{metric}")
        mu, sd = float(r["predicted_mean"]), float(r["predicted_std"])
        if not (math.isfinite(mu) and math.isfinite(sd) and sd > 0):
            raise RuntimeError(f"Invalid baseline estimate for {uid}/{metric}")
        baseline[(uid, metric)] = (mu, sd)
    return baseline, saved


def summarize(records, variant):
    residual = np.array([
        x["observed"] - x[f"{variant}_mean"] for x in records
    ], dtype=float)
    sd = np.array([x[f"{variant}_std"] for x in records], dtype=float)
    return {
        "n": len(records),
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual * residual))),
        "median_abs_error": float(np.median(np.abs(residual))),
        "approx95_interval_hit_rate": float(np.mean(np.abs(residual) <= Z_95 * sd)),
        "negative_predicted_means": int(sum(x[f"{variant}_mean"] < 0 for x in records)),
    }


def main():
    for p in (RESULT_CSV, RESULT_JSON):
        if p.exists():
            raise FileExistsError(f"Comparison already exists; never overwrite: {p}")

    rows, source_sha = read_source()
    if len(rows) != N_TRAIN + N_TEST:
        raise RuntimeError(f"Unexpected dataset size: {len(rows)}")
    bounds, targets, atlas_sha = check_config()
    semantic_meta = get_codes_and_horizons()
    if semantic_meta["atlas_sha"] != atlas_sha:
        raise RuntimeError("Inconsistent pinned ATLAS source")
    bad, validity_audit = read_flags(rows, source_sha, semantic_meta)
    original, baseline_audit = read_baseline(rows, source_sha, atlas_sha)

    # Keep all original measurements; validity masking only affects GP fitting
    # and like-for-like evaluation of quantitatively interpretable targets.
    X = np.asarray([[r[p] for p in PARAMS] for r in rows], dtype=float)
    if np.any(X < bounds[:, 0]) or np.any(X > bounds[:, 1]):
        raise RuntimeError("Historical design coordinates exceed YAML bounds")

    sys.path.insert(0, str(Path(os.environ.get("ATLAS_ROOT", "~/atlas")).expanduser().resolve()))
    import torch
    from topbo.gp_model import GPSurrogate
    from topbo.utils import parse_spec_constraints

    _, constraints, directions = parse_spec_constraints(targets)
    results, report = [], {}
    total_fit = 0.0
    print("=" * 67, flush=True)
    print("EXP-005 Stage 3A | GP A (original) vs GP B (fallback excluded)", flush=True)
    print("A: saved original ATLAS GP baseline | B: original GP code, filtered", flush=True)
    print("New SPICE calls: 0 | Original raw measurements are untouched", flush=True)
    print("=" * 67, flush=True)
    print(f"[CHECK] SOURCE SHA256={source_sha[:12]} | ATLAS SHA={atlas_sha[:12]}", flush=True)

    for metric in TARGET_METRICS:
        train_ids = [r["design_id"] for r in rows[:N_TRAIN] if not bad[r["design_id"]][metric]]
        test_rows = [r for r in rows[N_TRAIN:] if not bad[r["design_id"]][metric]]
        invalid_train = [r["design_id"] for r in rows[:N_TRAIN] if bad[r["design_id"]][metric]]
        invalid_test = [r["design_id"] for r in rows[N_TRAIN:] if bad[r["design_id"]][metric]]
        if len(train_ids) < 10 or len(test_rows) < 10:
            raise RuntimeError(f"Not enough unflagged rows to model {metric}")

        train_indices = [i for i, r in enumerate(rows[:N_TRAIN]) if not bad[r["design_id"]][metric]]
        x_train = X[train_indices]
        y_train = np.asarray([rows[i][metric] for i in train_indices], dtype=float)
        x_eval = np.asarray([[r[p] for p in PARAMS] for r in test_rows], dtype=float)

        # The SAME pinned GP architecture/fit is used for each metric, but
        # this time no detected invalid labels reach its per-metric fit.
        random.seed(SEED)
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED)
        model = GPSurrogate(
            [metric], {metric: constraints[metric]},
            {metric: directions[metric]}, bounds,
        )
        capture = io.StringIO()
        fit_start = time.monotonic()
        with contextlib.redirect_stdout(capture):
            model.fit(x_train, {metric: y_train}, fom_values=None, incremental=False)
        elapsed = time.monotonic() - fit_start
        total_fit += elapsed
        messages = capture.getvalue().strip().splitlines()
        fallback = any(f"MLL fit failed for {metric}:" in s for s in messages)
        print(f"[{metric}] GP(B) train={len(train_ids)}/{N_TRAIN}, "
              f"holdout={len(test_rows)}/{N_TEST}; fit={elapsed:.2f}s; "
              f"MLL_fallback={fallback}", flush=True)
        if fallback:
            for line in messages:
                if "MLL fit failed" in line:
                    print(f"[WARNING] {line}", flush=True)

        means, stds = model.predict(x_eval)
        current = []
        for i, r in enumerate(test_rows):
            uid = r["design_id"]
            a_mean, a_std = original[(uid, metric)]
            b_mean, b_std = float(means[metric][i]), float(stds[metric][i])
            y = float(r[metric])
            if not (math.isfinite(b_mean) and math.isfinite(b_std) and b_std > 0):
                raise RuntimeError(f"Invalid filtered-GP result for {uid}/{metric}")
            rec = {
                "design_id": uid, "metric": metric,
                "observed": y,
                "a_mean": a_mean, "a_std": a_std,
                "b_mean": b_mean, "b_std": b_std,
                "a_abs_error": abs(y - a_mean),
                "b_abs_error": abs(y - b_mean),
                "a_approx95_hit": abs(y - a_mean) <= Z_95*a_std,
                "b_approx95_hit": abs(y - b_mean) <= Z_95*b_std,
                "holdout_label_status": "NOT_FLAGGED_BUT_NOT_VERIFIED_WITH_WAVEFORM",
            }
            current.append(rec)
            results.append(rec)
        a, b = summarize(current, "a"), summarize(current, "b")
        unit, scale = UNITS[metric]
        delta_pct = 100.0 * (a["mae"] - b["mae"]) / a["mae"] if a["mae"] > 0 else None
        report[metric] = {
            "units": unit,
            "n_train_a": N_TRAIN,
            "n_train_b": len(train_ids),
            "n_holdout_for_both": len(test_rows),
            "excluded_train_ids_b": invalid_train,
            "excluded_holdout_ids_for_both": invalid_test,
            "a_original_baseline": a,
            "b_confirmed_fallbacks_excluded": b,
            "mae_reduction_pct_positive_means_improved": delta_pct,
            "b_fit_seconds": elapsed,
            "b_fit_fallback_detected": fallback,
            "b_fit_stdout": messages,
        }
        arrow = "lower" if b["mae"] < a["mae"] else "higher or equal"
        print(
            f"[COMPARE {metric}] MAE A={a['mae']*scale:.6g} {unit}, "
            f"B={b['mae']*scale:.6g} {unit} ({arrow} B); "
            f"approx95 coverage A={a['approx95_interval_hit_rate']:.0%}, "
            f"B={b['approx95_interval_hit_rate']:.0%}",
            flush=True,
        )
    report_json = {
        "experiment": "EXP-005",
        "stage": "3A confirmed_invalid_label_filtering",
        "status": "completed",
        "original_atlas_sha": atlas_sha,
        "raw_trajectory_sha256": source_sha,
        "metric_semantics_audit_sha256": hashlib.sha256(FLAGS_JSON.read_bytes()).hexdigest(),
        "metric_semantics_flags_sha256": hashlib.sha256(FLAGS_CSV.read_bytes()).hexdigest(),
        "baseline_predictions_sha256": hashlib.sha256(BASELINE_PRED.read_bytes()).hexdigest(),
        "baseline_summary_sha256": hashlib.sha256(BASELINE_SUMMARY.read_bytes()).hexdigest(),
        "split_train": "D000-D039",
        "split_holdout": "D040-D059",
        "seed_for_b_per_metric": SEED,
        "stage2_baseline_fit_fallbacks": baseline_audit.get("mll_fallback_spec_names"),
        "n_new_spice": 0,
        "gp_b_total_fit_seconds": total_fit,
        "metric_results": report,
        "limitations": [
            "Small/normal-looking settling values may still be extractor fallback values.",
            "Only confirmed invalid labels are excluded. Failed-design metadata must be "
            "preserved separately to prevent proposing bad candidates.",
            "The A model uses 40 training labels and the B model fewer, by design. "
            "Both are scored on the same metric-specific unflagged holdout designs.",
            "GP A uses recorded Stage-2 predictions; GP B refits pinned single-spec "
            "GPSurrogate with identical YAML bounds/kernel but a filtered dataset.",
            "The data were adaptively chosen. N=19 unflagged holdout observations "
            "are not an independent random generalization benchmark.",
            "Both A and B may predict performance for physically invalid designs. "
            "Classification or censored-output handling is needed before deploying "
            "model B for ATLAS candidate selection.",
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    columns = ["design_id", "metric", "observed", "a_mean", "a_std",
               "b_mean", "b_std", "a_abs_error", "b_abs_error",
               "a_approx95_hit", "b_approx95_hit", "holdout_label_status"]
    with RESULT_CSV.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
        f.flush()
        os.fsync(f.fileno())
    with RESULT_JSON.open("x", encoding="utf-8") as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    print(f"[SAVED] {RESULT_CSV}", flush=True)
    print(f"[SAVED] {RESULT_JSON}", flush=True)
    print("[BUDGET] GP(B) fits=3; new SPICE=0", flush=True)
    print("[NOTE] Small settling labels are not proven valid without waveform checks", flush=True)


if __name__ == "__main__":
    main()
