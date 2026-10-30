# Safety and test plan

## Compliance gap matrix (IEC 60335-2-80 basis)

| requirement / hazard | design response | verification | status |
|---|---|---|---|
| blade fragmentation | printed blade, no containment | none | **BLOCKED** |
| rotor imbalance | three identical parts | static balance not measured | **BLOCKED** |
| overspeed | original motor control | no limiter in this design | **OPEN** |
| blade-root failure | M4 root bolts, 40% infill | no test | **BLOCKED** |
| gimbal / servo failure | metal pivots carry load, servo only actuates | no test | **OPEN** |
| ceiling attachment | metal downrod into structural plate | no pull test | **OPEN** |
| fastener loosening | nyloc / threadlock specified | not verified | **OPEN** |
| pinch points | ring/cradle gaps, servo horn | not reviewed in motion | **OPEN** |
| wiring damage | collar strain relief, loop at pivot | not verified | **OPEN** |
| motor cooling | ventilated cover, open shroud | not measured | **OPEN** |
| unexpected movement on power loss | none | not addressed | **OPEN** |

## Staged test plan

1. CAD/dimensional check (done: body boxes, exports, envelope table).
2. Fit-check prints against the **measured** motor, motor unpowered.
3. Static inspection of the assembled tilt mechanism by hand.
4. Tilt motion with the rotor disabled; check stops, cable loop, pinch points.
5. Instrumented structural test by qualified personnel.
6. Controlled rotor run inside a rated enclosure, instrumented.
7. Balance and vibration assessment.
8. Thermal and endurance testing.
9. Formal compliance assessment.

**Powered operation is not approved.** A printed blade set has not been qualified at any speed, the rotor stores roughly 77 J at 380 RPM against a 130 J containment basis, and no containment structure exists. Do not run this fan until steps 1-6 are complete.
