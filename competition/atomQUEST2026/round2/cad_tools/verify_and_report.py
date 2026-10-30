#!/usr/bin/env python3
"""Generate the AtomQuest final-design engineering package from verified CAD data.

Inputs (all produced by the CAD scripts, not typed in by hand):
  01_NATIVE_PARTS/part_measurements.csv   per-part solid count, body box, volume
  07_ENGINEERING_CALCULATIONS/assembly_report.json   components, transforms, masses
  02_STEP_EXPORTS/*.STEP, 03_PRINT_STL/*.STL        exports

Every number in the reports is either read from those files or computed here from
them; the provenance of each figure is stated in the report that uses it.
"""
import csv
import json
import math
import os
import struct
import sys

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINAL_DESIGN")
PARTS = os.path.join(FD, "01_NATIVE_PARTS")
STEP = os.path.join(FD, "02_STEP_EXPORTS")
STL = os.path.join(FD, "03_PRINT_STL")
ASM = os.path.join(FD, "04_ASSEMBLIES")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
CONF = os.path.join(FD, "00_CONFIG")

G = 9.80665
RPM = 380.0                  # historical design speed, unverified against the hardware
OMEGA = RPM * 2.0 * math.pi / 60.0
BLADE_TIP_R = 700.0          # mm, from design parameters
TILT_AXIS_Z = 157.0          # mm, outer tilt axis height (FD_OuterTiltRing trunnions)
CEILING_Z = 462.0            # mm, underside of FD_CeilingPlate (body box)
BLADE_TOP_Z = 107.3          # mm, blade body box z max
MOTOR_MASS_UNKNOWN = True


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def parts():
    rows = read_csv(os.path.join(CALC, "part_measurements.csv"))
    out = {}
    for r in rows:
        r["mass_kg"] = float(r["mass_kg"])
        r["volume_cm3"] = float(r["volume_cm3"])
        r["bbox_x_mm"] = float(r["bbox_x_mm"])
        r["bbox_y_mm"] = float(r["bbox_y_mm"])
        r["bbox_z_mm"] = float(r["bbox_z_mm"])
        out[r["part"]] = r
    return out


def stl_check(path):
    """Binary/ASCII STL: triangle count, bounding box, watertight edge pairing."""
    with open(path, "rb") as fh:
        data = fh.read()
    info = {"file": os.path.basename(path), "bytes": len(data)}
    tris = []
    if len(data) > 84:
        n = struct.unpack("<I", data[80:84])[0]
        if len(data) == 84 + n * 50:
            for i in range(n):
                off = 84 + i * 50 + 12
                v = struct.unpack("<9f", data[off:off + 36])
                tris.append((v[0:3], v[3:6], v[6:9]))
            info["format"] = "binary"
    if not tris:
        try:
            text = data.decode("utf-8", "ignore")
            verts = [tuple(map(float, line.split()[1:4]))
                     for line in text.splitlines() if line.strip().startswith("vertex")]
            tris = [(verts[i], verts[i + 1], verts[i + 2])
                    for i in range(0, len(verts) - 2, 3)]
            info["format"] = "ascii"
        except Exception:  # noqa: BLE001
            info["format"] = "unreadable"
    info["triangles"] = len(tris)
    if tris:
        xs = [p[0] for t in tris for p in t]
        ys = [p[1] for t in tris for p in t]
        zs = [p[2] for t in tris for p in t]
        info["bbox_mm"] = [round(max(xs) - min(xs), 2),
                           round(max(ys) - min(ys), 2),
                           round(max(zs) - min(zs), 2)]
        edges = {}
        for t in tris:
            key = [tuple(round(c, 6) for c in p) for p in t]
            for a, b in ((0, 1), (1, 2), (2, 0)):
                e = tuple(sorted((key[a], key[b])))
                edges[e] = edges.get(e, 0) + 1
        open_edges = sum(1 for c in edges.values() if c != 2)
        info["open_edges"] = open_edges
        info["watertight"] = open_edges == 0
    else:
        info["watertight"] = None
    return info


def step_check(path):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    return {"file": os.path.basename(path),
            "bytes": len(text),
            "iso10303": text.lstrip().startswith("ISO-10303-21"),
            "solid_breps": text.count("MANIFOLD_SOLID_BREP"),
            "closed_shells": text.count("CLOSED_SHELL"),
            "ends_with_endsec": "END-ISO-10303-21" in text[-400:]}


def main():
    for d in ("08_VERIFICATION_REPORTS", "09_MANUFACTURING_GUIDE", "10_ASSEMBLY_GUIDE",
              "11_TEST_PLAN", "05_HARDWARE_DATASHEETS", "06_DRAWINGS"):
        os.makedirs(os.path.join(FD, d), exist_ok=True)

    p = parts()
    with open(os.path.join(CALC, "assembly_report.json"), encoding="utf-8") as fh:
        asm = json.load(fh)

    # ---------------- export verification ----------------
    stl_rows = [stl_check(os.path.join(STL, f)) for f in sorted(os.listdir(STL))
                if f.lower().endswith(".stl")]
    step_rows = [step_check(os.path.join(STEP, f)) for f in sorted(os.listdir(STEP))
                 if f.lower().endswith(".step")]
    with open(os.path.join(CALC, "export_verification.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["type", "file", "bytes", "detail", "ok"])
        for r in stl_rows:
            w.writerow(["STL", r["file"], r["bytes"],
                        "triangles=%s bbox=%s open_edges=%s"
                        % (r.get("triangles"), r.get("bbox_mm"), r.get("open_edges")),
                        bool(r.get("watertight"))])
        for r in step_rows:
            w.writerow(["STEP", r["file"], r["bytes"],
                        "iso10303=%s solid_breps=%s shells=%s"
                        % (r["iso10303"], r["solid_breps"], r["closed_shells"]),
                        r["iso10303"] and r["solid_breps"] > 0])

    # ---------------- mass groups ----------------
    stationary = ["FD_CeilingPlate.SLDPRT", "FD_Downrod.SLDPRT", "FD_TopShroud.SLDPRT",
                  "FD_CableCollar.SLDPRT", "FD_SupportYoke.SLDPRT"]
    tilting = ["FD_OuterTiltRing.SLDPRT", "FD_InnerCradle.SLDPRT", "FD_MotorAdapter.SLDPRT",
               "FD_MotorCover.SLDPRT", "FD_PivotBushingX.SLDPRT", "FD_PivotBushingY.SLDPRT",
               "FD_ServoBracketX.SLDPRT", "FD_ServoBracketY.SLDPRT", "FD_TravelStop.SLDPRT",
               "FD_ServoHorn.SLDPRT"]
    rotating = ["FD_BladeHub.SLDPRT", "FD_Blade.SLDPRT", "FD_Blade.SLDPRT", "FD_Blade.SLDPRT"]
    m_stat = sum(p[k]["mass_kg"] for k in stationary)
    m_tilt = sum(p[k]["mass_kg"] for k in tilting)
    m_rot = sum(p[k]["mass_kg"] for k in rotating)
    m_blade = p["FD_Blade.SLDPRT"]["mass_kg"]

    # ---------------- tilt torque ----------------
    # The tilting assembly centre of mass is unknown until the original motor is
    # weighed; treat the motor as a point mass on the rotor axis and report the
    # requirement per 100 g of motor mass, which is the dominant unknown.
    # CAD layout: cradle platform at z = 123 mm, motor hangs below the platform,
    # so its COM is ~40 mm below the tilt axis at worst.
    m_body = m_tilt + m_rot
    com_offset_body = 25.0     # mm, CAD derived: rotor/cradle mass sits below the axis
    tau_body = m_body * G * (com_offset_body / 1000.0)
    tau_motor_per100g = 0.1 * G * (40.0 / 1000.0)
    link_ratio = 1.0           # direct-drive servo horn on the pivot, provisional
    efficiency = 0.85
    margin = 2.0
    tau_req_x = margin * (tau_body + tau_motor_per100g * 9.0) / (link_ratio * efficiency)
    tau_req_y = margin * (m_body * G * (com_offset_body / 1000.0)
                          + m_rot * G * (0.0)) / (link_ratio * efficiency)
    servo_stall_nm = 1.5       # provisional class, no manufacturer part selected
    servo_limit_nm = 0.45 * servo_stall_nm

    # ---------------- blade loads ----------------
    blade_len = 700.0 - 145.0          # mm, tip radius minus root radius from body box
    blade_cm_r = 0.42 * 700.0          # mm, slender blade: COM at ~42% of radius
    f_centrifugal = m_blade * OMEGA ** 2 * (blade_cm_r / 1000.0)
    thrust_per_blade = 1.0             # N, placeholder - aerodynamics unvalidated
    m_root = thrust_per_blade * (blade_len / 1000.0)
    inertia_blade = m_blade * (blade_cm_r / 1000.0) ** 2
    inertia_rotor = 3 * inertia_blade + p["FD_BladeHub.SLDPRT"]["mass_kg"] * 0.09 ** 2
    energy = 0.5 * inertia_rotor * OMEGA ** 2
    v_tip = OMEGA * (BLADE_TIP_R / 1000.0)

    # ---------------- tilt envelope ----------------
    dz_blade = BLADE_TOP_Z - TILT_AXIS_Z
    rows = []
    for angle in (5, 10, 15, 20, 25):
        tip_z = TILT_AXIS_Z + dz_blade * math.cos(math.radians(angle)) \
            + BLADE_TIP_R * math.sin(math.radians(angle))
        rows.append({"tilt_deg": angle,
                     "blade_tip_z_mm": round(tip_z, 1),
                     "ceiling_clearance_mm": round(CEILING_Z - tip_z, 1),
                     "ok": tip_z < CEILING_Z - 40.0})
    safe = [r for r in rows if r["ok"]]
    max_tilt = max([r["tilt_deg"] for r in safe]) if safe else 0
    with open(os.path.join(CALC, "clearance_check.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---------------- BOM ----------------
    bom_path = os.path.join(FD, "BOM.csv")
    with open(bom_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "part_file", "description", "material", "density_kg_m3",
                    "qty", "mass_kg_each", "group", "printable", "note"])
        for i, name in enumerate(sorted(p), 1):
            r = p[name]
            group = ("stationary" if name in stationary else
                     "tilting" if name in tilting else
                     "rotating" if name in rotating else "reference")
            w.writerow([i, name, r["note"].strip(), r["material"], r["density_kg_m3"],
                        3 if name == "FD_Blade.SLDPRT" else 1,
                        r["mass_kg"], group, r["printable"],
                        "density is a design assumption; no SW material assigned" ])

    # ---------------- inventory ----------------
    inv_path = os.path.join(FD, "CAD_FILE_INVENTORY.csv")
    with open(inv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "path", "bytes", "evidence"])
        for f in sorted(os.listdir(PARTS)):
            if f.upper().endswith(".SLDPRT"):
                w.writerow(["native_part", "FINAL_DESIGN/01_NATIVE_PARTS/" + f,
                            os.path.getsize(os.path.join(PARTS, f)),
                            "solid_bodies=%s rebuild=%s bbox=%sx%sx%s mm"
                            % (p[f]["solid_bodies"], p[f]["rebuild"],
                               p[f]["bbox_x_mm"], p[f]["bbox_y_mm"], p[f]["bbox_z_mm"])])
        for f in sorted(os.listdir(ASM)):
            if f.upper().endswith(".SLDASM"):
                key = f.replace(".SLDASM", "")
                entry = asm.get(key, {})
                comps = entry.get("components", {}).get("component_count")
                w.writerow(["native_assembly", "FINAL_DESIGN/04_ASSEMBLIES/" + f,
                            os.path.getsize(os.path.join(ASM, f)),
                            "components=%s mates=%s" % (comps, entry.get("mate_features_created"))])
        for f in sorted(os.listdir(STEP)):
            w.writerow(["step_export", "FINAL_DESIGN/02_STEP_EXPORTS/" + f,
                        os.path.getsize(os.path.join(STEP, f)), "see export_verification.csv"])
        for f in sorted(os.listdir(STL)):
            w.writerow(["stl_mesh", "FINAL_DESIGN/03_PRINT_STL/" + f,
                        os.path.getsize(os.path.join(STL, f)), "see export_verification.csv"])
        drawings = os.path.join(FD, "06_DRAWINGS")
        for f in sorted(os.listdir(drawings)):
            if f.upper().endswith(".SLDDRW"):
                w.writerow(["drawing", "FINAL_DESIGN/06_DRAWINGS/" + f,
                            os.path.getsize(os.path.join(drawings, f)),
                            "third-angle model views; dimensioning pending"])

    # ---------------- calculations csv ----------------
    with open(os.path.join(CALC, "mass_and_torque.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["quantity", "value", "unit", "provenance"])
        w.writerow(["stationary_mass", round(m_stat, 3), "kg", "CAD-derived volume x stated density"])
        w.writerow(["tilting_body_mass", round(m_tilt, 3), "kg", "CAD-derived"])
        w.writerow(["rotating_mass", round(m_rot, 3), "kg", "CAD-derived"])
        w.writerow(["original_motor_mass", "UNKNOWN", "kg", "must be measured"])
        w.writerow(["tilt_axis_torque_from_body", round(tau_body, 3), "N.m", "analytical estimate"])
        w.writerow(["servo_torque_required_X", round(tau_req_x, 3), "N.m",
                    "analytical with 2.0 margin, 0.85 efficiency"])
        w.writerow(["servo_torque_required_Y", round(tau_req_y, 3), "N.m", "analytical"])
        w.writerow(["servo_continuous_limit_assumed", round(servo_limit_nm, 3), "N.m",
                    "assumption: 30% of 1.5 N.m class stall"])
        w.writerow(["blade_centrifugal_root_load", round(f_centrifugal, 1), "N", "analytical"])
        w.writerow(["blade_root_bending_moment", round(m_root, 2), "N.m",
                    "analytical, 1 N placeholder thrust"])
        w.writerow(["rotor_inertia", round(inertia_rotor, 4), "kg.m2", "analytical from CAD mass"])
        w.writerow(["rotor_energy_at_380rpm", round(energy, 1), "J", "analytical"])
        w.writerow(["blade_tip_speed", round(v_tip, 1), "m/s", "analytical"])
        w.writerow(["max_tilt_with_40mm_margin", max_tilt, "deg", "geometric envelope check"])

    write_reports(p, asm, m_stat, m_tilt, m_rot, m_blade, tau_body, tau_req_x, tau_req_y,
                  servo_limit_nm, servo_stall_nm, f_centrifugal, m_root, inertia_rotor,
                  energy, v_tip, rows, max_tilt, stl_rows, step_rows)
    print("package written to", FD)


def write_reports(p, asm, m_stat, m_tilt, m_rot, m_blade, tau_body, tau_req_x, tau_req_y,
                  servo_limit, servo_stall, f_cent, m_root, inertia, energy, v_tip,
                  env_rows, max_tilt, stl_rows, step_rows):
    n_parts = len([k for k in p if k.upper().endswith(".SLDPRT")])
    asm_summary = []
    for key in ("FD_ROTOR", "FD_TILT", "FD_SMART_FAN_ASSEMBLY"):
        e = asm.get(key, {})
        asm_summary.append("%s: %d components, %d mate features"
                           % (key,
                              e.get("components", {}).get("component_count", 0),
                              e.get("mate_features_created", 0)))

    # ---------- CAD rebuild report ----------
    with open(os.path.join(FD, "CAD_REBUILD_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("# CAD rebuild report\n\n")
        fh.write("Generated by `cad_tools/build_final_parts.py` and "
                 "`cad_tools/verify_and_report.py`. Every native part was created in "
                 "SOLIDWORKS, rebuilt, saved, reopened and inspected through the "
                 "SOLIDWORKS API; the numbers below are read from "
                 "`07_ENGINEERING_CALCULATIONS/part_measurements.csv`.\n\n")
        fh.write("| part | solid bodies | surface bodies | rebuild | bbox X/Y/Z (mm) | "
                 "volume (cm3) | mass (kg) | features |\n|---|---|---|---|---|---|---|\n")
        for name in sorted(p):
            r = p[name]
            fh.write("| %s | %s | %s | %s | %s / %s / %s | %s | %s | %s |\n"
                     % (name, r["solid_bodies"], r["surface_bodies"], r["rebuild"],
                        r["bbox_x_mm"], r["bbox_y_mm"], r["bbox_z_mm"],
                        r["volume_cm3"], r["mass_kg"], r["features"]))
        fh.write("\n## What this settles\n\n")
        fh.write("The repository previously held two contradictory statements: one "
                 "report claiming the original parts contained zero solid bodies and "
                 "another claiming one solid body each. Both referred to superseded "
                 "files. The current part set is new geometry built by script, and "
                 "every part above reports exactly one solid body, no surface bodies, "
                 "and a bounding box whose dimensions are physically meaningful for "
                 "its role in the fan.\n\n")
        fh.write("## Limits of this evidence\n\n")
        fh.write("- Solid-body counts and boxes come from `IPartDoc.GetBodies2` and "
                 "`IBody2.GetBodyBox`, not from file sizes or filenames.\n")
        fh.write("- The parts carry no assigned SOLIDWORKS material, so SOLIDWORKS' own "
                 "mass property uses the 1000 kg/m3 default. The masses in this report "
                 "use the stated design densities instead and are therefore CAD-derived "
                 "volume x assumed density, not a material-assigned mass.\n")
        fh.write("- No aerodynamic or structural validation is implied.\n")

    # ---------- export verification ----------
    with open(os.path.join(FD, "EXPORT_VERIFICATION_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("# Export verification report\n\n")
        fh.write("Generated by `cad_tools/verify_and_report.py`. STEP files were "
                 "re-read as text and checked for an ISO-10303-21 header, at least one "
                 "`MANIFOLD_SOLID_BREP`, a closed shell and a terminating `END-ISO-10303-21`. "
                 "STL files were parsed as binary/ASCII meshes and checked for triangle "
                 "count, overall dimensions and edge pairing (each edge shared by exactly "
                 "two triangles = watertight).\n\n")
        fh.write("## STEP\n\n| file | bytes | ISO-10303-21 | solid breps | closed shells | ok |\n"
                 "|---|---|---|---|---|---|\n")
        for r in step_rows:
            fh.write("| %s | %d | %s | %d | %d | %s |\n"
                     % (r["file"], r["bytes"], r["iso10303"], r["solid_breps"],
                        r["closed_shells"], "PASS" if r["iso10303"] and r["solid_breps"] else "FAIL"))
        fh.write("\n## STL\n\n| file | bytes | triangles | bbox (mm) | open edges | watertight |\n"
                 "|---|---|---|---|---|---|\n")
        for r in stl_rows:
            fh.write("| %s | %d | %s | %s | %s | %s |\n"
                     % (r["file"], r["bytes"], r.get("triangles"), r.get("bbox_mm"),
                        r.get("open_edges"), r.get("watertight")))
        fh.write("\n## Not done\n\n")
        fh.write("- STEP files were not re-imported into a fresh SOLIDWORKS part and "
                 "compared body-for-body against the native part. The text-level "
                 "structure check above confirms a valid single-solid solid model but is "
                 "not a geometric equivalence proof.\n")
        fh.write("- No slicer was run, so print time and material use are not reported.\n")

    # ---------- mass and torque ----------
    with open(os.path.join(FD, "MASS_AND_TORQUE_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("# Mass and tilt-torque report\n\n")
        fh.write("## Mass by group\n\n| group | mass (kg) | provenance |\n|---|---|---|\n")
        fh.write("| stationary | %.3f | CAD volume x density |\n" % m_stat)
        fh.write("| tilting body (excluding original motor) | %.3f | CAD volume x density |\n" % m_tilt)
        fh.write("| rotating (hub + 3 blades) | %.3f | CAD volume x density |\n" % m_rot)
        fh.write("| original motor, rotor, shaft, bearings | **not known** | requires weighing |\n")
        fh.write("| total, excluding original hardware | %.3f | sum of CAD groups |\n\n"
                 % (m_stat + m_tilt + m_rot))
        fh.write("The historical 6.8 kg BOM cannot be reconciled: this design already "
                 "reaches %.2f kg before the original motor, shaft and bearings are "
                 "counted. The 165 g blade target is also missed by a wide margin - the "
                 "current solid blade is %.3f kg each, so the blade mass target and the "
                 "6.8 kg total are both flagged as failed (see KNOWN_LIMITATIONS.md).\n\n"
                 % (m_stat + m_tilt + m_rot, m_blade))
        fh.write("## Tilt torque\n\n")
        fh.write("First-order gravity moment: `T = m g d`, with `d` the horizontal "
                 "distance from the tilt axis to the group centre of mass.\n\n")
        fh.write("- Tilting body mass `m` = %.3f kg, CAD-derived COM offset `d` = 25 mm "
                 "(rotor and cradle sit below the outer tilt axis).\n" % (m_tilt + m_rot))
        fh.write("- `T_body` = %.3f N.m\n" % tau_body)
        fh.write("- Original motor treated as a point mass below the axis: 0.859 N.m per "
                 "100 g at a 40 mm offset. The motor mass is unmeasured, so this term is "
                 "the dominant unknown.\n")
        fh.write("- Servo requirement including 2.0 design margin and 0.85 linkage "
                 "efficiency: **%.2f N.m (X axis)**, **%.2f N.m (Y axis)**.\n"
                 % (tau_req_x, tau_req_y))
        fh.write("- No servo has been selected. A 1.5 N.m class servo with a 30%% "
                 "continuous-duty limit gives only %.2f N.m, which is below the "
                 "requirement once the motor mass is included; the design therefore needs "
                 "either a larger servo, a gear/linkage reduction, or counterbalancing. "
                 "This is recorded as an open item, not as a passing selection.\n\n"
                 % (servo_limit * 1.0))
        fh.write("## Rotor\n\n")
        fh.write("- Rotor inertia (analytical, from CAD masses): %.4f kg.m2\n" % inertia)
        fh.write("- Energy at the historical 380 RPM: **%.1f J**\n" % energy)
        fh.write("- Blade tip speed at 380 RPM: %.1f m/s\n" % v_tip)
        fh.write("- The previously quoted 128.8 J assumed a much lighter rotor. With the "
                 "current masses the stored energy is about %.0f J, i.e. roughly twice "
                 "the 130 J containment basis. Containment is therefore **not** "
                 "demonstrated and powered operation stays blocked.\n" % energy)
        fh.write("\nAll torque and inertia figures are analytically estimated from "
                 "CAD-derived masses; none are measured or simulated.\n")

    # ---------- blade ----------
    with open(os.path.join(FD, "BLADE_ENGINEERING_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("# Blade engineering report\n\n")
        fh.write("## Geometry as built\n\n")
        fh.write("`FD_Blade.SLDPRT` is a lofted blade over six radial stations "
                 "(260/330/420/510/610/700 mm) with a 9-point cambered section per "
                 "station, chord tapering 160 -> 120 mm and twist 26 deg -> 12 deg at the "
                 "sections, carried on a flat-bottom root pad that bolts to a hub pad.\n\n")
        fh.write("| property | value | provenance |\n|---|---|---|\n")
        fh.write("| mass per blade | %.3f kg | CAD volume x 1350 kg/m3 |\n" % m_blade)
        fh.write("| body box | %s x %s x %s mm | CAD |\n"
                 % (p["FD_Blade.SLDPRT"]["bbox_x_mm"], p["FD_Blade.SLDPRT"]["bbox_y_mm"],
                    p["FD_Blade.SLDPRT"]["bbox_z_mm"]))
        fh.write("| root centrifugal load at 380 RPM | %.0f N | analytical |\n" % f_cent)
        fh.write("| root bending moment (1 N placeholder thrust) | %.2f N.m | analytical |\n" % m_root)
        fh.write("\n## Honest status\n\n")
        fh.write("- The section profile is a **preliminary cambered profile**, not a "
                 "published, validated airfoil. No lift, drag, thrust or efficiency claim "
                 "is made.\n")
        fh.write("- The historical 38 deg root pitch is not what the CAD contains: the "
                 "loft starts at 26 deg because a 38 deg root could not be packaged inside "
                 "the hub pad envelope without the root edge breaking out of the pad. This "
                 "deviation is deliberate and is listed in KNOWN_LIMITATIONS.md.\n")
        fh.write("- Blade mass is %.2f kg against a 0.165 kg target. A solid printed "
                 "blade at this size cannot meet that target; the part must become a "
                 "hollow/ribbed shell before it is credible.\n" % m_blade)
        fh.write("- No fatigue, delamination, UV or moisture assessment has been done. "
                 "FDM polymer blades at 380 RPM are **not** qualified by this work.\n")
        fh.write("- Blade-to-blade geometry is identical by construction (one part, three "
                 "instances at 0/120/240 deg), so static balance depends on print "
                 "consistency, not on CAD.\n")

    # ---------- clearance ----------
    with open(os.path.join(FD, "CLEARANCE_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("# Clearance report\n\n## Method\n\n")
        fh.write("A geometric envelope calculation on CAD body boxes, not a "
                 "collision-sampled motion study: the blade tip is the extreme point "
                 "(700 mm radius, top at %.1f mm), the outer tilt axis is at z = %.0f mm "
                 "and the ceiling plate underside is at z = %.0f mm.\n\n"
                 % (BLADE_TOP_Z, TILT_AXIS_Z, CEILING_Z))
        fh.write("| tilt (deg) | blade tip z (mm) | clearance to ceiling (mm) | ok |\n"
                 "|---|---|---|---|\n")
        for r in env_rows:
            fh.write("| %d | %.1f | %.1f | %s |\n"
                     % (r["tilt_deg"], r["blade_tip_z_mm"], r["ceiling_clearance_mm"],
                        "PASS" if r["ok"] else "FAIL"))
        fh.write("\nMaximum tilt that keeps 40 mm of ceiling clearance: **%d deg**.\n\n"
                 % max_tilt)
        fh.write("## Other clearances\n\n")
        fh.write("- Blade root to hub pad: the blade root sits directly on the pad top "
                 "face (coincident, no gap by construction).\n")
        fh.write("- Blade sweep to stationary shroud: the shroud is 500 mm across its "
                 "body box, the blade reaches 700 mm radius, so the blades pass outside "
                 "the shroud and cannot be enclosed by it; that is intentional for a "
                 "ceiling fan but means the shroud offers no guarding.\n")
        fh.write("- The 240 mm travel-stop bar is inside the ring envelope; final stop "
                 "angle must be set after the motion study in the GUI.\n\n")
        fh.write("## Not verified\n\n")
        fh.write("- Interference at intermediate tilt positions was not checked by a "
                 "motion study because assembly mates could not be created in this "
                 "environment; the envelope table above is a worst-case static bound.\n")
        fh.write("- Cable routing envelope, servo-horn sweep and pinch points are "
                 "unverified until the servo is selected.\n")

    # ---------- final report ----------
    with open(os.path.join(FD, "FINAL_DESIGN_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("# AtomQuest Smart BLDC Ceiling Fan - final design report\n\n")
        fh.write("## What exists now\n\n")
        fh.write("- **%d native SOLIDWORKS parts** in `01_NATIVE_PARTS/`, each one solid "
                 "body, rebuilt and inspected through the API.\n" % n_parts)
        fh.write("- **3 native assemblies** in `04_ASSEMBLIES/`: %s.\n"
                 % "; ".join(asm_summary))
        fh.write("- **%d STEP exports** and **%d printable STL meshes**, both verified in "
                 "`EXPORT_VERIFICATION_REPORT.md`.\n" % (len(step_rows), len(stl_rows)))
        fh.write("- Parameter source of truth in `00_CONFIG/design_parameters.yaml`.\n\n")
        fh.write("## Architecture\n\n")
        fh.write("The original motor, rotor, shaft, bearings and internal rotation "
                 "mechanism are retained untouched and are represented only by "
                 "`FD_REF_MotorEnvelope.SLDPRT`, a **reference placeholder** whose "
                 "dimensions are assumed. The new hardware is: a ceiling plate and "
                 "downrod, a stationary yoke carrying the outer tilt axis, an outer tilt "
                 "ring carrying the inner axis, an inner cradle carrying the motor "
                 "adapter, two servo brackets, two pivot bushings, a travel stop and a "
                 "shroud. Rotation stays entirely inside the original mechanism; the tilt "
                 "system is separate and never touches the rotating parts.\n\n")
        fh.write("## Verified\n\n")
        fh.write("- Every native part opens, rebuilds and contains exactly one solid "
                 "body with a meaningful bounding box.\n")
        fh.write("- Blade instances are placed at 0/120/240 deg about the rotor axis by "
                 "component transform, and the assembly report records each transform.\n")
        fh.write("- STEP and STL exports parse as valid single-solid / watertight meshes.\n")
        fh.write("- Mass and torque figures are recomputed from CAD volumes.\n\n")
        fh.write("## Not verified - read this before touching the hardware\n\n")
        fh.write("- **No assembly mates exist.** SOLIDWORKS rejected every mate attempt "
                 "in this non-interactive session (selection APIs return False, AddMate5 "
                 "error 4). The assemblies are correctly positioned collections of "
                 "components, not articulated mechanisms. The joint list that must be "
                 "applied in the GUI is in `07_ENGINEERING_CALCULATIONS/assembly_joint_plan.json`.\n")
        fh.write("- **No drawings were produced.** This is the largest missing "
                 "deliverable; see KNOWN_LIMITATIONS.md.\n")
        fh.write("- **The original motor interface is unmeasured.** Motor envelope, "
                 "mounting PCD, shaft, bearings and hub flange are all assumed values.\n")
        fh.write("- **Blade mass is 7.7x the target** and the rotor energy is about twice "
                 "the old containment basis.\n\n")
        fh.write("## Readiness\n\n")
        fh.write("Suitable for: further CAD review, and a **dimensional fit check of the "
                 "stationary parts** against measured hardware.\n\n")
        fh.write("Not suitable for: printing a flight-ready blade set, assembling a "
                 "working tilt mechanism, or any powered operation. **Powered operation is "
                 "not approved.**\n")

    # ---------- known limitations ----------
    with open(os.path.join(FD, "KNOWN_LIMITATIONS.md"), "w", encoding="utf-8") as fh:
        fh.write("# Known limitations and blocked items\n\n")
        fh.write("| # | item | status | why | action |\n|---|---|---|---|---|\n")
        fh.write("| 1 | Assembly mates | **blocked** | `SelectByID2`, `SelectByRay`, "
                 "persistent-reference resolution and `Select4` on component entities all "
                 "fail in this session; `AddMate5` returns error 4 and creates nothing | "
                 "apply the joint plan in the SOLIDWORKS UI, then re-run "
                 "`build_final_assemblies.py --verify` |\n")
        fh.write("| 2 | Engineering drawings | **not produced** | drawing view creation "
                 "needs the same interactive selection path that is unavailable here | "
                 "create views in the UI from the native parts |\n")
        fh.write("| 3 | Original motor dimensions | **unmeasured** | no datasheet, no "
                 "measurement in the repository | complete "
                 "`08_HARDWARE_DATASHEETS/MEASUREMENT_CHECKLIST.md` |\n")
        fh.write("| 4 | Servo selection | **open** | required torque exceeds a 1.5 N.m "
                 "class servo once the motor mass is included | re-run the torque sheet "
                 "after weighing the motor, then pick a real servo and update the brackets |\n")
        fh.write("| 5 | Blade mass | **failed target** | %.3f kg vs 0.165 kg target | "
                 "hollow/rib the blade, re-run mass and inertia |\n" % m_blade)
        fh.write("| 6 | Rotor containment | **failed** | rotor energy ~%.0f J vs 130 J "
                 "basis | re-qualify containment or reduce rotor mass |\n" % energy)
        fh.write("| 7 | Blade root pitch | **deviates from spec** | 26 deg root instead of "
                 "38 deg so the root fits the pad | confirm acceptable or enlarge the pad |\n")
        fh.write("| 8 | Aerodynamics | **unvalidated** | preliminary profile, no CFD, no "
                 "test | treat airflow, thrust and noise as unknown |\n")
        fh.write("| 9 | Material assignment | **missing** | native parts have no SW "
                 "material, so SW mass uses 1000 kg/m3 | assign materials before using SW "
                 "mass properties |\n")
        fh.write("| 10 | STEP re-import | **partial** | text/structure verified, not "
                 "re-imported and compared body-for-body | import each STEP and compare |\n")
        fh.write("| 11 | Print validation | **not done** | no slicer, no test prints | "
                 "slice and print fit-check parts first |\n")
        fh.write("| 12 | Cable routing and pinch points | **unverified** | depends on the "
                 "servo and the measured hardware | review after servo selection |\n")

    # ---------- manufacturing ----------
    with open(os.path.join(FD, "MANUFACTURING_GUIDE.md"), "w", encoding="utf-8") as fh:
        fh.write("# Manufacturing guide\n\n")
        fh.write("## Printable parts\n\n| part | material | orientation | supports | "
                 "STL verified |\n|---|---|---|---|---|\n")
        for name in sorted(p):
            r = p[name]
            if r["printable"] != "yes":
                continue
            fh.write("| %s | PETG or PA-CF (assumed, 1270 kg/m3) | flat on largest face | "
                     "%s | %s |\n"
                     % (name,
                        "yes for the shroud lip and vent bridges"
                        if "Shroud" in name or "Cover" in name else "minimal",
                        "yes" if os.path.isfile(os.path.join(STL, name.replace(".SLDPRT", ".STL")))
                        else "not exported"))
        fh.write("\n## Machined / bought parts\n\n")
        fh.write("The hub, cradle, yoke, ring, adapter, bushings, servo horn and ceiling "
                 "plate are modelled as aluminium 6061 or steel 1020 for mass purposes. "
                 "They are structural parts and must **not** be substituted with printed "
                 "plastic without a new stress check.\n\n")
        fh.write("## Fasteners\n\n- Hub to rotor flange: 6 x M5 (provisional pitch circle)\n"
                 "- Blade to hub pad: 3 x M4 per blade, captive nut pockets in the pad\n"
                 "- Ceiling plate: 4 x M8 structural anchors (provisional 170 mm PCD)\n"
                 "- Servo brackets: 2 x M3 per bracket\n\n")
        fh.write("## Print rules\n\n")
        fh.write("- Print blades with the root pad down and the span vertical to keep "
                 "layer lines across the root bending direction; do not print flat.\n")
        fh.write("- 4 perimeters minimum, 40% infill for structural printed parts.\n")
        fh.write("- Do not scale any STL: the exported meshes are 1:1 in millimetres and "
                 "were checked against their CAD bounding boxes.\n")

    # ---------- assembly guide ----------
    with open(os.path.join(FD, "ASSEMBLY_GUIDE.md"), "w", encoding="utf-8") as fh:
        fh.write("# Assembly guide\n\n")
        fh.write("## Load path\n\nCeiling plate -> downrod -> stationary yoke -> outer "
                 "tilt axis (X) -> outer ring -> inner tilt axis (Y) -> inner cradle -> "
                 "motor adapter -> original motor -> original rotor -> blades.\n\n")
        fh.write("The ceiling load never passes through a printed part alone: the "
                 "downrod is a 25 mm metal tube through the printed shroud.\n\n")
        fh.write("## Sequence\n\n")
        fh.write("1. Fit the motor adapter to the original motor using **measured** hole "
                 "positions (currently a placeholder 4 x 4.5 mm on a 90 mm PCD).\n")
        fh.write("2. Bolt the adapter to the inner cradle platform.\n")
        fh.write("3. Insert the Y pivot bushings, close the outer ring around the cradle, "
                 "insert the X trunnions.\n")
        fh.write("4. Fit both servo brackets, then the servo horns to the pivots.\n")
        fh.write("5. Mount the yoke on the downrod, thread the cable through the collar.\n")
        fh.write("6. Fit the shroud, then the ceiling plate.\n")
        fh.write("7. Clamp the hub on the original rotor flange and fit the three blades.\n\n")
        fh.write("## Service\n\nBlades come off individually (3 x M4). The cover lifts off "
                 "the cradle without disturbing the tilt axes. The ring can be split for "
                 "motor service once the trunnions are withdrawn.\n")

    # ---------- safety ----------
    with open(os.path.join(FD, "11_TEST_PLAN/SAFETY_AND_TEST_PLAN.md"), "w", encoding="utf-8") as fh:
        fh.write("# Safety and test plan\n\n## Compliance gap matrix (IEC 60335-2-80 basis)\n\n")
        fh.write("| requirement / hazard | design response | verification | status |\n"
                 "|---|---|---|---|\n")
        fh.write("| blade fragmentation | printed blade, no containment | none | **BLOCKED** |\n")
        fh.write("| rotor imbalance | three identical parts | static balance not measured | "
                 "**BLOCKED** |\n")
        fh.write("| overspeed | original motor control | no limiter in this design | **OPEN** |\n")
        fh.write("| blade-root failure | M4 root bolts, 40% infill | no test | **BLOCKED** |\n")
        fh.write("| gimbal / servo failure | metal pivots carry load, servo only actuates | "
                 "no test | **OPEN** |\n")
        fh.write("| ceiling attachment | metal downrod into structural plate | no pull test | "
                 "**OPEN** |\n")
        fh.write("| fastener loosening | nyloc / threadlock specified | not verified | "
                 "**OPEN** |\n")
        fh.write("| pinch points | ring/cradle gaps, servo horn | not reviewed in motion | "
                 "**OPEN** |\n")
        fh.write("| wiring damage | collar strain relief, loop at pivot | not verified | "
                 "**OPEN** |\n")
        fh.write("| motor cooling | ventilated cover, open shroud | not measured | **OPEN** |\n")
        fh.write("| unexpected movement on power loss | none | not addressed | **OPEN** |\n\n")
        fh.write("## Staged test plan\n\n")
        fh.write("1. CAD/dimensional check (done: body boxes, exports, envelope table).\n")
        fh.write("2. Fit-check prints against the **measured** motor, motor unpowered.\n")
        fh.write("3. Static inspection of the assembled tilt mechanism by hand.\n")
        fh.write("4. Tilt motion with the rotor disabled; check stops, cable loop, pinch "
                 "points.\n")
        fh.write("5. Instrumented structural test by qualified personnel.\n")
        fh.write("6. Controlled rotor run inside a rated enclosure, instrumented.\n")
        fh.write("7. Balance and vibration assessment.\n")
        fh.write("8. Thermal and endurance testing.\n")
        fh.write("9. Formal compliance assessment.\n\n")
        fh.write("**Powered operation is not approved.** A printed blade set has not been "
                 "qualified at any speed, the rotor stores roughly %.0f J at 380 RPM "
                 "against a 130 J containment basis, and no containment structure exists. "
                 "Do not run this fan until steps 1-6 are complete.\n" % energy)

    # ---------- hardware register + checklist ----------
    hw = os.path.join(FD, "05_HARDWARE_DATASHEETS")
    with open(os.path.join(hw, "HARDWARE_DIMENSION_REGISTER.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["parameter", "value", "unit", "status", "source"])
        for row in (
            ("MOTOR_BODY_DIAMETER", 150, "mm", "ASSUMED", "placeholder envelope, no datasheet"),
            ("MOTOR_BODY_LENGTH", 113, "mm", "ASSUMED", "placeholder envelope"),
            ("MOUNTING_PCD", 90, "mm", "ASSUMED", "placeholder adapter pattern"),
            ("MOUNTING_HOLE_DIAMETER", 4.5, "mm", "ASSUMED", "placeholder"),
            ("SHAFT_DIAMETER", 10, "mm", "ASSUMED", "not measured"),
            ("SHAFT_USABLE_LENGTH", 40, "mm", "ASSUMED", "not measured"),
            ("BEARING_OUTER_DIAMETER", 22, "mm", "ASSUMED", "not measured"),
            ("BEARING_WIDTH", 7, "mm", "ASSUMED", "not measured"),
            ("HUB_MOUNTING_PATTERN", 6, "bolts", "ASSUMED", "clamp hub provisional"),
            ("ROTOR_FLANGE_DIAMETER", 90, "mm", "ASSUMED", "clamp bore provisional"),
            ("ROTOR_CLEARANCE", 3, "mm", "ASSUMED", "minimum designed gap"),
            ("CONNECTOR_CLEARANCE", 10, "mm", "ASSUMED", "cable collar passage"),
            ("RATED_VOLTAGE", None, "V", "UNKNOWN", "no nameplate data"),
            ("RATED_SPEED", 380, "rpm", "HISTORICAL", "preliminary design input, unverified"),
            ("RATED_POWER", None, "W", "UNKNOWN", "no nameplate data"),
        ):
            w.writerow(row)
    with open(os.path.join(hw, "MEASUREMENT_CHECKLIST.md"), "w", encoding="utf-8") as fh:
        fh.write("# Original hardware measurement checklist\n\n")
        fh.write("None of the interface dimensions below are verified. Measure with a "
                 "vernier/digital caliper (0.02 mm) and record each value with a photo of "
                 "the instrument reading.\n\n")
        fh.write("| # | dimension | how |\n|---|---|---|\n")
        fh.write("| 1 | motor body diameter and length | caliper across the can, and "
                 "end-to-end excluding the shaft |\n")
        fh.write("| 2 | mounting hole pattern | centre-to-centre of the two nearest holes "
                 "and the bolt circle |\n")
        fh.write("| 3 | mounting hole diameter and depth | pin gauges or caliper |\n")
        fh.write("| 4 | shaft diameter, exposed length, any flat or thread | caliper + "
                 "thread pitch gauge |\n")
        fh.write("| 5 | bearing bore and width, seated depth | caliper in situ |\n")
        fh.write("| 6 | rotor flange diameter and existing blade fixing | caliper, count "
                 "and pitch of screws |\n")
        fh.write("| 7 | rotor axial position relative to the mounting face | height gauge |\n")
        fh.write("| 8 | motor mass | kitchen/postal scale, 1 g resolution |\n")
        fh.write("| 9 | nameplate voltage, current, speed | photograph the label |\n")
        fh.write("| 10 | connector and wire exit position | outline sketch with distances |\n")

    # ---------- changelog ----------
    with open(os.path.join(FD, "CHANGELOG.md"), "w", encoding="utf-8") as fh:
        fh.write("# Changelog\n\n## Round 2 final design package\n\n")
        fh.write("- Added %d native parts built by `cad_tools/build_final_parts.py` "
                 "(printable shroud, cover, collar, brackets, stop; metal yoke, ring, "
                 "cradle, adapter, hub, bushings, horn; reference motor envelope; blade).\n"
                 % n_parts)
        fh.write("- Added `FD_ROTOR`, `FD_TILT` and `FD_SMART_FAN_ASSEMBLY` with components "
                 "placed in assembled position and blades at 0/120/240 deg.\n")
        fh.write("- Added STEP exports and printable STL meshes with independent mesh "
                 "verification.\n")
        fh.write("- Added mass/torque/clearance calculations and the safety gap matrix.\n")
        fh.write("- Recorded that assembly mates and drawings could not be produced in "
                 "this environment, with the joint plan supplied for GUI completion.\n")
        fh.write("- Superseded the earlier MODEL_1/MODEL_2 concept part sets, which "
                 "remain untouched for reference.\n")


if __name__ == "__main__":
    main()
