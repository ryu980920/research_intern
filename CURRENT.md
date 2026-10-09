# CURRENT — Research Status

_Last updated: 2026-10-10_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**EXP-001·002 PVT baseline + EXP-003 GP-based TT adaptive pilot completed.**

지금까지 실제로 확보한 표본:

- **EXP-001:** D000 × 17 PVT = 17 evaluations, feasible 0.
- **EXP-002:** D001~D019 × 17 PVT = 323 evaluations, feasible 0. 이전 D000과 통합하면 **20 designs × 17 corners = 340 evaluations, feasible 0**.
- **EXP-003:** TT-only에서 D000~D019 재평가 + GP adaptive D020~D059 = **60 TT evaluations, feasible 0**. 최선의 near-feasible design은 D050 (PM=54.16°, UGBW=20.33 MHz, PASS 5/6, worst_margin=-0.0973).
- 첨부된 ATLAS `iterations.jsonl` 60행을 검증했다. GP fit_time이 adaptive 40회 모두 기록됐으나 **각 GP MLL fit의 성공과 예측 정확도는 아직 미검증**이다.

**다음 연구 단계:** PM–UGBW trade-off와 이상 metric 추출을 확인하고, TT feasible 후보를 찾는 추가 탐색 전략을 설계한다. TT feasible 표본이 0개이므로 아직 feasible island topology를 직접 검증할 수 없다.

장기 질문은 계속 같다.

> **PVT의 metric-wise worst 압축이 corner identity / feasible-region geometry를 얼마나 잃으며, corner-wise 정보를 보존하면 동일 비용의 robust candidate selection을 개선할 수 있는가?**

지금까지의 실험만으로 새 방법의 개선 효과가 입증된 것은 아니다.

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

## EXP-003 TT Adaptive Pilot Result Snapshot

실행 ID: `two_stage_opamp_gf180_ATLAS_B60_S42_20261009_235604`. 설정은 TT 3.3 V / 27 °C, GP 고정, seed 42, budget 60, n_init 20, 최초 feasible early-stop (해당 없음).

- **D020~D059:** 40개 Adaptive 설계안을 각각 SPICE로 평가했고 매 관측을 다음 GP fit 데이터로 추가하도록 ATLAS 코드에 구현돼 있다.
- **Feasible:** 0/60. 최선의 worst_margin·total_violation 설계는 D050 (-0.09727498, 0.09727498). D050의 PM만 목표 60°를 미달.
- **계산 시간(ATLAS JSONL):** fit 누적 313.299 s, acquisition 누적 282.603 s, TDA 1.264 s, 실제 TT 시뮬레이션 60회 누적 4.630 s.
- **주의:** `beta0`는 GP 예측 후보의 connected-component 근사값이며 실제 측정된 feasible island 개수가 아니다. JSONL만으로 MLL fit의 모든 성공을 확인할 수 없다.
- 자세한 수치와 자료: [EXP-003 README](experiments/EXP-003_tt_adaptive_feasible_discovery/README.md).

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
- [x] EXP-003: TT initial 20 + adaptive 40 = 60개 평가 완료 (feasible 0)
- [x] D050 best near-feasible 후보 확보 및 GP JSONL 60행 검사
- [x] EXP-001/002/003 공통 README 목차와 parameter/metric CSV schema 정리

## Data Policy for Current PVT Study

모든 Experiment README는 **Experiment at a Glance → Background → RQ/Hypothesis → Setup → Procedure → Metrics → Results → Discussion → Limitations → Conclusion/Next**의 공통 순서를 따른다. 템플릿: [EXPERIMENT_TEMPLATE.md](experiments/EXPERIMENT_TEMPLATE.md).

각 `EXP-XXX/data/` 루트의 표준 데이터는 두 개다.

```text
design_points.csv → design_id + 7개 실제 설계 파라미터
corner_metrics.csv → design_id × corner + 6개 metric + feasible
```

TT-only 실험에도 `corner=TT_3.3V_27C`를 표기한다. 실험에서 생성된 `trajectory.csv` 같은 복합 원본과 ATLAS `iterations.jsonl`은 `raw/`에 보존한다. 반복·파생 통계는 `data/analysis/`, 생성한 그림은 `figures/`에 저장한다.

전체 corner의 AC/DC/DC-sweep/transient raw waveform은 무조건 보존하지 않는다. 이상 metric 진단·물리적 근거 확보에 필요한 경우 해당 design/corner만 설정과 함께 재현한다. 기존 값의 무단 덮어쓰기는 금지한다.

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

1. D050은 왜 PM 54.16°에서 목표 60°를 넘지 못하는가? **PM–UGBW trade-off**는 compensation capacitor `cc` 및 width 변화로 해결될 수 있는가?
2. 일부 D014 등의 PM=-180°/UGBW=1 Hz/특이 settling 결과는 실제 동작인지 metric extractor의 fallback인가?
3. 현재 GP fit은 반복마다 실행됐다. 그러나 **GP MLL fit 성공/예측 정확도**를 어떻게 독립적으로 검증할 것인가?
4. 다른 seed, 넓은 전역 탐색과 경계 국소 탐색으로 실제 TT feasible point를 확보할 수 있는가?
5. TT feasible 표본을 얻은 뒤에도 서로 분리된 다른 island가 존재하는가? 7D에서 연결성을 어떻게 검증할 것인가?
6. 동일한 7D parameter points의 17-corner 평가로 persistence를 정의하고 **동일 SPICE cost/total runtime**에서 robust search 효율을 비교할 수 있는가?

## Next

### Step 1 — Follow-up: PM–UGBW 진단 및 TT Feasible 탐색 (미실행)

**이유:** EXP-003에서 최초 TT feasible을 찾지 못했지만 D050(5/6, PM만 미달)을 발견했다. 다음 budget만 늘리기 전에 병목의 원인을 확인해야 한다.

1. D050, D030, D044 등의 PM–UGBW trade-off를 원래 시뮬레이터 측정값과 필요 파형으로 확인한다.
2. PM=-180°, UGBW=1 Hz 같은 sentinel 가능성은 extractor/netlist에서 검증한다.
3. `cc` 및 width 민감도와 다른 seed/전역·국소 탐색 전략을 비교할 후속 Experiment 질문을 결정한다.
4. 측정과 GP 예측을 비교하려면 GP의 per-iteration 예측값/불확실성을 별도로 수집한다. 현재 `iterations.jsonl`에는 fit 시간만 있으며 MLL 성공 여부/예측 오차는 없다.

**성공 기준 후보:** 실제 TT에서 6개 spec을 동시에 통과하는 design 또는 기존 D050보다 작은 violation을 갖는 재현 가능한 design.

상세 이전 실험: [EXP-003](experiments/EXP-003_tt_adaptive_feasible_discovery/README.md).

### Step 2 — TT Multi-Island Discovery (후속, 미실행)

후속 TT 탐색에서 **first feasible point를 찾더라도 그 점 하나가 Feasible Island 전체는 아니다.**

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
