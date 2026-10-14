# Formulas and assumption set — Smart AI Fan (Track 1)

Every headline number in the submission PDF traces to exactly one block here and to
`calculations/fan_design_calculations.py`. **Nothing is measured hardware data.**

## Global assumptions
- Rotor diameter 1.4 m → radius R = 0.7 m. Top speed target 380 RPM.
- Rotor inertia I ≈ 0.113 kg·m² (CAD mass roll-up estimate — **assumption pending sign-off**).

## 1. Blade-tip speed
`v_tip = ω·R, ω = 2πN/60`
- N = 380 → **27.86 m/s** (calculated; under the IS-benchmark 30 m/s cap).
- N = 456 → **33.4 m/s** — exceeds the cap ⇒ 456 RPM is a **hazard case, never an operating target**.

## 2. Rotor kinetic energy (containment basis)
`E = ½·I·ω²`
- @380 RPM (ω = 39.79 rad/s) → **89.5 J** (calculated).
- @456 RPM (ω = 47.75 rad/s) → **128.8 J** (calculated; hazard case).
- Blade containment rating basis quoted as 130 J ⇒ margin is **thin** ⇒ gated **BLOCKED** pending
  test basis + authorization (T-19/T-20).
- Moving mass: component roll-up **7.00 kg** vs earlier stated **6.80 kg** — UNRECONCILED, both retained.

## 3. Service value (indicative)
`SV = air_delivery / input_power = 245 m³/min ÷ 28.3 W = **≈ 8.7 m³/min/W**`
- IS 374 requirement ≥ 4.1 m³/min/W. 245 m³/min itself is a **design target**, not a measurement.

## 4. Suspension / anchoring
- Anchor demand **139.9 N** (load analysis with the documented assumption set — see script).
- Ratings: anchors 600 N working / **1,500 N ultimate** ⇒ ≥ 10× ultimate factor; SS304 safety cable **6.5 kN**.

## 5. Tilt clearance geometry
`lowest_tip = H − (R + R·sin(θ))`
- H = 2.65 m (floor clearance untilted), θ = 20° full tilt → floor clearance at full tilt = 2.65 − (0.70 + 0.70·sin20°)
  ≈ **1.71 m ≥ 1.50 m requirement** (calculated; tilted disc is treated as dropping by R·sinθ about the disc centre).
- Supervisor interlock: **tilt disabled below 2.60 m floor clearance**.

## 6. Supervisor protection (definitions, not test results)
- Plausibility gates: −10…+80 °C, rate ≤ 3 K/s; implausible input → safe default curve.
- Motor NTC trip 165 °C. Supervisor watchdog 350 ms.
- Independent defenses: self-locking worm (holds on power loss) | encoders + limit switches + hard stops | supervisor raw power cut.
- Comfort targets: response ≤ 5 s (local mode); ≥ 95 % success over the 16 defined scenarios (`data/scenarios.csv`).

## 7. Cost model (planning estimates — **no quotations obtained**)
- BOM per fan: sum of `data/bom.csv` = **INR 26,650** (order of magnitude only).
- 3-fan programme: 3 × BOM + 10 % BOM contingency + NRE programme estimate (CFRP tooling/cure development,
  accredited lab testing, fixtures, iterations ≈ INR 4,90,000) ⇒ **≈ INR 5.8 lakh**.

## Evidence-status tiers
TARGET / DEFINITION / CALCULATED / ASSUMPTION / INDICATIVE / UNRECONCILED / BLOCKED — no value in this
repository is presented as a measured result.
