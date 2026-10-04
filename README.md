# research_intern

InfiniTree 연구 인턴 과정에서 수행하는 **아날로그 회로 강건설계(Analog Circuit Robust Design)** 연구를 재현 가능한 형태로 기록하기 위한 Private repository입니다.

## Research Context

- Internship: InfiniTree
- Advisor: 오영민 박사님
- Umbrella project: *Advanced Hardware Architecture with NVIDIA for Efficient ASR and Multimodal LLM Systems*
- Long-term goal: 아날로그 회로 강건설계 분야에서 논문으로 발전시킬 수 있는 연구 주제 발굴 및 검증

이 저장소는 단순 코드 보관용이 아니라 다음 연결을 추적하기 위한 연구 기록입니다.

**Research Question → Condition/Config → Code → Simulation → Metric Dataset → Interpretation → Next Decision**

## Current Snapshot

Latest completed experiment: `EXP-002_atlas_initial_design_pvt`

```text
ATLAS initial 20 design points
× 17 PVT corners
= 340 corner evaluations
```

현재 결과에서는 feasible evaluation이 0 / 340이었으며, metric별 worst corner가 서로 다른 현상은 multi-design에서도 반복 확인됐다.

따라서 다음 단계는 임의 PVT sample 수를 바로 늘리는 것이 아니라 **ATLAS adaptive TT search를 통해 feasible / near-feasible region을 먼저 찾는 것**이다.

최신 연구 상태와 다음 판단은 `CURRENT.md`를 기준으로 한다.

## Repository Structure

```text
research_intern/
├─ README.md
├─ CURRENT.md
├─ docs/
│  ├─ research_direction.md
│  ├─ literature/
│  └─ meetings/
├─ logs/
├─ experiments/
│  └─ EXP-xxx/
│     ├─ README.md
│     ├─ config/
│     ├─ scripts/
│     └─ data/
├─ src/
├─ notebooks/
└─ environment/
```

### 어디에 무엇을 넣는가

- `CURRENT.md`: 지금 연구가 어디까지 왔는지 요약
- `docs/research_direction.md`: 연구 방향과 방향이 바뀐 이유
- `docs/literature/`: 논문 및 기존 방법 조사
- `docs/meetings/`: 미팅 내용과 결정사항
- `logs/`: 날짜별 연구 과정 기록
- `experiments/`: 하나의 연구 질문을 검증하는 재현 가능한 실험
- 각 Experiment의 `data/`: 해당 실험에서 분석에 사용하는 핵심 metric CSV 또는 dataset
- `src/`: 여러 실험에서 재사용하는 코드
- `notebooks/`: 탐색적 분석
- `environment/`: Python/패키지/실행환경 정보

## Recording Principle

실험 결과는 수치만 저장하지 않습니다. 가능한 경우 다음 흐름을 함께 기록합니다.

**Observation → Interpretation → Research Implication → Next**

실패한 실험도 삭제하지 않고 원인, 수정, 배운 점을 남깁니다.

## Data Policy

기본적으로 각 실험은 **재현 가능한 config + 실행 script + 핵심 metric dataset**을 보존합니다.

SPICE가 내부적으로 생성하는 `ac.csv`, `dc.csv`, `dc_sweep.csv`, `tran.csv` 같은 waveform/raw output을 모든 design point와 모든 PVT corner에 대해 상시 저장하지 않습니다. 현재 연구의 feasible-region / feasible-island 분석에는 corner-wise metric table이 직접 사용되기 때문입니다.

raw waveform은 특정 metric의 이상값을 진단하거나 파형 자체가 연구 근거로 필요한 경우에만 해당 design/corner를 선택적으로 재생성하여 보존합니다. Figure 역시 연구 질문을 판단하거나 결과를 전달하는 데 필요할 때 생성합니다.

> 연구 방향은 탐색 과정에서 변경될 수 있습니다. 과거 아이디어보다 `CURRENT.md`, 최신 코드와 실제 실험 결과를 우선합니다.
