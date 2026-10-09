#!/usr/bin/env python3
"""EXP-005 stage 2 — historical ATLAS GP baseline holdout evaluation (NO SPICE).

Train on EXP-003 D000–D039 and predict D040–D059. The predictions are
genuinely out-of-training; the test labels are only used after GP.predict().
This is a chronological, adaptively selected test set, NOT an iid estimate.

From the research repository root, in the (atlas) conda environment:
  python experiments/EXP-005_gp_surrogate_reliability/scripts/evaluate_gp_baseline.py
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from audit_tt_dataset import EXP_DIR, METRICS, PARAMS, identify_flags, read_source

ATLAS_ROOT = Path(os.environ.get("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
ATLAS_SHA = "dd23c5ba7beb598909be593e4a84c81dab92cc69"
YAML_FILE = ATLAS_ROOT / "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"
N_TRAIN = 40
N_TEST = 20
SEED = 42
Z_95 = 1.96
OUTDIR = EXP_DIR / "data" / "analysis"
PRED_PATH = OUTDIR / "gp_baseline_holdout_predictions.csv"
SUMMARY_PATH = OUTDIR / "gp_baseline_holdout_summary.json"


def check_config():
    if not ATLAS_ROOT.is_dir():
        raise FileNotFoundError(f"ATLAS_ROOT does not exist: {ATLAS_ROOT}")
    sha = subprocess.check_output(
        ["git", "-C", str(ATLAS_ROOT), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if sha != ATLAS_SHA:
        raise RuntimeError(f"Wrong ATLAS commit: expected {ATLAS_SHA}, got {sha}")
    if not YAML_FILE.is_file():
        raise FileNotFoundError(f"ATLAS YAML file not found: {YAML_FILE}")
    # The pinned ATLAS YAML uses !!python/tuple, supported by FullLoader.
    import yaml
    with YAML_FILE.open(encoding="utf-8") as f:
        circuit = yaml.full_load(f)
    yaml_names = tuple(circuit["params"].keys())
    if yaml_names != PARAMS:
        raise RuntimeError(f"Parameter order mismatch: YAML {yaml_names} vs CSV {PARAMS}")
    bounds = np.asarray([circuit["params"][k] for k in PARAMS], dtype=float)
    target_specs = circuit["target_specs"]
    if set(target_specs) != set(METRICS):
        raise RuntimeError("YAML target specs differ from EXP-003 6-metric dataset")
    return bounds, target_specs, sha


def aggregate(records, metric):
    sub = [r for r in records if r["metric"] == metric]
    residuals = np.asarray([r["residual"] for r in sub], dtype=float)
    observed = np.asarray([r["observed"] for r in sub], dtype=float)
    pred = np.asarray([r["predicted_mean"] for r in sub], dtype=float)
    std = np.asarray([r["predicted_std"] for r in sub], dtype=float)
    n = len(sub)
    if n != N_TEST:
        raise RuntimeError(f"Expected {N_TEST} holdout predictions for {metric}, got {n}")
    bad_flags = sum(bool(r["audit_flags"]) for r in sub)
    return {
        "n": n,
        "mae": float(np.mean(np.abs(residuals))),
        "rmse": float(np.sqrt(np.mean(np.square(residuals)))),
        "median_absolute_error": float(np.median(np.abs(residuals))),
        "mean_standardized_residual": float(np.mean(residuals / std)),
        "mean_abs_standardized_residual": float(np.mean(np.abs(residuals / std))),
        "empirical_95_interval_hit_rate": float(np.mean(np.abs(residuals) <= Z_95 * std)),
        "n_flagged_designs_in_holdout": bad_flags,
        "n_negative_predicted_means": int(np.sum(pred < 0)),
        "observed_min": float(observed.min()),
        "observed_max": float(observed.max()),
    }


def main():
    print("=" * 66, flush=True)
    print("EXP-005 / STAGE-2: original ATLAS GP — holdout validation", flush=True)
    print("TRAIN D000-D039 (40) | TEST D040-D059 (20) | SPICE 0", flush=True)
    print("=" * 66, flush=True)

    # Avoid overwriting the scientific record before spending time fitting GPs.
    for dst in (PRED_PATH, SUMMARY_PATH):
        if dst.exists():
            raise FileExistsError(f"Existing EXP-005 GP evaluation cannot be overwritten: {dst}")

    rows, source_sha = read_source()
    if len(rows) != N_TRAIN + N_TEST:
        raise RuntimeError(f"Wrong dataset size: {len(rows)}")
    bounds, targets, atlas_sha = check_config()
    X = np.asarray([[float(r[p]) for p in PARAMS] for r in rows], dtype=float)
    if np.any(X < bounds[:, 0]) or np.any(X > bounds[:, 1]):
        raise RuntimeError("One or more historical parameters fall outside the pinned YAML bounds")

    # Pinned imports: use *the actual ATLAS GP*, not a separately reimplemented GP.
    sys.path.insert(0, str(ATLAS_ROOT))
    import torch
    from topbo.gp_model import GPSurrogate
    from topbo.utils import parse_spec_constraints

    names, constraints, directions = parse_spec_constraints(targets)
    if set(names) != set(METRICS):
        raise RuntimeError(f"Unexpected ATLAS spec_names: {names}")

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)

    # Test labels are NOT passed to GP.fit().
    X_train = X[:N_TRAIN]
    X_test = X[N_TRAIN:]
    y_train = {
        k: np.asarray([float(r[k]) for r in rows[:N_TRAIN]], dtype=float)
        for k in names
    }
    model = GPSurrogate(names, constraints, directions, bounds)
    print(f"[CHECK] Pinned ATLAS SHA={atlas_sha[:12]}, source SHA256={source_sha[:12]}", flush=True)
    print(f"[GP FIT] Fitting {len(names)} independent GPs on 40 actual TT observations...", flush=True)
    output = io.StringIO()
    started = time.monotonic()
    # ATLAS catches individual MLL fit failures and prints fallback warnings.
    # Capture the messages, do not silently assert that optimization succeeded.
    with contextlib.redirect_stdout(output):
        model.fit(X_train, y_train, fom_values=None, incremental=False)
    fit_seconds = time.monotonic() - started
    fit_messages = output.getvalue().strip().splitlines()
    fallback_specs = []
    for name in names:
        if any(f"MLL fit failed for {name}:" in line for line in fit_messages):
            fallback_specs.append(name)
    other_messages = [
        line for line in fit_messages
        if not any(f"MLL fit failed for {name}:" in line for name in names)
    ]
    if set(model.gps) != set(names):
        raise RuntimeError("Baseline GP did not produce 6 surrogate models")
    print(f"[GP FIT] Returned 6 GP models in {fit_seconds:.2f}s", flush=True)
    if fallback_specs:
        print("[WARNING] MLL fit fallback for: " + ", ".join(fallback_specs), flush=True)
        for line in fit_messages:
            if "MLL fit failed" in line:
                print("[GP DETAIL] " + line, flush=True)
    else:
        print("[GP FIT] No MLL fallback messages captured.", flush=True)
    for line in other_messages:
        print("[GP MESSAGE] " + line, flush=True)

    means, stds = model.predict(X_test)
    records = []
    for idx, row in enumerate(rows[N_TRAIN:]):
        flags = "|".join(identify_flags(row))
        for metric in METRICS:
            mu = float(means[metric][idx])
            std = float(stds[metric][idx])
            observed = float(row[metric])
            if not (math.isfinite(mu) and math.isfinite(std) and std > 0):
                raise ValueError(f"Invalid GP prediction for {row['design_id']}/{metric}: {mu}, {std}")
            residual = observed - mu
            records.append({
                "design_id": row["design_id"],
                "metric": metric,
                "observed": observed,
                "predicted_mean": mu,
                "predicted_std": std,
                "residual": residual,
                "abs_error": abs(residual),
                "normalized_residual": residual / std,
                "inside_approx_95_interval": abs(residual) <= Z_95 * std,
                "audit_flags": flags,
            })

    summaries = {metric: aggregate(records, metric) for metric in METRICS}
    result = {
        "status": "completed_baseline_holdout",
        "experiment": "EXP-005",
        "model": "original ATLAS GPSurrogate / independent Matérn 5/2 ARD BoTorch GPs",
        "atlas_sha": atlas_sha,
        "source": str(EXP_DIR.parent / "EXP-003_tt_adaptive_feasible_discovery" / "raw" / "trajectory.csv"),
        "source_sha256": source_sha,
        "seed": SEED,
        "train_ids": "D000-D039",
        "holdout_ids": "D040-D059",
        "n_train": N_TRAIN,
        "n_holdout": N_TEST,
        "n_new_spice_evaluations": 0,
        "fit_seconds": fit_seconds,
        "gp_device": str(model.device),
        "mll_fallback_spec_names": fallback_specs,
        "mll_fallback_messages": [s for s in fit_messages if "MLL fit failed" in s],
        "other_fit_messages": other_messages,
        "interval_note": (
            "mean +/- 1.96 * posterior std: diagnostic, not an independently "
            "guaranteed 95% prediction interval; posterior std refers to "
            "GP latent function unless model/likelihood treatment changes"
        ),
        "holdout_limitation": (
            "D040-D059 were adaptively chosen in EXP-003, so this is a "
            "chronological exploration holdout rather than iid validation. "
            "Using the same test set to choose models biases later comparisons."
        ),
        "metric_summary": summaries,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with PRED_PATH.open("x", newline="", encoding="utf-8") as f:
        fieldnames = [
            "design_id", "metric", "observed", "predicted_mean",
            "predicted_std", "residual", "abs_error",
            "normalized_residual", "inside_approx_95_interval", "audit_flags"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        f.flush()
        os.fsync(f.fileno())
    with SUMMARY_PATH.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    print("[RESULT] 6 metrics x 20 held-out designs = 120 predictions", flush=True)
    for name in METRICS:
        d = summaries[name]
        print(
            f"[{name}] MAE={d['mae']:.6g} RMSE={d['rmse']:.6g} "
            f"approx95_hit={d['empirical_95_interval_hit_rate']:.0%} "
            f"negative_mean={d['n_negative_predicted_means']} "
            f"flagged={d['n_flagged_designs_in_holdout']}",
            flush=True
        )
    print(f"[CSV] {PRED_PATH}", flush=True)
    print(f"[JSON] {SUMMARY_PATH}", flush=True)
    print("[BUDGET] SPICE calls: 0", flush=True)


if __name__ == "__main__":
    main()
