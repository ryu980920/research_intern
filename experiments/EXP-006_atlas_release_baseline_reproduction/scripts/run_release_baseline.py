#!/usr/bin/env python3
"""EXP-006: released-ATLAS GF180 TT baseline (paper-condition reproduction track).

Default = READ-ONLY preflight. No SPICE unless --execute is explicitly supplied.
After --execute, the original ATLAS TopoBO.optimize() performs at most 500 TT
design evaluations (seed=42, 21 initial points), with first-feasible early stop.

Files go to a NEW, timestamped directory under EXP-006/raw/runs/.
No changes to pinned ATLAS, EXP-003, or EXP-005.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

EXP_DIR = Path(__file__).resolve().parents[1]
RESEARCH = EXP_DIR.parents[1]
ATLAS = Path(os.getenv("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
PDK = Path(os.getenv("PDK_ROOT", "~/pdks")).expanduser().resolve()
PINNED_SHA = "dd23c5ba7beb598909be593e4a84c81dab92cc69"
BUDGET, SEED, N_INIT = 500, 42, 21
YAML_REL = "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"
EXPECTED_PDK_SHA = {
    "design.ngspice": "b55dcc56441acbe9946d55368a2702310f5392c49f7ece7ee56bce0600aca56c",
    "sm141064.ngspice": "73fc67d38747d95ce03f3c2ba5f0a25c98f56a293363a9df4c971a3a28a3dcda",
    "smbb000149.ngspice": "3b0995ba269b6cbc468f34fe977c4d21b0faa2935e02f4b2a5d24f58ea66affe",
}
METRICS = ("gain_min", "ibias_max", "phm_min", "t_settle_max", "ugbw_min", "vswing_min")
PARAMS = ("wp1", "wn1", "wp3", "wn3", "wn4", "wn5", "cc")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(1048576), b""):
            h.update(part)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ATLAS), *args],
                                   text=True, timeout=15).strip()


def preflight() -> dict:
    problems = []
    atlas_sha = git("rev-parse", "HEAD")
    if atlas_sha != PINNED_SHA:
        problems.append(f"ATLAS SHA differs: expected {PINNED_SHA}, got {atlas_sha}")

    status = git("status", "--porcelain").splitlines()
    tracked_changes = [s for s in status if not s.startswith("?? ")]
    if tracked_changes:
        problems.append(f"ATLAS tracked changes present: {tracked_changes}")

    exe = shutil.which("ngspice")
    if not exe:
        problems.append("ngspice is absent from PATH")
        version = "NOT FOUND"
    else:
        v = subprocess.run([exe, "-v"], capture_output=True, text=True, timeout=15)
        version = (v.stdout + v.stderr).strip()
        if "ngspice-44.2" not in version:
            problems.append("Expected ngspice-44.2 from current PATH")

    pdk_files = {}
    design_text = ""
    for name, expected in EXPECTED_PDK_SHA.items():
        path = PDK / "gf180" / "ngspice" / name
        actual = sha256(path) if path.exists() else None
        pdk_files[name] = {"path": str(path), "sha256": actual}
        if actual != expected:
            problems.append(f"PDK {name} hash mismatch/missing")
        if name == "design.ngspice" and path.exists():
            design_text = path.read_text(errors="replace")

    sw = {}
    for key in ("sw_stat_global", "sw_stat_mismatch"):
        m = re.search(rf"\b{key}\s*=\s*([01])\b", design_text)
        sw[key] = int(m.group(1)) if m else None
        if sw[key] != 0:
            problems.append(f"MC switch {key} is not confirmed OFF")

    yaml_path = ATLAS / YAML_REL
    config = {}
    if yaml_path.exists():
        import yaml
        config = yaml.full_load(yaml_path.read_text())
        if len(config.get("params", {})) != len(PARAMS):
            problems.append("TSA parameter count mismatch")
        if set(config.get("target_specs", {})) != set(METRICS):
            problems.append("TSA spec names mismatch")
        if any(float(v[0]) != float(v[1])
               for v in config.get("target_specs", {}).values()):
            problems.append("TSA target ranges are not fixed")
    else:
        problems.append("TSA circuit YAML missing")

    spiceinit = ATLAS / "eval_engines/ngspice/ngspice_inputs/netlist/.spiceinit"
    spiceinit_content = spiceinit.read_text(errors="replace").strip() if spiceinit.exists() else None

    return {
        "experiment": "EXP-006_atlas_release_baseline_reproduction",
        "purpose": "Released-code baseline, NOT exact paper-era reproduction",
        "ATLAS_ROOT": str(ATLAS), "ATLAS_sha": atlas_sha,
        "tracked_changes": tracked_changes, "untracked_files": [x for x in status if x.startswith("?? ")],
        "ngspice_executable": exe, "ngspice_version": version.splitlines()[1:5],
        "PDK_ROOT": str(PDK), "pdk_files": pdk_files, "statistical_switches": sw,
        "TSA_yaml_sha256": sha256(yaml_path) if yaml_path.exists() else None,
        "TSA_netlist_sha256": sha256(ATLAS / config["dsn_netlist"][0])
                                 if config and (ATLAS / config["dsn_netlist"][0]).is_file()
                                 else None,
        "targets": {k: [float(y) for y in v] for k, v in config.get("target_specs", {}).items()},
        "spiceinit_source_netlist_dir": spiceinit_content,
        "spiceinit_read_by_subprocess": "UNVERIFIED: ngspice launched with caller cwd=ATLAS root",
        "budget": BUDGET, "seed": SEED, "n_init_expected": N_INIT,
        "surrogate": "gp", "early_stop": True, "PVT": False,
        "new_SPICE_evaluations_during_preflight": 0,
        "preflight_problems": problems,
    }


def margins(specs, evaluator):
    d = {}
    for name in evaluator.spec_names:
        val = float(specs[name])
        bound = float(evaluator.constraints[name])
        d[name] = ((val - bound) if evaluator.directions[name] == "min"
                   else (bound - val)) / (abs(bound) + 1e-30)
    return d


def export_tables(source: Path, folder: Path, n_init: int) -> None:
    with source.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("Empty trajectory: no results to export")
    for idx, row in enumerate(rows):
        if int(row["iteration"]) != idx or row["design_id"] != f"D{idx:03d}":
            raise RuntimeError(f"Invalid run trajectory ordering at row {idx}")
        if row["phase"] != ("init" if idx < n_init else "adaptive"):
            raise RuntimeError(f"Invalid phase at row {idx}")
    folder.mkdir(parents=True, exist_ok=False)
    with (folder / "design_points.csv").open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, ["design_id", *PARAMS])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})
    with (folder / "corner_metrics.csv").open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, ["design_id", "corner", *METRICS, "feasible"])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **{key: row[key] for key in writer.fieldnames if key != "corner"},
                "corner": "TT_3.3V_27C",
            })


def execute(report: dict) -> None:
    if report["preflight_problems"]:
        raise RuntimeError("Preflight problems: " + "; ".join(report["preflight_problems"]))
    os.environ["PDK_ROOT"] = str(PDK)
    os.chdir(ATLAS)
    if str(ATLAS) not in sys.path:
        sys.path.insert(0, str(ATLAS))

    from run_experiment import n_init_for
    from topbo.circuit_eval import CircuitEvaluator
    from topbo.optimizers import get_optimizer
    from topbo.utils import check_feasibility

    # Each execution owns its own SPICE working directory and logged dataset.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = EXP_DIR / "raw" / "runs" / f"release_B500_S42_{stamp}"
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite run: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)
    with (run_dir / "environment_preflight.json").open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")

    evaluator = CircuitEvaluator(YAML_REL, root_dir=str(run_dir / "spice_tmp"), pvt=False)
    n_init = n_init_for(evaluator, BUDGET)
    if n_init != N_INIT:
        raise RuntimeError(f"n_init expected 21, actual {n_init}; no simulation launched")

    orig = evaluator.evaluate
    trajectory = run_dir / "trajectory.csv"
    columns = [
        "iteration", "design_id", "phase", *evaluator.param_names,
        *evaluator.spec_names, "feasible", "n_specs_passed",
        "worst_margin", "total_violation",
    ]
    with trajectory.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        f.flush()
        os.fsync(f.fileno())
        counter = 0

        def record(x):
            nonlocal counter
            result = orig(x)
            effective = evaluator._round_params(
                np.clip(np.asarray(x, dtype=float),
                        evaluator.param_bounds[:, 0], evaluator.param_bounds[:, 1])
            )
            mm = margins(result, evaluator)
            passed = check_feasibility(result, evaluator.constraints, evaluator.directions)
            row = {
                "iteration": counter,
                "design_id": f"D{counter:03d}",
                "phase": "init" if counter < n_init else "adaptive",
                "feasible": passed,
                "n_specs_passed": sum(v >= 0 for v in mm.values()),
                "worst_margin": min(mm.values()),
                "total_violation": sum(max(0, -v) for v in mm.values()),
            }
            row.update(dict(zip(evaluator.param_names, [float(v) for v in effective])))
            row.update({name: float(result[name]) for name in evaluator.spec_names})
            writer.writerow(row)
            f.flush()
            os.fsync(f.fileno())
            counter += 1
            return result

        evaluator.evaluate = record
        try:
            optimizer = get_optimizer("ATLAS")
            _, results = optimizer.optimize(
                evaluator, budget=BUDGET, n_init=n_init, seed=SEED,
                log_root=str(run_dir / "atlas_logs"),
                surrogate="gp", early_stop=True, gp_time_limit=10.0,
            )
        finally:
            evaluator.evaluate = orig

    export_tables(trajectory, run_dir / "data", n_init)
    run_summary = {
        **results, "total_evaluations_recorded": counter,
        "first_feasible_evaluation_1based": (
            results["first_feasible_iter"] + 1
            if results.get("first_feasible_iter") is not None else None
        ),
        "trajectory_sha256": sha256(trajectory),
        "surrogate": "gp", "PVT": False, "n_init": n_init,
        "ATLAS_sha": PINNED_SHA, "netlist_sha256": report["TSA_netlist_sha256"],
    }
    with (run_dir / "reproduction_summary.json").open("x", encoding="utf-8") as f:
        json.dump(run_summary, f, indent=2)
        f.write("\n")
    print(f"[COMPLETE] {run_dir}", flush=True)
    print(f"[BUDGET] evaluated={counter} / max {BUDGET}", flush=True)
    print(f"[RESULT] success={results.get('success')} / first_1based="
          f"{run_summary['first_feasible_evaluation_1based']}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                        help="Explicitly authorize up to 500 new TT SPICE evaluations")
    args = parser.parse_args()
    report = preflight()
    print("[PREFLIGHT] source=" + str(report["ATLAS_sha"])[:12]
          + " | ngspice=" + str(report["ngspice_executable"])
          + " | problems=" + str(len(report["preflight_problems"])))
    print("[SETUP] TSA 7D/6spec TT; seed=42; n_init=21; GP pinned; budget=500;"
          " early_stop=True")
    print("[SPICEINIT] Recorded netlist-dir setting, activation not assumed")
    if report["preflight_problems"]:
        print("[ISSUES] " + "; ".join(report["preflight_problems"]))
    if not args.execute:
        print("[SAFE] No files changed, no new SPICE. --execute is required to run.")
        return
    execute(report)


if __name__ == "__main__":
    main()
