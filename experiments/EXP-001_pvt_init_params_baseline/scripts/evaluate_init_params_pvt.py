import os
import csv
import sys
from collections import OrderedDict

ATLAS_ROOT = os.environ.get("ATLAS_ROOT", os.path.expanduser("~/atlas"))
if ATLAS_ROOT not in sys.path:
    sys.path.insert(0, ATLAS_ROOT)
os.chdir(ATLAS_ROOT)

from topbo.circuit_eval import CircuitEvaluator
from topbo.utils import check_feasibility

yaml_path = "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"

e = CircuitEvaluator(
    yaml_path,
    root_dir="tmp/pvt_init_check",
    pvt=True
)

design_id = "D000"

x = e._round_params(e.init_params)
state = OrderedDict(zip(e.param_names, x.tolist()))

rows = []

# TT corner
_, specs_list, _ = e.sim_env.run(state)
tt = e._remap_specs(specs_list[0])

rows.append({
    "design_id": design_id,
    "corner": "TT_3.3V_27C",
    **tt,
    "feasible": check_feasibility(tt, e.constraints, e.directions)
})

# Remaining 16 PVT corners
for name, sim in zip(e.corner_names, e.corner_sims):
    _, specs_list, _ = sim.run(state)
    specs = e._remap_specs(specs_list[0])

    # Example:
    # two_stage_opamp_cont_gf180_tran_ff_3.0_m40
    # -> FF_3.0V_m40C
    parts = name.split("_")
    process = parts[-3].upper()
    voltage = parts[-2] + "V"
    temperature = "m40C" if parts[-1] == "m40" else parts[-1] + "C"
    short_name = f"{process}_{voltage}_{temperature}"

    rows.append({
        "design_id": design_id,
        "corner": short_name,
        **specs,
        "feasible": check_feasibility(specs, e.constraints, e.directions)
    })

for row in rows:
    print(row)

data_dir = os.path.expanduser(
    "~/research_intern/experiments/EXP-001_pvt_init_params_baseline/data"
)
os.makedirs(data_dir, exist_ok=True)

design_points_path = os.path.join(data_dir, "design_points.csv")
corner_metrics_path = os.path.join(data_dir, "corner_metrics.csv")

with open(design_points_path, "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["design_id", *e.param_names],
    )
    writer.writeheader()
    writer.writerow({
        "design_id": design_id,
        **dict(state),
    })

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

with open(corner_metrics_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print()
print("Saved:", design_points_path)
print("Saved:", corner_metrics_path)
