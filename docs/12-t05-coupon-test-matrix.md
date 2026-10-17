# Rev 2 · T-05 Coupon Test Matrix — CFRP and Aluminium Routes (Equal Criteria)

**Revision 2 · October 2026 · Gate: T-05 (06-test-plan). Both material routes enter this matrix with identical pass criteria — the material decision is then fixed by evidence, not by paper.**

> Source-of-record note: expands 06-test-plan T-05 into an executable specimen
> matrix. Machine-readable version:
> `competition/atomQUEST2026/round1/atomquest-smart-ai-fan/data/t05_coupon_matrix.csv`.
> All allowables used as pass/fail gates come from supplier data via T-00c,
> not from the paper values in 08-material-screening.

## Common rules

- n = 6 specimens per cell (mean − 3σ basis where a distribution exists, runout basis for fatigue)
- Every specimen traceable: lot ID / batch / cure cycle / cure date / operator
- Post-test: all fractures photographed and classified (fibre failure vs adhesive vs delamination — mode matters, 02 §2.3)
- Failure of any gate cell → root-cause → route blocked from adoption until re-pass with documented change

## CFRP route (matrix C)

| ID | Coupon | Standard | Layup/orientation | n | Condition | Pass criterion (gate) |
| --- | --- | --- | --- | --- | --- | --- |
| C-1 | 0° tensile | ASTM D3039 | [0]₄ unidirectional | 6 | RT dry | ≥ A0° from supplier sheet (paper ref: ≥ 1,500 MPa) |
| C-2 | Quasi-iso tensile | ASTM D3039 | [0/±45/90]s | 6 | RT dry | ≥ 570 MPa-equivalent class value from datasheet |
| C-3 | Quasi-iso compression | ASTM D6641 | [0/±45/90]s | 6 | RT dry | ≥ datasheet compression allowable |
| C-4 | ±45° in-plane shear | ASTM D3518 | [+45/−45]ns | 6 | RT dry | ≥ datasheet in-plane shear |
| C-5 | ILSS short-beam | ASTM D2344 | [0]ₙ | 6 | RT dry | **≥ 45 MPa** (design ILSS spec, F-6) |
| C-6 | Tensile fatigue runout | ASTM D7774-class | [0/±45/90]s | 6 | RT dry | **10⁷ cycles @ 70% UTS, no failure** (sparse-runout rule: 5 of 6 runout = pass; any fibre-failure before 3×10⁶ = fail) |
| C-7 | Hot/wet knockdown | D3039 rig | [0/±45/90]s | 6 | 70 °C / 85% RH soak ≥ 168 h | tensile retention **≥ 95%** of C-2 mean |
| C-8 | Damage tolerance (T-05c) | internal | [0/±45/90]s | 6 | RT dry, 1 mm depth gouge at max-stress fibre line | retains **≥ 70%** of C-2 mean strength; no unacceptable delam growth (f-6 criterion) |
| C-9 | Humidity/mass-gain coupon | internal | [0/±45/90]s | 6 | 55 °C / 95% RH, 96 h + 168 h conditioning | weight gain **< 1%** (F-12); hot-wet retest pair vs C-7 |

## Aluminium route (matrix M) — metal blade runs the same gates + seam addendum

| ID | Coupon | Standard | Specimen | n | Condition | Pass criterion |
| --- | --- | --- | --- | --- | --- | --- |
| M-1 | Parent tensile | ASTM E8 | 6061-T6, 0.4 mm-class | 6 | RT | ≥ 276 MPa yield per lot certificate |
| M-2 | Parent fatigue runout | ASTM E466 | sheet axial | 6 | RT | 10⁷ cycles @ stress ≥ 2× envelope worst stress (9.2 MPa ⇒ ≥ 60 MPa) — trivial, documents the endurance-limit gap honestly |
| M-3 | **Seam fatigue** (bonded or roll-lock, per supplier's chosen method) | internal | formed-half specimen with actual seam | 6 | RT | 10⁷ cycles @ load corresponding to the matched-mass blade envelope moment 1.63 N·m × 1.44; no crack initiation from seam |
| M-4 | Seam peel/interlock | supplier method standard | seam coupon | 6 | RT | ≥ supplier qualified minimum; no unintentional seam opening at overspeed-equivalent load |
| M-5 | Seam corrosion | ASTM B117-class | seam coupon | 6 | 500 h salt spray | no crevice corrosion onset at seam (indoor duty, but installation humidity is real) |
| M-6 | Hot/wet retention | E8 rig | parent + seam | 6 | 70 °C (room-duty ceiling) | ≥ 95% of M-1 |

## Equal-criteria reconciliation

- CFRP C-6 fatigue gate (70% UTS) vs aluminium M-2/M-3 gates are **deliberately expressed identically in load terms** (10⁷ cycles at 2× envelope worst case) so neither route gets a softer test.
- The delamination risk the review flagged is closed by C-5 + C-8/C-9, not by tensile strength alone.
- Whichever route passes its full matrix first with supplier-certified allowables becomes the **adopted** blade material; the other route stays as comparison/backup with data on record.
- Both routes additionally face T-01 (165 ± 2 g / CoM gauge) on real blades and the guarded T-06 spin test — no material escapes the physical gate.

**Status: matrix defined; awaiting T-00c supplier docs to load real allowables into the pass criteria. Until then, gates row "paper-ref" values are targets, not allowables.**
