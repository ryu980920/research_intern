#!/usr/bin/env python3
"""EXP-005 Stage 3B-2: trace GP posterior variance BEFORE vs AFTER library floor.

This is a diagnosis of GPyTorch numerical semantics, NOT a GP B-vs-C model
selection. No SPICE, no edits to pinned ATLAS, no changes to EXP-003 data.

Controls: the same 34 confirmed-unflagged settling training labels, same 19
holdout inputs, same GPSurrogate model/kernel, seed 42. Refit two control
models differing ONLY by response units: seconds and microseconds.

Run in the (atlas) WSL environment from the research repo root:
    python experiments/EXP-005_gp_surrogate_reliability/scripts/trace_settling_posterior_variance.py
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
import warnings
from pathlib import Path

import numpy as np

from audit_tt_dataset import EXP_DIR, PARAMS, read_source
from compare_validity_aware_gp import read_flags
from diagnose_metric_semantics import get_codes_and_horizons
from evaluate_gp_baseline import N_TRAIN, N_TEST, SEED, check_config

METRIC = "t_settle_max"
UNITS = ("s", "us")
FACTOR = 1e6
OUTDIR = EXP_DIR / "data" / "analysis"
OUTPUT_CSV = OUTDIR / "stage3b2_variance_trace.csv"
OUTPUT_JSON = OUTDIR / "stage3b2_variance_trace_summary.json"
STAGE3B_CSV = OUTDIR / "stage3b_settling_unit_comparison.csv"
STAGE3B_JSON = OUTDIR / "stage3b_settling_unit_summary.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def warnings_as_text(w):
    return [f"{type(item.message).__name__}: {item.message}" for item in w]


def load_stage3b(expected_ids, source_sha, atlas_sha):
    for path in (STAGE3B_CSV, STAGE3B_JSON):
        if not path.is_file():
            raise FileNotFoundError(f"Need completed Stage 3B prerequisite: {path}")
    source = json.loads(STAGE3B_JSON.read_text(encoding="utf-8"))
    if (source.get("atlas_sha") != atlas_sha
            or source.get("raw_trajectory_sha256") != source_sha
            or source.get("n_train") != 34
            or source.get("n_holdout") != 19):
        raise RuntimeError("Stage 3B metadata does not match this experiment")
    with STAGE3B_CSV.open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    ids = [r["design_id"] for r in data]
    if ids != expected_ids:
        raise RuntimeError("Stage 3B validation IDs/order changed")
    return data


def train_model(name, unit_factor, X_train, y_train_s, bounds, target_s, X_test,
                torch, gp_cls, gpytorch):
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)

    model = gp_cls(
        [METRIC],
        {METRIC: float(target_s) * unit_factor},
        {METRIC: "max"},
        bounds,
    )
    captured_stdout = io.StringIO()
    with warnings.catch_warnings(record=True) as fit_warnings:
        warnings.simplefilter("always")
        with contextlib.redirect_stdout(captured_stdout):
            model.fit(X_train, {METRIC: y_train_s * unit_factor},
                      fom_values=None, incremental=False)
    fit_log = captured_stdout.getvalue().splitlines()
    if any(f"MLL fit failed for {METRIC}:" in s for s in fit_log):
        raise RuntimeError(f"{name} MLL fallback: {'; '.join(fit_log)}")
    if METRIC not in model.gps:
        raise RuntimeError(f"{name} GP was not fitted")

    gp = model.gps[METRIC]
    gp.eval()
    device = model.device
    dtype = model.dtype
    batch = torch.tensor(X_test, dtype=dtype, device=device)
    floor = float(gpytorch.settings.min_variance.value(dtype))

    # posterior.distribution is the GPyTorch MultivariateNormal holding the
    # unstandardized predictions (in the unit supplied to GP.fit).
    # The diagonal of its LazyLinearOperator is accessed BEFORE the
    # MultivariateNormal.variance clamp_min(min_variance) property.
    with torch.no_grad():
        with warnings.catch_warnings(record=True) as construction_warnings:
            warnings.simplefilter("always")
            posterior = gp.posterior(batch, observation_noise=False)

        dist = getattr(posterior, "distribution", None)
        if dist is None:
            raise RuntimeError(
                f"{name}: Unexpected BoTorch posterior class "
                f"{type(posterior).__name__}; cannot trace raw diagonal safely"
            )
        if not hasattr(dist, "lazy_covariance_matrix"):
            raise RuntimeError(
                f"{name}: Expected GPyTorch MVN, found {type(dist).__name__}"
            )
        with warnings.catch_warnings(record=True) as diagonal_warnings:
            warnings.simplefilter("always")
            raw_diag = dist.lazy_covariance_matrix.diagonal(
                dim1=-1, dim2=-2
            ).detach().cpu().numpy().reshape(-1)
        with warnings.catch_warnings(record=True) as variance_warnings:
            warnings.simplefilter("always")
            reported_var = posterior.variance.detach().cpu().numpy().reshape(-1)
        means = posterior.mean.detach().cpu().numpy().reshape(-1)

    n = len(X_test)
    if any(len(a) != n for a in (raw_diag, reported_var, means)):
        raise RuntimeError(f"{name}: Wrong posterior length")
    if not (np.isfinite(raw_diag).all() and
            np.isfinite(reported_var).all() and np.isfinite(means).all()):
        raise RuntimeError(f"{name}: Nonfinite raw/reported GP values")

    predicted_floor = np.maximum(raw_diag, floor)
    deviation = float(np.max(np.abs(reported_var - predicted_floor)))
    # The transformation can add numerical differences; compare with
    # scale-aware tolerances and report the actual deviation even if nonzero.
    matches_clamp = bool(np.allclose(
        reported_var, predicted_floor, rtol=1e-6, atol=1e-15
    ))
    return {
        "mean": means,
        "raw_variance": raw_diag,
        "reported_variance": reported_var,
        "min_variance_setting": floor,
        "raw_below_floor": raw_diag < floor,
        "raw_negative": raw_diag < 0,
        "variance_matches_library_floor": matches_clamp,
        "max_variance_deviation_from_floor_model": deviation,
        "construction_warnings": warnings_as_text(construction_warnings),
        "diagonal_warnings": warnings_as_text(diagonal_warnings),
        "variance_warnings": warnings_as_text(variance_warnings),
        "fit_warnings": warnings_as_text(fit_warnings),
        "fit_stdout": fit_log,
        "gp_device": str(device),
        "posterior_type": type(posterior).__name__,
        "distribution_type": type(dist).__name__,
        "model_outcome_stdvs": [
            float(x) for x in gp.outcome_transform.stdvs.detach().cpu().reshape(-1)
        ],
        "likelihood_noise_standardized": [
            float(x) for x in gp.likelihood.noise.detach().cpu().reshape(-1)
        ],
    }


def main():
    for dest in (OUTPUT_CSV, OUTPUT_JSON):
        if dest.exists():
            raise FileExistsError(f"Prior diagnosis exists, no overwrite: {dest}")
    rows, raw_sha = read_source()
    if len(rows) != N_TRAIN + N_TEST:
        raise RuntimeError(f"Wrong dataset length: {len(rows)}")
    bounds, targets, atlas_sha = check_config()
    semantics = get_codes_and_horizons()
    if semantics["atlas_sha"] != atlas_sha:
        raise RuntimeError("Mismatch in pinned ATLAS commit")
    flags, _ = read_flags(rows, raw_sha, semantics)

    train = [r for r in rows[:N_TRAIN] if not flags[r["design_id"]][METRIC]]
    test = [r for r in rows[N_TRAIN:] if not flags[r["design_id"]][METRIC]]
    excluded = [r["design_id"] for r in rows[:N_TRAIN]
                if flags[r["design_id"]][METRIC]]
    if (len(train) != 34 or len(test) != 19 or
            excluded != ["D013", "D014", "D015", "D016", "D017", "D023"]):
        raise RuntimeError("Stage 3B-2 train/test mask changed")

    names = [r["design_id"] for r in test]
    previous = load_stage3b(names, raw_sha, atlas_sha)
    X_train = np.array([[r[p] for p in PARAMS] for r in train], dtype=float)
    X_test = np.array([[r[p] for p in PARAMS] for r in test], dtype=float)
    Y_s = np.array([r[METRIC] for r in train], dtype=float)

    atlas_root = Path(os.environ.get("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
    sys.path.insert(0, str(atlas_root))
    import torch
    import gpytorch
    from topbo.gp_model import GPSurrogate
    # The above works when ATLAS_ROOT is in sys.path, as in earlier scripts.
    # No external code is patched by this diagnostic.

    print("EXP-005 Stage 3B-2 | trace GP posterior raw variance vs library floor", flush=True)
    print(f"[SOURCE] ATLAS={atlas_sha[:12]} | trajectory SHA={raw_sha[:12]}", flush=True)
    print("[SPLIT] Train 34 | Holdout 19 | new SPICE=0", flush=True)
    print("[RULE] B(s) is a *diagnostic control*, not a trustworthy benchmark", flush=True)
    print(f"[LIBRARY] gpytorch={gpytorch.__version__}, torch={torch.__version__}",
          flush=True)

    target_s = float(targets[METRIC][0])
    b = train_model("B", 1.0, X_train, Y_s, bounds, target_s, X_test,
                    torch, GPSurrogate, gpytorch)
    c = train_model("C", FACTOR, X_train, Y_s, bounds, target_s, X_test,
                    torch, GPSurrogate, gpytorch)

    # Scale variance QUADRATICALLY; GP C native posterior units are µs².
    values = []
    for i, uid in enumerate(names):
        x = {
            "design_id": uid,
            "b_raw_var_s2": float(b["raw_variance"][i]),
            "b_reported_var_s2": float(b["reported_variance"][i]),
            "b_below_floor": bool(b["raw_below_floor"][i]),
            "b_raw_negative": bool(b["raw_negative"][i]),
            "b_reported_std_us": float(
                np.sqrt(b["reported_variance"][i]) * FACTOR
            ),
            "c_raw_var_us2": float(c["raw_variance"][i]),
            "c_reported_var_us2": float(c["reported_variance"][i]),
            "c_below_floor": bool(c["raw_below_floor"][i]),
            "c_raw_negative": bool(c["raw_negative"][i]),
            "c_reported_std_us": float(
                np.sqrt(c["reported_variance"][i])
            ),
            "b_reported_mean_us": float(b["mean"][i] * FACTOR),
            "c_reported_mean_us": float(c["mean"][i]),
            "stage3b_saved_b_mean_us": float(previous[i]["stage3b_b_mean_us"]),
            "stage3b_saved_c_mean_us": float(previous[i]["stage3b_c_mean_us"]),
            "stage3b_saved_b_std_us": float(previous[i]["stage3b_b_std_us"]),
            "stage3b_saved_c_std_us": float(previous[i]["stage3b_c_std_us"]),
        }
        values.append(x)

    b_diff = float(max(abs(r["b_reported_std_us"] -
                           r["stage3b_saved_b_std_us"]) for r in values))
    c_diff = float(max(abs(r["c_reported_std_us"] -
                           r["stage3b_saved_c_std_us"]) for r in values))
    b_mean_diff = float(max(abs(r["b_reported_mean_us"] -
                                r["stage3b_saved_b_mean_us"]) for r in values))
    c_mean_diff = float(max(abs(r["c_reported_mean_us"] -
                                r["stage3b_saved_c_mean_us"]) for r in values))

    def summaries(obj):
        return {
            "floor_in_native_unit_squared": obj["min_variance_setting"],
            "num_raw_below_floor": int(np.count_nonzero(obj["raw_below_floor"])),
            "num_raw_negative": int(np.count_nonzero(obj["raw_negative"])),
            "min_raw_variance": float(obj["raw_variance"].min()),
            "max_raw_variance": float(obj["raw_variance"].max()),
            "min_reported_variance": float(obj["reported_variance"].min()),
            "variance_equals_raw_clamped_to_floor": obj["variance_matches_library_floor"],
            "max_abs_clamp_formula_deviation": obj["max_variance_deviation_from_floor_model"],
            "post_construction_warnings": obj["construction_warnings"],
            "covariance_diagonal_warnings": obj["diagonal_warnings"],
            "variance_property_warnings": obj["variance_warnings"],
            "fit_warnings": obj["fit_warnings"],
            "fit_stdout": obj["fit_stdout"],
            "device": obj["gp_device"],
            "posterior_type": obj["posterior_type"],
            "distribution_type": obj["distribution_type"],
            "outcome_stdvs": obj["model_outcome_stdvs"],
            "likelihood_noise_standardized": obj["likelihood_noise_standardized"],
        }

    summary = {
        "experiment": "EXP-005",
        "stage": "3B-2 posterior variance floor trace",
        "status": "completed",
        "research_question": (
            "Does GPyTorch clamp a small positive/negative raw variance "
            "to its fixed minimum in the original output units?"
        ),
        "atlas_sha": atlas_sha,
        "trajectory_sha256": raw_sha,
        "stage3b_csv_sha256": sha256(STAGE3B_CSV),
        "stage3b_json_sha256": sha256(STAGE3B_JSON),
        "n_train": len(train),
        "n_holdout": len(test),
        "seed": SEED,
        "new_spice": 0,
        "new_gp_fits": 2,
        "gpytorch_version": gpytorch.__version__,
        "torch_version": torch.__version__,
        "b_seconds": summaries(b),
        "c_microseconds": summaries(c),
        "b_max_reproduced_std_difference_us": b_diff,
        "c_max_reproduced_std_difference_us": c_diff,
        "b_max_reproduced_mean_difference_us": b_mean_diff,
        "c_max_reproduced_mean_difference_us": c_mean_diff,
        "min_variance_B_floor_as_s2": b["min_variance_setting"],
        "min_variance_C_floor_as_s2": c["min_variance_setting"] / FACTOR**2,
        "interpretation_limitations": [
            "Even if a variance floor is proved, the cause of very small raw "
            "variances (kernel hyperparameters, observation noise, numerical "
            "algebra) requires a separate diagnosis.",
            "This only inspects the latent-function GP posterior; no claim "
            "about observation predictive interval calibration is made.",
            "Current unflagged settling time values are not waveform-verified.",
            "B is a broken-uncertainty control, not a valid superiority benchmark.",
        ],
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("x", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
        f.flush()
        os.fsync(f.fileno())
    with OUTPUT_JSON.open("x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    for label, model in (("B/s", b), ("C/us", c)):
        print(f"[{label}] floor={model['min_variance_setting']:.5g} (native unit)^2"
              f" | raw<floor={model['raw_below_floor'].sum()}/19"
              f" | raw_negative={model['raw_negative'].sum()}/19"
              f" | clamp_match={model['variance_matches_library_floor']}"
              f" | variance_warn={len(model['variance_warnings'])}", flush=True)
    print(f"[REPRO] max saved mean mismatch B={b_mean_diff:.6g} us, "
          f"C={c_mean_diff:.6g} us; std mismatch B={b_diff:.6g} us, "
          f"C={c_diff:.6g} us", flush=True)
    print(f"[SAVED] {OUTPUT_CSV}", flush=True)
    print(f"[SAVED] {OUTPUT_JSON}", flush=True)
    print("[BUDGET] GP fits=2; SPICE=0", flush=True)


if __name__ == "__main__":
    main()
