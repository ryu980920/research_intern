# EXP-005 — GP Surrogate Reliability & Improvement

**Status:** Prepared · **Date:** 2026-10-10 · **Circuit:** GF180 two-stage op-amp · **PVT:** TT 3.3 V / 27 °C · **New SPICE budget:** **0**

## Experiment at a Glance

| 항목 | 이번 실험의 답 |
| --- | --- |
| **왜 했는가?** | [EXP-004](../EXP-004_warm_start_smoke_test/README.md)에서 Warm Start는 성공했지만 PM 오차와 비물리적 Settling 예측이 관찰되어, 탐색 횟수를 늘리기 전에 GP의 신뢰성을 평가할 필요가 있음 |
| **무엇을 하는가?** | EXP-003의 **60개 TT 실측**에서 이상값 점검 → 40개 학습/20개 시간순 검증 → 전처리·모델 비교 |
| **무엇을 발견했는가?** | **Pending.** 아직 EXP-005 분석을 실행하지 않음. EXP-004의 D060 단일 예측 오차만으로 전체 GP 품질을 결론 내리지 않음 |
| **그래서 다음은?** | 오류 원인을 데이터/전처리/모델 설정으로 좁히고, EXP-006에서 데이터 추가나 TT 탐색 확대 여부를 결정 |

## 01. Background & Motivation

[EXP-003](../EXP-003_tt_adaptive_feasible_discovery/README.md)은 ATLAS GP 기반 TT 탐색을 60개 설계안에 수행했으나 **Feasible 0/60**이었다. 가장 유망한 D050은 PM=54.16°로 60° 목표에 못 미쳤다.

[EXP-004](../EXP-004_warm_start_smoke_test/README.md)는 D000~D059의 관측값을 재시뮬레이션 없이 GP에 학습시키고, 새로운 D060을 실제 SPICE로 **1회 평가**해 Warm Start의 기능을 검증했다. D060 역시 **5/6 spec pass, PM=38.11°**로 feasible하지 않았다.

특히 D060의 GP 사전 예측에서는 PM 평균 약 **60.00°**와 실측 **38.11°**의 차이가 있었고, Settling Time 예측 평균은 **음수**였다. 음수 Settling은 비물리적이지만 GP 수학 모델이 고장 났다는 직접 증거는 아니다. 데이터 극단값·분포·학습 실패 여부·타깃 모델링 방식 등을 구분할 필요가 있다.

**핵심 판단:** 새 SPICE 평가를 늘리기 전에, **기존 60개 실측 데이터만으로** 예측 품질과 이상값 문제를 점검한다.

## 02. Research Question & Hypothesis

- **RQ1:** 기존 ATLAS GP는 학습에 쓰지 않은 TT 설계안들의 6개 metric을 얼마나 정확하게 예측하는가?
- **RQ2:** 극단적인 Settling/PM/UGBW 수치가 실제 회로 상태인지, metric extractor의 특수 처리값인지 추가 검증이 필요한가?
- **RQ3:** Settling처럼 양수인 물리량의 로그 변환이 raw-output GP의 비물리적 예측·오차를 줄이는가?
- **RQ4 (조건부):** 관심 설계 영역에 집중한 GP가 전체 공간 GP 대비 개선되는가? 단, 표본 수가 충분할 때만 비교.

**Working hypotheses (검증 전):**
1. 정상 µs 수준과 수백 ms 수준의 Settling을 한 회귀 타깃으로 학습하면 예측이 불안정해질 수 있다.
2. 양수 target의 로그 변환으로 비물리적 음수 예측을 피할 가능성이 있다.
3. D050 주변 표본을 더 잘 설명하려면 국소적 모델이 유용할 수 있지만, 표본이 적으면 오히려 악화할 수도 있다.

**판단 기준:** 같은 홀드아웃 설계점에서 예측 오차와 empirical interval hit rate가 유의미하게 개선되는지 살펴보고, GP 내부 fit fallback 발생 여부도 확인한다. 20점 비교만으로 광범위한 일반화나 인과적 원인을 확정하지 않는다.

## 03. Experimental Setup

| 항목 | 설정 |
| --- | --- |
| Circuit / corner | GF180 two-stage op-amp, TT 3.3 V / 27 °C |
| Historical dataset | [EXP-003 trajectory.csv](../EXP-003_tt_adaptive_feasible_discovery/raw/trajectory.csv), D000~D059 총 60개 |
| 참고 사례 | [EXP-004 GP prediction](../EXP-004_warm_start_smoke_test/raw/prediction_D060.json), D060 (초기 40/20 분할에서는 제외) |
| Param / metric | 7개 설계 변수, 6개 TT 성능지표 |
| GP baseline | ATLAS `GPSurrogate` / BoTorch independent GP, Matérn 5/2 ARD |
| Fixed ATLAS commit | `dd23c5ba7beb598909be593e4a84c81dab92cc69` |
| 검증 분할 | **학습 D000~D039 (40개), 검증 D040~D059 (20개)** |
| GP seed (예정) | 42 |
| **새 SPICE 설계점** | **0개** |
| 실험 단계 | 1. 데이터 점검 → 2. Baseline 검증 → 3. Transform/Local 비교 |

상세 설정, 이상값 판정 기준과 검증 유의사항: [config/run_config.md](config/run_config.md).

## 04. Method & Procedure

**Stage 1 — 데이터 점검 (코드 준비 완료, 아직 실행 전)**

1. D000~D059의 파라미터, 6개 성능값, 순서와 값의 유효성을 확인한다.
2. PM≈-180°, UGBW≤1 Hz, 매우 긴 Settling(목표의 100배 초과) 등의 설계안을 **점검 대상으로 표시**한다.
3. 분포 요약과 원본 CSV SHA256을 기록한다. Flag가 표시됐다고 데이터를 삭제하거나 SPICE 오류로 판정하지 않는다.

실행 코드: [scripts/audit_tt_dataset.py](scripts/audit_tt_dataset.py).

```bash
cd ~/research_intern
python experiments/EXP-005_gp_surrogate_reliability/scripts/audit_tt_dataset.py
```

기본 실행은 분석 결과만 출력한다. 확인 후 `--save`로 `data/analysis/`에 기록할 수 있으며 기존 결과를 덮어쓰지 않는다.

**Stage 2 — 기존 GP baseline의 예측 성능 검증 (예정, 아직 코드 미구현)**

- 학습 40개로 GP 6개 모델을 학습하고 D040~D059의 실제 성능을 학습에서는 제외한다.
- 각 metric의 GP mean/std와 실측을 비교하고 **MAE, RMSE, 정규화 오차, 예측 구간 포함률**을 계산한다.
- GP fit 실패 시 원본 ATLAS가 기본 hyperparameter로 fallback할 수 있으므로 그 여부를 로그에서 분리해 기록한다.
- 적응형 탐색으로 수집된 20개 검증 설계점은 iid 샘플이 아니므로 외삽 정확도의 일반화를 피한다.

**Stage 3 — 개선 가설 비교 (예정)**

- Baseline vs 양수 Settling의 로그 변환 모델을 **같은 데이터 분할**에서 비교한다.
- 필요하다면 지역별 학습 모델을 검토하되, D050 주변에 데이터가 충분하지 않으면 무리하게 국소 GP가 더 좋다고 주장하지 않는다.
- 비교 과정에서 새 설계점·SPICE 실행을 만들지 않는다. 추가 측정이 필요하다는 근거가 생길 때만 EXP-006에서 별도 예산을 정한다.

## 05. Metrics & Evaluation Criteria

| 지표 | 의미 | 이유 |
| --- | --- | --- |
| MAE (단위: 원래 metric) | 관측값과 예측값 차이의 절댓값 평균 | 전반적인 오차 크기 |
| RMSE (단위: 원래 metric) | 제곱 오차 평균의 제곱근 | 큰 예측 실패에 민감 |
| Standardized residual | `(y_true - mean) / pred_std` | GP가 추정한 불확실성 대비 실제 오차 |
| Empirical 95% interval hit rate | `mean ± 1.96 × std` 안에 실제 값이 포함된 비율 | 예측 구간의 사후 진단 (보장된 95% coverage 아님) |
| Fit/fallback check | MLL 최적화 성공·fallback 여부 | 모델 구조 문제와 fit 실패를 구분 |
| Physical validity | 예: Settling 예측값이 양수인지 | 모델 출력의 물리적 해석 가능성 |

MAE/RMSE는 성능별 단위가 다르므로 metric 간 원시 오차값을 직접 서열화하지 않는다. 로그 타깃 모델은 역변환과 예측 구간 정의를 별도로 명시해야 한다.

## 06. Results & Figures

**Pending — EXP-005 코드와 실험 문서를 준비한 상태. 아직 데이터 audit 또는 GP validation을 수행하지 않았다.**

예정 산출물:

```text
scripts/
  audit_tt_dataset.py         # Stage 1, 구현 완료
data/analysis/
  dataset_audit.json          # Stage 1 실행 후 생성
  anomaly_flags.csv           # Stage 1 실행 후 생성
  ...                         # Stage 2/3 metric-wise prediction/error (추후 정의)
figures/
  ...                         # Stage 2/3 예측 vs 실측 및 오차 시각화
```

EXP-005에는 **새로운 SPICE 관측값이 없으므로** 이전 실험의 `design_points.csv`와 `corner_metrics.csv`를 중복 저장하지 않는다. 원본 데이터는 EXP-003에 남겨 추적한다.

## 07. Discussion

**Observation (현재 알려진 이전 실험 사실):** EXP-004 D060에서 PM mean 59.995° vs observed 38.107°, Settling GP mean은 음수였다.

**Interpretation (미검증 가설):** raw-scale 타깃의 극단적인 분포나 모델 출력 방식이 원인일 가능성은 있으나, **현재 실험에서 증명된 것은 아니다**.

**Research implication:** EXP-005의 동일 학습·검증 데이터로 원인별 가설을 비교한 후, 추가 SPICE 데이터가 필요한지를 판단한다.

## 08. Limitations & Issues

- D040~D059는 EXP-003의 **adaptive search로 선택된 샘플**이며 독립 무작위 추출 표본이 아니다. 따라서 단일 holdout 통계는 제한된 탐색 궤적에 대한 진단 결과다.
- GP fit의 내부 MLL 최적화 실패 여부는 아직 직접 검증되지 않았다.
- 일부 extreme metric이 물리적으로 실제 가능한 값인지 extractor fallback인지는 아직 확인되지 않았다. 데이터를 임의로 삭제하지 않는다.
- 처음 60개의 모든 데이터가 학습에 충분한 공간 커버리지를 제공한다고 가정하지 않는다.
- TT-only의 GP 신뢰성은 17-corner robust feasibility 또는 feasible island persistence의 증거가 아니다.

## 09. Conclusion & Next Experiment

**결론 보류.** 실험 질문만 정하고 파일과 Stage 1 audit 코드를 준비했다. 이후 관측된 예측 오차를 바탕으로 기존 GP를 유지할지, 출력 변환 또는 국소 모델을 채택할지, 추가 데이터를 확보할지 결정한다.

**후속 EXP-006 (조건부):** EXP-005에서 데이터 부족이 병목이라고 판단되면 GP 예측 불확실성 및 near-feasible 영역을 고려하여 신규 TT 설계점의 평가 예산과 위치를 설계한다.
