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
