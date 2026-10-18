# TECHNOMANCERS — Smart AI Fan (atomQUEST 2026, Track 1 · Fan)

**One-line description:** Evidence repository (verified calculations, range-based cost basis, validation gates) for the TECHNOMANCERS *Smart AI Fan* and its 2-page atomQUEST 2026 Stage 1 abstract.

Evidence and calculation repository for the atomQUEST 2026 Round 1 (Stage 1) abstract:

> **Smart AI Fan** — an intelligent 1,400 mm-sweep ceiling fan: ambient temperature/humidity-based
> comfort automation and connected-device triggers (smart-home), sensor-based multi-directional
> swing (worm pan/tilt), and blade design for efficiency (quasi-isotropic CFRP on a 24 V sensorless-FOC BLDC drive),
> under a locked-firmware safety supervisor MCU that can cut motor and actuator power.

**Submission file:** `submission/TECHNOMANCERS_Track1.pdf` — **2 pages, 591 words** (pypdf, 18 Oct 2026; ≤ 600 ✔) — the canonical portal upload file, quoting the range-based cost basis
**Superseded:** `submission/TECHNOMANCERS_Track1_600word_2page.pdf` is an older draft with the withdrawn fixed-BOM cost text — kept for history, **not** the upload candidate.

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

Both scripts are deterministic; `fan_design_calculations.py` uses `pypdf` (installed) for its PDF quote gate.

## What every calculation does (so a judge can check any scenario)

1. **`calculations/fan_design_calculations.py`** — recomputes every headline number from first principles
   with the exact printed formula and its input assumption at each step, and asserts consistency with the PDF:
   blade-tip speed vs the 30 m/s cap, rotor inertia/energy at 380 and 456 RPM (456 = hazard case, never a target),
   service value (indicative), suspension demand vs ratings,   tilt-clearance geometry, plausibility-gate bounds,
   range-based cost roll-up vs the figures quoted in the PDF (line sums, 10 % contingency, rounding, and an
   assertion that the PDF quotes the new ranges and none of the withdrawn figures), safety defense-in-depth chain.
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
  cost_basis.md                  ← the cost basis that replaces the old BOM figures (18 Oct 2026)
data/
  design_targets.csv             ← parameter targets + evidence status (mirrors the PDF annexure table)
  bom_ranges.csv                 ← CURRENT range-based cost BOM (source of the PDF cost figures; no quotations)
  bom.csv                        ← legacy fixed per-item BOM (superseded; kept for traceability only)
  validation_gates.csv           ← T-00…T-21 validation programme gates
  risk_register.csv              ← unresolved risks preserved deliberately (incl. blocked items)
  scenarios.csv                  ← 16 defined Round 1 comfort/device scenarios (targets, not results)
calculations/
  fan_design_calculations.py     ← all design calculations (runnable, self-checking)
  check_scenarios.py             ← scenario framework + deterministic controller simulation
submission/
  TECHNOMANCERS_Track1.pdf                 ← 2 pages, 591 words, new cost basis (THE upload file)
  TECHNOMANCERS_Track1_Annexure.pdf        ← annexure (attach only if the portal permits extra files)
  TECHNOMANCERS_Track1_600word_2page.pdf   ← superseded older draft (withdrawn cost text); not the upload
  generate_600word_2page.py                ← generator of the 2-page A–D PDF (same content/cost text)
  generate_threepage_submission.py         ← legacy multi-page generator (not the upload generator; table uses the legacy BOM)
```

## Team

TECHNOMANCERS (T-2026) · Track 1 · Fan — Aditya Institute of Technology and Management, Tekkali,
Department of Electronics and Communication Engineering. Members: Harsha Vardhan Malipeddi,
Dabbiru Rochan Kumar, Simhadri Sri Teja, Guluvindala Ganesh Manikanta, Nakka Ugandhar.

## Submission status (checked 18 Oct 2026 — deadline day)

Grad Partners portal: Round 1 abstract submission closes **18 October 2026, 18:29 GMT (11:59 PM IST)**;
registration closed 17 October 2026. Rule as recorded in this repository: **two–three page abstract, ≤ 600 words,
PDF** (the portal page is a JavaScript app and did not render for our text fetch — confirm the binding wording
yourself at the link below). The upload file is `submission/TECHNOMANCERS_Track1.pdf` — **2 pages, 591 words
(pypdf, 18 Oct 2026)** — carrying the range-based cost basis (`docs/cost_basis.md`):
Level 1 prototype ≈ INR 10,000 (7,000–14,000), full-fan prototype ≈ INR 25,000 (17,000–33,000), and none of
the withdrawn figures (≈ INR 26,650 / ≈ INR 5.8 lakh). `submission/generate_600word_2page.py` carries the same
text and can re-derive an equivalent 2-page PDF if re-run (it was NOT used to rebuild the checked-in upload file).
Links: gradpartners.in/e/atomquest-2026-339 · atomberg.com
