# CURRENT — Research Status

_Last updated: 2026-10-02_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**Baseline / existing-method understanding and problem identification**

현재는 최종 제안 방법을 확정한 단계가 아니다. 기존 방법과 ATLAS 실행 흐름을 이해하고, 실제로 개선 가치가 있는 병목과 연구 질문을 좁히는 단계다.

## Current Baseline

- ATLAS 관련 연구 환경을 실행할 수 있는 상태
- smoke test 실행 성공
- 기본 출력 metric이 생성되는 것까지 확인

## Current Questions

1. ATLAS에서 design parameter가 어떤 흐름으로 평가되는가?
2. PVT / worst-case evaluation은 어디에서 수행되고 어떤 metric으로 판단되는가?
3. 계산 비용 또는 평가 방식에서 실제 연구 문제로 정의할 수 있는 병목은 무엇인가?
4. 그 문제를 개선했을 때 정확도·강건성·simulation cost를 어떤 실험으로 비교해야 하는가?

## Completed

- [x] 연구 인턴 GitHub repository 생성
- [x] 연구 기록 기본 구조 설계
- [x] ATLAS 연구 환경 smoke test
- [x] baseline metric 출력 확인

## In Progress

- [ ] ATLAS 코드/방법론 흐름 분석
- [ ] baseline에서 입력 parameter → evaluation → output metric 연결 확인
- [ ] 기존 방법의 문제를 연구 질문 형태로 명확히 정의

## Next

1. ATLAS 코드의 실제 실행 시작점과 핵심 모듈을 확인한다.
2. parameter, PVT/worst-case evaluation, metric 계산의 연결을 추적한다.
3. 분석 결과를 바탕으로 첫 정식 Experiment의 Research Question을 정한다.
4. 실험 목적이 정해진 뒤 `EXP-001`을 시작한다.

## Important

단순히 다음 코드를 실행하는 것이 목표가 아니다. 각 단계에서 **왜 확인하는지, 어떤 결과가 나오면 무엇을 의미하는지, 다음 판단에 어떻게 연결되는지**를 이해하면서 진행한다.
