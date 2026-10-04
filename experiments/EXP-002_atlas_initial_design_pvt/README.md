# EXP-002 — PVT Evaluation of the ATLAS Initial Design Set

_Date started: 2026-10-04_

## Purpose

ATLAS가 optimization을 시작할 때 실제로 사용하는 initial design set을 17개 PVT corner에서 평가해, 단일 `init_params` 점을 넘어 corner-wise feasible-region 구조가 나타나기 시작하는지 확인한다.

EXP-001의 `D000`은 이미 동일한 deterministic PVT 조건에서 평가했으므로 다시 시뮬레이션하지 않는다. EXP-002에서는 나머지 `D001`–`D019`를 추가한다.

최종적으로 EXP-001 + EXP-002를 합치면 **20 design points × 17 corners = 340 corner evaluations**가 된다.

## Research Question

1. ATLAS의 실제 initial design set에서 feasible / infeasible design이 함께 나타나는가?
2. 같은 design이라도 corner별 feasibility가 달라지는가?
3. metric별 worst corner는 design point에 따라 바뀌는가?
4. 이 20-point pilot이 feasible-island 분석을 확대할 근거를 제공하는가?

## Why 20 Points First

현재 ATLAS의 GP-based optimizer 기본값은 `n_init=20`이다.

YAML에 `init_params`가 있을 때 initial design은 다음 방식으로 만들어진다.

- 1 point: YAML `init_params` → 이미 EXP-001의 `D000`
- 12 points: `init_params` 주변 local perturbation
- 7 points: global Latin Hypercube Sampling (LHS)

따라서 처음부터 임의의 100 points를 생성하기보다, **ATLAS가 실제 optimization 시작 시 보는 20 points를 먼저 PVT로 평가**하는 것이 baseline 비교에 더 직접적이다.

## Data

```text
data/
├─ design_points.csv
└─ corner_metrics.csv
```

- `design_points.csv`: EXP-002에서 새로 평가한 D001–D019의 parameter
- `corner_metrics.csv`: 각 design_id의 17-corner metric / feasibility
- EXP-001의 D000은 중복 저장하지 않는다.

두 CSV는 실행 도중 design point가 완료될 때마다 누적된다. 이미 17 corner가 모두 저장된 design_id는 재실행 시 건너뛴다.

## Data Retention

모든 corner의 raw AC/DC/DC-sweep/transient CSV는 상시 저장하지 않는다. 이상 metric 진단이나 waveform 근거가 필요한 design/corner만 선택적으로 재실행한다.

## Decision After This Experiment

20-point 결과를 본 뒤 다음을 결정한다.

- feasible point가 충분히 존재 → 50/100 points로 확대할지 판단
- feasible point가 거의 또는 전혀 없음 → 무작정 100 points를 추가하지 않고 sampling 범위/방식을 재검토
- corner별 구조 차이가 뚜렷함 → feasible-region / island 분석 방법을 구체화
