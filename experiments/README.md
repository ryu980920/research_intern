# Experiments — Reproducible Research Records

각 `EXP-XXX_...`는 **하나의 명시적인 Research Question → 측정 → 판단**을 남기는 독립 연구 기록이다. `logs/`는 날짜별 작업 기록, `experiments/`는 논리적 실험 단위이다.

## Standard README Structure

**모든 신규 Experiment의 README는 같은 10개 제목을 같은 순서로 사용한다.** 상세 실행 조건은 `config/run_config.md`에, 반복 설명은 공통 정책에 둬서 README 최상단에서 핵심 목적과 실제 결론을 바로 찾도록 한다.

1. `Experiment at a Glance` — **왜 / 무엇 / 발견 / 다음 판단** 4행 요약
2. `01. Background & Motivation` — 이전 EXP의 문제와 실험 필요성
3. `02. Research Question & Hypothesis` — 무엇을 검증하고 어떤 결과를 기대했나
4. `03. Experimental Setup` — 회로, PVT, 버전, budget 등 재현 조건
5. `04. Method & Procedure` — 실제 수행 순서와 선택 이유
6. `05. Metrics & Evaluation Criteria` — spec·단위·성공 판정
7. `06. Results & Figures` — 수치·표·증거 데이터·그림
8. `07. Discussion` — Observation → Interpretation → Research implication
9. `08. Limitations & Issues` — 실패/불확실성/미검증 가설
10. `09. Conclusion & Next Experiment` — 가설 판단, 다음 RQ와 이유

시작할 때 복사할 표준 문서: **[EXPERIMENT_TEMPLATE.md](EXPERIMENT_TEMPLATE.md)**.

## Standard Data Structure

```text
EXP-XXX_name/
├─ README.md                       # Research question + result + decision
├─ config/
│  └─ run_config.md                # PVT, bounds, tool versions, seeds, reproducibility
├─ scripts/                        # SPICE run + reproducible analysis/export code
├─ data/
│  ├─ design_points.csv            # required: design_id + applied physical parameters
│  ├─ corner_metrics.csv           # required: design_id × corner + measured metrics + feasible
│  └─ analysis/                    # optional: derived statistics, margins and summaries
├─ raw/                            # optional: original run trajectory, logs, waveforms
└─ figures/                        # optional: plots linked to scripts/data
```

**데이터 기본 규칙**

- `data/` 루트에는 **표준 측정 결과 CSV 두 개만** 저장한다.
- `design_points.csv`: 1 design 당 1행 (`design_id,wp1,wn1,wp3,wn3,wn4,wn5,cc`). Width 단위 m, `cc` 단위 F.
- `corner_metrics.csv`: 1 design × 1 corner 당 1행 (`design_id,corner,gain_min,ibias_max,phm_min,t_settle_max,ugbw_min,vswing_min,feasible`). 측정 단위는 각각 무차원, A, degree, s, Hz, V.
- TT-only 실험도 `corner=TT_3.3V_27C`를 기입해 같은 schema를 쓴다. **TT feasible ≠ 17-corner robust feasible**.
- 실험별 `iteration`, `phase`, `worst_margin`, `total_violation` 같은 확장정보는 `raw/trajectory.csv` 또는 `data/analysis/`에서 보존한다. `corner_metrics.csv`에 임의로 확장 열을 추가하지 않는다.
- 코너별/설계별 요약표는 `data/analysis/`, 원본 run log/streaming 데이터는 `raw/`, 그림은 `figures/`에 둔다. 파일의 출처와 생성 script를 README에 연결한다.
- 원본 연구 데이터는 **새 스키마로 정리했다는 이유로 잃지 않는다**. 실행 중 오류·실패한 평가도 기록한다.
- 전체 AC/DC/transient waveform은 항상 GitHub에 올리지 않아도 된다. 지표가 비정상적이거나 파형 자체가 근거일 때 필요한 design/corner만 생성 조건과 함께 보존한다.
- 이미 저장된 결과를 **덮어쓰지 않는다**. 반복 실험은 새로운 run ID/Experiment를 사용하거나 출력을 별도 보존한다.

## Experiment Index

| Experiment | Status | 왜 했는가? | 완료 결과 / 다음 판단 |
| --- | --- | --- | --- |
| [EXP-001](EXP-001_pvt_init_params_baseline/README.md) | **Completed** | D000 한 점에서 corner-wise worst-corner 차이 검증 | 0/17 feasible; 서로 다른 metric의 worst corner 불일치 → 설계점 확대 |
| [EXP-002](EXP-002_atlas_initial_design_pvt/README.md) | **Completed** | ATLAS initial 20점으로 corner-wise 결과 확장 | D001–D019의 323회 추가; EXP-001과 합쳐 0/340 feasible → TT 탐색 필요 |
| [EXP-003](EXP-003_tt_adaptive_feasible_discovery/README.md) | **Completed** | GP 기반 Adaptive TT 설계로 first-feasible 탐색 | 0/60 feasible; D050 5/6 pass, worst margin -0.0973 → PM–UGBW bottleneck 및 탐색 확대 |
| [EXP-004](EXP-004_warm_start_smoke_test/README.md) | **Prepared** | EXP-003의 TT 60개 관측치로 GP Warm Start 기능 검증 | 60개 replay + 신규 D060 TT SPICE **1회 예정**; 실행 후 EXP-005 예산 확대 판단 |

### 현재 연구 흐름

```text
RQ: Corner-wise structure 보존이 robust search 효율에 도움을 주는가?
   ↓
EXP-001: D000 × 17 corners → feasible 0
   ↓
EXP-002: initial 20 designs × 17 corners → feasible 0
   ↓
EXP-003: TT initial20 + adaptive40 → feasible 0, best D050
   ↓
EXP-004: 이전 실측 60개 Warm Start + 신규 D060 1회 (검증 예정)
   ↓
EXP-005: Warm Start 검증 후 신규 평가 횟수 확대 / PM–UGBW 탐색
   ↓
Follow-up: 여러 TT region / 7D 연결성 검증
   ↓
Follow-up: same-point 17-corner PVT / persistence
   ↓
Follow-up: 동일 SPICE budget·전체 시간의 baseline 대비 개선 검증
```

## Experiment Terminal Output Convention (2026-10-09)

앞으로 **모든 신규 Experiment 실행 스크립트**는 각 설계점의 실제 평가가 끝날 때마다, 결과를 사용자가 즉시 이해할 수 있도록 **명시적인 feasibility 상태**를 터미널에 출력한다.

TT-only 실험의 표준 예시:

```text
[TT RESULT] D020 | TT_FEASIBLE=False | PASS=5/6 | WORST_MARGIN=-0.370
[CSV] Saved D020 -> .../data/trajectory.csv

[TT RESULT] D021 | TT_FEASIBLE=True | PASS=6/6 | WORST_MARGIN=+0.040
[CSV] Saved D021 -> .../data/trajectory.csv
```

- `TT_FEASIBLE=True/False`처럼 **조건(corner)과 판정(True/False)을 모두 출력**한다. `INFEAS` 같은 약어만으로 결과를 표시하지 않는다.
- `PASS=n/N`은 실제 **동일한 design**에서 충족한 spec 개수이며, 하나라도 실패하면 feasible이 아니다.
- `WORST_MARGIN`은 target에 대한 정규화된 가장 작은 여유다. **0 미만이면 최소 하나의 조건 위반**, **0 이상이면 전부 통과**한다.
- 실제로 적용된 평가 조건(예: `TT`, `FF_3.0V_125C`)을 로그에서 알 수 있어야 한다.
- 여러 PVT corner를 평가할 때는 corner별 결과를 `[PVT RESULT]` 등으로 분리하고, 필요하면 동일 design의 `ROBUST_FEASIBLE=True/False`를 별도로 표시한다. **TT feasible과 17-corner robust feasible을 혼동하지 않는다.**
- 실험 목적과 metric 특성이 다르면 `PASS` 및 `WORST_MARGIN` 등은 의미 있는 지표로 조정할 수 있지만, **평가 성공/실패의 기준 및 조건을 명시하는 원칙**은 유지한다.
- 수행된 실제 평가마다 CSV row를 즉시 저장할 수 있도록 설계하고, 중간 오류 시 기존 데이터 손실 위험을 줄인다. 출력에 `[CSV] Saved`를 표시할 때는 실제 기록이 성공했음을 확인한 뒤 출력한다.
- 실행 코드가 갱신되어도 **이미 실행 중인 Python process에는 자동 적용되지 않는다**. 실행 로그와 사용한 코드 버전을 함께 기록한다.

이 규칙은 future Experiment 기본 규칙이며 기존 완료된 EXP-001/002를 소급 재실행한다는 뜻은 아니다.

