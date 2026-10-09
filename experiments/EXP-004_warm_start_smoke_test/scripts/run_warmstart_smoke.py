#!/usr/bin/env python3
"""EXP-004: test observation warm-start with exactly ONE new TT SPICE design.

Keeps the pinned ATLAS source untouched. Its first 60 evaluator calls return
EXP-003 measured metrics from memory; only the new adaptive candidate invokes
CircuitEvaluator.evaluate(). It is NOT exact restoration of EXP-003 GP/Mapper state.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

EXP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EXP_DIR.parents[1]
EXP003 = REPO_ROOT / "experiments" / "EXP-003_tt_adaptive_feasible_discovery"
SOURCE = EXP003 / "raw" / "trajectory.csv"
ATLAS_ROOT = Path(os.environ.get("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
EXPECTED_ATLAS_SHA = "dd23c5ba7beb598909be593e4a84c81dab92cc69"
YAML = "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"
RUN_ID = "EXP-004_warmstart_smoke_seed42"
PARAMS = ("wp1", "wn1", "wp3", "wn3", "wn4", "wn5", "cc")
METRICS = ("gain_min", "ibias_max", "phm_min", "t_settle_max", "ugbw_min", "vswing_min")
N_HISTORY = 60
BUDGET = 61                 # 60 cached observations + 1 *new* SPICE evaluation
SEED = 42
CORNER = "TT_3.3V_27C"


def load_history(path: Path | None = None):
    """Validate provenance and return measured EXP-003 arrays (not predictions)."""
    if path is None:
        path = SOURCE
    if not path.is_file():
        raise FileNotFoundError(f"EXP-003 trajectory not found: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"iteration", "design_id", "phase", "feasible", *PARAMS, *METRICS}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing EXP-003 columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) != N_HISTORY:
        raise ValueError(f"Expected exactly 60 EXP-003 rows, got {len(rows)}")
    x_rows = []
    y_rows = []
    for i, row in enumerate(rows):
        expect_phase = "init" if i < 20 else "adaptive"
        if (int(row["iteration"]) != i
                or row["design_id"] != f"D{i:03d}"
                or row["phase"] != expect_phase):
            raise ValueError(f"Incorrect EXP-003 sequence at row {i}")
        if row["feasible"] != "False":
            raise ValueError(f"Unexpected feasibility value for {row['design_id']}")
        x = [float(row[k]) for k in PARAMS]
        y = {k: float(row[k]) for k in METRICS}
        if not all(np.isfinite(v) for v in x + list(y.values())):
            raise ValueError(f"Non-finite source value at {row['design_id']}")
        x_rows.append(x)
        y_rows.append(y)
    X = np.asarray(x_rows, dtype=float)
    if np.unique(X, axis=0).shape[0] != N_HISTORY:
        raise ValueError("Duplicate design in prior observations")
    return X, y_rows


def check_environment():
    def sha(repo):
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
    got = sha(ATLAS_ROOT)
    if got != EXPECTED_ATLAS_SHA:
        raise RuntimeError(f"ATLAS SHA mismatch: expected {EXPECTED_ATLAS_SHA}, got {got}")
    model = (Path(os.environ.get("PDK_ROOT", "~/pdks")).expanduser()
             / "gf180" / "models" / "ngspice" / "design.ngspice")
    if not model.is_file():
        raise FileNotFoundError(f"Missing GF180 statistical model: {model}")
    content = model.read_text(errors="ignore")
    for flag in ("sw_stat_global", "sw_stat_mismatch"):
        m = re.search(rf"\b{flag}\s*=\s*([01])", content)
        if m is None or int(m.group(1)) != 0:
            raise RuntimeError(f"Expected {flag}=0 in {model} (found {m.group(1) if m else 'missing'})")
    print("[CHECK] ATLAS SHA and GF180 MC-off configuration: PASS", flush=True)


def margins(values, constraints, directions):
    out = []
    for k in METRICS:
        target = float(constraints[k])
        value = float(values[k])
        margin = ((value - target) if directions[k] == "min" else (target - value)) / (abs(target) + 1e-30)
        out.append(margin)
    return out


def smoke(args):
    X, Y = load_history()
    print(f"[WARM START] Source: {SOURCE}", flush=True)
    print("[WARM START] Validated 60 prior TT measurements, D000-D059", flush=True)
    print(f"[WARM START] D050: PM={Y[50]['phm_min']:.6f} deg, UGBW={Y[50]['ugbw_min']/1e6:.6f} MHz (historical)", flush=True)
    if args.check_only:
        print("[CHECK ONLY] No GP training, new candidate or SPICE evaluation performed.", flush=True)
        return

    check_environment()
    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    os.chdir(ATLAS_ROOT)
    from topbo.circuit_eval import CircuitEvaluator
    from topbo.optimizers import TopoBO
    from topbo.utils import check_feasibility

    evaluator = CircuitEvaluator(YAML, root_dir="tmp/exp004_warmstart_smoke", pvt=False)
    if tuple(evaluator.param_names) != PARAMS or set(evaluator.spec_names) != set(METRICS):
        raise RuntimeError("ATLAS evaluator's parameter/metric definition changed")
    if np.any(X < evaluator.param_bounds[:, 0]) or np.any(X > evaluator.param_bounds[:, 1]):
        raise RuntimeError("Some historical design points are outside current parameter bounds")
    for i, x in enumerate(X):
        effective_x = evaluator._round_params(x)
        if not np.allclose(x, effective_x, rtol=0, atol=1e-18):
            raise RuntimeError(f"Historical design D{i:03d} doesn't match current rounding")
        expected_feas = check_feasibility(Y[i], evaluator.constraints, evaluator.directions)
        if expected_feas:
            raise RuntimeError(f"Historical design D{i:03d} is feasible but source says False")
    print("[CHECK] Historic data match current YAML parameter bounds/specs: PASS", flush=True)

    raw = EXP_DIR / "raw"
    data = EXP_DIR / "data"
    trajectory = raw / "trajectory.csv"
    design_path = data / "design_points.csv"
    metrics_path = data / "corner_metrics.csv"
    output_paths = [trajectory, design_path, metrics_path]
    if any(path.exists() for path in output_paths):
        raise FileExistsError("EXP-004 results already exist. Never overwrite. Use a new experiment for a new run.")
    raw.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)

    original_evaluate = evaluator.evaluate
    replayed = 0
    actually_simulated = 0
    new_params = None
    new_specs = None
    prediction = None

    class WarmStartTopoBO(TopoBO):
        def _initial_design(self, evaluator, bounds, log_scale, n_init, seed):
            if n_init != N_HISTORY:
                raise RuntimeError(f"Invalid n_init: {n_init}")
            return X.copy()   # crucial: no fresh initial LHS designs

        def _select_next(self, model, X_cand, bounds, t, T, best_f, observed_Y=None):
            nonlocal prediction
            selected = super()._select_next(
                model, X_cand, bounds, t, T, best_f, observed_Y=observed_Y
            )
            x = np.asarray(selected["x_next"], dtype=float).reshape(1, -1)
            mu, std = model.predict(x)
            prediction = {name: {"mean": float(mu[name][0]),
                                 "std": float(std[name][0])}
                          for name in METRICS}
            print(f"[GP] fit complete; predicted 6 spec distributions for D060", flush=True)
            return selected

    def replay_or_evaluate(x):
        nonlocal replayed, actually_simulated, new_params, new_specs
        x = np.asarray(x, dtype=float)
        if replayed < N_HISTORY:
            i = replayed
            # Fails loudly if ATLAS asks for a different initial design.
            if not np.allclose(x, X[i], rtol=0, atol=1e-18):
                raise RuntimeError(f"Warm-start sequence mismatch at D{i:03d}")
            replayed += 1
            return dict(Y[i])  # NO SPICE call for D000..D059

        if actually_simulated >= 1:
            raise RuntimeError("Smoke test must evaluate only one new design")
        if prediction is None:
            raise RuntimeError("No GP prediction recorded before D060 evaluation")
        effective = evaluator._round_params(
            np.clip(x, evaluator.param_bounds[:, 0], evaluator.param_bounds[:, 1])
        )
        if np.any(np.all(np.isclose(X, effective, rtol=0, atol=1e-18), axis=1)):
            raise RuntimeError("Proposed D060 duplicates previously evaluated design")
        if args.dry_run:
            print("[DRY RUN] GP proposed a NEW D060; no SPICE evaluation.", flush=True)
            raise DryRunComplete(effective)

        print("[SPICE] Evaluating exactly one new design: D060", flush=True)
        actually_simulated += 1
        specs = original_evaluate(x)  # the ONLY real SPICE call
        if any(not np.isfinite(float(specs[k])) for k in METRICS):
            raise RuntimeError("D060 SPICE produced non-finite metrics; inspect simulator output")
        new_params = dict(zip(PARAMS, map(float, effective)))
        new_specs = {k: float(specs[k]) for k in METRICS}
        mm = margins(new_specs, evaluator.constraints, evaluator.directions)
        feas = check_feasibility(new_specs, evaluator.constraints, evaluator.directions)
        row = {
            "iteration": 60, "design_id": "D060", "phase": "warmstart_smoke",
            **new_params, **new_specs, "feasible": str(bool(feas)),
            "n_specs_passed": sum(v >= 0 for v in mm),
            "worst_margin": min(mm),
            "total_violation": sum(max(0, -v) for v in mm),
        }
        # Persist D060 before proceeding. 'x' prevents overwriting old results.
        with trajectory.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row))
            writer.writeheader()
            writer.writerow(row)
            f.flush()
            os.fsync(f.fileno())
        print(f"[TT RESULT] D060 | TT_FEASIBLE={feas} | PASS={row['n_specs_passed']}/6 | WORST_MARGIN={row['worst_margin']:+.4f}", flush=True)
        print(f"[CSV] Saved D060 -> {trajectory}", flush=True)
        return specs

    class DryRunComplete(Exception):
        def __init__(self, proposed):
            self.proposed = proposed

    optimizer = WarmStartTopoBO()
    evaluator.evaluate = replay_or_evaluate
    try:
        if args.dry_run:
            print("[DRY RUN] GP training + candidate selection only; no new SPICE call", flush=True)
        try:
            logger, result = optimizer.optimize(
                evaluator, budget=BUDGET, n_init=N_HISTORY, seed=SEED,
                surrogate="gp", early_stop=True, gp_time_limit=10.0,
                log_root=str(raw / "atlas_logs"),
            )
        except DryRunComplete as e:
            print("[DRY RUN] Proposed parameters:", dict(zip(PARAMS, map(float, e.proposed))))
            print(f"[VERIFIED] historical replay={replayed}, actual SPICE calls={actually_simulated}", flush=True)
            return
    finally:
        evaluator.evaluate = original_evaluate

    if replayed != N_HISTORY or actually_simulated != 1 or new_params is None:
        raise RuntimeError(f"Unexpected replay/SPICE counts: {replayed}/{actually_simulated}")
    with design_path.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["design_id", *PARAMS])
        w.writeheader()
        w.writerow({"design_id": "D060", **new_params})
    with metrics_path.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["design_id", "corner", *METRICS, "feasible"])
        w.writeheader()
        w.writerow({"design_id": "D060", "corner": CORNER, **new_specs,
                    "feasible": str(bool(check_feasibility(new_specs, evaluator.constraints, evaluator.directions)))})
    (raw / "prediction_D060.json").write_text(json.dumps({
        "source": "EXP-003 D000-D059", "n_replayed": replayed,
        "n_new_spice": actually_simulated, "predicted": prediction,
        "observed": new_specs,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"[VERIFIED] warm-start replay={replayed}, actual NEW TT SPICE calls={actually_simulated}", flush=True)
    print(f"[OUTPUT] {trajectory}", flush=True)
    print(f"[OUTPUT] {design_path}", flush=True)
    print(f"[OUTPUT] {metrics_path}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check-only", action="store_true", help="Only validate 60 prior observations, no Atlas import/SPICE")
    p.add_argument("--dry-run", action="store_true", help="GP fitting and selecting D060, but do not run SPICE")
    args = p.parse_args()
    if args.check_only and args.dry_run:
        p.error("Choose at most one of --check-only or --dry-run")
    smoke(args)


if __name__ == "__main__":
    main()
