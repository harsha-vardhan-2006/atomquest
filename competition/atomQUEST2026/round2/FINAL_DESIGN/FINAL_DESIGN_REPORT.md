# AtomQuest Smart BLDC Ceiling Fan - final design report

## What exists now

- **18 native SOLIDWORKS parts** in `01_NATIVE_PARTS/`, each one solid body, rebuilt and inspected through the API.
- **3 native assemblies** in `04_ASSEMBLIES/`: FD_ROTOR: 4 components, 0 mate features; FD_TILT: 11 components, 0 mate features; FD_SMART_FAN_ASSEMBLY: 7 components, 0 mate features.
- **18 STEP exports**, **7 printable STL meshes** and **21 drawing sheets**, all verified in `EXPORT_VERIFICATION_REPORT.md` and `06_DRAWINGS/README.md`.
- Parameter source of truth in `00_CONFIG/design_parameters.yaml`.

## Architecture

The original motor, rotor, shaft, bearings and internal rotation mechanism are retained untouched and are represented only by `FD_REF_MotorEnvelope.SLDPRT`, a **reference placeholder** whose dimensions are assumed. The new hardware is: a ceiling plate and downrod, a stationary yoke carrying the outer tilt axis, an outer tilt ring carrying the inner axis, an inner cradle carrying the motor adapter, two servo brackets, two pivot bushings, a travel stop and a shroud. Rotation stays entirely inside the original mechanism; the tilt system is separate and never touches the rotating parts.

## Verified

- Every native part opens, rebuilds and contains exactly one solid body with a meaningful bounding box.
- Blade instances are placed at 0/120/240 deg about the rotor axis by component transform, and the assembly report records each transform.
- STEP and STL exports parse as valid single-solid / watertight meshes.
- Mass and torque figures are recomputed from CAD volumes.

## Not verified - read this before touching the hardware

- **No assembly mates exist.** SOLIDWORKS rejected every mate attempt in this non-interactive session (selection APIs return False, AddMate5 error 4). The assemblies are correctly positioned collections of components, not articulated mechanisms. The joint list that must be applied in the GUI is in `07_ENGINEERING_CALCULATIONS/assembly_joint_plan.json`.
- **Drawings exist but are not dimensioned.** `06_DRAWINGS/` holds 21 sheets (one per part and assembly) with real third-angle views generated from the native models. Dimensions, tolerances, BOM balloons and the title block still have to be added in the UI, because annotation insertion needs the same selection path that is unavailable here.
- **The original motor interface is unmeasured.** Motor envelope, mounting PCD, shaft, bearings and hub flange are all assumed values.
- **Blade mass is 7.7x the target** and the rotor energy is about twice the old containment basis.

## Readiness

Suitable for: further CAD review, and a **dimensional fit check of the stationary parts** against measured hardware.

Not suitable for: printing a flight-ready blade set, assembling a working tilt mechanism, or any powered operation. **Powered operation is not approved.**
