# Research Direction

## 1. Background

본 연구는 InfiniTree 연구 인턴 과정에서 수행한다. 장기적으로는 **Analog Circuit Robust Design** 분야에서 논문으로 발전 가능한 연구 문제를 찾는 것이 목표다.

현재 단계에서는 특정 개선 방법을 논문 주제로 확정하지 않는다. 기존 강건설계 및 회로 평가 방법을 분석하고, 실제 simulation 결과에서 검증 가능한 문제를 먼저 찾는다.

## 2. Research Workflow

연구는 다음 순서를 기본으로 한다.

**Existing Method / Baseline → Problem → Hypothesis → Experiment → Result → Interpretation → New Hypothesis / Improvement → Validation**

핵심은 단순한 simulation 반복이 아니라, 매 실험이 하나의 질문에 답하도록 만드는 것이다.

## 3. Current Research Question

현재 초점은 ATLAS의 PVT robust evaluation에서 다음 질문을 검증하는 것이다.

> **metric-wise worst-case compression이 corner-wise feasible-region 구조를 얼마나 잃고, 그 정보 손실이 robust analog sizing의 candidate selection에 실제 영향을 주는가?**

ATLAS evaluator의 PVT mode는 여러 corner를 평가한 뒤 metric별 worst-case 값으로 압축할 수 있다.

이때 gain, phase margin, UGBW 등의 worst value가 서로 다른 physical corner에서 발생하면, optimizer가 보는 vector는 실제 하나의 corner를 그대로 나타내지 않을 수 있다.

## 4. Evidence So Far

### EXP-001 — One-Point PVT Baseline

YAML init_params인 D000을 17 corners에서 평가했다.

관찰:

- 0 / 17 corners feasible
- 모든 corner에서 phase margin target 미달
- metric별 worst corner가 서로 다름

이 결과로 metric-wise worst-case vector가 여러 corner의 값을 조합한 synthetic representation이 될 수 있음을 확인했다.

### EXP-002 — ATLAS Initial 20-Point PVT Pilot

TopoBO optimizer의 기본값 `n_init=20`으로 생성한 initial 20 points를 모두 17 corners에서 평가했다. 큰 budget의 standard runner에서는 `n_init=21`일 수 있으므로 두 경우를 구분한다.

```text
20 designs × 17 corners = 340 evaluations
```

결과:

- feasible evaluation: 0 / 340
- any-corner feasible design: 0 / 20
- robust feasible design: 0 / 20

가장 많이 실패한 spec은 UGBW, output swing, gain, phase margin 순이었다.

TT에서는 D000, D007, D008, D009가 6개 spec 중 phase margin만 실패했다.

반면 phase margin이 충분한 D002 / D006은 gain, UGBW, swing이 크게 부족했다.

### Worst-Corner Identity

20 designs에서도 metric별 worst corner가 서로 달랐다.

대표적으로:

- Gain → FF / 3.0 V / 125 C가 15 / 20 designs에서 worst
- Ibias → FF / 3.6 V / -40 C가 18 / 20 designs에서 worst
- Phase Margin → FS / 3.6 V / -40 C가 13 / 20 designs에서 worst
- UGBW → SS / 3.0 V / 125 C가 18 / 20 designs에서 worst

따라서 corner-wise information loss 가능성은 한 design에만 나타난 우연이 아니라 multi-design에서도 반복됐다.

## 5. Current Bottleneck

현재 문제는 **feasible-island를 분석할 feasible sample 자체가 없다는 것**이다.

따라서 지금 바로 50/100-point PVT dataset으로 확대하는 것은 근거가 부족하다.

sample 수만 늘리면:

- feasible region을 계속 놓칠 수 있고
- 17-corner simulation cost만 증가하며
- island topology를 분석할 데이터가 여전히 생기지 않을 수 있다.

현재 bottleneck은 sample 개수 자체보다 **feasible / near-feasible region discovery**다.

## 6. Current Research Sequence (2026-10-09 update)

현재 문제를 다음 **서로 다른 연구 질문**으로 나누어 접근한다.

### Phase A — TT Feasible Discovery: EXP-003 (실행 전)

최초 TT feasible 설계점 탐색 및 adaptive search 진단.

- budget=60 (초기 20 + 추가 최대 40 **실제 TT 설계점 평가**)
- 7 parameters, seed=42, surrogate=GP, first feasible 시 early stop
- initial 20개 TT 결과를 다시 시뮬레이션하며 기존 EXP-001/002와 대조
- metric별 normalized margin, worst_margin, total_violation, feasibility trajectory 관찰

**왜 TT 먼저?** 17-corner robust-feasible 점이라면 TT에서도 반드시 feasible해야 한다. 초기 20개가 모두 TT-infeasible하므로 TT의 joint feasible/near-boundary region을 먼저 찾는 것이 이후 corner 평가 대상을 좁히는 데 도움이 된다.

**한계:** first feasible은 단지 한 점이다. 해당 region의 경계·연결성이나 다른 island가 없다는 사실을 보장하지 않는다.

### Phase B — TT Multi-Island Discovery (후속, 미실행)

**추가로 제기한 핵심 위험:** feasible 영역은 TT에서도 하나가 아니라 **서로 떨어진 여러 island A/B/...**로 존재할 수 있다.

한 feasible point 근처만 탐색하면 멀리 있는 island를 놓칠 수 있다.

따라서 EXP-003의 first feasible 발견 뒤 **별도의 탐색 단계**에서 다음을 수행한다.

1. 발견한 TT feasible point의 local boundary와 주변 margin을 탐색
2. 다른 seed / global sampling / 독립 초기 영역 등을 통해 먼 영역도 탐색
3. 필요 시 early stop 없이 추가 탐색을 진행하는 별도 run 설계
4. design parameter 7차원을 normalized coordinate로 나타내고 distance/adjacency 기준 정의
5. 측정된 feasible points와 Mapper의 predicted components를 구분
6. 2D 투영에서 분리되어 보여도 실제 7D에서 이어질 수 있으므로 **연결 경로 검증** 고려

결과는 "몇 개 island가 확정됐다"라고 성급히 주장하지 않고, region 후보와 연결성에 대한 근거 강도를 기록한다.

### Phase C — Same-Point Cross-PVT Feasible Map (후속, 미실행)

서로 다른 TT region 후보 A/B/...에서 고른 **공통 x 집합**을 TT 포함 17개 corner 모두에 투입한다.

- 동일 design x에서 corner별 metric 및 feasibility
- 각 region의 local boundary 변화
- corner별 feasible set의 이동·축소·소멸·분리 가능성
- 17개 corner 모두 만족하는 robust-feasible 교집합

**왜 같은 x를 사용하나?** Corner마다 다른 x로 최적화하면 영역이 PVT 조건에 의해 어떻게 달라졌는지 직접 비교할 수 없다.

### Phase D — Island Matching, Persistence, and Improvement Test (후속, 미실행)

Corner별 feasible region을 어떻게 대응시킬지(matching)와 지속성(persistence)을 어떻게 정의할지 설계한다.

최종 검증 질문:

> Corner-wise island 정보를 이용하는 후보 선택 방법이 기존 metric-wise worst-case baseline보다 **같은 simulation cost에서** robust feasible design을 더 효과적으로 찾는가?

비교 지표 후보: robust feasibility discovery success, first robust design까지의 evaluation cost, 지정 budget 내 robust design 수, region coverage.

**중요한 원칙:** 각 corner를 정확히 평가해 metric별 최악값을 취하는 것은 **최종 robust feasibility 판정의 참/거짓**을 바꾸지 않는다. 잃는 것은 corner별 metric identity와 geometry/연결 정보다. 따라서 novelty는 더 정확한 pass/fail 판정이 아니라 **그 정보가 탐색에 어떤 이득을 주는지**에서 검증해야 한다.

현재 Phase A만 EXP-003으로 지정했다. 나머지의 실험 번호와 budget은 결과를 본 뒤 결정한다.

## 7. Working Hypothesis

현재 working hypothesis는 다음과 같다.

1. 같은 design space에서도 PVT corner에 따라 feasible set의 위치와 연결 구조가 달라질 수 있다.
2. metric-wise worst-case compression은 이러한 corner-specific structure를 제거할 수 있다.
3. corner-wise 정보를 유지하면 robust candidate selection에 추가적인 유용한 정보를 제공할 가능성이 있다.

하지만 아직 3번은 검증되지 않았다.

현재 실험은 **정보 손실이 존재하는지**와 **그 정보가 실제 candidate selection에 도움이 되는지**를 분리해서 검증하는 단계다.

## 8. Experiment Decision Rule

새 simulation을 제안하기 전에 다음 질문에 답한다.

1. 무엇을 확인하려는가?
2. 왜 이 simulation이 필요한가?
3. 어떤 변수를 바꾸는가?
4. 어떤 metric / waveform / graph를 볼 것인가?
5. 어떤 결과가 나오면 가설을 지지하거나 반박하는가?
6. 그 결과가 다음 실험에 어떻게 연결되는가?

이 질문에 답할 수 없는 simulation은 우선 실행하지 않는다.

## 9. Research Recording Rule

결과는 다음 구조로 기록한다.

- **Observation:** 실제로 무엇이 나타났는가?
- **Interpretation:** 그 결과를 어떻게 해석할 수 있는가?
- **Research Implication:** 현재 연구 질문에 어떤 의미가 있는가?
- **Next:** 다음에 무엇을 검증해야 하는가?

해석 근거가 부족하면 사실처럼 단정하지 않고 가설로 표시한다.

## 10. Direction Changes

연구 방향이 바뀌면 이전 방향을 지우지 않는다.

무엇을 확인했고, 왜 기존 방향을 유지하지 않았는지 날짜별 log에 근거를 남긴다.

현재 방향 판단에는 항상 최신 `CURRENT.md`, 실제 코드, config, simulation 결과를 우선한다.
