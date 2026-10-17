# Rev 2 · T-00c Supplier Datasheet Request Checklist

**Revision 2 · October 2026 · Gate: T-00c (06-test-plan) — no order is placed until this is signed off (BOM §2 procurement gate).**

> Source-of-record note: this checklist operationalizes review item 2
> ("material names such as 'T300-class' are not complete procurement
> specifications"). Columns for machine consumption live in
> `competition/atomQUEST2026/round1/atomquest-smart-ai-fan/data/t00c_supplier_spec_checklist.csv`
> (status column: OPEN until supplier doc received and matched vs the spec table in 03 §1–§4).

## Rule

Every field below must arrive as a **supplier datasheet, certificate, or normative standard reference** — not a name, not a class, not a datasheet-class memory. Any substitution after order re-runs the affected sizing equation (documented change, BOM §2).

## Route A · CFRP prepreg (lead candidate)

| # | Field | Required form |
| --- | --- | --- |
| A1 | Fiber designation | Exact fiber (e.g. T300/T700/T800 product code), not "3K carbon" |
| A2 | Fiber areal weight | g/m² ± tolerance (±5% per T-00b) |
| A3 | Resin system | Exact epoxy product, cure temperature class (120 °C), Tg |
| A4 | Fiber volume fraction | % with tolerance (target 40%) |
| A5 | Prepreg form | UD tape / twill fabric, width, tack level |
| A6 | Laminate data sheet | 0°/±45°/90° tensile & compressive moduli and strengths, Poisson |
| A7 | ILSS | Short-beam value (≥ 45 MPa spec) + test standard cited |
| A8 | Fatigue data | S–N or runout data at 70% UTS class, 10⁷ cycles (T-05 basis) |
| A9 | Hot/wet knockdowns | Retention % at 70 °C/85% RH class (≤5% drop target) |
| A10 | Density | Cured laminate density (mass model uses 1.55 g/cc) |
| A11 | Cure cycle | Ramp/hold/pressure/vacuum windows + recommended press/autoclave |
| A12 | Storage & out-time | Freezer storage temp, shelf life, cumulative out-time limit |
| A13 | Traceability | Batch CoA, expiry,rolled stock ID; Country of origin |
| A14 | Price & lead time | Prototype qty (₹/m² or ₹/preform) + India availability |

## Route B · Aluminium comparison

| # | Field | Required form |
| --- | --- | --- |
| B1 | Al 6061-T6 sheet | ASTM B209 / EN 485 cert, temper T6, 0.4 mm class thickness tolerance |
| B2 | Lot mechanicals | Yield/UTS/elongation per lot (T6 ≥ 276 MPa yield basis) |
| B3 | Sheet surface | Mill finish class, flatness, thickness variation (feeds the 0.36 mm wall wall-visible dent analysis) |
| B4 | Forming route | Formed-halves seam method: roll-lock OR adhesive — supplier must state which they can supply **with joint data** |
| B5 | Seam qualification data | Fatigue + peel + corrosion data for the seam method (gate: seam coupon per T-05 metal addendum) |
| B6 | Al-Li 2099-T83 | Plate availability in prototype qty, lead time, forming limits (comparison option only) |
| B7 | EN 10204 cert type | 3.1 minimum for both aluminium lots |

## Route C · Hybrid backup

| # | Field | Required form |
| --- | --- | --- |
| C1 | S2-glass + carbon prepreg availability | Same fields as A1–A14 for both fibers (only if Route A quotes fail) |

## Non-material T-00c items (from 06-test-plan T-00c verbatim)

| # | Component | Datasheet must match spec table |
| --- | --- | --- |
| D1 | BLDC motor | 03 §1: ≥0.62 N·m cont / 2.5 N·m peak, ≥25 W mech, L10 ≥15,000 h, weight, thermal class |
| D2 | Encoders | AS5048-class absolute, resolution, interface, AEC qualification |
| D3 | SMPS | 24 V/3.5 A + 5 V rail, inrush, leakage class II per 03 §3 |
| D4 | Anchor hardware | M10 G-grade eye-bolt: ≥600 N working / 1,500 N ultimate, with test report format |
| D5 | Worm actuators | ≥6 N·m tilt / ≥2.5 N·m pan **AND** self-lock at rated torque together (risk register TO CONFIRM item) |
| D6 | Safety cable | Ø3 mm SS304 MBS ≥6.5 kN with certificate |

## Sign-off block

- [ ] All received docs matched field-by-field vs 03 §1–§4 spec tables
- [ ] Any mismatch raised as documented change (sizing re-run) before order
- [ ] T-00c sign-off dated & recorded, then orders may be placed

**Status: checklist defined; all items OPEN pending supplier contact. This is a procurement gate, not a design change.**
