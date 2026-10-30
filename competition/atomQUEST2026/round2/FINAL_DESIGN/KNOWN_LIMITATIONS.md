# Known limitations and blocked items

| # | item | status | why | action |
|---|---|---|---|---|
| 1 | Tilt motion | **not simulated** | mates are created and validated for zero component displacement, but no motion study drives the axes through their travel | run SOLIDWORKS Motion over the full travel and check the stops |
| 2 | Engineering drawings | **partial** | views and dimension notes exist, but there are no dimension entities, GD&T or title block | add dimensions, tolerances and the title block in the drawing UI |
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
