# EXP-007 — D292 TT waveform and metric validation

**Status:** Prepared / **SPICE not executed yet** · **Circuit:** GF180 two-stage op-amp · **Design:** EXP-006 D292 · **Condition:** TT, 3.3 V, 27 °C

## Experiment at a Glance

| 항목 | 내용 |
| --- | --- |
| 왜 하는가? | EXP-006이 D292에서 TT 6/6 PASS를 반환했으나 원본 AC/Transient 파형은 ATLAS 실행 직후 삭제됐다. |
| 무엇을 하는가? | EXP-006에서 사용한 D292의 **동일 7D 설계변수**를 고정해 ngspice TT **딱 1회** 재평가한다. |
| 무엇을 확인하는가? | 기존 성능 수치 재현, AC unity crossing/PM 유효성, transient 상승·하강 양쪽의 실제 settling time 추출 여부. |
| 그래서 다음은? | 파형/측정 유효성을 확인한 뒤, 동일 x의 17-corner PVT 평가로 넘어갈지 결정한다. |

## 01. Background & Motivation

[EXP-006](../EXP-006_atlas_release_baseline_reproduction/README.md)의 공개 ATLAS TT baseline에서 293번째 평가 D292가 최초 Feasible이었다. 원본 실행 기록과 CSV는 보존됐지만 **원본 파형은 남아 있지 않다.**

원인 확인: pinned ATLAS `eval_engines/ngspice/ngspice_wrapper_parallel.py`의 `create_design_and_simulate`는 `translate_result(design_folder)` 이후 `shutil.rmtree(design_folder)`로 임시 폴더를 지운다.

따라서 **같은 설계점 한 개만**, 같은 netlist/PDK/조건과 공개 ATLAS extractor로 평가하되 **raw waveform을 보존**한다. 처음부터 293회를 반복하지 않는다.

## 02. Research Question & Hypothesis

- **RQ:** D292의 TT 6개 성능값은 동일 환경에서 재현되고, 특히 PM·UGBW·Settling은 유효한 파형에서 추출되는가?
- **Working hypothesis:** 환경과 설계점이 동일하고 MC global/mismatch가 OFF이면 기존 수치에 가깝게 재현된다.
- **Decision rule:**
  - 6개 수치/Feasible 판단이 같고 AC unity-crossing과 양쪽 step settling이 유효하며 파형을 시각적으로 확인하면, TT measured-feasible 근거가 강화된다.
  - 수치가 다르면 netlist/PDK/환경/hash, simulator 로그, 파형 및 extractor 계산을 조사한다.
  - 동일 수치가 나오더라도 transient fallback 또는 의심스러운 waveform이면 **physically verified**로 분류하지 않는다.

## 03. Experimental Setup

- Reference EXP-006 run: `raw/runs/release_B500_S42_20261010_033242_863546/`
- Source: reference trajectory 293행, SHA256 `2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34`.
- Frozen 7D (native SI): wp1 `2.249e-6` m, wn1 `3.433e-6` m, wp3 `8.4329e-5` m, wn3 `9.656e-6` m, wn4 `1.1757e-5` m, wn5 `8.8097e-5` m, cc `9.775e-13` F.
- TT, 3.3 V, 27 °C; 1 design only. **No GP, BO, TDA or new candidate selection**.
- Public ATLAS pinned commit `dd23c5ba7beb598909be593e4a84c81dab92cc69`; `ngspice` 44.2, GF180 PDK SHA verification via EXP-006 preflight; nominal `sw_stat_global=0`, `sw_stat_mismatch=0`.
- Existing design/spec targets and extraction formulas are unchanged. Netlist generation uses pinned `NgSpiceWrapper.create_design`; ngspice command and 120s timeout match pinned wrapper; `CircuitClass.translate_result` retains released metric definitions.

## 04. Method & Procedure

1. **Read-only preflight:**
   ```bash
   cd ~/research_intern
   conda activate atlas
   python experiments/EXP-007_d292_tt_waveform_validation/scripts/verify_d292_tt.py
   ```
   Verifies original trajectory SHA, D292 parameters, pinned ATLAS hash, ngspice/PDK hashes, and MC switches; no SPICE/no file writes.
2. **One new SPICE evaluation, with explicit authorization:**
   ```bash
   python experiments/EXP-007_d292_tt_waveform_validation/scripts/verify_d292_tt.py --execute
   ```
   Creates **new timestamped directory** under `raw/runs/d292_tt_<timestamp>/`. Original EXP-006 run is never edited; previous validation attempts are never overwritten.
3. Inspect the newly generated `validation_summary.json`, ngspice stdout/stderr, complete generated .cir file, and **ac.csv, dc.csv, dc_sweep.csv, tran.csv**.
4. Plot gain/phase Bode and Vin/Vout transient from preserved CSV. Check actual crossing and settling threshold before final interpretation.
5. Only after review, preserve important run-specific raw files under an identified `raw/` archive folder, derived datasets under `data/`, statistics under `data/analysis/`, and generated plots under `figures/` as appropriate; document provenance and outcome.

## 05. Metrics & Evaluation Criteria

| Metric | Bound | EXP-006 D292 extracted result |
| --- | ---: | ---: |
| Gain | >= 300 | 396.72 |
| Ibias | <= 0.001 A | 0.00085909745 A |
| PM | >= 60° | 62.0557101° |
| Settling | <= 6 µs | 1.77803 µs |
| UGBW | >= 20 MHz | 20.6937696 MHz |
| Swing | >= 0.3 V | 0.461981 V |

- **AC:** Verify unity-gain crossing exists; PM/UGBW are not `-180° / 1 Hz` sentinel substitutes; review Bode curve.
- **Transient:** Verify both rising and falling edges return finite settling times. Original extractor may substitute dimensionless `d_settle` when any edge fails. Do not confuse this with seconds.
- **Numerical reproducibility:** report signed difference and relative difference for each measured metric. Do not invent pass/fail tolerance without looking at numerical precision and waveform.

## 06. Results & Figures

**Pending: not executed.** Planned output: per-run `validation_summary.json`, `design_parameters.json`, `environment_preflight.json`, generated .cir, four raw CSVs, and `ngspice_stdout.log`/`ngspice_stderr.log`. Follow-on figures: AC gain/phase, transient Vin/Vout, settling threshold annotations.

## 07. Discussion

**Observation:** No EXP-007 simulation result yet. Source ATLAS cleanup logic was inspected.

**Interpretation:** EXP-006 result being archived without waveforms is expected from pinned wrapper cleanup, not evidence that ngspice failed.

**Research implication:** Only reliable TT waveform evidence justifies using D292 as a cross-PVT design benchmark.

## 08. Limitations & Issues

- One-point TT replication is **not** an independent statistical evaluation of ATLAS success rate.
- The validation script records whether both edges returned a finite settling time, but a complete waveform/threshold and simulator-convergence review is still required.
- The raw SPICE logs/CSVs should be reviewed before being committed; bulk outputs should not be pushed automatically.
- Any error should leave the run folder for debugging, not overwrite original experiments.

## 09. Conclusion & Next Experiment

**Prepared; no new SPICE run yet.** After waveforms and metrics are checked, evaluate the **same fixed D292** in the 17 configured PVT corners, retaining corner identity and extraction validity.
