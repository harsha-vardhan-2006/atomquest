#!/usr/bin/env python3
"""Final-design calculations for the AtomQuest printable fan body (round 2).

Reads the CAD-derived part measurements and the assembly report, then derives the
mass roll-up, centre of gravity, rotor inertia, tilt-axis gravity torque, servo
sizing, blade centrifugal and root loads, fastener and ceiling-anchor loads, and
the stored rotor energy.

Evidence classes (kept separate, never mixed):
  M  measured              - taken from a physical object (none available yet)
  S  manufacturer-specified - datasheet value (none available yet)
  C  CAD-derived           - geometric property read out of the native part file
  A  analytically estimated - formula applied to CAD-derived or assumed inputs
  U  unverified assumption - input that has no source yet

Every printed number carries one of these tags so a reader can see which claims
are geometry and which are still assumptions.

Outputs (written next to the other calculation artefacts):
  mass_and_torque.csv          per-part and per-group mass, CG radius, inertia
  servo_sizing.csv             required torque per tilt axis vs assumed servo
  blade_root_loads.csv         centrifugal / bending / bolt loads per blade
  ceiling_anchor_loads.csv     load path to the ceiling anchors

Run:  py -3.13 calculations/final_design_calculations.py
Exit code 0 means every calculation ran; it does NOT mean the design is safe.
"""
import csv
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(ROOT, "competition", "atomQUEST2026", "round2", "FINAL_DESIGN")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")

# ---------------------------------------------------------------------------
# Frozen design inputs (docs/00-design-freeze.md, Rev 2)
# ---------------------------------------------------------------------------
R_TIP_M = 0.700
R_ROOT_M = 0.200          # blade root station in the current CAD (was 150 historical)
N_TOP_RPM = 380.0
N_IDLE_RPM = 80.0
TIP_SPEED_CAP = 30.0      # m/s, IS 374:2019 + Amd.1
N_BLADES = 3
G = 9.80665

# Rotor axis sits at (300, 300) mm in part space (documented modelling offset).
AXIS_X_MM, AXIS_Y_MM = 300.0, 300.0

# Assumed servo: the design still has no selected servo model (KNOWN_LIMITATIONS).
SERVO_STALL_NM = 2.0      # U - typical class, NOT a selected part
SERVO_DUTY_FRACTION = 0.4  # U - continuous share of stall torque
TILT_MAX_DEG = 20.0       # S/A - firmware limit, hard stop 27 deg
TILT_RATE_DEG_S = 10.0    # frozen target T10

# Densities come from the part builder (build_final_parts.py DENSITY) so the
# mass here is the same mass the CAD reports.
GROUPS = {
    "rotating": ["FD_BladeHub", "FD_Blade"],
    "tilting": ["FD_SupportYoke", "FD_OuterTiltRing", "FD_InnerCradle",
                "FD_MotorAdapter", "FD_MotorCover", "FD_PivotBushingX",
                "FD_PivotBushingY", "FD_ServoBracketX", "FD_ServoBracketY",
                "FD_TravelStop", "FD_ServoHorn", "FD_REF_MotorEnvelope"],
    "stationary": ["FD_CeilingPlate", "FD_Downrod", "FD_TopShroud", "FD_CableCollar"],
}


def read_parts():
    """CAD-derived per-part records from the part build audit."""
    path = os.path.join(CALC, "part_measurements.csv")
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("part"):
                continue
            # the audit appends one row per run; keep the last record per part
            rows = [r for r in rows if r["part"] != row["part"]]
            rows.append(row)
    out = {}
    for r in rows:
        stem = r["part"].replace(".SLDPRT", "")
        out[stem] = {
            "part": r["part"],
            "material": r["material"],
            "density": float(r["density_kg_m3"]),
            "volume_cm3": float(r["volume_cm3"]),
            "mass_kg": float(r["mass_kg"]),
            "com_x_mm": float(r["com_x_mm"]),
            "com_y_mm": float(r["com_y_mm"]),
            "com_z_mm": float(r["com_z_mm"]),
            "bbox": (float(r["bbox_x_mm"]), float(r["bbox_y_mm"]), float(r["bbox_z_mm"])),
            "printable": r["printable"],
        }
    return out


def show(title, formula, inputs, value, unit, status):
    print("\n%s" % title)
    print("  formula : %s" % formula)
    for k, v in inputs.items():
        print("  input   : %s = %s" % (k, v))
    print("  output  : %s %s  [%s]" % (value, unit, status))


def radius_mm(part):
    return math.hypot(part["com_x_mm"] - AXIS_X_MM, part["com_y_mm"] - AXIS_Y_MM)


def inertia_about_axis(part):
    """Point-mass inertia at the CG radius plus a box radius of gyration.

    Not a solid-model tensor: the native files do carry one, but the CSV audit
    does not export it, so this is the closed-form estimate of a part treated as
    a uniform box of the measured bounding box.
    """
    m = part["mass_kg"]
    r = radius_mm(part) / 1000.0
    bx, by, bz = (v / 1000.0 for v in part["bbox"])
    k2 = (bx ** 2 + by ** 2) / 12.0     # about a vertical axis through the box centre
    return m * (r ** 2 + k2)


def main():
    parts = read_parts()
    with open(os.path.join(CALC, "assembly_report.json"), encoding="utf-8") as fh:
        asm = json.load(fh)

    # ------------------------------------------------------------------
    # 1. Mass roll-up
    # ------------------------------------------------------------------
    groups = {k: [] for k in GROUPS}
    unassigned = [p for p in parts if p not in sum(GROUPS.values(), [])]
    for name, members in GROUPS.items():
        for member in members:
            if member in parts:
                groups[name].append(parts[member])

    mass = {k: sum(p["mass_kg"] for p in v) for k, v in groups.items()}
    total_mass = sum(mass.values()) + sum(parts[p]["mass_kg"] for p in unassigned)

    print("=" * 78)
    print("ATOMQUEST FINAL DESIGN CORE CALCULATIONS")
    print("CAD source: %s" % os.path.join(CALC, "part_measurements.csv"))
    print("=" * 78)

    show("1. Mass roll-up from CAD solids",
         "m_group = sum(m_part) ; m_part = rho_part * V_part",
         {"rotating (hub + 3 blades)": "%.3f kg" % mass["rotating"],
          "tilting (yoke, rings, cradle, servos, motor)": "%.3f kg" % mass["tilting"],
          "stationary (plate, downrod, shroud, collar)": "%.3f kg" % mass["stationary"]},
         round(total_mass, 3), "kg", "C (CAD-derived)")

    show("1b. Moving mass vs the frozen 6.80 kg budget",
         "margin = m_moving - m_budget",
         {"m_moving (rotating + tilting)": "%.3f kg" % (mass["rotating"] + mass["tilting"]),
          "budget (T16)": "6.80 kg"},
         round(mass["rotating"] + mass["tilting"], 3), "kg", "A")
    over_budget = mass["rotating"] + mass["tilting"] - 6.80
    print("  note    : %s by %.3f kg -> mass budget NOT met by the current CAD"
          % ("OVER" if over_budget > 0 else "UNDER", abs(over_budget)))

    # ------------------------------------------------------------------
    # 2. Rotor inertia, tip speed and stored energy
    # ------------------------------------------------------------------
    omega_top = N_TOP_RPM * 2.0 * math.pi / 60.0
    v_tip = omega_top * R_TIP_M
    show("2. Blade-tip speed at top speed",
         "v_tip = omega * R ; omega = 2*pi*N/60",
         {"N": "%g rpm" % N_TOP_RPM, "R": "%.3f m" % R_TIP_M},
         round(v_tip, 2), "m/s", "A (calculated)")
    print("  check   : cap %.1f m/s -> margin %.1f %%"
          % (TIP_SPEED_CAP, 100.0 * (TIP_SPEED_CAP - v_tip) / TIP_SPEED_CAP))

    inertia_rows = []
    rotor_inertia = 0.0
    for name in GROUPS:
        for part in groups[name]:
            i = inertia_about_axis(part)
            inertia_rows.append({
                "part": part["part"], "group": name, "material": part["material"],
                "volume_cm3": round(part["volume_cm3"], 2),
                "mass_kg": round(part["mass_kg"], 4),
                "cg_radius_mm": round(radius_mm(part), 1),
                "inertia_about_rotor_axis_kgm2": round(i, 6),
                "evidence": "C/A",
            })
            if name == "rotating":
                rotor_inertia += i

    energy = 0.5 * rotor_inertia * omega_top ** 2
    show("3. Rotor inertia and stored energy",
         "E = 0.5 * I * omega^2",
         {"I_rotor (hub + blades, CAD masses)": "%.5f kg.m^2" % rotor_inertia,
          "omega at %g rpm" % N_TOP_RPM: "%.2f rad/s" % omega_top},
         round(energy, 1), "J", "A")
    print("  comparison: repo containment basis 130 J (rating basis itself UNCONFIRMED)")
    print("  verdict : %s" % ("energy exceeds the 130 J basis -> containment BLOCKED"
                              if energy > 130.0 else
                              "below 130 J, but a basis without a test is not containment"))
    print("  note    : the ORIGINAL rotor/shaft/magnets are NOT in this roll-up (their")
    print("            masses are unmeasured), so this energy is a lower bound [U].")

    # ------------------------------------------------------------------
    # 4. Tilt-axis gravity torque and servo sizing
    # ------------------------------------------------------------------
    tilt_mass = mass["tilting"]
    cg_sum_x = sum(p["mass_kg"] * p["com_x_mm"] for p in groups["tilting"])
    cg_sum_y = sum(p["mass_kg"] * p["com_y_mm"] for p in groups["tilting"])
    cg_sum_z = sum(p["mass_kg"] * p["com_z_mm"] for p in groups["tilting"])
    cg = (cg_sum_x / tilt_mass, cg_sum_y / tilt_mass, cg_sum_z / tilt_mass)
    cg_offset_x = cg[0] - AXIS_X_MM
    cg_offset_y = cg[1] - AXIS_Y_MM
    cg_offset_z = cg[2] - 0.0

    t_max = math.radians(TILT_MAX_DEG)
    # Pivot lines, taken from the CAD (FD_SupportYoke X bore, FD_OuterTiltRing Y
    # bore): both sit at z = 157 mm, x = 0 and y = 0 respectively.
    pivot_z = 157.0
    y0 = cg[1] - AXIS_Y_MM          # CG offset perpendicular to the X axis, level
    x0 = cg[0] - AXIS_X_MM          # CG offset perpendicular to the Y axis, level
    z0 = cg[2] - pivot_z            # CG height below the pivot line
    # Rotating the body by theta swings that offset into the gravity arm.
    d_perp_x = abs(y0 * math.cos(t_max) + z0 * math.sin(t_max))
    d_perp_y = abs(x0 * math.cos(t_max) + z0 * math.sin(t_max))
    t_grav_x = tilt_mass * G * (d_perp_x / 1000.0)
    t_grav_y = tilt_mass * G * (d_perp_y / 1000.0)

    # Axis inertia for the dynamic term: tilting mass at its CG radius.
    i_tilt = sum(inertia_about_axis(p) for p in groups["tilting"])
    alpha = math.radians(TILT_RATE_DEG_S) / 0.2      # reach rate in 0.2 s (assumed ramp)
    t_dyn = i_tilt * alpha
    t_friction = 0.02 * (t_grav_x + t_grav_y)        # 2 % bearing/friction allowance [U]
    margin = 1.5

    servo_rows = []
    for axis, t_grav in (("X (outer ring)", t_grav_x), ("Y (inner cradle)", t_grav_y)):
        t_req = (t_grav + t_dyn + t_friction) * margin
        servo_rows.append({
            "axis": axis,
            "moving_mass_kg": round(tilt_mass, 3),
            "cg_offset_mm": round(d_perp_x if axis.startswith("X") else d_perp_y, 1),
            "gravity_torque_Nm": round(t_grav, 3),
            "dynamic_torque_Nm": round(t_dyn, 3),
            "friction_torque_Nm": round(t_friction, 3),
            "required_with_1p5_margin_Nm": round(t_req, 3),
            "assumed_servo_stall_Nm": SERVO_STALL_NM,
            "assumed_servo_duty_Nm": SERVO_STALL_NM * SERVO_DUTY_FRACTION,
            "verdict": "OK on assumed servo" if t_req <= SERVO_STALL_NM * SERVO_DUTY_FRACTION
                       else "NO SERVO SELECTED can be confirmed",
            "evidence": "A/U",
        })

    show("4. Tilt-axis gravity torque at the %g deg limit" % TILT_MAX_DEG,
         "T_gravity = m * g * d_perpendicular",
         {"m_tilting": "%.3f kg" % tilt_mass,
          "CG (x, y, z)": "(%.1f, %.1f, %.1f) mm from the part-space origin" % cg,
          "arm about X": "%.1f mm" % d_perp_x,
          "arm about Y": "%.1f mm" % d_perp_y},
         "%.2f / %.2f" % (t_grav_x, t_grav_y), "N.m (X / Y)", "A")

    show("5. Servo torque requirement (both axes)",
         "T_req = (T_grav + T_dyn + T_fric) * 1.5",
         {"T_dyn = I_tilt * alpha": "%.3f N.m (I=%.4f kg.m^2, alpha=%.2f rad/s^2)"
                                     % (t_dyn, i_tilt, alpha),
          "T_friction (2 %)": "%.3f N.m" % t_friction,
          "requirement X / Y": "%.2f / %.2f N.m" % (servo_rows[0]["required_with_1p5_margin_Nm"],
                                                    servo_rows[1]["required_with_1p5_margin_Nm"])},
         "%g" % SERVO_STALL_NM, "N.m assumed stall", "U")
    print("  note    : no servo model is selected, so this is a SIZING TARGET, not a")
    print("            selection. The mass overshoot above makes both axes harder.")

    # ------------------------------------------------------------------
    # 6. Blade loads
    # ------------------------------------------------------------------
    blade = parts.get("FD_Blade")
    blade_rows = []
    if blade:
        r_cg = radius_mm(blade) / 1000.0
        m_blade = blade["mass_kg"]
        f_cent = m_blade * omega_top ** 2 * r_cg
        # Thrust per blade from the frozen actuator-disk momentum reaction 2.17 N.
        thrust_per_blade = 2.17
        span = R_TIP_M - R_ROOT_M
        m_bend = thrust_per_blade * span / 3.0        # uniform load, root moment
        bolt_circle_r = 0.045
        n_bolts = 2
        f_bolt_cent = f_cent / n_bolts
        sigma = f_cent / (math.pi * (0.003 ** 2))     # M6 shank area, gross section
        blade_rows.append({
            "blade_mass_kg": round(m_blade, 4),
            "cg_radius_mm": round(r_cg * 1000.0, 1),
            "centrifugal_force_N": round(f_cent, 1),
            "root_bending_moment_Nm": round(m_bend, 2),
            "bolts_per_root": n_bolts,
            "force_per_bolt_N": round(f_bolt_cent, 1),
            "bolt_tension_MPa_gross": round(sigma / 1e6, 1),
            "thrust_per_blade_N": thrust_per_blade,
            "evidence": "A",
        })
        show("6. Blade centrifugal and root loads",
             "F_c = m * omega^2 * r_cg ; M_root = q * span^2 / 2 (uniform thrust)",
             {"blade mass": "%.3f kg" % m_blade,
              "blade CG radius": "%.0f mm" % (r_cg * 1000.0),
              "thrust per blade (frozen)": "%s N" % thrust_per_blade},
             "%.0f N centrifugal / %.2f N.m bending" % (f_cent, m_bend),
             "", "A")
        print("  note    : printed-blade strength is NOT established by this number;")
        print("            static stress is not a fatigue or delamination test [U].")

    # ------------------------------------------------------------------
    # 7. Ceiling anchor and downrod loads
    # ------------------------------------------------------------------
    anchor_rows = []
    load = total_mass * G
    show("7. Ceiling support load (static, level)",
         "F = m_total * g",
         {"m_total": "%.3f kg" % total_mass},
         round(load, 1), "N", "A")
    for case, factor in (("static", 1.0), ("x3 dynamic allowance", 3.0),
                         ("x8 abuse / yank", 8.0)):
        anchor_rows.append({"case": case, "load_N": round(load * factor, 1),
                            "per_anchor_N_4_anchors": round(load * factor / 4.0, 1),
                            "evidence": "A"})
    print("  note    : anchor ratings of 600 N working / 1500 N ultimate are hardware")
    print("            CLASS values, still to be confirmed by the supplier [S/U].")
    print("  note    : the load path must run metal-fastener-to-metal-anchor; a printed")
    print("            joint alone is not an acceptable ceiling support [design rule].")

    # ------------------------------------------------------------------
    # 8. Write the CSV artefacts
    # ------------------------------------------------------------------
    def write_csv(name, rows):
        if not rows:
            return None
        path = os.path.join(CALC, name)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return path

    mass_rows = []
    for name in GROUPS:
        for part in groups[name]:
            mass_rows.append({
                "group": name, "part": part["part"], "material": part["material"],
                "density_kg_m3": part["density"],
                "volume_cm3": round(part["volume_cm3"], 2),
                "mass_kg": round(part["mass_kg"], 4),
                "cg_radius_mm": round(radius_mm(part), 1),
                "inertia_about_rotor_axis_kgm2": round(inertia_about_axis(part), 6),
                "evidence": "C/A",
            })
    for name in unassigned:
        part = parts[name]
        mass_rows.append({
            "group": "unassigned", "part": part["part"], "material": part["material"],
            "density_kg_m3": part["density"], "volume_cm3": round(part["volume_cm3"], 2),
            "mass_kg": round(part["mass_kg"], 4),
            "cg_radius_mm": round(radius_mm(part), 1),
            "inertia_about_rotor_axis_kgm2": round(inertia_about_axis(part), 6),
            "evidence": "C/A",
        })
    write_csv("mass_and_torque.csv", mass_rows)
    write_csv("servo_sizing.csv", servo_rows)
    write_csv("blade_root_loads.csv", blade_rows)
    write_csv("ceiling_anchor_loads.csv", anchor_rows)

    summary = {
        "source_of_geometry": os.path.relpath(os.path.join(CALC, "part_measurements.csv"), ROOT),
        "mass_kg": {k: round(v, 3) for k, v in mass.items()},
        "mass_total_kg": round(total_mass, 3),
        "mass_moving_kg": round(mass["rotating"] + mass["tilting"], 3),
        "moving_mass_budget_kg": 6.80,
        "moving_mass_over_budget_kg": round(over_budget, 3),
        "rotor_inertia_kgm2": round(rotor_inertia, 5),
        "rotor_energy_J": round(energy, 1),
        "containment_basis_J": 130.0,
        "tip_speed_m_s": round(v_tip, 2),
        "tilt_gravity_torque_Nm": {"X": round(t_grav_x, 3), "Y": round(t_grav_y, 3)},
        "servo_required_Nm": {r["axis"]: r["required_with_1p5_margin_Nm"] for r in servo_rows},
        "blade_loads": blade_rows,
        "ceiling_load_static_N": round(load, 1),
        "evidence_legend": {"M": "measured", "S": "manufacturer-specified",
                            "C": "CAD-derived", "A": "analytically estimated",
                            "U": "unverified assumption"},
        "limitations": [
            "Original motor, rotor, shaft, magnets and bearings are not modelled in "
            "mass or inertia; all totals are lower bounds.",
            "No servo model is selected, so servo figures are sizing targets.",
            "Blade strength, containment and fatigue are NOT established.",
        ],
    }
    with open(os.path.join(CALC, "calculations_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print("\n" + "=" * 78)
    print("Mass total        : %.3f kg (CAD-derived)" % total_mass)
    print("Moving mass       : %.3f kg vs 6.80 kg budget -> %+.3f kg"
          % (mass["rotating"] + mass["tilting"], over_budget))
    print("Rotor inertia     : %.5f kg.m^2 -> %.1f J at %g rpm"
          % (rotor_inertia, energy, N_TOP_RPM))
    print("Tip speed         : %.2f m/s (cap %.1f)" % (v_tip, TIP_SPEED_CAP))
    print("Tilt torque X/Y   : %.2f / %.2f N.m"
          % (t_grav_x, t_grav_y))
    print("Written           : mass_and_torque.csv, servo_sizing.csv,")
    print("                    blade_root_loads.csv, ceiling_anchor_loads.csv,")
    print("                    calculations_summary.json")
    print("=" * 78)


if __name__ == "__main__":
    main()
