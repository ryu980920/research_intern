# EXP-003 Configuration

## Circuit

- Circuit: two-stage GF180 op-amp
- YAML: `eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml`
- PVT mode: OFF
- Evaluation corner: TT / 3.3 V / 27 C

## ATLAS

- ATLAS commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- Method: ATLAS / `TopoBO`
- Budget: 60
- Seed: 42
- n_init: standard `n_init_for()` result = 20
- Surrogate: GP
- Early stop: ON
- Candidate pool: 50,000

## Why n_init = 20 Here

```text
n_params = 7
budget = 60

n_init = max(min(3*n_params, budget//3, 50), 10)
       = max(min(21, 20, 50), 10)
       = 20
```

This intentionally aligns the standard-run initial definition with EXP-002 D000-D019.

## Parameter Bounds

```text
wp1: 0.5e-6  ~ 100e-6
wn1: 0.5e-6  ~ 100e-6
wp3: 0.5e-6  ~ 100e-6
wn3: 0.5e-6  ~ 100e-6
wn4: 0.5e-6  ~ 100e-6
wn5: 0.5e-6  ~ 100e-6
cc : 0.1e-12 ~ 10e-12
```

## Target Specs

```text
gain_min      >= 300
vswing_min    >= 0.3
ugbw_min      >= 2e7
phm_min       >= 60
ibias_max     <= 0.001
t_settle_max  <= 6e-6
```

## GF180 Statistical Settings

Required for this deterministic TT baseline:

```spice
sw_stat_global = 0
sw_stat_mismatch = 0
```

## Output

Primary:

- `data/trajectory.csv`
- `data/run_summary.json`

Execution evidence:

- `raw/atlas_logs/<run_id>/config.json`
- `raw/atlas_logs/<run_id>/iterations.jsonl`
- `raw/atlas_logs/<run_id>/progress.log`
- `raw/atlas_logs/<run_id>/results.json`
