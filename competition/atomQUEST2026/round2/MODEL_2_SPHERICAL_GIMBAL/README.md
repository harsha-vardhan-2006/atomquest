# Model 2 — Spherical Gimbal
## TECHNOMANCERS Smart AI Fan Rev 2 — atomQUEST 2026 Round 2

### Architecture Overview

```
Fixed ceiling plate
  → Upper structural support
    → Internal X/Y pivot mechanism (load-bearing gimbal)
      → Fan carrier plate
        → Motor + hub + 3 CFRP blades
          → REMOVABLE spherical housing (surrounds mechanism, NOT structural)
```

- **X-axis pivot**: Internal gimbal shaft supported by bearings in upper support
- **Y-axis pivot**: Perpendicular internal gimbal shaft supported by bearings in X-axis housing
- **Axis intersection**: At center of spherical housing interior
- **Spherical housing**: Removable, non-structural exterior shell for aesthetic/premium appearance
- **Inspection cover**: Removable access panel for maintenance
- **Tilt range**: ±20° each axis (firmware-limited; 27° mechanical backstop)
- **Pan capability**: Reserved for future (not in Round 2 scope)

### Mass Properties (Preliminary — to be verified by CAD)

| Component | Mass (kg) |
|-----------|-----------|
| Ceiling mounting plate | 2.00 |
| Upper structural support | 2.50 |
| Inner load-bearing gimbal | 1.50 |
| X-axis pivot components | 0.50 |
| Y-axis pivot components | 0.50 |
| Shafts and bearings | 0.40 |
| Spherical housing sections | 2.80 |
| Removable inspection cover | 0.30 |
| Servo mounting brackets (4×) | 0.40 |
| Servo drive arms/linkages | 0.20 |
| Mechanical travel stops | 0.20 |
| Fan carrier plate | 1.00 |
| Motor mounting interface | 0.30 |
| Cable routing and strain relief | 0.20 |
| Internal reinforcement ribs/webs | 0.30 |
| Secondary retention hardware | 0.30 |
| Fasteners and locking hardware | 0.20 |
| Blade set (3× CFRP) | 0.495 |
| Hub/rotor assembly (est.) | 0.23 |
| **Total moving mass** | **9.83** |
| **Total assembly mass** | **14.33** |

**WARNING**: Moving mass (9.83 kg) exceeds the Round 1 target of ≤6.8 kg. This mass is even higher than Model 1 due to the spherical housing.

### Center of Gravity

- Estimated CoG offset below axis intersection: **0.123 m**
- More compact design means CoG is closer to pivot than Model 1
- Dominated by blade mass below hub
- Reduced CoG offset gives lower gravity torque than Model 1

### Gravity Torque

- Maximum gravity torque per axis: **4.07 N·m** (at ±20° tilt, single axis max)
- Worst case occurs at (θ_X=±20°, θ_Y=0) or (θ_X=0, θ_Y=±20°)
- At combined ±20° both axes: 4.07 N·m on one axis, 3.82 N·m on the other
- **29% lower gravity torque** than Model 1 due to compact CoG placement

### Servo Requirements (Preliminary)

- 4 servos total: X1+X2 for X-axis, Y1+Y2 for Y-axis
- **Continuous torque per servo (symmetric)**: 5.63 N·m
- **Continuous torque per servo (single failure case)**: 11.25 N·m
- **Peak/stall torque per servo**: 5.63 N·m
- Safety factor: 2.0× on continuous
- Linkage efficiency: 95%
- Static friction multiplier: 1.3×
- Linkage arm length: 50 mm (compact design)

**NOTE**: One servo CAN hold against gravity in symmetric case (margin 1.56 N·m).
However, the structure MUST support the fan independently of servo holding per REQ-23.

### Spherical Housing Requirements

The spherical housing must NOT be treated as structural support unless engineered to carry the loads.

**Housing requirements:**
1. Clear of all moving internal parts at all allowed tilt angles (±20° each axis)
2. Sufficient access for inspection and maintenance
3. No cable pinching at any tilt angle
4. No interference with servo arms and linkages
5. Permits assembly and disassembly using a defined sequence
6. Preserves required structural load path through internal gimbal only

**Housing clearance analysis:**
- Internal gimbal diameter: approximately 0.55 m
- Spherical housing inner diameter: approximately 0.65-0.70 m (clearance for movement)
- Clearance required: ≥50 mm between housing and any moving part at extreme tilt
- Housing sections: 2-3 split sections with fasteners for removal

### Tilt Axis Specifications

- X-axis: Revolute joint, shaft diameter 16-20 mm (to be verified), bearing spacing 60-80 mm
- Y-axis: Revolute joint, shaft diameter 16-20 mm (to be verified), bearing spacing 60-80 mm
- Axes approximately perpendicular at intersection point
- Travel stops: Mechanical hard stops at ±27° (backstop only)
- Servo linkage: 50 mm arm from servo horn to gimbal (compact, torque ratio ~2.5×)

### Comparison with Model 1

| Parameter | Model 1 (Dual-Ring) | Model 2 (Spherical) | Advantage |
|-----------|---------------------|---------------------|-----------|
| Moving mass | 9.03 kg | 9.83 kg | Model 1 (-0.8 kg) |
| CoG offset | 0.190 m | 0.123 m | Model 2 (-35%) |
| Max gravity torque | 5.77 N·m | 4.07 N·m | Model 2 (-29%) |
| Servo continuous (each) | 7.96 N·m | 5.63 N·m | Model 2 (-31%) |
| Servo peak (each) | 7.96 N·m | 5.63 N·m | Model 2 (-31%) |
| Mechanical complexity | Higher (2 rings) | Lower (1 gimbal) | Model 2 |
| Manufacturing complexity | Lower (open structure) | Higher (housing) | Model 1 |
| Aesthetics | Industrial open | Premium enclosed | Model 2 |
| Service access | Easy (open) | Requires housing removal | Model 1 |
| Cable routing | Simpler | More complex | Model 1 |
| Cost (preliminary) | Lower | Higher (housing) | Model 1 |

### Critical Design Notes

1. **NOT safe for operation** until structural FEA, spin-proof testing, and containment validation are complete
2. **Blade containment margin is BLOCKED**: 128.8 J hazard energy vs 130 J rating basis = thin margin
3. **Ceiling height rule applies**: ≥2.660 m for full ±20° tilt, 2.650-2.660 m level-only, <2.650 m not qualified
4. **Rotor must be stopped before tilt** — enforced by firmware (REQ-11)
5. **All mass properties are preliminary** — actual CAD mass properties required
6. **Spherical housing is NOT structural** — must not be relied upon for load carrying

### How to Open the Assembly

1. Open SOLIDWORKS 2026 SP04.1
2. File → Open → Navigate to `02_CAD_ASSEMBLIES/`
3. Open the main assembly file (.SLDASM)
4. The assembly should show the internal gimbal mechanism surrounded by the spherical housing
5. The housing should be a separate subassembly or set of parts that can be hidden/suppressed
6. Use the Mate Manager to verify the X-axis and Y-axis revolute mates
7. Use Motion Study to animate and verify clearance between housing and moving parts

### File Structure

```
MODEL_2_SPHERICAL_GIMBAL/
├── 01_CAD_PARTS/          # Individual SOLIDWORKS part files (.SLDPRT)
├── 02_CAD_ASSEMBLIES/     # Assembly files (.SLDASM)
├── 03_DRAWINGS/           # Drawing files (.SLDDRW)
├── 04_ENGINEERING_CALCULATIONS/  # Calculation reports and spreadsheets
├── 05_SIMULATION/         # FEA and motion study files
├── 06_MATERIALS_AND_COMPONENTS/  # Material specs and component datasheets
├── 07_MANUFACTURING/      # Manufacturing process recommendations
├── 08_IMAGES_AND_EXPLODED_VIEWS/  # Renderings and exploded views
├── 09_VERIFICATION_AND_TESTS/     # Verification checklist and test plans
└── 10_FINAL_REPORTS/      # Final design reports
```

### Status

- **Design phase**: Preliminary — calculations complete, CAD not yet created
- **CAD status**: NOT STARTED — waiting for SOLIDWORKS license verification
- **Calculations status**: COMPLETE (preliminary, based on estimated masses)
- **Simulation status**: NOT RUN — pending CAD creation
- **Verification status**: NOT RUN

### Blockers

1. SOLIDWORKS license not confirmed active on this system
2. Mass reconciliation (7.00 vs 6.80 vs 9.83 kg) not resolved
3. Blade material properties not confirmed (T-00c/T-01/T-05 pending)
4. Servo model not selected (torque requirements defined but no specific part)
5. Ceiling substrate and anchoring not specified
6. Spherical housing material and wall thickness not finalized

### References

- Round 1 design freeze: `/e/atomquest/docs/00-design-freeze.md`
- Round 1 assumptions register: `/e/atomquest/docs/assumptions-register.md`
- Round 1 formulas: `/e/atomquest/docs/formulas.md`
- Round 1 clearance plan: `/e/atomquest/docs/13-cad-clearance-closure-plan.md`
- Load analysis script: `COMMON_ENGINEERING_REFERENCE/load_analysis_gimbal_servos.py`
- Requirements register: `COMMON_ENGINEERING_REFERENCE/REQUIREMENTS_REGISTER.csv`
- Material downselection: `/e/atomquest/docs/material-downselection-cfrp-vs-aluminium.md`
