# Tilt motion study

Method: `cad_tools/tilt_motion_study.py` opens the native root assembly, reads the two pivot axes off the pivot bushing components, rotates `FD_TILT` and `FD_ROTOR` about them, rebuilds, and runs SOLIDWORKS interference detection at every pose. Volumes come from `IInterference::Volume` in m3 and are reported in mm3; overlaps below 0.5 mm3 are treated as numerical coincidence.

| item | value |
|---|---|
| X pivot axis | point [0.0, 0.157, -0.3] m, direction [1.0, 0.0, 0.0] |
| Y pivot axis | point [0.3, 0.157, 0.0] m, direction [0.0, 0.0, 1.0] |
| travel limits | +/- 20 deg first axis, +/- 15 deg second axis |
| poses sampled | 45 |
| poses that failed | 0 |
| positive control (rotor pushed 60.0 mm) | 12 pairs, 78410.5 mm3 |
| worst pose-application error | 3.47e-14 mm, 4.44e-16 matrix elements |
| rest-pose overlapping pairs | 7 |
| rest-pose repeat check | 0 new pair(s), 0.00 mm3 difference |
| worst motion-induced growth | 28506.0 mm3 |
| no new colliding pair up to | first axis +/- 20.0 deg, second axis +/- 15.0 deg |
| overlaps grow < 100 mm3 up to | first axis none deg, second axis none deg |

## Overlaps present at rest

These exist in the assembly before any tilt is applied. Some are deliberate press/snap interfaces (pivot bushings in the ring, cable collar in the downrod); the rest are parts blocking into each other and must be corrected in CAD before printing.

| pair | volume (mm3) |
|---|---|
| FD_TILT-1/FD_SupportYoke-1 | FD_TopShroud-1 | 27510.4 |
| FD_TILT-1/FD_OuterTiltRing-1 | FD_TILT-1/FD_TravelStop-1 | 5488.0 |
| FD_ROTOR-1/FD_Blade-1 | FD_TILT-1/FD_SupportYoke-1 | 2490.6 |
| FD_TILT-1/FD_OuterTiltRing-1 | FD_TILT-1/FD_PivotBushingX-1 | 1659.4 |
| FD_CableCollar-1 | FD_Downrod-1 | 1577.2 |
| FD_TILT-1/FD_InnerCradle-1 | FD_TILT-1/FD_PivotBushingY-1 | 1131.0 |
| FD_TILT-1/FD_ServoBracketY-1 | FD_TILT-1/FD_TravelStop-1 | 498.2 |

## Sweep result

**Verdict: the tilt mechanism does not have a usable travel range in its current geometry.**

No *newly* colliding pair appears until the limits are reached (20.0 deg first axis, 15.0 deg second axis), but that number is misleading on its own, because the group already overlaps the top shroud at rest, so some of the motion is happening inside solid material. Counting that growth, the usable travel is **none deg / none deg**: the first few degrees of rotation already push the yoke, ring, cradle and servo brackets further into the top shroud, by up to 28506 mm3.

The configured limits are +/-20 deg and +/-15 deg, so they are **not** supported by the current geometry. Before the tilt can be built, the top shroud must be opened up or the tilt group lowered so that the rest pose is clear, and the travel stop re-positioned so that it does not sit in the ring's swept volume.

New interfering pairs appear as the fan tilts:

- X +10.0 deg, Y -15.0 deg: 3 new pair(s) - FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (8836.5 mm3); FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (3035.2 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (1575.8 mm3)
- X +10.0 deg, Y -7.5 deg: 4 new pair(s) - FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (7867.8 mm3); FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (3091.4 mm3); FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (3035.2 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (1575.8 mm3)
- X +10.0 deg, Y +0.0 deg: 5 new pair(s) - FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (7736.2 mm3); FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (3035.2 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (1575.8 mm3); FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (797.4 mm3); FD_TILT-1/FD_PivotBushingX-1 | FD_TopShroud-1 (201.5 mm3)
- X +10.0 deg, Y +7.5 deg: 3 new pair(s) - FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (7867.8 mm3); FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (3035.2 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (1575.8 mm3)
- X +10.0 deg, Y +15.0 deg: 3 new pair(s) - FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (8836.4 mm3); FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (3035.2 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (1575.8 mm3)
- X +20.0 deg, Y -15.0 deg: 5 new pair(s) - FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8147.8 mm3); FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (10912.1 mm3); FD_ROTOR-1/FD_Blade-2 | FD_TopShroud-1 (1462.4 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (767.1 mm3); FD_Downrod-1 | FD_TILT-1/FD_ServoBracketY-1 (7.2 mm3)
- X +20.0 deg, Y -7.5 deg: 5 new pair(s) - FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8147.6 mm3); FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (10839.2 mm3); FD_Downrod-1 | FD_TILT-1/FD_ServoBracketY-1 (2046.8 mm3); FD_ROTOR-1/FD_Blade-2 | FD_TopShroud-1 (1505.0 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (767.1 mm3)
- X +20.0 deg, Y +0.0 deg: 7 new pair(s) - FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8147.5 mm3); FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (11830.5 mm3); FD_Downrod-1 | FD_TILT-1/FD_ServoBracketY-1 (1846.7 mm3); FD_ROTOR-1/FD_Blade-2 | FD_TopShroud-1 (1562.0 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (767.1 mm3); FD_Downrod-1 | FD_TILT-1/FD_InnerCradle-1 (690.7 mm3); FD_Downrod-1 | FD_TILT-1/FD_PivotBushingY-1 (199.9 mm3)
- X +20.0 deg, Y +7.5 deg: 6 new pair(s) - FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8147.9 mm3); FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (10839.2 mm3); FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (2521.3 mm3); FD_Downrod-1 | FD_TILT-1/FD_ServoBracketY-1 (2046.8 mm3); FD_ROTOR-1/FD_Blade-2 | FD_TopShroud-1 (1520.2 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (767.1 mm3)
- X +20.0 deg, Y +15.0 deg: 7 new pair(s) - FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8147.6 mm3); FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (10912.2 mm3); FD_ROTOR-1/FD_Blade-2 | FD_TopShroud-1 (1259.5 mm3); FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (1202.7 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (767.1 mm3); FD_TILT-1/FD_PivotBushingX-1 | FD_TopShroud-1 (267.4 mm3); FD_Downrod-1 | FD_TILT-1/FD_ServoBracketY-1 (7.2 mm3)
- X +2.5 deg, Y +0.0 deg: 1 new pair(s) - FD_Downrod-1 | FD_TILT-1/FD_SupportYoke-1 (667.6 mm3)
- X +5.0 deg, Y +0.0 deg: 1 new pair(s) - FD_Downrod-1 | FD_TILT-1/FD_SupportYoke-1 (3014.3 mm3)
- X +7.5 deg, Y +0.0 deg: 4 new pair(s) - FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (2118.1 mm3); FD_Downrod-1 | FD_TILT-1/FD_SupportYoke-1 (657.2 mm3); FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (336.4 mm3); FD_TILT-1/FD_PivotBushingX-1 | FD_TopShroud-1 (92.9 mm3)
- X +12.5 deg, Y +0.0 deg: 7 new pair(s) - FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (14388.2 mm3); FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8199.4 mm3); FD_TILT-1/FD_TravelStop-1 | FD_TopShroud-1 (5899.9 mm3); FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (1986.4 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (1222.4 mm3); FD_TILT-1/FD_PivotBushingY-1 | FD_TopShroud-1 (252.0 mm3); FD_TILT-1/FD_PivotBushingX-1 | FD_TopShroud-1 (243.0 mm3)
- X +15.0 deg, Y +0.0 deg: 6 new pair(s) - FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (17625.4 mm3); FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8349.0 mm3); FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (2195.9 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (2005.3 mm3); FD_TILT-1/FD_PivotBushingX-1 | FD_TopShroud-1 (4.2 mm3); FD_TILT-1/FD_PivotBushingY-1 | FD_TopShroud-1 (0.6 mm3)
- X +17.5 deg, Y +0.0 deg: 6 new pair(s) - FD_TILT-1/FD_InnerCradle-1 | FD_TopShroud-1 (8710.8 mm3); FD_TILT-1/FD_OuterTiltRing-1 | FD_TopShroud-1 (11432.7 mm3); FD_TILT-1/FD_ServoBracketY-1 | FD_TopShroud-1 (2201.9 mm3); FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (1674.2 mm3); FD_ROTOR-1/FD_Blade-2 | FD_TopShroud-1 (839.2 mm3); FD_Downrod-1 | FD_TILT-1/FD_InnerCradle-1 (91.5 mm3)
- X +0.0 deg, Y -10.0 deg: 1 new pair(s) - FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (1431.2 mm3)
- X +0.0 deg, Y -12.5 deg: 1 new pair(s) - FD_TILT-1/FD_ServoBracketX-1 | FD_TopShroud-1 (1442.5 mm3)

## Limits of this check

- 45 poses on a 10 deg / 7.5 deg grid. Poses between samples are not covered.

- Only tilt was driven; blade spin was held at its modelled angle, so blade-to-body contact at other rotor angles is not covered.

- Interference detection tests body overlap. It does not measure residual clearance, deflection, vibration or fastener loading, and it is not a safety case for powered operation.

- The rest-pose overlaps are real geometry defects; a clean tilt sweep does not excuse them.
