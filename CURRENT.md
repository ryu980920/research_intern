# CURRENT — Research Status

_Last updated: 2026-10-04_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**Optimizer-default 20-point PVT pilot completed — adaptive TT search design is next**

ATLAS의 기본 실행 흐름과 PVT aggregation 방식을 실제 코드로 추적했고, EXP-001 + EXP-002를 통해 ATLAS가 optimization 시작 시 사용하는 initial 20 design points를 17개 PVT corner에서 모두 평가했다.

현재 핵심 연구 질문은 그대로 유지한다.

> **PVT 정보를 metric-wise worst-case로 압축하는 방식이 corner-wise feasible-region 구조를 얼마나 잃고, 그 정보 손실이 robust candidate selection에 실제 영향을 주는가?**

다만 현재 20-point initial set에서는 feasible point가 전혀 나오지 않았기 때문에, 아직 feasible-island topology를 직접 분석할 단계는 아니다.

개선 방법은 아직 확정하지 않는다.

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

## Important PVT Findings

- two-stage GF180 op-amp YAML에는 TT 포함 총 17개의 PVT netlist가 존재한다.
- 현재 확인한 standard runner는 evaluator의 기본값 `pvt=False`를 사용하므로 일반 실행은 **TT-only**다.
- evaluator 내부 PVT mode는 TT 이후 나머지 corner를 평가하고 optimizer에 전달하기 전에 **metric별 worst-case 값으로 압축**한다.
- EXP-001의 D000 한 점에서 이미 metric별 worst corner가 서로 달랐다.
- EXP-002까지 20 design으로 확대해도 metric별 worst corner가 하나의 physical corner로 일치하지 않았다.

따라서 “17 corner를 평가한다”와 “17 corner의 구조를 optimizer가 그대로 본다”는 서로 다른 말이다.

## EXP-001 + EXP-002 Result Snapshot

통합 dataset:

```text
20 design points × 17 corners = 340 corner evaluations
```

Feasibility:

- feasible corner evaluation: **0 / 340**
- 하나 이상의 corner에서 feasible한 design: **0 / 20**
- 17 corners 모두 feasible한 robust design: **0 / 20**

Constraint failure frequency:

| Spec | Fail count | Fail rate |
| --- | ---: | ---: |
| UGBW | 252 | 74.1% |
| Output swing | 238 | 70.0% |
| Gain | 218 | 64.1% |
| Phase margin | 208 | 61.2% |
| Settling time | 169 | 49.7% |
| Bias current | 29 | 8.5% |

TT에서 D000, D007, D008, D009는 6개 spec 중 **phase margin만 실패**했다. 반대로 D002 / D006처럼 phase margin이 충분한 design은 gain, UGBW, output swing이 크게 부족했다.

현재 관찰은 stability와 gain / bandwidth / swing 사이에 강한 trade-off가 있음을 보여준다.

## Worst-Corner Observation

20 designs에서 가장 자주 worst가 된 corner:

- Gain: FF / 3.0 V / 125 C — 15 / 20
- Ibias: FF / 3.6 V / -40 C — 18 / 20
- Phase Margin: FS / 3.6 V / -40 C — 13 / 20
- UGBW: SS / 3.0 V / 125 C — 18 / 20

따라서 worst-case compressed vector는 하나의 실제 physical corner 상태가 아니라 여러 corner의 worst metric을 조합한 synthetic vector가 될 수 있다.

## Simulation Reproducibility Finding

GF180 `design.ngspice`의 기본 statistical setting은 다음과 같이 활성화되어 있었다.

```spice
sw_stat_global = 1
sw_stat_mismatch = 1
```

PVT 변화와 random process / mismatch variation을 분리하기 위해 현재 PVT baseline에서는 다음처럼 고정한다.

```spice
sw_stat_global = 0
sw_stat_mismatch = 0
```

수정 후 동일 netlist 반복 실행에서 raw CSV hash와 metric이 동일하게 재현됨을 확인했다.

현재 원칙:

```text
PVT study → nominal statistical switches OFF
Monte Carlo / mismatch study → 별도 실험에서 명시적으로 ON
```

## Execution Reliability Finding

EXP-002에서 D006의 FF / 3.6 V / -40 C corner가 8-way parallel PVT 실행 중 120 s timeout에 걸렸다.

같은 D006을 corner-wise sequential execution으로 재실행했을 때 17 / 17 corners가 모두 완료됐다.

현재 해석은:

- 해당 design/corner가 본질적으로 simulation 불가능하다는 근거는 없음
- 병렬 실행 시 resource contention 또는 wall-time 증가가 timeout에 영향을 줬을 가능성이 커짐
- 원인을 완전히 확정한 것은 아님

따라서 현재 20-point pilot에서는 안정적인 dataset 확보를 우선해 corner-wise sequential execution을 사용했다.

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
- [x] EXP-001: D000 17-corner PVT baseline 완료
- [x] EXP-002: D001-D019 17-corner PVT evaluation 완료
- [x] EXP-001 + EXP-002 통합 20 designs × 17 corners = 340 evaluations 확보
- [x] initial 20 designs에서 feasible point 0개 확인
- [x] metric별 worst corner 불일치가 multi-design에서도 반복됨을 확인
- [x] D006 parallel timeout을 sequential rerun으로 진단하고 실행 정책 수정

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

## Baseline Definition Correction — 2026-10-09

EXP-002는 `TopoBO.optimize(...)`의 기본 인자 `n_init=20`을 명시적으로 사용한 pilot이다.

하지만 standard `run_experiment.py`는:

```python
n_init_for(evaluator, budget)
= max(min(3 * n_params, budget // 3, 50), 10)
```

으로 initial sample 수를 계산한다.

two-stage GF180 op-amp는 7 parameters이므로 budget >= 63인 standard run에서는 `n_init=21`이다.

따라서 이후 adaptive trajectory 실험에서는 **EXP-002의 20-point pilot을 그대로 이어갈지, standard runner의 21-point baseline에 맞출지 먼저 결정**해야 한다.

## Current Questions

1. initial 20-point에서 feasible이 0개인 이유는 단순 sample 부족인가, spec trade-off 구조 때문인가?
2. ATLAS adaptive search는 initial 20 points 이후 어떤 surrogate / acquisition 정보로 다음 candidate를 제안하는가?
3. TT feasible 또는 near-feasible region을 어떻게 정량적으로 정의할 것인가?
4. TT에서 확보한 후보를 17-corner PVT로 넘겼을 때 corner별 feasibility가 어떻게 달라지는가?
5. 충분한 feasible point가 확보되면 worst-case compression과 corner-wise feasible structure의 차이가 candidate selection에 실제 영향을 주는가?

## Next

### Step 1 — ATLAS post-initial adaptive candidate selection 이해

D000-D019는 optimization 전에 미리 정해지는 initial design set이다.

다음 단계에서는 initial 20 points 이후 ATLAS가 실제로 adaptive하게 다음 candidate를 만드는 흐름을 코드로 확인한다.

특히 확인할 항목:

- initial observations가 surrogate에 어떻게 들어가는가
- acquisition이 어떤 값을 기준으로 candidate를 선택하는가
- D020 이후 candidate가 어떤 함수에서 생성되는가
- feasibility information이 candidate selection에 어떻게 반영되는가

### Step 2 — TT feasible / near-feasible search 설계

임의의 100-point PVT sweep을 바로 시작하지 않는다.

Robust feasible design은 반드시 TT에서도 feasible해야 하므로 먼저 TT에서 feasible 또는 feasible boundary에 가까운 candidate를 찾는다.

```text
initial 20 points
→ ATLAS adaptive TT search
→ TT feasible / near-feasible candidates
→ selected candidates만 17-corner PVT
```

이 단계에서 near-feasible의 정량 기준과 저장할 dataset 구조를 먼저 정의한 뒤 실행한다.

### Step 3 — Selected Candidate PVT Evaluation

TT에서 찾은 모든 candidate를 무조건 PVT 평가하지 않는다.

TT feasible 또는 boundary 근처 point를 선정해 17 corners에서 다음을 비교한다.

- corner-wise feasibility
- spec margin
- metric별 worst corner
- robust feasibility

### Step 4 — Feasible-Island Analysis 확대 판단

corner별 feasible point가 충분히 확보된 이후에만 50/100-point dataset 확대와 feasible-island topology / persistence 분석을 시작한다.

여전히 feasible point가 거의 없다면 sample 수를 늘리기 전에 parameter range, spec trade-off, ATLAS candidate trajectory를 먼저 분석한다.

## Working Principle

다음 명령을 실행하는 것 자체가 목적이 아니다.

새 simulation을 시작하기 전에 반드시 **왜 이 데이터를 뽑는지, 어떤 결과가 나오면 가설을 지지하거나 반박하는지, 그 결과가 다음 판단에 어떻게 연결되는지**를 이해하고 진행한다.
