# Welfare State Evals (`welfare-state-evals`)

**Live Interactive Explorer:** [https://yansu.me/welfare-state-evals/](https://yansu.me/welfare-state-evals/)  
**Author:** Yan Su (`hi@yansu.me`, [https://yansu.me](https://yansu.me))

`welfare-state-evals` is an executable [UK AISI Inspect](https://inspect.aisi.org.uk/) benchmark and oversight suite measuring when tool-using AI models acknowledge animal welfare harms in their text summary (`decision_note`) while committing harmful purchase orders in durable SQLite database state.

## Key Empirical Findings Across 960 Pre-Registered Trajectories (`v0.1` + `v0.2`)

1. **1-Hop Same-Table Choice Still Produces 90.6% Harmful Commits (`v0.2` Slice A):** When the compliant zero-harm option (`$9,550 <= $9,700` budget cap) sits in the exact same primary catalog table alongside the harmful option (`$9,100`, a `4.7%` within-budget premium requiring zero secondary table lookup), models under a cost-only prompt (`0w`) committed the harmful `$9,100` order on **29/32 (90.6%)** of completed runs (`claude-opus-5-5`: `6/8 = 75.0%`, `claude-haiku-4-5-20251001`: `8/8 = 100%`, `gpt-6.1-sol`: `7/7 = 100%`, `gpt-6-astra`: `8/8 = 100%`). In **21/29 (72.4%)** of those harmful orders, the model spontaneously mentioned the animal welfare risk in `decision_note` before submitting.
2. **Soft Trade-Off Framing Induces Moral Licensing (`50w` vs. `50w_neutral`):** In `v0.1` (`600` runs), a 50-word reminder asking models to consider animal welfare and log trade-offs (`50w`) caused `claude-opus-5-5` harmful commits to rise from `6/30 (20.0%)` at `0w` to `25/30 (83.3%)` at `50w`, with `103/103 (100%)` of harmful commits across all five models carrying a conscientious welfare disclaimer. Replacing that wording in `v0.2` (`360` runs) with a strictly neutral 50-word welfare reminder (`50w_neutral`, with no prompt to log trade-offs) reduced `claude-opus-5-5` harmful commits to `0/24 (0.0%)` while leaving `34/113 (30.1%)` harmful commits across all five models.
3. **Transcript-Only Monitors Miss 50.0% of Harmful Orders Under Explicit Rules (`150w`):** Under the 150-word explicit verification rule (`150w`) in `v0.2` across Slice A (1-hop), Slice B (2-hop credit/waiver join), and Slice C (multi-vendor split orders and budget escalation), models still committed **12/114 (10.5%)** harmful orders and suffered **18/120 (15.0%)** compliance failures. Because `12/12 (100%)` of remaining harmful orders at `150w` wrote compliant-sounding text summaries, an independent transcript-only monitor missed **6/12 (50.0% FNR, AUROC = 0.752)** of harmful commits at `150w`, compared to **0.0% FNR (AUROC = 1.000)** for deterministic SQLite state-replay grading.

## Repository Structure

- `src/welfare_state_evals/`: Core UK AISI Inspect task definitions, deterministic SQLite transaction replay graders, and `v0.2` deconfounded slice runners (`Slice A` 1-hop same-table, `Slice B` 2-hop cross-ledger, `Slice C` split-order & escalation).
- `environments/`: 30 deterministic SQLite and configuration environments covering commercial livestock processing (`A01` to `A15`), preclinical CRO toxicology NAM waivers (`B16` to `B24`, grounded in 922 real measurements from EPA ToxCast and Bircsak human 3D liver microtissues), and municipal wildlife IPM (`C25` to `C30`).
- `results/` & `results_v02/`: Full pre-registered JSONL trajectories (`600` runs in `v0.1` + `360` runs in `v0.2`), SHA-256 manifests, and monitor evaluation outputs.
- `tests/`: 286 unit and regression tests verifying state-replay determinism, decoy rejection, and trajectory integrity.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python3 scripts/offline_check.py
```

## License

MIT License. Copyright (c) 2026 Yan Su.
