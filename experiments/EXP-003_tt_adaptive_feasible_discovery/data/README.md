# EXP-003 — Data Dictionary and Provenance

## Source

- Source: user-provided `trajectory.csv`, recorded by `run_adaptive_tt_search.py` during the EXP-003 local TT optimization run
- Run: `ATLAS / TopoBO`, GF180 two-stage op-amp; seed `42`, GP surrogate, budget `60`, initial points `20`
- Analysis condition: `TT_3.3V_27C` (3.3 V, 27 °C), 17-corner PVT evaluation was **not** performed in EXP-003
- Statistical variation: `sw_stat_global=0`, `sw_stat_mismatch=0` (nominal TT; not Monte Carlo)
- ATLAS pinned commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- Source design count: 60 points (D000–D059); 20 initial / 40 adaptive
- Reported TT feasible: 0 / 60
- Cross-check: D000–D019 values and TT results matched the EXP-001 / EXP-002 committed baseline files

## Data files

| File | Rows | Fields / role |
| --- | ---: | --- |
| `trajectory.csv` | 60 | Original combined iteration-level records provided by the user; 7 parameters, 6 metrics, feasibility and violation measures |
| `design_points.csv` | 60 | Exactly one record per `design_id`; only 7 physical design parameters, matching the EXP-001/002 design_points schema |
| `corner_metrics.csv` | 60 | Exactly one record per `design_id` and `corner`; 6 measured metrics + feasibility and iteration/phase/constraint-margin metadata |

Join key: `design_id`. All EXP-003 metric rows use `corner=TT_3.3V_27C`. Do not interpret these as 60×17 PVT results.

## Column definition

- `wp1, wn1, wp3, wn3, wn4, wn5`: transistor widths in meters
- `cc`: compensation capacitor in farads
- `gain_min`: DC gain (dimensionless as returned by the evaluator)
- `ibias_max`: bias current in amperes
- `phm_min`: phase margin in degrees
- `t_settle_max`: settling time in seconds
- `ugbw_min`: unity-gain bandwidth in hertz
- `vswing_min`: output swing metric in volts
- `feasible`: whether **one design** satisfies all 6 original TT target constraints simultaneously
- `iteration`: 0-based evaluation index
- `phase`: `init` for D000–D019 and `adaptive` for D020–D059
- `n_specs_passed`: number of the 6 original constraints satisfied
- `worst_margin`: minimum normalized constraint margin across 6 specs
- `total_violation`: sum of negative normalized margins' absolute values

Targets: gain >= 300, bias current <= 0.001 A, phase margin >= 60°, settling time <= 6e-6 s, UGBW >= 20e6 Hz, swing >= 0.3 V.

For a lower-bound spec, `margin = (measured-target)/target`; for an upper-bound spec, `margin = (target-measured)/target`. `worst_margin >= 0` is equivalent to meeting all constraints, assuming valid finite measurements.

## Observation and limitation

- Observed 0 feasible / 60, so this run does **not** establish any actual TT feasible island or 17-corner robustness.
- D050 has the best observed `worst_margin` and lowest `total_violation` within the recorded run. This is a promising near-boundary candidate, **not** a feasible design.
- Some records contain sentinel-like or anomalous values (e.g. UGBW=1 Hz, PM=-180°). Check waveform/evaluator extraction before interpreting them physically.
- The uploaded source does not contain ATLAS native `iterations.jsonl`, `run_summary.json`, per-analysis SPICE raw waveforms or full PVT results; those have **not** been fabricated.
- These files preserve the EXP-003 measured trajectory. The separate multi-island discovery and cross-PVT experiments have not been run here.
