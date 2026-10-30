# Known limitations and blocked items

| # | item | status | why | action |
|---|---|---|---|---|
| 1 | Tilt travel | **failed** | measured motion study: 45 poses with interference detection. The yoke already overlaps the top shroud by ~27,500 mm3 at rest and the overlap grows from the first degrees of tilt; new colliding pairs appear from about +2.5 deg on the first axis. No usable travel exists | open up the top shroud / lower the tilt group, move the travel stop out of the ring's swept volume, then re-run the sweep |
| 2 | Engineering drawings | **partial** | 172 dimension entities across 21 sheets, measured off real view edges, but no GD&T, fit tolerances, title block or BOM table | add tolerances, title block and BOM in the drawing UI |
| 2b | Rest-pose interference | **defect** | 7 pairs overlap before any tilt: yoke/shroud 27,510 mm3, ring/travel stop 5,488 mm3, blade/yoke 2,491 mm3 plus four press-fit pairs | correct the geometry, then re-verify |
| 3 | Original motor dimensions | **unmeasured** | no datasheet, no measurement in the repository | complete `08_HARDWARE_DATASHEETS/MEASUREMENT_CHECKLIST.md` |
| 4 | Servo selection | **open** | required torque exceeds a 1.5 N.m class servo once the motor mass is included | re-run the torque sheet after weighing the motor, then pick a real servo and update the brackets |
| 5 | Blade mass | **failed target** | 0.330 kg vs 0.165 kg target | hollow/rib the blade, re-run mass and inertia |
| 6 | Rotor containment | **failed** | rotor energy ~77 J vs 130 J basis | re-qualify containment or reduce rotor mass |
| 7 | Blade root pitch | **deviates from spec** | 26 deg root instead of 38 deg so the root fits the pad | confirm acceptable or enlarge the pad |
| 8 | Aerodynamics | **unvalidated** | preliminary profile, no CFD, no test | treat airflow, thrust and noise as unknown |
| 9 | Material assignment | **missing** | native parts have no SW material, so SW mass uses 1000 kg/m3 | assign materials before using SW mass properties |
| 10 | STEP re-import | **verified, 1 exception** | all 18 STEP files were re-imported with `LoadFile4`; 17 match their native part within 0.5 mm. The spline-lofted blade trims 6.7 mm at the tip and 1.3 mm in thickness, so its effective tip radius is 693 mm, not 700 mm | see `07_ENGINEERING_CALCULATIONS/step_reimport.csv` |
| 11 | Print validation | **not done** | no slicer, no test prints | slice and print fit-check parts first |
| 12 | Cable routing and pinch points | **unverified** | depends on the servo and the measured hardware | review after servo selection |
