#!/usr/bin/env python3
"""Read-only ATLAS paper-reproduction preflight. No SPICE simulation is run.

In (atlas) conda, from ~/research_intern:
    python docs/reproduction/inspect_atlas_environment.py

Optionally save a machine-local JSON snapshot to a *new* file:
    python docs/reproduction/inspect_atlas_environment.py --out /some/new/path.json

Never changes ATLAS source files, PDK switches, EXP-003, or EXP-005 outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

EXPECTED_ATLAS_SHA = "dd23c5ba7beb598909be593e4a84c81dab92cc69"


def digest(path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd(argv, cwd=None):
    try:
        p = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=12,
            check=False,
        )
        return {"returncode": p.returncode, "output": (p.stdout + "\n" + p.stderr).strip()[:2000]}
    except Exception as exc:
        return {"error": str(exc)}


def stat_value(content, name):
    m = re.search(rf"\b{re.escape(name)}\s*=\s*([01])\b", content)
    return int(m.group(1)) if m else None


def versions():
    names = ("numpy", "torch", "botorch", "gpytorch", "scipy", "PyYAML")
    result = {}
    for name in names:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, help="Write JSON only to a *new* filename")
    args = ap.parse_args()

    atlas = Path(os.getenv("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
    pdk = Path(os.getenv("PDK_ROOT", "~/pdks")).expanduser().resolve()
    yaml_path = atlas / "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"
    wrapper_path = atlas / "eval_engines/ngspice/ngspice_wrapper_parallel.py"
    runner_path = atlas / "run_experiment.py"
    evaluator_path = atlas / "topbo/circuit_eval.py"
    netlist_path = atlas / "eval_engines/ngspice/ngspice_inputs/netlist/two_stage_opamp_cont_gf180_tran_tt_3.3_27.cir"

    report = {
        "purpose": "ATLAS ICCAD2026 vs EXP-003 paper reproduction environment preflight",
        "SPICE_simulations_run": 0,
        "ATLAS_ROOT": str(atlas),
        "ATLAS_head": cmd(["git", "-C", str(atlas), "rev-parse", "HEAD"]),
        "ATLAS_clean_worktree": cmd(["git", "-C", str(atlas), "status", "--porcelain"]),
        "pinned_expected_sha": EXPECTED_ATLAS_SHA,
        "PDK_ROOT": str(pdk),
        "ngspice_from_PATH": shutil.which("ngspice"),
        "ngspice_version_from_PATH": None,
        "pinned_runner_sha256": digest(runner_path),
        "pinned_evaluator_sha256": digest(evaluator_path),
        "pinned_wrapper_sha256": digest(wrapper_path),
        "TSA_yaml_sha256": digest(yaml_path),
        "TT_netlist_sha256": digest(netlist_path),
        "local_python_package_versions": versions(),
        "source_structure_checks": {},
        "TSA_config": {},
        "PDK_model_candidates": [],
        "warnings": [],
    }
    if report["ngspice_from_PATH"]:
        report["ngspice_version_from_PATH"] = cmd(["ngspice", "-v"])

    alternate = Path("~/ngspice-44.2-noomp/src/ngspice").expanduser()
    if alternate.exists():
        report["separate_ngspice_44_2_build"] = {
            "path": str(alternate),
            "version": cmd([str(alternate), "-v"]),
        }

    head = report["ATLAS_head"].get("output", "")
    if head != EXPECTED_ATLAS_SHA:
        report["warnings"].append("ATLAS HEAD differs from EXP-003 pinned revision")
    if report["ATLAS_clean_worktree"].get("output"):
        report["warnings"].append(
            "ATLAS working tree is not clean; inspect modifications before any reproduction"
        )

    for key, path, token in (
        ("runner_initial_design_cap", runner_path, "budget // 3"),
        ("evaluator_TT_default", evaluator_path, "pvt=False"),
        ("wrapper_calls_PATH_ngspice", wrapper_path, '["ngspice", "-b", fpath]'),
    ):
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        report["source_structure_checks"][key] = token in content
        if token not in content:
            report["warnings"].append(f"Missing expected pinned-code token: {key}")

    if yaml_path.exists():
        try:
            import yaml
            cfg = yaml.full_load(yaml_path.read_text(encoding="utf-8"))
            params = {key: [float(x) for x in val]
                      for key, val in cfg["params"].items()}
            targets = {key: [float(x) for x in val]
                       for key, val in cfg["target_specs"].items()}
            netlists = cfg["dsn_netlist"]
            d = len(params)
            n_init_60 = max(min(3 * d, 60 // 3, 50), 10)
            n_init_500 = max(min(3 * d, 500 // 3, 50), 10)
            report["TSA_config"] = {
                "parameter_bounds": params,
                "spec_targets": targets,
                "all_target_ranges_fixed": all(lo == hi for lo, hi in targets.values()),
                "n_parameters": d,
                "n_specs": len(targets),
                "num_netlists_in_YAML": len(netlists),
                "first_TT_netlist": netlists[0],
                "initial_design_budget60": n_init_60,
                "initial_design_budget500": n_init_500,
                "has_init_params": "init_params" in cfg,
            }
            if (d != 7 or len(targets) != 6 or n_init_60 != 20 or
                    n_init_500 != 21):
                report["warnings"].append("Unexpected TSA dimensions or n_init rules")
        except Exception as exc:
            report["warnings"].append(f"Cannot parse TSA YAML: {exc}")
    else:
        report["warnings"].append("TSA circuit YAML not found")

    # Candidate PDK structures differ between the public README, netlist,
    # and the user's historical workstation layout; inspect rather than guess.
    candidates = [
        pdk / "gf180/ngspice/design.ngspice",
        pdk / "gf180/models/ngspice/design.ngspice",
        pdk / "gf180/ngspice/sm141064.ngspice",
        pdk / "gf180/models/ngspice/sm141064.ngspice",
        pdk / "gf180/ngspice/smbb000149.ngspice",
        pdk / "gf180/models/ngspice/smbb000149.ngspice",
    ]
    found_design = False
    for path in candidates:
        info = {"path": str(path), "exists": path.is_file(), "sha256": digest(path)}
        if path.is_file() and path.name == "design.ngspice":
            found_design = True
            txt = path.read_text(encoding="utf-8", errors="replace")
            info["sw_stat_global"] = stat_value(txt, "sw_stat_global")
            info["sw_stat_mismatch"] = stat_value(txt, "sw_stat_mismatch")
        report["PDK_model_candidates"].append(info)
    if not found_design:
        report["warnings"].append(
            "GF180 design.ngspice not found at known layouts; inspect expanded netlist includes"
        )
    if not report["ngspice_from_PATH"]:
        report["warnings"].append("ngspice executable not present on PATH")

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        dst = args.out.expanduser()
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("x", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"[SAVED] {dst}")
    else:
        print(output)

    print(f"[PREFLIGHT] new SPICE evaluations=0 | warnings={len(report['warnings'])}")
    if report["warnings"]:
        print("[CHECK] " + "; ".join(report["warnings"]))


if __name__ == "__main__":
    main()
