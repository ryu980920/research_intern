# Research Direction

## 1. Background

본 연구는 InfiniTree 연구 인턴 과정에서 수행한다. 장기적으로는 **Analog Circuit Robust Design** 분야에서 논문으로 발전 가능한 연구 문제를 찾는 것이 목표다.

현재 단계에서는 특정 아이디어를 논문 주제로 확정하지 않는다. 기존 강건설계 및 회로 평가 방법을 분석하고, 실제로 검증 가능한 문제를 찾는 것을 먼저 수행한다.

## 2. Research Workflow

연구는 다음 순서를 기본으로 한다.

**Existing Method / Baseline → Problem → Hypothesis → Experiment → Result → Interpretation → New Hypothesis / Improvement → Validation**

핵심은 단순한 시뮬레이션 반복이 아니라, 매 실험이 하나의 질문에 답하도록 만드는 것이다.

## 3. Current Direction

현재 초점은 **ATLAS baseline 및 관련 robust-design evaluation 흐름을 이해하는 것**이다.

확인해야 할 핵심은 다음과 같다.

- 어떤 design parameter가 입력되는가?
- 성능 metric은 어떻게 계산되는가?
- PVT 또는 worst-case 평가가 어떤 방식으로 연결되는가?
- 평가 비용이 어디에서 증가하는가?
- 기존 방법의 한계가 실제 simulation 결과에서 확인되는가?

이 분석이 끝난 뒤에야 개선 방법을 정한다.

## 4. Experiment Decision Rule

새 simulation을 제안하기 전에 다음 질문에 답한다.

1. 무엇을 확인하려는가?
2. 왜 이 simulation이 필요한가?
3. 어떤 변수를 바꾸는가?
4. 어떤 metric / waveform / graph를 볼 것인가?
5. 어떤 결과가 나오면 가설을 지지하거나 반박하는가?
6. 그 결과가 다음 실험에 어떻게 연결되는가?

이 질문에 답할 수 없는 simulation은 우선 실행하지 않는다.

## 5. Research Recording Rule

결과는 다음 구조로 기록한다.

- **Observation:** 실제로 무엇이 나타났는가?
- **Interpretation:** 그 결과를 어떻게 해석할 수 있는가?
- **Research Implication:** 현재 연구 질문에 어떤 의미가 있는가?
- **Next:** 다음에 무엇을 검증해야 하는가?

해석 근거가 부족하면 사실처럼 단정하지 않고 가설로 표시한다.

## 6. Direction Changes

연구 방향이 바뀌면 이전 방향을 지우지 않는다. 무엇을 확인했고, 왜 기존 방향을 유지하지 않았는지 근거를 남긴다. 현재 방향 판단에는 항상 최신 `CURRENT.md`, 실제 코드, config, simulation 결과를 우선한다.
