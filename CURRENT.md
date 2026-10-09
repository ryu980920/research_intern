# CURRENT — Research Status

_Last updated: 2026-10-09_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**Optimizer-default 20-point PVT pilot completed — adaptive TT search design is next**

ATLAS의 기본 실행 흐름과 PVT aggregation 방식을 실제 코드로 추적했고, EXP-001 + EXP-002를 통해 **optimizer-default `n_init=20`으로 생성한 initial 20 design points**를 17개 PVT corner에서 모두 평가했다.

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

현재 EXP-003은 **budget=60**을 선택했으므로 standard `n_init_for()`도 **20**을 반환한다. 이로써 초기 D000–D019 definition을 EXP-002와 맞췄다. 다만 EXP-003 script는 기존 CSV로 warm start하지 않고 **초기 20점을 TT에서 다시 시뮬레이션**한다.

## Current Questions

1. ATLAS의 첫 adaptive evaluation인 D020 이후, 6개 TT spec의 **joint violation**이 실제로 줄어드는가?
2. 최초 TT feasible point를 발견할 수 있는가? 불가능하다면 어느 spec이 bottleneck으로 남는가?
3. **TT feasible point가 발견되더라도** 주변만 탐색하면 다른 disconnected TT feasible island를 놓치지 않는가?
4. TT에서 서로 떨어진 feasible region 후보들이 실제 7차원 공간에서도 연결되어 있는가, 독립적인가?
5. 같은 7D parameter points를 17 PVT corners에서 평가하면 어떤 region이 유지·축소·소멸·분리되는가?
6. corner-wise 정보를 활용하는 방법이 metric-wise worst-case baseline보다 **동일 비용에서** robust design을 더 효율적으로 찾는가?

## Next

### Step 1 — EXP-003: TT Adaptive First-Feasible Discovery (실행 전)

현재 문서/설정/실행 script를 보강했고, 아직 SPICE 실행 결과는 없다.

Research Question:

> 처음 20개 TT 설계안이 모두 Infeasible일 때, ATLAS가 제한된 추가 adaptive evaluation으로 **같은 설계에서 6개 spec을 동시에 만족하는 지점**을 찾을 수 있는가?

설정:

- Circuit: GF180 two-stage op-amp / TT 3.3 V, 27 °C
- parameter dimension: 7
- budget 60 / n_init 20 / 최대 40 adaptive
- seed 42 / GP surrogate / first feasible early stop
- `sw_stat_global = 0`, `sw_stat_mismatch = 0`
- D000–D019 **TT 재실행** 후 D020부터 adaptive (EXP-002 data warm-start가 아님)
- output: `trajectory.csv`, `run_summary.json`, ATLAS native logs

관찰할 값: feasible 여부만이 아니라 iteration별 per-spec margin, worst_margin, total_violation, 7개 parameter trajectory와 ATLAS 내부 진단값.

**Why:** feasibility 여부만 보면 왜 성공 또는 실패했는지 알 수 없다. 예컨대 PM은 개선되는데 UGBW가 떨어지는 trade-off를 확인해야 다음 탐색 전략을 정할 수 있다.

상세 목적/가설/결과 해석/후속 방향은 `experiments/EXP-003_tt_adaptive_feasible_discovery/README.md`를 따른다.

### Step 2 — TT Multi-Island Discovery (후속, 미실행)

EXP-003에서 **first feasible point를 찾더라도 그 점 하나가 Feasible Island 전체는 아니다.**

서로 다른 위치에 **여러 disconnected TT feasible region**이 존재할 가능성을 확인하기 위해:

- first feasible 주변 boundary refinement
- 먼 영역의 global sampling / 다른 seed / 다른 시작점
- 필요하면 early stop이 없는 별도 continuation run
- normalized 7D distance와 이웃 정의
- Mapper가 예측한 component와 실제 measured feasible set 비교
- 2D projection 상 분리와 실제 7D disconnected component를 구분

진짜 disconnected island라고 판단하려면 샘플이 비어 있다는 사실만으로 충분하지 않다. 두 region 사이의 연결 경로를 추가 확인해야 할 수 있다.

### Step 3 — Same-Point 17-Corner PVT Comparison (후속, 미실행)

TT에서 발견한 **복수 region 후보 A/B/...**와 boundary에서 여러 대표 design points를 선택한다.

이 **동일한 7개 파라미터 조합**을 TT 포함 17 PVT corners에서 시뮬레이션하고 `design_points.csv` + `corner_metrics.csv`로 기록한다.

Corner마다 parameter를 달리 최적화하는 것이 아니라 동일 좌표의 feasibility 변화를 비교해야 island의 이동·축소·소멸을 논할 수 있다.

### Step 4 — Persistence / Baseline Comparison (후속, 미실행)

Corner별 island matching 및 persistence 정의를 설계한 뒤:

- worst-case vector baseline
- corner-wise island-information-aware candidate selection

을 동일 spec/PVT/simulation-budget 조건에서 비교한다.

**중요:** metric-wise worst-case aggregation은 corner identity/geometry를 잃지만, 17개 corner 모두를 정확히 평가했다면 **최종 robust feasibility의 참/거짓 자체를 잃는 것은 아니다.** 우리 가설은 추가 구조 정보가 **탐색 효율**을 개선한다는 것이다.

## Working Principle

다음 명령을 실행하는 것 자체가 목적이 아니다.

새 simulation을 시작하기 전에 반드시 **왜 이 데이터를 뽑는지, 어떤 결과가 나오면 가설을 지지하거나 반박하는지, 그 결과가 다음 판단에 어떻게 연결되는지**를 이해하고 진행한다.
