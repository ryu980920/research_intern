# Experiments

`experiments/`는 **하나의 연구 질문 또는 가설을 검증하는 재현 가능한 실험**을 저장합니다.

기본 구조:

```text
EXP-001_xxx/
├─ README.md
├─ config/
├─ scripts/
└─ data/
```

- `README.md`: 목적, 질문/가설, 조건, 결과, 해석, 다음 판단
- `config/`: parameter, target spec, PVT, 버전 등 실행 조건
- `scripts/`: 해당 실험을 재현하는 실행/분석 코드
- `data/`: 연구 판단에 직접 사용하는 핵심 metric CSV 또는 dataset

`raw/`와 `figures/`는 기본 폴더로 강제하지 않습니다.

- raw waveform이 특정 이상 결과의 원인 분석이나 근거 제시에 필요할 때만 `raw/`를 만듭니다.
- 실제 분석/발표에 필요한 figure가 생길 때만 `figures/`를 만듭니다.

각 Experiment README에는 가능한 경우 다음 내용을 포함합니다.

- Purpose
- Research Question / Hypothesis
- Simulation Setup
- Parameter / Condition
- Procedure
- Metrics
- Results
- Interpretation
- Conclusion
- Limitations
- Next Experiment

단순한 환경 확인이나 작은 시행착오는 바로 Experiment 번호를 부여하지 않고 먼저 `logs/`에 기록할 수 있습니다.


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

## PVT Sizing Dataset Convention

여러 design point를 PVT에서 비교하는 실험은 가능한 경우 다음 두 table을 사용합니다.

```text
data/
├─ design_points.csv
└─ corner_metrics.csv
```

- `design_points.csv`: design_id와 설계 파라미터를 1 design당 1행으로 저장
- `corner_metrics.csv`: design_id × PVT corner별 metric과 feasibility를 저장
- 두 파일은 `design_id`로 연결

이 구조는 transistor parameter를 corner 수만큼 반복 저장하지 않으면서도, 특정 design과 모든 PVT 결과를 추적할 수 있게 합니다.


## Experiment Index

| Experiment | Status | Role in Research Logic | Key Result |
| --- | --- | --- | --- |
| `EXP-001_pvt_init_params_baseline` | Completed | D000 한 점에서 17-corner PVT baseline 확보 | metric별 worst corner가 서로 다름, feasible 0 / 17 |
| `EXP-002_atlas_initial_design_pvt` | Completed | ATLAS initial 20-point set을 multi-design PVT로 확대 | 20 × 17 = 340 evaluations, feasible 0 / 340, worst-corner mismatch 반복 확인 |
| `EXP-003_tt_adaptive_feasible_discovery` | Planned / preflight 대기 | ATLAS adaptive TT search로 **최초 TT feasible point 및 joint violation 추세** 확인 | budget 60, n_init 20, GP surrogate, first feasible early stop; multi-island 검증은 범위 밖 |

현재 연구 논리:

```text
EXP-001
one-point corner-wise baseline
        ↓
EXP-002
optimizer-default 20-point PVT pilot
        ↓
feasible point 0
        ↓
EXP-003 (실행 전)
first TT feasible / boundary discovery
        ↓
후속 계획 A — TT Multi-Island Discovery
first point 주변 + 서로 떨어진 feasible region 후보 탐색
        ↓
후속 계획 B — Same-Point 17-Corner PVT
동일한 7D x 집합으로 각 corner의 region 변화 관찰
        ↓
후속 계획 C — Persistence Modeling / Baseline Comparison
corner-wise information의 robust search 효율 검증
```

Experiment 번호는 단순 작업 순서가 아니라 **독립적인 Research Question / Hypothesis가 명확해졌을 때** 부여한다.
