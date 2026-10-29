# Model 1 — Dual-Ring Gimbal
## TECHNOMANCERS Smart AI Fan Rev 2 — atomQUEST 2026 Round 2

### Architecture Overview

```
Fixed ceiling plate
  → Structural support housing
    → Outer gimbal ring (X-axis pivot)
      → Inner gimbal ring (Y-axis pivot)
        → Fan carrier plate
          → Motor + hub + 3 CFRP blades
```

- **X-axis pivot**: Outer gimbal ring rotates on shaft supported by bearings in the structural support housing
- **Y-axis pivot**: Inner gimbal ring rotates on shaft supported by bearings in the outer ring
- **Axis intersection**: Near the center of the inner ring (design intent: near CoG to minimize gravity torque)
- **Tilt range**: ±20° each axis (firmware-limited; 27° mechanical backstop)
- **Pan capability**: Achieved through rotation of the entire gimbal assembly about the vertical axis (not currently in scope for Round 2, reserved for future)

### Mass Properties (Preliminary — to be verified by CAD)

| Component | Mass (kg) |
|-----------|-----------|
| Ceiling mounting plate | 2.50 |
| Structural support housing | 3.20 |
| Outer gimbal ring | 1.80 |
| Inner gimbal ring | 1.20 |
| Pivot shafts (2×) | 0.40 |
| Bearing assemblies | 0.60 |
| Servo mounting brackets | 0.50 |
| Servo drive arms/linkages | 0.30 |
| Fan carrier plate | 1.50 |
| Motor mounting interface | 0.40 |
| Cable routing features | 0.20 |
| Protective covers | 0.80 |
| Secondary retention hardware | 0.30 |
| Fasteners and locking hardware | 0.30 |
| Blade set (3× CFRP) | 0.495 |
| Hub/rotor assembly (est.) | 0.23 |
| **Total moving mass** | **9.03** |
| **Total assembly mass** | **14.73** |

**WARNING**: Moving mass (9.03 kg) exceeds the Round 1 target of ≤6.8 kg. This discrepancy must be resolved.
Current Round 1 baseline already has an UNRECONCILED discrepancy: 7.00 kg (component sum) vs 6.80 kg (stated).
Model 1 structural mass increases this gap further.

### Center of Gravity

- Estimated CoG offset below axis intersection: **0.190 m**
- Dominated by blade mass at 0.571 m below pivot
- Axis intersection placement at inner ring center reduces gravity torque
- Full 3D CoG analysis performed in load_analysis_gimbal_servos.py

### Gravity Torque

- Maximum gravity torque per axis: **5.77 N·m** (at ±20° tilt, single axis max)
- Worst case occurs at (θ_X=±20°, θ_Y=0) or (θ_X=0, θ_Y=±20°)
- At combined ±20° both axes: 5.77 N·m on one axis, 5.42 N·m on the other
- At level (0,0): 0 N·m (ideal)

### Servo Requirements (Preliminary)

- 4 servos total: X1+X2 for X-axis, Y1+Y2 for Y-axis
- **Continuous torque per servo (symmetric)**: 7.96 N·m
- **Continuous torque per servo (single failure case)**: 15.92 N·m
- **Peak/stall torque per servo**: 7.96 N·m
- Safety factor: 2.0× on continuous
- Linkage efficiency: 95%
- Static friction multiplier: 1.3×

**NOTE**: One servo CAN hold against gravity in symmetric case (margin 2.20 N·m).
However, the structure MUST support the fan independently of servo holding per REQ-23.

### Tilt Axis Specifications

- X-axis: Revolute joint, shaft diameter 20 mm (to be verified by stress calc), bearing spacing 80 mm
- Y-axis: Revolute joint, shaft diameter 20 mm (to be verified), bearing spacing 80 mm
- Axes approximately perpendicular at design intersection point
- Travel stops: Mechanical hard stops at ±27° (backstop only)
- Servo linkage: 65 mm arm from servo horn to gimbal ring (torque ratio ~3.25×)

### Critical Design Notes

1. **NOT safe for operation** until structural FEA, spin-proof testing, and containment validation are complete
2. **Blade containment margin is BLOCKED**: 128.8 J hazard energy vs 130 J rating basis = thin margin
3. **Ceiling height rule applies**: ≥2.660 m for full ±20° tilt, 2.650-2.660 m level-only, <2.650 m not qualified
4. **Rotor must be stopped before tilt** — enforced by firmware (REQ-11)
5. **All mass properties are preliminary** — actual CAD mass properties required

### How to Open the Assembly

1. Open SOLIDWORKS 2026 SP04.1
2. File → Open → Navigate to `02_CAD_ASSEMBLIES/`
3. Open the main assembly file (.SLDASM)
4. The assembly should show the complete gimbal mechanism with two revolute joints
5. Use the Mate Manager to verify the X-axis and Y-axis revolute mates are correctly defined
6. Use Motion Study to animate the tilt range

### File Structure

```
MODEL_1_DUAL_RING_GIMBAL/
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
2. Mass reconciliation (7.00 vs 6.80 vs 9.03 kg) not resolved
3. Blade material properties not confirmed (T-00c/T-01/T-05 pending)
4. Servo model not selected (torque requirements defined but no specific part)
5. Ceiling substrate and anchoring not specified

### References

- Round 1 design freeze: `/e/atomquest/docs/00-design-freeze.md`
- Round 1 assumptions register: `/e/atomquest/docs/assumptions-register.md`
- Round 1 formulas: `/e/atomquest/docs/formulas.md`
- Round 1 clearance plan: `/e/atomquest/docs/13-cad-clearance-closure-plan.md`
- Load analysis script: `COMMON_ENGINEERING_REFERENCE/load_analysis_gimbal_servos.py`
- Requirements register: `COMMON_ENGINEERING_REFERENCE/REQUIREMENTS_REGISTER.csv`
