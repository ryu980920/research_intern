# CURRENT — Research Status

_Last updated: 2026-10-10_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**EXP-001/002 PVT baseline, EXP-003 TT pilot, EXP-004 warm-start smoke, EXP-006 released-code TT baseline completed (CSV-confirmed). EXP-005 paused.**

지금까지 실제로 확보한 표본:

- **EXP-001:** D000 × 17 PVT = 17 evaluations, feasible 0.
- **EXP-002:** D001~D019 × 17 PVT = 323 evaluations, feasible 0. 이전 D000과 통합하면 **20 designs × 17 corners = 340 evaluations, feasible 0**.
- **EXP-003:** TT-only에서 D000~D019 재평가 + GP adaptive D020~D059 = **60 TT evaluations, feasible 0**. 최선의 near-feasible design은 D050 (PM=54.16°, UGBW=20.33 MHz, PASS 5/6, worst_margin=-0.0973).
- 첨부된 ATLAS `iterations.jsonl` 60행을 검증했다. GP fit_time이 adaptive 40회 모두 기록됐으나 **각 GP MLL fit의 성공과 예측 정확도는 아직 미검증**이다.

**현재 연구 판단 (2026-10-10 종료):** [EXP-006](experiments/EXP-006_atlas_release_baseline_reproduction/README.md)에서 공개 ATLAS의 500회 예산 / 21 초기 / seed42 / GP 고정 / TT-only 실행 결과, **293번째 평가의 D292에서 최초 Feasible(6/6 PASS)**을 찾았다. 원본 CSV 293행을 독립 검산했고 0건 불일치. 이는 **현재 공개 코드의 단일 실행 탐색 성공**이지 논문의 10-run 통계 재현, D292 waveform 물리 검증 또는 17-PVT 강건설계 검증을 의미하지 않는다. [EXP-005](experiments/EXP-005_gp_surrogate_reliability/README.md)는 Stage 3B-2 후 보류를 유지한다. 오늘 추가 SPICE/GP 실행 없음.

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
- [x] EXP-004: Warm Start 60개 cached replay + 신규 D060 TT 평가 1회 성공 (설계 feasible=False)

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

## EXP-004 Warm Start Smoke Result (Completed, 2026-10-10)

- **RQ:** 기존 60개 TT 실측을 재시뮬레이션 없이 GP 학습에 재사용하고 **신규 D060 설계점만** 평가할 수 있는가?
- **결과:** **성공.** EXP-003의 D000–D059 60개 cached replay, 신규 D060 한 점 TT evaluator 실행, CSV와 GP 사전 예측 JSON 저장. 전체 실행 시간 약 16.5 s.
- **D060 실제:** gain 439.52, Ibias 0.6681 mA, PM **38.107°**, settling 1.7633 µs, UGBW 26.312 MHz, swing 0.7744 V. **5/6 조건 통과, worst margin -0.3649, TT feasible=False**.
- **사전 GP 예측:** PM 59.995 ±16.845° (실측 38.107°; 오차 -1.30σ), UGBW 34.050 ±4.203 MHz (실측 26.312 MHz), Ibias 0.5798 ±0.0331 mA (실측 0.6681 mA, +2.66σ). Settling 예측 평균은 -785.8 µs(비물리적), 실측은 1.7633 µs.
- **해석:** Warm Start 기능 검증은 완료되었으나 GP 예측·불확실성 품질은 표본 1개로 입증할 수 없다. 음수 Settling 예측은 추가 조사 필요.
- **기록:** [EXP-004 README](experiments/EXP-004_warm_start_smoke_test/README.md), [설계점](experiments/EXP-004_warm_start_smoke_test/data/design_points.csv), [실측 성능](experiments/EXP-004_warm_start_smoke_test/data/corner_metrics.csv), [GP 예측/관측](experiments/EXP-004_warm_start_smoke_test/raw/prediction_D060.json).
- **EXP-005:** 신규 평가 예산을 늘릴 때 모든 신규 후보의 사전 GP 평균/표준편차와 실제 SPICE 성능을 함께 보존하고 모델 예측 품질을 점검한다.

## Paper Reproduction Audit (Priority, 2026-10-10)

- **자료:** [ATLAS 논문 §4.1–4.2 / Tables 1–3 및 EXP-003 설정 비교](docs/reproduction/ATLAS_ICCAD2026_vs_EXP003_audit.md).
- **현재 확인한 차이:** 논문 TSA=GF180 7D 6 specs, 500 evaluation/run × 10 runs, initial 3d=21; EXP-003=동일 회로·스펙이나 60 budget × 1 seed, initial 20. 논문 TSA 결과 10/10, 176±101 evaluations; EXP-003 0/60을 즉시 실패로 판정할 수 없음.
- **미해결:** 논문 'random spec targets' 문구와 현재 공개 YAML `low==high`의 차이, 논문 실험 이후 수정된 ATLAS 코드, GF180 PDK model hashes 및 통계 스위치 등 세부 환경.
- **다음:** WSL에서 ATLAS SHA/작업트리, ngspice executable/version, PDK 모델 위치·해시·MC 스위치, YAML targets 확인 → 공개 코드 standard run을 별도 experiment로 할지 결정. **현재 신규 시뮬레이션 0회, 정식 논문 재현 실행 미실행.**

### Environment preflight 실측 결과 (2026-10-10, 신규 SPICE 0회)

- `inspect_atlas_environment.py` 사용자 WSL 실행 완료. **ATLAS HEAD=`dd23c5ba7beb598909be593e4a84c81dab92cc69`**, 현재 PATH `ngspice=/usr/local/bin/ngspice` **44.2**, PDK_ROOT `/home/ryu98/pdks`, GF180 global/mismatch MC 모두 **0**.
- 7D TSA, 6 specs, YAML target ranges 모두 고정, 17 netlists, **n_init60=20/n_init500=21** 확인. ATLAS source tracked files modified 없음.
- 유일한 `warnings=1`: untracked `netlist/.spiceinit` 및 `ac.csv`, `dc.csv`, `dc_sweep.csv`, `tran.csv` 5개 때문. 소스 코드 변경으로 혼동하지 않으며, `.spiceinit`을 **삭제하지 않고 내용 확인**할 것.
- GF180 `design.ngspice`, `sm141064.ngspice`, `smbb000149.ngspice`의 로컬 SHA256 기록 완료. 동일한 로컬 모델 사본들의 해시 일치는 확인, **논문 당시 PDK 모델 해시와의 일치는 여전히 미검증**.
- **다음 할 일:** `cd ~/atlas && git status --short && cat eval_engines/ngspice/ngspice_inputs/netlist/.spiceinit` (읽기만). 그다음 독립 500-eval run 출력/환경 provenance/예산 승인 여부 결정. 상세 수치와 source hashes: [재현성 감사 §7](docs/reproduction/ATLAS_ICCAD2026_vs_EXP003_audit.md).
- **주의:** ngspice 44.2가 **현재** 기본 PATH에서 확인된 것이며 EXP-003 실행 순간 같은 바이너리를 썼다는 확정 증거는 아직 없음. **실제 benchmark/논문 재현은 아직 실행하지 않았다.**

### .spiceinit 확인 및 공개 코드 기준선 준비 (2026-10-10)

- `~/atlas/eval_engines/ngspice/ngspice_inputs/netlist/.spiceinit` 내용 확인: **`set num_threads=1` 한 줄뿐**. 이는 ngspice 스레드 설정. 소자·스펙·파라미터 변경 사항 없음. **ATLAS subprocess가 실제 이 파일을 읽는지는 미확인**(프로세스 cwd=ATLAS root); 파일은 변경하거나 삭제하지 않음.
- **[EXP-006: 공개 ATLAS GF180 TSA TT 기준선 재현](experiments/EXP-006_atlas_release_baseline_reproduction/README.md) — 준비 완료, 실행 전**. ATLAS 고정 SHA, `budget=500`, `n_init=21`, `seed=42`, `surrogate=gp`, early-stop. **공개 release의 1-run baseline이지 논문 당시 정확한 10-run 재현 결과가 아님**.
- 고정 ATLAS `TopoBO.optimize`를 사용하며 설계변수·TT 실측·실패 원본·원래 logger·환경 해시를 독립 보존. 기본 실행은 읽기 전용 검사로, **명시적 `--execute`에서만 신규 SPICE 시작**. 현재 신규 SPICE 0회.
- **지금 바로 할 작업:** `cd ~/research_intern && git pull --ff-only && python experiments/EXP-006_atlas_release_baseline_reproduction/scripts/run_release_baseline.py` (안전한 사전 점검만 실행). 출력 확인 후 실제 최대 500회 실행 여부 별도 판단.
- 점검 근거: [논문 재현 조건 감사 §7.4](docs/reproduction/ATLAS_ICCAD2026_vs_EXP003_audit.md).

## EXP-006 Released ATLAS TT Baseline (Completed from uploaded trajectory, 2026-10-10)

- **목표:** 논문 조건에 가까운 공개 ATLAS 단일 기준선 실험에서 최초 Feasible 회로를 찾는가? **한 번의 실행에서 성공.**
- **설정:** GF180 two-stage, TT/3.3V/27°C, 7D, 6 Specs, fixed public YAML target, seed42, n_init21, GP 고정, budget500, early-stop.
- **실제 결과:** 293 TT 평가 = initial21 + adaptive272; D000–D291은 Feasible=False, **D292 (zero-based iteration292, 293번째 평가)는 최초 True, 6/6**. 나머지 207회 예산은 조기 종료 시 사용하지 않음(원래 전체 terminal exit log는 미제출).
- **D292 metrics:** Gain 396.72; PM 62.0557°; UGBW 20.6938 MHz; Ibias 0.8591 mA; settling 1.77803 µs; swing 0.461981 V; worst_margin +0.0342618 (PM 제한).
- **데이터 무결성:** 293개 설계점 연속/중복 파라미터 0/feasibility & margin 재계산 0 불일치. CRLF 원본 71,793 bytes, SHA256 `2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34`를 GitHub에 직접 보존.
- **원본/가공:** [EXP-006 raw uploaded trajectory](experiments/EXP-006_atlas_release_baseline_reproduction/raw/received/2026-10-10_uploaded_trajectory.csv) / [분석 요약 JSON](experiments/EXP-006_atlas_release_baseline_reproduction/data/analysis/2026-10-10_trajectory_summary.json).
- **주의:** 추출된 성능값으로 PASS를 재검산했지만 **D292의 실제 AC/transient waveform 유효성은 미검증**. 제공된 파일에 `reproduction_summary.json`과 원래 `atlas_logs`가 없으므로 walltime/GP fit 상세, 프로세스 정상 종료 여부는 미확인.
- **논문과 비교:** 논문 TSA 10/10 성공/FSD 176±101 대비, 이번 단일 실행은 FSD293. 코드 시기/타깃 고정 방식 등 차이 때문에 우열이나 논문 전체 재현을 단정하지 않음.
- **다음 날 우선:** 실행원본 로그 연결 → D292 성능 추출 파형 검증 → 다중 seed 및 17-corner/PVT 연구 단계 선택. **오늘은 실험 종료 및 기록만 완료.**

## EXP-005 GP Surrogate Reliability (Paused after Stage 3B-2, 2026-10-10)

- **RQ:** 기존 GP 예측 오차가 data quality·극단값·모델링/fit 문제 중 어디와 연결되는가? 관측값 부족이 실제 병목인가?
- **Stage 1 (WSL 완료):** EXP-003 `raw/trajectory.csv` 60개 점검, 중복 0개, 조사 대상 7개(PM -180° 부근 2, UGBW 1 Hz 2, Settling >600 µs 7). 이때는 원인 미확인이었으며 Stage 2b에서 추출기 의미를 조사했다. `--save` 실행은 미확인.
- **Stage 2 (WSL 실행 완료):** 실제 ATLAS GP를 D000–D039(40개) 학습하고 D040–D059(20개×6 metric=120예측) 검증. PM MAE 28.73°, Settling MAE 53.24 ms(아래의 데이터 단위 혼합 때문에 물리적 시간 오차로 해석 불가), 20개 중 Settling GP 음수 평균 8개. Fit 8.51s, 캡처된 MLL fallback 메시지 없음. **신규 SPICE 0회**. Stage 2 예측 120행 CSV는 GitHub `data/analysis/archive/`에 byte-preserved 업로드 완료.
- **Stage 2b (WSL 완료, 기록 파일 생성):** [diagnose_metric_semantics.py](experiments/EXP-005_gp_surrogate_reliability/scripts/diagnose_metric_semantics.py) 실행됨. 고정 ATLAS `CircuitClass.py`는 unity-crossing 실패 시 UGBW=AC 첫 주파수(1 Hz), PM=-180° 반환; settling 실패 시 **무차원 `d_settle`을 `settlingTime` 필드에 저장**. GF180 TT transient는 401 µs 길이인데 7개(D013/014/015/016/017/023/047)의 `t_settle`은 이를 초과(학습 6/검증 1), AC paired sentinel은 D014/D047. 이 결과를 바탕으로 **확정 대체값 제외 GP B의 A/B 비교**를 진행.
- **Stage 3A (WSL 완료):** [compare_validity_aware_gp.py](experiments/EXP-005_gp_surrogate_reliability/scripts/compare_validity_aware_gp.py)로 GP A(기존 40개 학습) vs GP B(확정 대체값만 제외: PM/UGBW 39개, Settling 34개)를 동일 **19개 홀드아웃**에서 비교. **MAE:** PM 16.8995→14.9638°(개선), UGBW 7.1082→9.8395 MHz(악화), Settling 저장값 8005.33→7.9326 µs 상당(대폭 개선, 유효 시간 MAE로 인증 불가). GP B fitting 3회/5.62 s, 새 SPICE 0회. Settling B에 **GPyTorch 음수분산 보정 경고**가 있었고 표준편차 **18/19가 10 µs**로 동일; 불확실성 신뢰성 미확인. [분석 CSV·JSON](experiments/EXP-005_gp_surrogate_reliability/data/analysis/archive/README.md) 보존.
- **중요:** D040–D059는 adaptive 탐색으로 선택된 데이터이며 iid 일반화 성능을 보장하지 않는다. 기존 Settling MAE는 시간과 무차원 fallback이 섞인 label에 대한 수학적 오차이고, 남은 소형 settling 값도 waveform 없이는 유효성 미확인이다. 이 확인만으로 GP 품질 전체의 원인을 단정하지 않는다.
- **Stage 3B (WSL 실행 완료):** [Stage 3B 스크립트](experiments/EXP-005_gp_surrogate_reliability/scripts/test_settling_gp_unit_stability.py)로 GP B(s)와 C(µs)를 동일 Settling 학습 34개·검증 19개, seed 42, CUDA에서 평가. **B MAE 7.93263 µs / std 10 µs 18·19 / 음수 분산 경고 1건; C MAE 7.72849 µs / std 10 µs 0·19 / 경고 0건**. B의 Stage 3A 대비 예측 평균·std 차이는 **0 µs**로 재현됨. C−B 예측 평균 최대 차이 2.25941 µs, 표준편차 최대 차이 8.951 µs. **신규 SPICE 0회, GP fit 2회 완료.** 원본 데이터의 레이블 유효성과 C의 calibration은 여전히 미검증. Stage 3B CSV/JSON [GitHub archive](experiments/EXP-005_gp_surrogate_reliability/data/analysis/archive/README.md)에 보존. 상세 분석: GP B posterior 95% 근사 구간 18/19 (94.7%), GP C는 13/19 (68.4%). C는 수치 경고 제거에도 구간 포함률이 낮았고 D048/D052/D054/D058/D059가 추가 누락됨. D056은 양쪽 모두 큰 예측 오차. 다음은 측정 유효성 및 GP posterior 분산 계산 경로 확인. [날짜별 기록](logs/2026-10/2026-10-10.md).
- **Stage 3B-2 (계산 경로 진단 준비 당시):** [trace_settling_posterior_variance.py](experiments/EXP-005_gp_surrogate_reliability/scripts/trace_settling_posterior_variance.py)를 추가. **중요한 해석 정정:** GPyTorch `Negative variance` 경고는 진짜 음수뿐 아니라 **양수이지만 min_variance 하한 미만**인 원시 분산에도 발생할 수 있음. double precision의 기본 하한 `1e-10`과 B에서 반복된 10 µs std는 수치상 일치하지만, 실제 원인은 아직 미확인. B는 신뢰 가능한 uncertainty 기준 모델이 아니라 **문제 재현 대조군**. 따라서 B 94.7% vs C 68.4%를 'C 성능 악화'의 결정적 근거로 사용하지 않는다. raw covariance diagonal / posterior variance / min_variance를 같은 34/19에서 기록해 원인을 먼저 판별할 예정. **SPICE 0회, GP 2회 예정, 결과 아직 없음.**
- **Stage 3B-2 (WSL 실행 완료, 2026-10-10):** B(s)/C(µs) 같은 34 train/19 holdout GP를 다시 학습해 **원시 분산과 GPyTorch `min_variance`를 직접 비교**함. gpytorch 1.15.2, torch 2.14.1+cu130. B에서는 raw variance가 하한(`1e-10 s²`) 미만인 점 **18/19**, 원시 음수 **0/19**, 반환 분산이 `max(raw, floor)`와 일치(**True**); C에서는 하한 미만 **0/19**, 음수 **0/19**, 일치(**True**). 둘 다 Stage 3B 저장 예측 mean/std 재현 최대 오차 0 µs. **결론: B의 10 µs std 반복은 분산 하한 보정으로 발생한 사실 확인.** raw 분산이 작아진 근본 원인과 C의 calibrated uncertainty는 미검증. 신 SPICE 0회, GP fit 2회. 원본 CSV/JSON은 로컬 생성 완료, GitHub 업로드 대기. **이제 Stage 4에서 PM 60° 경계 오판 및 PM–UGBW 동시 충족 예측을 분석**하고, 추가 Settling GP 튜닝은 보류.
- **Budget:** 현재 EXP-005에서 **추가 ngspice 설계 평가 0개**. 이후 필요성이 입증될 때 EXP-006에서 별도로 결정.
- **문서:** [EXP-005 README](experiments/EXP-005_gp_surrogate_reliability/README.md), [실험 설정](experiments/EXP-005_gp_surrogate_reliability/config/run_config.md), [2026-10-10 순서별 연구일지](logs/2026-10/2026-10-10.md).

## Current Questions

1. D050은 왜 PM 54.16°에서 목표 60°를 넘지 못하는가? **PM–UGBW trade-off**는 compensation capacitor `cc` 및 width 변화로 해결될 수 있는가?
2. D014/D047의 UGBW 1 Hz·PM -180°는 extractor의 **교차점 미발견 대체값**임을 확인했다. 긴 settling 값 7개도 정상 측정된 실제 시간은 아니다. **남은 수치의 측정 유효성**과 실패 플래그 기록 방법을 어떻게 확인할까?
3. 현재 GP fit은 반복마다 실행됐다. 그러나 **GP MLL fit 성공/예측 정확도**를 어떻게 독립적으로 검증할 것인가?
4. D292의 추출 성능이 실제 AC/Transient 파형에서도 검증되는가? 다른 seed와 더 넓은 탐색은 서로 다른 TT feasible region을 찾는가?
5. 확보한 TT feasible D292 이외에 서로 분리된 다른 island가 존재하는가? 7D에서 연결성을 어떻게 검증할 것인가?
6. 동일한 7D parameter points의 17-corner 평가로 persistence를 정의하고 **동일 SPICE cost/total runtime**에서 robust search 효율을 비교할 수 있는가?

## Next

### Step 1 — D292 TT Feasible의 측정 유효성 검증 (후속, 미실행)

**이유:** EXP-006에서 첫 Feasible을 찾았으므로 'TT feasible 최초 탐색'은 완료됐다. 다음은 그 값이 실제 회로 파형에서 적절히 측정되었는지 확인할 단계다.

- 먼저 실행 때 생성된 환경 스냅샷/ATLAS 원본 로그 및 D292 시뮬레이션 출력의 존재 여부를 확인한다.
- D292 PM unity gain crossing, UGBW, settling-time 파형을 점검하고 extractor의 fallback과 구분한다.
- 필요하다는 근거가 있을 때만 동일 D292 한 점에 대한 TT 재시뮬레이션 계획을 세운다. 오늘은 신규 SPICE를 추가하지 않는다.
- 그 후 다중 seed 통계 재현/TT feasible 지역 탐색/17-corner same-point 검증의 우선순위를 선택한다.

상세: [EXP-006](experiments/EXP-006_atlas_release_baseline_reproduction/README.md).
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
