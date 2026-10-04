import csv
import os
import sys
from collections import Counter, OrderedDict

import numpy as np

ATLAS_ROOT = os.environ.get("ATLAS_ROOT", os.path.expanduser("~/atlas"))
if ATLAS_ROOT not in sys.path:
    sys.path.insert(0, ATLAS_ROOT)
os.chdir(ATLAS_ROOT)

from topbo.circuit_eval import CircuitEvaluator
from topbo.optimizers import ATLAS
from topbo.utils import check_feasibility


YAML_PATH = (
    "eval_engines/ngspice/ngspice_inputs/yaml_files/"
    "two_stage_opamp_gf180.yaml"
)

DATA_DIR = os.path.expanduser(
    "~/research_intern/experiments/"
    "EXP-002_atlas_initial_design_pvt/data"
)

DESIGN_POINTS_PATH = os.path.join(DATA_DIR, "design_points.csv")
CORNER_METRICS_PATH = os.path.join(DATA_DIR, "corner_metrics.csv")

N_INIT = 20
SEED = 42


def short_corner_name(name):
    parts = name.split("_")
    process = parts[-3].upper()
    voltage = parts[-2] + "V"
    temperature = "m40C" if parts[-1] == "m40" else parts[-1] + "C"
    return f"{process}_{voltage}_{temperature}"


def read_existing_design_ids(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return set()

    with open(path, newline="") as f:
        return {row["design_id"] for row in csv.DictReader(f)}


def read_corner_counts(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return Counter()

    with open(path, newline="") as f:
        return Counter(row["design_id"] for row in csv.DictReader(f))


def append_rows(path, fieldnames, rows):
    file_exists = os.path.exists(path) and os.path.getsize(path) > 0

    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def evaluate_all_corners(evaluator, state, design_id):
    rows = []

    # TT
    _, specs_list, _ = evaluator.sim_env.run(state)
    tt = evaluator._remap_specs(specs_list[0])
    rows.append({
        "design_id": design_id,
        "corner": "TT_3.3V_27C",
        **tt,
        "feasible": check_feasibility(
            tt, evaluator.constraints, evaluator.directions
        ),
    })

    # Remaining 16 corners. CircuitEvaluator configures up to 8 in parallel.
    _, pvt_specs_list, _ = evaluator.sim_env_pvt.run(state)

    for name, raw_specs in zip(evaluator.corner_names, pvt_specs_list):
        if raw_specs is None:
            raise RuntimeError(
                f"{design_id}: simulation failed at corner {name}"
            )

        specs = evaluator._remap_specs(raw_specs)
        rows.append({
            "design_id": design_id,
            "corner": short_corner_name(name),
            **specs,
            "feasible": check_feasibility(
                specs, evaluator.constraints, evaluator.directions
            ),
        })

    if len(rows) != 17:
        raise RuntimeError(
            f"{design_id}: expected 17 corner rows, got {len(rows)}"
        )

    return rows


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    evaluator = CircuitEvaluator(
        YAML_PATH,
        root_dir="tmp/exp002_pvt_initial_design",
        pvt=True,
    )

    # Reproduce the ATLAS default initial-design set exactly.
    atlas = ATLAS()
    x_init = atlas._initial_design(
        evaluator,
        evaluator.param_bounds,
        evaluator.log_scale,
        N_INIT,
        SEED,
    )
    x_init = np.array([evaluator._round_params(x) for x in x_init])

    expected_d000 = evaluator._round_params(evaluator.init_params)
    if not np.allclose(x_init[0], expected_d000, rtol=0.0, atol=0.0):
        raise RuntimeError(
            "The first ATLAS initial point is not the YAML init_params."
        )

    existing_designs = read_existing_design_ids(DESIGN_POINTS_PATH)
    corner_counts = read_corner_counts(CORNER_METRICS_PATH)

    design_fields = ["design_id", *evaluator.param_names]
    metric_fields = [
        "design_id",
        "corner",
        "gain_min",
        "ibias_max",
        "phm_min",
        "t_settle_max",
        "ugbw_min",
        "vswing_min",
        "feasible",
    ]

    # D000 is EXP-001. Evaluate only the remaining 19 points here.
    for index in range(1, N_INIT):
        design_id = f"D{index:03d}"

        if design_id in existing_designs and corner_counts[design_id] == 17:
            print(f"[SKIP] {design_id}: already complete")
            continue

        if design_id in existing_designs or corner_counts[design_id] != 0:
            raise RuntimeError(
                f"{design_id}: partial/inconsistent existing data detected. "
                "Inspect the CSVs before rerunning."
            )

        x = x_init[index]
        state = OrderedDict(zip(evaluator.param_names, x.tolist()))

        print(f"[RUN] {design_id}")
        rows = evaluate_all_corners(evaluator, state, design_id)

        # Save only after all 17 corners for this design have completed.
        append_rows(
            DESIGN_POINTS_PATH,
            design_fields,
            [{"design_id": design_id, **dict(state)}],
        )
        append_rows(
            CORNER_METRICS_PATH,
            metric_fields,
            rows,
        )

        existing_designs.add(design_id)
        corner_counts[design_id] = 17

        n_feasible = sum(bool(row["feasible"]) for row in rows)
        print(
            f"[DONE] {design_id}: "
            f"{n_feasible}/17 corners feasible"
        )

    print()
    print("Saved:", DESIGN_POINTS_PATH)
    print("Saved:", CORNER_METRICS_PATH)


if __name__ == "__main__":
    main()
