# Rev 2 · CAD Clearance Closure Plan — T-00a (the pre-power precheck)

**Revision 2 · October 2026 · Gate: T-00a (06-test-plan). No powered hardware before this sign-off.**

> Source-of-record note: this plan operationalizes 04-clearance §6 and 06
> T-00a as an executable CAD programme. The geometric math used as acceptance
> reference is computed by
> `competition/atomQUEST2026/round1/atomquest-smart-ai-fan/calculations/cad_clearance_grid_plan.py`
> (runnable, exit 0) — including one **new exact result** that resolves a known
> 1 cm tension in the clearance rule (§4 below).

## 1. Model set required (all CAD instances, before scan)

| # | Model | Detail |
| --- | --- | --- |
| M1 | Rotor assembly | 3 blades at 120°, hub, motor bell, blade mass envelopes ±2 g scatter |
| M2 | Blade geometry | root chord 160 → tip 120, depth 10 → 6 mm, root fillet, final wall schedule candidate; also an over-mass variant (+5%) as worst case |
| M3 | Pan/tilt carriage | hub + tilt gimbal + housing sweep surfaces |
| M4 | Statics | downrod (450 mm), canopy, ceiling plane at each reference height, safety cable slack loop Ø ≤ 100 mm, wire/PCB lead lofts |
| M5 | Envelope extremes | pan −175°…+175° hard-stop surfaces, tilt ±27° hard stops, stop-margin acknowledgement |

## 2. Scan specification (T-00a verbatim)

- Grid: **pan −170°…+170° step 0.5° → 681 points × tilt −27°…+27° step 0.5° → 109 points = 74,229 poses** (script prints exact counts)
- 3 blades evaluated per pose → interference pairs checked: blade-blade, blade-ceiling, blade-static (cable/wires/canopy), blade-floor across reference ceiling planes
- Reference ceiling planes: 2.55 m (tilt-disabled region), 2.65 m, 2.70 m, 2.85 m, 3.00 m
- Step sanity: run once at 0.25° in neighborhoods of any near-miss found at 0.5°

## 3. Acceptance thresholds (as coded in the gates)

| Clearance pair | Required minimum | Source |
| --- | --- | --- |
| Blade-blade (adjacent, 120° apart) | **≥ +1 mm separation** (never touching; CAD gain over the airfoil build) | 04 §6 |
| Blade-ceiling (highest tip at tilt) | **≥ 50 mm static** | 06 T-00a |
| Blade-object (cable loop, wires, canopy) | **≥ 50 mm static** | 06 T-00a |
| Blade-floor | not a CAD result — floor clearance is governed by the firmware ceiling-height rule (§4) | 04 §2 |

Parser definition (deterministic, re-runnable): minimum clearance = min distance between CAD tessellations at the pose; report per pair the pose, angle pair, and value; the scan result is a table, not a pass flag alone.

## 4. The 1 cm tension in the clearance rule — resolved analytically (new exact result)

The lowest blade tip below the hub is z_low(θ) = R·cos θ + a·sin θ (R = 0.70 m,
a = 0.12 m hub half-height). Differentiating: the **maximum drop is not at the
level position — it is at θ* = atan(a/R) ≈ 9.74°, where z_low = √(R² + a²) ≈
0.7102 m**, which is ~1 cm *worse* than the level case (0.700 m) and 1.1 cm
worse than full ±20° tilt (0.699 m). Consequence, printed by the script:

- For the floor-clearance rule (≥ 1.50 m): minimum ceiling for **unlimited ±20° tilt = 0.45 + 0.7102 + 1.50 = 2.660 m** — the 04 "2.65 m passes everywhere" statement is true at 0° and 20° but is ~1 cm short near 10° tilt.
- **The firmware rule is binary, not tiered.** Because z_low(θ) EXCEEDS the level value for every tilt in 0° < |θ| < ~19.8° (it peaks at θ* ≈ 9.73°), a ceiling that only just passes at level (budget = 0.700 m, e.g. H = 2.65 m — exactly on the boundary) cannot host *any* intermediate tilt: 1–19.7° all dip deeper. So:
  - **H ≥ 2.660 m → full ±20° tilt** (function makes the ceiling test pass for all tilts up to 20°)
  - **H = 2.65 m → LEVEL ONLY (cap 0°)** — boundary case, exactly on the line
  - **H < 2.65 m → not qualified for installation** (level clearance itself < 1.50 m)
  - the old tiered tables (3.20/3.00/2.60 m and any "±10° cap at some midpoint") are doubly superseded — this is a documented correction to 00-design-freeze T13b/T13c, 04 §2.2, and default D-04, alignment to be propagated in a passing doc change
- **T-00a/T-16 therefore verify the firmware cap against this binary rule**, and the T-17 arrested-tip height check uses the same worst-case θ* geometry.

## 5. Outputs & sign-off

1. Clearance heat-map per ceiling plane (pan × tilt grid)
2. Worst-10-pose table per pair type
3. Firmware θ_cap table for the reference ceilings (from script §4 formula)
4. Sign-off: CAD engineer + design lead dated → **T-00a closed** → gate to T-16 envelope dry run (physical) remains

**Status: plan defined and script-verified; the acceptance machinery is now executable in pre-CAD mode via `calculations/cad_clearance_scan_workflow.py` (baseline report + strict CSV ingest interface for the real model-to-model minimum-distance map, header `pair,pan_deg,tilt_deg,distance_mm`). CAD models to be built on the next work block; the harness cross-checks the blade-ceiling rows against the exact law and refuses deviating model sets. Nothing physical starts before this sign-off.**
