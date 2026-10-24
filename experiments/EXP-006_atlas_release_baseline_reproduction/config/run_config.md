# EXP-006 — Pinned Configuration (executed; trajectory received)

## Identity

- Experiment: `EXP-006_atlas_release_baseline_reproduction`
- Research status: first feasible confirmed from 293-row uploaded trajectory on 2026-10-10; full ATLAS original execution logs not yet received
- Scope: released-code TSA TT baseline, not paper-era exact reproduction
- ATLAS SHA: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- Repository: `ryu980920/research_intern`; pinned ATLAS: `~/atlas`
- Simulation root: GF180 TSA YAML, `pvt=False`
- `PDK_ROOT`: `~/pdks`

## Locked run values

```yaml
circuit: two_stage_opamp_gf180
method: ATLAS
surrogate: gp
seed: 42
budget: 500
n_init: 21
pvt: false
early_stop_on_first_feasible: true
target_spec_mode: fixed_public_yaml
candidate_pool: 50000
gp_time_limit_s: 10.0  # ignored for gp-pinned switching; retained as original API arg
statistical_switches:
  sw_stat_global: 0
  sw_stat_mismatch: 0
```

- Width bounds: six `[0.5e-6, 100e-6]` (m); `cc=[1e-13,1e-11]` (F).
- Targets: `gain_min≥300`, `phm_min≥60°`, `ugbw_min≥2e7 Hz`, `vswing_min≥0.3 V`, `ibias_max≤1e-3 A`, `t_settle_max≤6e-6 s`.
- n_init formula from pinned ATLAS runner: `max(min(3 * d, budget // 3, 50), 10)`, d=7, budget=500 → **21**.
- Initial design uses pinned ATLAS `_initial_design` (YAML `init_params` reference + local/global samples); no manual new starting points.
- Run-time directory per execution: `raw/runs/release_B500_S42_<timestamp_microseconds>/`; no overwrite. Observations saved in `trajectory.csv` with original measured units and `0-based` iteration.
- `--execute` explicitly required to start ngspice evaluations. Default execution is a read-only environment check.
- Source changes: **prohibited**; wrapper only records `CircuitEvaluator.evaluate(x)` return values and preserves original optimizer choices. Original ATLAS logs are captured independently.
- `ngspice`: pinned installed version 44.2 currently `/usr/local/bin/ngspice`; version/path verified again by preflight. No claim about ngspice loading `netlist/.spiceinit`.
- 3 PDK hash values pinned by preflight, see [script](../scripts/run_release_baseline.py) and [reproduction audit](../../../docs/reproduction/ATLAS_ICCAD2026_vs_EXP003_audit.md).

## Failed measurement labels — baseline fidelity policy

**Decision (before any EXP-006 SPICE run):** Preserve the **released ATLAS** GP training pathway without manual filtering. This is a *baseline reproduction control*, **not** a claim that fallback labels are statistically or physically ideal.

- `CircuitEvaluator.evaluate(x)`의 TT metric dict를 원형 그대로 `TopoBO.optimize()`과 `GPSurrogate.fit()`에 전달한다. Settling의 `d_settle` 대체값이나 PM=-180°/UGBW=1 Hz sentinel에 별도 마스킹·재단위화·보정·제거를 적용하지 않는다.
- 고정 ATLAS `topbo/gp_model.py`의 `fit()`: `y_clean = np.nan_to_num(y, nan=0.0)` 뒤 `SingleTaskGP`로 모든 metric을 학습한다. 이 코드의 `nan=0.0` 처리도 그대로 보존한다. 원본 주석 `# Replace NaN with worst-case values`와 실제 구현이 일치하지 않으므로, 이를 'worst-case 대체'라고 기술하지 않는다.
- Wrapper의 per-design `trajectory.csv`에 6개 원시 반환값과 `feasible`, `n_specs_passed`, normalized margin을 보존한다. **이 CSV만으로 모든 추출기의 성공 flag가 기록되는 것은 아니다.** PM=-180/UGBW=1Hz 짝 또는 transient horizon 초과와 같은 *알려진 확정 신호*만 분석 단계에서 별도 플래그 가능하며, 정상이었다는 보증은 아님.
- 실험 중 첫 `feasible=True`를 만나면 공개 ATLAS 원래 규칙대로 early stop한다. 그 뒤 해당 설계점의 waveform/추출 유효성을 검증한 경우에만 **physically verified feasible**라고 표현한다. 추출 실패 대체값을 물리적 settling time으로 받아들이지 않는다.
- 이후 `validity-aware surrogate` 방법을 시험하려면 **독립적인 후속 실험**, 동일 SPICE budget/seed/PDK/목표 spec과 선택 후보 이력의 차이를 기록한다. '기존 500개 평가점을 다시 GP에 학습'하는 것은 **fixed-dataset 후향 분석**이지 적응형 optimizer의 탐색 성공률 개선을 검증하는 실험이 아니다.
- EXP-005에서 사용한 failure-label exclusion은 diagnostic GP 학습 비교로 보존하고, **EXP-006 baseline의 원본 학습 규칙에 역으로 적용하지 않는다**.

## Evidence linking

```text
code + source SHA → environment_preflight.json → parameters/conditions
→ raw/runs/<id>/trajectory.csv → raw/runs/<id>/atlas_logs/<ATLAS_run_id>/
→ raw/runs/<id>/data/{design_points.csv,corner_metrics.csv}
→ raw/runs/<id>/reproduction_summary.json → EXP-006 README interpretation
```

No simulation has yet been performed for EXP-006. Do not fill first-feasible counts, design coordinates, timing, or figures until real output files exist.

## Post-run evidence — 2026-10-10 (do not retroactively modify pinned settings)

- Original user-uploaded CSV: [raw/received/2026-10-10_uploaded_trajectory.csv](../raw/baseline_seed42/trajectory.csv), exactly preserved including CRLF.
- SHA-256: `2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34`.
- 293 design evaluations, 21 initial + 272 adaptive. First feasible design at zero-based iteration 292, **293rd evaluation**, ID D292.
- Extracted SPICE specifications for D292: gain 396.72; phase margin 62.0557 deg; UGBW 20.69377 MHz; Ibias 0.859097 mA; settling 1.77803 us; swing 0.461981 V.
- User provided a standalone `trajectory(1).csv` without the originating `raw/runs/<run_id>` name, `atlas_logs`, wrapper summary or original waveforms. Run-level log timings and full process completion cannot be separately certified yet.
- Data validation performed: 293 sequential indices and unique parameter tuples; six target pass flags, pass counts and worst margins independently recomputed for all rows with zero mismatches.
- **Paper comparison:** this is one run of current released ATLAS with fixed TSA targets; not an exact replication of paper-era 10-run statistics. Do not conflate.
- **Next day:** check D292 raw AC/transient waveforms and missing original run metadata before any PVT or extra seed benchmarking.

## 2026-10-25 GitHub archive reorganization

- Keep original WSL execution directory `raw/runs/release_B500_S42_20261010_033242_863546/` unchanged.
- In the repository, uploaded original `trajectory.csv`, `config.json` and `iterations.jsonl` are now grouped in [`raw/baseline_seed42/`](../raw/baseline_seed42/). Source bytes remain unchanged.
- [`data/design_points.csv`](../data/design_points.csv) and [`data/corner_metrics.csv`](../data/corner_metrics.csv) are transformed standard tables; [`data/analysis/`](../data/analysis/) contains derived summaries.
- Some earlier paragraphs document the original upload state as of 2026-10-10. Later recovery established the local run identity and original logs; see [EXP-006 README](../README.md).
