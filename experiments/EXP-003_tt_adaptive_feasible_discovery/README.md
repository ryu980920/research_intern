# EXP-003 — ATLAS TT Adaptive Feasible Discovery

_설계/문서화: 2026-10-09_  
_상태: 실행 전 (Planned / Ready for preflight)_  
_역할: 본격적인 Cross-PVT Feasible-Island 연구를 위한 **feasible-region discovery pilot**_

## 1. Background — 왜 EXP-003을 하는가?

장기 연구 질문은 **Cross-PVT Persistent Feasible-Island Modeling for Robust Analog Sizing**이다.

> 설계 파라미터가 같더라도 PVT corner에 따라 feasible 영역의 위치·크기·연결성이 달라질 수 있다. 기존 ATLAS의 metric-wise worst-case 압축이 이런 corner-wise 구조 정보를 제거할 때, 그 정보를 따로 보존·활용하면 robust design 탐색을 더 효율적으로 할 수 있는가?

기존 EXP-001/002 결과:

- 설계 변수: transistor width 6개 + compensation capacitor 1개 = **7차원 설계공간**
- EXP-001 D000: 17 PVT corners 평가, feasible **0/17**
- EXP-002 D001–D019: 19 designs × 17 corners = 323 evaluations
- 전체 통합: **20 designs × 17 corners = 340 corner evaluations**
- 총 feasible corner evaluation: **0/340**
- TT에서도 20 designs 모두 infeasible
- D000, D007, D008, D009는 TT에서 **6개 spec 중 phase margin만 실패**
- 반면 PM이 높은 일부 designs는 gain/UGBW/output swing이 부족
- metric별 worst corner가 서로 달라 worst-case 압축 결과가 단일 실제 physical corner와 일치하지 않을 수 있음을 관찰

**Observation:** 지금 표본에서는 TT 및 다른 PVT corner에서 feasible point가 없다.

**Interpretation:** 현재 점들로는 feasible 영역의 경계나 연결 구조를 관찰할 수 없다. 이는 설계공간 전체에 feasible solution이 없다는 증거가 아니라, 선택한 초기 20점에서 못 찾았다는 뜻이다.

**Research implication:** 바로 100개 design × 17 corners를 추가로 평가하기보다, 학습을 이용해 feasible 또는 경계 부근을 먼저 찾는 것이 합리적인 다음 단계다.

## 2. 이번 실험의 정확한 목표와 범위

**1차 목표:** ATLAS가 초기 20개 TT-infeasible 관측치를 바탕으로 adaptive candidate를 제안하고, 제한된 추가 TT 평가 안에서 **6개 조건을 동시에 만족하는 첫 TT feasible design**을 찾는지 확인한다.

**2차 목표:** 아직 feasible을 못 찾더라도, 후보를 고를수록 전체 constraint 위반 정도가 실제로 줄어드는지 관찰한다.

이 실험은 **ATLAS 자체의 최종 성능 평가도, island topology의 입증도, PVT robust design의 검증도 아니다.** 후속 실험의 시작점을 확보하는 예비 실험이다.

이번 실험에서 **하지 않는 것**:

- 17-corner PVT sweep
- 첫 점 주변의 면적/경계 확정
- TT feasible island가 하나인지 여러 개인지 판정
- Cross-PVT persistence의 수치화
- 기존 ATLAS 대비 새 방법의 우월성 주장

특히 **TT feasible point 한 개 ≠ TT feasible island 전체**이다. 한 점만으로 연결 영역의 개수·크기·경계는 알 수 없다.

## 3. Research Questions / Working Hypotheses

### RQ1 — Feasible discovery

초기 D000–D019가 모두 infeasible할 때, ATLAS가 GP 기반 adaptive 탐색으로 실제 TT feasible design을 찾을 수 있는가?

- **H1 (검증할 가설):** adaptive 탐색은 임의의 초기 점들만 평가했을 때보다 joint constraint 위반이 작은 후보를 발견할 수 있다.
- 이 실험에는 별도의 Random/other BO 대조군이 없으므로 **다른 방법보다 우수하다는 결론은 내릴 수 없다.**

### RQ2 — Joint trade-off

D020 이후 gain, UGBW, PM, swing 등을 **같은 design에서 동시에** 개선하는가, 아니면 한 spec의 향상이 다른 spec을 악화시키는가?

초기 데이터에서 일부 design은 PM만 실패하고, 다른 design은 PM이 좋아도 다른 여러 spec을 실패한다. 이 trade-off가 실제 adaptive trajectory에서 어떻게 나타나는지 본다.

### RQ3 — Search behavior

모델이 예측한 near-feasible set과 Mapper topology 관련 지표가 변화할 때, 실제 SPICE 기반 constraint margin도 개선되는가?

주의: `F_hat`과 `beta0`는 모델이 예측한 후보 구조를 나타내는 값이며, **실제로 측정한 feasible island의 개수는 아니다.**

## 4. 개념 정의 (용어 혼동 방지)

| 용어 | 이 실험에서의 의미 |
| --- | --- |
| Design point \(x\) | 7개 설계 파라미터를 한 번에 지정한 조합 |
| TT evaluation 1회 | 한 design point를 TT 3.3 V, 27 °C에서 SPICE로 평가해 6개 metric 확보 |
| `budget` | 실제 design 평가 횟수의 상한. **돈이나 GP 예측 후보 수가 아님** |
| `n_init` | GP 학습을 위한 최초 실제 평가 점 개수 |
| Adaptive evaluation | 이전 실제 평가값을 학습해 ATLAS가 선택한 새로운 점을 SPICE로 평가 |
| Feasible | **하나의 design이 6개 조건을 동시에** 통과 |
| Near-feasible (분석용) | 정규화된 constraint margin 등을 이용해 target에 얼마나 가까운지 보는 정도. 아직 threshold로 이산 분류하지 않음 |
| Feasible Island | 설계공간에서 서로 연결된 feasible 점들의 **영역**. 한 feasible 점과 다름 |
| Robust feasible | **동일한 design point**가 TT를 포함한 17 PVT corners에서 모두 feasible |

하나의 TT evaluation에서 ngspice는 AC/DC/DC-sweep/transient 등의 여러 분석을 수행할 수 있다. 따라서 `budget=60`은 ngspice의 내부 분석 명령이나 SPICE subprocess 총합을 뜻하지 않고, **최대 60개 design point의 TT 성능 평가**를 뜻한다.

## 5. 회로와 실험 조건

### Circuit / design variables

- Circuit: GF180 two-stage op-amp
- 평가 corner: **TT / 3.3 V / 27 °C**
- 평가 형태: TT-only, `CircuitEvaluator(..., pvt=False)`
- 설계 변수 7개: `wp1, wn1, wp3, wn3, wn4, wn5, cc`
- `wp*`, `wn*`: transistor width; `cc`: compensation capacitor
- Bounds: width 0.5–100 µm, `cc` 0.1–10 pF (정확한 config는 `config/run_config.md` 참조)
- 다른 netlist/PDK 및 bias 조건은 기존 YAML과 netlist에 고정

### Specifications — 6개를 모두 만족해야 feasible

| Metric | 의미 | Target | 근거가 되는 분석 |
| --- | --- | --- | --- |
| Gain | 증폭 이득 | ≥ 300 | DC sweep 결과에서 추출 |
| UGBW | unity-gain bandwidth | ≥ 20 MHz | AC frequency response |
| Phase Margin (PM) | 피드백 안정성 관련 여유 | ≥ 60° | AC frequency response |
| Bias Current | 바이어스 전류 | ≤ 1 mA | DC operating point |
| Settling Time | 출력이 최종값에 안정되는 시간 | ≤ 6 µs | Transient |
| Output Swing | 출력이 움직일 수 있는 범위 관련 metric | ≥ 0.3 V | DC sweep 기반 추출 |

위 각 항목을 **서로 다른 design에서 하나씩 통과**하는 것으로는 feasible이 되지 않는다. 같은 \(x\)에 대해 6개가 동시에 통과해야 한다.

### Reproducibility

- ATLAS commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- GF180 PDK commit: `9f992d5a9186d1f7820c58f039c484ad35b2edea`
- 기존 baseline simulator: ngspice 44.2
- Python: 3.10.22 / conda env `atlas`
- GF180 global statistical variation = OFF
- GF180 mismatch statistical variation = OFF

```spice
sw_stat_global = 0
sw_stat_mismatch = 0
```

같은 design x + 같은 TT corner에서 **MC 랜덤 샘플이 달라져 metric이 바뀌는 문제**를 피하려는 설정이다. EXP-003에서 Monte Carlo를 수행하는 것은 아니다.

## 6. 왜 budget=60, n_init=20인가?

실제 `run_experiment.py`는 initial sample 수를 다음과 같이 계산한다.

```python
n_init = max(min(3 * n_params, budget // 3, 50), 10)
```

이 식은 초기 표본 수를 parameter 수와 전체 평가 예산에 맞추는 **알고리즘의 휴리스틱 설정**이지, 회로의 물리 법칙이 아니다.

현재:

```text
n_params = 7
budget = 60

3 × 7 = 21
60 // 3 = 20
n_init = max(min(21, 20, 50), 10) = 20
```

따라서:

```text
D000–D019 : 20 initial design evaluations
D020–D059 : 최대 40 adaptive design evaluations
전체 상한 : 60 TT evaluations
```

- **20개:** EXP-002의 `TopoBO.optimize(n_init=20, seed=42)` initial-set 정의와 맞추기 위해
- **40개:** 일단 어디까지 adaptive 탐색이 가는지 관찰하기 위한 제한된 추가 평가 횟수
- **60회:** 20개 initial + 최대 40개 adaptive가 되도록 정한 pilot budget이지 최적값으로 증명된 숫자가 아님
- **Early stop:** 첫 feasible 점 발견 시 더 이상 평가하지 않음. feasible이 없으면 예산 소진 시 종료

참고: 큰 budget에서는 standard runner가 `n_init=21`을 사용할 수 있다. EXP-002는 **optimizer-default 20-point pilot**이며 모든 ATLAS run의 초기값이 20으로 고정된 것은 아니다.

**중요한 실행 특성:** 현재 script는 EXP-002 CSV를 그대로 surrogate에 넣는 warm start가 아니다. D000–D019를 **TT에서 다시 실제 평가**한 뒤 D020부터 적응형 탐색한다. 같은 설정인지 확인하기 위해 초기 TT 결과를 EXP-002와 비교해야 하며, 계산비용 측면에서도 이 재평가 20회가 budget에 포함된다.

## 7. ATLAS가 D020을 고르는 과정

```text
D000–D019 parameter + 실제 TT metric
                 ↓
GP surrogate 학습 (설계 변수 → 각 성능의 예측)
                 ↓
50,000개 후보 x 생성 (아직 SPICE 실행 X)
                 ↓
현재 feasible sample 없음 → 대략 global LHS 40,000 + local 10,000
                 ↓
예측 성능·제약 만족 가능성 계산
                 ↓
예측상 near-feasible한 후보 집합 F_hat 구성
                 ↓
Mapper로 F_hat의 연결 영역/bridge/frontier 구조 근사
                 ↓
wEI와 topology 항을 결합한 acquisition score
                 ↓
점수가 가장 높은 후보 **1개** 선택
                 ↓
D020만 실제 TT SPICE 평가 → 결과 추가
                 ↓
GP 재학습 → D021 선택 → 반복
```

- **GP surrogate:** 모든 후보를 SPICE로 돌리지 않고 성능을 예측하는 대리 모델
- **Acquisition:** 다음 SPICE 평가에 어떤 후보를 쓸지 순위를 매기는 규칙
- **Global LHS:** 넓은 설계공간을 살피는 후보
- **Local sampling:** 현재까지 가능성이 높았던 점 주변 후보
- **Mapper:** 모델의 예측 가능 영역이 하나인지 여러 영역인지 등의 형태를 근사하는 도구
- **`F_hat`:** 실제 측정된 island가 아니라, 모델이 예측한 near-feasible 후보 집합
- **50,000 candidates:** 예측용 후보 수. **50,000회 SPICE simulation이 아니다.**

현재 ATLAS에는 feasible 점이 없는 동안 surrogate의 **작업용 constraint를 일시적으로 완화**하는 로직도 있다. 하지만 실제 feasible 판정은 언제나 원래 target spec으로 한다. 완화된 목표를 통과했다고 실제 feasible로 기록하면 안 된다.

본 실험은 `surrogate='gp'`를 고정한다. 표준 runner의 `auto`는 학습 시간이 길어지면 NN으로 전환할 수 있으므로, machine speed에 따른 전환을 피하고 동일 모델 기반 trajectory를 기록하려는 선택이다.

## 8. Procedure — 무엇을, 왜 확인하는가?

| 단계 | 작업 | 확인 목적 | 확인 후 판단 |
| --- | --- | --- | --- |
| Preflight | ATLAS commit, PDK/MC switch, Python/ngspice 확인 | 환경 차이가 결과에 섞이는지 방지 | 불일치 시 실행 보류 |
| Initial | D000–D019 TT 재평가 | 동일 출발 데이터로 GP 학습 | 기존 EXP-002의 TT metric/parameter와 비교 |
| Adaptive | D020–D059 중 가능한 횟수만큼 선택·TT 평가 | 실제 joint-feasible 방향으로 움직이는가 | iteration별 margin/trade-off 분석 |
| Stop | first feasible 또는 60회 소진 | 발견 성공 및 비용 기록 | 다음 실험 분기 |
| Save | trajectory와 run logs 저장 | 코드를 재실행하지 않고 연구 결과 추적 | 데이터 무결성 점검 |
| Analyze | margin/metric/parameter trajectory 비교 | 어떤 spec을 개선하며 움직였는지 이해 | 후보 선정 및 다음 가설 |

실제 실행 script: `scripts/run_adaptive_tt_search.py`

**실행 전에 확인할 것:** script가 참조하는 로컬 GF180 모델 경로, active statistical switches, ngspice executable과 기존 EXP-002의 설정이 실제 PC와 맞는지. 버전·경로·MC 설정이 다르면 결과 비교를 중단하고 먼저 원인을 해결한다.

## 9. Numerical metrics — 단순 feasible 여부 이상으로 보는 값

각 iteration \(t\)에서 \(x_t\)의 6개 실제 성능을 얻는다.

### Feasibility

```text
feasible = 모든 6개 original target specs를 동시에 만족
n_specs_passed = 6개 중 통과한 spec 개수
```

`5/6`을 만족해도 마지막 하나가 target에서 아주 멀 수 있으므로, `n_specs_passed`만으로 “거의 feasible”이라고 결론 내리지 않는다.

### Normalized constraint margin

각 spec의 방향에 따라:

```text
minimum constraint (gain, UGBW, PM, swing):
    margin = (measured - target) / target

maximum constraint (ibias, settling):
    margin = (target - measured) / target
```

예: PM=45°이고 target=60°이면 `(45-60)/60 = -0.25`로, 25% 부족하다.

- margin > 0: 해당 spec 통과 여유
- margin = 0: 경계
- margin < 0: 해당 spec 위반

```text
worst_margin     = min(6개 spec margins)
total_violation  = sum(max(0, -margin) for each spec)
```

- `worst_margin >= 0`이면 수학적으로 모든 spec을 통과
- `worst_margin` 상승: 가장 불리한 spec의 상대 여유 개선 가능성
- `total_violation` 감소: 모든 실패 항목을 합친 위반량 감소

두 지표를 함께 보면 한 성능만 크게 향상되는 현상을 구분할 수 있다. 계산 불능/penalty/sentinel metric은 물리적 측정값으로 단정하지 않고 별도 진단해야 한다.

### ATLAS 내부 진단값

`iterations.jsonl` 등에서 얻을 수 있는 `beta0`, `n_F_hat`, `lambda_t`, fit/simulation time도 참고한다.

이는 탐색 내부 상태를 보여줄 뿐 **실제 feasible component 개수를 입증하지 않는다.**

## 10. 저장 데이터와 필요한 그래프

### Primary/derived data

실행 **후** 생성될 파일(현재 결과 없음):

```text
data/
├── trajectory.csv
└── run_summary.json

raw/
└── atlas_logs/
    └── <run_id>/
        ├── config.json
        ├── iterations.jsonl
        ├── progress.log
        └── results.json
```

`trajectory.csv` columns:

```text
iteration, design_id, phase,
wp1, wn1, wp3, wn3, wn4, wn5, cc,
gain_min, ibias_max, phm_min, t_settle_max, ugbw_min, vswing_min,
feasible, n_specs_passed, worst_margin, total_violation
```

원본 ATLAS `iterations.jsonl`만으로는 7개 설계 파라미터 전체를 복원할 수 없기 때문에, 연구 script는 **TT 평가 1회가 완료될 때마다** `CircuitEvaluator.evaluate()`의 실제 결과와 그때 사용된 7개 유효 파라미터(clip/round 적용)를 `trajectory.csv` 한 행으로 기록한다.

### Incremental CSV preservation (2026-10-09 변경)

- Python 실행 시 `data/trajectory.csv`를 새로 생성하고 header를 먼저 기록한다.
- D000 평가 완료 → `D000` 행 추가 → `flush + fsync`로 디스크 기록
- D001 평가 완료 → `D001` 행 추가 → 디스크 기록
- 이후 D020+도 동일하게 한 행씩 기록한다.
- 따라서 최적화 중 프로그램이 오류로 중단돼도 **이미 끝난 평가 행은 파일에 보존**된다. 단, 실행 중이던 미완료 평가 결과는 기록되지 않는다.
- 같은 경로에 기존 CSV가 있으면 **덮어쓰지 않고 실행을 중단**한다. 새 실행 전에는 이전 파일을 보존·이름 변경하거나 run directory를 따로 계획한다.
- 원래 GP optimizer 자체의 학습·후보 선택 동작은 변경하지 않는다.
- 성공적으로 종료하면 별도로 `data/run_summary.json`이 생성된다. 실패로 중단한 경우 summary는 만들어지지 않을 수 있다.
- **주의:** 중단된 run의 CSV를 보존할 수 있지만, 이것이 곧 **ATLAS optimizer state의 자동 재시작(resume)** 기능을 제공하는 것은 아니다.

`trajectory.csv`는 향후 비교·분석용 핵심 dataset이며, completion 후 `ExperimentLogger.history_X`만으로 새로 생성하는 방식은 사용하지 않는다.

실행 완료 후 다음 **그림을 분석 코드와 원본 CSV를 연결해 생성**한다. 현재 그림 파일이 생성됐다는 뜻은 아니다.

| Figure (계획) | 가로축 / 세로축 | 왜 필요한가? |
| --- | --- | --- |
| Worst-margin trajectory | iteration / worst_margin | 최악 constraint가 개선되며 0 경계를 넘는지 확인 |
| Total-violation trajectory | iteration / total_violation | 6개 spec을 종합한 위반량이 감소하는지 확인 |
| Per-spec normalized margins | iteration / spec별 margin (target=0) | PM 개선이 gain/UGBW 손실을 동반하는 등 trade-off 진단 |
| Parameters vs iteration (선택) | iteration / 각 parameter | ATLAS가 실제로 어느 설계 변수를 바꾸는지 확인 |
| ATLAS diagnostic trend (선택) | iteration / beta0, n_F_hat 등 | 모델 예측 구조와 실제 성능 향상 간 차이 탐색 |

TT의 여러 feasible component를 시각화하는 2D 투영 그래프는 후속 연구에서 만들며, **2D상 분리돼 보인다고 7D에서도 분리됐다는 증거는 아니다.**

### Terminal result visibility (2026-10-09 추가)

향후 실행에서 **각 design의 TT 평가 결과가 끝날 때마다** 다음 내용을 출력한다.

```text
[TT RESULT] D020 | TT_FEASIBLE=False | PASS=5/6 | WORST_MARGIN=-0.370
[CSV] Saved D020 -> .../data/trajectory.csv
```

- `TT_FEASIBLE`: 해당 설계점의 **실제 TT** 6개 spec 동시 충족 여부
- `PASS`: 6개 성능 목표 중 충족한 개수
- `WORST_MARGIN`: 가장 불리한 normalized margin. `0` 이상이어야 6개 모두 충족한다.
- 이 메시지는 `trajectory.csv`에 평가 row가 성공적으로 기록된 이후 출력한다.
- `[INIT] INFEAS` 및 `[ITER] INFEAS`는 ATLAS 원본 logger가 출력하는 메시지이고, `[TT RESULT]`는 EXP-003 연구 스크립트가 추가한 **명시적인 조건별 판정 출력**이다.
- **이미 실행 중인 EXP-003 process에는 이번 수정이 실시간 반영되지 않는다.** 실험을 완료한 뒤 저장된 `trajectory.csv`에서 동일한 `feasible`, `n_specs_passed`, `worst_margin` 값을 확인할 수 있다.

향후 모든 새로운 Experiment에 적용할 공통 원칙은 `experiments/README.md`의 `Experiment Terminal Output Convention`에 정의한다.

## 11. 결과에 따른 해석 / 다음 판단

### Case A — 최초 TT feasible 발견

- **Observation:** first feasible iteration과 7개 parameter, 6개 TT metrics 기록
- **Interpretation:** 적어도 하나의 TT feasible design이 존재하며 이번 탐색이 그 점에 도달했다
- **Research implication:** feasible-region 주변을 측정할 출발점 확보
- **Next:** 다른 TT feasible island가 존재할 가능성을 고려한 탐색·경계 지도화 후, 여러 대표 후보의 17-corner 평가

주의: early stop 때문에 **첫 점 외의 다른 island 존재/부재는 판단 불가**.

### Case B — feasible 0, worst_margin/violation 개선

- **Observation:** target 전부는 미달하지만 실제 joint violation 개선
- **Interpretation:** 방향은 개선됐으나 아직 threshold 도달 전
- **Next:** 개선 추세·후보 다양성을 보고 budget 확대, warm-start 확장 또는 탐색 설정 변경을 별도 실험으로 결정

### Case C — feasible 0, 개선 정체

- **Observation:** 가장 나쁜 margin이 정체하거나 특정 spec을 계속 위반
- **Interpretation:** 탐색법, parameter bounds, spec trade-off, 지표 계산 오류 중 원인 미확정
- **Next:** GP 예측과 실제 값 비교, 페널티 metric/파형 검증, 다른 seed 또는 탐색 방식과 비교

어느 경우에도 **단 60회 결과만으로 설계공간 전체의 feasible island 존재/부재 또는 ATLAS의 우월성은 결론 내리지 않는다.**

## 12. Limitation / Risk

1. 최초 feasible 발견 시 종료하므로 **다중 Island 탐색을 수행하지 않음**.
2. 20 initial points를 기존 CSV에서 warm-start하지 않고 TT로 다시 시뮬레이션함.
3. 전체 budget 60은 논문용 수렴성 검증이 아닌 pilot.
4. `F_hat` / Mapper `beta0`는 **surrogate-predicted structure**; 측정 기반 ground-truth component 아님.
5. 회로는 7차원이다. 2개 변수를 축으로 표시한 그림만으로 연결성 판단 불가.
6. Corner-wise persistence를 평가하려면 같은 parameter point 집합을 여러 corner에 적용해야 함.
7. TT feasible은 17-corner robust feasible의 **필요조건이지 충분조건이 아님**.
8. 이상하게 작은 gain, UGBW placeholder, 특이 PM 등은 먼저 추출 코드/operating point/waveform을 확인해야 함.

## 13. Next Experiments — 다른 Feasible Island 가능성 포함

EXP-003 이후의 정확한 실험 번호와 예산은 **결과를 보고 결정**한다.

### Follow-up A — TT Multi-Island Discovery

**Research Question:** TT 설계공간에서 feasible 영역이 하나가 아니라 **서로 분리된 두 개 이상** 존재하는가?

첫 feasible point 주변만 관찰하면 다른 Island B를 놓칠 수 있으므로 다음을 검토한다.

1. first feasible 이후에도 탐색을 이어가는 **separate continuation run** (첫 발견에서 멈추는 EXP-003 설정 자체는 보존)
2. 여러 random seed, global/local 탐색 비율 또는 시작점의 변화
3. 첫 island 주변의 boundary 탐색과 **먼 영역에서의 feasible discovery**를 병행
4. 7D parameter bounds를 정규화한 거리/이웃 기준을 정의해 candidate grouping
5. Mapper가 예측한 component와 실제 SPICE feasible samples의 연결 구조를 구분해 검증

**판단:** 여러 군집이 보이더라도 finite sample의 빈 공간만으로 실제 7D disconnected component라고 단정하지 않는다. 필요하면 두 영역 사이 연결 경로를 추가 샘플링해 확인한다.

**산출물 후보:** TT design/metric CSV, normalized-margin distribution, region 후보별 parameter range/representatives, boundary evidence, component-assignment rule.

### Follow-up B — Same-Point 17-Corner PVT Island Comparison

TT에서 찾은 **복수의 영역 A/B/... 및 boundary/대표 점들에 동일한 7개 파라미터 조합**을 사용해 17 corners를 평가한다.

Corner마다 parameter를 다시 최적화하면 같은 위치에서 feasible이 살아남는지 비교할 수 없으므로, 우선 **공통 x 좌표 집합**을 사용한다.

검증 항목:

- 각 `design_id × corner`에 대한 6개 metric과 feasible
- corner에 따른 region의 이동·축소·분리·사라짐에 대한 **측정 기반 근거**
- 각 corner의 feasible set 및 17-corner 교집합
- Island A/B 중 어느 곳에서 robust-feasible point가 더 많이 나타나는가
- boundary 근처가 corner에 따라 어떻게 바뀌는가

**산출물 후보:** `design_points.csv`, `corner_metrics.csv`, corner별 feasibility/normalized margin plot, 동일 위치의 corner 비교.

### Follow-up C — Persistence Modeling and Baseline Comparison

여러 corner에서 동일/대응 가능한 feasible region을 어떻게 **matching**할지와 persistence metric을 어떻게 정의할지 결정한다.

비교는 같은 회로·spec·PVT·seed/예산 규칙에서 수행한다.

- Baseline: ATLAS의 metric-wise worst-case information을 이용하는 방식
- Proposed candidate: corner-wise island/region 정보를 유지해 다음 후보 선택에 반영하는 방식
- 비교 지표: robust feasible discovery rate, 첫 robust-feasible까지의 SPICE 호출/시간, 동일 예산 내 robust design 수, 영역 coverage 등

**중요한 경계:** metric-wise worst-case 압축은 corner identity/geometry 정보를 잃지만, 모든 corner에 대해 정확한 worst metric을 계산했다면 **최종 robust feasibility의 참/거짓 자체는 보존**한다. 우리가 증명할 것은 판정 오류가 아니라, 추가 구조 정보가 **탐색 효율을 개선하는지**다.

## 14. Current Status / Completion Checklist

- [x] EXP-001/002 baseline 결과와 EXP-003 필요성 연결
- [x] budget/n_init/TT-only/early-stop 의미 설명
- [x] 연구 질문, 결과별 판단, 저장 metrics/그래프 정의
- [x] 다중 TT feasible island 탐색 및 cross-PVT 후속 연구 방향 명시
- [ ] 실행환경 preflight 검증
- [ ] TT optimization 실행
- [ ] D000–D019 기존 TT 결과와 비교
- [ ] D020+ trajectory/metrics 확보
- [ ] 관측 기반 Results / Figures / Interpretation / Conclusion 기록
