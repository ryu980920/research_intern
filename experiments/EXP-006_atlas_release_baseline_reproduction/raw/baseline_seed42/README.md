# EXP-006 — ATLAS 기준선 실험 원본 데이터 (Seed 42)

이 폴더는 **EXP-006의 동일한 실행에서 생성된 원본 데이터**를 모아 보존하는 곳이다. 사용자가 전달한 파일을 분석하거나 값을 수정하지 않고 원본 그대로 저장했다.

이 폴더는 **GitHub에 보관한 원본 자료의 위치**이며, WSL에서 시뮬레이션이 실제로 수행된 폴더와는 구분한다.

## 1. 실험 정보 및 원본 출처

| 항목 | 내용 |
| --- | --- |
| 실험 | EXP-006 — 공개 ATLAS 코드의 TT 기준선 재현 |
| 회로 | GF180 기반 Two-stage Op-amp |
| PVT 조건 | TT, 3.3 V, 27 °C |
| 최적화 방법 | ATLAS, GP Surrogate |
| Random Seed | 42 |
| 최대 평가 예산 | 500개 설계점 |
| 초기 설계점 | 21개 |
| 실제 평가한 설계점 | 293개 |
| 최초 Feasible 설계점 | D292 (0부터 시작하는 iteration 292, 실제 293번째 평가) |
| 종료 방식 | 최초 Feasible 발견 후 조기 종료 |

- **원본 ATLAS 실행 ID:** `two_stage_opamp_gf180_ATLAS_B500_S42_20261010_033242`
- **원본 WSL 실행 폴더:** `/home/ryu98/research_intern/experiments/EXP-006_atlas_release_baseline_reproduction/raw/runs/release_B500_S42_20261010_033242_863546/`

## 2. GitHub에 보존한 원본 파일

| 파일 | 사용자가 전달한 파일명 | 크기 | 역할 |
| --- | --- | ---: | --- |
| [trajectory.csv](trajectory.csv) | `trajectory(1).csv` | 71,793 bytes | 293개 설계점의 파라미터, 추출 성능, Feasible 판정 기록 |
| [config.json](config.json) | `config.json` | 712 bytes | ATLAS 실행 설정, 설계변수, 제약조건 |
| [iterations.jsonl](iterations.jsonl) | `iterations(2).jsonl` | 111,277 bytes | 각 반복의 결과 및 탐색 과정 기록 |

### 원본 데이터 무결성 검증

원본 파일을 다른 경로로 이동하면서 내용을 변경하지 않았는지 확인하기 위해 SHA-256 해시를 보존했다.

| 파일 | SHA-256 |
| --- | --- |
| `trajectory.csv` | `2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34` |
| `config.json` | `f78cd70c8d11ac317f5e96fa55ef19efa2ac9bb63368268f37f773320d971a04` |
| `iterations.jsonl` | `5d2284690bf1cf0357c60ef51e1abc54dec8257139502dc5ee1c9c4e4b51ad91` |

GitHub 폴더를 정리할 때 **기존 파일의 Git Blob SHA를 그대로 사용하여 이동**했기 때문에, 원본 파일 내용과 줄바꿈 방식(`trajectory.csv`의 CRLF 포함)은 변경되지 않았다. WSL의 원본 실행 폴더도 수정하지 않았다.

## 3. 아직 GitHub에 보존하지 않은 실행 원본

다음 파일은 사용자의 WSL 실행 폴더에서 존재 여부를 확인했지만, 아직 GitHub에는 업로드하지 않았다.

| 파일 | 역할 |
| --- | --- |
| `environment_preflight.json` | 사용한 ATLAS·ngspice·PDK 환경 및 해시 확인 |
| `reproduction_summary.json` | 전체 실행 결과와 데이터 무결성 요약 |
| `atlas_logs/<run_id>/results.json` | ATLAS가 기록한 최종 성공 여부 및 실행 시간 |
| `atlas_logs/<run_id>/progress.log` | 실행 과정의 진행 기록과 메시지 |

이 파일들은 채팅에 나타난 수치로 새로 만들지 않고, **WSL에 저장된 실제 원본을 그대로 가져와 보존**해야 한다.

## 4. 원본 데이터와 분석 데이터의 구분

이 실험에서는 다음 기준으로 파일을 관리한다.

| 위치 | 저장 대상 |
| --- | --- |
| **`raw/baseline_seed42/` (현재 폴더)** | ATLAS 실행 당시 생성된 원본 기록 |
| [`data/design_points.csv`](../../data/design_points.csv) | 원본에서 추출한 설계점별 7개 설계변수 |
| [`data/corner_metrics.csv`](../../data/corner_metrics.csv) | 원본에서 추출한 TT 조건의 6개 성능값과 Feasible 판정 |
| [`data/analysis/`](../../data/analysis/) | Feasible 개수, 제약조건 충족 여부 등의 가공·집계 결과 |
| `figures/` | 실제 분석으로 생성한 그래프 (현재 생성 전) |

즉, **원본 기록 → 표준 데이터 → 분석 결과 → 그래프** 순서로 연구 결과를 추적할 수 있도록 관리한다.

## 5. 현재 검증 범위와 한계

EXP-006에서는 ATLAS가 **D292를 최초 TT Feasible 설계점**으로 판정했고, 원본 CSV와 실행 요약 기록의 결과가 일치함을 확인했다.

다만 ATLAS 원본 코드가 성능값 추출 후 설계점별 임시 폴더를 삭제하므로, 당시 D292의 AC·Transient 원본 파형은 남아 있지 않다.

따라서 이 결과는 **ATLAS가 추출한 여섯 성능 수치 기준의 TT Feasible**을 의미하며, 실제 파형을 독립적으로 검증했다는 뜻은 아니다. 또한 17개 PVT 코너 전체에서 강건하다는 뜻도 아니다.

- **후속 실험:** [EXP-007 — D292 TT 파형 및 성능 추출 검증](../../../EXP-007_d292_tt_waveform_validation/README.md)
- **EXP-007의 목적:** D292 한 점만 TT 조건에서 재시뮬레이션하여 AC·Transient 파형을 보존하고, 기존 성능 수치가 타당하게 추출됐는지 확인한다.
