# Known limitations and blocked items

| # | item | status | why | action |
|---|---|---|---|---|
| 1 | Assembly mates | **blocked** | `SelectByID2`, `SelectByRay`, persistent-reference resolution and `Select4` on component entities all fail in this session; `AddMate5` returns error 4 and creates nothing | apply the joint plan in the SOLIDWORKS UI, then re-run `build_final_assemblies.py --verify` |
| 2 | Engineering drawings | **views only** | 21 sheets carry real third-angle views of the final CAD, but dimensioning, tolerances, BOM balloons and the title block are not applied: annotation insertion needs the same selection path that is unavailable here | finish the sheets in the UI |
| 3 | Original motor dimensions | **unmeasured** | no datasheet, no measurement in the repository | complete `08_HARDWARE_DATASHEETS/MEASUREMENT_CHECKLIST.md` |
| 4 | Servo selection | **open** | required torque exceeds a 1.5 N.m class servo once the motor mass is included | re-run the torque sheet after weighing the motor, then pick a real servo and update the brackets |
| 5 | Blade mass | **failed target** | 1.265 kg vs 0.165 kg target | hollow/rib the blade, re-run mass and inertia |
| 6 | Rotor containment | **failed** | rotor energy ~272 J vs 130 J basis | re-qualify containment or reduce rotor mass |
| 7 | Blade root pitch | **deviates from spec** | 26 deg root instead of 38 deg so the root fits the pad | confirm acceptable or enlarge the pad |
| 8 | Aerodynamics | **unvalidated** | preliminary profile, no CFD, no test | treat airflow, thrust and noise as unknown |
| 9 | Material assignment | **missing** | native parts have no SW material, so SW mass uses 1000 kg/m3 | assign materials before using SW mass properties |
| 10 | STEP re-import | **partial** | text/structure verified, not re-imported and compared body-for-body | import each STEP and compare |
| 11 | Print validation | **not done** | no slicer, no test prints | slice and print fit-check parts first |
| 12 | Cable routing and pinch points | **unverified** | depends on the servo and the measured hardware | review after servo selection |
