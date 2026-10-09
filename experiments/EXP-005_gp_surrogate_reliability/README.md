# EXP-005 — GP Surrogate Reliability & Improvement

**Status:** Running (Stage 1/2/2b/3A executed; Stage 3B planned) · **Date:** 2026-10-10 · **Circuit:** GF180 two-stage op-amp · **PVT:** TT 3.3 V / 27 °C · **New SPICE budget:** **0**

## Experiment at a Glance

| 항목 | 이번 실험의 답 |
| --- | --- |
| **왜 했는가?** | [EXP-004](../EXP-004_warm_start_smoke_test/README.md)에서 Warm Start는 성공했지만 PM 오차와 비물리적 Settling 예측이 관찰되어, 탐색 횟수를 늘리기 전에 GP의 신뢰성을 평가할 필요가 있음 |
| **무엇을 하는가?** | EXP-003의 **60개 TT 실측**에서 이상값 점검 → 40개 학습/20개 시간순 검증 → 전처리·모델 비교 |
| **무엇을 발견했는가?** | **Stage 1:** 60개 중 7개 조사 대상. **Stage 2:** 원본 GP 40/20 검증, PM MAE 28.73°. **Stage 2b:** Settling의 무차원 fallback이 시간 필드에 혼합됨을 확인. **Stage 3A:** 대체값 제외 GP(B)는 PM·Settling 오차 감소, UGBW 오차 증가. Settling B의 분산 경고 발견 |
| **그래서 다음은?** | Stage 3B에서 GP B의 수치 안정성/예측 분산을 확인(아직 미실행) → 측정 성공 flag·실패 설계 정보 분리 → 필요 시 EXP-006 추가 평가 결정 |

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
1. 일부 Settling은 실제 시간이 아닌 **무차원 정규화 편차 `d_settle`**이므로 시간과 섞어 GP에 학습시키면 모델 성능을 왜곡할 수 있다. (소스 확인)
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
| GP seed | 42 (실행 시 사용) |
| **새 SPICE 설계점** | **0개** |
| 실제 진행 순서 | **1. audit → 2. 원본 GP baseline → 2b. extractor 의미 확인 → 3A. 대체값 제외 A/B 완료 → 3B. 수치 안정성 검증 계획** |

상세 설정, 이상값 판정 기준과 검증 유의사항: [config/run_config.md](config/run_config.md).

## 04. Method & Procedure

**Stage 1 — 데이터 점검 (WSL audit 실행 확인, 저장은 확인 대기)**

1. D000~D059의 파라미터, 6개 성능값, 순서와 값의 유효성을 확인한다.
2. PM≈-180°, UGBW≤1 Hz, 매우 긴 Settling(목표의 100배 초과) 등의 설계안을 **점검 대상으로 표시**한다.
3. 분포 요약과 원본 CSV SHA256을 기록한다. Flag가 표시됐다고 데이터를 삭제하거나 SPICE 오류로 판정하지 않는다.

실행 코드: [scripts/audit_tt_dataset.py](scripts/audit_tt_dataset.py).

```bash
cd ~/research_intern
python experiments/EXP-005_gp_surrogate_reliability/scripts/audit_tt_dataset.py
```

기본 실행은 분석 결과만 출력한다. 확인 후 `--save`로 `data/analysis/`에 기록할 수 있으며 기존 결과를 덮어쓰지 않는다.

**Stage 2 — 기존 GP baseline의 예측 성능 검증 (WSL 완료)**

- 학습 40개로 GP 6개 모델을 학습하고 D040~D059의 실제 성능을 학습에서는 제외한다.
- 각 metric의 GP mean/std와 실측을 비교하고 **MAE, RMSE, 정규화 오차, 예측 구간 포함률**을 계산한다.
- GP fit 실패 시 원본 ATLAS가 기본 hyperparameter로 fallback할 수 있으므로 그 여부를 로그에서 분리해 기록한다.
- 적응형 탐색으로 수집된 20개 검증 설계점은 iid 샘플이 아니므로 외삽 정확도의 일반화를 피한다.

실행 코드: [scripts/evaluate_gp_baseline.py](scripts/evaluate_gp_baseline.py). **실제 ATLAS `GPSurrogate`를 그대로 사용**하며 기존 YAML/ATLAS commit을 검증한다. SPICE 실행 없이 6개 모델 fit → D040–D059 예측 120행을 계산한다. GP의 `MLL fit failed` 메시지를 별도로 기록한다.

```bash
cd ~/research_intern
python experiments/EXP-005_gp_surrogate_reliability/scripts/evaluate_gp_baseline.py
```

결과는 `data/analysis/gp_baseline_holdout_predictions.csv` 및 `gp_baseline_holdout_summary.json`에 저장한다(덮어쓰기 금지). 이 실행은 GP fitting을 수행하며 **ngspice는 호출하지 않는다**.

**Stage 2b — Metric 추출 의미 점검 (소스 검증 및 WSL 진단 실행 완료)**

- [ATLAS `CircuitClass.py`](https://github.com/youngmin0oh/atlas/blob/dd23c5ba7beb598909be593e4a84c81dab92cc69/eval_engines/ngspice/CircuitClass.py)의 `find_ugbw`는 unity-crossing 탐색 실패 시 **첫 AC 주파수(이 netlist에서 1 Hz)**를 반환한다. `find_phm`도 탐색 실패 시 **-180°**를 반환한다.
- `get_tran_stable_meas`는 유효한 settling index가 없어 계산 결과가 NaN이면 **무차원 `d_settle`을 `settlingTime`에 대입**한다. [GF180 TT netlist](https://github.com/youngmin0oh/atlas/blob/dd23c5ba7beb598909be593e4a84c81dab92cc69/eval_engines/ngspice/ngspice_inputs/netlist/two_stage_opamp_cont_gf180_tran_tt_3.3_27.cir)의 transient 종료는 **401 µs**이다.
- EXP-003 `trajectory.csv` 확인: D013, D014, D015, D016, D017, D023, D047의 저장된 Settling 값은 **401 µs보다 크므로 관측 가능한 실제 settling 시간일 수 없다**(학습 6, holdout 1). D014/D047의 **UGBW 1 Hz + PM -180°**는 코드의 paired sentinel과 정확히 일치한다(학습 1, holdout 1).
- 작은 settling 값이라고 유효한 시간이라는 증거는 아니다. 모든 개별 결과의 waveform과 유효성 flag는 아직 남아 있지 않다.
- 기록 코드: [scripts/diagnose_metric_semantics.py](scripts/diagnose_metric_semantics.py). 소스 SHA·netlist SHA·dataset SHA와 설계별 확정 가능한 플래그를 `data/analysis/metric_semantics_*.{json,csv}`에 보존한다. SPICE/GP 재실행 0회.

```bash
cd ~/research_intern
python experiments/EXP-005_gp_surrogate_reliability/scripts/diagnose_metric_semantics.py
```

**Stage 3A — 대체값 학습 제외 GP 비교 (WSL 실행 완료)**

- [scripts/compare_validity_aware_gp.py](scripts/compare_validity_aware_gp.py)는 Stage 2에서 저장한 **원본 GP(A) 예측 120개**와 동일한 고정 코드의 **대체값 제외 GP(B)** 예측을 비교한다.
- B는 **metric별 독립 GP**를 원래 ATLAS `GPSurrogate`로 다시 학습한다. PM/UGBW는 학습 D014를 제외해 **39개**, Settling은 D013/014/015/016/017/023을 제외해 **34개**로 학습한다. Gain, Ibias, Swing은 영향을 받지 않으므로 재학습하지 않는다.
- 공정한 오차 비교를 위해 PM/UGBW/Settling 모두 **D047(확정 대체값)을 제외한 공통 검증 19개**에서 A와 B의 MAE/RMSE/근사 95% 구간 포함률/음수 예측 수를 비교한다.
- 원본 60개 관측/실패 설계안 정보는 **삭제·수정하지 않는다**. 확정된 대체값을 regression 학습에만 사용하지 않는다. 작은 Settling 값을 모두 유효하다고 보증하지 않으며, 검증도 잠정적이다.
- 의존 파일: Stage 2 `gp_baseline_holdout_predictions.csv`, `gp_baseline_holdout_summary.json`; Stage 2b `metric_semantics_audit.json`, `metric_semantics_flags.csv`. 모든 입력 SHA와 ATLAS 고정 커밋을 검증한다.
- 결과: `data/analysis/validity_aware_gp_comparison.csv`, `data/analysis/validity_aware_gp_summary.json`. 신규 SPICE 0회, B GP fit 3회.

```bash
cd ~/research_intern
git pull --ff-only
python experiments/EXP-005_gp_surrogate_reliability/scripts/compare_validity_aware_gp.py
```

**Stage 3B — 단위에 따른 Settling GP 수치 안정성 검증 (실행 코드 준비, WSL 미실행)**

- GP B에서 **GPyTorch Negative variance 경고**가 출력됐고, Settling B 예측 표준편차가 **19개 중 18개에서 1e-5 s = 10 µs**로 동일했다.
- **가설적 후속 비교:** Settling B의 **동일한 학습 34개 / 검증 19개**에서 target 단위만 초(s) → 마이크로초(µs)로 변경하고 공통 단위로 역변환해 평균·MAE/RMSE·분산/표준편차·경고 여부를 비교한다.
- 아직 실행하지 않았다. 단위 변환이 안정성을 개선한다는 결론은 없음.



실행 스크립트: [scripts/test_settling_gp_unit_stability.py](scripts/test_settling_gp_unit_stability.py). 원본 GF180 실험이나 Stage 3A 결과를 덮어쓰지 않는다.

실험은 **GP B를 동일 설정으로 한 번 재학습(재현성 검증)**한 뒤, **GP C에 동일한 34개 출력값만 10^6배로 변경해 한 번 더 학습**한다. 같은 D040~D059 중 D047을 뺀 19개에서 예측을 수행하고 **평균과 표준편차를 모두 µs로 환산**한다. 경고 메시지·음수 평균 수·표준편차 10 µs 동일값 개수·Stage 3A B와의 재현 차이·MAE/RMSE를 별도로 기록한다. 결과 파일은 \`data/analysis/stage3b_settling_unit_comparison.csv\`, \`stage3b_settling_unit_summary.json\`이며 신규 SPICE는 0회다.

\`\`\`bash
cd ~/research_intern
git pull --ff-only
python experiments/EXP-005_gp_surrogate_reliability/scripts/test_settling_gp_unit_stability.py
\`\`\`

출력 \`MLL_fallback\`과 음수 분산 경고는 다른 문제다. 경고가 사라진다는 것만으로 GP가 정확하거나 uncertainty-calibrated 모델이 됐다고 결론 내릴 수 없다. 실행 결과 수치를 확인한 뒤에만 Stage 3B의 결론을 기재한다.

**Stage 3C 및 이후 — 측정 유효성/실패 영역 처리 (추후 검토)**

- 기존 Baseline은 원본 그대로 보존하고, 별도로 **확정적인 무차원 fallback을 학습에서 제외한 raw-target GP와 동일 학습셋의 log-target GP**를 비교한다. 검증도 동일한 후보 집합(확실한 무효 label 제외)에서 한다. 단, 제외되지 않은 샘플의 Settling 유효성은 파형 없이 보장할 수 없다는 한계를 명시한다.
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

**Stage 1:** 60개 점검·중복 0개, 이상값 플래그 7개.  
**Stage 2:** 40 train/20 holdout, 총 120개 예측, GP fit 8.51 s, 캡처된 MLL fallback 메시지 없음, 신규 SPICE 0회. 첨부된 로컬 `gp_baseline_holdout_predictions.csv`를 검사했고 GitHub 업로드는 아직 진행하지 않았다.

| GP | Holdout MAE | 근사 95% 구간 포함률 |
| --- | ---: | ---: |
| Gain | 101.542 | 90% |
| Ibias | 0.160212 mA | 90% |
| Phase Margin | 28.7337° | 80% |
| Settling | 53.2425 ms (유효 시간 + 무차원 fallback 혼합이라 **물리적 시간 MAE로 해석 불가**) | 95% |
| UGBW | 7.05829 MHz (sentinel 포함) | 90% |
| Swing | 0.165618 V | 90% |

**Extractor 확인:** pin된 ATLAS 코드에서 AC invalid-crossing sentinel과 settling 무차원 fallback의 정확한 발생 경로를 확인했다. 기존 MAE는 **원시 데이터에 대한 수학적 오차**지만 일관된 물리량의 오차로 해석할 수 없는 metric이 있다.

**Stage 2b:** TT transient 종료 시간 401 µs. Settling 필드가 시간창보다 큰 설계안 **D013/014/015/016/017/023/047 (학습 6, 검증 1)**; AC UGBW 1 Hz·PM -180° paired sentinel **D014/D047 (학습 1, 검증 1)**. 원본 waveform 없음으로 나머지 53개 settling 값은 측정 유효성 미확정.

**Stage 3A — 같은 검증 설계점 19개에서 A/B 성능 비교** (`GP A`: 원본 40개 학습 / `GP B`: metric별 대체값 제외; PM/UGBW 39개, Settling 34개):

| Metric | A MAE | B MAE | A RMSE | B RMSE | 근사 95% 포함률 A→B | 판단 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| PM (°) | 16.8995 | **14.9638** | 21.8781 | **19.0677** | 84.2% → 89.5% | **11.45% 개선**, B 유리한 점 10/19 |
| UGBW (MHz) | **7.1082** | 9.8395 | **10.5405** | 15.3291 | 89.5% → 89.5% | **38.42% 악화**, B 유리한 점 6/19 |
| Settling (µs 상당*) | 8005.33 | **7.93263** | 19293.75 | **22.6951** | 100% → 94.7% | 저장 숫자 기준 **99.90% 오차 감소**, B 유리 19/19 |

*검증 Settling 레이블 19개의 실제 물리적 유효성이 입증된 것은 아니므로, GP B의 7.93 µs를 실제 time-prediction 정확도라고 단정하면 안 된다.*

**Stage 3A 추가 관찰:** GP B fitting 시간 **5.62 s**(PM 3.22, UGBW 1.58, Settling 0.82), 명시적 MLL fallback 0개. Settling B 음수 평균 예측 **0/19**(A 8/19)이나, **GPyTorch의 `Negative variance values detected` 경고**, B posterior `std=1e-5 s`가 **18/19**에서 발생. 분산이 1e-10으로 보정될 때 나오는 크기와 일치하므로 **95% coverage 94.7%를 곧바로 calibrated uncertainty의 증거로 해석하지 않는다.** 실제 원인과 개선 효과는 다음 검증이 필요하다.

**업로드된 실험 결과 사본(로컬 파일과 충돌하지 않도록 분리 보존):**

- [Stage 2 GP 120행 예측 CSV](data/analysis/archive/gp_baseline_holdout_predictions.csv)
- [Stage 3A GP A/B 57행 비교 CSV](data/analysis/archive/validity_aware_gp_comparison.csv)
- [Stage 3A GP A/B 통계 JSON](data/analysis/archive/validity_aware_gp_summary.json)
- [결과 파일 provenance 및 SHA256](data/analysis/archive/README.md)
- [2026-10-10 연구일지 (실행 순서)](../../logs/2026-10/2026-10-10.md)

**경로 주의:** `data/analysis/archive/`는 사용자가 업로드한 결과를 GitHub에 보존하기 위한 별도 폴더다. WSL `data/analysis/`의 기존 생성 파일은 이름 충돌 방지를 위해 덮어쓰거나 이동시키지 않았다. Stage 1의 `--save` 실행 확인 및 Stage 2/2b 일부 원본 summary/flag 파일 업로드는 미완료.

예정 산출물:

```text
scripts/
  audit_tt_dataset.py         # Stage 1, 구현/실행 확인
  evaluate_gp_baseline.py     # Stage 2, GP 학습/검증 WSL 실행 완료
  diagnose_metric_semantics.py # Stage 2b, extractor 소스 판정 확인/WSL 실행 완료
  compare_validity_aware_gp.py # Stage 3A, GP(A) vs 대체값 제외 GP(B) WSL 실행 완료
  test_settling_gp_unit_stability.py  # Stage 3B, 수치 안정성 비교 실행 대기
data/analysis/
  dataset_audit.json          # Stage 1 실행 후 생성
  anomaly_flags.csv           # Stage 1 --save 실행 후 생성
  gp_baseline_holdout_predictions.csv   # Stage 2 실행 후 120행
  gp_baseline_holdout_summary.json       # Stage 2 실행 후 MAE/RMSE/coverage/fallback
  metric_semantics_audit.json            # Stage 2b 실행 후 근거와 split별 개수
  metric_semantics_flags.csv             # Stage 2b 실행 완료, 설계점별 유효성 판정
  validity_aware_gp_comparison.csv       # Stage 3A 실행 후, 동일 검증점별 A/B 오차
  validity_aware_gp_summary.json         # Stage 3A 실행 후 지표별 MAE/RMSE/coverage
  stage3b_settling_unit_comparison.csv   # Stage 3B 실행 후 설계점별 B/C 결과
  stage3b_settling_unit_summary.json     # Stage 3B 실행 후 단위/분산경고/차이 검증
  ...                         # Stage 2/3 metric-wise prediction/error (추후 정의)
figures/
  ...                         # Stage 2/3 예측 vs 실측 및 오차 시각화
```

EXP-005에는 **새로운 SPICE 관측값이 없으므로** 이전 실험의 `design_points.csv`와 `corner_metrics.csv`를 중복 저장하지 않는다. 원본 데이터는 EXP-003에 남겨 추적한다.

## 07. Discussion

**Observation:** Stage 2에서 PM/Settling 큰 예측 오차를 확인했다. Stage 2b에서 일부 settling이 **실제 시간 대신 무차원 오차**임을 확인했다. Stage 3A에서 B의 PM/Settling 오차는 줄고 UGBW 오차는 커졌다. Settling B에 음수 분산 경고와 10 µs 표준편차의 18/19 반복이 나타났다.

**Interpretation:** 일부 settling label은 무차원 fallback을 실제 시간처럼 저장한 것임을 코드와 시뮬레이션 길이의 불일치로 확인했다. 이는 GP 학습 타깃의 의미 혼합이다. 다만 이것만으로 모든 PM/UGBW 오차나 GP 학습 불안정의 원인이 확정되지는 않는다.

**Research implication:** 성능값 정제만으로 모든 metric이 좋아지는 것은 아니다. **실패 여부(flag)와 유효한 실수형 성능 레이블을 분리**하되, uncertainty-aware candidate selection 전에 GP의 posterior 분산 수치 안정성부터 확인해야 한다.

## 08. Limitations & Issues

- D040~D059는 EXP-003의 **adaptive search로 선택된 샘플**이며 독립 무작위 추출 표본이 아니다. 따라서 단일 holdout 통계는 제한된 탐색 궤적에 대한 진단 결과다.
- Stage 2 fit에서 캡처된 MLL 실패/fallback 메시지는 없었다. 수치 최적화의 완전한 품질을 보장하는 것은 아니다.
- 원본 7개 settling 값이 401 µs 파형으로 측정 가능한 시간이 아님을 확인했다. 해당 raw 숫자는 삭제하지 않는다. 이외 설계점은 waveform이 없어 settling 유효성을 확정하지 못한다.
- 처음 60개의 모든 데이터가 학습에 충분한 공간 커버리지를 제공한다고 가정하지 않는다.
- GP B의 `Negative variance` 경고와 18/19 동일한 분산 하한 의심으로 settling uncertainty calibration 판단 보류.
- Stage 3A 유효성 평가도 **D047만 확실하게 제외한 19개 임시 holdout**에 대한 결론이다. 선택 편향·단일 seed·소표본 한계가 있다.
- 로컬 Stage 2 summary와 Stage 2b audit/flag 파일 자체의 GitHub 반영은 아직 완료되지 않았다. 업로드된 Stage 2/3A 파일의 byte-preserved SHA256은 archive README에 남겼다.
- TT-only의 GP 신뢰성은 17-corner robust feasibility 또는 feasible island persistence의 증거가 아니다.

## 09. Conclusion & Next Experiment

**현재 부분 결론:** Stage 1/2/2b/3A까지 실제 실행했다. 학습 label validity 문제가 코드와 원본 실측 비교로 밝혀졌고, 확인된 fallback을 제외하자 PM·Settling의 MAE는 줄었지만 UGBW는 증가했다. Settling GP B의 posterior 분산 경고 때문에 uncertainty calibration은 미검증이다. **GP B를 곧바로 ATLAS에 적용하거나 연구 가설을 입증했다고 결론 내리지 않는다.** Stage 3B는 **계획이며 실행·결과 없음**.

**후속 EXP-006 (조건부):** EXP-005에서 데이터 부족이 병목이라고 판단되면 GP 예측 불확실성 및 near-feasible 영역을 고려하여 신규 TT 설계점의 평가 예산과 위치를 설계한다.
