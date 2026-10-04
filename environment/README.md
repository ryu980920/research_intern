# Environment

이 디렉터리는 ATLAS 기반 아날로그 강건설계 연구의 실행환경과 재현성 관련 설정을 기록한다.

## Current Local Setup

- Host: Windows + WSL2
- Linux: Ubuntu 22.04
- Conda environment: `atlas`
- Python: 3.10.22
- ATLAS: `youngmin0oh/atlas` @ `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- Simulator: ngspice 44.2 (KLU Direct Linear Solver build)
- PDK: GF180 primitive ngspice model @ `9f992d5a9186d1f7820c58f039c484ad35b2edea`
- PDK root: `$HOME/pdks`
- Environment variable: `PDK_ROOT=$HOME/pdks`

새 PC 설치 과정 자체는 연구 결과가 아니므로 세부 설치 명령은 최소화하고, 연구 결과에 영향을 주는 설정만 기록한다.

## GF180 Statistical Model Setting

### Problem

GF180 `design.ngspice`의 기본 설정은 다음과 같이 statistical variation이 켜져 있었다.

```spice
sw_stat_global = 1
sw_stat_mismatch = 1
```

이 상태에서는 동일한 TT netlist와 동일한 transistor sizing을 반복 실행해도 global process variation과 local mismatch가 랜덤하게 적용되어 결과가 달라졌다.

즉 초기 smoke test는 의도한 deterministic nominal TT evaluation이 아니라, TT model을 기준으로 서로 다른 statistical sample을 평가하고 있었다.

### Baseline Fix

현재 PVT baseline 연구에서는 다음과 같이 설정한다.

```spice
sw_stat_global = 0
sw_stat_mismatch = 0
```

로컬 원본은 `design.ngspice.bak`으로 백업했다.

### Verification

수정 후 동일 TT netlist를 3회 직접 실행했을 때 `ac.csv`, `dc.csv`, `dc_sweep.csv`, `tran.csv`의 SHA-256이 각각 3회 모두 동일했다.

또한 `CircuitEvaluator.evaluate_tt(init_params)`를 3회 반복했을 때 다음 metric이 정확히 동일하게 재현됐다.

```text
gain_min      = 543.4600000000053
ibias_max     = 0.00055581049
phm_min       = 29.214151096544953
t_settle_max  = 1.6563499999999829e-06
ugbw_min      = 25927856.743177846
vswing_min    = 1.0206877
```

## Research Rule

현재 PVT 연구에서는 **PVT variation과 Monte Carlo/mismatch variation을 분리**한다.

```text
PVT baseline
→ statistical switches OFF
→ same design x + same corner = same metrics

Monte Carlo / mismatch study
→ statistical switches explicitly ON
→ repeated random samples evaluated separately
```

이 구분을 유지해야 corner 변화 때문에 성능이 달라진 것인지, random process/mismatch 때문에 달라진 것인지 해석할 수 있다.

관련 연구일지: `logs/2026-10/2026-10-04.md`
