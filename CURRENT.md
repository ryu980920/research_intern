# CURRENT — Research Status

_Last updated: 2026-10-04_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**Baseline PVT representation analysis — first 17-corner run completed**

ATLAS의 기본 실행 흐름을 실제 코드로 추적했고, design parameter → SPICE → metric → surrogate/acquisition → next candidate 연결을 확인했다.

현재 핵심은 **PVT 정보를 worst-case로 압축하는 방식과 corner-wise 정보를 유지하는 방식의 차이가 실제 설계 탐색에서 의미가 있는지 검증하는 것**이다.

아직 개선 방법을 확정하지 않는다.

## Verified Baseline Flow

```text
YAML parameter range
→ initial / proposed design x
→ netlist .param replacement
→ ngspice AC / OP / DC / transient
→ raw CSV
→ gain / ibias / phase margin / settling / UGBW / swing
→ feasibility + surrogate
→ ATLAS topology-aware acquisition
→ next design x
```

상세 내용: `docs/atlas_code_flow.md`

## Important PVT Finding

- two-stage op-amp YAML에는 TT 포함 총 17개의 netlist가 존재한다.
- 현재 확인한 `run_experiment.py`, `run_benchmark.py`는 evaluator의 기본값 `pvt=False`를 사용한다.
- 따라서 기존 smoke test의 일반 실행은 **TT-only**다.
- evaluator 내부에는 PVT mode가 구현되어 있다.
- PVT mode에서는 TT soft gate 후 나머지 corner를 평가하고, optimizer에 전달하기 전에 **metric별 worst-case 값으로 압축**한다.

따라서 “17 corner를 사용한다”와 “기본 ATLAS run이 17 corner를 모두 사용한다”는 서로 다른 말이다.

## Simulation Reproducibility Finding

새 PC에서 ATLAS 실행환경을 재구축하며 동일 TT design point의 반복 결과가 달라지는 문제를 확인했다.

원인은 GF180 `design.ngspice`의 기본 statistical setting이었다.

```spice
sw_stat_global = 1
sw_stat_mismatch = 1
```

이 상태에서는 TT 조건에서도 global process variation과 local mismatch가 랜덤하게 적용되어 반복 실행마다 서로 다른 virtual chip sample이 평가된다.

PVT baseline과 Monte Carlo variation을 분리하기 위해 로컬 GF180 model을 다음과 같이 변경했다.

```spice
sw_stat_global = 0
sw_stat_mismatch = 0
```

수정 후 동일 netlist 3회 raw CSV hash와 `CircuitEvaluator.evaluate_tt()` 3회 metric이 모두 완전히 동일함을 확인했다.

따라서 현재 baseline 원칙은:

```text
PVT study → nominal statistical switches OFF
Monte Carlo / mismatch study → 별도 실험에서 명시적으로 ON
```

상세 기록: `logs/2026-10/2026-10-04.md`

## Current Questions

1. PVT mode를 실제로 실행했을 때 각 design point에서 corner별 metric은 어떻게 달라지는가?
2. 각 metric의 worst corner는 동일한가, 서로 다른가?
3. worst-case compression으로 인해 corner별 feasible-region 구조가 사라지는가?
4. 그 정보 손실이 candidate selection 또는 robust feasible design 탐색에 실제 영향을 주는가?
5. corner-wise 정보를 사용하는 방법이 추가 simulation/모델 복잡도에 비해 충분한 이득을 주는가?

## Completed

- [x] 연구 인턴 GitHub repository 생성 및 기본 구조 구축
- [x] ATLAS smoke test 및 기록
- [x] ATLAS main execution flow 추적
- [x] design parameter → SPICE netlist 연결 확인
- [x] SPICE raw output → metric extraction 연결 확인
- [x] metric → surrogate / ATLAS candidate selection 연결 확인
- [x] 기본 runner의 TT-only 동작 확인
- [x] evaluator의 PVT worst-case aggregation 방식 확인
- [x] 새 PC ATLAS/ngspice/GF180 실행환경 연결 확인
- [x] GF180 기본 statistical variation 활성화로 인한 비결정성 원인 확인
- [x] statistical switches OFF 후 TT 반복 재현성 확인
- [x] EXP-001: YAML init_params 1개 design point의 17-corner PVT evaluation 완료
- [x] 17-corner metric CSV 보존 및 metric별 worst corner 비교

## Data Policy for Current PVT Study

현재 feasible-region / feasible-island 분석의 핵심 데이터는 두 table이다.

```text
design_points.csv
→ design_id별 transistor sizing / compensation capacitor 값

corner_metrics.csv
→ design_id × 17 PVT corner별 metric / feasibility
```

두 파일은 `design_id`로 연결한다.

모든 corner의 AC/DC/DC-sweep/transient raw CSV를 상시 보존하지 않는다. raw waveform은 이상 metric 진단이나 파형 근거가 필요한 특정 design/corner에서만 선택적으로 재생성한다.

## Next

### Step 1 — Multi-design-point PVT baseline dataset

여러 design point를 정의하고 각 point에 대해 17개 corner를 평가한다.

저장 구조:

```text
design_points.csv
design_id | wp1 | wn1 | wp3 | wn3 | wn4 | wn5 | cc

corner_metrics.csv
design_id | corner | gain | ugbw | phm | ibias | t_settle | vswing | feasible
```

목적은 feasible / infeasible point가 섞이는 영역을 확보해 corner별 feasible set을 비교하는 것이다.

### Step 2 — Corner-wise structure observation

각 design point에서:

- corner별 feasibility
- metric별 worst corner
- worst-case compressed vector

를 비교하고, design space 전체에서는 corner별 feasible set의 이동·겹침·분리를 관찰한다.

### Step 3 — Feasible-island analysis 조건 판단

충분한 feasible point가 확보된 이후에만 island topology를 분석한다. EXP-001의 한 design point만으로 island 존재나 persistence를 결론 내리지 않는다.

## Working Principle

다음 명령을 실행하는 것 자체가 목적이 아니다.

PVT simulation을 시작하기 전에 반드시 **왜 이 데이터를 뽑는지, 어떤 결과가 나오면 가설을 지지하거나 반박하는지**를 이해하고 진행한다.
