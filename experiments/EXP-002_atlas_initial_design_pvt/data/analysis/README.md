# EXP-002 Derived Analysis Tables

이 폴더의 CSV는 primary simulation output이 아니라, 다음 두 committed datasets를 결합해 만든 **derived analysis data**다.

```text
EXP-001/data/corner_metrics.csv  → D000
EXP-002/data/corner_metrics.csv  → D001-D019
```

통합 기준:

```text
20 design points × 17 PVT corners = 340 evaluations
```

재생성 스크립트:

```text
../../scripts/analyze_initial_design_pvt.py
```

파일 역할:

- `design_summary.csv`: design별 feasible corner 수와 spec pass 수준
- `corner_summary.csv`: corner별 feasible design 수와 metric별 pass count
- `constraint_failure_summary.csv`: 전체 340 evaluations에서 spec별 fail count / rate
- `worst_corner_frequency.csv`: metric별로 각 corner가 worst가 된 design 수
- `near_feasible_tt.csv`: TT에서 6개 spec 중 5개 이상을 만족한 design

분석 기준 target spec은 EXP-002 `config/run_config.md`와 동일하다.

이 폴더의 값이 primary CSV와 충돌하면 primary simulation dataset과 재생성 스크립트를 기준으로 다시 계산한다.
