# EXP-006 Original ATLAS Run Logs — Recovered 2026-10-25

**Original WSL directory:** `/home/ryu98/research_intern/experiments/EXP-006_atlas_release_baseline_reproduction/raw/runs/release_B500_S42_20261010_033242_863546/atlas_logs/two_stage_opamp_gf180_ATLAS_B500_S42_20261010_033242/`

**Run identity:** `two_stage_opamp_gf180_ATLAS_B500_S42_20261010_033242` · budget 500 · seed 42 · initial 21 · evaluated 293 TT designs · first feasible zero-based iteration 292 (D292).

## User-uploaded originals (bytes preserved)

| Path | Size | SHA-256 |
| --- | ---: | --- |
| `config.json` | 712 bytes | `f78cd70c8d11ac317f5e96fa55ef19efa2ac9bb63368268f37f773320d971a04` |
| `iterations.jsonl` | 111,277 bytes | `5d2284690bf1cf0357c60ef51e1abc54dec8257139502dc5ee1c9c4e4b51ad91` |

`iterations.jsonl` has 293 valid JSON lines with 0-based indices 0...292. The original trajectory SHA-256 is `2e5827b2cb812f75f5ee307506385945acdbc7ec40395a558dad5c11855fab34`; the original trajectory is separately archived at [2026-10-10_uploaded_trajectory.csv](../2026-10-10_uploaded_trajectory.csv).

## Original files still on WSL, not yet archived on GitHub

- `environment_preflight.json` — execution environment and model hashes
- `reproduction_summary.json` — wrapper summary, recorded evaluations
- `atlas_logs/<run_id>/results.json` — ATLAS's native final result
- `atlas_logs/<run_id>/progress.log` — chronological process log

These files should be copied from their actual original WSL bytes rather than reconstructed from conversation text. Existing EXP-006 run outputs must not be overwritten.

## Validation boundary

EXP-006's extracted TT `success=True` has been confirmed from logs and trajectory, but its AC/transient waveforms are no longer present; the pinned ATLAS wrapper deletes per-design temporary folders after extraction. D292 waveform/metric confirmation is a separate [EXP-007](../../../../EXP-007_d292_tt_waveform_validation/README.md) and has **not** been executed yet.
