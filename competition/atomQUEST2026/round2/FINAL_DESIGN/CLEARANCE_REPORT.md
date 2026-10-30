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

## Not verified

- Interference at intermediate tilt positions was not checked by a motion study because assembly mates could not be created in this environment; the envelope table above is a worst-case static bound.
- Cable routing envelope, servo-horn sweep and pinch points are unverified until the servo is selected.
