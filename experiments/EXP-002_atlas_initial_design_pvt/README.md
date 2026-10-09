# EXP-002 — ATLAS 초기 20개 설계안의 PVT 평가

**Status:** Completed · **Date:** 2026-10-04 시작 · **Circuit:** GF180 two-stage op-amp · **Evaluation:** D001–D019 × 17 PVT corners (EXP-001과 통합해 20 × 17)

## Experiment at a Glance

| 항목 | 이번 실험의 답 |
| --- | --- |
| **왜 했는가?** | EXP-001의 단일점 worst-corner 현상이 다른 설계안에서도 나타나는지, feasible sample을 찾을 수 있는지 확인하기 위해 |
| **무엇을 했는가?** | ATLAS initial-set `n_init=20, seed=42`에서 D000은 재사용하고 D001~D019를 17개 PVT corner에서 평가 |
| **무엇을 알았는가?** | EXP-001·002 통합 **340개 중 feasible 0개**; worst corner 불일치는 반복됨 |
| **그래서 다음은?** | 추가 전역 PVT sweep보다 **TT feasible 또는 경계 부근부터 탐색** → [EXP-003](../EXP-003_tt_adaptive_feasible_discovery/README.md) |

## 01. Background & Motivation

EXP-001은 D000 한 점의 corner-wise 성능 차이를 보여줬지만, feasible region의 위치나 형태는 보여주지 못했다. **여러 설계점을 동일 PVT set에서 평가**해야 worst-corner 변화를 설계 변수 관점에서 비교할 수 있다. 그래서 임의의 큰 sweep 대신 ATLAS가 실제 사용하는 initial design 생성 규칙으로 20점을 정의했다.

## 02. Research Question & Hypothesis

- **RQ1:** 초기 20개 중 하나라도 corner-feasible인 설계안이 있는가?
- **RQ2:** 같은 설계안의 feasibility는 corner에 따라 달라지는가?
- **RQ3:** worst corner의 identity는 성능마다, 설계점마다 바뀌는가?
- **Working hypothesis:** initial set에 feasible 또는 near-feasible 설계안이 포함될 수 있으며, metric별 worst corner가 다를 수 있다.

**판정:** 이 표본에서는 feasible point가 없어서 첫 가설의 feasible 부분은 지지되지 않았다. Worst-corner 불일치는 다수의 설계안에서 반복됐다.

## 03. Experimental Setup

| 항목 | 설정 |
| --- | --- |
| Circuit | GF180 two-stage op-amp |
| Parameter dimension | Width 6개 + 보상 capacitor 1개 = 7D |
| Initial set | `TopoBO._initial_design(n_init=20, seed=42)` |
| Initial composition | D000 YAML init; D001~D012 local perturbation; D013~D019 global LHS |
| PVT | TT 포함 17개 corner (EXP-001과 동일) |
| Simulator | ngspice 44.2; GF180 PDK `9f992d5a9186d1f7820c58f039c484ad35b2edea` |
| Statistical switches | `sw_stat_global=0`, `sw_stat_mismatch=0` |
| ATLAS revision | `dd23c5ba7beb598909be593e4a84c81dab92cc69` |

**Baseline 주의:** 여기서 `n_init=20`은 `TopoBO.optimize()`의 기본값을 명시한 pilot이다. 표준 `run_experiment.py`는 `n_init_for(evaluator,budget)`을 사용하며, 7D에 budget ≥ 63이면 `n_init=21`이 될 수 있다. EXP-002를 모든 budget의 표준 초기 샘플 집합으로 일반화하지 않는다.

상세 설정: [config/run_config.md](config/run_config.md).

## 04. Method & Procedure

1. 동일 ATLAS commit에서 20개 초기 파라미터를 재현하고 D000이 EXP-001 `init_params`와 일치하는지 검사했다.
2. EXP-001의 D000은 재평가하지 않고 재사용했다. 이번 실험에서 새로 평가한 것은 D001~D019, **19×17=323회**다.
3. D006 병렬 timeout을 진단한 뒤 순차 실행으로 전환해 각 설계점의 17개 corner가 전부 완료된 후 데이터를 저장했다.
4. [analyze_initial_design_pvt.py](scripts/analyze_initial_design_pvt.py)로 EXP-001·002를 통합해 20×17=340개 평가, 실패 spec 빈도, worst-corner 분포를 분석했다.

실행: [evaluate_initial_design_pvt.py](scripts/evaluate_initial_design_pvt.py); D006 진단: [evaluate_d006_single.py](scripts/evaluate_d006_single.py).

## 05. Metrics & Evaluation Criteria

공통 target spec 6개: **Gain ≥ 300**, **UGBW ≥ 20 MHz**, **PM ≥ 60°**, **Ibias ≤ 1 mA**, **Settling ≤ 6 µs**, **Swing ≥ 0.3 V**.

- **Corner-feasible:** `design_id × corner`에서 6개 spec 모두 통과.
- **Robust-feasible:** 한 설계안이 17개 corner에서 모두 corner-feasible.
- **Worst corner:** 하나의 metric을 가장 불리하게 만드는 corner. 한 평가가 여러 spec을 실패할 수 있으므로 실패 횟수의 합은 총 평가 수보다 클 수 있다.

## 06. Results & Figures

| 결과 범위 | 설계점 | PVT 결과 | Feasible |
| --- | ---: | ---: | ---: |
| EXP-001 D000 | 1 | 17 | 0 |
| EXP-002 D001~D019 (이번 신규 평가) | 19 | 323 | 0 |
| **합계** | **20** | **340** | **0 / 340** |

**최소 한 corner라도 feasible인 설계안 0/20**, robust-feasible 설계안 **0/20**.

| Spec | 실패 횟수 / 340 | 실패율 |
| --- | ---: | ---: |
| UGBW | 252 | 74.1% |
| Output Swing | 238 | 70.0% |
| Gain | 218 | 64.1% |
| Phase Margin | 208 | 61.2% |
| Settling Time | 169 | 49.7% |
| Bias Current | 29 | 8.5% |

TT에서 **D000, D007, D008, D009**는 6개 중 PM만 실패했다. PM은 각각 약 29.21°, 30.50°, 30.44°, 37.94°로 목표 60°를 넘지 못했다. 반대로 일부 PM이 높은 설계점은 Gain·UGBW·Swing에서 크게 부족했다.

주요 worst-corner 빈도(통합 20 design):
- Gain: FF/3.0 V/125 °C — 15/20
- Ibias: FF/3.6 V/-40 °C — 18/20
- PM: FS/3.6 V/-40 °C — 13/20
- UGBW: SS/3.0 V/125 °C — 18/20

**Data:** `data/design_points.csv` **19행**, `data/corner_metrics.csv` **323행**. D000은 EXP-001의 두 CSV에만 저장한다. 통합 summary tables는 [data/analysis/](data/analysis/)에 있으며 분석 스크립트에서 재생성할 수 있다.

## 07. Discussion

- **Observation:** 모든 관측 corner가 infeasible이었고, near-feasible TT 후보의 주요 병목은 PM이었다. Metric별 최악 corner는 다수 설계에서 일치하지 않았다.
- **Interpretation:** corner-wise 데이터를 metric별 worst-case로 압축하면 해당 metric을 악화시킨 physical corner identity를 놓칠 수 있다. 그러나 feasible 점이 없어 island topology를 비교할 실제 데이터는 없다.
- **Research implication:** 모든 후보를 17-corner로 계속 평가하기보다 **먼저 TT에서 실제 feasible 또는 위반량이 작은 설계안**을 찾는 것이 계산비용 측면에서 유리한 후속 질문이다. 단, TT feasible 자체가 17-corner robust feasibility를 보장하지는 않는다.

## 08. Limitations & Issues

**실패/진단 기록도 재현성의 일부로 유지한다.**

- **Attempt 1 — ImportError:** `from topbo.optimizers import ATLAS`는 실패. 실제 Python class는 `TopoBO`이므로 `from topbo.optimizers import TopoBO`로 수정했다. SPICE 이전의 코드 오류로 dataset에는 영향 없음.
- **Attempt 2 — D006 timeout:** 병렬 PVT 평가 중 `FF_3.6V_m40C`가 120 s timeout. D006 전체를 순차 재평가해 17/17 완료했다. 원인은 자원 경합 또는 wall-time 증가 *가능성*이며 확정하지 않았다. 원본 진단 결과: `diagnostics/D006/`.

또한 데이터는 20개 설계점에 한정되고 corner-feasible 표본이 없어 region 경계·연결성·persistence를 판단할 수 없다. 전체 AC/DC/transient waveform은 상시 보존하지 않고, 이상 원인 검증 시 필요한 corner만 재생성한다.

## 09. Conclusion & Next Experiment

**결론:** multi-design에서도 worst-corner 불일치가 나타났으나, 초기 20개 설계점에서는 feasible region의 단서가 부족했다.

**다음 연구 질문:** ATLAS가 초기 20개 실측 결과를 학습해 새로운 TT 설계안을 순차적으로 제안하면 joint constraint 위반량이 감소하거나 최초 TT feasible을 찾을 수 있는가? → [EXP-003](../EXP-003_tt_adaptive_feasible_discovery/README.md).

최종 robust feasibility의 참/거짓은 17개 corner를 정확히 평가했을 때의 metric-wise worst 압축으로도 보존되므로, 이후 제안법은 **판정 자체가 아니라 탐색 효율을 개선하는지** 검증해야 한다.
