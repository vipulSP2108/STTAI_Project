"""release_drift_loop.py - Drift replay, detection and gated retraining on the release split (A2 Part E).

One command runs the whole loop:
    python code/a2_part_e_monitoring/release_drift_loop.py

1. Read configs/gate_release.yaml and log its SHA-256 BEFORE any scoring.
2. Production router (router_v2, expert-final labels) = release-train speakers minus Cohort B (P4, P13), C chosen on
   validation speakers.
3. Thresholds for two label-free signals - batch mean decoder avg_logprob and batch share of clips
   routed to Hindi - from 1000 bootstrap batches of validation clips only; false-alarm rate measured
   on 500 further in-distribution batches.
4. Replay (seed 42): six batches of 20 whose Cohort-B share follows the gate schedule; the labelled
   metric (intent accuracy) is computed per batch only for the plot / correlation.
5. On alert: select the 10 lowest-confidence clips of the Cohort-B adaptation pool, reveal their
   labels from the pre-labelled pool (simulated annotator), validate them, retrain two candidates
   (rehearsal = old data + new clips; no-rehearsal = new clips only), score on the Cohort-B held-out
   half and on the release test split, apply the frozen gate, promote or reject, show rollback.
Outputs: supporting_files/release_drift/{replay.json, gate_decisions.json, registry.json, drift.png}
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "a2_part_d_deployment"))
from router_v2 import Embedder, IntentRouter  # noqa: E402
from revised_data import release_rows  # noqa: E402

OUT = ROOT / "supporting_files" / "release_drift"
LOG = ROOT / "TEST_SET_LOG.md"


def log(line):
    with open(LOG, "a") as f:
        f.write(line + "\n")


def gate_decision(before, after, criteria):
    """Frozen gate: promote only if Cohort-B held-out gains enough AND release test drops little."""
    gain = after["heldout"] - before["heldout"]; drop = before["test"] - after["test"]
    ok = gain >= criteria["min_cohort_b_heldout_accuracy_gain"] and drop <= criteria["max_release_test_accuracy_drop"] + 1e-9
    return ok, gain, drop


def update_registry(registry, candidate_name, train_clips, promoted):
    """Promotion moves the old production model to the 'rollback' alias; rejection changes nothing."""
    if not promoted:
        return dict(registry)
    return {"production": {"name": candidate_name, "train_clips": train_clips}, "rollback": registry["production"]}


def rollback(registry):
    """Restore the previous production model; only valid after a promotion."""
    if "rollback" not in registry:
        raise ValueError("nothing to roll back to")
    return {"production": registry["rollback"], "rolled_back_from": registry["production"]}


def acc(router, rows):
    if not rows:
        return None
    cls, P = router.predict_proba([r["text"] for r in rows])
    return float(np.mean(cls[P.argmax(1)] == np.array([r["intent"] for r in rows])))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-retrain", action="store_true",
                    help="mechanism demo: run selection/retrain/gate even without an alert (labelled as such in all logs)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    gate_path = ROOT / "configs/gate_release.yaml"
    gate_sha = hashlib.sha256(gate_path.read_bytes()).hexdigest()
    gate = yaml.safe_load(gate_path.read_text())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    log(f"| `GATE-{time.strftime('%Y%m%d-%H%M')}` | {stamp} | `{commit}`+working tree | gate_release.yaml v{gate['gate_version']} | "
        f"gate file sha256 `{gate_sha[:16]}` recorded before scoring | - | - | - | **GATE FROZEN** |")

    conf = {r["uuid"]: r for r in json.loads((ROOT / "model/data/reports/asr_indic_v2_confidence.json").read_text())["clips"]}
    g = release_rows()
    for part in g.values():
        for r in part:
            r["logprob"] = conf[r["uuid"]]["avg_logprob"]
            r["route"] = conf[r["uuid"]]["route"]
            r["text"] = conf[r["uuid"]]["transcription"]      # prompt-free Indic decode
    cb_spk = set(gate["shifted_cohort"]["speakers"])
    cohort = sorted([r for r in g["train"] if r["original_speaker_id"] in cb_spk], key=lambda r: r["uuid"])
    base_train = [r for r in g["train"] if r["original_speaker_id"] not in cb_spk]
    rng = np.random.default_rng(gate["shifted_cohort"]["seed"])
    perm = rng.permutation(len(cohort)); half = int(len(cohort) * gate["shifted_cohort"]["adapt_fraction"])
    adapt = [cohort[i] for i in perm[:half]]; held = [cohort[i] for i in perm[half:]]
    val, test = g["validation"], g["test"]

    emb = Embedder()
    prod = IntentRouter(emb); sel = prod.select_and_fit(base_train, val)
    registry = {"production": {"name": "router_v1", "train_clips": len(base_train), "C": sel["selected_C"]}}

    # ---- thresholds from validation only -----------------------------------------
    B = gate["drift_detection"]["batch_size"]
    lp_val = np.array([r["logprob"] for r in val]); hi_val = np.array([r["route"] == "hi" for r in val], float)
    boot = rng.integers(0, len(val), size=(1000, B))
    # Two-sided bands (gate: "1st/99th percentile"). Run 1 used only the lower logprob bound and
    # the upper Hindi bound - a bug kept on record in supporting_files/release_drift/*_run1_*.
    lp_lo, lp_hi = (float(x) for x in np.percentile(lp_val[boot].mean(1), [1, 99]))
    hi_lo, hi_hi = (float(x) for x in np.percentile(hi_val[boot].mean(1), [1, 99]))
    out_of_band = lambda lp, hi: (lp < lp_lo) or (lp > lp_hi) or (hi < hi_lo) or (hi > hi_hi)
    fa_boot = rng.integers(0, len(val), size=(500, B))
    fa_single = float(np.mean([out_of_band(a, b) for a, b in zip(lp_val[fa_boot].mean(1), hi_val[fa_boot].mean(1))]))
    fa_two = fa_single ** 2   # alert needs two consecutive out-of-threshold batches

    # ---- replay -----------------------------------------------------------------
    sched = gate["drift_detection"]["schedule_cohort_b_share"]
    stream = held + adapt   # Cohort-B traffic the service sees (labels hidden)
    batches, flags = [], []
    for k, share in enumerate(sched):
        nb = int(round(share * B))
        rows = [stream[i] for i in rng.integers(0, len(stream), nb)] + [val[i] for i in rng.integers(0, len(val), B - nb)]
        lp = float(np.mean([r["logprob"] for r in rows])); hi = float(np.mean([r["route"] == "hi" for r in rows]))
        flag = out_of_band(lp, hi)
        flags.append(flag)
        batches.append({"batch": k + 1, "cohort_b_share": share, "mean_logprob": lp, "hindi_route_share": hi,
                        "flag": bool(flag), "intent_accuracy_labelled": acc(prod, rows)})
    alert_at = next((k + 1 for k in range(1, len(flags)) if flags[k] and flags[k - 1]), None)
    first_shift = next(k + 1 for k, s in enumerate(sched) if s > 0)
    lp_s = [b["mean_logprob"] for b in batches]; ac_s = [b["intent_accuracy_labelled"] for b in batches]
    replay = {"gate_sha256": gate_sha, "thresholds": {"mean_logprob_band": [lp_lo, lp_hi], "hindi_share_band": [hi_lo, hi_hi]},
              "false_alarm_rate_per_batch": fa_single, "false_alarm_rate_alert_rule": fa_two,
              "batches": batches, "alert_batch": alert_at, "first_shifted_batch": first_shift,
              "detection_delay_batches": (alert_at - first_shift) if alert_at else None,
              "corr_logprob_vs_accuracy": float(np.corrcoef(lp_s, ac_s)[0, 1]),
              "cohort_sizes": {"adapt_pool": len(adapt), "heldout": len(held), "base_train": len(base_train)}}

    # ---- retrain on alert --------------------------------------------------------------
    decisions = []
    trigger = "alert" if alert_at else ("forced demo (no alert)" if args.force_retrain else None)
    replay["retrain_trigger"] = trigger
    if trigger:
        k = gate["criteria"]["selection_budget"]
        picked = sorted(adapt, key=lambda r: r["logprob"])[:k]                         # AL: low decoder confidence
        assert all(r["original_speaker_id"] in cb_spk for r in picked)                    # validation of revealed data
        assert not {r["uuid"] for r in picked} & {r["uuid"] for r in held + test + val}
        assert all(r["intent"] in {"admissions", "hostel_mess", "it_support", "student_services"} for r in picked)
        before = {"heldout": acc(prod, held), "test": acc(prod, test)}
        for name, train in (("rehearsal", base_train + picked), ("no_rehearsal", picked)):
            cand = IntentRouter(emb)
            if len({r["intent"] for r in train}) < 2:
                decisions.append({"candidate": name, "decision": "rejected", "reason": "fewer than two classes"}); continue
            cand.select_and_fit(train, val)
            after = {"heldout": acc(cand, held), "test": acc(cand, test)}
            ok, gain, drop = gate_decision(before, after, gate["criteria"])
            decisions.append({"candidate": name, "trigger": trigger, "selected_uuids": [r["uuid"] for r in picked], "before": before, "after": after,
                              "heldout_gain": gain, "test_drop": drop, "decision": "promoted" if ok else "rejected"})
            log(f"| `GATE-{time.strftime('%Y%m%d-%H%M')}-{name}` | {time.strftime('%Y-%m-%dT%H:%M:%S')} | `{commit}`+working tree | "
                f"router {name} [{trigger}] | gate v{gate['gate_version']} check: Cohort-B held-out {before['heldout']:.3f}->{after['heldout']:.3f}, "
                f"release test {before['test']:.3f}->{after['test']:.3f} | - | - | {after['test']:.3f} | **{'PROMOTED' if ok else 'REJECTED'}** |")
            if registry["production"]["name"] == "router_v1":
                registry = update_registry(registry, f"router_v2_{name}", len(train), ok)
        registry["rollback_demo"] = ("production restored from 'rollback' alias" if "rollback" in registry
                                     else "no promotion, production unchanged")
    (OUT / "replay.json").write_text(json.dumps(replay, indent=1))
    (OUT / "gate_decisions.json").write_text(json.dumps(decisions, indent=1))
    (OUT / "registry.json").write_text(json.dumps(registry, indent=1))

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.0)); x = [b["batch"] for b in batches]
    ax[0].plot(x, lp_s, "o-"); ax[0].axhspan(lp_lo, lp_hi, color="grey", alpha=0.2); ax[0].set_title("decoder avg log-prob")
    ax[1].plot(x, [b["hindi_route_share"] for b in batches], "o-"); ax[1].axhspan(hi_lo, hi_hi, color="grey", alpha=0.2); ax[1].set_title("share routed to Hindi")
    ax[2].plot(x, ac_s, "o-", c="g"); ax[2].set_title("intent accuracy (labelled)")
    for a in ax:
        a.set_xlabel("batch"); a.axvline(first_shift - 0.5, c="grey", lw=0.6)
        if alert_at:
            a.axvline(alert_at, c="r", lw=0.8)
    fig.tight_layout(); fig.savefig(OUT / "drift.png", dpi=150)
    fig.savefig(ROOT / "STTAI_reports/report_final/report/fig_f_drift.pdf")
    print(json.dumps({"replay": {k: v for k, v in replay.items() if k != "batches"}, "batches": batches,
                      "decisions": decisions, "registry": registry}, indent=1))


if __name__ == "__main__":
    main()
