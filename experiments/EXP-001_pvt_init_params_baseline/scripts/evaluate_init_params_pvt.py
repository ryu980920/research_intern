import os
import csv
from collections import OrderedDict

from topbo.circuit_eval import CircuitEvaluator
from topbo.utils import check_feasibility

yaml_path = "eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml"

e = CircuitEvaluator(
    yaml_path,
    root_dir="tmp/pvt_init_check",
    pvt=True
)

x = e._round_params(e.init_params)
state = OrderedDict(zip(e.param_names, x.tolist()))

rows = []

# TT corner
_, specs_list, _ = e.sim_env.run(state)
tt = e._remap_specs(specs_list[0])

rows.append({
    "corner": "TT_3.3V_27C",
    **tt,
    "feasible": check_feasibility(tt, e.constraints, e.directions)
})

# Remaining 16 PVT corners
for name, sim in zip(e.corner_names, e.corner_sims):
    _, specs_list, _ = sim.run(state)
    specs = e._remap_specs(specs_list[0])

    rows.append({
        "corner": name,
        **specs,
        "feasible": check_feasibility(specs, e.constraints, e.directions)
    })

for row in rows:
    print(row)

out_path = os.path.expanduser(
    "~/research_intern/data/raw/pvt_init_params_corner_metrics.csv"
)

os.makedirs(os.path.dirname(out_path), exist_ok=True)

fieldnames = [
    "corner",
    "gain_min",
    "ibias_max",
    "phm_min",
    "t_settle_max",
    "ugbw_min",
    "vswing_min",
    "feasible",
]

with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print()
print("Saved:", out_path)
