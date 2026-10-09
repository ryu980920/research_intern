# EXP-006 — ATLAS 공개 코드 기준선 재현 (500-eval, GF180 TSA TT)

**Status:** Prepared; **simulation NOT started** (2026-10-10).  
**Track:** Released-code baseline replication, **NOT exact ICCAD paper-era code reproduction**.  
**Preceding analysis:** [ATLAS 논문 vs EXP-003 재현 조건 감사](../../docs/reproduction/ATLAS_ICCAD2026_vs_EXP003_audit.md).  
**Current active experiment:** EXP-006. [EXP-005](../EXP-005_gp_surrogate_reliability/README.md) is paused after Stage 3B-2.

## Experiment at a Glance

| 질문 | 현재 상태 |
| --- | --- |
| **왜 하는가?** | EXP-003은 60 TT evaluations/초기 20개/seed42 1회였으므로 논문의 500회/초기 21개/10회 성공률과 직접 비교할 수 없다. GP 이상값만으로 ATLAS 알고리즘이 실패했다고 단정하지 않도록 기본 탐색을 재현한다. |
| **무엇을 할 것인가?** | 공개 ATLAS 커밋을 고정해 GF180 TSA에서 budget 500, seed 42, initial 21, GP 고정, TT-only로 **첫 feasible까지** 실행한다. |
| **무엇을 얻을 것인가?** | 모든 eval의 설계 파라미터·TT 6개 실측·feasibility·iteration, ATLAS 원래 구조화 로그, 실행환경 hashes, first-feasible evaluation. |
| **현재 결과** | **아직 SPICE 0회.** 독립 실행 코드와 원본 보존 구조만 준비. |

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

## 05. Metrics & Evaluation Criteria

- `success`: 동일 설계점의 **6개 실제 TT Spec을 모두 통과**했는지.
- `first_feasible_iter`: ATLAS 원본 logger 기준 **0-based** iteration; 재현 요약에는 `first_feasible_evaluation_1based=iter+1`도 저장.
- `total_evaluations_recorded`: 실제 TT evaluator가 평가한 설계 조합의 개수 (최대 500).
- `worst_margin`, `total_violation`: spec 방향에 따라 정규화된 위반 정도. 모든 후보의 개선 추세를 보존.
- `sim_time`, `fit_time`, `tda_time`, `acq_time`: 원래 ATLAS logger 기준 시간. GP 평가시간과 SPICE 평가횟수 혼동 금지.

## 06. Results & Figures

**Not run.** 완료 전 수치/그래프를 생성하거나 기대 결과를 사실처럼 기록하지 않는다.

Run 이후 제안할 그림: 최초 feasible 유무/first-success iteration, worst-margin vs evaluation, PM/UGBW 동시 margin vs iteration, constraint pass-count vs iteration. 각 그림의 원본은 `raw/runs/.../trajectory.csv` 및 `atlas_logs/.../iterations.jsonl`.

## 07. Discussion (Observation → Interpretation → Research Implication)

**현재 Observation:** 설치환경은 공개 코드 baseline 실행에 필요한 핵심 값이 확인됐다. `.spiceinit`은 단일 스레드 명령만 포함한다. **실행 결과는 없음**.

**Interpretation:** EXP-003/60회 실패와 논문/500회 성공 보고는 바로 충돌하는 데이터가 아니다.

**Implication:** 새 GP 수정 전에 정상적인 released-code baseline 결과를 확보해야 Cross-PVT 개선 실험의 대조군을 정의할 수 있다.

## 08. Limitations & Issues

- 현재 공개 코드에는 논문 실험 뒤 수정된 동작이 있다. **Paper-era exact reproduction 별도**.
- 논문의 'random specification targets'와 공개 TSA YAML의 `low==high`를 해결하지 않은 상태. 한 번의 현재 고정타깃 실행만으로 논문 10-run 통계 재현 주장 불가.
- PDK 해시와 ngspice 버전은 **현 환경**에서 확인됨; paper-era hash와 동일하다는 증명은 아니다.
- `set num_threads=1`은 소스 디렉터리의 파일에 있으나 실행 중 ngspice가 읽는지 불명확. 성능/환경 변수로 기록하고 임의로 재설정하지 않는다.
- 사용자 로그에 보이는 untracked `.spiceinit`·CSV 4개는 소스 코드 변경이 아니며 삭제하지 않는다.
- 각 시행은 별도 디렉터리를 사용하나 실행 중 예기치 않은 중단 시 부분 로그만 남을 수 있다. **재시작 시 같은 출력을 덮어쓰지 않는다**.

## 09. Conclusion & Next Experiment

**Status: PREPARED ONLY.** 먼저 preflight만 실행하고 결과를 검토한 뒤 최대 500회 TT 실행을 시작할지 결정한다. 실험 완료 시 1-run 결과를 논문의 TSA 10-run 평균과 **범위/해석 차이를 명시하며** 대조한다. EXP-005의 GP error analysis는 이 기준선이 명확해질 때까지 보류.
