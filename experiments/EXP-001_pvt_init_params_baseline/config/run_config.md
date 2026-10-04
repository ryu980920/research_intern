# EXP-001 Configuration

## Circuit

- YAML: `eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml`
- Circuit: two-stage GF180 op-amp
- Design point source: YAML `init_params`

## init_params

```text
wp1 = 17.33e-6
wn1 = 88.76e-6
wp3 = 72.10e-6
wn3 = 46.21e-6
wn4 = 19.64e-6
wn5 = 70.00e-6
cc  = 3.48e-12
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

## PVT

17 corners total:

- TT: 3.3 V, 27 C
- FF/SS/FS/SF at 3.0 V, -40 C
- FF/SS/FS/SF at 3.6 V, -40 C
- FF/SS/FS/SF at 3.0 V, 125 C
- FF/SS/FS/SF at 3.6 V, 125 C

## GF180 Statistical Settings

```spice
sw_stat_global = 0
sw_stat_mismatch = 0
```

Reason: isolate deterministic PVT response from Monte Carlo process/mismatch variation.

## Reproducibility Identifiers

- ATLAS commit SHA: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- GF180 PDK commit SHA: `9f992d5a9186d1f7820c58f039c484ad35b2edea`
- ngspice: `ngspice-44.2`
- ngspice solver build: `KLU Direct Linear Solver`
- Python: `3.10.22`

These identifiers correspond to the local environment used for EXP-001.
