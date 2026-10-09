# EXP-005 — GP Surrogate Reliability: 실행 조건과 평가 설계

**Status:** Running (Stage 1/2/2b/3A WSL 완료; Stage 3B planned) · **New SPICE evaluations:** **0**

## 1. Dataset & provenance

- **Circuit:** GF180 two-stage op-amp, TT 3.3 V / 27 °C.
- **원본 측정 데이터:** `../EXP-003_tt_adaptive_feasible_discovery/raw/trajectory.csv`의 D000~D059 **60개**, 7개 물리 파라미터와 6개 TT metric. EXP-005에 데이터를 복사하지 않고 소스 참조.
- **별도 참고용 신규 관측:** EXP-004의 D060 / `raw/prediction_D060.json`. D060은 40/20 기본 평가에 넣지 않는다. EXP-004의 GP는 60개 전체로 학습했고, 그 D060은 해당 모델이 선택한 설계안이다.
- **ATLAS baseline:** commit `dd23c5ba7beb598909be593e4a84c81dab92cc69`, `topbo.gp_model.GPSurrogate` / BoTorch `SingleTaskGP`, independent GP per spec, Matérn 5/2 ARD, input Normalize, outcome Standardize, float64.
- **이 단계의 simulator:** 사용하지 않음 (SPICE 0회). 향후 원본 결과 의심 시 별도 진단 실험으로 관리.
- **Baseline reproducibility:** conda `atlas`, repo `~/atlas`, research repo `~/research_intern`. GP 평가 코드에서 seed=42 사용.

## 2. Data audit — Stage 1 (구현됨)

실행 코드: `scripts/audit_tt_dataset.py`. 표준 Python 라이브러리만 사용한다.

### 이상값 판정은 오류 확정이 아님

| Flag | 조건 | 의미 |
| --- | --- | --- |
| `PM_NEAR_MINUS_180_DEG` | PM ≤ -179° | 위상/추출 정의 확인 대상 |
| `UGBW_AT_OR_BELOW_1_HZ` | UGBW ≤ 1 Hz | 측정값 또는 fallback 여부 확인 대상 |
| `SETTLING_ABOVE_100X_SPEC` | Settling > 600 µs (목표 6 µs × 100) | 매우 느린 과도응답 또는 추출 실패 여부 확인 대상 |
| `NONPOSITIVE_SETTLING` | Settling ≤ 0 | 물리 단위·추출 정의 검토 |
| `NEGATIVE_BIAS_CURRENT` | Ibias < 0 A | 부호 규약 또는 추출 오류 확인 |
| `NEGATIVE_SWING` | Swing < 0 V | 정의·추출 오류 확인 |

100배 임계값은 **진단용 휴리스틱**이지 SPICE 오류 판정 기준이 아니다. 회로가 spec을 통과하지 못하는 것 자체는 잘못된 데이터의 증거가 아니다.

기본 실행은 콘솔에 요약만 출력하고 파일을 만들지 않는다.

```bash
cd ~/research_intern
python experiments/EXP-005_gp_surrogate_reliability/scripts/audit_tt_dataset.py
```

기록이 필요하면 결과 확인 후 `--save`를 붙여 `data/analysis/dataset_audit.json`, `anomaly_flags.csv`를 생성한다. 기존 파일은 덮어쓰지 않는다. JSON에 원본 SHA256을 남긴다.

## 3. GP baseline — Stage 2 (WSL 완료)

- **실행 스크립트:** `scripts/evaluate_gp_baseline.py`. 신규 SPICE 호출 없이 실제 ATLAS `GPSurrogate` import, pinned SHA 및 YAML에서 bounds/spec 확인.
- **시간 순서 분할:** train = D000~D039 (40개), holdout = D040~D059 (20개).
- Train 이외 20개 성능을 GP 학습에 넣지 않고 예측 평균·표준편차와 실제 TT 성능을 비교한다.
- Metric마다 MAE, RMSE, empirical interval hit rate (예: predicted mean ± 1.96 × predicted std), normalized residual `(observed - mean)/std`를 계산한다.
- **GP MLL fit fallback** 여부를 확인·기록해 최적화가 완전히 학습됐다는 근거 없이 주장하지 않는다.
- GP 예측은 잠재 함수 posterior를 의미할 수 있으므로 95% interval hit rate를 모집단 신뢰수준으로 단정하지 않는다.
- **출력 파일:** `data/analysis/gp_baseline_holdout_predictions.csv` (20×6=120행) 및 `gp_baseline_holdout_summary.json`(MAE/RMSE/interval/fit status/source SHA). 두 파일은 원본을 덮어쓰지 않는다.
- **실행 명령:** `python experiments/EXP-005_gp_surrogate_reliability/scripts/evaluate_gp_baseline.py`.
- D040~D059는 ATLAS가 앞선 결과를 보며 *adaptive selection*한 표본이다. 따라서 이 holdout 결과는 **탐색 궤적에 대한 시간순 진단**이지 iid 무작위 일반화 정확도는 아니다.
- 검증 세트로 모델 설정을 고르면 최종 성능을 같은 세트에서 편향 없이 평가했다고 주장할 수 없다. 가능하면 rolling-origin/후속 관측에서 확인한다.

## 3b. Extractor semantics — Stage 2b (WSL 진단 실행 완료)

고정된 ATLAS 커밋의 `eval_engines/ngspice/CircuitClass.py`:
- `find_ugbw`: unity-gain crossing 실패 시 `freq[0]` (GF180 TT testbench 시작 1 Hz)
- `find_phm`: 같은 crossing 실패 시 `-180`
- `get_tran_stable_meas`: settle 미발견 시 `settlingTime = d_settle` (무차원 정규화 편차)
- GF180 TT netlist: `tran 1u 4.01e-4` (종료 시각 401 µs). 이보다 큰 `t_settle_max`는 측정 가능한 시간값이 아님

실제 60개 원본에서 time-window 초과: D013, D014, D015, D016, D017, D023, D047 (train 6, holdout 1).
paired AC sentinels: D014, D047 (train 1, holdout 1). 
**주의:** 시간값이 401 µs 이하라는 사실만으로 valid settling이라고 단정할 수 없다.

독립 확인/기록: `python experiments/EXP-005_gp_surrogate_reliability/scripts/diagnose_metric_semantics.py`.
결과 `data/analysis/metric_semantics_audit.json` / `metric_semantics_flags.csv`. 신규 SPICE/GP 0회.

## 4a. Matched A/B evaluation — Stage 3A (WSL 완료)

- Script: `scripts/compare_validity_aware_gp.py`
- GP A: `data/analysis/gp_baseline_holdout_predictions.csv`에서 기존 실제 ATLAS GP 예측값 읽기. Stage-2 JSON 및 원본 SHA 검증.
- GP B: 동일 `topbo.gp_model.GPSurrogate`, 각 metric별 학습셋만 확정 대체값 제외 (PM/UGBW 39, Settling 34). 각 GP 별 seed=42, 7D 입력과 Matérn 5/2 ARD 유지.
- 평가: metric별 확정 무효 D047을 제외한 공통 D040–D059 **19개**; A와 B 모두 같은 설계점에서 MAE/RMSE/근사 95% 구간 포함률 비교. 무효 평가 레이블은 두 모델 모두 채점하지 않음.
- 원본 60개 데이터는 절대 변경하지 않음. 제외된 failure design들은 실패 정보로 계속 보존.
- 주의: 나머지 작은 `t_settle`도 전부 진정한 settling 시간인지는 알 수 없다. 파형 또는 시뮬레이터 출력에 측정 유효성 flag가 없다는 한계 명시.
- 신규 SPICE 0회, 추가 B GP fitting 3회. 출력: `data/analysis/validity_aware_gp_comparison.csv`, `validity_aware_gp_summary.json`.

```bash
cd ~/research_intern
git pull --ff-only
python experiments/EXP-005_gp_surrogate_reliability/scripts/compare_validity_aware_gp.py
```

### Stage 3A 실험 결과 (D047 제외 후 19개 공통 검증)

| 지표 | MAE A | MAE B | RMSE A | RMSE B | 해석 |
| --- | ---: | ---: | ---: | ---: | --- |
| PM (°) | 16.8995 | **14.9638** | 21.8781 | 19.0677 | B 개선 |
| UGBW (MHz) | **7.1082** | 9.8395 | 10.5405 | 15.3291 | B 악화 |
| Settling (µs 상당) | 8005.33 | **7.93263** | 19293.75 | 22.6951 | 수학적 오차 감소, 검증 label 유효성 미완료 |

- Stage 3A GP(B) fitting 3회(5.62 s), 명시적 MLL fallback 메시지 없음.
- B Settling GP에서 GPyTorch `NumericalWarning: Negative variance values detected` 발생. posterior std가 **18/19에서 정확히 1e-5 s (10 µs)**. 라이브러리 분산 하한 보정과 일치하는 수치지만 원인은 미확인.
- B settling 평균 음수 예측 0/19 (A는 8/19). Coverage B 94.7%는 분산 경고가 있어 검증된 uncertainty calibration으로 보지 않음.
- Stage 2 및 Stage 3A 사용자 업로드 결과를 **`data/analysis/archive/`**에 보존(원본 WSL 분석 경로와 `git pull` 충돌 방지), 원본 raw 데이터는 EXP-003에 유지. Provenance: [archive README](../data/analysis/archive/README.md).
- 시간순 연구 기록: [2026-10-10 log](../../../logs/2026-10/2026-10-10.md).

## 4b. Numerical stability — Stage 3B (코드 구현 완료, WSL 실행 대기)
**Prepared executable:** `scripts/test_settling_gp_unit_stability.py`

- 두 모델 B(s) / C(µs) 각각 GP fit 1회씩 수행. 동일 seed=42, X_train=34, X_holdout=19, 같은 `t_settle_max` mask와 Matérn ARD kernel 사용. Stage 3A 저장된 B를 참조해 rerun consistency 점검.
- C의 posterior mean **및 std 모두 1e6으로 나누어** B와 비교(공통 물리적 단위: seconds, 표시 µs).
- 수치 안정성 진단: `NumericalWarning` 포함 경고 목록, 예측 19개의 std==10µs 개수, MAE/RMSE, 음수 예측, posterior interval hit, GP fit fallback, Stage 3A B 재현 오차.
- `gp_model.py` 변경하지 않으며 기존 파일을 덮어쓰지 않음. 결과는 신규 `stage3b_settling_unit_comparison.csv`와 `stage3b_settling_unit_summary.json`에 생성.
- 결과 미실행. 개선 여부·분산 보정 원인 단정 금지.

```bash
cd ~/research_intern
git pull --ff-only
python experiments/EXP-005_gp_surrogate_reliability/scripts/test_settling_gp_unit_stability.py
```


**RQ:** B에서 음수 분산 경고/10 µs std 반복이 초(s) 단위의 작은 타깃 수치 또는 분산 하한 처리에 영향을 받은 것인가?

- GP B vs 동일 34 train/19 holdout의 GP C: 출력 타깃을 **s → µs**로 표현. 같은 커널/seed/유효성 제외 마스크 사용.
- 공통 초(s)로 역변환 후 예측 평균, MAE/RMSE, posterior std, 경고 개수 비교.
- `Standardize`는 이상적 조건에서 선형 단위 변화에 불변이어야 하므로 실제 차이가 있다면 numerical implementation/hard floor 영향 가설을 검증.
- **아직 코드 실행하지 않았고, 결과도 없다.**

## 4. Candidate improvements — Stage 3C 이후 (미실행)

A. **Baseline:** 현재 GP 그대로.

B. **Validity-aware Settling 비교:** fallback으로 확인된 설계점을 training/holdout regression MAE에서 구분하고, 동일한 확인 가능한 data split의 raw GP와 `log10(t_settle_max)` GP를 비교. 여전히 waveform 없는 남은 행은 valid가 보장되지 않음. 단순 로그 변환으로 단위 혼합 문제를 해결했다고 주장하지 않음.

C. **Local fit (optional):** D050 중심 영역 또는 TT 관심 영역 모델은 표본 수/영역 정의가 충분한지 확인한 뒤 검토한다. 작은 학습 집합은 과적합 위험이 있으므로 임의로 개선이라 단정하지 않는다.

**Comparison principle:** 같은 train/test 설계점, 동일 metric/단위, 동일 실험 조건으로 모델 비교. 데이터 전처리와 output transform 이외의 차이도 명시.

## 5. Decision & artifacts

- **Model choice:** holdout predictive error, interval hit rate, MLL fit failures, 비물리적 예측, 실행시간을 보고 판단.
- **Added SPICE budget:** **0 (현재 범위)**. 데이터 부족이라고 판단되는 근거가 확보된 이후 별도 EXP-006에서 샘플 수/위치를 결정한다.
- **Output policy:** EXP-005에는 새 SPICE 관측값이 없으므로 표준 `data/design_points.csv`/`corner_metrics.csv`를 복제하지 않는다. 분석 산출물은 `data/analysis/`에 저장하고 원본 데이터와 실행 코드/설정을 링크한다.
- **Experiment README:** [../README.md](../README.md)
