# EXP-003 Configuration

## Circuit

- Circuit: two-stage GF180 op-amp
- YAML: `eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml`
- PVT mode: OFF
- Evaluation corner: TT / 3.3 V / 27 C

## ATLAS

- ATLAS commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- Method: ATLAS / `TopoBO`
- Budget: 60
- Seed: 42
- n_init: standard `n_init_for()` result = 20
- Surrogate: GP
- Early stop: ON
- Candidate pool: 50,000

## Why n_init = 20 Here

```text
n_params = 7
budget = 60

n_init = max(min(3*n_params, budget//3, 50), 10)
       = max(min(21, 20, 50), 10)
       = 20
```

This intentionally aligns the standard-run initial definition with EXP-002 D000-D019.

## Parameter Bounds

```text
wp1: 0.5e-6  ~ 100e-6
wn1: 0.5e-6  ~ 100e-6
wp3: 0.5e-6  ~ 100e-6
wn3: 0.5e-6  ~ 100e-6
wn4: 0.5e-6  ~ 100e-6
wn5: 0.5e-6  ~ 100e-6
cc : 0.1e-12 ~ 10e-12
```

## Target Specs

```text
gain_min      >= 300
vswing_min    >= 0.3
ugbw_min      >= 2e7
phm_min       >= 60
ibias_max     <= 0.001
t_settle_max  <= 6e-6
```

## GF180 Statistical Settings

Required for this deterministic TT baseline:

```spice
sw_stat_global = 0
sw_stat_mismatch = 0
```

## Output

Primary:

- `data/trajectory.csv`
- `data/run_summary.json`

Execution evidence:

- `raw/atlas_logs/<run_id>/config.json`
- `raw/atlas_logs/<run_id>/iterations.jsonl`
- `raw/atlas_logs/<run_id>/progress.log`
- `raw/atlas_logs/<run_id>/results.json`


## Research Purpose and Experiment Boundary

**Purpose:** EXP-001/002 initial 20 designs의 17-corner dataset에서 feasible evaluation이 0/340이었다. 현재는 island 경계를 측정할 실제 feasible point가 없으므로, 먼저 TT-only adaptive search로 첫 feasible / lower-violation candidate를 찾는다.

**This experiment DOES test:**

- initial TT-infeasible observations 20개 뒤에 ATLAS가 추가 candidate를 선택하는 방식
- 실제 TT metric / normalized violation의 iteration별 변화
- budget 60 이내 first TT feasible을 찾는지 여부

**This experiment DOES NOT test:**

- TT feasible island가 하나인지 여러 개인지
- 17-corner robust feasibility
- corner-wise feasible island persistence
- 기존 ATLAS 대비 proposed method의 성능 우위

본격적인 multi-island discovery와 Cross-PVT comparison은 후속 실험에서 따로 계획한다.

## Budget Accounting

\`\`\`text
budget = 60 (maximum number of TT design evaluations)
n_init = 20
adaptive = up to 40

D000-D019 = initial
D020-D059 = adaptive (if no early stop)
\`\`\`

이 'evaluation 1회'는 **설계 파라미터 한 조합을 TT에서 평가하는 단위**다. 한 TT 평가 내부에서 AC, DC, transient 등 여러 종류의 SPICE 분석이 일어나므로, subprocess 총 횟수와 같지 않다.

50,000 candidate pool은 **surrogate-based prediction/scoring** 대상이지 50,000 SPICE calls가 아니다. feasible point가 아직 없으면 candidate pool은 통상 global LHS 40,000 + observed promising points 주변 local 10,000으로 구성된다.

최초 feasible 발견 시 종료하는 것은 **EXP-003 pilot을 위한 정책**이다. 후속 multi-island 탐색에서는 다른 island를 발견하기 위해 early stop을 끄거나 독립 seed run을 별도로 설계해야 한다.

이 budget 60은 과학적으로 최적인 예산으로 입증된 것이 아니다. 7 parameters에서 standard \`n_init_for()\`가 20이 되도록 맞춘, 제한된 pilot budget이다.

## Initial Data Reuse Policy

\`run_adaptive_tt_search.py\`는 EXP-001/002의 committed TT metric CSV를 optimizer에 직접 주입해 warm-start하지 않는다.

**D000-D019를 TT에서 다시 실제 시뮬레이션**한다. 따라서:

- 동일한 ATLAS commit, seed, parameter bounds, PDK/MC settings로 initial set이 재현되는지 확인한다.
- 재평가한 D000-D019의 parameter 및 TT metric을 기존 EXP-001/002의 값과 비교해야 한다.
- 불일치 발생 시 adaptive candidate 분석에 앞서 먼저 원인을 조사한다.
- 재평가 20회도 budget=60에 포함된다.

## Optimizer and Decision Logic

\`\`\`text
X/Y observations
→ GP surrogate refit
→ 50,000 candidate generation
→ predicted spec margins + feasibility probability
→ predicted near-feasible set (F_hat)
→ Mapper topology-aware acquisition
→ one x_next selected
→ one actual TT evaluation
→ observation appended
\`\`\`

- \`F_hat\` / \`beta0\`: 모델에서 예측한 near-feasible structure; 실제 SPICE 기반 feasible-island 수가 아님.
- 내부 surrogate의 working constraints는 infeasible 단계에서 완화될 수 있지만 **feasible 판정은 본 config의 original target specs**를 사용.
- \`surrogate=gp\`를 선택한 이유: \`auto\`에서 학습 시간에 따른 NN 전환 변수를 배제해 trajectory 비교를 단순화하기 위함.

## Derived Metrics and Interpretation

Minimum constraint (\`gain_min, ugbw_min, phm_min, vswing_min\`):

\`\`\`text
margin = (measured - target) / abs(target)
\`\`\`

Maximum constraint (\`ibias_max, t_settle_max\`):

\`\`\`text
margin = (target - measured) / abs(target)
\`\`\`

Calculated columns:

- \`n_specs_passed\`: original specs 통과 개수
- \`worst_margin\`: 6개 normalized margins의 최소값
- \`total_violation\`: \`sum(max(0, -margin))\`
- \`feasible\`: **한 design이 여섯 target을 동시에 만족**

예: PM 30° / target 60°이면 margin = -0.5. 이 design이 나머지 다섯 spec을 통과했더라도, phase margin이 50% 부족하므로 spec pass count만으로 "feasible 경계에 매우 가깝다"고 판단하지 않는다.

## Analysis Figures to Generate After Run

| Figure | Input | Decision |
| --- | --- | --- |
| worst_margin vs iteration | \`data/trajectory.csv\` | 가장 나쁜 spec이 0 경계 쪽으로 개선되는가? |
| total_violation vs iteration | \`data/trajectory.csv\` | 실패 항목들의 전체 위반량이 줄어드는가? |
| per-spec margins vs iteration | \`data/trajectory.csv\` | PM을 높이면서 Gain/UGBW가 악화되는 trade-off가 있는가? |
| parameter trajectory | \`data/trajectory.csv\` | ATLAS가 어느 설계 변수를 움직이는가? |
| beta0 / n_F_hat diagnostic | \`raw/atlas_logs/<run_id>/iterations.jsonl\` | predicted topology 변화와 실제 개선이 관련되어 보이는가? |

현재 Figure나 Results는 아직 생성/확인된 것이 아니다.

## Reproducibility and Failure Checks

- 실행 전 ATLAS commit hash 확인
- 사용 중인 PDK \`design.ngspice\`의 statistical switches가 실제로 0인지 확인
- 로컬 PDK 모델 **경로와 include 경로**가 현재 PC와 맞는지 확인
- ngspice 버전 / 사용 executable 확인
- D000-D019 baseline TT 비교
- \`feasible\`, \`worst_margin\` 계산 결과의 일치 여부 확인
- metric이 NaN, penalty, sentinel 또는 물리적으로 이상한 값이면 해당 corner/netlist/waveform을 재검증하고 그대로 수치 해석하지 않기

## Follow-up Branching Rule

- **First TT feasible found:** 이번 run 종료. 이 결과를 단일 island 전체로 간주하지 않고, 다음 실험에서 다른 TT feasible region 및 boundary를 탐색.
- **No feasible but margin improves:** iteration별 trend를 보고 추가 budget / parameter exploration 계획.
- **No feasible and stagnation:** GP prediction, trade-off, bounds, evaluator/metric extraction 또는 multi-start 방법 검토.

**후속 multi-island 연구:** EXP-003 이후 first feasible 근처 local 탐색뿐 아니라 멀리 떨어진 feasible component의 가능성을 global sampling / 여러 seed / 다른 출발점으로 확인해야 한다. 7차원 연결성을 2D 투영만으로 판정하지 않는다.

**후속 17-corner 비교:** 서로 다른 TT region 후보 A/B/...에서 선택한 **동일한 design_id와 동일한 7D x**를 각 corner에 적용해 결과를 \`design_points.csv\` + \`corner_metrics.csv\`에 보존한다. 그 뒤 persistence 정의와 robust-search baseline 비교를 설계한다.
