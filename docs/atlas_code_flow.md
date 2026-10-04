# ATLAS Code Flow Analysis

_Last checked against `youngmin0oh/atlas` main branch: 2026-10-04_

## Purpose

ATLAS를 수정하기 전에 먼저 **설계 파라미터가 어디에서 정의되고, SPICE에 어떻게 전달되며, 성능 metric이 어떻게 optimizer로 되돌아오는지** 실제 코드 기준으로 추적한다.

이 문서는 추측이 아니라 현재 repository의 코드를 직접 확인한 결과를 기록한다.

## 1. Entry Point

기본 실행 시작점은 `run_experiment.py`이다.

흐름:

```text
run_experiment.py
  ↓
CircuitEvaluator
  ↓
get_optimizer("ATLAS") → TopoBO
  ↓
optimizer.optimize(...)
```

`run_experiment.py`는 회로 YAML을 선택하고 evaluator와 optimizer를 연결하는 역할을 한다.

## 2. Design Variables and Specifications

`two_stage_opamp_gf180.yaml` 기준 design variable은 다음 7개다.

- wp1
- wn1
- wp3
- wn3
- wn4
- wn5
- cc

각 변수의 탐색 범위와 초기 reference parameter도 YAML에서 정의된다.

Target specification:

| Spec | Constraint |
| --- | ---: |
| gain_min | ≥ 300 |
| vswing_min | ≥ 0.3 |
| ugbw_min | ≥ 2.0e7 |
| phm_min | ≥ 60 |
| ibias_max | ≤ 0.001 |
| t_settle_max | ≤ 6.0e-6 |

즉 ATLAS는 단일 성능만 최대화하는 것이 아니라 여러 성능 조건을 동시에 만족하는 sizing point를 찾는다.

## 3. Parameter → SPICE

`topbo/circuit_eval.py`의 `CircuitEvaluator.evaluate()`는 optimizer가 제안한 parameter vector `x`를 parameter 이름과 결합해 `state` dictionary로 만든다.

```text
x
→ clip / rounding
→ {wp1: ..., wn1: ..., ..., cc: ...}
→ NgSpiceWrapper.run(state)
```

`eval_engines/ngspice/ngspice_wrapper_parallel.py`에서는 이 값으로 netlist의 `.param` 값을 직접 치환한다.

따라서 optimizer가 제안한 candidate가 실제 transistor width / compensation capacitor 값으로 바뀌어 ngspice에 입력된다.

## 4. SPICE → Raw Output

TT netlist에서는 한 candidate에 대해 다음 분석이 수행된다.

- AC analysis → `ac.csv`
- Operating point → `dc.csv`
- DC sweep → `dc_sweep.csv`
- Transient analysis → `tran.csv`

ngspice는 batch mode로 실행된다.

## 5. Raw Output → Metrics

`CircuitClass.translate_result()`가 raw CSV를 읽어 성능값으로 변환한다.

대표적인 연결은 다음과 같다.

```text
ac.csv
→ UGBW
→ Phase Margin

dc.csv
→ Bias Current

dc_sweep.csv
→ Gain
→ Output Swing

tran.csv
→ Settling Time
```

최종적으로 다음과 같은 spec dictionary가 evaluator로 반환된다.

```text
gain
ibias
phm
t_settle
ugbw
vswing
```

이 값들은 YAML의 `gain_min`, `ibias_max` 등 target key로 다시 매핑된다.

## 6. Metrics → Next Candidate

`topbo/optimizers.py`의 공통 BO loop는 다음 순서로 동작한다.

1. 초기 design points 생성
2. 각 design을 SPICE로 평가
3. observed parameter와 metric을 surrogate model에 학습
4. candidate pool 생성
5. ATLAS acquisition으로 다음 candidate 선택
6. 선택한 candidate를 다시 SPICE 평가
7. 결과를 dataset에 추가
8. budget까지 반복

초기 design은 reference parameter 주변 sampling과 LHS를 함께 사용한다.

ATLAS(`TopoBO`)는 surrogate가 예측한 near-feasible candidate에 Mapper graph를 만들고, feasible-region topology와 weighted Expected Improvement를 함께 이용해 다음 candidate를 결정한다.

현재 코드의 candidate pool 상수는 `N_CANDIDATES = 50000`이다.

## 7. PVT Handling — Important Finding

`two_stage_opamp_gf180.yaml`에는 총 17개의 netlist가 존재한다.

- 첫 번째: TT 3.3 V, 27 °C
- 나머지 16개: FF/SS/FS/SF × voltage/temperature 조합

그러나 **현재 확인한 표준 실행기 `run_experiment.py`와 `run_benchmark.py`는 `CircuitEvaluator(..., pvt=True)`를 전달하지 않는다.**

`CircuitEvaluator`의 기본값은:

```python
pvt=False
```

따라서 우리가 기존 smoke test에서 사용한 일반 실행 흐름은 **TT-only evaluation**이다.

### PVT mode를 명시적으로 켜면

`CircuitEvaluator` 내부에는 multi-corner 기능이 구현되어 있다.

흐름:

```text
candidate
→ TT 먼저 평가
→ TT가 soft gate를 통과하면 나머지 PVT corners 평가
→ corner별 feasibility count
→ metric별 worst-case 값으로 압축
→ optimizer에 worst-case spec dictionary 반환
```

metric별 worst-case는 다음 방식이다.

- minimum requirement (`gain_min`, `ugbw_min` 등) → corner 중 최소값
- maximum requirement (`ibias_max`, `t_settle_max` 등) → corner 중 최대값

중요하게도 optimizer가 받는 일반 spec 값은 **corner-wise 전체 landscape가 아니라 metric별 worst-case로 압축된 값**이다.

현재 반환 metadata에는 PVT 전체 pass 여부와 통과 corner 수가 포함되지만, optimizer가 학습하는 기본 spec vector에는 개별 corner별 성능값이 유지되지 않는다.

## 8. Current Interpretation

현재 코드 기준으로 두 상황을 구분해야 한다.

### 현재 기본 ATLAS 실행

```text
Design x
→ TT simulation
→ TT metrics
→ surrogate / topology
→ next x
```

### PVT mode를 켠 경우

```text
Design x
→ TT
→ 필요 시 16 PVT simulations
→ metric-wise worst-case compression
→ surrogate / topology
→ next x
```

EXP-001과 EXP-002에서 실제 corner-wise PVT baseline을 수행한 결과, metric별 worst corner가 하나로 일치하지 않는 현상이 multi-design에서도 반복됐다.

즉 worst-case compression이 여러 physical corner의 정보를 하나의 synthetic vector로 합칠 수 있다는 점은 실제 데이터에서 확인됐다.

다만 initial 20 designs에서는 feasible evaluation이 0 / 340이었기 때문에, 아직 corner-wise feasible island 자체의 이동·분리·지속성을 관찰할 수는 없다.

## 9. Resolved Question and Remaining Question

### 확인된 부분

다음 질문의 첫 부분은 실제 데이터로 확인됐다.

> worst-case compression 과정에서 corner identity 정보가 사라지는가?

**Yes.** metric별 worst corner가 서로 달라 하나의 physical corner가 아닌 조합 vector가 만들어질 수 있다.

### 아직 확인되지 않은 부분

다음 질문은 아직 남아 있다.

> 그 정보 손실이 실제 robust candidate selection 또는 feasible-region 탐색 성능에 의미 있는 영향을 주는가?

이를 검증하려면 먼저 feasible 또는 near-feasible region을 확보해야 한다.

## 10. Next Code-Level Question

다음으로 확인할 코드는 initial 20 points 이후의 adaptive search 구간이다.

```text
D000-D019
→ predefined initial design set

D020 and later
→ surrogate + acquisition을 이용한 adaptive candidate
```

확인할 항목:

1. initial observations가 surrogate에 어떻게 전달되는가
2. feasibility 정보가 acquisition에 어떻게 반영되는가
3. `TopoBO`가 D020 이후 candidate를 어느 함수에서 선택하는가
4. candidate pool과 topology-aware score가 어떻게 연결되는가
5. TT feasible / near-feasible candidate를 연구용 dataset으로 어떻게 보존할 것인가

이 확인 이후 TT adaptive search 실험을 설계한다.
