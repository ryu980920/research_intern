# EXP-001 — PVT Baseline at ATLAS Initial Parameters

_Date: 2026-10-04_

## Purpose

ATLAS two-stage GF180 op-amp의 기본 `init_params` 한 점을 17개 PVT corner에서 실제로 평가해, corner-wise metric 수집이 정상 동작하는지 확인하고 향후 feasible-island 분석의 첫 baseline을 확보한다.

## Research Question

1. 동일한 design point를 17개 PVT corner에서 평가했을 때 metric이 실제로 corner별로 달라지는가?
2. metric별 worst corner는 동일한가, 서로 다른가?
3. 이 한 점의 결과가 corner-wise 정보를 유지해야 할 필요성을 조사할 근거를 제공하는가?

이 실험 하나만으로 feasible island의 존재나 구조를 결론 내리지는 않는다. Island를 보려면 여러 design point가 필요하다.

## Simulation Setup

- Circuit: two-stage op-amp, GF180
- Design point: YAML의 `init_params`
- PVT corners: TT 1개 + FF/SS/FS/SF 기반 16개 = 총 17개
- Simulator: ngspice 44.2
- PDK: GF180 primitive ngspice model
- Statistical variation:
  - `sw_stat_global = 0`
  - `sw_stat_mismatch = 0`
- 목적: PVT 영향만 분리해 deterministic하게 비교

## Parameter / Condition

| Parameter | Value |
| --- | ---: |
| wp1 | 17.33e-6 |
| wn1 | 88.76e-6 |
| wp3 | 72.10e-6 |
| wn3 | 46.21e-6 |
| wn4 | 19.64e-6 |
| wn5 | 70.00e-6 |
| cc | 3.48e-12 |

Target specifications:

| Metric | Constraint |
| --- | ---: |
| gain_min | >= 300 |
| ugbw_min | >= 20 MHz |
| phm_min | >= 60 deg |
| ibias_max | <= 1 mA |
| t_settle_max | <= 6 us |
| vswing_min | >= 0.3 V |

## Procedure

1. `CircuitEvaluator(..., pvt=True)`로 17개 corner simulator를 구성했다.
2. 동일한 `init_params`를 TT와 나머지 16개 corner에 각각 입력했다.
3. 각 corner에서 gain, Ibias, PM, settling time, UGBW, output swing을 추출했다.
4. 각 corner가 target specification을 모두 만족하는지 판정했다.
5. 17개 결과를 하나의 corner-wise metric CSV로 저장했다.

실행 스크립트: `scripts/evaluate_init_params_pvt.py`

## Data

Primary result dataset:

- `data/corner_metrics.csv`
- 17 rows = 17 PVT corners
- columns: corner, gain, Ibias, PM, settling, UGBW, Vswing, feasible

## Results

- Feasible corners: **0 / 17**
- 17개 모든 corner에서 `phm_min < 60 deg`
- 추가로 UGBW가 20 MHz 미만인 corner:
  - SS / 3.0 V / 125 C: 18.922 MHz
  - SF / 3.0 V / 125 C: 19.936 MHz

Metric별 worst corner:

| Metric | Worst corner | Worst value | Target satisfied? |
| --- | --- | ---: | --- |
| Gain | FF / 3.0 V / 125 C | 420.06 | Yes |
| Ibias | FF / 3.6 V / -40 C | 0.660 mA | Yes |
| Phase Margin | FS / 3.6 V / -40 C | 26.64 deg | **No** |
| Settling Time | SS / 3.0 V / 125 C | 2.971 us | Yes |
| UGBW | SS / 3.0 V / 125 C | 18.922 MHz | **No** |
| Vswing | FF / 3.0 V / 125 C | 0.780 V | Yes |

## Observation

metric별 worst corner가 하나로 일치하지 않았다.

- Gain / Vswing worst: FF / 3.0 V / 125 C
- Ibias worst: FF / 3.6 V / -40 C
- PM worst: FS / 3.6 V / -40 C
- Settling / UGBW worst: SS / 3.0 V / 125 C

## Interpretation

PVT worst-case compression으로 만든 spec vector는 하나의 실제 corner 상태를 그대로 나타내는 것이 아니라, metric마다 서로 다른 corner에서 가져온 worst value의 조합이 될 수 있다.

다만 design point가 한 개뿐이므로, 이 결과만으로 corner-wise feasible island가 실제로 이동/분열/소멸한다고 결론 내릴 수는 없다.

## Research Implication

첫 17-corner baseline에서 이미 metric별 worst corner가 다르다는 사실을 확인했다. 따라서 이후 여러 design point를 수집할 때는 worst-case vector만 저장하지 않고 **corner-wise metric과 feasibility를 함께 보존**해야 한다.

이 데이터가 누적되어야 다음 질문을 검증할 수 있다.

> worst-case compression이 corner별 feasible-region 구조를 얼마나 지우는가?

## Data Retention

본 실험의 연구 판단에 직접 필요한 결과는 `data/corner_metrics.csv`에 보존한다.

ngspice가 내부적으로 생성하는 AC/DC/DC-sweep/transient raw CSV는 모든 corner에 대해 상시 보존하지 않는다. feasible-region 분석에는 corner-wise metric과 feasibility가 직접 사용되며, 모든 raw waveform을 저장하면 design point 수가 증가할수록 파일 관리 비용이 크게 늘어나기 때문이다.

특정 metric의 이상값을 진단하거나 waveform 자체가 근거로 필요한 경우에는 해당 design/corner만 동일 config로 재실행해 raw waveform을 선택적으로 보존한다.

## Limitations

- design point가 YAML `init_params` 한 점뿐이다.
- 17개 corner가 모두 infeasible이므로 이 실험만으로 feasible-island의 위치, 크기, 이동 또는 persistence를 판단할 수 없다.
- 따라서 이번 결과는 corner-wise evaluation 동작과 metric별 worst-corner 차이를 확인한 baseline으로 해석한다.

## Next Experiment

다음 PVT dataset에서는:

1. 여러 design point를 정의한다.
2. 각 point에 `design_id`를 부여한다.
3. 각 design point의 17-corner metric과 feasibility를 하나의 분석용 table로 누적한다.
4. feasible / infeasible point가 함께 나타나는 영역을 확보한다.
5. 충분한 데이터가 모인 뒤 corner-wise feasible set과 worst-case compressed representation을 비교한다.
