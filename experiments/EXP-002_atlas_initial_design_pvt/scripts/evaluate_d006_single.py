import csv
import os
import sys
from collections import OrderedDict

import numpy as np

ATLAS_ROOT = os.environ.get("ATLAS_ROOT", os.path.expanduser("~/atlas"))
if ATLAS_ROOT not in sys.path:
    sys.path.insert(0, ATLAS_ROOT)
os.chdir(ATLAS_ROOT)

from topbo.circuit_eval import CircuitEvaluator
from topbo.optimizers import TopoBO
from topbo.utils import check_feasibility


YAML_PATH = (
    "eval_engines/ngspice/ngspice_inputs/yaml_files/"
    "two_stage_opamp_gf180.yaml"
)

DESIGN_ID = "D006"
N_INIT = 20
SEED = 42

OUTPUT_DIR = os.path.expanduser(
    "~/research_intern/experiments/"
    "EXP-002_atlas_initial_design_pvt/diagnostics/D006"
)

DESIGN_CSV = os.path.join(OUTPUT_DIR, "design_point.csv")
METRIC_CSV = os.path.join(OUTPUT_DIR, "corner_metrics.csv")


def short_corner_name(name):
    parts = name.split("_")
    process = parts[-3].upper()
    voltage = parts[-2] + "V"
    temperature = "m40C" if parts[-1] == "m40" else parts[-1] + "C"
    return f"{process}_{voltage}_{temperature}"


def append_metric(row):
    fieldnames = [
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

    file_exists = os.path.exists(METRIC_CSV) and os.path.getsize(METRIC_CSV) > 0

    with open(METRIC_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    evaluator = CircuitEvaluator(
        YAML_PATH,
        root_dir="tmp/exp002_d006_single",
        pvt=True,
    )

    atlas = TopoBO()
    x_init = atlas._initial_design(
        evaluator,
        evaluator.param_bounds,
        evaluator.log_scale,
        N_INIT,
        SEED,
    )
    x_init = np.array([evaluator._round_params(x) for x in x_init])

    x = x_init[6]
    state = OrderedDict(zip(evaluator.param_names, x.tolist()))

    print()
    print("======================================")
    print("D006 Design Parameters")
    print("======================================")
    for key, value in state.items():
        print(f"{key}: {value}")

    with open(DESIGN_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["design_id", *evaluator.param_names],
        )
        writer.writeheader()
        writer.writerow({
            "design_id": DESIGN_ID,
            **dict(state),
        })

    print()
    print("Saved design:")
    print(DESIGN_CSV)

    if os.path.exists(METRIC_CSV):
        os.remove(METRIC_CSV)

    print()
    print("[RUN] D006 - TT_3.3V_27C")

    _, specs_list, _ = evaluator.sim_env.run(state)
    tt = evaluator._remap_specs(specs_list[0])

    row = {
        "design_id": DESIGN_ID,
        "corner": "TT_3.3V_27C",
        **tt,
        "feasible": check_feasibility(
            tt,
            evaluator.constraints,
            evaluator.directions,
        ),
    }

    append_metric(row)
    print("[DONE] D006 - TT_3.3V_27C")

    for name, sim in zip(evaluator.corner_names, evaluator.corner_sims):
        corner = short_corner_name(name)

        print()
        print(f"[RUN] D006 - {corner}")

        _, specs_list, _ = sim.run(state)
        specs = evaluator._remap_specs(specs_list[0])

        row = {
            "design_id": DESIGN_ID,
            "corner": corner,
            **specs,
            "feasible": check_feasibility(
                specs,
                evaluator.constraints,
                evaluator.directions,
            ),
        }

        append_metric(row)
        print(f"[DONE] D006 - {corner}")

    print()
    print("======================================")
    print("D006 COMPLETE")
    print("======================================")
    print()
    print("Saved:")
    print(DESIGN_CSV)
    print(METRIC_CSV)


if __name__ == "__main__":
    main()
