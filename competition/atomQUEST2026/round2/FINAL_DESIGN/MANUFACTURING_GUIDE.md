# Manufacturing guide

## Printable parts

| part | material | orientation | supports | STL verified |
|---|---|---|---|---|
| FD_Blade.SLDPRT | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | minimal | yes |
| FD_CableCollar.SLDPRT | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | minimal | yes |
| FD_MotorCover.SLDPRT | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | yes for the shroud lip and vent bridges | yes |
| FD_ServoBracketX.SLDPRT | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | minimal | yes |
| FD_ServoBracketY.SLDPRT | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | minimal | yes |
| FD_TopShroud.SLDPRT | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | yes for the shroud lip and vent bridges | yes |
| FD_TravelStop.SLDPRT | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | minimal | yes |

## Machined / bought parts

The hub, cradle, yoke, ring, adapter, bushings, servo horn and ceiling plate are modelled as aluminium 6061 or steel 1020 for mass purposes. They are structural parts and must **not** be substituted with printed plastic without a new stress check.

## Fasteners

- Hub to rotor flange: 6 x M5 (provisional pitch circle)
- Blade to hub pad: 3 x M4 per blade, captive nut pockets in the pad
- Ceiling plate: 4 x M8 structural anchors (provisional 170 mm PCD)
- Servo brackets: 2 x M3 per bracket

## Print rules

- Print blades with the root pad down and the span vertical to keep layer lines across the root bending direction; do not print flat.
- 4 perimeters minimum, 40% infill for structural printed parts.
- Do not scale any STL: the exported meshes are 1:1 in millimetres and were checked against their CAD bounding boxes.
