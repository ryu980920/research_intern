# EXP-006 — 사용자 제공 원본 데이터 보관

## 2026-10-10 trajectory 업로드

- **원본 제출 파일명:** `trajectory(1).csv` (사용자 제공)
- **보관 경로:** [2026-10-10_uploaded_trajectory.csv](2026-10-10_uploaded_trajectory.csv)
- **SHA-256 (원본 업로드 파일):** `2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34`
- **크기 / 인코딩:** 71,793 bytes, ASCII-compatible UTF-8 text, **CRLF**. 업로드 파일과 GitHub 저장본의 텍스트/줄바꿈/길이가 정확히 일치함을 재조회로 확인.
- **수집 범위:** `iteration=0..292`, `D000..D292`, 293개 설계점, 21 init + 272 adaptive, `D292`가 첫 `feasible=True`(원본 성능 추출값 기준).
- **사용자가 제출하지 않은 별도 출력:** `atlas_logs/`의 `iterations.jsonl`, `config.json`, `progress.log`, `results.json`, 실행 폴더의 `environment_preflight.json`, `reproduction_summary.json`, 개별 waveform.
- **원본 위치에 관한 한계:** CSV 자체에는 wrapper가 생성한 `raw/runs/<run_id>` ID가 없으므로 **특정 실행 폴더를 추측하지 않고** `raw/received/`에 별도 보관한다. `raw/runs/<run_id>`가 업로드됐다고 주장하지 않는다.
- **가공 데이터:** [../.. /data/analysis/2026-10-10_trajectory_summary.json](../../data/analysis/2026-10-10_trajectory_summary.json)
- **분석 / 판단:** [EXP-006 README](../../README.md).

> **데이터 해석:** 293번째 평가에서 '기록된 여섯 성능 수치 기준' 최초 Feasible을 찾았다. D292의 출력 파형과 SPICE 성능 추출 성공 여부는 별도로 검증해야 한다. 원본 CSV는 수정하지 않는다.
