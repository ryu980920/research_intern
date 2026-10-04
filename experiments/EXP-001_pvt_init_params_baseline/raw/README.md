# Raw Data Status

EXP-001은 17-corner metric CSV를 정상적으로 생성했지만, 각 corner의 ngspice raw output은 보존하지 못했다.

각 corner simulation은 내부적으로 다음 파일을 생성한다.

- `ac.csv`
- `dc.csv`
- `dc_sweep.csv`
- `tran.csv`

17 corners이므로 한 design point에 대해 최대 68개의 raw CSV가 생성된다.

현재 ATLAS wrapper는 metric을 추출한 뒤 temporary design directory를 삭제하므로 이 최초 실행의 68개 raw CSV는 남아 있지 않다.

이 사실을 숨기지 않고 EXP-001의 limitation으로 기록한다. 다음 PVT dataset부터는 raw output을 보존하도록 실행 경로를 수정한 뒤 수집한다.
