# EXP-004 Configuration — Warm-start smoke only

| Item | Value |
| --- | --- |
| Circuit | GF180 two-stage opamp |
| PVT | TT 3.3 V, 27 °C |
| EXP-003 source | `experiments/EXP-003_tt_adaptive_feasible_discovery/raw/trajectory.csv` |
| Historical observations | **60** (D000–D059; no SPICE re-simulation) |
| New SPICE budget | **1** (D060 only) |
| ATLAS internal args | `n_init=60`, `budget=61`, `seed=42`, `surrogate='gp'`, `early_stop=True` |
| Fixed ATLAS SHA | `dd23c5ba7beb598909be593e4a84c81dab92cc69` |
| Statistical controls | `sw_stat_global=0`, `sw_stat_mismatch=0` |
| Main script | `scripts/run_warmstart_smoke.py` |

**Important:** `budget=61` counts 60 historical observations plus **one new TT SPICE evaluation**, not 61 new SPICE calls.

This script is an observation-based warm start via cached evaluator replay, **not** an exact restored ATLAS checkpoint. The pinned ATLAS code remains unchanged.

Test sequence: `--check-only` (source data) → `--dry-run` (actual GP fit + candidate proposal, zero new SPICE) → no flags (one new SPICE call). Existing results must not be overwritten.
