#!/usr/bin/env python3
"""EXP-007: re-evaluate only EXP-006 D292 at TT and PRESERVE ngspice CSVs.

Default: safe read-only preflight; --execute: exactly one TT circuit evaluation.
Pinned ATLAS is imported but NEVER modified. EXP-006 trajectory is NEVER edited.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

import numpy as np

EXP = Path(__file__).resolve().parents[1]
REPO = EXP.parents[1]
EXP006 = REPO / "experiments" / "EXP-006_atlas_release_baseline_reproduction"
RUN = EXP006 / "raw/runs/release_B500_S42_20261010_033242_863546"
TRAJECTORY = RUN / "trajectory.csv"
EXPECTED_TRAJECTORY_SHA = "2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34"
ATLAS = Path(os.getenv("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
YAML = "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"
PARAMS = ("wp1", "wn1", "wp3", "wn3", "wn4", "wn5", "cc")
METRICS = ("gain_min", "ibias_max", "phm_min", "t_settle_max", "ugbw_min", "vswing_min")
RAW_FILES = ("ac.csv", "dc.csv", "dc_sweep.csv", "tran.csv")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_d292() -> dict:
    if not TRAJECTORY.is_file():
        raise FileNotFoundError(f"Original EXP-006 WSL trajectory missing: {TRAJECTORY}")
    got = sha256(TRAJECTORY)
    if got != EXPECTED_TRAJECTORY_SHA:
        raise RuntimeError(f"EXP-006 trajectory hash changed! expected={EXPECTED_TRAJECTORY_SHA} got={got}")
    with TRAJECTORY.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 293:
        raise RuntimeError(f"Expected 293 evaluations; found {len(rows)}")
    row = rows[292]
    if row.get("iteration") != "292" or row.get("design_id") != "D292":
        raise RuntimeError("Row 292 is not D292")
    if row.get("feasible", "").lower() != "true":
        raise RuntimeError("Original D292 row is not feasible")
    return row


def preflight():
    sys.path.insert(0, str(EXP006 / "scripts"))
    from run_release_baseline import preflight as original_preflight
    report = original_preflight()
    if report["preflight_problems"]:
        raise RuntimeError("Original EXP-006 environment preflight failed: "
                           + "; ".join(report["preflight_problems"]))
    return report


def run_one(row: dict, report: dict):
    # Never modify the source run or an earlier validation attempt.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out = EXP / "raw" / "runs" / f"d292_tt_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    (out / "environment_preflight.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    os.environ["PDK_ROOT"] = str(Path(report["PDK_ROOT"]))
    os.chdir(ATLAS)
    sys.path.insert(0, str(ATLAS))
    from collections import OrderedDict
    from topbo.circuit_eval import CircuitEvaluator
    from topbo.utils import check_feasibility
    from eval_engines.ngspice.CircuitClass import (
        analyze_amplifier_performance, extract_tran_data,
    )

    evaluator = CircuitEvaluator(YAML, root_dir=str(out / "spice_tmp"), pvt=False)
    if tuple(evaluator.param_names) != PARAMS:
        raise RuntimeError(f"Parameter order changed: {evaluator.param_names}")
    x = np.asarray([float(row[p]) for p in PARAMS], dtype=float)
    effective = evaluator._round_params(
        np.clip(x, evaluator.param_bounds[:, 0], evaluator.param_bounds[:, 1])
    )
    if not np.array_equal(x, effective):
        raise RuntimeError(f"Parameter rounding/clipping changed D292: {x} -> {effective}")
    state = OrderedDict(zip(PARAMS, effective.tolist()))

    # Use pinned ATLAS's exact netlist generation and extraction methods.
    # Crucially do NOT call create_design_and_simulate(): it deletes the
    # whole design directory using shutil.rmtree(...) after extraction.
    sim = evaluator.sim_env
    base_name = sim.base_design_names[0]
    name = sim.get_design_name(state, base_name)
    design_folder, netlist = sim.create_design(
        state, name, sim.gen_dirs[0], sim.tmp_lines[0]
    )
    design_folder, netlist = Path(design_folder), Path(netlist)
    (out / "design_parameters.json").write_text(
        json.dumps({"source": str(TRAJECTORY), "source_iteration": 292,
                    "source_trajectory_sha256": EXPECTED_TRAJECTORY_SHA,
                    "params_SI": dict(state),
                    "original_metrics": {k: float(row[k]) for k in METRICS},
                    "generated_netlist": str(netlist)}, indent=2) + "\n",
        encoding="utf-8"
    )

    # Same ngspice -b <netlist> command and 120s timeout as pinned wrapper,
    # but capture stdout/stderr and check return code for the audit.
    try:
        proc = subprocess.run(["ngspice", "-b", str(netlist)], cwd=str(ATLAS),
                              capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired as exc:
        (out / "ERROR.txt").write_text(str(exc) + "\n", encoding="utf-8")
        raise
    (out / "ngspice_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (out / "ngspice_stderr.log").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"ngspice returncode={proc.returncode}; raw files preserved at {out}")
    missing = [name for name in RAW_FILES if not (design_folder / name).is_file()]
    if missing:
        raise RuntimeError(f"Missing raw waveforms {missing}; raw files preserved at {out}")

    # Released ATLAS extractor; report its results without changing any formulas.
    measured = evaluator._remap_specs(sim.translate_result(str(design_folder)))
    differences = {
        k: {"original": float(row[k]), "retest": float(measured[k]),
            "absolute_difference": float(measured[k]) - float(row[k])}
        for k in METRICS
    }

    # Check whether settling time was a true two-edge time measurement,
    # rather than the dimensionless d_settle fallback in CircuitClass.py.
    t, vin, vout = extract_tran_data(str(design_folder / "tran.csv"))
    d0, d1, d2, stable, sr_p, t_p, sr_n, t_n = \
        analyze_amplifier_performance(vin, vout, t, 0.01)
    settling_valid = bool(np.isfinite(t_p) and np.isfinite(t_n))
    feasible = bool(check_feasibility(measured, evaluator.constraints,
                                      evaluator.directions))
    manifest = {
        "experiment": "EXP-007_d292_tt_waveform_validation",
        "status": "SPICE_COMPLETED_EXTRACTOR_CHECK_PENDING_VISUAL_REVIEW",
        "design_id": "D292",
        "corner": "TT_3.3V_27C",
        "single_ngspice_evaluation": 1,
        "ATLAS_sha": report["ATLAS_sha"],
        "original_EXP006_trajectory_sha256": EXPECTED_TRAJECTORY_SHA,
        "measurements": {k: float(v) for k, v in measured.items()},
        "comparison": differences,
        "extracted_tt_feasible": feasible,
        "settling_both_edges_have_finite_time": settling_valid,
        "settling_time_rise_s": float(t_p),
        "settling_time_fall_s": float(t_n),
        "pre_step_stable_flag": bool(stable),
        "no_ac_missing_crossing_sentinel": bool(
            measured["ugbw_min"] != 1.0 and measured["phm_min"] != -180.0
        ),
        "files": {
            p.name: {"sha256": sha256(p), "bytes": p.stat().st_size}
            for p in [netlist, *(design_folder / f for f in RAW_FILES)]
        },
    }
    (out / "validation_summary.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=True) + "\n", encoding="utf-8"
    )
    print(f"[COMPLETE] One TT SPICE evaluation: {out}")
    print(f"[TT] extracted_feasible={feasible}; 2-edge settling valid={settling_valid}")
    for k, v in differences.items():
        print(f"  {k}: original={v['original']:.12g}, "
              f"retest={v['retest']:.12g}, delta={v['absolute_difference']:+.4g}")
    print("[RAW] ac.csv, dc.csv, dc_sweep.csv, tran.csv, generated .cir PRESERVED")
    print("[NEXT] Visually inspect Bode plot and transient before calling it physically verified.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true",
                    help="Authorize exactly ONE new D292 TT ngspice evaluation")
    args = ap.parse_args()
    row = read_d292()
    report = preflight()
    print("[PREFLIGHT] EXP-006 D292 and source SHA verified")
    print(f"[PREFLIGHT] ATLAS={report['ATLAS_sha'][:12]}, ngspice={report['ngspice_executable']}")
    print("[DESIGN]", ", ".join(f"{k}={row[k]}" for k in PARAMS))
    print("[SCOPE] TT 3.3V 27C; one point; NO optimizer/GP/TDA; preserves CSV/waveforms")
    if not args.execute:
        print("[SAFE] Read-only. To run one SPICE evaluation, add --execute.")
        return
    run_one(row, report)


if __name__ == "__main__":
    main()
