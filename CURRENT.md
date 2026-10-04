# CURRENT — Research Status

_Last updated: 2026-10-04_

## Long-term Goal

아날로그 회로 강건설계(Analog Circuit Robust Design) 분야에서 기존 방법의 한계를 찾고, 실험으로 검증 가능한 개선 방법을 제안하여 논문 후보 주제로 발전시킨다.

## Current Stage

**Baseline / existing-method understanding and problem identification**

현재는 최종 제안 방법을 확정한 단계가 아니다. 기존 방법과 ATLAS 실행 흐름을 이해하고, 실제로 개선 가치가 있는 병목과 연구 질문을 좁히는 단계다.

## Current Baseline

- ATLAS 관련 연구 환경을 실행할 수 있는 상태
- smoke test 실행 성공
- 기본 출력 metric이 생성되는 것까지 확인
- 연구 결과를 기록할 GitHub repository 기본 구조 구축 완료

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
- [x] smoke test를 첫 연구 일지로 기록

## In Progress

- [ ] ATLAS 코드/방법론 흐름 분석
- [ ] baseline에서 입력 parameter → evaluation → output metric 연결 확인
- [ ] 기존 방법의 문제를 Research Question 형태로 명확히 정의

## Next

### Step 1 — ATLAS 실행 흐름 이해

실제 코드를 따라가며 다음 연결을 확인한다.

**입력 design parameter → 회로 평가/SPICE 실행 → metric 추출 → constraint 또는 objective 판단 → 다음 candidate 선택**

목적은 단순히 파일 이름을 찾는 것이 아니라, **ATLAS가 어떤 정보를 이용해 다음 설계점을 정하는지 이해하는 것**이다.

### Step 2 — PVT / Worst-case 평가 위치 확인

ATLAS의 baseline 흐름에서 PVT 또는 worst-case 평가가 어디에 들어가는지 확인한다.

확인할 항목:

- 한 design point를 평가할 때 몇 번의 simulation이 필요한가?
- corner별 결과를 각각 유지하는가, 하나의 worst 값으로 압축하는가?
- 어떤 metric에 대해 worst-case를 판단하는가?
- 이 과정이 전체 simulation cost에 얼마나 영향을 줄 수 있는가?

### Step 3 — 첫 Research Question 결정

코드와 방법론을 실제로 확인한 뒤 기존 방식의 한계를 하나의 질문으로 좁힌다.

이 단계 전에는 개선 방법을 먼저 확정하지 않는다.

### Step 4 — EXP-001 시작

Research Question이 정해졌을 때 처음으로 `EXP-001_xxx`를 만든다.

EXP-001에는 최소한 다음을 명확히 한다.

- 무엇을 검증하는가?
- baseline은 무엇인가?
- 어떤 parameter를 바꾸는가?
- 어떤 metric / waveform / graph가 필요한가?
- 어떤 결과가 나오면 가설을 지지하거나 반박하는가?

## Working Principle

단순히 다음 코드를 실행하는 것이 목표가 아니다.

각 단계에서 반드시 다음을 이해하면서 진행한다.

1. 왜 지금 이 작업을 하는가?
2. 무엇을 확인하려는가?
3. 어떤 결과가 나오면 무엇을 의미하는가?
4. 그 결과가 다음 판단에 어떻게 연결되는가?
