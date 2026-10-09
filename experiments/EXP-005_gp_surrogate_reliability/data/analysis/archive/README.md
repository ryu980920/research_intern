# EXP-005 analyzed outputs — uploaded-evidence archive

This folder contains **exact byte-preserved copies** of CSV/JSON artifacts
uploaded by the researcher from completed WSL runs. They are located here
instead of the scripts' default `../` output directory to **avoid Git pull
collisions with already existing untracked local WSL results**.

## Files preserved

| File | Role | SHA256 (uploaded bytes) |
| --- | --- | --- |
| [gp_baseline_holdout_predictions.csv](gp_baseline_holdout_predictions.csv) | Stage 2; 20 designs × 6 specs = 120 prediction rows, original ATLAS GP | `6a342e0aea5249bcb444cec67eb4d85b06ad50900b85746e541506370eecee72` |
| [validity_aware_gp_comparison.csv](validity_aware_gp_comparison.csv) | Stage 3A; matched 19 designs × 3 specs = 57 A/B prediction rows | `d7e049c5aa689cf080c4ae988b99b2d567b202aca8a5629553050413e8f0a0c1` |
| [validity_aware_gp_summary.json](validity_aware_gp_summary.json) | Stage 3A; MAE/RMSE/hit rate, metric-specific masks and fit diagnostics | `602d4bf241f94d594a1c15374dbd9b2d6facad7275e49c152d9bc0257ca6ab6f` |

All metrics originate from EXP-003 historical [`raw/trajectory.csv`](../../../EXP-003_tt_adaptive_feasible_discovery/raw/trajectory.csv).
Underlying raw trajectory SHA256: `46688d66b66d41e3f485cfeb1a6e152105dd60ae91e3d89a192a53ac648d5ba3`.
Pinned ATLAS commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`.

The Stage-3A summary JSON also records hashes of its locally generated
prerequisite artifacts:
- Stage 2 baseline summary JSON: `d834795a96ef513307282bddc72aead270669ba780bec91eb341622318d4e897`
- Stage 2b metric semantics audit JSON: `9aab242abc1b9be8a1dc30b0252a20f4ba7bc3179b05aae1177109b24d5ef65f`
- Stage 2b metric semantics flags CSV: `9f5972cf7600d6715c39c4fc673ed644a2e2096295d95556d8421fcba9c620cc`

**Those three prerequisite files were generated locally but were not provided
for this GitHub archiving step.** Their source code, observed counts, and run
commands are in [EXP-005 README](../../../README.md) and
[2026-10-10 research log](../../../../../logs/2026-10/2026-10-10.md).
Do not represent them as already archived.

## Reproducing from local WSL

From `~/research_intern` with `(atlas)` active:
```bash
python experiments/EXP-005_gp_surrogate_reliability/scripts/audit_tt_dataset.py
python experiments/EXP-005_gp_surrogate_reliability/scripts/evaluate_gp_baseline.py
python experiments/EXP-005_gp_surrogate_reliability/scripts/diagnose_metric_semantics.py
python experiments/EXP-005_gp_surrogate_reliability/scripts/compare_validity_aware_gp.py
```

**Note:** These scripts use exclusive-create file outputs. Do not rerun a stage
when its local outputs already exist, unless setting up a separate clean
analysis working directory/run. Do not overwrite research records just to
reproduce them.

These are **derived GP predictions and summaries**, not additional SPICE
observations or raw waveform. Never treat unexplained fallback values as
measured seconds.
