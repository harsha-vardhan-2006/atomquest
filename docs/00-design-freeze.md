# Rev 2 · Design Freeze — Smart AI Fan

> Source-of-record note (MASTER2 Phase B): this is a Rev 2 source document under `docs/design/rev2/`. It was reviewed file-by-file in the current Stage 2 Phase B audit and received a controlled source note. It is a design freeze table, not a quantitative calculations notebook. It is preserved as a controlled source document. Where it conveys a quantitative requirement, that requirement should be traceable to a calculation or a controlling engineering record. Any figure used as input to later calculations must be checked against the calculation register and the corrected number set in `docs/design/rev2/09-arithmetic-audit.md`. In particular, the mass figure is not closed: the listed components sum to 7.00 kg while the stated total is 6.80 kg; that discrepancy is UNRESOLVED and is recorded in `engineering/audit/MASTER_MASS_RECONCILIATION.md` and tracked in the MASTER2 requirement traceability matrix `engineering/audit/MASTER2_REQUIREMENT_TRACEABILITY_MATRIX.md`.

**Revision 2 · 10 October 2026 · Engineering design frozen on paper. Physical validation still required (see `docs/design/rev2/06-test-plan.md`).**

This document freezes the design targets that everything else is sized against.
Unlike Rev 1, the values below are **selected commitments derived from a real
regulatory boundary (IS 374:2019 + Amendment 1)**, not illustrations.

## 1. Regulatory boundary (research result)

From IS 374:2019 (4th rev.) + Amendment No. 1 (Oct 2022), Table 1 and clause
14.4.1, verified against the published amendment text:

| Requirement (fan size >1,320 ≤1,400 mm)     | Value            | Consequence for our design            |
| ------------------------------------------- | ---------------- | ------------------------------------- |
| Minimum air delivery                        | 245 m³/min       | Design target ≥ 245 CMM at top speed  |
| Minimum service value (air delivery ÷ W)    | 4.1 m³/min/W     | Power ≤ 245/4.1 = **59.8 W**; target ≤ 32 W |
| **Maximum peripheral (blade-tip) speed**    | **30 m/s**       | Governs maximum RPM (§3)              |
| Preferred sizes                             | incl. 1,400 mm   | Sweep 1,400 mm is legal ✓             |
| Scope note 3                                | Fans ≤ 250 RPM "for air circulation" are optional | Our 380 RPM fan is fully in scope |

Also relevant: IS 302 (Part 2/Sec 80) household fan safety; IS 14700
(Part 3/Sec 2) EMC for electronic regulators; IEC 60335-2-80 as international
reference. Compliance is **not yet claimed** — BIS testing per §06 test plan.

## 2. Frozen design targets

| #  | Parameter                       | Frozen value                   | Rationale |
| -- | ------------------------------- | ------------------------------ | --------- |
| T1 | Sweep (rotor diameter)          | 1,400 mm (R = 700 mm)          | Preferred size; luxury segment |
| T2 | Blades                          | 3 × CFRP, 120° spacing         | Agreed design |
| T3 | Top design speed                | **380 RPM**                    | Tip = 27.85 m/s; **7.1% margin under the 30 m/s legal cap** |
| T4 | Idle (min) speed                | 80 RPM                         | Convenience slow mode |
| T5 | Air delivery at top speed       | ≥ 245 m³/min (target 250)      | IS 374 minimum |
| T6 | Input power at top speed        | ≤ 32.4 W (aero input 28.3 W; peak 64.3 W) | Service value 245/28.3 ≈ **8.7** (min 4.1) — corrected thickness ½·ρA·v_a³/2 → 8.65 W ideal; adopted 20.8 W at η_prop 0.42 |
| T7 | Control granularity             | 0–100% speed, 80–380 RPM map   | FOC, continuously variable |
| T8 | Sound pressure                  | ≤ 55 dB(A) @ 3 m, top speed    | Luxury target |
| T9 | Manual tilt (tilt axis)         | ±20° (firmware-limited; actual limit = function of installed ceiling height, §04 §2.2); hard backstop 27° | Binary ceiling rule (13-cad-clearance) |
| T10| Tilt rate                       | ≤ 10°/s, accel ≤ 10°/s²        | Gyro/clearance margins |
| T11| Pan travel                      | −170° … +170°, hard stops ±175° | No slip ring needed |
| T12| Ceiling-to-hub drop             | 450 mm fixed downrod           | Clearance §04 |
| T13| Min ceiling for full ±20° tilt, floor clearance ≥ 1.50 m | **2.660 m** (2.70 m recommended for margin) | **Exact worst case (13-cad-clearance-closure-plan):** lowest tip peaks at θ* = atan(a/R) ≈ 9.73° with z_low = √(R²+a²) = 0.7102 m — deeper than level (0.700 m) or ±20° (0.699 m). Ceiling = 1.50 + 0.45 + 0.7102 ≈ **2.660 m**. Tolerance closure (T-00a CAD) pending before approval.
| T13b | Min ceiling for intermediate tilt tiers (±10° etc.) | **superseded — no intermediate tiers exist** | Binary rule: every tilt in 0° < \|θ\| < ≈19.8° dips deeper than level (z_low peaks at 9.73°), so a ceiling that only just passes at level hosts no intermediate tilt either (13 doc §4).
| T13c | Min ceiling level (0°), floor clearance ≥ 1.50 m | **2.650 m** (boundary; level-only) | 1.50 + 0.45 + 0.700 = 2.65 — passes by exactly 0.00 m; any tilt beyond level fails this ceiling |
| T14| Ceiling rule (tiered rule superseded) | **binary firmware rule** | ≥ 2.660 m ceiling → full ±20°; 2.65–2.660 m → LEVEL ONLY (cap 0°); < 2.65 m → not qualified (level clearance < 1.50 m). Firmware measures installed ceiling height. Hard stop 27° is backstop only. Supersedes the 2.60 m wording and all tiered tables (13 doc §4). |
| T15| Rotor stopped before tilt       | **Enforced by supervisor MCU** | Essential safety rule ( gyro fault quantified in §05) |
| T16| Mass target (moving assembly)   | ≤ 6.8 kg (stated design commitment; UNRECONCILED vs the 7.00 kg listed-component sum in 03 §6 — see BOM §2 and the calculation register §1.3) | Actuator sizing input |
| T17| Operating life                  | 15,000 h bearings; 5,000 h @ L10 blades | Endurance test |

## 3. Speed limit derivation (the key calculation)

Tip speed: v_tip = 2πRN/60 → N_max = 60·v_cap/(2πR) = 60 × 30 / (2π × 0.7)
= **409.3 RPM absolute legal max.**

Selecting 380 RPM: v_tip = 2π×0.7×380/60 = **27.85 m/s** → margin = (30−27.85)/30 = **7.1%**.
(Rev 1's 500 RPM illustration would have been illegal: 36.65 m/s > 30.)

## 4. Operating duty points (used by all downstream sizing)

| Mode        | RPM | Shaft power | Shaft torque | Input power |
| ----------- | --- | ----------- | ------------ | ----------- |
| Idle        | 80  | ~0.4 W      | 0.01 N·m     | ~2.7 W      |
| Sleep worst | 190 | 2.6 W       | 0.13 N·m     | 5.8 W      |
| **Top**     | **380** | **20.8 W** | **0.553 N·m** | **28.3 W** |

(Shaft-power/efficiency chain: 20.8 W shaft = 22.0 W cutoff; actual: 8.65 W min
kinetic power ideal, adopted 20.8 W at conservative η_prop ≈0.42; motor η 0.80 ×
driver η 0.92 → 28.3 W input. (Rev 2.1/Rev 2.2 audits used wrong algebra forms;
corrected here — see §09 audit.) Thrust (correct actuator-disk momentum reaction):
**6.52 N** total (2.17 N per blade × 3); replaces the wrongly-used 13.04 N throughout
Rev 2.x; see §09 audit.)

## Related documents

- `01-blade-aero.md` — blade geometry, twist/chord/thickness schedule, flow calc
- `02-rotor-structure.md` — loads, inertia, modal, spin-proof, balancing
- `03-motor-drive-power.md` — BLDC motor, controller, power budget, BOM
- `04-pan-tilt-mount-clearance.md` — gimbal, actuators, anchors, safety cable, clearance envelope
- `05-controls-failure-cases.md` — controls architecture + every failure case quantified
- `06-test-plan.md` — acceptance criteria (the physical gate)
- `07-bom-budget.md` — bill of materials and budget

**Status: design frozen. Production not claimable until 06-test-plan passes on real hardware.**
