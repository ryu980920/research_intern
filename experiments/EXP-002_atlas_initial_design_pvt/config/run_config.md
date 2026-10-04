# EXP-002 Configuration

## Circuit

- Circuit: two-stage GF180 op-amp
- YAML: `eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml`

## Sampling

ATLAS default initial-design rule을 그대로 사용한다.

```text
n_init = 20
seed   = 42

D000        : YAML init_params (EXP-001에서 이미 평가)
D001-D012   : init_params 주변 local perturbation 12 points
D013-D019   : global LHS 7 points
```

ATLAS의 현재 코드에서 local perturbation radius는 각 point마다 0.03–0.15 범위에서 선택되며, parameter의 log-scale 설정을 반영한다.

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

## PVT

17 corners:

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

## Reproducibility

- ATLAS commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- GF180 PDK commit: `9f992d5a9186d1f7820c58f039c484ad35b2edea`
- ngspice: 44.2
- Python: 3.10.22
