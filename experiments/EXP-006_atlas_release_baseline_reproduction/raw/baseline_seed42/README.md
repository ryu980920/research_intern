# EXP-006 — Baseline ATLAS seed42 raw records

This directory groups the **unaltered original output files** from the same EXP-006 run. Files were supplied as uploads and verified against the GitHub byte content before this directory reorganization. This is a **GitHub archive**, not the on-machine execution directory.

## Source provenance

- Original WSL execution folder: `/home/ryu98/research_intern/experiments/EXP-006_atlas_release_baseline_reproduction/raw/runs/release_B500_S42_20261010_033242_863546/`.
- ATLAS run ID: `two_stage_opamp_gf180_ATLAS_B500_S42_20261010_033242`.
- Experiment: GF180 two-stage op-amp, TT 3.3 V / 27 °C, ATLAS GP, seed 42, budget 500, initial 21, early-stop.
- 293 actual design evaluations, first extracted-metric feasible design D292 (zero-based iteration 292).

## Original files already archived here

| File | Original upload | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [trajectory.csv](trajectory.csv) | `trajectory(1).csv` | 71,793 | `2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34` |
| [config.json](config.json) | `config.json` | 712 | `f78cd70c8d11ac317f5e96fa55ef19efa2ac9bb63368268f37f773320d971a04` |
| [iterations.jsonl](iterations.jsonl) | `iterations(2).jsonl` | 111,277 | `5d2284690bf1cf0357c60ef51e1abc54dec8257139502dc5ee1c9c4e4b51ad91` |

**Integrity:** Files were moved by reusing their existing Git blob SHAs, keeping the bytes, including the trajectory's CRLF line endings, unchanged. The GitHub archive's paths are consolidated; the original WSL run folder remains untouched.

## Remaining original WSL outputs (not yet archived)

- `environment_preflight.json` (environment and PDK hashes)
- `reproduction_summary.json` (wrapper-run summary)
- `atlas_logs/<run_id>/results.json` (ATLAS final results)
- `atlas_logs/<run_id>/progress.log` (run chronology)

These four files must be copied from the original WSL location, not fabricated or replaced with values reconstructed from conversation.

## Raw vs processed

- Original input/outputs: **this `raw/baseline_seed42/`**.
- Standardized observation tables: [`data/design_points.csv`](../../data/design_points.csv), [`data/corner_metrics.csv`](../../data/corner_metrics.csv).
- Derived statistical summaries: [`data/analysis/`](../../data/analysis/).
- Figures: `figures/` only once actual charts have been generated.

**Limitation:** The raw waveforms were deleted by the upstream ATLAS simulator wrapper after extraction; `success=true` is an extracted-metric TT success, **not yet an independently waveform-verified feasible result**. See [EXP-007](../../../EXP-007_d292_tt_waveform_validation/README.md).
