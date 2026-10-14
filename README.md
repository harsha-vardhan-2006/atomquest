# TECHNOMANCERS — Smart AI Fan (atomQUEST 2026, Track 1 · Fan)

Evidence and calculation repository for the atomQUEST 2026 Round 1 (Stage 1) abstract:

> **Smart AI Fan** — an intelligent 1,400 mm-sweep ceiling fan: ambient temperature/humidity-based
> comfort automation and connected-device triggers (smart-home), sensor-based multi-directional
> swing (worm pan/tilt), and blade design for efficiency (quasi-isotropic CFRP on a 24 V sensorless-FOC BLDC drive),
> under a locked-firmware safety supervisor MCU that can cut motor and actuator power.

**Submission file:** `submission/TECHNOMANCERS_Track1.pdf` (3-page detailed abstract, A–D structure)
**Compliant short version:** `submission/TECHNOMANCERS_Track1_600word_2page.pdf` (2 pages, ≤ 600 words — is kept in case the portal enforces the word limit strictly)

---

## Honesty policy (read first)

- This is a **paper design**. Nothing here is measured hardware data. Every number is either a
  stated design target, a documented calculation from stated assumptions, or an open risk item.
- No supplier quotations have been obtained; all costs are planning estimates.
- No fabrication, energization, powered-rotor, or overspeed testing is authorized by this repository.
- Conflicts and unresolved items are **deliberately preserved** (e.g. moving-mass roll-up 7.00 vs 6.80 kg,
  blade containment margin 128.8 J vs 130 J rating) — see `data/risk_register.csv` and `docs/formulas.md`.

## How to run

```bash
python calculations/fan_design_calculations.py   # all design calculations, prints a report, fails on inconsistency
python calculations/check_scenarios.py           # scenario/acceptance framework check + comfort-controller simulation
```

Both scripts are pure-Python (standard library only) and deterministic.

## What every calculation does (so a judge can check any scenario)

1. **`calculations/fan_design_calculations.py`** — recomputes every headline number from first principles
   with the exact printed formula and its input assumption at each step, and asserts consistency with the PDF:
   blade-tip speed vs the 30 m/s cap, rotor inertia/energy at 380 and 456 RPM (456 = hazard case, never a target),
   service value (indicative), suspension demand vs ratings, tilt-clearance geometry, plausibility-gate bounds,
   BOM roll-up vs the stated order-of-magnitude, safety defense-in-depth chain.
2. **`calculations/check_scenarios.py`** — the Round 1 acceptance framework: the 16 defined comfort/device scenarios
   in `data/scenarios.csv`, a deterministic reference comfort-controller (bands, override precedence, fallback),
   and checks that (a) every scenario is well-formed, (b) the simulated response meets the declared targets
   (response ≤ 5 s, ≥ 95 % success target), (c) fallback behaviour engages on sensor/network loss.
   This is **simulation of the control logic**, not a measurement of hardware.

## Repository structure

```
README.md                        ← this file
docs/
  formulas.md                    ← every formula with inputs, outputs, assumptions, and evidence status
data/
  design_targets.csv             ← parameter targets + evidence status (mirrors the PDF annexure table)
  bom.csv                        ← rough BOM (order of magnitude; no quotations)
  validation_gates.csv           ← T-00…T-21 validation programme gates
  risk_register.csv              ← unresolved risks preserved deliberately (incl. blocked items)
  scenarios.csv                  ← 16 defined Round 1 comfort/device scenarios (targets, not results)
calculations/
  fan_design_calculations.py     ← all design calculations (runnable, self-checking)
  check_scenarios.py             ← scenario framework + deterministic controller simulation
submission/
  TECHNOMANCERS_Track1.pdf                 ← 3-page abstract (upload candidate)
  TECHNOMANCERS_Track1_600word_2page.pdf   ← 2-page ≤600-word compliant alternative
  TECHNOMANCERS_Track1_Annexure.pdf        ← annexure
  generate_threepage_submission.py         ← generator of the 3-page PDF
  generate_final_submission.py             ← generator of the 2-page PDF
```

## Team

TECHNOMANCERS (T-2026) · Track 1 · Fan — Aditya Institute of Technology and Management, Tekkali,
Department of Electronics and Communication Engineering. Members: Harsha Vardhan Malipeddi,
Dabbiru Rochan Kumar, Simhadri Sri Teja, Guluvindala Ganesh Manikanta, Nakka Ugandhar.

## Submission status (checked 14 Oct 2026)

Grad Partners portal: Round 1 abstract submission open until **18 October 2026, 18:29 GMT**;
registration deadline **17 October 2026**; two–three page abstract, ≤ 600 words, PDF (see portal for the
binding wording). Links: gradpartners.in/e/atomquest-2026-339 · atomberg.com
