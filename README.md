# research_intern

InfiniTree 연구 인턴 과정에서 수행하는 **아날로그 회로 강건설계(Analog Circuit Robust Design)** 연구를 재현 가능한 형태로 기록하기 위한 Private repository입니다.

## Research Context

- Internship: InfiniTree
- Advisor: 오영민 박사님
- Umbrella project: *Advanced Hardware Architecture with NVIDIA for Efficient ASR and Multimodal LLM Systems*
- Long-term goal: 아날로그 회로 강건설계 분야에서 논문으로 발전시킬 수 있는 연구 주제 발굴 및 검증

이 저장소는 단순 코드 보관용이 아니라 다음 연결을 추적하기 위한 연구 기록입니다.

**Research Question → Condition/Config → Code → Simulation → Raw Data → Processed Data → Figure → Interpretation → Next Decision**

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
├─ src/
├─ notebooks/
├─ data/
│  ├─ raw/
│  └─ processed/
└─ environment/
```

### 어디에 무엇을 넣는가

- `CURRENT.md`: 지금 연구가 어디까지 왔는지 요약
- `docs/research_direction.md`: 연구 방향과 방향이 바뀐 이유
- `docs/literature/`: 논문 및 기존 방법 조사
- `docs/meetings/`: 미팅 내용과 결정사항
- `logs/`: 날짜별 연구 과정 기록
- `experiments/`: 하나의 연구 질문을 검증하는 재현 가능한 실험
- `src/`: 여러 실험에서 재사용하는 코드
- `notebooks/`: 탐색적 분석
- `data/raw/`: 원본 데이터
- `data/processed/`: 분석용으로 가공한 데이터
- `environment/`: Python/패키지/실행환경 정보

## Recording Principle

실험 결과는 수치나 그림만 저장하지 않습니다. 가능한 경우 다음 흐름을 함께 기록합니다.

**Observation → Interpretation → Research Implication → Next**

실패한 실험도 삭제하지 않고 원인, 수정, 배운 점을 남깁니다.

## Data Policy

대용량 SPICE raw 파일은 GitHub에 무조건 업로드하지 않습니다. 필요한 경우 외부 저장 위치와 생성 방법을 기록하고, GitHub에는 설정값, 핵심 CSV, figure, 요약 결과를 남깁니다.

> 연구 방향은 탐색 과정에서 변경될 수 있습니다. 과거 아이디어보다 `CURRENT.md`, 최신 코드와 실제 실험 결과를 우선합니다.
