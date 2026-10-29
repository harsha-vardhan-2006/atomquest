# Common Engineering Reference
## TECHNOMANCERS Smart AI Fan Rev 2 — atomQUEST 2026 Round 2

This folder contains shared engineering inputs, calculations, and references used by both Model 1 (Dual-Ring Gimbal) and Model 2 (Spherical Gimbal).

### Contents

```
COMMON_ENGINEERING_REFERENCE/
├── README.md                       # This file
├── REQUIREMENTS_REGISTER.csv       # Complete requirements register (43 requirements)
├── load_analysis_gimbal_servos.py  # Primary load and servo torque analysis
├── assumptions_register.md         # Link to Round 1 assumptions register
├── design_baseline.pdf             # Summary of Round 1 frozen design values
└── verification_checklist.csv      # Machine-readable verification matrix
```

### Key Shared Parameters

**Fan Configuration:**
- Rotor diameter: 1,400 mm (R = 0.7 m)
- Blades: 3 × CFRP, 120° spacing
- Top design speed: 380 RPM (tip 27.86 m/s, 7.1% under 30 m/s cap)
- Legal max: 409.3 RPM (NOT a certified operating target)
- Hazard case: 456 RPM (33.4 m/s tip — NEVER an operating target)

**Mass Properties (Round 1 baseline):**
- Blade mass: 165 g per blade (ASSUMPTION, pending T-01/T-05)
- Blade CoM radius: 0.451 m (ASSUMPTION, pending T-05)
- Moving mass: 7.00 kg (component sum) vs 6.80 kg (stated) — **UNRECONCILED**

**Centrifugal Loading:**
- F_c per blade at 380 RPM: 117.84 N
- F_c per blade at 456 RPM: 169.2 N (hazard case)
- Rotor energy at 380 RPM: 89.5 J
- Rotor energy at 456 RPM: 128.8 J vs 130 J containment basis (THIN MARGIN, BLOCKED)

**Motor Requirements:**
- Continuous torque: ≥0.62 N·m
- Peak torque: ≥2.5 N·m (5 s)
- Mechanical power: ≥25 W
- Control: sensorless FOC, 24 V

**Ceiling Mount:**
- Anchor demand: 139.9 N
- Anchor rating: 600 N working / 1,500 N ultimate (factor 10.7× ultimate)
- Safety cable: SS304, 3 mm dia, 6.5 kN rating (factor 46.5× demand)
- Downrod length: 0.45 m fixed

**Tilt Mechanism:**
- Controlled axes: X and Y (two-axis gimbal)
- Actuators: 4 servos (2 per axis)
- Tilt range: ±20° (firmware-limited)
- Mechanical backstop: ±27°
- Pan: ±170° working, ±175° hard stops (from Round 1, not re-verified for Round 2)

**Safety Requirements:**
- Rotor stopped before tilt (firmware interlock) — REQ-11
- Floor clearance ≥1.50 m at all tilt positions — REQ-17
- Structure carries fan independently of servo holding — REQ-23
- Servo failure must not cause runaway tilt

**Ceiling Height Rule (Binary):**
- ≥2.660 m: full ±20° tilt allowed
- 2.650–2.660 m: level-only (cap 0°)
- <2.650 m: not qualified

### Load Analysis Results Summary

**Model 1 — Dual-Ring Gimbal:**
- Moving mass: 9.03 kg (preliminary)
- CoG offset below axis: 0.190 m
- Max gravity torque per axis: 5.77 N·m
- Required servo continuous rating (symmetric): 7.96 N·m per servo
- Required servo continuous rating (failure case): 15.92 N·m per servo

**Model 2 — Spherical Gimbal:**
- Moving mass: 9.83 kg (preliminary)
- CoG offset below axis: 0.123 m
- Max gravity torque per axis: 4.07 N·m
- Required servo continuous rating (symmetric): 5.63 N·m per servo
- Required servo continuous rating (failure case): 11.25 N·m per servo

**Note:** All mass properties are preliminary estimates. Actual values depend on CAD models.

### Verification Checklist

See `verification_checklist.csv` for the complete machine-readable checklist.
Status legend: VERIFIED | FAILED | NOT RUN | BLOCKED | NOT APPLICABLE

### Sources and References

All calculations trace back to:
1. Round 1 design freeze (`/e/atomquest/docs/00-design-freeze.md`)
2. Round 1 assumptions register (`/e/atomquest/docs/assumptions-register.md`)
3. Round 1 formulas (`/e/atomquest/docs/formulas.md`)
4. Round 1 clearance plan (`/e/atomquest/docs/13-cad-clearance-closure-plan.md`)
5. Round 1 risk register (`/e/atomquest/data/risk_register.csv`)
6. Round 1 validation gates (`/e/atomquest/data/validation_gates.csv`)

### Important Disclaimers

- Nothing in this repository is measured hardware data
- All values are either stated design targets, documented calculations from stated assumptions, or open risk items
- No supplier quotations have been obtained
- No fabrication, energization, powered-rotor, or overspeed testing is authorized
- Conflicts and unresolved items are deliberately preserved
