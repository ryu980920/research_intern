# EXP-006 — ATLAS 공개 코드 기준선 재현 (500-eval, GF180 TSA TT)

**Status:** Completed — first feasible at evaluation **293/500** (CSV-confirmed, 2026-10-10). Full ATLAS logs/waveform verification pending.  
**Track:** Released-code baseline replication, **NOT exact ICCAD paper-era code reproduction**.  
**Preceding analysis:** [ATLAS 논문 vs EXP-003 재현 조건 감사](../../docs/reproduction/ATLAS_ICCAD2026_vs_EXP003_audit.md).  
**Record:** EXP-006 single-run completed based on submitted trajectory. [EXP-005](../EXP-005_gp_surrogate_reliability/README.md) remains paused after Stage 3B-2.

## Experiment at a Glance

| 질문 | 현재 상태 |
| --- | --- |
| **왜 하는가?** | EXP-003은 60 TT evaluations/초기 20개/seed42 1회였으므로 논문의 500회/초기 21개/10회 성공률과 직접 비교할 수 없다. GP 이상값만으로 ATLAS 알고리즘이 실패했다고 단정하지 않도록 기본 탐색을 재현한다. |
| **무엇을 할 것인가?** | 공개 ATLAS 커밋을 고정해 GF180 TSA에서 budget 500, seed 42, initial 21, GP 고정, TT-only로 **첫 feasible까지** 실행한다. |
| **무엇을 얻을 것인가?** | 모든 eval의 설계 파라미터·TT 6개 실측·feasibility·iteration, ATLAS 원래 구조화 로그, 실행환경 hashes, first-feasible evaluation. |
| **실제 결과** | **293회 평가(21 init + 272 adaptive)**, D292에서 최초 6/6 동시 통과. Extracted-metric feasible=True, 원본 CSV 검증 완료. |

## 01. Background & Motivation

논문 [ATLAS (ICCAD 2026)](https://arxiv.org/abs/2610.10985)의 TSA Table 3에는 ATLAS **10/10 성공**, 최초 성공까지 **176 ± 101 SPICE evaluations**(성공한 run의 평균±표준편차)가 기록돼 있다. 이는 GP가 개별 metric을 항상 낮은 MAE로 예측한다는 주장이 아니라 **탐색 전체의 실행 성능**이다.

EXP-003은 60회 pilot에서 0/60이고 D050이 5/6 specs를 통과했다. 60회 결과만으로 논문 실패 또는 성공을 판단하지 않는다. 공개 README에는 paper 실험 후 코드 수정이 기록돼 있으므로 이 EXP는 **공개 소스의 재현 baseline**이지 정확한 논문 당시 구현의 재현이라고 주장하지 않는다.

## 02. Research Question & Hypothesis

- **RQ:** 공개 ATLAS 2026-10 고정 소스·GF180 PDK·TT/seed42 기준에서, 최대 500번의 설계점 시뮬레이션 중 6개 목표 Spec을 동시에 만족하는 첫 설계점을 찾는가?
- **H0 (검증 전):** 성공 여부 미확정. 현재로서는 어떤 결과도 예측하거나 보장하지 않는다.
- **Primary metric:** 실제 SPICE 기준 `first_feasible_evaluation_1based`(첫 성공의 **1부터 세는 평가 수**). 실패 시 `None`과 실제 사용한 평가 수를 모두 기록.
- **Secondary:** 실제 평가 수, violation progression, 각 성능 및 iteration, fit/acquisition/TDA/TT simulation 시간.
- **범위 제한:** 이 단일 run은 논문의 **10-run success rate** 자체를 재현하지 않는다. 필요한 경우 비용과 제어변수를 확인한 뒤 10-run을 별도 계획한다.

## 03. Experimental Setup

| 항목 | 설정 |
| --- | --- |
| Circuit | `two_stage_opamp_gf180` (GF180 Two-stage) |
| Design space | Width 6개 (0.5–100 µm), cc 1개 (0.1–10 pF) |
| PVT | **TT only**, 3.3 V / 27 °C, `pvt=False` |
| Original ATLAS | `dd23c5ba7beb598909be593e4a84c81dab92cc69` (**수정 금지**) |
| ngspice | 실측 현재 PATH `/usr/local/bin/ngspice` → 44.2; 실행 전 재확인 |
| PDK | `/home/ryu98/pdks`; `sw_stat_global=0`, `sw_stat_mismatch=0`; [preflight hashes](../../docs/reproduction/ATLAS_ICCAD2026_vs_EXP003_audit.md) |
| Optimization | `ATLAS`/`TopoBO`, `surrogate=gp` 고정, `seed=42` |
| Evaluations | **최대 500 설계점**, 처음 21개(`n_init_for`) 후 adaptive 최대 479개; 첫 feasible 시 조기 종료 |
| Candidate pool | 50,000개 **GP 예측용**, SPICE 50,000회가 아님 |
| Statistical targets | 공개 TSA YAML의 각 고정 spec target, 논문 서술의 'random targets'와 차이 가능 |
| `.spiceinit` | 소스 netlist 폴더에 `set num_threads=1`. **실제 ngspice 실행에서 해당 파일이 읽혔다는 것은 미검증.** 편집·이동하지 않음 |

**목표 Spec:** Gain ≥300, PM ≥60°, UGBW ≥20 MHz, Vswing ≥0.3 V, Ibias ≤1 mA, Tsettle ≤6 µs. 실제 측정 실패 대체값/비물리량과 성공 판정의 관계는 결과 분석 시 별도로 점검한다.

## 04. Method & Procedure

1. **Preflight (현재 수행할 단계):** WSL에서 환경 해시와 pinned commit, PDK 스위치, 현재 PATH ngspice 44.2, tracked 파일 무수정 상태 점검. 기본 스크립트 실행은 **SPICE를 전혀 돌리지 않음**.
2. **Separate explicit authorization (미실행):** 연구자가 승인한 뒤에만 `--execute`로 최대 500개 신규 TT 설계점을 평가. 처음 feasible 발견 시 중지. 기존 D000–D059를 Warm Start로 로드하지 않음.
3. ATLAS의 **기존 `TopoBO.optimize()`**를 그대로 호출. 추가 래퍼는 평가된 파라미터/실측 지표를 CSV에 **기록하기만** 하며 GP, acquisition, 적응형 초기 샘플 생성을 수정하지 않음.
4. 시작 시 별도 `raw/runs/release_B500_S42_<timestamp>/` 생성. 충돌 시 덮어쓰기 금지. `environment_preflight.json`, `trajectory.csv`, `atlas_logs/...`, 중간 SPICE 디렉터리, 완료 후 `data/` 표준 CSV 및 `reproduction_summary.json` 보존.
5. 끝난 후 **실제 1-based FSD**, feasible 6개 스펙, 시간비용, 기존 EXP-003과 조건 차이 분석. 논문 결과와 수치가 다르면 우선 paper-era code/PDK/targets/seed 차이를 재검증.

### 먼저 실행할 안전 점검 명령 (이 명령으로 SPICE는 실행되지 않음)

```bash
cd ~/research_intern
git pull --ff-only
conda activate atlas
python experiments/EXP-006_atlas_release_baseline_reproduction/scripts/run_release_baseline.py
```

`[SAFE] No files changed, no new SPICE` 메시지를 확인하면 됨. **여기서 멈추고 결과를 공유**한다. 전체 500회 실행은 그 뒤 별도 결정.

### GP training-value policy locked before execution

**EXP-006 기준선:** 공개 ATLAS의 결과 추출기가 반환한 `Y_dict`를 수정 없이 GP에 학습시킨다. Settling fallback, UGBW/PM sentinel, `NaN→0` 원본 GP 처리 등 **현재 release의 구현 동작을 그대로 보존**한다. 이는 방법론이 더 좋다는 주장과 무관하며, 배제하면 재현 대상 baseline 자체가 바뀌기 때문이다.

**분리되는 두 검증 질문:** (a) 공개 ATLAS가 원본 처리로 500회 이내 first feasible을 찾는가(이번 EXP), (b) **실패 상태를 인지하는 새 학습 정책**이 같은 SPICE budget에서 탐색을 개선하는가(후속 별도 EXP, 이번 실험 아님).

**결과 해석 주의:** `feasible=True`는 extractor가 반환한 수치를 기반으로 한 기준선 판정이다. 신규 feasible 후보는 phase margin/UGBW crossing 및 transient settling extraction의 **측정 유효성**을 추가로 확인한 뒤 `verified feasible`이라고 부른다. 기존 ATLAS는 별도의 failure flag를 로깅하지 않으므로 기록된 sentinel과 transient horizon 초과로 알 수 있는 일부 경우와 **미확인 값**을 구분하며 실패 비율을 임의로 추정하지 않는다.

**원본 코드 근거:** `topbo/optimizers.py`의 `Y_data` 누적 및 `model.fit(X_data,Y_np)`, `topbo/gp_model.py`의 `y_clean = np.nan_to_num(y, nan=0.0)`. 구체적 결정은 [config/run_config.md](config/run_config.md)의 failure-label policy 참조.

## 05. Metrics & Evaluation Criteria

- `success`: 동일 설계점의 **6개 실제 TT Spec을 모두 통과**했는지.
- `first_feasible_iter`: ATLAS 원본 logger 기준 **0-based** iteration; 재현 요약에는 `first_feasible_evaluation_1based=iter+1`도 저장.
- `total_evaluations_recorded`: 실제 TT evaluator가 평가한 설계 조합의 개수 (최대 500).
- `worst_margin`, `total_violation`: spec 방향에 따라 정규화된 위반 정도. 모든 후보의 개선 추세를 보존.
- `sim_time`, `fit_time`, `tda_time`, `acq_time`: 원래 ATLAS logger 기준 시간. GP 평가시간과 SPICE 평가횟수 혼동 금지.

## 06. Results & Figures

**실행 완료 — 사용자 제공 trajectory CSV에서 검증.** 전체 293개 설계점(0..292), 21 initial 및 272 adaptive, 중복 파라미터 0개, 모든 293개 행의 feasibility/pass-count/worst-margin 독립 재검산 결과 불일치 0개.

Run 이후 제안할 그림: 최초 feasible 유무/first-success iteration, worst-margin vs evaluation, PM/UGBW 동시 margin vs iteration, constraint pass-count vs iteration. 각 그림의 원본은 `raw/runs/.../trajectory.csv` 및 `atlas_logs/.../iterations.jsonl`.

### EXP-006 archived measurements — 2026-10-10

- Original uploaded file: trajectory(1).csv; archived unmodified at [raw/received/2026-10-10_uploaded_trajectory.csv](raw/received/2026-10-10_uploaded_trajectory.csv).
- Machine-readable derived results: [data/analysis/2026-10-10_trajectory_summary.json](data/analysis/2026-10-10_trajectory_summary.json).
- Source SHA-256: 2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34 (71,793 bytes; CRLF preserved).
- 292 infeasible + 1 feasible, D292 is first feasible and last recorded evaluation. Previous closest failing point: D231 PM=59.86999 deg, UGBW=22.15198 MHz, worst_margin=-0.002167.

| Measured metric | Target | D292 extracted result | Status |
| --- | ---: | ---: | --- |
| Gain | >= 300 | 396.72 | PASS |
| Phase margin | >= 60 deg | 62.05571 deg | PASS |
| UGBW | >= 20 MHz | 20.69377 MHz | PASS |
| Bias current | <= 1 mA | 0.859097 mA | PASS |
| Settling time | <= 6 us | 1.77803 us | PASS |
| Output swing | >= 0.3 V | 0.461981 V | PASS |

**D292 design vector:** wp1=2.249 um, wn1=3.433 um, wp3=84.329 um, wn3=9.656 um, wn4=11.757 um, wn5=88.097 um, cc=0.9775 pF. Native CSV stores widths in meters and cc in farads.

**Feasibility:** D292 worst_margin=+0.03426183536833562 (limiting metric PM) and total_violation=0. Pass counts: 1/6=22; 2/6=29; 3/6=57; 4/6=76; 5/6=108; 6/6=1.

**Extractor caveat:** among 293 entries there are 8 PM=-180-deg sentinels, 8 UGBW=1-Hz sentinels, and 11 settling values above the 401-us TT transient window known from EXP-005. Those signal the need to distinguish measured physical values from failed-extraction substitutes. No such easily identified sentinel is present in D292, but its waveform extraction validity is not independently proven.

**Missing primary execution outputs:** User supplied only the trajectory CSV. Original atlas_logs/iterations.jsonl, config.json, results.json, progress.log, environment_preflight.json, reproduction_summary.json, full terminal completion message, and D292 waveforms were not uploaded. Thus complete process exit status and real walltime cannot yet be verified. Do not invent them.

**Plot provenance:** Worst margin vs iteration, per-spec margins, PM-UGBW trade-off and pass-count can be computed later directly from archived raw CSV; no figures generated this session.

## 07. Discussion (Observation → Interpretation → Research Implication)

**Observation:** 공개 ATLAS 원본 반환값과 원래 GP 학습 규칙을 사용해 D292에서 최초 Feasible 판정(293번째 실제 평가)을 얻었다. 293개 설계점의 파라미터/TT metrics를 원본 그대로 보존했다.

**Interpretation:** 이번 한 번의 공개 코드 TT 실행은 최초 Feasible 탐색에 성공했다. EXP-005의 개별 GP 예측 오류가 반드시 ATLAS 전체 탐색 실패를 뜻하는 것은 아니다. 초기 관측 20개였던 EXP-003과 본 실행(21개)의 첫 20개 중 일치하는 것은 13개뿐이므로 동일한 탐색 경로라고 가정할 수 없다.

**Implication:** 추출값 기준 TT Feasible 출발점을 확보했다. 실제 D292의 waveform/성능 추출 유효성 확인이 선행되어야 17-corner PVT robust feasibility나 island topology 후속 연구의 물리적 기준점으로 사용할 수 있다.

## 08. Limitations & Issues

- 현재 공개 코드에는 논문 실험 뒤 수정된 동작이 있다. **Paper-era exact reproduction 별도**.
- 논문의 'random specification targets'와 공개 TSA YAML의 `low==high`를 해결하지 않은 상태. 한 번의 현재 고정타깃 실행만으로 논문 10-run 통계 재현 주장 불가.
- PDK 해시와 ngspice 버전은 **현 환경**에서 확인됨; paper-era hash와 동일하다는 증명은 아니다.
- `set num_threads=1`은 소스 디렉터리의 파일에 있으나 실행 중 ngspice가 읽는지 불명확. 성능/환경 변수로 기록하고 임의로 재설정하지 않는다.
- 사용자 로그에 보이는 untracked `.spiceinit`·CSV 4개는 소스 코드 변경이 아니며 삭제하지 않는다.
- 각 시행은 별도 디렉터리를 사용하나 실행 중 예기치 않은 중단 시 부분 로그만 남을 수 있다. **재시작 시 같은 출력을 덮어쓰지 않는다**.

## 09. Conclusion & Next Experiment

**Status: Completed (raw-CSV confirmed).** 최초 성공 D292 / 실제 293번째 평가, 6/6 통과, worst margin +0.0342618354. **오늘은 추가 시뮬레이션을 시작하지 않고 종료한다.** 원본 제출 범위에 없는 ATLAS 로그와 waveform을 확인한 뒤 이 결과를 물리적으로 검증된 Feasible이라고 표현할지 결정한다. 논문의 10-run mean FSD(176±101)와 직접 통계 비교할 수 없는 단일 실행임을 유지한다.
