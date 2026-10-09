#!/usr/bin/env python3
"""EXP-003: ATLAS TT adaptive search for first feasible design.

Runs the same TopoBO optimization loop used by ATLAS, appending each completed
TT evaluation to data/trajectory.csv immediately for crash-safe research records.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ATLAS_ROOT = Path(os.environ.get("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
RESEARCH_ROOT = Path("~/research_intern").expanduser().resolve()
EXP_DIR = RESEARCH_ROOT / "experiments" / "EXP-003_tt_adaptive_feasible_discovery"
DATA_DIR = EXP_DIR / "data"
RAW_LOG_ROOT = EXP_DIR / "raw" / "atlas_logs"

EXPECTED_ATLAS_COMMIT = "dd23c5ba7beb598909be593e4a84c81dab92cc69"
BUDGET = 60
SEED = 42

YAML_REL = (
    "eval_engines/ngspice/ngspice_inputs/yaml_files/"
    "two_stage_opamp_gf180.yaml"
)


def git_head(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def check_atlas_version() -> None:
    head = git_head(ATLAS_ROOT)
    if head != EXPECTED_ATLAS_COMMIT:
        raise RuntimeError(
            "ATLAS commit mismatch.\n"
            f"Expected: {EXPECTED_ATLAS_COMMIT}\n"
            f"Current : {head}\n"
            "Do not continue until the research baseline version is confirmed."
        )


def check_statistical_switches() -> None:
    pdk_root = Path(os.environ.get("PDK_ROOT", "~/pdks")).expanduser()
    design_model = pdk_root / "gf180" / "models" / "ngspice" / "design.ngspice"

    if not design_model.exists():
        raise FileNotFoundError(f"GF180 design model not found: {design_model}")

    text = design_model.read_text(errors="ignore")

    def value_of(name: str) -> int | None:
        m = re.search(rf"{name}\s*=\s*([01])", text)
        return int(m.group(1)) if m else None

    global_sw = value_of("sw_stat_global")
    mismatch_sw = value_of("sw_stat_mismatch")

    print(f"[CHECK] sw_stat_global   = {global_sw}")
    print(f"[CHECK] sw_stat_mismatch = {mismatch_sw}")

    if global_sw != 0 or mismatch_sw != 0:
        raise RuntimeError(
            "GF180 statistical variation is not OFF. "
            "EXP-003 requires deterministic TT simulation."
        )


def normalized_margins(specs, constraints, directions, spec_names):
    margins = {}
    for name in spec_names:
        value = float(specs[name])
        target = float(constraints[name])
        denom = abs(target) + 1e-30
        if directions[name] == "min":
            margin = (value - target) / denom
        else:
            margin = (target - value) / denom
        margins[name] = margin
    return margins


def enable_incremental_trajectory(evaluator, n_init: int):
    """Append one durable CSV row immediately after each TT evaluation.

    The original evaluator remains responsible for SPICE; this wrapper only
    records its returned metrics. Using exclusive create ('x') prevents an
    accidental rerun from truncating an earlier experiment.
    """
    from topbo.utils import check_feasibility

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "trajectory.csv"

    fieldnames = (
        ["iteration", "design_id", "phase"]
        + evaluator.param_names
        + evaluator.spec_names
        + ["feasible", "n_specs_passed", "worst_margin", "total_violation"]
    )

    try:
        csv_file = out.open("x", newline="")
    except FileExistsError as exc:
        raise FileExistsError(
            f"EXP-003 trajectory already exists: {out}\\n"
            "Preserve/rename the existing CSV before starting a new run. "
            "This script will not overwrite earlier research data."
        ) from exc

    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    csv_file.flush()
    os.fsync(csv_file.fileno())

    original_evaluate = evaluator.evaluate
    iteration = 0

    def evaluate_and_record(x):
        nonlocal iteration

        # One SPICE design evaluation, including all required TT analyses.
        specs = original_evaluate(x)

        # Store the effective clipped/rounded parameters passed to SPICE.
        effective_x = evaluator._round_params(
            np.clip(
                np.asarray(x, dtype=float),
                evaluator.param_bounds[:, 0],
                evaluator.param_bounds[:, 1],
            )
        )
        margins = normalized_margins(
            specs, evaluator.constraints, evaluator.directions, evaluator.spec_names
        )
        feasible = check_feasibility(
            specs, evaluator.constraints, evaluator.directions
        )

        row = {
            "iteration": iteration,
            "design_id": f"D{iteration:03d}",
            "phase": "init" if iteration < n_init else "adaptive",
            "feasible": bool(feasible),
            "n_specs_passed": sum(m >= 0 for m in margins.values()),
            "worst_margin": min(margins.values()),
            "total_violation": sum(max(0.0, -m) for m in margins.values()),
        }
        row.update({
            name: float(value)
            for name, value in zip(evaluator.param_names, effective_x)
        })
        row.update({
            name: float(specs[name]) for name in evaluator.spec_names
        })

        writer.writerow(row)
        # Ensure completed evaluations survive ordinary crashes/interruption.
        csv_file.flush()
        os.fsync(csv_file.fileno())

        print(f"[CSV] Saved D{iteration:03d} -> {out}", flush=True)
        iteration += 1
        return specs

    evaluator.evaluate = evaluate_and_record
    return out, csv_file, original_evaluate


def write_summary(mem_logger, results, n_init: int, trajectory_path: Path) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "run_summary.json"

    first_feasible = mem_logger.first_feasible_iter()
    summary = {
        "atlas_commit": EXPECTED_ATLAS_COMMIT,
        "budget": BUDGET,
        "seed": SEED,
        "n_init": n_init,
        "surrogate": "gp",
        "early_stop": True,
        "n_evaluated": len(mem_logger.history_X),
        "n_feasible": mem_logger.n_feasible(),
        "first_feasible_iter": first_feasible,
        "first_feasible_design_id": (
            f"D{first_feasible:03d}" if first_feasible is not None else None
        ),
        "trajectory_csv": str(trajectory_path),
        "atlas_results": results,
    }

    out.write_text(json.dumps(summary, indent=2))
    return out


def main() -> None:
    print("=" * 64)
    print("EXP-003 — ATLAS TT Adaptive Feasible Discovery")
    print("=" * 64)

    check_atlas_version()
    check_statistical_switches()

    if str(ATLAS_ROOT) not in sys.path:
        sys.path.insert(0, str(ATLAS_ROOT))
    os.chdir(ATLAS_ROOT)

    from run_experiment import n_init_for
    from topbo.circuit_eval import CircuitEvaluator
    from topbo.optimizers import TopoBO

    evaluator = CircuitEvaluator(
        YAML_REL,
        root_dir=os.path.join("tmp", "exp003_tt_adaptive_feasible_discovery"),
        pvt=False,
    )

    n_init = n_init_for(evaluator, BUDGET)

    print(f"[CONFIG] budget = {BUDGET}")
    print(f"[CONFIG] n_init = {n_init}")
    print(f"[CONFIG] seed = {SEED}")
    print("[CONFIG] surrogate = gp")
    print("[CONFIG] early_stop = True")

    if n_init != 20:
        raise RuntimeError(
            f"Expected n_init=20 for EXP-003, got {n_init}. "
            "Do not continue because D000-D019 alignment would be lost."
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_LOG_ROOT.mkdir(parents=True, exist_ok=True)

    optimizer = TopoBO()

    # Create the CSV before simulation and persist every completed TT evaluation.
    # If optimization crashes, rows already written remain on disk.
    trajectory_path, csv_file, original_evaluate = enable_incremental_trajectory(
        evaluator, n_init
    )
    try:
        mem_logger, results = optimizer.optimize(
            evaluator,
            budget=BUDGET,
            n_init=n_init,
            seed=SEED,
            log_root=str(RAW_LOG_ROOT),
            surrogate="gp",
            early_stop=True,
            gp_time_limit=10.0,
        )
    finally:
        evaluator.evaluate = original_evaluate
        csv_file.close()

    summary_path = write_summary(mem_logger, results, n_init, trajectory_path)

    print("=" * 64)
    print("EXP-003 COMPLETE")
    print("=" * 64)
    print(f"Evaluated designs : {len(mem_logger.history_X)}")
    print(f"Feasible designs  : {mem_logger.n_feasible()}")
    print(f"First feasible    : {mem_logger.first_feasible_iter()}")
    print(f"Trajectory        : {trajectory_path}")
    print(f"Summary           : {summary_path}")


if __name__ == "__main__":
    main()
