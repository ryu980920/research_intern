# EXP-004 — Warm Start 기능 검증 (신규 TT 평가 1회)

**Status:** Prepared / WSL 실험 미실행 · **Circuit:** GF180 two-stage op-amp · **Target:** EXP-003 D000–D059 재사용 + 신규 D060 1회

## Experiment at a Glance

| 항목 | 내용 |
| --- | --- |
| **왜 했는가?** | EXP-003의 60개 TT 결과를 다시 SPICE로 평가하지 않고 GP 학습에 재사용할 수 있는지 확인 |
| **무엇을 하는가?** | 이전 측정값 60개를 ATLAS initial observations로 replay한 뒤, 새 후보 D060만 실제 SPICE 평가 |
| **무엇을 성공으로 보나?** | 기존 60개 replay, 신규 SPICE 1회, GP 예측과 D060 실측 파라미터·6개 성능 모두 저장 |
| **그래서 다음은?** | 동작 검증에 성공하면 EXP-005에서 신규 평가 예산을 확대해 TT feasible 탐색 |

## 01. Background & Motivation

[EXP-003](../EXP-003_tt_adaptive_feasible_discovery/README.md)은 TT 평가 총 60회를 마쳤지만 feasible은 0/60이었다. 가장 유망한 D050은 worst margin 약 -0.0973, PM 54.16°(목표 60°)이다.

기존 `TopoBO.optimize()`를 그대로 새로 호출하면 초기 샘플을 SPICE로 다시 평가한다. 이 과정의 중복 계산을 없애고 기존 **60개 실측치를 사용해 GP를 새로 학습**할 수 있는지 검증한다. 이번 실험의 목표는 최적화 성능 비교나 island 발견이 아니다.

## 02. Research Question & Hypothesis

- **RQ1:** EXP-003의 60개 TT 관측값을 재시뮬레이션 없이 GP 학습에 사용할 수 있는가?
- **RQ2:** GP가 새로운 D060을 제안하고 **그 한 점만** 실제 SPICE 평가하는가?
- **RQ3:** D060의 GP 예측 평균·표준편차와 SPICE 실측치를 함께 기록할 수 있는가?
- **Working hypothesis:** 저장된 측정값을 첫 60번의 평가 반환값으로 공급하면, ATLAS 원본을 변경하지 않고 observation-based warm start를 구현할 수 있다.

## 03. Experimental Setup

| 항목 | 설정 |
| --- | --- |
| Circuit / PVT | GF180 two-stage op-amp; TT 3.3 V / 27 °C |
| PDK statistical variation | `sw_stat_global=0`, `sw_stat_mismatch=0` |
| Previous data | [EXP-003 raw/trajectory.csv](../EXP-003_tt_adaptive_feasible_discovery/raw/trajectory.csv): D000–D059, 설계 변수 7개 + 실측 metric 6개 |
| Optimizer | `TopoBO` / BoTorch GP, seed 42, `early_stop=True` |
| ATLAS commit | `dd23c5ba7beb598909be593e4a84c81dab92cc69` |
| Internal args | **`n_init=60, budget=61`** |
| **신규 SPICE budget** | **1회** (D060) |

내부 budget은 초기 replay 60개와 신규 평가 1개를 합친 누적 관측 수다. **신규 ngspice 호출이 61회라는 뜻이 아니다.** 상세: [config/run_config.md](config/run_config.md).

## 04. Method & Procedure

1. EXP-003 `raw/trajectory.csv`의 D000–D059 순서, 파라미터, metric, feasibility를 검증한다.
2. ATLAS의 초기 설계안 생성 함수는 이전 60개 파라미터를 반환하도록 변경하고, 해당 60개 `evaluate()` 호출에서는 **이미 측정한 metric을 반환**한다. 원본 `~/atlas`의 코드는 수정하지 않는다.
3. `surrogate="gp"`로 실측 데이터 60개를 학습해 ATLAS가 새 설계안 D060을 1개 제안한다.
4. `--dry-run`에서는 D060을 실제 시뮬레이션하기 직전 종료하고, 제안 값만 확인한다.
5. 검증 성공 후 일반 모드에서 D060을 실제 TT SPICE로 **한 번만 평가**하고 GP 예측값과 실측값을 따로 저장한다.

**실행 명령 (WSL, conda atlas 환경):**

```bash
cd ~/research_intern
python experiments/EXP-004_warm_start_smoke_test/scripts/run_warmstart_smoke.py --check-only
python experiments/EXP-004_warm_start_smoke_test/scripts/run_warmstart_smoke.py --dry-run
python experiments/EXP-004_warm_start_smoke_test/scripts/run_warmstart_smoke.py
```

단계별로 결과를 확인하고 진행한다. 특히 세 번째 명령은 **실제 ngspice 1회 실행**을 포함한다.

## 05. Metrics & Evaluation Criteria

**기능 성공 조건:** `n_replayed=60`, `n_new_spice=1`, 중복 없는 D060, 실제 평가 이전에 GP 예측 확보.

**회로 spec (6개 동시 통과):** Gain ≥300, UGBW ≥20 MHz, PM ≥60°, Ibias ≤1 mA, Settling ≤6 µs, Swing ≥0.3 V.

**진단 산출물:** D060의 각 spec별 GP 평균·표준편차, 실제 성능, `worst_margin`, `total_violation`. 한 점으로 GP의 전체 예측 정확도를 일반화하지 않는다.

## 06. Results & Figures

**Pending — 실제 WSL 실행 전.** 성공 시 예상 파일:

```text
data/
├─ design_points.csv       # 신규 D060 1행
└─ corner_metrics.csv      # 신규 D060 TT 1행
raw/
├─ trajectory.csv          # 신규 D060 + iteration/margins 1행
├─ prediction_D060.json    # 실제 SPICE 결과와 사전 GP 예측
└─ atlas_logs/             # 로컬 로그, GitHub 업로드 필수 아님
```

기존 D000–D059는 EXP-003의 파일을 **참조만** 하고 재저장·재시뮬레이션하지 않는다.

## 07. Discussion

실행 후 관측(60회 replay·신규 1회 확인 및 실측값), 해석(데이터 재사용 의미), 연구 시사점(EXP-005에서 보존할 상태 및 로그)을 **Observation → Interpretation → Research Implication** 순서로 기록한다.

## 08. Limitations & Issues

- GP 파라미터·Mapper cache 및 ATLAS 내부 학습 상태를 완전히 복원하는 checkpoint resume는 아니다. **이전 60개 데이터로 GP를 다시 학습**하는 observation warm start다.
- 이번 실행은 `n_init=60`, `budget=61`을 사용하므로 EXP-003을 끊김 없이 이어 돌렸을 때와 curriculum/최적화 시간축이 다를 수 있다.
- RunLogger에서 기존 60개는 `INIT`으로 보일 수 있지만 이번 EXP-004에서 새로 SPICE를 돌린 것이 아니다.
- GP MLL 최적화가 실패하면 ATLAS 코드가 기본 하이퍼파라미터로 돌아갈 수 있으므로 GP 학습 완전 성공이라고 단정할 수 없다.
- EXP-003의 일부 비정상적 metric에 따른 surrogate 예측 오차는 추가 검증이 필요하다.
- 사용자 연구환경에서 실제 GP/ngspice 실행은 아직 검증하지 않았다. `--dry-run`도 최적화 로그 파일을 생성할 수 있다.

## 09. Conclusion & Next Experiment

**Pending.** Warm Start가 정상적으로 실행되고 D060 실측값이 저장되면 EXP-004의 기능 가설을 지지한다. 그다음 [EXP-005](../README.md)에서 신규 SPICE 예산을 늘려 PM–UGBW trade-off를 관찰하면서 TT feasible 후보를 탐색한다.
