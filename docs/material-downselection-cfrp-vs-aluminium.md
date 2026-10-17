# Rev 2 · Blade Material Down-Selection — CFRP vs Aluminium (Same Geometry, Same Loads)

**Revision 2 · October 2026 · Responsive to the external review memo ("freeze the concept, not the material").**

> Source-of-record note: this is a Rev 2 source document for the blade-material
> decision. All numbers are paper calculations under the frozen load set; the
> runnable check is `calculations/compare_cfrp_vs_aluminium.py` (exit 0,
> assertions on). Both material routes remain gated by `06-test-plan.md`
> T-00c / T-01 / T-05 before anything here becomes a procurement commitment.

## 1. Decision status (adopted from the review memo's discipline)

| Decision layer | Status |
| --- | --- |
| Concept configuration | **FROZEN** — whole-room 1,400 mm, 380 RPM, 3 blades, pan/tilt supervisor-locked (00-design-freeze) |
| Lead blade material | **PROVISIONAL**: CFRP prepreg QI [0/±45/90]s, T300-class, epoxy 120 °C |
| Comparison material | **RETAINED**: Al 6061-T6 sheet (+ Al-Li 2099-T83 specialty option), on the explicit condition that any metal route must pass the same T-05 coupons, T-01 blade gauge, and a seam qualification before adoption |
| Backup | Carbon-spar + S2-glass-skin hybrid, same validation conditions |
| NOT approved (deliberately open) | final wall schedule, root fastening detail, final safe-RPM limit, containment rating basis (blocked pending T-06 rig) |

## 2. The same-geometry, same-load comparison (review item 1, now closed)

Identical for every option: span 0.55 m, chord 160→120 mm, envelope depth
10→6 mm, M_d = 1.63 N·m, q = 3.95 N/m, overspeed ×1.44, tip-speed/IEC load
environment identical. Results (paper values; script-verified):

| Option | ρ (g/cc) | E (GPa) | y @165 g (mm) | Wall @165 g | Mass to hit 0.60 mm | Worst stress / allow | ₹/blade | Moving assembly (kg) | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · CFRP-QI T300/epoxy | 1.55 | 70 | **0.60**, 0.63 mm | 165 g | — | 5.3 / 570 (1%) | 1,800 | 7.00 | **Lead candidate** — joint-free, gaugeable, process-controlled |
| B · CFRP-QI IM T800 | 1.57 | 95 | 0.45 | 0.62 | 123 g | 5.4 / 900 (1%) | 2,430 | 6.87 | Upgrade option — −28% deflection, +35% cost |
| C · Al 6061-T6 sheet | 2.70 | 69 | **1.06 (F)** | 0.36 | 292 g | 9.2 / 276 (3%) | 225 | 7.38 (+0.38) | Comparison candidate — needs matched mass (292 g) to reach the CFRP margin; wall 0.36 mm dent/impact-critical; joint-dependent |
| D · Al-Li 2099-T83 | 2.63 | 78 | 0.91 | 0.37 | 251 g | 9.0 / 500 (2%) | 650 | 7.27 (+0.27) | Comparison candidate — inside the 1 mm rule at 165 g, but seam-dependent + special-order lead time |
| E · C-spar + S2-glass hybrid | 1.70 | 50 | 0.92 | 0.57 | 253 g | 5.8 / 600 (1%) | 1,440 | 7.27 (+0.27) | Backup — 8% deflection margin only |

**Knock-on effects of an aluminium match:** +0.27–0.38 kg moving mass (T16
budget 6.80 kg is already UNRECONCILED against 7.00 kg — any metal option
grows the gap in the wrong direction), rotor inertia +3.5–4.9%, and the
aluminium wall at matched stiffness is 0.56–0.64 mm — a dent/impact-critical
sheet that needs either an adhesive seam or a mechanical roll-lock (both are
unqualified for a safety blade in this programme; a bonded-joint
qualification would have to be created and passed first).

**Fatigue statement (review item 4 sub-point):** aluminium has no true
endurance limit; the composite is fatigue-favoured but is
delamination-critical instead. This is why the comparison does **not** end in
"aluminium eliminated" — it ends in **both routes configured to enter the
same T-05 coupon suite (incl. 10⁷-cycle fatigue, hot-wet, and, for the metal
route, seam fatigue) with the same pass criteria.** The material is then
fixed by evidence, not by this document.

## 3. What still blocks finalisation (review items 2 and 8, tracked)

| Open item | Gate | Owner record |
| --- | --- | --- |
| Procurement-grade spec (*not "T300-class"*): exact fiber areal weight, resin system + cure, supplier datasheet, laminate allowables | T-00b/T-00c + T-05 | BOM §2 procurement gate |
| Aerodynamic closure: twist/chord build, noise vs ≤55 dB(A) @3 m, IS 374 chamber flow | T-02/T-03 | 01-blade-aero §4 re-freeze rule |
| Structural closure: FEA deflection, root joint, modal tap-test, delamination inspection criteria | T-04/T-05/T-06/T-08 | 02-rotor-structure [FEA REQUIRED] flags |
| Rotor/mount safety: spin-proof at 456 RPM, anchor pull, safety-cable arrest, containment basis (128.8 J vs 130 J — still BLOCKED) | T-06/T-17 | 05-controls, 06-test-plan |
| Applicable conformity route: IS 374:2019+Amd.1 (India, chosen boundary); IEC 60335-2-80 tracked as international reference — *the export-market route, if ever relevant, is a separate decision* | T-21 | 00-design-freeze §1, 06-test-plan T-21 |
| Prototype validation: 3 fans, guarded spin, endurance | T-19/T-20/T-21 | 06-test-plan acceptance logic |

## 4. Honest verdict

The review's core claim is correct and is now reflected here: **the material
is a provisional lead, not a frozen fact.** What the full material space
screening (`blade_material_screening_full.py`) and this comparison establish
is narrower and defensible: within this concept's geometry, loads,
certification regime and budget, no aluminium alloy reaches the CFRP blade's
deflection margin at equal mass, and none avoids a joint — so CFRP is the
*right first thing to prototype*, pending the evidence gates above that can
still reverse the decision.
