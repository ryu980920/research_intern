# EXP-001 — Initial Design의 17-Corner PVT Baseline

**Status:** Completed · **Date:** 2026-10-04 · **Circuit:** GF180 two-stage op-amp · **Evaluation:** D000 × 17 PVT corners

## Experiment at a Glance

| 항목 | 이번 실험의 답 |
| --- | --- |
| **왜 했는가?** | ATLAS 기본 설계안에서 PVT에 따른 성능 차이와 worst-corner 정보를 확인하고, 이후 연구의 첫 기준점을 확보하기 위해 |
| **무엇을 했는가?** | YAML `init_params`인 D000을 TT 포함 17개 corner에서 ngspice로 평가 |
| **무엇을 알았는가?** | Feasible corner **0/17**; 성능 지표마다 가장 불리한 corner가 서로 달랐음 |
| **그래서 다음은?** | 설계안 수를 늘려 같은 현상을 검증해야 함 → [EXP-002](../EXP-002_atlas_initial_design_pvt/README.md) |

## 01. Background & Motivation

장기 연구 목표는 **Cross-PVT Persistent Feasible-Island Modeling for Robust Analog Sizing**이다. 단순히 worst-case 값 한 세트만 저장하면 어떤 corner가 각 성능을 제한했는지 추적하기 어렵다. 먼저 실제로 corner별 결과가 달라지는지 한 설계안에서 확인해야 이후 multi-design 연구를 설계할 수 있다.

## 02. Research Question & Hypothesis

- **RQ1:** 동일한 설계안 D000은 17개 PVT corner에서 서로 다른 성능을 보이는가?
- **RQ2:** Gain·Ibias·PM·Settling·UGBW·Swing의 worst corner가 일치하는가?
- **Working hypothesis:** corner별 성능 차이가 있으며, 모든 metric의 worst corner가 같지는 않을 수 있다.

이번 실험은 **feasible island의 존재를 검증하지 않는다**. 설계점 하나로는 영역의 경계나 연결성을 알 수 없기 때문이다.

## 03. Experimental Setup

| 항목 | 설정 |
| --- | --- |
| Circuit | GF180 two-stage op-amp |
| Design point | `D000` = YAML `init_params` |
| Parameters | `wp1=17.33e-6`, `wn1=88.76e-6`, `wp3=72.10e-6`, `wn3=46.21e-6`, `wn4=19.64e-6`, `wn5=70e-6` m; `cc=3.48e-12` F |
| PVT | TT(3.3 V, 27 °C) + FF/SS/FS/SF × {3.0/3.6 V} × {-40/125 °C}; 총 17 |
| Simulator | ngspice 44.2; GF180 primitive PDK |
| Statistical switches | `sw_stat_global=0`, `sw_stat_mismatch=0` (deterministic PVT 비교) |
| Code baseline | ATLAS `dd23c5ba7beb598909be593e4a84c81dab92cc69` |

자세한 모델 버전·환경·조건은 [config/run_config.md](config/run_config.md)에 기록한다.

## 04. Method & Procedure

1. `CircuitEvaluator`와 동일한 회로 모델을 사용해 D000의 7개 설계 변수를 고정했다.
2. TT + 16개 PVT corner를 각각 평가해 여섯 성능 지표를 추출했다.
3. corner별로 **여섯 목표를 동시에 통과하는지** 판정했다.
4. 설계 변수는 `data/design_points.csv`, 측정값은 `data/corner_metrics.csv`에 구분해 저장했다.
5. 각 metric을 가장 나쁘게 만드는 corner를 비교했다.

재현 코드: [scripts/evaluate_init_params_pvt.py](scripts/evaluate_init_params_pvt.py).

## 05. Metrics & Evaluation Criteria

| Metric | 통과 조건 | 단위 |
| --- | --- | --- |
| `gain_min` | ≥ 300 | dimensionless |
| `ugbw_min` | ≥ 20 | MHz |
| `phm_min` | ≥ 60 | degree |
| `ibias_max` | ≤ 1 | mA |
| `t_settle_max` | ≤ 6 | µs |
| `vswing_min` | ≥ 0.3 | V |

**Corner feasible** = 해당 corner에서 여섯 spec 모두 통과. Worst corner는 각 metric의 최소/최대 방향에 따라 결정한다. 모든 corner의 metric-wise worst 값을 모아 만든 vector는 한 physical corner의 실제 관측치와 다를 수 있다.

## 06. Results & Figures

**실측 결과:** 17개 corner 모두 infeasible. 전 corner에서 `phm_min < 60°`이고, 두 corner에서는 UGBW도 20 MHz 미만이었다(SS/3.0 V/125 °C: 18.922 MHz; SF/3.0 V/125 °C: 19.936 MHz).

| Metric | 가장 불리한 corner | Worst value | 목표 |
| --- | --- | ---: | --- |
| Gain | FF / 3.0 V / 125 °C | 420.06 | Pass |
| Ibias | FF / 3.6 V / -40 °C | 0.660 mA | Pass |
| PM | FS / 3.6 V / -40 °C | 26.64° | **Fail** |
| Settling | SS / 3.0 V / 125 °C | 2.971 µs | Pass |
| UGBW | SS / 3.0 V / 125 °C | 18.922 MHz | **Fail** |
| Swing | FF / 3.0 V / 125 °C | 0.780 V | Pass |

주요 데이터: [design_points.csv](data/design_points.csv) (1행), [corner_metrics.csv](data/corner_metrics.csv) (17행). 두 CSV는 `design_id`로 연결된다. 현재 필수 figure는 별도 생성하지 않았으며 표는 원본 CSV 값에 근거한다.

## 07. Discussion

- **Observation:** Gain·Swing, Ibias, PM, Settling·UGBW가 각각 다른 corner에서 최악이었다.
- **Interpretation:** metric-wise worst-case로 압축한 결과는 여러 corner의 관측치를 섞은 vector가 될 수 있다.
- **Research implication:** 향후 optimizer의 worst-case 입력뿐 아니라 **corner identity와 corner-wise metric/feasibility**를 따로 보존해야 한다. 다만 모든 corner를 평가했다면 worst-case 압축이 최종 robust feasible의 참/거짓을 바꾸는 것은 아니다. 여기서 검증할 것은 구조 정보의 유실과 탐색 영향이다.

## 08. Limitations & Issues

- 단일 설계점만 평가해 feasible region의 크기·경계·연결성·persistence는 분석할 수 없다.
- Feasible corner가 0개라는 사실은 전체 설계공간에서 feasible이 존재하지 않는다는 증거가 아니다.
- 모든 corner의 AC/DC/transient 원시 파형은 상시 보존하지 않았다. 이상 결과 검증 시 필요 corner만 재실행하고 생성 조건을 남긴다.

## 09. Conclusion & Next Experiment

**결론:** PVT corner가 달라지면 성능이 바뀌며 metric별 worst corner도 일치하지 않음을 확인했다. 이 결과는 corner-wise 측정값을 보존하는 실험 구조의 첫 근거다.

**다음 연구 질문:** 여러 설계점에서도 같은 현상이 나타나는가? → [EXP-002](../EXP-002_atlas_initial_design_pvt/README.md)에서 D001~D019를 추가 평가했고 전체 340개 corner 평가 모두 infeasible이었다.
