# ATLAS ICCAD 2026 논문 재현 조건 감사 — EXP-003 비교

**기록일:** 2026-10-10  
**작업 상태:** 정적 문서·코드 검토 완료 / 새 SPICE 실행 **0회** / 정식 논문 재현 실행 **미실행**  
**연구 결정:** EXP-005는 Stage 3B-2까지 기록하고 **Paused**. 개별 GP의 MAE·분산 문제를 ATLAS 논문 전체의 재현 실패라고 확대하지 않는다.

## 1. 재현할 연구 질문

**RQ:** 우리의 EXP-003 (GF180 two-stage, TT, seed42, budget60)은 ATLAS ICCAD 2026 논문에서 검증한 설정과 어느 정도 같은가? 차이가 있다면, 논문 결과를 재현했거나 반박했다고 말하기 전에 무엇을 통제해야 하는가?

**기본 구분:**
- **Paper-level reproduction:** 논문의 논리·설정·성공률(SR)/최초 성공까지의 SPICE 평가 수(FSD)를 가능한 동일한 조건으로 다시 측정한다.
- **Released-code baseline replication:** 2026-10-10에 확인한 공개 코드(ATLAS commit `dd23c5ba7beb598909be593e4a84c81dab92cc69`)를 고정하고 현재 환경에서 standard 실행 결과를 측정한다.
- **EXP-003:** 논문 재현이 아닌 **60 TT evaluation pilot**. 0/60 feasible은 논문의 10-run/500-eval 결과와 충돌한다는 뜻이 아니다.

논문 발표 당시 코드와 현재 공개 코드가 동일하지 않을 수 있으므로 **위의 두 재현 목적을 혼동하지 않는다.**

## 2. 확인한 1차 출처

1. 논문 원문: Youngmin Oh et al., *ATLAS: Adaptive TDA-guided Landscape-Aware Transistor Sizing*, ICCAD 2026, arXiv [2610.10985](https://arxiv.org/abs/2610.10985), DOI [10.1145/3831252.3834039](https://doi.org/10.1145/3831252.3834039). 비교 근거: **§4.1 Experimental Setup**, **Table 1 Parameter Ranges**, **Table 2 Target Specifications**, **§4.2 / Table 3 Main Results**.
2. 공개 소스(고정 commit): [README](https://github.com/youngmin0oh/atlas/blob/dd23c5ba7beb598909be593e4a84c81dab92cc69/README.md), [run_experiment.py](https://github.com/youngmin0oh/atlas/blob/dd23c5ba7beb598909be593e4a84c81dab92cc69/run_experiment.py), [run_benchmark.py](https://github.com/youngmin0oh/atlas/blob/dd23c5ba7beb598909be593e4a84c81dab92cc69/run_benchmark.py), [circuit_eval.py](https://github.com/youngmin0oh/atlas/blob/dd23c5ba7beb598909be593e4a84c81dab92cc69/topbo/circuit_eval.py), [two_stage_opamp_gf180.yaml](https://github.com/youngmin0oh/atlas/blob/dd23c5ba7beb598909be593e4a84c81dab92cc69/eval_engines/ngspice/ngspice_inputs/yaml_files/two_stage_opamp_gf180.yaml).
3. 우리 완료 실험: [EXP-003 README](../../experiments/EXP-003_tt_adaptive_feasible_discovery/README.md), [실행 설정](../../experiments/EXP-003_tt_adaptive_feasible_discovery/config/run_config.md), [실제 사용 스크립트](../../experiments/EXP-003_tt_adaptive_feasible_discovery/scripts/run_adaptive_tt_search.py), [원본 trajectory](../../experiments/EXP-003_tt_adaptive_feasible_discovery/raw/trajectory.csv).
4. [InfiniTree 연구 소개](https://www.infinitree.ai/tech-blog/tda-for-analog-circuit-optimization/): 논문의 주요 수치와 목적을 해설한 보조 자료. 가능하면 논문 원문과 실제 코드가 우선.

## 3. 검증된 비교표

| 항목 | ICCAD 논문 | 공개 ATLAS 고정 코드 | EXP-003 실제 완료 실험 | 판단 |
| --- | --- | --- | --- | --- |
| 목적 | 최초로 모든 사양을 만족하는 설계점 탐색 | Success/first feasible 로깅 | 60회 내 first TT feasible pilot | 같은 목표, 다른 검증 범위 |
| 회로 | TSA, GF180MCU | `two_stage_opamp_gf180` | 동일 GF180 two-stage | **일치** |
| 설계 변수 | 7D, 여섯 width+cc | 6×[0.5,100] µm, cc [0.1,10] pF | 동일 bounds | **일치** |
| 목표 사양 | Gain≥300, PM≥60°, UGBW≥20 MHz, swing≥0.3 V, Ibias≤1 mA, Tsettle≤6 µs | YAML 여섯 target 동일 값 | 동일 목표 | **일치** |
| 논문 회로 평가 | 오픈소스 ngspice benchmark; post-layout/PVT signoff로 보고하지 않음 | `CircuitEvaluator(pvt=False)`가 기본 → TT netlist 1개 | `pvt=False`, TT 3.3V 27°C | 공개 코드 TT 정책과 **일치**; 논문 내부 전 버전 검증은 별개 |
| 예산 | 500 evaluations per run | runner 기본값 500 | **60** | **핵심 차이** |
| 초기 관측 | `3d` (최대 50) → TSA 21개 | `n_init_for(..., budget)` = `max(min(3*d,budget//3,50),10)` | **20** (`budget=60`으로 인해) | **핵심 차이** |
| 반복 실험 | 10개 runs, seed=42 기반 | benchmark `n_runs=10`, run seed `42+index` | **seed42 1회** | **핵심 차이** |
| Spec target 변화 | 본문에 '10 random specification targets (seed=42)'라고 기술 | 현재 YAML은 모든 `[low,high]`가 `low==high`: **동일한 타깃**이 10번 적용됨 | 한 고정 목표 | **논문 기술과 공개 설정 간 확인 필요** |
| Surrogate | specification별 독립 GP | Matern 5/2 ARD GP, `auto`는 일정 fit 시간 이후 NN 전환 가능 | `surrogate=gp` 고정 | 모델 계열 일치; 모드 차이 여부 확인 |
| Candidate pool | 50,000 | 50,000 / Mapper 3 iter | 50,000 / 3 iter | 기본 설정 **일치** |
| Early stop | 최초 feasible에서 중단 | `run_benchmark.py` early_stop=True | True | **일치** |
| Statistical options | 논문 §4.1에서 글로벌/미스매치 MC 스위치 수치를 직접 고정하지 않음 | PDK dependency / include 설정 필요 | `sw_stat_global=0`, `sw_stat_mismatch=0` | **논문 실행 시 설정 확인 필요** |
| SPICE/PDK 버전 | 오픈소스 GF180MCU, ngspice benchmark (특정 전체 버전 해시 미확인) | README ngspice 44.2 tested | ngspice 44.2, GF180 primitive | 버전 *번호* 유사; model-deck hash 확인 필요 |
| ATLAS 코드 | 발표 당시 실험 코드 | README는 **논문 실험 시 있던 구현 문제 2가지가 이후 수정됨**이라고 명시 | release SHA 고정 | **논문 버전과 완전 동일 재현 불보장** |
| 성공률 및 비용 | TSA **10/10 성공**, FSD **176±101** (성공한 run 기준, 평가횟수) | 결과를 실행해야 확인 가능 | **0/60**, D050은 5/6 통과 | **아직 직접 비교 불가** |

**숫자 주의:** FSD `176±101`은 '최초 feasible까지 소요된 SPICE 평가 수의 평균±표준편차'이며 시간(초)이 아니고, 60회 이전에 모든 run이 성공해야 한다는 뜻도 아니다. 논문의 10/10과 우리의 0/60을 성공률 비교로 해석하지 않는다.

### 3.1. 논문과 공개 저장소의 '10 random targets' 차이

논문 §4.1은 `10 random specification targets (seed=42)`를 기술한다. 그러나 확인한 **고정 commit**의 TSA YAML target들은 모두 `[same, same]`이고, 공개 `run_benchmark.py`의 `sample_spec_targets()`는 동일한 최소·최대 목표에 대해 매 run 같은 스펙을 사용한다. 따라서 **현재 공개 YAML을 그대로 사용한다면 10개 run의 스펙 수치는 동일하며 seed만 달라진다.**

이 차이가 논문 당시 실험 설정의 변화 때문인지, 논문 서술이 전체 벤치마크의 일반 절차를 기술한 것인지, 당시 다른 YAML range를 사용한 것인지는 **확인되지 않았다**. 논문 재현과 공개 코드의 standard-run 재현이 동일하다고 가정하면 안 된다. 명확한 근거(당시 논문용 YAML/config 또는 저자 확인)가 필요하다.

### 3.2. 왜 n_init 1개 차이가 중요할까?

`run_experiment.py`의 `n_init_for()`는 **budget/3 상한**을 둔다.
- 7D, budget=60 → `min(21,20,50)=20` (EXP-003)
- 7D, budget=500 → `min(21,166,50)=21` (논문과 일치)

초기 점 집합이 조금만 달라도 GP posterior → acquisition → 다음 관측값이 변화하므로, seed42와 같은 회로라도 이후 trajectory가 같을 것이라고 예상하면 안 된다. 특히 공개 `_initial_design()`은 YAML `init_params`를 중심으로 일부 local sample을 섞으므로 '전부 단순 임의 LHS'로 설명하면 부정확하다.

### 3.3. 코드를 고정했다는 사실만으로 논문 코드 재현은 아니다

공개 ATLAS README에서 논문 실험 당시 존재했던 두 구현 문제가 release에서 수정되었다고 밝혔다:
1. Mapper node의 거리 좌표계 정규화 문제.
2. Constraint curriculum에서 surrogate의 완화 목표를 실제 feasible 판정과 혼동할 수 있었던 문제.

따라서 **현재 코드가 논문 실험보다 수정된 구현일 수 있다.** 이 차이가 실제 재현 숫자에 어떤 영향을 줬는지는 실행 전에는 모른다. 수정 전 코드를 임의로 복구하거나 현재 코드를 '논문과 반드시 동일'이라고 주장하지 않는다.

## 4. 판정: 지금까지 무엇을 알았나?

**Observation:** EXP-003은 논문과 동일한 TSA 회로/목표값/7D 기반이지만, **60 vs 500 budget**, **20 vs 21 initial samples**, **1 vs 10 runs**, **논문 당시 코드와 현재 release 차이 가능성**이 있다. 현재 공개 YAML의 고정 targets와 논문이 기술한 'random targets'도 별도 확인이 필요하다.

**Interpretation:** EXP-003이 60회에서 feasible을 찾지 못한 것은 논문에서 500회 내 10/10 성공한 결과를 반박하지 않는다. GP holdout의 높은 MAE나 특정 metric 분산 보정만으로 ATLAS 전체의 논문 성과를 기각할 수도 없다.

**Research implication:** Cross-PVT novelty 실험 전에 **기존 ATLAS baseline을 재현하는 작업**이 선행되어야 논문 대비 방법론 차이를 주장할 수 있다. 이 단계는 성공/실패의 근거를 확보하는 baseline QA이며, 새 Novelty 자체는 아니다.

## 5. 다음 실험의 조건(아직 실행 금지)

우선 목적을 두 개로 나눈다.

**Track A — 공개 코드의 표준 기준선 재현(우선):**
- 원본 ATLAS SHA `dd23c5ba7beb598909be593e4a84c81dab92cc69` 유지. 논문용 역사 버전과 동일함은 주장하지 않는다.
- `two_stage_opamp_gf180`, default TT(`pvt=False`), 7D와 공개 YAML에 고정된 여섯 스펙 유지.
- **Budget 500**, `n_init=21`, `seed=42`, `surrogate=gp`를 지정하여 수치 모드를 고정 (논문은 GP 사용). 첫 feasible 시 early stop.
- 1회 실행 후 성공/최초 성공 평가 수, metric, GP/Mapper timing을 확인. 동일 환경에서 다중 seed 실행은 1회 결과와 자원 소요를 검토한 후 결정. **논문 SR 10/10과 비교하려면 같은 프로토콜의 10-run 반복이 필요**.
- 새로운 output 디렉터리/실험 ID; EXP-003/005 raw, ATLAS 원본 소스는 덮어쓰거나 수정하지 않는다.
- 초기 21개와 PDK 모델의 deterministic evaluation이 올바른지 기록한다.

**Track B — 논문 당시 실험 조건의 엄밀 재현(미결):**
- 논문 당시 사용된 **spec target per run**, 당시 코드 SHA/변경 내역, 구체적인 PDK/model hash 및 MC 조건을 증거로 확인해야 한다.
- 논문 당시 설정이 현재 공개 코드와 다르면 수정 내용을 명시적으로 분리한 재현 실험으로 수행한다. 증거 없는 버전/target 범위를 임의로 만들지 않는다.

**환경 확인 스크립트:** [inspect_atlas_environment.py](inspect_atlas_environment.py). ATLAS/PDK 파일의 해시, 실행 가능한 `ngspice` 경로·버전, seed와 YAML 초기점 수·스펙 설정, PDK 스위치를 **읽기 전용**으로 검사한다. 실제 SPICE 평가나 코드 수정은 하지 않는다.

```bash
cd ~/research_intern
git pull --ff-only
conda activate atlas
python docs/reproduction/inspect_atlas_environment.py
```

**새 SPICE 시뮬레이션에 앞서 수행할 정적/로컬 확인(다음 바로 할 일):**
1. WSL의 ATLAS HEAD와 공개 고정 SHA 동일 확인; 로컬 변경 여부 `git status --short`.
2. `ngspice` 실행 바이너리의 절대 경로, `ngspice -v` 버전 및 실제 ATLAS가 호출하는 경로 비교.
3. `PDK_ROOT`와 include chain, GF180 model file SHA256, `sw_stat_global/mismatch` 스위치 0/1 확인; 사용한 PDK가 공식 자료와 얼마나 맞는지 근거 남기기.
4. `two_stage_opamp_gf180.yaml` target/bounds와 `n_init_for(...,500)=21` 확인. 기존 60회 데이터는 그대로 보존.
5. **시뮬레이션 예산 및 저장 경로를 정한 뒤** 독립 재현 Experiment를 만들고 실행. 현재는 500-run을 시작하지 않는다.

## 6. 파일/연구 기록 정책

- 이 파일은 새 SPICE가 없는 **문헌·코드 재현 조건 감사**이므로 `docs/reproduction/`에 보관한다. 아직 EXP-006을 생성하거나 번호를 선점하지 않는다.
- EXP-005는 **Paused after Stage 3B-2**로 명시한다. 측정 실패 데이터/분산 하한의 직접 관측값 및 결과 파일은 삭제하지 않는다.
- 후속 재현을 실제로 시작할 때 별도 `experiments/EXP-xxx_atlas_baseline_reproduction/` 구성: 목적 → config → run scripts → raw → processed → figures → interpretation. 500회 실행 전 input/code/config/model hashes와 출력 경로를 고정.
- **현재 감사의 결론:** 환경 및 소스 설정의 미해결 차이를 분리했을 뿐, 논문의 수치 재현 여부는 아직 결정하지 않았다.
