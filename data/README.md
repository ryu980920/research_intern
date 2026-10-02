# Data Management

## raw/

시뮬레이터나 원본 소스에서 직접 얻은 **가공 전 데이터**를 저장합니다.

원본 데이터는 가능하면 수정하지 않습니다.

## processed/

raw data에서 metric 추출, 정리, 필터링, 계산 등을 수행한 **분석용 데이터**를 저장합니다.

## Principles

- figure만 남기지 말고 가능한 경우 figure의 원본 CSV도 보존합니다.
- 파일만 보고도 조건을 구분할 수 있도록 일관된 이름을 사용합니다.
- 어떤 processed data가 어떤 raw data와 script에서 생성됐는지 추적 가능하게 합니다.
- 대용량 SPICE raw 파일은 GitHub에 무조건 올리지 않습니다.
- 외부에 보관한다면 저장 위치, 생성 조건, 필요한 요약 데이터를 README 또는 Experiment 문서에 기록합니다.
