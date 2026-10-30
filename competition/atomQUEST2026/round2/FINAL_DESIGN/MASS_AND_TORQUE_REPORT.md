# Mass and tilt-torque report

## Mass by group

| group | mass (kg) | provenance |
|---|---|---|
| stationary | 8.010 | CAD volume x density |
| tilting body (excluding original motor) | 5.119 | CAD volume x density |
| rotating (hub + 3 blades) | 5.664 | CAD volume x density |
| original motor, rotor, shaft, bearings | **not known** | requires weighing |
| total, excluding original hardware | 18.794 | sum of CAD groups |

The historical 6.8 kg BOM cannot be reconciled: this design already reaches 18.79 kg before the original motor, shaft and bearings are counted. The 165 g blade target is also missed by a wide margin - the current solid blade is 1.265 kg each, so the blade mass target and the 6.8 kg total are both flagged as failed (see KNOWN_LIMITATIONS.md).

## Tilt torque

First-order gravity moment: `T = m g d`, with `d` the horizontal distance from the tilt axis to the group centre of mass.

- Tilting body mass `m` = 10.784 kg, CAD-derived COM offset `d` = 25 mm (rotor and cradle sit below the outer tilt axis).
- `T_body` = 2.644 N.m
- Original motor treated as a point mass below the axis: 0.859 N.m per 100 g at a 40 mm offset. The motor mass is unmeasured, so this term is the dominant unknown.
- Servo requirement including 2.0 design margin and 0.85 linkage efficiency: **7.05 N.m (X axis)**, **6.22 N.m (Y axis)**.
- No servo has been selected. A 1.5 N.m class servo with a 30% continuous-duty limit gives only 0.68 N.m, which is below the requirement once the motor mass is included; the design therefore needs either a larger servo, a gear/linkage reduction, or counterbalancing. This is recorded as an open item, not as a passing selection.

## Rotor

- Rotor inertia (analytical, from CAD masses): 0.3432 kg.m2
- Energy at the historical 380 RPM: **271.7 J**
- Blade tip speed at 380 RPM: 27.9 m/s
- The previously quoted 128.8 J assumed a much lighter rotor. With the current masses the stored energy is about 272 J, i.e. roughly twice the 130 J containment basis. Containment is therefore **not** demonstrated and powered operation stays blocked.

All torque and inertia figures are analytically estimated from CAD-derived masses; none are measured or simulated.
