# AtomQuest Smart BLDC Ceiling Fan - final design report

## What exists now

- **18 native SOLIDWORKS parts** in `01_NATIVE_PARTS/`, each one solid body, rebuilt and inspected through the API.
- **3 native assemblies** in `04_ASSEMBLIES/`: FD_ROTOR: 4 components, 4 mate features; FD_TILT: 11 components, 4 mate features; FD_SMART_FAN_ASSEMBLY: 7 components, 2 mate features.
- **18 STEP exports** and **7 printable STL meshes**, both verified in `EXPORT_VERIFICATION_REPORT.md`.
- **21 drawing sheets** in `06_DRAWINGS/`, one per part and assembly, each with third-angle views, **172 dimension entities** (`AddDimension2` between parallel model edges plus `AddDiameterDimension2` on circular edges, 21 of 21 sheets dimensioned) and a note carrying its CAD-measured overall size, material and mass.
- **Appearance previews** of the finished fan in `08_VERIFICATION_REPORTS/assembly_*.png`.
- Parameter source of truth in `00_CONFIG/design_parameters.yaml`.

## Architecture

The original motor, rotor, shaft, bearings and internal rotation mechanism are retained untouched and are represented only by `FD_REF_MotorEnvelope.SLDPRT`, a **reference placeholder** whose dimensions are assumed. The new hardware is: a ceiling plate and downrod, a stationary yoke carrying the outer tilt axis, an outer tilt ring carrying the inner axis, an inner cradle carrying the motor adapter, two servo brackets, two pivot bushings, a travel stop and a shroud. Rotation stays entirely inside the original mechanism; the tilt system is separate and never touches the rotating parts.

## Verified

- Every native part opens, rebuilds and contains exactly one solid body with a meaningful bounding box.
- Blade instances are placed at 0/120/240 deg about the rotor axis by component transform, and the assembly report records each transform.
- STEP and STL exports parse as valid single-solid / watertight meshes.
- Mass and torque figures are recomputed from CAD volumes, by two independent scripts: `calculations/final_design_calculations.py` (repo-style calculation sheet) and `cad_tools/verify_and_report.py`.
- Blade roots now start at the hub pad radius (200 mm) and rest on the pad face, and the root assembly is rotated so the finished fan hangs from its ceiling plate with the rotor axis vertical - before this the blades floated 45 mm outboard of the hub and the whole fan lay on its side.

## Not verified - read this before touching the hardware

- **The tilt axes now have a measured motion study, and it fails.** Each mate is created from a geometry-matched face pair with align = CLOSEST and validated by comparing every component transform before and after. `cad_tools/tilt_motion_study.py` then drives both axes through 45 poses (validated against the stored transforms to 1e-13 mm) and runs SOLIDWORKS interference detection at each one, with a positive control that proves the detector finds a deliberate 60 mm collision. Result: the tilt group already overlaps the top shroud at rest (27,510 mm3) and tilting grows that overlap from the first degrees, so there is **no usable travel**. The configured +/-20 deg / +/-15 deg limits are not supported by the geometry. See `08_VERIFICATION_REPORTS/TILT_MOTION_REPORT.md`.
- **Drawings carry dimension entities, but not a full GD&T set.** Each part sheet has dimensions measured off real view edges (the parts are built from undimensioned sketches, so `InsertModelAnnotations4` had nothing to import and dimensions had to be added from the drawing side). GD&T, fit tolerances, a title block and BOM balloons are still missing; `InsertBomTable5` returns nothing in this non-interactive session.
- **The original motor interface is unmeasured.** Motor envelope, mounting PCD, shaft, bearings and hub flange are all assumed values.
- **Mass is over budget.** Moving mass is 10.37 kg against the 6.80 kg frozen budget (+3.57 kg); total mass is 12.49 kg. Blade mass is 0.330 kg each against a 0.165 kg target. Rotor energy is 77 J here and 69 J in the calculation sheet (different inertia estimators); both are below the 130 J containment basis, which is itself unconfirmed.

## Readiness

Suitable for: further CAD review, and a **dimensional fit check of the stationary parts** against measured hardware.

Not suitable for: printing a flight-ready blade set, assembling a working tilt mechanism, or any powered operation. **Powered operation is not approved.**
