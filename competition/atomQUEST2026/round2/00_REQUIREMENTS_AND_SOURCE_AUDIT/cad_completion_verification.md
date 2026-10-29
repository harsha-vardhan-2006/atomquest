# CAD completion and verification log (preliminary concepts)

Generated from the native SOLIDWORKS files in this directory on 2026-10-29.

## Deliverable checks

- Both native assembly documents reopened and rebuilt successfully. Model 1 contains 8 unsuppressed referenced components; Model 2 contains 9 unsuppressed referenced components. Referenced part files exist in each model's `01_CAD_PARTS` directory. Each component has a nonzero insertion transform when reopened, but the layout has no mates and has not been checked for relative fit. Treat drawings/assemblies as unconstrained concept layouts, not as validated mechanical fits or motion-ready assemblies.
- Every referenced concept part rebuilt with at least one solid body and a nonzero bounding box. The per-part size, volume, and nominal-density mass ledger is `rebuilt_parts_audit.csv`.
- Each concept assembly has a saved isometric drawing and PDF in `03_DRAWINGS/`. Individual concept part drawings are also saved there.
- Every concept part and each assembly was exported to AP203 STEP in `11_NEUTRAL_EXPORTS/`. Each exchange file passed a basic header/footer and size check. This confirms serialization only, not downstream interoperability geometry equivalence.
- Each SOLIDWORKS application session was exited after its document was saved/exported, before processing the next document.

## Checks that are not passed / not established

- **Motion / articulated range: NOT VERIFIED.** The assemblies are unconstrained layouts with no X/Y revolute joints. No motion study, articulated axis test, or ±20° sweep has passed. A transform-only probe does not establish moving-subassembly kinematics.
- **Clearance / collision: NOT VERIFIED.** Assembly component placements are unconstrained and no clearance scan has passed. Parts are preliminary prismatic/cylindrical concept solids and do not establish shaft/bearing interfaces, servo linkages, travel stops, or the missing fan/blades/downrod. The spherical housing's 50 mm tilt-clearance requirement cannot be inferred from its current cylindrical shell.
- **Mass requirement: NOT CLOSED.** The measured part masses at the assumed densities are CAD-part subtotals only: Model 1 approximately 60.25 kg; Model 2 approximately 37.98 kg. They exclude required items absent from the CAD (fan blades, motor/rotor, bearings, servos, fasteners, cabling, retention hardware, etc.). These preliminary solid-model subtotals already exceed REQ-29's 6.8 kg target; the legacy README estimates (9.03/9.83 kg moving mass) remain unreconciled. No released material assignments or complete product mass roll-up exists.
- **Engineering / operating safety: NOT VERIFIED.** No structural FEA, fatigue, rotor containment, anchor/substrate qualification, servo torque validation for selected hardware, or operating test is represented by these files. Do not use for manufacture or operation.
- The per-part drawings are preliminary isometric views, not dimensioned manufacturing drawings.

## Current recommendation

Treat assemblies, drawings, and neutral exports as reviewable concept geometry only. Do not claim compliance with requirements REQ-12 through REQ-23, REQ-29, REQ-32, or REQ-35 based on these deliverables. Before release, resolve true revolute-axis and load-path geometry, add the missing drive/fan hardware and realistic materials, then run interference, motion, mass, and structural verification with recorded inputs and acceptance criteria.
