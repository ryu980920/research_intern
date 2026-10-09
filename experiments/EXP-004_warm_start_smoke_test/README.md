# EXP-004 — Warm Start 기능 검증 (신규 TT 평가 1회)

**Status:** Completed (Warm Start functional validation) · **Circuit:** GF180 two-stage op-amp · **Target:** EXP-003 D000–D059 재사용 + 신규 D060 1회

## Experiment at a Glance

| 항목 | 내용 |
| --- | --- |
| **왜 했는가?** | EXP-003의 60개 TT 결과를 다시 SPICE로 평가하지 않고 GP 학습에 재사용할 수 있는지 확인 |
| **무엇을 하는가?** | 이전 측정값 60개를 ATLAS initial observations로 replay한 뒤, 새 후보 D060만 실제 SPICE 평가 |
| **무엇을 성공으로 보나?** | 기존 60개 replay, 신규 D060 설계점 1회 TT 평가, GP 예측과 실측 저장 → **성공** |
| **그래서 다음은?** | EXP-005에서 모델의 예측 한계(특히 PM, settling)를 추적하면서 신규 평가 예산 확대 |

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

**완료 — 2026-10-10.** `--check-only` → `--dry-run` → 실제 실행 검증 완료.

**실행 증거(WSL stdout):** `[VERIFIED] warm-start replay=60, actual NEW TT SPICE calls=1`. 기존 D000–D059는 evaluator의 캐시 반환값으로만 전달되어 다시 시뮬레이션하지 않았다. 여기서 **1회는 신규 설계안 하나에 대한 evaluator 호출**이고 그 내부의 AC/DC/transient 분석 수까지 1이라는 뜻은 아니다.

| 항목 | 검증된 값 |
| --- | --- |
| Historical observations | **60개**, EXP-003 D000–D059 |
| Historical evaluations in new run | **0개** |
| Newly evaluated design | **D060**, TT 3.3 V / 27 °C |
| New design evaluations | **1개** |
| New feasible design | **0개**; 5/6 spec pass |
| New D060 worst margin | **-0.3649** (PM 부족) |
| Wall time | **16.5 s** (GP fit 8.91 s; 새로운 설계점 시뮬레이션 로그 0.14 s) |
| GP model | BoTorch GP fit 호출 완료, 사전 예측 저장; MLL의 내부 수치 최적화 성공 여부는 별도 검증되지 않음 |

D060 physical parameters:

| wp1 | wn1 | wp3 | wn3 | wn4 | wn5 | cc |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5.336 µm | 51.370 µm | 55.526 µm | 27.429 µm | 16.638 µm | 83.126 µm | 2.2511 pF |

**GP prediction vs. SPICE measurement for D060**

| Metric | GP predicted mean ± std | TT SPICE observed | Observation − prediction (std units) |
| --- | ---: | ---: | ---: |
| Gain | 426.785 ± 78.728 | 439.520 | +0.16σ |
| Ibias | 0.5798 ± 0.0331 mA | 0.6681 mA | +2.66σ |
| Phase Margin | 59.995 ± 16.845° | **38.107°** | **−1.30σ** |
| Settling Time | **−785.81 ± 1496.12 µs** | 1.7633 µs | +0.53σ |
| UGBW | 34.050 ± 4.203 MHz | 26.312 MHz | −1.84σ |
| Output Swing | 0.5607 ± 0.1651 V | 0.7744 V | +1.29σ |

GP PM 평균 59.995°는 목표 60°에 거의 같지만 **16.845° 표준편차**를 갖는다. 따라서 GP가 PM 충족을 확신했다는 해석은 잘못이다. Settling 평균은 음수로 **물리적으로 의미가 없는 값**이다.

**측정 데이터(원본 사용자 제공):**
- [data/design_points.csv](data/design_points.csv) — D060 실제 적용 물리 파라미터.
- [data/corner_metrics.csv](data/corner_metrics.csv) — D060 실제 6개 TT metric.
- [raw/prediction_D060.json](raw/prediction_D060.json) — SPICE 평가 전에 생성된 GP mean/std와 평가 후 observed.
- `raw/trajectory.csv` — 스크립트가 로컬 WSL에 생성한 D060 상세 기록. **GitHub에는 아직 미업로드**, 제공받은 표준 CSV와 JSON만 GitHub에 저장함.
- `raw/atlas_logs/` — 로컬 실행 기록. GitHub 업로드 필수 아님.

## 07. Discussion

**Observation:** EXP-003의 60개 표본을 재평가하지 않고 GP 데이터로 전달했고 신규 D060 한 점을 선택·시뮬레이션했다. 기능적 Warm Start 성공. D060은 5/6 통과했으나 PM 38.11°가 목표 60° 미달. EXP-003 최선 D050(PM 54.16°, UGBW 20.33 MHz) 대비 신규 D060(PM 38.11°, UGBW 26.31 MHz)은 BW가 높아지고 PM이 낮아졌다.

**Interpretation:** GP가 D060의 PM을 59.995°로 예측했으나 실측은 38.107°(−21.888°, −1.30σ)였다. Ibias 오차는 +2.66σ, UGBW 오차는 −1.84σ였다. 한 점의 오차만으로 GP의 전반적 보정 성능 또는 PM–UGBW 인과적 trade-off를 확정할 수 없다. GP predicted std는 calibration의 증거가 아니라 모델의 불확실성 추정값이다.

**Research implication:** 이후 예산을 확대한다면 설계안별 GP의 **사전 예측 평균/표준편차 → 실제 SPICE 결과**를 보존해 실제 오류 분포를 측정해야 한다. Settling Time의 음수 평균은 GP가 raw-positive 물리량을 직접 모델링하는 과정 및 극단값 처리의 적절성을 점검할 이유가 된다. EXP-003 historical 데이터에는 settle 최대 0.9851 s, 중앙값 약 2.316 µs의 큰 범위 차이가 있어 예측을 악화시키는지 추가 검증이 필요하다. **원인으로 확정하지 않는다.**

## 08. Limitations & Issues

- 이 방법은 기존 GP/Mapper checkpoint 복구가 아니라 **60개 관측값을 재사용해 GP를 다시 학습**하는 observation warm start다.
- `n_init=60, budget=61`과 이전의 `n_init=20, budget=60`은 최적화 스케줄이 달라, 완전히 동일한 연속 실행과 같다고 주장할 수 없다.
- GP MLL hyperparameter optimization의 모든 성공 여부는 WSL 로그/소스의 fallback 검증 없이 단정할 수 없다.
- **Settling Time 예측 평균이 음수**여서 물리량 모델링의 적절성이 의심된다. 극단값이 원인이라는 설명은 아직 가설이다.
- D060 **한 점**으로 평균 예측 오차, calibration, surrogate 품질 전체를 평가할 수 없다.
- 60개의 historical observations가 실행 로그상 `INIT`으로 표시되더라도 신규 SPICE를 60번 실행했다는 뜻이 아니다.
- 현재 실험은 TT-only이며 **17-corner robust feasibility와 무관**하다.

## 09. Conclusion & Next Experiment

**기능 가설 채택:** 60개 캐시 replay와 신규 D060 설계점 평가 1회가 실제로 확인되었으므로, 기존 측정 데이터를 다시 시뮬레이션하지 않고 ATLAS GP 최적화에 재사용하는 Warm Start 기능을 검증했다. **설계 성공은 아니다**: D060은 PM 한 조건 때문에 TT feasible = False.

**EXP-005 방향:** 새로운 설계안 평가 예산을 점진적으로 확대하되, 모든 신규 제안에 대해 6개 GP 사전 예측과 실측을 짝지어 기록하고, 특이 metric 및 모델의 불확실성 추정을 점검한다. D050 주변 local search와 다른 유망 영역 탐색의 비중은 성능 측정 결과를 근거로 결정한다. Feasible island / robust PVT 가설 검증은 이후 단계다.
