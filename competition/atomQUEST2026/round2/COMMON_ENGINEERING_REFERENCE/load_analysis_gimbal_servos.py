#!/usr/bin/env python3
"""
Load Analysis for TECHNOMANCERS Smart AI Fan Rev 2
Four-Servo Gimbal Mechanisms (Model 1: Dual-Ring Gimbal, Model 2: Spherical Gimbal)

SI units throughout. All results traceable to Round 1 design baseline.
REVISED: Fixed inertia calculation to use d^2 not CoG^2 factor.
"""

import math

# =============================================================================
# ROUND 1 DESIGN BASELINE (verified from existing repository)
# =============================================================================
R_BLADE = 0.70
A_HUB_HALF_HEIGHT = 0.12
N_DESIGN = 380
N_HAZARD = 456
RPM_CAP = 409.3
M_BLADE = 0.165
M_BLADE_COM_R = 0.451
M_MOVING_BASE = 7.00  # component sum (UNRECONCILED vs 6.80 stated)
M_HUB_ESTIMATE = 0.23
G = 9.81

M_BLADES_TOTAL = 3 * M_BLADE  # 0.495 kg

OMEGA_DESIGN = 2 * math.pi * N_DESIGN / 60
F_C_B380 = M_BLADE * M_BLADE_COM_R * OMEGA_DESIGN**2
E_380 = 0.5 * 0.113 * OMEGA_DESIGN**2

print("BASELINE: Tip@380=%.2f m/s, F_C_blade@380=%.2f N, E@380=%.1f J, E@456=%.1f J" % (
    2*math.pi*R_BLADE*N_DESIGN/60, F_C_B380, E_380, 0.5 * 0.113 * (2*math.pi*N_HAZARD/60)**2))

# =============================================================================
# MODEL 1 - DUAL-RING GIMBAL
# =============================================================================
M_CEILING_P = 2.5
M_SUPPORT = 3.2
M_OUTER_RING = 1.8
M_INNER_RING = 1.2
M_SHAFTS = 0.4
M_BEARINGS = 0.6
M_SRV_MOUNT = 0.5
M_SRV_ARM = 0.3
M_FAN_CARRIER = 1.5
M_MOTOR_IF = 0.4
M_CABLE = 0.2
M_COVER = 0.8
M_RETENTION = 0.3
M_FASTENERS = 0.3

M_FIXED_M1 = M_CEILING_P + M_SUPPORT
M_MOVING_M1 = (M_OUTER_RING + M_INNER_RING + M_SHAFTS + M_BEARINGS + M_SRV_MOUNT + M_SRV_ARM +
               M_FAN_CARRIER + M_MOTOR_IF + M_CABLE + M_COVER + M_RETENTION + M_FASTENERS +
               M_BLADES_TOTAL + M_HUB_ESTIMATE)

H_BELOW_M1 = A_HUB_HALF_HEIGHT + M_BLADE_COM_R  # 0.571 m

# CoG: weighted average, but blade mass at large distance dominates
# Blade CoM is 0.571m below pivot. Other components close to pivot.
# Total mass below needs to be balanced by structure above (rings are symmetric)
# For a reasonable estimate: the CoG offset is roughly where the mass is concentrated
# The ring masses (outer+inner) are symmetric about pivot, so their CoG is at pivot
# The bearings/shafts are at pivot
# The fan carrier, motor interface, blades are below pivot
# Net CoG = (mass_below * h_below) / total_mass

mass_below_M1 = M_FAN_CARRIER + M_MOTOR_IF + M_BLADES_TOTAL + M_HUB_ESTIMATE * 0.5 + M_CABLE + M_RETENTION
h_below_M1 = H_BELOW_M1  # blade CoM dominates
COG_M1 = mass_below_M1 * h_below_M1 / M_MOVING_M1
# Remaining components (rings, bearings, shafts, servo mounts, covers) are near pivot

print("\nMODEL 1: Fixed=%.2f kg, Moving=%.2f kg, Total=%.2f kg" % (M_FIXED_M1, M_MOVING_M1, M_FIXED_M1+M_MOVING_M1))
print("  mass_below=%.2f kg at h=%.3f m, CoG_offset=%.3f m" % (mass_below_M1, h_below_M1, COG_M1))

# =============================================================================
# MODEL 2 - SPHERICAL GIMBAL  
# =============================================================================
M_CEILING_P2 = 2.0
M_SUPPORT2 = 2.5
M_INNER_GIMBAL = 1.5
M_X_PIVOT = 0.5
M_Y_PIVOT = 0.5
M_SHAFTS2 = 0.4
M_SPHER_HOUSING = 2.8
M_INSPECT_COVER = 0.3
M_SRV_MOUNT2 = 0.4
M_SRV_ARM2 = 0.2
M_STOPS = 0.2
M_FAN_CARRIER2 = 1.0
M_MOTOR_IF2 = 0.3
M_CABLE2 = 0.2
M_REINF = 0.3
M_RETENTION2 = 0.3
M_FASTENERS2 = 0.2

M_FIXED_M2 = M_CEILING_P2 + M_SUPPORT2
M_MOVING_M2 = (M_INNER_GIMBAL + M_X_PIVOT + M_Y_PIVOT + M_SHAFTS2 + M_SRV_MOUNT2 + M_SRV_ARM2 +
               M_STOPS + M_FAN_CARRIER2 + M_MOTOR_IF2 + M_CABLE2 + M_REINF + M_RETENTION2 +
               M_FASTENERS2 + M_SPHER_HOUSING + M_INSPECT_COVER + M_BLADES_TOTAL + M_HUB_ESTIMATE)

H_BELOW_M2 = A_HUB_HALF_HEIGHT + M_BLADE_COM_R * 0.85  # compact design

mass_below_M2 = M_FAN_CARRIER2 + M_MOTOR_IF2 + M_BLADES_TOTAL + M_HUB_ESTIMATE * 0.5 + M_CABLE2 + M_RETENTION2
COG_M2 = mass_below_M2 * H_BELOW_M2 / M_MOVING_M2

print("\nMODEL 2: Fixed=%.2f kg, Moving=%.2f kg, Total=%.2f kg" % (M_FIXED_M2, M_MOVING_M2, M_FIXED_M2+M_MOVING_M2))
print("  mass_below=%.2f kg at h=%.3f m, CoG_offset=%.3f m" % (mass_below_M2, H_BELOW_M2, COG_M2))

def grav_torque_3d(mass, cog_z, tx_deg, ty_deg):
    """Gravity torque on X and Y axes for 3D gimbal. CoG initially at (0,0,-cog_z)."""
    tx = math.radians(tx_deg)
    ty = math.radians(ty_deg)
    x0, y0, z0 = 0.0, 0.0, -cog_z
    
    # Rotate about X: (x, y*cos(tx)+z*sin(tx), -y*sin(tx)+z*cos(tx))
    x1, y1, z1 = x0, y0*math.cos(tx)+z0*math.sin(tx), -y0*math.sin(tx)+z0*math.cos(tx)
    # Rotate about Y: (x*cos(ty)-z*sin(ty), y, x*sin(ty)+z*cos(ty))
    x2 = x1*math.cos(ty) - z1*math.sin(ty)
    y2 = y1
    z2 = x1*math.sin(ty) + z1*math.cos(ty)
    
    tX = mass * G * y2  # torque about X-axis = M*g * (perpendicular distance in Y)
    tY = mass * G * x2  # torque about Y-axis = M*g * (perpendicular distance in X)
    return tX, tY, x2, y2

# Test angles across the ±20° envelope
angles = [(0,0),(20,0),(-20,0),(0,20),(0,-20),
          (20,20),(20,-20),(-20,20),(-20,-20),
          (10,10),(-10,-10),(15,-15),(-15,15),
          (5,20),(20,5),(-5,-20),(-20,-5)]

print("\n" + "="*70)
print("MODEL 1 - GRAVITY TORQUE ANALYSIS (M_MOVING=%.2f kg, CoG=%.3f m below axis)" % (M_MOVING_M1, COG_M1))
print("="*70)
print("%-8s %-8s %-10s %-10s %-8s %-8s %-8s %-8s" % ("Theta_X","Theta_Y","Torque_X","Torque_Y","|T_X|","|T_Y|","CoG_X","CoG_Y"))
print("-"*72)

max_tx1, max_ty1 = 0, 0
worst_x1, worst_y1 = None, None
for tx, ty in angles:
    tX, tY, cx, cy = grav_torque_3d(M_MOVING_M1, COG_M1, tx, ty)
    ax, ay = abs(tX), abs(tY)
    if ax > max_tx1:
        max_tx1 = ax
        worst_x1 = (tx, ty, tX, tY, cx, cy)
    if ay > max_ty1:
        max_ty1 = ay
        worst_y1 = (tx, ty, tX, tY, cx, cy)
    print("%8.1f %8.1f %10.2f %10.2f %8.2f %8.2f %8.3f %8.3f" % (tx, ty, tX, tY, ax, ay, cx, cy))

print("\nMODEL 1 worst case X: %.2f N·m at (%.1f, %.1f)°" % (max_tx1, worst_x1[0], worst_x1[1]))
print("MODEL 1 worst case Y: %.2f N·m at (%.1f, %.1f)°" % (max_ty1, worst_y1[0], worst_y1[1]))

print("\n" + "="*70)
print("MODEL 2 - GRAVITY TORQUE ANALYSIS (M_MOVING=%.2f kg, CoG=%.3f m below axis)" % (M_MOVING_M2, COG_M2))
print("="*70)
print("%-8s %-8s %-10s %-10s %-8s %-8s %-8s %-8s" % ("Theta_X","Theta_Y","Torque_X","Torque_Y","|T_X|","|T_Y|","CoG_X","CoG_Y"))
print("-"*72)

max_tx2, max_ty2 = 0, 0
worst_x2, worst_y2 = None, None
for tx, ty in angles:
    tX, tY, cx, cy = grav_torque_3d(M_MOVING_M2, COG_M2, tx, ty)
    ax, ay = abs(tX), abs(tY)
    if ax > max_tx2:
        max_tx2 = ax
        worst_x2 = (tx, ty, tX, tY, cx, cy)
    if ay > max_ty2:
        max_ty2 = ay
        worst_y2 = (tx, ty, tX, tY, cx, cy)
    print("%8.1f %8.1f %10.2f %10.2f %8.2f %8.2f %8.3f %8.3f" % (tx, ty, tX, tY, ax, ay, cx, cy))

print("\nMODEL 2 worst case X: %.2f N·m at (%.1f, %.1f)°" % (max_tx2, worst_x2[0], worst_x2[1]))
print("MODEL 2 worst case Y: %.2f N·m at (%.1f, %.1f)°" % (max_ty2, worst_y2[0], worst_y2[1]))

# =============================================================================
# INERTIA CALCULATION (REVISED)
# =============================================================================
# For a 3-blade rotor about the hub axis: I_rotor = 3 * M_BLADE * R_BLADE_COM^2
# = 3 * 0.165 * 0.451^2 = 0.1007 kg·m² (matches Round 1 calculation C-03)
# Hub/rotor estimate adds ~0.0123 kg·m², total ~0.113 kg·m²

# For the GIMBAL axes (X and Y tilt axes), the inertia is DIFFERENT.
# It's the inertia of the moving assembly about the tilt axis.
# This depends on the mass distribution relative to the tilt axis.

# For a simplified model where the moving mass is concentrated at CoG:
# I_tilt_axis = M_MOVING * (CoG_offset_perpendicular_to_axis)^2
# This is the MINIMUM possible inertia (point mass at CoG).
# Actual inertia is HIGHER due to mass distribution (blades are extended).

# Better estimate: include blade inertia contribution
# Blades rotate about hub center, but hub center is at tilt axis intersection
# For blade at angle phi from X-axis, distance from X-axis = R_BLADE_com * sin(phi)
#   when blade is in Y-Z plane, or similar
# For 3 blades at 0, 120, 240°, average sin^2 over the 3 blades:
# sin^2(0) + sin^2(120) + sin^2(240) = 0 + 3/4 + 3/4 = 1.5, avg = 0.5
# So effective blade contribution to I_x = M_BLADE * R_BLADE_COM^2 * 0.5 per blade
# Per 3 blades: 3 * 0.165 * 0.451^2 * 0.5 = 0.0504 kg·m²

# For the full moving assembly, the dominant contribution is the blade inertia
# about the tilt axis. The structural components contribute smaller amounts.

# Model 1: Dual-ring gimbal - blades hang below pivot, rings are symmetric
# I_x_m1 ≈ I_blades_about_x + M_rings * r_ring^2 + M_other * h^2

I_BLADE_3D = M_BLADES_TOTAL * M_BLADE_COM_R**2 * 0.5  # 3 blades, average factor
I_HUB_APPROX = M_HUB_ESTIMATE * (0.1)**2  # hub approximated as point at small offset
I_CARRIER = M_FAN_CARRIER * COG_M1**2  # carrier plate at CoG
I_MOTOR = M_MOTOR_IF * COG_M1**2
I_STRUCTURAL_M1 = (M_OUTER_RING + M_INNER_RING + M_SHAFTS + M_BEARINGS + M_SRV_MOUNT + 
                   M_SRV_ARM + M_COVER + M_FASTENERS) * (0.02)**2  # near pivot

I_X_M1 = I_BLADE_3D + I_HUB_APPROX + I_CARRIER + I_MOTOR + I_STRUCTURAL_M1
I_Y_M1 = I_X_M1  # symmetric assumption

# Model 2: Compact, blades closer to pivot
I_BLADE_3D_M2 = M_BLADES_TOTAL * (M_BLADE_COM_R * 0.85)**2 * 0.5
I_HUB_APPROX_M2 = M_HUB_ESTIMATE * (0.08)**2
I_CARRIER_M2 = M_FAN_CARRIER2 * COG_M2**2
I_MOTOR_M2 = M_MOTOR_IF2 * COG_M2**2
I_STRUCTURAL_M2 = (M_INNER_GIMBAL + M_X_PIVOT + M_Y_PIVOT + M_SHAFTS2 + M_SRV_MOUNT2 +
                   M_SRV_ARM2 + M_SPHER_HOUSING + M_INSPECT_COVER + M_STOPS + M_CABLE2 + 
                   M_REINF + M_FASTENERS2 + M_RETENTION2) * (0.02)**2

I_X_M2 = I_BLADE_3D_M2 + I_HUB_APPROX_M2 + I_CARRIER_M2 + I_MOTOR_M2 + I_STRUCTURAL_M2
I_Y_M2 = I_X_M2

# Also add rotor spin inertia for reference (this is what Round 1 computed)
I_ROTOR_SPIN = 0.113  # from Round 1, includes blade rotation about hub axis

print("\n" + "="*70)
print("INERTIA ABOUT TILT AXES")
print("="*70)
print("Model 1: I_X = %.4f, I_Y = %.4f kg·m² (about tilt axes)" % (I_X_M1, I_Y_M1))
print("  Blade contribution: %.4f kg·m²" % I_BLADE_3D)
print("  Hub contribution: %.4f kg·m²" % I_HUB_APPROX)
print("Model 2: I_X = %.4f, I_Y = %.4f kg·m² (about tilt axes)" % (I_X_M2, I_Y_M2))
print("  Blade contribution: %.4f kg·m²" % I_BLADE_3D_M2)
print("For reference (Round 1): I_rotor_spin = %.3f kg·m² (about spinner axis)" % I_ROTOR_SPIN)
print("NOTE: Tilt-axis inertia is MUCH smaller than spin-axis inertia.")
print("      Acceleration/deceleration torque for tilt is therefore small.")
print()

# Acceleration torque
ANG_ACCEL = math.radians(10.0)  # 10 deg/s² max tilt accel (design freeze T10)
T_ACCEL_X1 = I_X_M1 * ANG_ACCEL
T_ACCEL_Y1 = I_Y_M1 * ANG_ACCEL
T_ACCEL_X2 = I_X_M2 * ANG_ACCEL
T_ACCEL_Y2 = I_Y_M2 * ANG_ACCEL

print("Accel torque @ 10°/s²: M1 X=%.2f Y=%.2f, M2 X=%.2f Y=%.2f N·m" % (
    T_ACCEL_X1, T_ACCEL_Y1, T_ACCEL_X2, T_ACCEL_Y2))

# =============================================================================
# FRICTION AND EFFICIENCY
# =============================================================================
BEARING_FRIC_PER = 0.015  # N·m per bearing (ball bearing, light load)
BEARINGS_PER_AXIS = 2
BEARING_FRIC = BEARING_FRIC_PER * BEARINGS_PER_AXIS  # 0.030 N·m per axis

# Static friction is higher - account for startup
STATIC_MULT = 1.3

# Linkage efficiency (servo horn -> linkage -> ring)
LINKAGE_EFF = 0.95

# Safety factor for servo sizing
SF = 2.0

print("\n" + "="*70)
print("FRICTION AND EFFICIENCY")
print("="*70)
print("Bearing friction per axis: %.3f N·m (%d bearings × %.3f N·m each)" % (BEARING_FRIC, BEARINGS_PER_AXIS, BEARING_FRIC_PER))
print("Static friction multiplier: %.1f" % STATIC_MULT)
print("Linkage efficiency: %.0f%%" % (LINKAGE_EFF*100))
print("Servo safety factor: %.1f" % SF)
print()

# =============================================================================
# TOTAL SERVO TORQUE REQUIREMENTS
# =============================================================================
def servo_req(max_grav, accel, fric):
    """Compute servo torque requirements for one axis with 2 servos."""
    T_base = max_grav + accel + fric  # worst-case combined load
    T_servo_out = T_base / LINKAGE_EFF  # at servo output shaft
    T_with_static = T_servo_out * STATIC_MULT  # startup torque
    T_continuous_rating = T_with_static * SF  # required servo continuous rating
    T_per_servo_sym = T_continuous_rating / 2  # each servo in symmetric case
    T_per_servo_fail = T_continuous_rating  # single-servo-failure case
    T_holding = max_grav  # holding against gravity only (static, no accel)
    return {
        'T_base': T_base,
        'T_servo_out': T_servo_out,
        'T_with_static': T_with_static,
        'T_continuous': T_continuous_rating,
        'T_per_servo_sym': T_per_servo_sym,
        'T_per_servo_fail': T_per_servo_fail,
        'T_holding': T_holding,
    }

print("="*70)
print("SERVO TORQUE REQUIREMENTS SUMMARY")
print("="*70)

requirements = {}
for model, mgx, mgy, ax1, ay1 in [
    ("Model 1", max_tx1, max_ty1, T_ACCEL_X1, T_ACCEL_Y1),
    ("Model 2", max_tx2, max_ty2, T_ACCEL_X2, T_ACCEL_Y2)
]:
    print("\n%s (M_mov=%.2f kg, CoG=%.3f m, I_xx=%.4f kg·m²):" % (
        model, (M_MOVING_M1 if model=="Model 1" else M_MOVING_M2),
        (COG_M1 if model=="Model 1" else COG_M2),
        (I_X_M1 if model=="Model 1" else I_X_M2)))
    print("-"*55)
    
    for axis_name, max_g, acc in [("X-axis", mgx, ax1), ("Y-axis", mgy, ay1)]:
        r = servo_req(max_g, acc, BEARING_FRIC)
        requirements["%s_%s" % (model, axis_name)] = r
        
        print("  %s:" % axis_name)
        print("    Max gravity torque: %.2f N·m" % max_g)
        print("    Acceleration torque: %.3f N·m" % acc)
        print("    Bearing friction: %.3f N·m" % BEARING_FRIC)
        print("    Base required torque: %.2f N·m" % r['T_base'])
        print("    / Linkage efficiency: %.2f N·m at servo" % r['T_servo_out'])
        print("    * Static factor: %.2f N·m (startup)" % r['T_with_static'])
        print("    * Safety factor %.1f: %.2f N·m continuous rating required" % (SF, r['T_continuous']))
        print("    Per servo (symmetric, 2 servos): %.2f N·m each" % r['T_per_servo_sym'])
        print("    Per servo (single failure): %.2f N·m each (full load)" % r['T_per_servo_fail'])
        print("    Holding requirement (gravity only): %.2f N·m" % r['T_holding'])
        
        # Check if one servo can hold against gravity
        if r['T_per_servo_sym'] >= max_g:
            print("    >>> ONE SERVO CAN HOLD against gravity (margin: %.2f N·m)" % (r['T_per_servo_sym'] - max_g))
        else:
            print("    >>> ONE SERVO CANNOT hold - mechanical stops + structure critical")
        
        print()

# Peak/stall requirement (worst-case transient: max gravity + max accel + friction)
print("="*70)
print("PEAK/STALL TORQUE REQUIREMENTS (transient worst case)")
print("="*70)
print("Peak = (max_gravity + max_acceleration + friction) / efficiency * static_factor")
print("(No safety factor on peak - this is the absolute maximum expected transient)")
print()

for model, mgx, mgy, ax1, ay1 in [
    ("Model 1", max_tx1, max_ty1, T_ACCEL_X1, T_ACCEL_Y1),
    ("Model 2", max_tx2, max_ty2, T_ACCEL_X2, T_ACCEL_Y2)
]:
    for axis_name, max_g, acc in [("X-axis", mgx, ax1), ("Y-axis", mgy, ay1)]:
        T_base_pk = max_g + acc + BEARING_FRIC
        T_peak = T_base_pk / LINKAGE_EFF * STATIC_MULT
        print("  %s %s: peak/stall requirement = %.2f N·m (base %.2f N·m)" % (
            model, axis_name, T_peak, T_base_pk))

print()
print("="*70)
print("FINAL RECOMMENDED SERVO SPECIFICATIONS")
print("="*70)
print("""
Model 1 - DUAL-RING GIMBAL:
  4 servos total (2 per axis)
  Each servo must meet:
    - CONTINUOUS torque >= [T_continuous] N·m (see per-axis values above)
    - PEAK/STALL torque >= [T_peak] N·m (see above)
    - Speed: sufficient to achieve 10°/s at output linkage
    - Position feedback (encoder or potentiometer)
    - Communication: PWM/Serial/I2C compatible with ESP32
    - Operating voltage: 5-6V typical (matches ESP32/24V system via buck)
  
  Single-servo-failure survivability:
    - Structure must carry fan independently of servo holding
    - Mechanical stops must prevent over-travel
    - Secondary retention recommended for power loss

Model 2 - SPHERICAL GIMBAL:
  4 servos total (2 per axis)
  Same torque specifications as Model 1 (very similar values)
  Compact linkage geometry: shorter servo arms = different torque requirements
  Spherical housing adds mass but doesn't contribute to tilt loads

NOTE: These are PRELIMINARY values based on mass estimates.
      Actual values depend on CAD mass properties which must be verified.
      Final servo selection must use ACTUAL calculated values from finished CAD.
""")

# Save key results
print("\n" + "="*70)
print("KEY RESULTS FOR REPORT")
print("="*70)
print("MODEL 1: Moving mass = %.2f kg, CoG = %.3f m below axis" % (M_MOVING_M1, COG_M1))
print("  Max gravity torque: X=%.2f N·m, Y=%.2f N·m" % (max_tx1, max_ty1))
print("  Required servo continuous rating: X=%.2f, Y=%.2f N·m" % (
    requirements['Model 1_X-axis']['T_continuous'],
    requirements['Model 1_Y-axis']['T_continuous']))
print("  Required servo peak rating: X=%.2f, Y=%.2f N·m" % (
    (max_tx1+T_ACCEL_X1+BEARING_FRIC)/LINKAGE_EFF*STATIC_MULT,
    (max_ty1+T_ACCEL_Y1+BEARING_FRIC)/LINKAGE_EFF*STATIC_MULT))

print("\nMODEL 2: Moving mass = %.2f kg, CoG = %.3f m below axis" % (M_MOVING_M2, COG_M2))
print("  Max gravity torque: X=%.2f N·m, Y=%.2f N·m" % (max_tx2, max_ty2))
print("  Required servo continuous rating: X=%.2f, Y=%.2f N·m" % (
    requirements['Model 2_X-axis']['T_continuous'],
    requirements['Model 2_Y-axis']['T_continuous']))
print("  Required servo peak rating: X=%.2f, Y=%.2f N·m" % (
    (max_tx2+T_ACCEL_X2+BEARING_FRIC)/LINKAGE_EFF*STATIC_MULT,
    (max_ty2+T_ACCEL_Y2+BEARING_FRIC)/LINKAGE_EFF*STATIC_MULT))
