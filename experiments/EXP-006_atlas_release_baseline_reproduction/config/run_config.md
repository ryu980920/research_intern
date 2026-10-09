# EXP-006 — Pinned Configuration (Prepared, NOT run)

## Identity

- Experiment: `EXP-006_atlas_release_baseline_reproduction`
- Research status: code prepared / no new SPICE yet
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

## Evidence linking

```text
code + source SHA → environment_preflight.json → parameters/conditions
→ raw/runs/<id>/trajectory.csv → raw/runs/<id>/atlas_logs/<ATLAS_run_id>/
→ raw/runs/<id>/data/{design_points.csv,corner_metrics.csv}
→ raw/runs/<id>/reproduction_summary.json → EXP-006 README interpretation
```

No simulation has yet been performed for EXP-006. Do not fill first-feasible counts, design coordinates, timing, or figures until real output files exist.
