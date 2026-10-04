# CURRENT — Research Status

_Last updated: 2026-10-04_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**Baseline PVT representation analysis**

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

## Next

### Step 1 — PVT baseline 실행 준비

처음부터 optimization 전체를 PVT로 돌리지 않는다.

먼저 **소수 design point**에 대해 PVT evaluation을 수행해 코드와 결과 형식을 검증한다.

사전 조건:

- GF180 statistical variation은 OFF (`sw_stat_global=0`, `sw_stat_mismatch=0`)
- PVT 변화와 Monte Carlo/mismatch variation을 혼합하지 않는다.

확인해야 할 것:

- 17개 corner가 실제로 정상 실행되는가?
- corner별 raw metric을 어떻게 보존할 것인가?
- 한 design point당 simulation 시간이 어느 정도 증가하는가?

### Step 2 — Corner-wise dataset 생성

최소한 다음 형태의 table을 만든다.

```text
design_id | corner | gain | ugbw | phm | ibias | t_settle | vswing | feasible
```

이 데이터가 있어야 worst-case compression 전후를 실제로 비교할 수 있다.

### Step 3 — Baseline observation

각 design point에서:

- metric별 worst corner
- corner별 feasibility
- worst-case compressed vector

를 비교한다.

### Step 4 — EXP-001 결정

PVT baseline 관찰 결과에서 실제 정보 손실 또는 구조적 차이가 확인될 때 첫 정식 Research Question과 `EXP-001`을 정의한다.

## Working Principle

다음 명령을 실행하는 것 자체가 목적이 아니다.

PVT simulation을 시작하기 전에 반드시 **왜 이 데이터를 뽑는지, 어떤 결과가 나오면 가설을 지지하거나 반박하는지**를 이해하고 진행한다.
