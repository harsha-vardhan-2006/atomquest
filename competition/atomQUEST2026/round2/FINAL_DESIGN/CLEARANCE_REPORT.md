# Clearance report

## Method

A geometric envelope calculation on CAD body boxes, not a collision-sampled motion study: the blade tip is the extreme point (700 mm radius, top at 107.3 mm), the outer tilt axis is at z = 157 mm and the ceiling plate underside is at z = 462 mm.

| tilt (deg) | blade tip z (mm) | clearance to ceiling (mm) | ok |
|---|---|---|---|
| 5 | 168.5 | 293.5 | PASS |
| 10 | 229.6 | 232.4 | PASS |
| 15 | 290.2 | 171.8 | PASS |
| 20 | 349.7 | 112.3 | PASS |
| 25 | 407.8 | 54.2 | PASS |

Maximum tilt that keeps 40 mm of ceiling clearance: **25 deg**.

## Other clearances

- Blade root to hub pad: the blade root sits directly on the pad top face (coincident, no gap by construction).
- Blade sweep to stationary shroud: the shroud is 500 mm across its body box, the blade reaches 700 mm radius, so the blades pass outside the shroud and cannot be enclosed by it; that is intentional for a ceiling fan but means the shroud offers no guarding.
- The 240 mm travel-stop bar is inside the ring envelope; final stop angle must be set after the motion study in the GUI.

## Tilt motion study (measured)

`cad_tools/tilt_motion_study.py` drives both tilt axes through 45 poses and runs SOLIDWORKS interference detection at each one. Volumes are `IInterference::Volume` in m3, reported in mm3; a controlled 200 mm3 overlap was measured as 2.0e-7 to confirm the unit before the sweep.

| check | result |
|---|---|
| positive control (rotor pushed 60.0 mm) | 12 pairs, 78410.5 mm3 |
| pose-application error | <= 1e-13 mm (verified) |
| rest-pose overlapping pairs | 7 |
| usable travel (no growth of existing overlaps) | none / none |

Rest-pose overlapped pairs:

| pair | volume (mm3) |
|---|---|
| FD_TILT-1/FD_SupportYoke-1 | FD_TopShroud-1 | 27510.4 |
| FD_TILT-1/FD_OuterTiltRing-1 | FD_TILT-1/FD_TravelStop-1 | 5488.0 |
| FD_ROTOR-1/FD_Blade-1 | FD_TILT-1/FD_SupportYoke-1 | 2490.6 |
| FD_TILT-1/FD_OuterTiltRing-1 | FD_TILT-1/FD_PivotBushingX-1 | 1659.4 |
| FD_CableCollar-1 | FD_Downrod-1 | 1577.2 |
| FD_TILT-1/FD_InnerCradle-1 | FD_TILT-1/FD_PivotBushingY-1 | 1131.0 |
| FD_TILT-1/FD_ServoBracketY-1 | FD_TILT-1/FD_TravelStop-1 | 498.2 |

**The tilt mechanism has no usable travel in the current geometry.** The yoke already intersects the top shroud at rest, and tilting about either axis grows that overlap from the first few degrees; new colliding pairs appear from about +2.5 deg on the first axis. The configured +/-20 / +/-15 deg limits are therefore not supported. Full result: `08_VERIFICATION_REPORTS/TILT_MOTION_REPORT.md` and `07_ENGINEERING_CALCULATIONS/tilt_motion_report.csv`.

## Not verified

- The motion sweep samples discrete poses and holds the rotor at one angle, so blade-to-body contact at other rotor angles and poses between samples are not covered.
- Cable routing envelope, servo-horn sweep and pinch points are unverified until the servo is selected.
