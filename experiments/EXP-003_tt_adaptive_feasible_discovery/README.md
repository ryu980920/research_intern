# EXP-003 — ATLAS TT Adaptive Feasible Discovery

_Date started: 2026-10-09_  
_Status: Ready to run_

## Purpose

EXP-002의 optimizer-default 20-point pilot에서는 20 designs × 17 PVT corners를 평가했지만 feasible evaluation이 0 / 340이었다.

다음 단계에서는 PVT sample 수를 무작정 늘리지 않고, **ATLAS의 post-initial adaptive search가 TT에서 joint-feasible region으로 실제로 이동할 수 있는지** 확인한다.

이 실험의 역할은 feasible-island 분석 자체가 아니라, 그 분석에 필요한 feasible / boundary candidates를 먼저 확보하는 것이다.

## Research Question

> Initial 20 points가 모두 TT-infeasible한 상태에서, ATLAS의 adaptive candidate selection은 joint constraint violation을 줄이고 TT-feasible design을 찾을 수 있는가?

추가로 adaptive trajectory를 보면서 다음을 확인한다.

1. D020 이후 candidate의 normalized worst constraint margin이 개선되는가?
2. 어떤 spec이 candidate별 bottleneck으로 남는가?
3. first feasible이 발견된다면 몇 번째 evaluation에서 나타나는가?
4. topology 관련 `beta0`, `|F_hat|` 변화와 실제 feasibility 개선이 함께 나타나는가?

## Why Budget = 60

Standard `run_experiment.py`의 initial size rule은:

```python
n_init = max(min(3 * n_params, budget // 3, 50), 10)
```

two-stage GF180 op-amp는 7 parameters이다.

```text
budget = 60
→ min(21, 20, 50)
→ n_init = 20
```

따라서 budget 60을 사용하면 **standard runner의 n_init 계산을 유지하면서 EXP-002의 D000-D019 20-point definition과 정확히 맞출 수 있다.**

구성:

```text
D000-D019 : initial 20 points
D020-D059 : 최대 40 adaptive candidates
```

단, first feasible을 찾으면 early stop한다.

## Why TT Only

Robust feasible design이라면 TT에서도 target spec을 모두 만족해야 한다.

따라서 지금은 비싼 17-corner PVT를 모든 adaptive candidate에 적용하지 않고:

```text
TT adaptive discovery
→ feasible / near-feasible candidate selection
→ selected candidate만 PVT
```

순서로 진행한다.

## Surrogate Choice

Standard runner의 default `surrogate=auto`는 GP fitting 시간이 특정 시간보다 길어지면 NN으로 전환한다.

이 전환 시점은 machine speed에 영향을 받을 수 있다.

본 실험은 candidate trajectory의 재현성이 우선이므로:

```text
surrogate = gp
```

로 고정한다.

이는 standard runner의 `auto` 설정과의 의도적인 차이이며 config에 명시한다.

## Metrics

각 실제 SPICE evaluation마다 다음을 저장한다.

- iteration / design_id
- phase: init or adaptive
- 7 design parameters
- six TT metrics
- feasible
- number of passed specs
- worst normalized constraint margin
- total normalized violation

Normalized constraint margin:

minimum-required spec:

```text
margin = (value - target) / target
```

maximum-allowed spec:

```text
margin = (target - value) / target
```

따라서:

```text
worst_margin >= 0
→ all specs satisfied
→ feasible
```

이다.

## Expected Interpretation

### Case A — TT feasible found

ATLAS가 initial infeasible region에서 joint-feasible region으로 이동할 수 있음을 확인한다.

그 다음에는 first feasible 및 boundary candidates를 선정해 17-corner PVT로 넘긴다.

### Case B — No TT feasible within budget 60

즉시 100-point PVT로 확대하지 않는다.

adaptive trajectory에서:

- worst margin이 개선되고 있는지
- 특정 spec에서 stagnation하는지
- bottleneck weighting과 실제 joint bottleneck이 어긋나는지
- candidate diversity / topology가 유지되는지

를 먼저 분석한 뒤 budget 확대 또는 baseline 수정 여부를 결정한다.

## Data

실행 후 생성 예정:

```text
data/
├─ trajectory.csv
└─ run_summary.json

raw/
└─ atlas_logs/
   └─ <run_id>/
      ├─ config.json
      ├─ iterations.jsonl
      ├─ progress.log
      └─ results.json
```

`trajectory.csv`가 parameter + metric을 함께 보존하는 primary analysis dataset이다.

ATLAS의 기본 `iterations.jsonl`에는 design parameter x가 저장되지 않으므로, 본 실험 script가 `ExperimentLogger.history_X`를 이용해 별도 trajectory CSV를 만든다.

## Procedure

1. ATLAS commit과 GF180 statistical switch를 확인한다.
2. TT-only evaluator를 생성한다.
3. standard `n_init_for()`로 budget 60의 n_init=20을 확인한다.
4. TopoBO를 GP surrogate로 실행한다.
5. first feasible까지 또는 budget 60까지 실행한다.
6. complete trajectory를 CSV로 저장한다.
7. initial D000-D019가 기존 deterministic TT 결과와 일치하는지 확인한다.
8. adaptive D020+의 margin trajectory를 분석한다.

## Next

실행 결과를 본 뒤에만 selected candidate PVT evaluation을 설계한다.
