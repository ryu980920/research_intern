#!/usr/bin/env python3
"""EXP-005 Stage 3B — controlled sensitivity of Settling GP to target units.

GP B: original confirmed-fallback-filtered output in seconds.
GP C: EXACT same X, rows, kernel, seed and pinned ATLAS GP, but y scaled by
      1e6 (microseconds). Convert means AND posterior std back to seconds.

This is a numerical stability experiment, not a new SPICE simulation and not
a claim that all remaining settling labels are physically valid.

From ~/research_intern, in the atlas conda environment:
  python experiments/EXP-005_gp_surrogate_reliability/scripts/test_settling_gp_unit_stability.py
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
import warnings
from pathlib import Path

import numpy as np

from audit_tt_dataset import EXP_DIR, PARAMS, read_source
from compare_validity_aware_gp import (
    RESULT_CSV as STAGE3A_CSV,
    RESULT_JSON as STAGE3A_JSON,
    load_json,
    read_flags,
)
from diagnose_metric_semantics import (
    OUTPUT_CSV as FLAGS_CSV,
    OUTPUT_JSON as FLAGS_JSON,
    get_codes_and_horizons,
)
from evaluate_gp_baseline import N_TRAIN, N_TEST, SEED, Z_95, check_config

METRIC = "t_settle_max"
UNIT_FACTOR = 1e6
OUTDIR = EXP_DIR / "data" / "analysis"
OUTPUT_CSV = OUTDIR / "stage3b_settling_unit_comparison.csv"
OUTPUT_JSON = OUTDIR / "stage3b_settling_unit_summary.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_previous_b(rows, source_sha, atlas_sha, test_ids):
    prior = load_json(STAGE3A_JSON)
    if (prior["original_atlas_sha"] != atlas_sha
            or prior["raw_trajectory_sha256"] != source_sha):
        raise RuntimeError("Stage 3A and current data / ATLAS SHA do not match")
    expected = prior["metric_results"][METRIC]
    if expected["n_train_b"] != 34 or expected["n_holdout_for_both"] != 19:
        raise RuntimeError("Stage 3A Settling model used different sample sizes")
    if expected["excluded_holdout_ids_for_both"] != ["D047"]:
        raise RuntimeError("Stage 3A excluded unexpected holdout designs")
    saved = {}
    with STAGE3A_CSV.open(newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            if rec["metric"] != METRIC:
                continue
            uid = rec["design_id"]
            if uid in saved:
                raise ValueError(f"Duplicate Stage 3A Settling row: {uid}")
            saved[uid] = (float(rec["observed"]), float(rec["b_mean"]),
                          float(rec["b_std"]))
    if list(saved) != test_ids:
        raise RuntimeError("Stage 3A Settling holdout order or design IDs changed")
    by_id = {r["design_id"]: r for r in rows}
    for uid, (observed, _mu, _std) in saved.items():
        if not math.isclose(observed, by_id[uid][METRIC], rel_tol=1e-10, abs_tol=1e-14):
            raise RuntimeError(f"Stage 3A true observation changed: {uid}")
    return saved


def warning_summary(captured):
    return [
        {"category": type(w.message).__name__,
         "message": str(w.message),
         "file": str(w.filename).split("site-packages/")[-1],
         "line": w.lineno}
        for w in captured
    ]


def fit_predict(label, x_train, y_train, x_test, bounds, target, torch, gp_cls):
    # Seed is RESET for each model; only target units are varied.
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)

    model = gp_cls(
        [METRIC],
        {METRIC: target},
        {METRIC: "max"},  # settling is an upper-bounded specification
        bounds,
    )
    messages = io.StringIO()
    start = time.monotonic()
    with warnings.catch_warnings(record=True) as fit_warnings:
        warnings.simplefilter("always")
        with contextlib.redirect_stdout(messages):
            model.fit(x_train, {METRIC: y_train}, fom_values=None, incremental=False)
    elapsed = time.monotonic() - start
    fit_msgs = messages.getvalue().splitlines()
    fallback = any(f"MLL fit failed for {METRIC}:" in l for l in fit_msgs)

    with warnings.catch_warnings(record=True) as pred_warnings:
        warnings.simplefilter("always")
        mu, std = model.predict(x_test)
    mu = np.asarray(mu[METRIC], dtype=float)
    std = np.asarray(std[METRIC], dtype=float)

    if not (np.isfinite(mu).all() and np.isfinite(std).all() and
            (std > 0).all()):
        raise RuntimeError(f"Non-finite predictions from GP {label}")
    return {
        "mu": mu, "std": std, "fit_seconds": elapsed, "device": str(model.device),
        "fit_stdout": fit_msgs, "mll_fallback_detected": fallback,
        "fit_warnings": warning_summary(fit_warnings),
        "predict_warnings": warning_summary(pred_warnings),
    }


def measures(true_s, mu_s, std_s):
    residual = true_s - mu_s
    return {
        "n": len(true_s),
        "mae_us": float(np.mean(np.abs(residual)) * 1e6),
        "rmse_us": float(np.sqrt(np.mean(residual**2)) * 1e6),
        "negative_mean_count": int(np.count_nonzero(mu_s < 0)),
        "approx_95_interval_hit_rate": float(
            np.mean(np.abs(residual) <= Z_95 * std_s)),
        "std_min_us": float(np.min(std_s) * 1e6),
        "std_median_us": float(np.median(std_s) * 1e6),
        "std_max_us": float(np.max(std_s) * 1e6),
        "std_equal_10us_count": int(np.count_nonzero(
            np.isclose(std_s * 1e6, 10.0, rtol=1e-9, atol=1e-9))),
    }


def main():
    # Previous outputs are protected. Never rerun into the same result paths.
    for dst in (OUTPUT_CSV, OUTPUT_JSON):
        if dst.exists():
            raise FileExistsError(f"Existing Stage 3B result: {dst}")

    rows, source_sha = read_source()
    if len(rows) != N_TRAIN + N_TEST:
        raise RuntimeError(f"Expected {N_TRAIN+N_TEST} historical designs")
    bounds, targets, atlas_sha = check_config()
    metadata = get_codes_and_horizons()
    if metadata["atlas_sha"] != atlas_sha:
        raise RuntimeError("ATLAS source and YAML SHA mismatch")
    flagged, audit = read_flags(rows, source_sha, metadata)
    bad_train = [r["design_id"] for r in rows[:N_TRAIN]
                 if flagged[r["design_id"]][METRIC]]
    good_train = [r for r in rows[:N_TRAIN]
                  if not flagged[r["design_id"]][METRIC]]
    good_test = [r for r in rows[N_TRAIN:]
                 if not flagged[r["design_id"]][METRIC]]
    test_ids = [r["design_id"] for r in good_test]
    if (len(good_train), len(good_test), bad_train) != (
        34, 19, ["D013", "D014", "D015", "D016", "D017", "D023"]
    ):
        raise RuntimeError("Validity mask differs from previous Stage 3A")
    original_b = get_previous_b(rows, source_sha, atlas_sha, test_ids)

    x_train = np.asarray([[r[p] for p in PARAMS] for r in good_train])
    x_test = np.asarray([[r[p] for p in PARAMS] for r in good_test])
    true_s = np.asarray([r[METRIC] for r in good_test], dtype=float)
    y_train_s = np.asarray([r[METRIC] for r in good_train], dtype=float)
    if not np.isfinite(y_train_s).all() or np.any(y_train_s <= 0):
        raise RuntimeError("Unexpected training Settling label")
    if not np.isfinite(true_s).all():
        raise RuntimeError("Nonfinite holdout Settling label")

    atlas_root = Path(os.environ.get("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
    sys.path.insert(0, str(atlas_root))
    import torch
    from topbo.gp_model import GPSurrogate

    # The YAML supplies a fixed upper-bound target [low,high]; the GP 'fit'
    # does not depend on this number, but keep its units consistent anyway.
    spec_range = targets[METRIC]
    threshold_s = float(spec_range[0]) if isinstance(spec_range, (list, tuple)) else None
    if threshold_s is None:
        raise RuntimeError("Unexpected fixed YAML Settling spec structure")
    # The only independent variable across the two runs is the output scale.
    print("=" * 73, flush=True)
    print("EXP-005 Stage 3B | Settling GP units: seconds (B) vs microseconds (C)",
          flush=True)
    print("Same 34 train / 19 holdout, same ATLAS GP, seed 42 | SPICE=0",
          flush=True)
    print("=" * 73, flush=True)
    print(f"[CHECK] source={source_sha[:12]}, atlas={atlas_sha[:12]}", flush=True)
    print("[MASK] excluded train=" + ", ".join(bad_train)
          + " | excluded test=D047", flush=True)

    b = fit_predict("B", x_train, y_train_s, x_test, bounds,
                    threshold_s, torch, GPSurrogate)
    c = fit_predict("C", x_train, y_train_s * UNIT_FACTOR, x_test, bounds,
                    threshold_s * UNIT_FACTOR, torch, GPSurrogate)
    # Convert C posterior std as well as mean to seconds for comparison.
    b_mu_s, b_sd_s = b["mu"], b["std"]
    c_mu_s, c_sd_s = c["mu"] / UNIT_FACTOR, c["std"] / UNIT_FACTOR
    stored_b_mu_s = np.array([original_b[k][1] for k in test_ids])
    stored_b_sd_s = np.array([original_b[k][2] for k in test_ids])

    saved_b_error_us = float(np.max(np.abs(b_mu_s - stored_b_mu_s)) * 1e6)
    saved_b_std_error_us = float(np.max(np.abs(b_sd_s - stored_b_sd_s)) * 1e6)
    rows_out = []
    for i, uid in enumerate(test_ids):
        rows_out.append({
            "design_id": uid, "observed_us": float(true_s[i]*1e6),
            "stage3a_b_mean_us": float(stored_b_mu_s[i]*1e6),
            "stage3a_b_std_us": float(stored_b_sd_s[i]*1e6),
            "stage3b_b_mean_us": float(b_mu_s[i]*1e6),
            "stage3b_b_std_us": float(b_sd_s[i]*1e6),
            "stage3b_c_mean_us": float(c_mu_s[i]*1e6),
            "stage3b_c_std_us": float(c_sd_s[i]*1e6),
            "b_abs_error_us": float(abs(true_s[i] - b_mu_s[i])*1e6),
            "c_abs_error_us": float(abs(true_s[i] - c_mu_s[i])*1e6),
            "b_near_10us_std": bool(np.isclose(b_sd_s[i]*1e6, 10, rtol=1e-9, atol=1e-9)),
            "c_near_10us_std": bool(np.isclose(c_sd_s[i]*1e6, 10, rtol=1e-9, atol=1e-9)),
        })

    summary = {
        "experiment": "EXP-005",
        "stage": "3B target_unit_numerical_stability",
        "status": "completed",
        "atlas_sha": atlas_sha,
        "raw_trajectory_sha256": source_sha,
        "stage3a_csv_sha256": digest(STAGE3A_CSV),
        "stage3a_summary_sha256": digest(STAGE3A_JSON),
        "metric_semantics_audit_sha256": digest(FLAGS_JSON),
        "metric_semantics_flags_sha256": digest(FLAGS_CSV),
        "metric": METRIC, "seed_per_fit": SEED,
        "n_train": len(good_train), "n_holdout": len(good_test),
        "excluded_train_ids": bad_train, "excluded_holdout_ids": ["D047"],
        "new_spice_evaluations": 0, "new_gp_fits": 2,
        "unit_scale": UNIT_FACTOR,
        "model_B_train_unit": "seconds",
        "model_C_train_unit": "microseconds",
        "common_report_unit": "microseconds",
        "b": {k: v for k, v in b.items() if k not in ("mu", "std")},
        "c": {k: v for k, v in c.items() if k not in ("mu", "std")},
        "b_metrics": measures(true_s, b_mu_s, b_sd_s),
        "c_metrics": measures(true_s, c_mu_s, c_sd_s),
        "delta_c_minus_b_mae_us": (
            measures(true_s, c_mu_s, c_sd_s)["mae_us"]
            - measures(true_s, b_mu_s, b_sd_s)["mae_us"]),
        "max_abs_b_refit_vs_stage3a_mean_diff_us": saved_b_error_us,
        "max_abs_b_refit_vs_stage3a_std_diff_us": saved_b_std_error_us,
        "max_abs_c_vs_b_mean_diff_us": float(
            np.max(np.abs(c_mu_s - b_mu_s)) * 1e6),
        "max_abs_c_vs_b_std_diff_us": float(
            np.max(np.abs(c_sd_s - b_sd_s)) * 1e6),
        "warnings_interpretation": (
            "Recorded warning messages are numerical implementation diagnostics. "
            "Exact 10-us posterior std may be GPyTorch 1e-10 variance clipping, "
            "but do not claim this is established by coincidence alone."
        ),
        "limitations": [
            "Confirmed invalid labels alone were removed; remaining labels lack waveform validity flags.",
            "The holdout is adaptively chosen, not independent or iid.",
            "Unit scaling is an input to the same GP implementation, not a new physical model.",
            "A unit-sensitive change suggests numeric effects but does not prove their source.",
            "The refitted B may differ from historical B on different GPU/library versions.",
        ],
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0]))
        writer.writeheader()
        writer.writerows(rows_out)
        f.flush()
        os.fsync(f.fileno())
    with OUTPUT_JSON.open("x", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    print(f"[GP B / s] MAE={summary['b_metrics']['mae_us']:.6g} us "
          f"| std==10us {summary['b_metrics']['std_equal_10us_count']}/19 "
          f"| prediction warnings={len(b['predict_warnings'])}", flush=True)
    print(f"[GP C / us] MAE={summary['c_metrics']['mae_us']:.6g} us "
          f"| std==10us {summary['c_metrics']['std_equal_10us_count']}/19 "
          f"| prediction warnings={len(c['predict_warnings'])}", flush=True)
    print(f"[REPRO B] Max |new B - Stage 3A B| mean={saved_b_error_us:.6g} us, "
          f"std={saved_b_std_error_us:.6g} us", flush=True)
    print(f"[UNITS] Max |C - B| mean={summary['max_abs_c_vs_b_mean_diff_us']:.6g} us, "
          f"std={summary['max_abs_c_vs_b_std_diff_us']:.6g} us", flush=True)
    for label, result in (("B", b), ("C", c)):
        if result["mll_fallback_detected"]:
            print(f"[WARNING] GP {label}: MLL fit fallback recorded", flush=True)
        for warning in result["predict_warnings"]:
            print(f"[PREDICT WARNING / {label}] {warning['category']}: "
                  f"{warning['message']}", flush=True)
        print(f"[FIT] GP {label} seconds={result['fit_seconds']:.2f} "
              f"device={result['device']}", flush=True)
    print(f"[SAVED] {OUTPUT_CSV}", flush=True)
    print(f"[SAVED] {OUTPUT_JSON}", flush=True)
    print("[BUDGET] GP fits=2; New SPICE=0", flush=True)


if __name__ == "__main__":
    main()
