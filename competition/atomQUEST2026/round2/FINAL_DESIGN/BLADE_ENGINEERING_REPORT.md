# Blade engineering report

## Geometry as built

`FD_Blade.SLDPRT` is a lofted blade over six radial stations (260/330/420/510/610/700 mm) with a 9-point cambered section per station, chord tapering 160 -> 120 mm and twist 26 deg -> 12 deg at the sections, carried on a flat-bottom root pad that bolts to a hub pad.

| property | value | provenance |
|---|---|---|
| mass per blade | 1.265 kg | CAD volume x 1350 kg/m3 |
| body box | 555.0 x 170.85 x 83.27 mm | CAD |
| root centrifugal load at 380 RPM | 589 N | analytical |
| root bending moment (1 N placeholder thrust) | 0.56 N.m | analytical |

## Honest status

- The section profile is a **preliminary cambered profile**, not a published, validated airfoil. No lift, drag, thrust or efficiency claim is made.
- The historical 38 deg root pitch is not what the CAD contains: the loft starts at 26 deg because a 38 deg root could not be packaged inside the hub pad envelope without the root edge breaking out of the pad. This deviation is deliberate and is listed in KNOWN_LIMITATIONS.md.
- Blade mass is 1.26 kg against a 0.165 kg target. A solid printed blade at this size cannot meet that target; the part must become a hollow/ribbed shell before it is credible.
- No fatigue, delamination, UV or moisture assessment has been done. FDM polymer blades at 380 RPM are **not** qualified by this work.
- Blade-to-blade geometry is identical by construction (one part, three instances at 0/120/240 deg), so static balance depends on print consistency, not on CAD.
