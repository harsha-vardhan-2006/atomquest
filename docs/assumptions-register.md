# Assumptions Register — Smart AI Fan (Rev 2)

Rev 1's split of "illustrative vs. calculated" is now tightened: the reference
values are **selected design commitments** (backed by regulation or physics,
not yet by hardware), and each carries explicit traceability. Every Rev 2
number maps to exactly one of the four kinds below.

## A. Design commitments (selected; regulation- or physics-backed)

| ID   | Commitment                              | Value      | Backing |
| ---- | --------------------------------------- | ---------- | ------- |
| A-01 | Rotor diameter                          | 1,400 mm   | IS 374 preferred size |
| A-02 | Blade mass                              | 165 g      | Derived from constructed planform + CFRP density |
| A-03 | Blade CoM radius                        | 0.451 m    | Derived from planform integral |
| A-04 | Blade count                             | 3          | Agreed concept |
| A-05 | Top design speed                        | 380 RPM    | Derived from IS 374 30 m/s cap (margin 7.2%) |
| A-06 | Shaft power at top speed                | 20.8 W     | ideal kinetic power 8.65 W ÷ conservative η_prop 0.42 (corrected derivation) |
| A-07 | Input power at top speed (motor input) | 28.3 W     | 20.8 ÷ (0.80 × 0.92) |
| A-08 | Air delivery target                     | ≥ 245 CMM  | IS 374:2019+Amd.1 Table 1 |
| A-09 | Moving-assembly mass                    | ≤ 6.8 kg   | Mass roll-up table (03 §6) |
| A-10 | CoM offset from tilt axis               | ≤ 22 mm    | Design layout estimate |
| A-11 | Friction moment at axes                 | 1.5 / 1.2 N·m | Gearbox estimate |
| A-12 | CFRP allowable stress                   | ~500 MPa quasi-isotropic | Standard laminate data — **to confirm via T-05 coupons** |
| A-13 | Downrod length                          | 0.45 m     | Selected (T12) |
| A-14 | Dynamic factors (anchor design)         | 2.0× gust/stop; 1.5× standard uplift | Conservative selection |
| A-15 | Prototype qty                           | 3 fans     | Test plan |

## B. Calculated results (valid math; validity limited by A-item accuracy)

| ID   | Result                          | Basis |
| ---- | ------------------------------- | ----- |
| C-01 | Tip speed 27.85 m/s @ 380 RPM   | v = 2πRN/60 |
| C-02 | Centrifugal load 117.5 N/blade @ 380 RPM; 169.2 N @ 456 RPM | F = m·r_cm·ω²; over-speed 120% |
| C-03 | Rotor inertia 0.113 kg·m² (blades 0.1007 + hub/rotor 0.0123) | I = 3mr² + hub estimate |
| C-04 | Rotor stored energy 89.4 J @ 380 RPM | E = ½Iω² |
| C-05 | Start torque 1.50 N·m (0→380 RPM in 3 s) | T = I·dω/dt |
| C-06 | Aero thrust 6.52 N / 2.17 N per blade (momentum reaction) | T = ρ·Q·v_a/2 · v_a ... correct actuator-disk derivation (was 13.05 N, wrong) |
| C-07 | Ideal kinetic power 8.65 W; adopted shaft 20.8 W at η_prop 0.42 (conservative) | kinetic-energy flux of wake (correct derivation); was 18.2→22 W, wrong |
| C-08 | Induced velocity 2.654 m/s | Q/A = 245 CMM / 1.539 m² |
| C-09 | Tilt actuator worst moment 3.0 N·m → rate 6 N·m | gravity + accel + friction + 2× margin |
| C-10 | Anchor demand 150 N → spec 600 N working / 1,500 N ultimate | W×2 + thrust |
| C-11 | Power budget 32.4 W avg / 64.3 W peak; anchor demand 139.9 N (66.7×2 + 6.52) | load roll-up + corrected thrust (was 146.5 N) |
| C-12 | Clearance (exact binary): floor clearance = ceiling − h_rod − z_low(θ); z_low peaks at θ* ≈ 9.73° (√(R²+a²) ≈ 0.7102 m). Thresholds: ≥ 2.660 m full ±20°; 2.650–2.660 m level-only; < 2.650 m not qualified | exact geometric derivation, 13-cad-clearance-closure-plan §4 + `cad_clearance_grid_plan.py` (replaces the tiered rule and all earlier 2.65/2.85 m wording) |
| C-12b | Worst tip drop ≈ 0.710 m below hub at θ* ≈ 9.73° (exact; 0.700 m level / 0.699 m at ±20°). The historical "0.249 m simplified tilt-drop" line is a stale R·sin(20°) approximation — superseded | exact tilt-envelope geometry, `cad_clearance_grid_plan.py` (asserts 0.700/0.710/0.699) |
| C-13 | 1st flap mode ≈ 27 Hz; 1P 6.3 Hz / 3P 19.0 Hz | cantilever estimate |

## C. Not established — requires physical verification (each maps to a T-test)

| ID   | Item                                          | Test gate |
| ---- | --------------------------------------------- | --------- |
| V-01 | Blade mass/CoM per physical blade             | T-01 |
| V-02 | Actual air delivery & shaft power             | T-02, T-03 |
| V-03 | Blade-tip deflection under real load          | T-04 (static) + FEA |
| V-04 | Composite allowables (T/C, ILSS, fatigue, hot-wet) | T-05 |
| V-05 | Spin-proof at 456 RPM                         | T-06 |
| V-06 | Resonance frequencies (tap + running)         | T-08 |
| V-07 | Motor thermal at duty                         | T-09 |
| V-08 | No-load overspeed behavior                    | T-11 |
| V-09 | Electrical safety & EMC                       | T-12, T-13, T-21 |
| V-10 | Actuator torque & worm self-lock              | T-14 |
| V-11 | Runaway interlock response                    | T-15 |
| V-12 | Full 3-D envelope clearance                   | T-00a, T-16 |
| V-13 | Anchor pull + safety-cable arrest             | T-17 |
| V-14 | Power-loss / reboot behaviors                 | T-18 |
| V-15 | Endurance (3,000 h)                           | T-19 |
| V-16 | Security (replay/fuzz/override)               | T-20 |
| V-17 | Formal compliance (BIS IS 374 + IS 302-2/80)  | T-21 |

## Standing safety defaults (unchanged from Rev 1)

- **D-01:** Rotor stopped before pan/tilt movement — enforced by supervisor firmware.
- **D-02:** No prototype operation over people; containment ring until T-06 passes.
- **D-03:** Wi-Fi loss −→ autonomous local control; priority supervisor → local → remote → web → automation.

- **D-04 (this revision — exact binary rule):** lowest-tip law is z_low(θ) = R·cos θ + a·sin θ with worst case θ* = atan(a/R) ≈ 9.73° at z_low = √(R²+a²) ≈ 0.7102 m (~10 mm deeper than level). Ceiling rule is therefore **binary**, not tiered:
  ≥ 2.660 m ceiling → full ±20° tilt; 2.650–2.660 m → LEVEL ONLY (cap 0°, boundary); < 2.650 m → not qualified (level clearance < 1.50 m). Firmware measures installed ceiling height and applies the cap; hard stop 27° is a backstop only, never a working limit.
  Supersedes: the old tiered 3.20/3.00/2.60 m table, the 2.85 m-minimum generation, the "2.65 m passes everywhere" line, the "±10° cap at ~10°" wording, and the 2.60 m tilt-disable wording. See `13-cad-clearance-closure-plan.md` §4 and script `cad_clearance_grid_plan.py`; T-00a CAD tolerance closure pending before approval.
- **D-05 (new):** No-dwell RPM zone 7–24 Hz until T-08 confirms actual modal margin.
  (The D-04 tier above replaced the old wrong "2.15 m floor on 2.85 m ceiling at
  20° tilt" — see §09 audit.)
