# EXP-002 — PVT Evaluation of the ATLAS Initial Design Set

_Date started: 2026-10-04_  
_Status: Completed_

## Purpose

ATLAS가 optimization을 시작할 때 실제로 사용하는 initial design set을 17개 PVT corner에서 평가해, 단일 `init_params` 점을 넘어 corner-wise feasible-region 구조가 나타나기 시작하는지 확인한다.

EXP-001의 `D000`은 이미 동일한 deterministic PVT 조건에서 평가했으므로 다시 시뮬레이션하지 않는다. EXP-002에서는 나머지 `D001`–`D019`를 추가했다.

최종적으로 EXP-001 + EXP-002를 합치면 **20 design points × 17 corners = 340 corner evaluations**가 된다.

## Research Question

1. ATLAS의 실제 initial design set에서 feasible / infeasible design이 함께 나타나는가?
2. 같은 design이라도 corner별 feasibility가 달라지는가?
3. metric별 worst corner는 design point에 따라 바뀌는가?
4. 이 20-point pilot이 feasible-island 분석을 확대할 근거를 제공하는가?

## Hypothesis

초기 design set에서도 일부 feasible 또는 near-feasible point가 나타나고, corner에 따라 feasibility와 worst-corner identity가 달라질 가능성이 있다고 보았다.

만약 충분한 feasible point가 나타나면 corner-wise feasible-set 이동을 분석할 수 있고, 그렇지 않으면 sampling 확대보다 먼저 feasible region 탐색 전략을 다시 설계해야 한다.

## Why 20 Points First

현재 ATLAS의 GP-based optimizer 기본값은 `n_init=20`이다.

YAML에 `init_params`가 있을 때 initial design은 다음 방식으로 만들어진다.

- 1 point: YAML `init_params` → EXP-001의 `D000`
- 12 points: `init_params` 주변 local perturbation
- 7 points: global Latin Hypercube Sampling (LHS)

따라서 처음부터 임의의 100 points를 생성하기보다, **ATLAS가 실제 optimization 시작 시 보는 20 points를 먼저 PVT로 평가**하는 것이 baseline 비교에 더 직접적이다.

## Simulation Setup

- Circuit: two-stage GF180 op-amp
- Simulator: ngspice 44.2
- Python: 3.10.22
- ATLAS commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- GF180 PDK commit: `9f992d5a9186d1f7820c58f039c484ad35b2edea`
- Statistical variation:
  - `sw_stat_global = 0`
  - `sw_stat_mismatch = 0`
- PVT corners: 17
- Initial design rule:
  - D000: YAML init_params
  - D001-D012: local perturbation
  - D013-D019: global LHS
- Seed: 42

Target specifications:

| Metric | Constraint |
| --- | ---: |
| gain_min | >= 300 |
| ugbw_min | >= 20 MHz |
| phm_min | >= 60 deg |
| ibias_max | <= 1 mA |
| t_settle_max | <= 6 us |
| vswing_min | >= 0.3 V |

상세 조건: `config/run_config.md`

## Procedure

1. ATLAS의 실제 `_initial_design(..., n_init=20, seed=42)` 규칙으로 initial 20 points를 재생성했다.
2. D000은 EXP-001 결과를 재사용했다.
3. D001-D019를 17 PVT corners에서 평가했다.
4. 각 design의 17 corners가 모두 완료된 뒤에만 정식 dataset에 저장했다.
5. 이미 완료된 design_id는 재실행 시 skip하도록 구성했다.
6. D006 parallel timeout 이후 PVT corner 실행을 sequential mode로 변경해 D007-D019까지 완료했다.
7. 결과를 EXP-001과 결합해 20-design baseline을 분석했다.

Main execution script:

`scripts/evaluate_initial_design_pvt.py`

D006 diagnostic script:

`scripts/evaluate_d006_single.py`

## Data

```text
data/
├─ design_points.csv
├─ corner_metrics.csv
└─ analysis/
   ├─ design_summary.csv
   ├─ corner_summary.csv
   ├─ constraint_failure_summary.csv
   ├─ worst_corner_frequency.csv
   └─ near_feasible_tt.csv
```

- `design_points.csv`: EXP-002에서 새로 평가한 D001-D019의 parameter
- `corner_metrics.csv`: 각 design_id의 17-corner metric / feasibility
- EXP-001의 D000은 중복 저장하지 않는다.
- `analysis/`: EXP-001 D000 + EXP-002 D001-D019를 합쳐 계산한 derived summary tables

두 primary CSV는 `design_id`로 연결한다.

분석 재현 스크립트:

`scripts/analyze_initial_design_pvt.py`

이 스크립트는 EXP-001과 EXP-002의 committed `corner_metrics.csv`를 읽어 340 evaluations를 검증하고 `data/analysis/`의 summary tables를 재생성한다.

D006 timeout 진단 결과는 다음에 별도 보존했다.

```text
diagnostics/D006/
├─ design_point.csv
└─ corner_metrics.csv
```

## Failure / Diagnostic Record

### Attempt 1 — Python class import error

오류:

```text
ImportError: cannot import name 'ATLAS' from 'topbo.optimizers'
```

원인:

CLI method 이름은 ATLAS이지만 실제 Python class 이름은 `TopoBO`였다.

수정:

```python
from topbo.optimizers import TopoBO
atlas = TopoBO()
```

이 오류는 simulation 시작 전에 발생했으므로 결과 데이터에는 영향이 없다.

### Attempt 2 — D006 PVT timeout

D001-D005 완료 후 D006의 `FF_3.6V_m40C` corner가 120 s timeout에 걸렸다.

당시 나머지 PVT corners를 최대 8개 병렬 실행하고 있었다.

같은 D006을 corner-wise sequential execution으로 다시 평가한 결과:

- 17 / 17 corners 완료
- 이전 timeout corner도 정상 완료
- D006 결과 정상 저장

현재 근거는 parallel resource contention 또는 wall-time 증가가 timeout에 영향을 줬을 가능성을 지지하지만, 원인을 완전히 확정한 것은 아니다.

따라서 본 pilot에서는 안정적인 dataset 확보를 우선해 sequential execution을 사용했다.

## Results

EXP-001 + EXP-002를 통합한 최종 dataset:

```text
20 designs × 17 corners = 340 corner evaluations
```

### Feasibility

- feasible corner evaluation: **0 / 340**
- 하나 이상의 corner에서 feasible한 design: **0 / 20**
- 17 corners 모두 feasible한 robust design: **0 / 20**

즉 initial 20-point set만으로는 feasible-island의 이동·분열·persistence를 직접 분석할 수 없었다.

### Constraint Failure Frequency

한 evaluation이 여러 spec을 동시에 실패할 수 있으므로 fail count의 합은 340보다 클 수 있다.

| Spec | Fail count | Fail rate |
| --- | ---: | ---: |
| UGBW | 252 | 74.1% |
| Output swing | 238 | 70.0% |
| Gain | 218 | 64.1% |
| Phase margin | 208 | 61.2% |
| Settling time | 169 | 49.7% |
| Bias current | 29 | 8.5% |

Bias current는 대부분 만족했지만, gain / UGBW / output swing / phase margin 사이에서 강한 trade-off가 나타났다.

### Near-Feasible TT Designs

TT에서 D000, D007, D008, D009는 6개 spec 중 **phase margin만 실패**했다.

예:

| Design | TT Phase Margin | PM Target | Other 5 specs |
| --- | ---: | ---: | --- |
| D000 | 29.21 deg | >= 60 deg | Pass |
| D007 | 30.50 deg | >= 60 deg | Pass |
| D008 | 30.44 deg | >= 60 deg | Pass |
| D009 | 37.94 deg | >= 60 deg | Pass |

반대로 D002 / D006처럼 phase margin이 충분히 높은 design은 gain, UGBW, output swing이 크게 부족했다.

### Metric-Wise Worst Corner

20 designs에서 가장 자주 worst가 된 corner:

| Metric | Most frequent worst corner | Frequency |
| --- | --- | ---: |
| Gain | FF / 3.0 V / 125 C | 15 / 20 |
| Ibias | FF / 3.6 V / -40 C | 18 / 20 |
| Phase Margin | FS / 3.6 V / -40 C | 13 / 20 |
| UGBW | SS / 3.0 V / 125 C | 18 / 20 |

worst corner는 metric마다 달랐고, 일부 metric은 design point에 따라서도 worst corner가 달라졌다.

## Observation

1. Initial 20 designs에서는 feasible corner가 하나도 없었다.
2. local neighborhood의 일부 point는 TT에서 6개 spec 중 5개를 만족해 feasible boundary에 상대적으로 가까웠다.
3. phase margin이 높은 design과 gain / UGBW / swing이 높은 design이 서로 다른 경향을 보였다.
4. metric별 worst corner가 하나로 일치하지 않았다.
5. global LHS 쪽의 여러 point는 여러 spec을 동시에 크게 실패했다.

## Interpretation

이번 결과는 두 가지를 동시에 보여준다.

첫째, **worst-case compression이 여러 physical corner의 정보를 하나의 synthetic vector로 합칠 수 있다는 점**은 D000 한 점이 아니라 20 designs에서도 반복됐다.

둘째, 현재 dataset에서는 feasible point가 전혀 없기 때문에 아직 corner-wise feasible island 자체를 관찰할 수 없다.

따라서 다음 단계에서 필요한 것은 sample 개수를 단순히 늘리는 것이 아니라 **feasible 또는 near-feasible region을 먼저 찾는 것**이다.

## Research Implication

Robust feasible design은 반드시 TT에서도 feasible해야 한다.

따라서 TT에서 feasible region을 찾지 못한 상태에서 모든 candidate를 17-corner PVT로 확대하는 것은 simulation cost 대비 정보 효율이 낮을 수 있다.

현재 가장 합리적인 다음 흐름은:

```text
ATLAS initial 20 points
→ adaptive TT search
→ TT feasible / near-feasible candidates
→ selected candidates 17-corner PVT
→ corner-wise feasible-set comparison
```

이다.

## Conclusion

EXP-002의 초기 가설 중 “initial set에서 feasible / infeasible이 함께 나타날 수 있다”는 부분은 현재 dataset에서는 지지되지 않았다.

대신 다음 두 결과를 얻었다.

- metric-wise worst-corner mismatch는 multi-design에서도 실제로 존재한다.
- initial 20-point만으로는 feasible-island 분석에 필요한 feasible sample이 부족하다.

따라서 feasible-island 연구를 계속하려면 먼저 feasible boundary discovery 단계가 필요하다.

## Limitations

- initial 20 points만 평가했으며 adaptive optimization 이후 candidate는 아직 포함하지 않았다.
- feasible sample이 0개이므로 island 위치, 크기, 연결성, persistence를 분석할 수 없다.
- D006 timeout 원인이 parallel resource contention이라고 완전히 확정하지는 않았다.
- 현재 결과는 two-stage GF180 op-amp와 현재 spec / parameter range에 한정된다.

## Data Retention

모든 corner의 raw AC/DC/DC-sweep/transient CSV는 상시 저장하지 않는다.

현재 연구 판단에 직접 필요한 것은:

- config
- execution / diagnostic scripts
- design point table
- corner-wise metric / feasibility table
- 결과 해석

이다.

이상 metric이나 waveform 근거가 필요한 design/corner만 선택적으로 재실행해 raw data를 보존한다.

## Next Experiment

다음 단계는 임의 100-point PVT sweep이 아니다.

먼저 initial 20 points 이후 ATLAS가 실제로 adaptive candidate를 제안하는 흐름을 이해하고, TT에서 feasible / near-feasible candidate를 확보하는 실험을 설계한다.

다음 실험에서 먼저 정해야 할 항목:

1. D020 이후 candidate generation flow
2. near-feasible의 정량 기준
3. TT adaptive search budget / stopping criterion
4. 저장할 design / metric / iteration dataset 구조
5. 어떤 TT candidate를 17-corner PVT로 넘길지 selection rule

이 설계가 완료되기 전에는 다음 Experiment 번호를 확정하지 않는다.
