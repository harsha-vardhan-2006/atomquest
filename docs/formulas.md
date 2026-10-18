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

## 5. Tilt clearance geometry (exact law — supersedes the older R·sin(θ) approximation)
`z_low(θ) = R·cos(θ) + a·sin(θ)` with a = 0.12 m hub half-height; worst case at θ* = atan(a/R) ≈ 9.73°
  → z_low* = √(R² + a²) ≈ **0.7102 m** (deeper than level 0.700 m or ±20° 0.699 m).
- Binary ceiling rule: **≥ 2.660 m → full ±20° tilt; 2.650–2.660 m → level-only (cap 0°); < 2.650 m → not qualified**.
- Supervisor interlock: tilt capped by this rule; mechanical 27° stop is a backstop only (13-cad-clearance-closure-plan).

## 6. Supervisor protection (definitions, not test results)
- Plausibility gates: −10…+80 °C, rate ≤ 3 K/s; implausible input → safe default curve.
- Motor NTC trip 165 °C. Supervisor watchdog 350 ms.
- Independent defenses: self-locking worm (holds on power loss) | encoders + limit switches + hard stops | supervisor raw power cut.
- Comfort targets: response ≤ 5 s (local mode); ≥ 95 % success over the 16 defined scenarios (`data/scenarios.csv`).

## 7. Cost model (planning estimates — **no quotations obtained**)
- Source of truth: `docs/cost_basis.md` (added 18 Oct 2026; **replaces the earlier fixed-BOM figures**),
  line items in `data/bom_ranges.csv`. Legacy per-item fixed BOM kept for traceability only in `data/bom.csv`.
- Round 2 Level 1 prototype: lines **INR 6,400–13,000**; +10 % contingency ⇒ **INR 7,040–14,300**
  (central ≈ INR 10,700; the submission PDF quotes ≈ **INR 10,000 (7,000–14,000)**, rounded to the nearest thousand).
- Full single-fan prototype: lines **INR 15,600–29,900**; +10 % contingency ⇒ **INR 17,160–32,890**
  (central ≈ INR 25,000; the submission PDF quotes ≈ **INR 25,000 (17,000–33,000)**).
- The earlier "≈ INR 26,650 per fan / ≈ INR 5.8 lakh for 3 fans" figures are **withdrawn**: the programme
  breakdown could not be reconciled with 3 × per-fan cost. The 26,650 sits inside the full-fan range, so the
  per-fan estimate barely moved; the programme figure was removed from the abstract (see `docs/cost_basis.md`).
- Derived check: `python calculations/fan_design_calculations.py` recomputes the line sums, contingency and
  rounding, and asserts the submission PDF quotes the new ranges (and no withdrawn figure).

## Evidence-status tiers
TARGET / DEFINITION / CALCULATED / ASSUMPTION / INDICATIVE / UNRECONCILED / BLOCKED — no value in this
repository is presented as a measured result.
