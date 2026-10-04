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
