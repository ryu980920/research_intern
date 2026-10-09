#!/usr/bin/env python3
"""EXP-005 Stage 2b: inspect op-amp metric extraction semantics; NO SPICE/GP.

Analyze source code + 60 historical TT metrics. Distinguish unmistakable
sentinel/fallback cases from merely unusual physical measurements. This
script never modifies the historical trajectory or its extracted metrics.

From ~/research_intern:
  python experiments/EXP-005_gp_surrogate_reliability/scripts/diagnose_metric_semantics.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from audit_tt_dataset import EXP_DIR, read_source

EXPECTED_ATLAS_SHA = "dd23c5ba7beb598909be593e4a84c81dab92cc69"
ATLAS_ROOT = Path(os.environ.get("ATLAS_ROOT", "~/atlas")).expanduser().resolve()
EXTRACTOR = ATLAS_ROOT / "eval_engines/ngspice/CircuitClass.py"
NETLIST = (ATLAS_ROOT / "eval_engines/ngspice/ngspice_inputs/netlist" /
           "two_stage_opamp_cont_gf180_tran_tt_3.3_27.cir")
OUTDIR = EXP_DIR / "data" / "analysis"
OUTPUT_JSON = OUTDIR / "metric_semantics_audit.json"
OUTPUT_CSV = OUTDIR / "metric_semantics_flags.csv"


def sha256(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def get_codes_and_horizons():
    sha = subprocess.check_output(
        ["git", "-C", str(ATLAS_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != EXPECTED_ATLAS_SHA:
        raise ValueError(f"ATLAS SHA mismatch: expected {EXPECTED_ATLAS_SHA}, got {sha}")
    source = EXTRACTOR.read_text(encoding="utf-8")
    netlist = NETLIST.read_text(encoding="utf-8")
    # These checks are specific to the pinned source and show precisely why
    # a number might be a sentinel rather than a valid physical measurement.
    required = {
        "UGBW returns first AC frequency if no unity crossing": "return freq[0]",
        "PM returns -180 if no unity crossing": "return -180",
        "Settling uses dimensionless error on no-settle": "settlingTime = d_settle",
        "Actual settle is measured relative to step time": "settling_time = time_segment[idx_settle] - start_t",
    }
    for explanation, token in required.items():
        if token not in source:
            raise RuntimeError(f"Unexpected extractor content: {explanation}")

    tran = re.search(r"(?im)^\s*tran\s+\S+\s+([0-9.eE+-]+)\s*$", netlist)
    ac = re.search(r"(?im)^\s*ac\s+\S+\s+\S+\s+([0-9.eE+-]+)\s+", netlist)
    if tran is None or ac is None:
        raise ValueError("Expected transient horizon / AC starting frequency not found")
    transient_stop_s = float(tran.group(1))
    ac_start_hz = float(ac.group(1))
    if transient_stop_s <= 0 or ac_start_hz <= 0:
        raise ValueError("Invalid netlist simulation limits")
    return {
        "atlas_sha": sha,
        "extractor_source": str(EXTRACTOR),
        "extractor_sha256": sha256(EXTRACTOR),
        "netlist_source": str(NETLIST),
        "netlist_sha256": sha256(NETLIST),
        "transient_stop_s": transient_stop_s,
        "ac_start_hz": ac_start_hz,
        "code_semantics_checks": list(required.keys()),
    }


def main():
    for p in (OUTPUT_JSON, OUTPUT_CSV):
        if p.exists():
            raise FileExistsError(f"Analysis record already exists (not overwritten): {p}")
    meta = get_codes_and_horizons()
    rows, source_sha = read_source()
    tstop = meta["transient_stop_s"]
    freq_first = meta["ac_start_hz"]
    flags = []
    for i, r in enumerate(rows):
        # If the recorded time exceeds the entire simulated horizon it
        # CANNOT have been measured as a time from the available waveform.
        # A small *unflagged* value is NOT proof of valid settling, however.
        impossible_time = r["t_settle_max"] > tstop + 1e-12
        # The paired special values are exactly what the pinned extractor
        # returns when a valid AC unity crossing is not found.
        paired_ac_sentinel = (
            r["ugbw_min"] == freq_first and r["phm_min"] == -180.0
        )
        flags.append({
            "design_id": r["design_id"],
            "split": "train" if i < 40 else "holdout",
            "settling_stored_value": r["t_settle_max"],
            "settling_exceeds_transient_window": impossible_time,
            "ac_missing_crossing_sentinel_pair": paired_ac_sentinel,
            "settling_status": (
                "DEFINITELY_NOT_MEASURED_TIME" if impossible_time
                else "NOT_PROVEN_VALID_WITHOUT_WAVEFORM"
            ),
            "ac_status": (
                "MISSING_CROSSING_SENTINEL" if paired_ac_sentinel
                else "NOT_FLAGGED"
            )
        })

    split_counts = {}
    for split in ("train", "holdout"):
        portion = [r for r in flags if r["split"] == split]
        split_counts[split] = {
            "n": len(portion),
            "settling_beyond_simulation": sum(
                r["settling_exceeds_transient_window"] for r in portion
            ),
            "ac_paired_sentinels": sum(
                r["ac_missing_crossing_sentinel_pair"] for r in portion
            ),
        }
    diagnostics = {
        "experiment": "EXP-005",
        "stage": "metric_extraction_semantics",
        "status": "code-verified detection; waveform inspection still needed",
        "new_spice_evaluations": 0,
        "new_gp_fits": 0,
        "source_sha256": source_sha,
        **meta,
        "split_counts": split_counts,
        "settling_beyond_simulation_designs": [
            r["design_id"] for r in flags
            if r["settling_exceeds_transient_window"]
        ],
        "ac_paired_sentinel_designs": [
            r["design_id"] for r in flags
            if r["ac_missing_crossing_sentinel_pair"]
        ],
        "interpretation": (
            "An apparent settling time greater than the full transient "
            "window is not a real measured duration. The pinned extractor "
            "substitutes dimensionless d_settle when settling is not found. "
            "A normal-looking value alone cannot prove settling was found. "
            "A paired UGBW=start frequency/PM=-180 denotes missing AC "
            "unity-crossing according to the pinned extractor."
        ),
        "next_decision": (
            "Do not log-transform all raw settling targets as though every "
            "value were a measured time. Compare surrogate approaches only "
            "after defining measurement-valid vs censored/no-settle outcomes."
        ),
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flags[0]))
        writer.writeheader()
        writer.writerows(flags)
        f.flush()
        os.fsync(f.fileno())
    with OUTPUT_JSON.open("x", encoding="utf-8") as f:
        json.dump(diagnostics, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    print(f"[SOURCE] ATLAS SHA: {meta['atlas_sha'][:12]}")
    print(f"[TRANSIENT] Simulated stop time: {tstop:g} s = {tstop*1e6:g} us")
    print(f"[AC] Starting frequency: {freq_first:g} Hz")
    print("[CHECK] Extractor fallback code matches the pinned release")
    for split, c in split_counts.items():
        print(
            f"[{split.upper()}] {c['n']} designs; "
            f"non-time settling values >= {c['settling_beyond_simulation']}; "
            f"AC paired sentinels = {c['ac_paired_sentinels']}"
        )
    print("[SETTLING IDS] " + ", ".join(diagnostics["settling_beyond_simulation_designs"]))
    print("[AC IDS] " + ", ".join(diagnostics["ac_paired_sentinel_designs"]))
    print("[CAUTION] Unflagged settling values are not guaranteed to be valid")
    print(f"[SAVED] {OUTPUT_JSON}")
    print(f"[SAVED] {OUTPUT_CSV}")
    print("[BUDGET] New SPICE=0, GP fits=0")


if __name__ == "__main__":
    main()
