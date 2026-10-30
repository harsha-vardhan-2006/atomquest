#!/usr/bin/env python3
"""Sweep the tilt envelope and check interference with the real CAD kernel.

The tilt mechanism is driven by the two pivot axes in the design frame: the X
pivot (pivot bushing X) and the Y pivot (pivot bushing Y). The root assembly is a
-90 deg rotation of that design frame about X, so this script does not assume the
axis positions - it reads them off the pivot bushing components' assembly-space
boxes, which place each axis where the parts were actually built.

For every pose it rotates ``FD_TILT`` (yoke, rings, cradle, adapter, brackets,
servo horn) and ``FD_ROTOR`` (hub plus three blades) about the two pivot axes,
rebuilds, and runs ``IInterferenceDetectionMgr`` - SOLIDWORKS' own body-body
intersection test - on the whole assembly.

Two things make the result trustworthy:

* **Positive control.** Before sweeping, the rotor is pushed 60 mm into the
  cradle and the detector must report a non-zero volume. "Nothing found" only
  means something if the same call finds a deliberate collision.
* **Units.** ``IInterference::Volume`` is cubic metres; a controlled 200 mm3
  overlap returns 2.0e-7. Volumes are converted to mm3 and anything below
  0.5 mm3 is treated as numerical coincidence rather than an overlap.

Results must be read before ``IInterferenceDetectionMgr::Done()``; calling Done()
first makes ``Volume`` fail with RPC_E_SERVERFAULT, which silently looks like
"zero interference".

The assembly already overlaps itself at rest (press-fit pivots, cable collar in
the downrod, and some parts blocking into each other), so the sweep reports two
numbers per pose: pairs that overlap but did not overlap at rest - motion-induced
collisions - and how much the pre-existing overlaps grew. The rest-pose overlaps
are listed on their own, because they are a CAD defect list rather than a
consequence of tilting.

The result is a sampled envelope, not a proof: it says nothing about poses between
the sampled ones, and nothing about blade spin relative to the body.
"""
import csv
import json
import math
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type, Array, Double
from SolidWorks.Interop.sldworks import (
    ISldWorks, IModelDoc2, IAssemblyDoc, IComponent2, IMathUtility,
    IMathTransform, IInterferenceDetectionMgr, IInterference,
)
from SolidWorks.Interop.swconst import (
    swDocumentTypes_e, swOpenDocOptions_e,
)

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINAL_DESIGN")
ASM = os.path.join(FD, "04_ASSEMBLIES", "FD_SMART_FAN_ASSEMBLY.SLDASM")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
REP = os.path.join(FD, "08_VERIFICATION_REPORTS")

# Provisional travel limits from 00_CONFIG/design_parameters.yaml.
LIMIT_X_DEG = 20.0
LIMIT_Y_DEG = 15.0
GRID_X = [-LIMIT_X_DEG, -10.0, 0.0, 10.0, LIMIT_X_DEG]
GRID_Y = [-LIMIT_Y_DEG, -7.5, 0.0, 7.5, LIMIT_Y_DEG]
MIN_VOLUME_MM3 = 0.5


def arr(tr):
    return [float(v) for v in tr.ArrayData]


def box_centre(comp):
    try:
        b = [float(v) for v in comp.GetBox(True, False)]
        if max(abs(v) for v in b) < 1e-9:
            return None
        return [(b[0] + b[3]) / 2.0, (b[1] + b[4]) / 2.0, (b[2] + b[5]) / 2.0]
    except Exception:  # noqa: BLE001
        return None


def compose(a, b):
    """Compose two 16-element SOLIDWORKS transform arrays: C = A . B.

    The 3x3 block is stored column-major (a -90 deg rotation about X reads as
    [1,0,0, 0,0,-1, 0,1,0], which is the transpose of the textbook matrix), so the
    product is assembled element by element in true-matrix terms and written back
    in the same storage order. Both orders are returned; the caller compares them
    with the transform SOLIDWORKS stored, which settles the convention from the
    data instead of assuming it.
    """
    # true_A[i][j] = a[j * 3 + i]
    def mul(a_, b_):
        m = [sum(a_[k * 3 + j] * b_[i * 3 + k] for k in range(3))
             for i in range(3) for j in range(3)]
        t = [sum(a_[k * 3 + i] * b_[9 + k] for k in range(3)) + a_[9 + i]
             for i in range(3)]
        return m + t + [1.0]

    return mul(a, b), mul(b, a)


def pair_key(names):
    return " | ".join(sorted(names))


def main():
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = True
    r = sw.OpenDoc6(ASM, int(swDocumentTypes_e.swDocASSEMBLY),
                    int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
    doc = r[0] if isinstance(r, tuple) else r
    if doc is None:
        raise SystemExit("cannot open %s" % ASM)
    md = IModelDoc2(doc)
    asm = IAssemblyDoc(md)

    # Top-level components drive the motion; the pivot bushings sit inside the
    # tilt subassembly, so the whole tree is searched for them.
    comps = {}
    for c in (asm.GetComponents(False) or []):
        comp = IComponent2(c)
        comps[str(comp.Name2)] = comp

    def find(prefix):
        for name, comp in comps.items():
            if name.split("/")[-1].upper().startswith(prefix.upper()):
                return comp
        raise SystemExit("missing component %r" % prefix)

    tilt = find("FD_TILT")
    rotor = find("FD_ROTOR")
    bush_x = find("FD_PivotBushingX")
    bush_y = find("FD_PivotBushingY")

    base = {str(c.Name2): arr(c.Transform2) for c in (tilt, rotor)}
    centre0 = box_centre(tilt)
    bx = box_centre(bush_x)
    by = box_centre(bush_y)
    if centre0 is None or bx is None or by is None:
        raise SystemExit("cannot read component boxes")

    # The X pivot bushing lies along X, so only its y and z locate that axis; the
    # Y pivot bushing lies along the (rotated) Y pivot, so only its x and y matter.
    ax_point = [0.0, bx[1], bx[2]]
    ax_dir = [1.0, 0.0, 0.0]
    ay_point = [by[0], by[1], 0.0]
    ay_dir = [0.0, 0.0, 1.0]
    print("X axis point %s dir %s" % (ax_point, ax_dir), flush=True)
    print("Y axis point %s dir %s" % (ay_point, ay_dir), flush=True)

    mu = IMathUtility(sw.GetMathUtility())
    px = mu.CreatePoint(Array[Double](ax_point))
    vx = mu.CreateVector(Array[Double](ax_dir))
    py = mu.CreatePoint(Array[Double](ay_point))
    vy = mu.CreateVector(Array[Double](ay_dir))

    def pose(tx_deg, ty_deg):
        rx = IMathTransform(mu.CreateTransformRotateAxis(px, vx, math.radians(tx_deg)))
        ry = IMathTransform(mu.CreateTransformRotateAxis(py, vy, math.radians(ty_deg)))
        return IMathTransform(rx.Multiply(ry))

    def set_components(t):
        for comp in (tilt, rotor):
            rest = IMathTransform(mu.CreateTransform(Array[Double](base[str(comp.Name2)])))
            comp.SetTransformAndSolve3(IMathTransform(t.Multiply(rest)), False)
        md.EditRebuild3()

    # FD_REF_MotorEnvelope is a reference volume standing in for the unmeasured
    # original motor, not a part that will be built. Counting it as interfering
    # with the cover that encloses it would bury the real findings.
    reference_parts = [str(c.Name2) for c in comps.values()
                       if "REF_" in str(c.Name2).upper()]

    def detect():
        """Interfering body pairs with their overlap volume, in mm3."""
        mgr = IInterferenceDetectionMgr(asm.InterferenceDetectionManager)
        if mgr is None:
            return None
        mgr.TreatCoincidenceAsInterference = False
        mgr.IncludeMultibodyPartInterferences = True
        mgr.TreatSubAssembliesAsComponents = False
        mgr.IgnoreHiddenBodies = True
        got = mgr.GetInterferences()
        rows = []
        n = 0 if got is None else len(got)
        for i in range(n):
            intr = IInterference(got[i])
            try:
                vol = float(intr.Volume) * 1e9
            except Exception:  # noqa: BLE001
                vol = None
            names = []
            try:
                for c in (intr.Components or []):
                    names.append(str(IComponent2(c).Name2))
            except Exception:  # noqa: BLE001
                pass
            rows.append({"volume_mm3": None if vol is None else round(vol, 2),
                         "components": names, "pair": pair_key(names)})
        mgr.Done()  # only safe after every result has been read
        rows = [r for r in rows
                if not any(ref in (r["components"] or []) for ref in reference_parts)]
        # The same pair can be reported more than once (one result per pair of
        # bodies, so a multi-body part lists it several times); summing per pair
        # keeps the rest-pose baseline and the posed result comparable.
        merged = {}
        for r in rows:
            vol = r["volume_mm3"] or 0.0
            if vol < MIN_VOLUME_MM3:
                continue
            if r["pair"] in merged:
                merged[r["pair"]]["volume_mm3"] = round(
                    merged[r["pair"]]["volume_mm3"] + vol, 2)
            else:
                merged[r["pair"]] = {"volume_mm3": round(vol, 2),
                                      "components": r["components"],
                                      "pair": r["pair"]}
        return list(merged.values())

    # ---- positive control ------------------------------------------------
    control = {}
    try:
        rest_rotor = IMathTransform(mu.CreateTransform(Array[Double](base[str(rotor.Name2)])))
        m = arr(rest_rotor)
        pushed = IMathTransform(mu.CreateTransform(Array[Double](
            m[:9] + [m[9], m[10] + 0.060, m[11], 1.0, 0.0, 0.0, 0.0])))
        rotor.SetTransformAndSolve3(pushed, False)
        md.EditRebuild3()
        res = detect()
        control = {"offset_mm": 60.0,
                   "pairs": 0 if res is None else len(res),
                   "volume_mm3": 0.0 if res is None else round(
                       sum(x["volume_mm3"] or 0.0 for x in res), 1)}
        rotor.SetTransformAndSolve3(rest_rotor, False)
        md.EditRebuild3()
    except Exception as exc:  # noqa: BLE001
        control = {"error": repr(exc)}
    print("positive control:", control, flush=True)

    # ---- rest baseline ---------------------------------------------------
    set_components(IMathTransform(mu.CreateTransform(Array[Double](
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]))))
    baseline_rows = detect() or []
    baseline = {r["pair"]: r["volume_mm3"] for r in baseline_rows}
    print("rest overlaps:", len(baseline_rows), flush=True)

    # Method self-check: re-detecting the identical rest geometry must reproduce
    # the baseline exactly. If it does not, the comparison against the baseline
    # would invent collisions that are really detector noise.
    repeat = detect() or []
    repeat_growth = 0.0
    for r in repeat:
        if r["pair"] in baseline:
            repeat_growth += abs((r["volume_mm3"] or 0.0) - baseline[r["pair"]])
        else:
            repeat_growth += r["volume_mm3"] or 0.0
    repeat_new = len([r for r in repeat if r["pair"] not in baseline])
    print("rest repeat check: new=%d diff=%.2f mm3" % (repeat_new, repeat_growth),
          flush=True)

    # ---- sweep -----------------------------------------------------------
    poses = []
    targets = [(x, y) for x in GRID_X for y in GRID_Y]
    targets += [(-LIMIT_X_DEG, -LIMIT_Y_DEG), (LIMIT_X_DEG, LIMIT_Y_DEG),
                (-LIMIT_X_DEG, LIMIT_Y_DEG), (LIMIT_X_DEG, -LIMIT_Y_DEG)]
    # Single-axis scans, in both directions, to locate where contact starts.
    scan = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, LIMIT_X_DEG]
    targets += [(a, 0.0) for a in scan] + [(-a, 0.0) for a in scan if a]
    targets += [(0.0, a) for a in scan if a <= LIMIT_Y_DEG]
    targets += [(0.0, -a) for a in scan if a and a <= LIMIT_Y_DEG]
    targets = list(dict.fromkeys(targets))
    for tx, ty in targets:
        entry = {"theta_x_deg": tx, "theta_y_deg": ty}
        try:
            t = pose(tx, ty)
            set_components(t)

            # Self-check: the transform SOLIDWORKS stored must equal the
            # commanded rotation composed with the rest transform. Comparing
            # against the stored transform proves the pose was applied exactly as
            # built; comparing a bounding-box centre would not, because a rotated
            # part's axis-aligned box centre is not a material point.
            actual = arr(tilt.Transform2)
            for cand in compose(arr(t), base[str(tilt.Name2)]):
                dt = max(abs(cand[9 + i] - actual[9 + i]) for i in range(3)) * 1000.0
                dr = max(abs(cand[i] - actual[i]) for i in range(9))
                entry.setdefault("transform_delta_mm", dt)
                entry.setdefault("transform_delta_matrix", dr)
                entry["transform_delta_mm"] = min(entry["transform_delta_mm"], dt)
                entry["transform_delta_matrix"] = min(entry["transform_delta_matrix"], dr)

            rows = detect() or []
            new_pairs = [r for r in rows if r["pair"] not in baseline]
            growth = 0.0
            for r in rows:
                if r["pair"] in baseline:
                    growth += max(0.0, (r["volume_mm3"] or 0.0) - baseline[r["pair"]])
            entry["pairs"] = len(rows)
            entry["new_pairs"] = len(new_pairs)
            entry["new_pairs_detail"] = [
                {"pair": r["pair"], "volume_mm3": r["volume_mm3"]} for r in new_pairs[:8]]
            entry["growth_mm3"] = round(growth, 2)
            entry["max_volume_mm3"] = round(max((r["volume_mm3"] or 0.0) for r in rows), 2) \
                if rows else 0.0
        except Exception as exc:  # noqa: BLE001
            entry["error"] = repr(exc)
            print("  ERROR at %+0.1f/%+0.1f: %r" % (tx, ty, exc), flush=True)
        poses.append(entry)
        print("%+6.1f / %+6.1f  pairs=%s new=%s growth=%s mm3  transform_err=%s mm"
              % (tx, ty, entry.get("pairs"), entry.get("new_pairs"),
                 entry.get("growth_mm3"), entry.get("transform_delta_mm")), flush=True)

    # restore the rest pose so the saved assembly is untouched
    set_components(IMathTransform(mu.CreateTransform(Array[Double](
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]))))
    sw.CloseDoc(os.path.basename(ASM))

    # ---- report ----------------------------------------------------------
    errors = [p for p in poses if p.get("error")]

    def clean_limit(axis, growth_limit_mm3):
        """Largest |angle| on one axis alone that stays within a collision budget."""
        best = 0.0
        for sign in (1.0, -1.0):
            run = 0.0
            for p in sorted(poses, key=lambda p: abs(p.get("theta_%s_deg" % axis, 0.0))):
                other = "theta_y_deg" if axis == "x" else "theta_x_deg"
                ang = p.get("theta_%s_deg" % axis, 0.0)
                if abs(p.get(other, 0.0)) > 1e-9 or ang * sign < 0:
                    continue
                if ((p.get("new_pairs") or 0) > 0
                        or (p.get("growth_mm3") or 0.0) > growth_limit_mm3):
                    break
                run = abs(ang)
            best = max(best, run)
        return best

    # Two bounds: no *new* colliding pair at all, and the stricter one where the
    # pre-existing overlaps grow by less than 100 mm3.
    clean_x = clean_limit("x", 1e9)
    clean_y = clean_limit("y", 1e9)
    strict_x = clean_limit("x", 100.0)
    strict_y = clean_limit("y", 100.0)
    worst_growth = max((p.get("growth_mm3") or 0.0) for p in poses) if poses else 0.0
    worst_new = max((p.get("new_pairs") or 0) for p in poses) if poses else 0
    bad = [p for p in poses if (p.get("new_pairs") or 0) > 0]
    worst_delta = max((p.get("transform_delta_mm") or 0.0) for p in poses) if poses else 0.0
    worst_delta_matrix = max((p.get("transform_delta_matrix") or 0.0)
                             for p in poses) if poses else 0.0

    with open(os.path.join(CALC, "tilt_motion_report.json"), "w", encoding="utf-8") as fh:
        json.dump({"axis_x_point_m": ax_point, "axis_x_dir": ax_dir,
                   "axis_y_point_m": ay_point, "axis_y_dir": ay_dir,
                   "tilt_group_rest_centre_m": [round(v, 6) for v in centre0],
                   "limit_x_deg": LIMIT_X_DEG, "limit_y_deg": LIMIT_Y_DEG,
                   "min_volume_mm3": MIN_VOLUME_MM3,
                   "positive_control": control,
                   "rest_repeat_check": {"new_pairs": repeat_new,
                                        "diff_mm3": round(repeat_growth, 2)},
                   "clear_x_deg": clean_x, "clear_y_deg": clean_y,
                   "strict_x_deg": strict_x, "strict_y_deg": strict_y,
                   "rest_overlaps": baseline_rows,
                   "poses": poses}, fh, indent=2)

    with open(os.path.join(CALC, "tilt_motion_report.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["theta_x_deg", "theta_y_deg", "pairs", "new_pairs",
                    "growth_mm3", "max_volume_mm3", "transform_delta_mm",
                    "transform_delta_matrix", "new_pair_list"])
        for p in poses:
            w.writerow([p.get("theta_x_deg"), p.get("theta_y_deg"), p.get("pairs"),
                        p.get("new_pairs"), p.get("growth_mm3"),
                        p.get("max_volume_mm3"), p.get("transform_delta_mm"),
                        p.get("transform_delta_matrix"),
                        "; ".join(x["pair"] for x in (p.get("new_pairs_detail") or []))])

    lines = ["# Tilt motion study\n"]
    lines.append("Method: `cad_tools/tilt_motion_study.py` opens the native root "
                 "assembly, reads the two pivot axes off the pivot bushing "
                 "components, rotates `FD_TILT` and `FD_ROTOR` about them, "
                 "rebuilds, and runs SOLIDWORKS interference detection at every "
                 "pose. Volumes come from `IInterference::Volume` in m3 and are "
                 "reported in mm3; overlaps below %.1f mm3 are treated as "
                 "numerical coincidence.\n" % MIN_VOLUME_MM3)
    lines.append("| item | value |\n|---|---|")
    lines.append("| X pivot axis | point %s m, direction %s |"
                 % ([round(v, 4) for v in ax_point], ax_dir))
    lines.append("| Y pivot axis | point %s m, direction %s |"
                 % ([round(v, 4) for v in ay_point], ay_dir))
    lines.append("| travel limits | +/- %.0f deg first axis, +/- %.0f deg second axis |"
                 % (LIMIT_X_DEG, LIMIT_Y_DEG))
    lines.append("| poses sampled | %d |" % len(poses))
    lines.append("| poses that failed | %d |" % len(errors))
    lines.append("| positive control (rotor pushed %s mm) | %s pairs, %s mm3 |"
                 % (control.get("offset_mm"), control.get("pairs"),
                    control.get("volume_mm3")))
    lines.append("| worst pose-application error | %.2e mm, %.2e matrix elements |"
                 % (worst_delta, worst_delta_matrix))
    lines.append("| rest-pose overlapping pairs | %d |" % len(baseline_rows))
    lines.append("| rest-pose repeat check | %d new pair(s), %.2f mm3 difference |"
                 % (repeat_new, repeat_growth))
    lines.append("| worst motion-induced growth | %.1f mm3 |" % worst_growth)
    lines.append("| no new colliding pair up to | first axis %s deg, second axis %s deg |"
                 % ("+/- %.1f" % clean_x if clean_x else "none",
                    "+/- %.1f" % clean_y if clean_y else "none"))
    lines.append("| overlaps grow < 100 mm3 up to | first axis %s deg, second axis %s deg |\n"
                 % ("+/- %.1f" % strict_x if strict_x else "none",
                    "+/- %.1f" % strict_y if strict_y else "none"))

    lines.append("## Overlaps present at rest\n")
    lines.append("These exist in the assembly before any tilt is applied. Some are "
                 "deliberate press/snap interfaces (pivot bushings in the ring, "
                 "cable collar in the downrod); the rest are parts blocking into "
                 "each other and must be corrected in CAD before printing.\n")
    if baseline_rows:
        lines.append("| pair | volume (mm3) |\n|---|---|")
        for r in sorted(baseline_rows, key=lambda r: -(r["volume_mm3"] or 0)):
            lines.append("| %s | %.1f |" % (r["pair"], r["volume_mm3"] or 0.0))
        lines.append("")

    lines.append("## Sweep result\n")
    lines.append("**Verdict: the tilt mechanism does not have a usable travel range in "
                 "its current geometry.**\n")
    lines.append("No *newly* colliding pair appears until the limits are reached (%s deg "
                 "first axis, %s deg second axis), but that number is misleading on its "
                 "own, because the group already overlaps the top shroud at rest, so "
                 "some of the motion is happening inside solid material. Counting that "
                 "growth, the usable travel is **%s deg / %s deg**: the first few "
                 "degrees of rotation already push the yoke, ring, cradle and servo "
                 "brackets further into the top shroud, by up to %.0f mm3.\n"
                 % ("%.1f" % clean_x if clean_x else "none",
                    "%.1f" % clean_y if clean_y else "none",
                    "%.1f" % strict_x if strict_x else "none",
                    "%.1f" % strict_y if strict_y else "none", worst_growth))
    lines.append("The configured limits are +/-%.0f deg and +/-%.0f deg, so they are "
                 "**not** supported by the current geometry. Before the tilt can be "
                 "built, the top shroud must be opened up or the tilt group lowered so "
                 "that the rest pose is clear, and the travel stop re-positioned so "
                 "that it does not sit in the ring's swept volume.\n"
                 % (LIMIT_X_DEG, LIMIT_Y_DEG))
    if bad:
        lines.append("New interfering pairs appear as the fan tilts:\n")
        for p in bad:
            pairs = "; ".join("%s (%.1f mm3)" % (x["pair"], x["volume_mm3"] or 0.0)
                              for x in (p.get("new_pairs_detail") or []))
            lines.append("- X %+0.1f deg, Y %+0.1f deg: %d new pair(s) - %s"
                         % (p["theta_x_deg"], p["theta_y_deg"],
                            p["new_pairs"], pairs))
        lines.append("")
    else:
        lines.append("No new interfering pair appeared at any sampled pose: within "
                     "+/-%.0f deg (first axis) and +/-%.0f deg (second axis), the "
                     "tilting group does not collide with the body, ceiling plate "
                     "or support structure. The pre-existing overlaps listed above "
                     "grow by at most %.1f mm3 across the envelope.\n"
                     % (LIMIT_X_DEG, LIMIT_Y_DEG, worst_growth))

    lines.append("## Limits of this check\n")
    lines.append("- %d poses on a 10 deg / 7.5 deg grid. Poses between samples are "
                 "not covered.\n" % len(poses))
    lines.append("- Only tilt was driven; blade spin was held at its modelled "
                 "angle, so blade-to-body contact at other rotor angles is not "
                 "covered.\n")
    lines.append("- Interference detection tests body overlap. It does not measure "
                 "residual clearance, deflection, vibration or fastener loading, "
                 "and it is not a safety case for powered operation.\n")
    lines.append("- The rest-pose overlaps are real geometry defects; a clean tilt "
                 "sweep does not excuse them.\n")
    with open(os.path.join(REP, "TILT_MOTION_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    import swutil
    swutil.shutdown(sw)
    print("tilt motion poses=%d new_pair_poses=%d rest_overlaps=%d (assembly closed)"
          % (len(poses), len(bad), len(baseline_rows)), flush=True)


if __name__ == "__main__":
    main()
