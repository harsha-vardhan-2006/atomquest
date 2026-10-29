# Engineering Gap Report — Stage 1 inventory & source audit

Scope: AtomQuest Smart AI Fan Rev 2, mechanical CAD workstream.
Inputs read: `docs/00-design-freeze.md`, `docs/assumptions-register.md`,
`docs/13-cad-clearance-closure-plan.md` (via registers), `data/design_targets.csv`,
`calculations/parametric_fan_model.py`, `cad_models/*`,
`competition/atomQUEST2026/round2/COMMON_ENGINEERING_REFERENCE/*`.
Full file list: `source_inventory.csv` (83 rows).

## 1. What exists today

| Class | Count | Notes |
| --- | --- | --- |
| Native SolidWorks parts (`.SLDPRT`) | 17 | 8 × Model 1, 9 × Model 2 — all created by the earlier round-2 script |
| Native assemblies (`.SLDASM`) | **0** | `02_CAD_ASSEMBLIES/` folders are empty; they are not tracked by git (empty dirs) |
| Drawings (`.SLDDRW`) | **0** | none |
| Neutral CAD (`.STEP`) | **0** | none |
| Mesh CAD (`.stl`) | 7 | **1:4-scale display meshes** from `calculations/parametric_fan_model.py` — display only, not the 1,400 mm design |
| Engineering calculations | 9 `.py` | `parametric_fan_model.py`, `fan_design_calculations.py`, clearance scripts, scenario checks |
| SolidWorks lock files (`~$*`) | 17 | ignored by `round2/.gitignore` |

## 2. Blockers found in the existing CAD tooling

`round2/create_cad_models.py` (the script that produced the 17 parts) **cannot run**:

1. **Syntax error, line 99** — `return new_part(doc=None)def save(doc, path):` (missing newline). Verified with `py_compile`.
2. **`new_part._fresh` is never bound** (lines 30/199) → `AttributeError`, which the broad `except` converts into a false "SOLIDWORKS NOT accessible" exit.
3. **`part_extrude(..., cut=False)` ignores `cut`** — there is no `FeatureCut` call, so `make_pipe()` never bores the rings. `M1_OuterRing`, `M1_InnerRing`, `M2_InnerGimbalRing`, `M2_SphericalHousing` are expected to be **solid cylinders, not rings/shells** (to be confirmed by reopening them in Stage 2).
4. Duplicate dead definitions (`_new_part_using_active_session`, `_new_asm_doc`), `FeatureExtrusion` called with 15 of its 18 arguments, and `SM_create_circle(dia)` passing a **diameter where the API expects a radius** (parts may be 2× the labelled size).

Consequence: every existing part must be **re-opened, rebuilt and measured** before it can be reused (Stage 2 gate).

## 3. Documentation vs. reality

- Both model READMEs state **"CAD status: NOT STARTED"** while 17 parts exist, and instruct the user to open assemblies in `02_CAD_ASSEMBLIES/`, which contains nothing.
- `COMMON_ENGINEERING_REFERENCE/README.md` advertises `assumptions_register.md`, `design_baseline.pdf`, `verification_checklist.csv` — **none of the three exist**; it also claims "43 requirements" while the register holds **42** (REQ-01…REQ-42), with REQ-42 duplicating REQ-32.
- `REQUIREMENTS_REGISTER.csv` is **malformed**: 6 rows (REQ-03, 05, 13, 20, 32, 38) carry an unquoted comma in the description, shifting every later column; the `units` column mixes real units with trace IDs (`T1`, `derived`, `requirement`); status vocabulary is uncontrolled (`TARGET`/`target`, `CALCULATED`/`calculated`).
- REQ-30 states F_c = 117.5 N @380 RPM while `load_analysis_gimbal_servos.py` and the README print **117.84 N** (the arithmetic agrees with 117.84).
- Model READMEs quote **"Peak/stall torque per servo 7.96 N·m"**, but that figure is the *per-axis total for two servos* in the script (3.98 N·m each when shared); it equals the "continuous per servo" figure, while the script's key-results block prints continuous 15.92 > peak 7.96 — contradictory as a spec.

## 4. Open engineering conflicts (not resolved here)

| # | Conflict | Evidence | Handling |
| --- | --- | --- | --- |
| G-01 | Moving mass 6.8 kg (T16) vs 7.00 kg component sum vs **9.03 kg (M1) / 9.83 kg (M2)** round-2 estimates | `00-design-freeze.md`, `load_analysis_gimbal_servos.py` | All three retained; CAD mass properties will be measured in Stage 11 and compared |
| G-02 | Centrifugal load 117.5 N (C-02) vs 117.84 N (script) | `assumptions-register.md` vs script output | Difference = 0.3%; both recorded, script value is the arithmetically correct one |
| G-03 | Blade section: source has **no airfoil**, only a rectangular chord × depth proxy with twist 38°→12° and an undefined pitch reference axis | `parametric_fan_model.py` | Blade will be modelled as a clearly labelled **preliminary** geometry; no aerodynamic performance claim |
| G-04 | Rotor containment 128.8 J vs 130 J basis | `design_targets.csv`, REQ-32 | BLOCKED; spin-proof (T-06) not authorized — never marked verified |
| G-05 | Motor/bearing/shaft physical dimensions unknown | no datasheet, no measured model in repo | Placeholder envelope + interface-control document required; fit **not** labelled verified |
| G-06 | No bearing part numbers, bolt-circle, shaft diameter or fastener schedule anywhere in the repo | searched | Assumed sizes must be recorded as assumptions |
| G-07 | Servo model not selected (torque requirement only) | REQ-20/REQ-35 | Mount pattern modelled to a documented placeholder envelope |
| G-08 | Legacy `cad_models/*.stl` are 1:4 display meshes, not the 1,400 mm design | `parametric_fan_model.py` uses mm values but meshes are display artifacts | Not used as CAD basis; regenerated as STEP/STL from native parts |
| G-09 | Existing 17 parts may be solid (no bores) and 2× oversize | see §2 | Measured in Stage 2; repaired or rebuilt as needed |

## 5. Missing physical inputs (must stay unapproved)

- Blade mass/CoM (T-01), composite allowables (T-05), spin-proof (T-06) — no hardware.
- Motor outer dimensions, shaft extension, bearing fits, mounting-hole pattern.
- Ceiling substrate and anchor qualification; safety-cable certificate.
- Actual servo dimensions, horn geometry and torque curve.
- No FEA material card for the composite; structural analysis readiness only.

**Rule applied throughout:** no dimension, test result, material property or safety
status is invented. Every unavailable input is modelled as a labelled placeholder
and listed here and in the final report.
