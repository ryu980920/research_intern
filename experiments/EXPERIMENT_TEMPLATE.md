# EXP-XXX — [실험 이름: 무엇을 확인하는가?]

**Status:** Planned / Running / Completed / Blocked · **Date:** YYYY-MM-DD · **Circuit:** [...] · **Evaluation:** [...]

## Experiment at a Glance

| 항목 | 이번 실험의 답 |
| --- | --- |
| **왜 했는가?** | 바로 이전 결과의 어떤 문제/불확실성 때문에 필요한가? |
| **무엇을 했는가?** | 몇 개의 design, 어떤 corner, 어떤 최적화/시뮬레이션을 수행했나? |
| **무엇을 알았는가?** | 실제 측정된 대표 숫자·성공/실패 (실행 전이면 Pending이라고 표시) |
| **그래서 다음은?** | 관측에서 어떤 연구 판단이 도출됐고 후속으로 뭘 검증하나? |

## 01. Background & Motivation

기존 방법/이전 EXP 링크 → 발견한 문제 → **왜 이번 실험이 필수인지**.
아직 실행되지 않은 가설과 이미 관찰한 사실을 구분한다.

## 02. Research Question & Hypothesis

- **RQ:** 하나의 실험으로 답할 수 있는 구체적인 질문은?
- **Working hypothesis:** 예상 결과와 그 이유는?
- **Decision rule:** 무엇이 나오면 지지/반박/판단 보류할 것인가?

## 03. Experimental Setup

회로·소자·7D parameter/bounds·PVT corner·VDD·온도·bias·ngspice/PDK/ATLAS 버전·seed·budget·모델과 MC switch.
길어지면 [config/run_config.md](config/run_config.md)에 자세히 기록하고 여기에는 표로 핵심만 넣는다.

## 04. Method & Procedure

1. 실제로 수행한 순서(계획과 수행 기록 구분).
2. 각 단계가 어떤 질문을 검증하는지 설명.
3. 재현 스크립트와 config, 코드 commit 링크 제시.
4. 실패한 시행과 설정 변경은 삭제하지 말고 08 섹션에 기록.

## 05. Metrics & Evaluation Criteria

필요한 spec만 선택하고 단위/Pass 조건을 명시. TT feasible / corner feasible / 17-corner robust feasible은 분리.
정규화 margin 등 파생 metric을 쓰면 수식 및 부호 의미를 기록.

## 06. Results & Figures

실측 결과를 수치/표로 제시. 어떤 파일/분석 코드에서 생성됐는지 명시.
실행 전이면 **Pending**이라고 쓰고 측정값을 상상해 채우지 않는다.

- Standard: [data/design_points.csv](data/design_points.csv), [data/corner_metrics.csv](data/corner_metrics.csv)
- Optional processed: `data/analysis/`
- Optional source/evidence: `raw/`
- Optional figures: `figures/`

## 07. Discussion

- **Observation:** 실제 값에서 확인한 사실
- **Interpretation:** 왜 그런 현상이 발생했는지의 설명 (**가설과 사실 구분**)
- **Research implication:** 다음 연구 방향이 어떻게 바뀌었는가

## 08. Limitations & Issues

불완전한 데이터, 미검증 원인, 불확실성, 실패한 시도와 해결.
특정 원인이 추정이라면 가능성으로 명시한다.

## 09. Conclusion & Next Experiment

연구 질문의 **답 / 답하지 못한 부분**을 구분해 결론을 작성.
다음 Experiment에서 검증할 **새 질문과 그 이유**를 제안하고 관련 링크 연결.
