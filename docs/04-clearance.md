# Rev 2 · Pan/Tilt Kinematics, Clearance Envelope & Geometry (corrected — binary rule)

> Source-of-record note (MASTER2 Phase B): this is a Rev 2 source document for clearance geometry. This revision carries the corrected FIGURES for the 2026 Oct 16/17 boundary-case review — T-00a CAD tolerance closure remains required before any approval (13-cad-clearance-closure-plan; run script `calculations/cad_clearance_grid_plan.py`). Superseded historical rule surfaces (2.85 m-minimum generation; tiered 3.20/3.00/2.60 m; "2.65 m passes everywhere"; "±10° firmware cap at ~10°") are retained inline only where marked SUPERSEDED and must not be quoted as current requirements.

**All values geometric (paper-exact); to be closed with 3-D CAD at P2 per §6 before prototypes (gate T-00a).**

## 1. Geometry constants (frozen)

| Symbol | Value | Meaning |
| ------ | ----- | ------- |
| h_rod  | 0.45 m | ceiling-to-hub drop (T12) |
| R      | 0.70 m | blade tip radius (T1) |
| a      | 0.12 m | hub + motor housing half-height (axial) |
| θ_tilt | working ±20° (T9); mechanical hard stop 27° (backstop only) | firmware rule sets the working limit per installed ceiling (binary, §2.3) |
| θ_pan  | −170°…+170° working (T11), hard stops ±175° | |

## 2. Lowest blade tip — exact treatment

### 2.1 Lowest tip geometry, level hang

Lowest tip below hub = R = −0.700 m. Floor clearance = ceiling − h_rod − 0.700:

| Ceiling height | Floor clearance (level) | Meets 1.50 m rule? |
| ----------------- | ----------------------- | ------------------ |
| 2.40 m | 1.25 m | No |
| 2.65 m | 1.50 m | Yes (exactly — boundary) |
| 2.660 m | 1.510 m | Yes |
| 2.70 m | 1.55 m | Yes |
| 2.85 m | 1.70 m | Yes |
| 3.00 m | 1.85 m | Yes |

### 2.2 Lowest tip at tilt θ — exact law and the worst case

z_low(θ) = R·cos θ + a·sin θ. Differentiating: the drop is deepest where
tan θ = a/R → **θ* = atan(a/R) ≈ 9.73°**, where the tip sits
**√(R² + a²) ≈ 0.7102 m below the hub** — ≈10 mm **deeper** than level
(0.700 m) and ≈11 mm deeper than ±20° (0.699 m). So:

- the binding tilt for floor clearance is ~10°, **not** 0° or 20°;
- the tilt geometry is *not monotone*: z_low(θ) exceeds the level value for **every 0° < |θ| < ≈19.8°** and falls back below it near ±20°.

| Ceiling | Floor clearance at θ* (worst) | At 0° (level) | At ±20° |
| ------- | ---------------------------- | ------------- | ------- |
| 2.660 m | **1.500 m** | 1.510 m | 1.511 m |
| 2.70 m | 1.540 m | 1.550 m | 1.551 m |
| 2.85 m | 1.690 m | 1.700 m | 1.701 m |
| 3.00 m | 1.840 m | 1.850 m | 1.851 m |
| (superseded note) — the earlier "2.85 m is the minimum"/"2.65 m passes everywhere" statements are both reconciled by this exact result (SUPERSEDED) | | | |

### 2.3 Ceiling-rule closure (corrected) — binary

Proof (geometric justification):
min floor clearance at tilt cap θ_c = ceiling − h_rod − max{z_low(θ) : |θ| ≤ θ_c}.
For any allowed cap θ_c ≥ 0 covering 0…θ_c with θ_c ≥ 9.73°, the max is
0.7102 m; for θ_c < 9.73° the max is z_low(θ_c) (increasing in θ_c). Since
z_low rises with θ from level, a ceiling where level *just* passes binds at
every intermediate angle down to the θ* peak — **no intermediate tier can fit**
between the level-only and full cases on a single fixed ceiling.

**Rule (final):**
- ceiling ≥ **2.660 m** → full ±20° tilt (clearance ≥ 1.50 m at all tilts ≤ 20°);
- **2.650 m ≤ ceiling < 2.660 m** → **LEVEL ONLY** (cap = 0°; boundary case 2.650 passes by exactly 0.00 m);
- ceiling < 2.650 m → **not qualified** for this installation (even level fails 1.50 m);
- measurement at install: firmware takes ceiling height (downrod length entered) and applies the binary cap; mechanical 27° hard stop is a backstop only — never a working limit.

Ceiling height reference planes (T-00a scan inputs): 2.55 (not qualified), 2.65 (boundary), 2.70, 2.85, 3.00; exact threshold 2.660 m. See `13-cad-clearance-closure-plan.md` §4; acceptance requires T-00a CAD tolerance closure before approval.

## 3. Highest blade tip (ceiling side)

z_high(θ) = R·cos θ + a·sin θ (upward mirror). At 20°: 0.699 m above hub;
ceiling clearance at 20° = ceiling − 0.45 − 0.699.

| Ceiling | Ceiling clearance at 20° tilt | Adequate |
| ------- | ----------------------------- | -------- |
| 2.65 m | 1.501 m | yes |
| 2.85 m | 1.701 m | yes |
| 3.00 m | 1.851 m | yes |
| 3.25 m | 2.101 m | yes |

Ceiling-side clearance is generous on any realistic ceiling; the binding axis is the floor tip (§2).

## 4. Side clearance (lateral envelope)

Pan does not change the vertical envelope; lateral envelope is a disc of radius R = 0.70 m + buffer ≥ 0.30 m → install ≥ 1.0 m from walls / tall furniture (manual requirement). Pan-vs-wall uses the corner cases only (±175° hard stops); no vertical envelope change from pan.

## 5. Tilt-while-spinning prohibition — geometric statement

Frozen (T15): tilt only with rotor stopped, enforced in controls. The combined gyro + static + fault case is the F-4/F-5 resolution in 05; geometry alone never permits spin-and-tilt.

## 6. CAD closure requirement (P2 / T-00a)

Scan grid: {pan −170°…+170°} × {tilt −27°…+27°} at 0.5° steps = 74,229 poses; thresholds: blade-blade ≥ +1 mm, blade-ceiling ≥ 50 mm, blade-object ≥ 50 mm (cable loop, wires, canopy). Full model set and outputs: `13-cad-clearance-closure-plan.md`. Reference for T-17: arrested-tip height must use the worst-case θ* = 9.73° geometry (not the level case).

---

**Clearance verdict (corrected — single-generation):**
- Floor clearance ≥ 1.50 m → ceiling threshold **≈ 2.660 m for full ±20° tilt** (exact: 2.6602 m).
- 2.65–2.660 m → level-only; < 2.65 m → not qualified.
- Old tiered tables (3.20/3.00/2.60 m), the 2.85-m-*minimum* generation, the "2.65 m everywhere" line, and the "~10° cap" wording are all SUPERSEDED (tracked in 13 doc §4; D-04 updated).
- All figures paper-exact per the exact z_low law; tolerance closure reserved for T-00a CAD before approval.
