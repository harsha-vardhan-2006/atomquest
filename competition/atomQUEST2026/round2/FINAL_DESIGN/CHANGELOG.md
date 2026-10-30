# Changelog

## Round 2 final design package

- Added 18 native parts built by `cad_tools/build_final_parts.py` (printable shroud, cover, collar, brackets, stop; metal yoke, ring, cradle, adapter, hub, bushings, horn; reference motor envelope; blade).
- Added `FD_ROTOR`, `FD_TILT` and `FD_SMART_FAN_ASSEMBLY` with components placed in assembled position and blades at 0/120/240 deg.
- Added STEP exports and printable STL meshes with independent mesh verification.
- Added mass/torque/clearance calculations and the safety gap matrix.
- Assemblies now carry validated mates (created from geometry-matched face pairs; any mate that displaced a component is rejected and never saved).
- Blades now start at the hub pad radius (200 mm) and rest on the pad face instead of floating 45 mm outboard and 6 mm above it.
- The root assembly is rotated -90 deg about X so the finished fan hangs from its ceiling plate with the rotor axis vertical.
- Lightened FD_SupportYoke (solid slabs -> tube boss + webs + thin arms), FD_OuterTiltRing (20 mm wall -> 12 mm, 34 -> 26 mm tall) and FD_TopShroud (5 -> 3 mm cap); moving mass dropped accordingly.
- Added `calculations/final_design_calculations.py` and `cad_tools/verify_step_reimport.py`.
- Superseded the earlier MODEL_1/MODEL_2 concept part sets, which remain untouched for reference.
