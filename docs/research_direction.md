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

ATLAS가 optimization 시작 시 사용하는 initial 20 points를 모두 17 corners에서 평가했다.

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

## 6. Next Direction

Robust feasible design은 반드시 TT에서도 feasible해야 한다.

따라서 다음 연구 흐름은 다음과 같이 잡는다.

```text
ATLAS initial 20 points
→ post-initial adaptive candidate selection 이해
→ TT feasible / near-feasible search
→ selected candidates 17-corner PVT evaluation
→ corner-wise feasible-set comparison
→ worst-case compression 영향 분석
→ feasible-island / persistence 분석 확대 판단
```

다음 단계에서 먼저 정해야 할 것은:

1. D020 이후 ATLAS candidate가 실제로 생성되는 코드 흐름
2. near-feasible의 정량 정의
3. TT adaptive search budget / stopping condition
4. 어떤 TT candidate를 PVT로 넘길지 selection rule
5. adaptive search 과정에서 보존할 dataset 구조

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
