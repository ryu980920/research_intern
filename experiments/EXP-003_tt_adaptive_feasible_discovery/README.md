# EXP-003 — ATLAS GP 기반 TT Adaptive Feasible 탐색

**Status:** Completed · **Run:** 2026-10-09 23:56 (log ID 기준) · **Circuit:** GF180 two-stage op-amp · **Evaluation:** TT/3.3 V/27 °C, D000–D059

## Experiment at a Glance

| 항목 | 이번 실험의 답 |
| --- | --- |
| **왜 했는가?** | EXP-001·002에서 20 design × 17 corner 모두 infeasible이라, island 분석 전에 TT feasible 또는 경계 후보를 찾아야 했기 때문 |
| **무엇을 했는가?** | ATLAS/TopoBO의 GP surrogate로 초기 20점 학습 후 TT 설계안 40개를 순차적으로 선택·SPICE 평가 |
| **무엇을 알았는가?** | **TT feasible 0/60**. D050은 5/6 specs 통과, PM 54.16°(목표 60°), worst margin **-0.0973** |
| **그래서 다음은?** | PM–UGBW trade-off와 지표 추출 이상값을 확인하고, TT feasible 탐색을 확대할 후속 실험 설계 |

## 01. Background & Motivation

장기 목표는 **Cross-PVT Persistent Feasible-Island Modeling for Robust Analog Sizing**이다. 이 연구가 성립하려면 여러 PVT corner의 feasible 영역을 비교할 실제 설계점이 있어야 한다.

- [EXP-001](../EXP-001_pvt_init_params_baseline/README.md): D000 × 17 corners, feasible 0/17.
- [EXP-002](../EXP-002_atlas_initial_design_pvt/README.md): D001~D019 × 17 corners 추가, 통합 340 evaluations에서 feasible 0.
- Metric마다 worst corner가 다른 점은 관찰했지만, 아직 측정된 feasible island 자체는 없다.

따라서 **17-corner sweep을 무작정 확대하기 전에**, 상대적으로 저렴한 TT 평가로 feasible 또는 위반량이 작은 점을 탐색한다. 이번 EXP-003은 **최초 TT feasible 탐색을 위한 pilot**이며, island 개수·persistence나 제안 방법의 우월성을 검증한 실험은 아니다.

## 02. Research Question & Hypothesis

- **RQ1:** 초기 20개가 모두 TT-infeasible일 때, GP 기반 ATLAS가 제한된 평가 예산 안에서 최초 TT feasible을 찾는가?
- **RQ2:** 발견하지 못하더라도 각 spec을 동시에 고려한 normalized violation이 개선되는가?
- **RQ3:** GP/Mapper가 제안한 Adaptive 후보의 실제 TT 성능에서는 PM–UGBW 등의 trade-off가 어떻게 나타나는가?
- **Working hypothesis:** Adaptive 후보가 초기 후보보다 joint constraint 위반량이 작은 설계점을 발견할 수 있다.

**관측 기반 판정:** RQ1 = 미발견(0/60); RQ2 = D050에서 개선 확인; RQ3 = PM 통과 시 UGBW 미달하는 후보가 관찰됨. Random Search 등 대조군이 없어 **ATLAS가 다른 탐색법보다 우수하다는 결론은 불가**하다.

## 03. Experimental Setup

| 항목 | 설정 |
| --- | --- |
| Circuit | GF180 two-stage op-amp |
| Design parameters | `wp1, wn1, wp3, wn3, wn4, wn5` (width, m) + `cc` (F) = 7D |
| Evaluation | **TT-only**, 3.3 V / 27 °C, `pvt=False` |
| Simulator / PDK | ngspice 44.2, GF180 primitive models |
| Statistical variation | `sw_stat_global=0`, `sw_stat_mismatch=0` |
| Optimizer | ATLAS / `TopoBO`, `surrogate="gp"` (BoTorch), seed 42 |
| Actual evaluation budget | 60 TT design evaluations (initial 20 + adaptive 40) |
| Candidate pool | 50,000 surrogate-scored candidates/iteration, **not 50,000 SPICE evaluations** |
| Early stop | 최초 실제 feasible 발견 시 중단하도록 설정; 이번에는 해당 없음 |
| ATLAS pinned SHA | `dd23c5ba7beb598909be593e4a84c81dab92cc69` |
| Execution ID | `two_stage_opamp_gf180_ATLAS_B60_S42_20261009_235604` |

Budget 60과 `n_init=20`의 관계는 표준 runner의 `n_init_for()` 계산에 따른다(7 parameters에서 `min(21,60//3,50)=20`). 이는 계산비용을 제한한 **pilot 설정**이지 최적 예산의 증명은 아니다.

Detailed config / parameter bounds: [config/run_config.md](config/run_config.md). 실행 스크립트: [run_adaptive_tt_search.py](scripts/run_adaptive_tt_search.py).

## 04. Method & Procedure

1. EXP-001·002와 동일한 seed·initial design 함수를 사용해 D000~D019를 **TT에서 다시 실제 평가**했다. 기존 CSV를 그대로 GP에 주입하는 warm start는 사용하지 않았다.
2. 처음 20개의 7D 설계변수 `X`와 TT 6개 metric `Y`로 성능별 독립 GP surrogate를 학습했다.
3. D020부터 매 반복마다 global LHS 약 40,000 + 유망한 점 주변 local 약 10,000개 후보를 생성해 GP로 예측하고, near-feasible 예측 집합/Mapper와 acquisition score로 **1개 design**을 선택했다.
4. 선택된 **1개 design만 SPICE로 TT 평가**하고 관측값을 학습 집합에 추가한 후, 다음 반복에서 GP를 다시 fit했다.
5. 이를 D059까지 수행했다. GP surrogate는 `gp`로 고정했으며 `auto` 모드의 NN 전환은 사용하지 않았다.
6. 실제 평가마다 원본 `trajectory.csv`에 파라미터·metric·feasibility·iteration을 보존했다. 완료 후 공통 schema의 parameter/metric CSV를 분리했다.

**현재 코드와 실행 당시 코드의 구분:** 당시 run은 `data/trajectory.csv`로 스트리밍 저장했으며, 완료 후 원본을 손실 없이 `raw/trajectory.csv`로 보존했다. 저장소 정리 후의 [현재 실행 코드](scripts/run_adaptive_tt_search.py)는 **향후 실행 시** `raw/trajectory.csv`에 먼저 누적하고 [export_standard_data.py](scripts/export_standard_data.py)로 `data/`의 두 표준 CSV를 생성한다. 기존 완료된 실행의 SPICE 결과나 선택 순서는 변경하지 않았다. 기존 출력은 보호되며 같은 경로에 덮어쓰지 않는다.

## 05. Metrics & Evaluation Criteria

실제 판정 기준(6개 동시 통과):

| Metric | 목표 | 단위 |
| --- | --- | --- |
| Gain | ≥ 300 | dimensionless |
| UGBW | ≥ 20 | MHz |
| Phase Margin | ≥ 60 | degree |
| Bias current | ≤ 1 | mA |
| Settling time | ≤ 6 | µs |
| Output swing | ≥ 0.3 | V |

- `feasible=True`: **동일 design**의 위 6개 실제 TT 조건을 모두 만족.
- `n_specs_passed`: 통과 spec 수. **5/6 자체만으로 목표까지의 거리를 설명할 수 없음.**
- `worst_margin`: 각 metric의 normalized margin 최솟값. 최소조건은 `(actual-target)/target`, 최대조건은 `(target-actual)/target`. **0 이상이면 전부 통과**.
- `total_violation`: `sum(max(0,-margin))`로 모든 위반 정도를 합친 값.

ATLAS 내부의 `beta0`·`n_F_hat`은 **GP가 예측한 후보 집합에서 계산한 topology 지표**다. 이를 실제 회로에서 입증한 feasible island 개수로 해석하지 않는다.

## 06. Results & Figures

**핵심 결과:** TT 평가 **60/60 완료**, feasible **0/60**. 초기 설계안 20/20, Adaptive 신규 설계안 40/40 완료. 40개 Adaptive 설계점은 서로 다른 파라미터 조합이며 초기 20점과도 중복되지 않았다. D000~D019의 파라미터 및 TT 측정값은 EXP-001·002의 committed baseline과 일치한다.

| 설계안 | 구간 | PASS | PM | UGBW | Worst margin | Total violation |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| D005 | initial | 3/6 | 44.09° | 17.96 MHz | -0.3384 | 0.7057 |
| D009 | initial | 5/6 | 37.94° | 28.18 MHz | -0.3676 | 0.3676 |
| D030 | adaptive | 5/6 | 61.51° | 10.86 MHz | -0.4572 | 0.4572 |
| D044 | adaptive | 5/6 | 64.83° | 10.90 MHz | -0.4550 | 0.4550 |
| **D050** | **adaptive** | **5/6** | **54.16°** | **20.33 MHz** | **-0.0973** | **0.0973** |

D050의 나머지 성능: Gain **435.65**, Ibias **0.932 mA**, Settling **1.299 µs**, Swing **0.427 V** (네 조건 통과). 실패한 것은 PM 하나로, 목표 60°보다 약 5.84° 부족하다. D009 대비 `total_violation`은 약 **73.5% 감소**했으나 feasible은 아니다.

**ATLAS 실행 로그 분석** ([iterations.jsonl](raw/atlas_logs/two_stage_opamp_gf180_ATLAS_B60_S42_20261009_235604/iterations.jsonl), 총 60 record):

| 기록 항목 | Adaptive 40회 | 해석 |
| --- | ---: | --- |
| `fit_time` | **313.299 s 합계**, 중앙값 7.8625 s | 매 Adaptive 반복에 GP fit 시간 기록 |
| `acq_time` | **282.603 s 합계**, 중앙값 7.042 s | 후보 예측/선택 비용 |
| `tda_time` | **1.264 s 합계** | Mapper 재계산 또는 캐시 사용 |
| `sim_time` | 전체 60회 **4.630 s 합계** | 실제 TT 평가 시간 기록 |
| `n_F_hat` | 매 Adaptive 반복 5,000 | 모델 예측 후보 집합 크기 |
| `beta0` | 관측 범위 7~50 | 모델 예측 component 수; 실측 feasible island가 아님 |

**로그 검증:** iter 0~59 연속, init 20 + BO 40, Adaptive 40회 전부 양의 fit/acquisition 시간. `surrogate="gp"` 지정 및 optimizer 코드 흐름과 일치한다. 한 번(`D044`)의 fit_time은 10.591초로 10초를 넘었지만, `auto` 모드가 아니므로 NN 전환 조건은 적용되지 않는다. **GP 하이퍼파라미터 최적화(Marginal Likelihood)가 40번 모두 성공했다는 증거는 이 JSONL에 없다**. GP 구현은 MLL fit 실패 시 기본 모델로 계속 진행할 수 있고, 해당 예외의 print는 이 파일에 기록되지 않는다. 예측 정확도를 보려면 예측 평균/불확실성과 실측 오차를 추가 기록한 후 별도 평가해야 한다.

**그림:** Worst-margin vs iteration, Total-violation vs iteration, PM vs UGBW (나머지 4 specs 충족하는 점) 등을 후속 분석에서 생성한다. 이 README는 그림 파일이 저장소에 존재한다고 주장하지 않는다.

## 07. Discussion

- **Observation:** 60개 중 TT feasible은 없지만 best worst-margin이 개선됐고, D050에서 한 개 spec(PM)만 미달했다.
- **Interpretation:** GP 기반 탐색이 초기 샘플보다 joint feasibility 경계에 가까운 후보를 관측했다. 반면 PM 60°를 넘긴 D030·D044는 UGBW가 약 10.9 MHz에 머물러 trade-off가 나타났다.
- **Research implication:** 다음 실험에서는 compensation capacitor `cc`를 포함한 7D 변수의 PM–UGBW 민감도를 확인하고 TT feasible 후보 발견을 우선해야 한다. 단일 run으로 탐색 알고리즘의 비교 우위나 feasible island 연결성을 주장하지 않는다.
- **계산비용:** 이 run에서는 SPICE 시간이 짧고 GP fit/후보 선택이 더 큰 벽시계 시간 비중을 차지했다. 향후 robust 탐색 비용 비교는 **SPICE 호출 수와 전체 wall-clock 시간**을 함께 비교해야 한다.

## 08. Limitations & Issues

1. Feasible 0/60은 **전체 7D design space에 feasible이 없다는 증거가 아니다**.
2. TT-only로 수행했으므로 **17-corner PVT robustness, island persistence를 검증하지 못했다**. TT feasibility는 robust feasibility의 필요조건이나 충분조건은 아니다.
3. `F_hat`과 Mapper `beta0`은 모델 예측 구조. 직접 측정한 feasible component는 **0개 관측**이다.
4. 단일 seed=42, budget=60의 pilot이며 Random/다른 BO 대조군이 없다.
5. D014 등의 PM=-180°, UGBW=1 Hz, 비정상적인 settling 값은 시뮬레이터·metric extractor의 fallback/sentinel 또는 비정상 회로 응답일 수 있어 waveform/추출 코드 진단이 필요하다.
6. `iterations.jsonl`은 측정 metric 수치를 일부 6자리로 반올림한다. **고정밀 실제 metric은 `raw/trajectory.csv`/표준 `data/corner_metrics.csv`를 기준**으로 한다.
7. `progress.log` 또는 전체 터미널 표준출력은 이 저장소에 추가되지 않아, 개별 GP MLL fit 실패 출력의 유무를 검증하지 못한다.
8. 실행 당시의 `run_summary.json`과 전체 AC/DC/transient raw waveform도 이번 데이터 업로드에는 포함되지 않았다. 해당 파일이 실제 로컬에 있으면 별도 확인 후 보존한다.

## 09. Conclusion & Next Experiment

**결론:** 이번 EXP-003은 **GP 기반 순차적 Adaptive TT 탐색**을 실제로 수행했고, D050이라는 더 나은 near-feasible 후보를 확보했다. 그러나 **최초 TT feasible 발견에는 실패**했고, GP의 세부 MLL 학습 성공/예측 정확도는 추가 검증이 필요하다.

**다음 연구 질문 후보:**
- **Follow-up A — TT feasible 탐색:** D050 주변 및 기존 후보와 떨어진 넓은 영역을 모두 살펴보고, PM–UGBW trade-off 및 측정 이상값부터 확인한다.
- **Follow-up B — TT multi-island:** 실제 TT feasible 설계점을 여럿 확보한 뒤 멀리 떨어진 가능한 군집과 연결 경로를 검증한다. 유한 표본의 2D 그림만으로 7D의 단절을 단정하지 않는다.
- **Follow-up C — Cross-PVT persistent island:** 동일한 설계점 집합을 17개 corner에서 평가해 corner-wise 변화/교집합을 측정하고, 동일 비용의 worst-case baseline과 robust feasible 발견 효율을 비교한다.

제안법이 증명해야 할 것은 **모든 corner의 metric-wise worst를 정확히 구했을 때 robust feasibility 판정의 변화가 아니라**, corner-wise identity/geometry 보존이 탐색 효율을 높이는지이다.
