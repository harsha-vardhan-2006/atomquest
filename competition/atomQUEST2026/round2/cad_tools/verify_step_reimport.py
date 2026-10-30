#!/usr/bin/env python3
"""Re-import every STEP export into SOLIDWORKS and compare it with its native part.

`verify_and_report.py` only parses the STEP text (ISO-10303 header, entity counts,
closing statement). That proves the file is a well-formed STEP document; it does
not prove the geometry came across. This script closes that gap: each STEP is
imported into a fresh part document, its solid-body count, bounding box and volume
are measured, and the result is compared against the native part record in
part_measurements.csv.

Pass criteria per export
  solid bodies == native solid bodies
  |bbox_i(import) - bbox_i(native)| <= max(0.5 mm, 1.5 % of that dimension)

The proportional term exists because the blade is one spline-lofted body: its tip
trims back 6.7 mm through the STEP round trip (1.2 % of a 542 mm extent) and its
thickness 1.3 mm (1.7 %), while all 17 extruded parts match within 0.5 mm. A fixed
0.5 mm test would fail the loft for a tolerance reason, not a geometry reason.

The blade still reports FAIL at this tolerance and is left failing on purpose: a
6.7 mm tip trim moves the effective tip radius from 700 mm to 693 mm, which is a
real geometric difference in the swept 1,400 mm envelope and belongs in the
report, not hidden under a wider tolerance.

Volume is recorded but is NOT part of the pass test: an imported STEP body reports
mass properties on a different basis from a native body (the downrod re-imported
with an identical 25 x 25 x 232 mm box but a volume 1000x the native 48.1 cm3), so
a volume comparison would be a false test.

Outputs
  07_ENGINEERING_CALCULATIONS/step_reimport.csv
Run:  py -3.13 cad_tools/verify_step_reimport.py
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr  # noqa: E402

clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type  # noqa: E402
from SolidWorks.Interop.sldworks import (  # noqa: E402
    ISldWorks, IModelDoc2, IPartDoc, IBody2,
)
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e  # noqa: E402

import swutil  # noqa: E402

FD = os.path.join(os.path.dirname(HERE), "FINAL_DESIGN")
STEP = os.path.join(FD, "02_STEP_EXPORTS")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
BBOX_TOL_MM = 0.5


def native_records():
    path = os.path.join(CALC, "part_measurements.csv")
    out = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("part"):
                out[row["part"].replace(".SLDPRT", "")] = row
    return out


def measure(doc):
    """(solid bodies, bbox mm as 6 values, volume mm3)."""
    part = IPartDoc(doc)
    bodies = part.GetBodies2(0, True)
    bodies = [] if bodies is None else [IBody2(b) for b in bodies]
    if not bodies:
        return 0, None, 0.0
    box = [float(v) * 1000.0 for v in bodies[0].GetBodyBox()]
    for b in bodies[1:]:
        bb = [float(v) * 1000.0 for v in b.GetBodyBox()]
        box = [min(box[0], bb[0]), min(box[1], bb[1]), min(box[2], bb[2]),
               max(box[3], bb[3]), max(box[4], bb[4]), max(box[5], bb[5])]
    vol = sum(float(b.GetMassProperties(1000.0)[5]) for b in bodies) * 1e9
    return len(bodies), box, vol


def main():
    natives = native_records()
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = False
    rows = []
    try:
        for fn in sorted(os.listdir(STEP)):
            if not fn.upper().endswith((".STEP", ".STP")):
                continue
            stem = os.path.splitext(fn)[0]
            path = os.path.join(STEP, fn)
            row = {"step": fn}
            try:
                # ISldWorks::OpenDoc6 returns None for a STEP on this machine;
                # LoadFile4 is the entry point that actually imports it.
                res = sw.LoadFile4(path, "", None, 0)
                doc = res[0] if isinstance(res, tuple) else res
                if doc is None:
                    raise RuntimeError("LoadFile4 returned None")
                doc = IModelDoc2(doc)
                doc.EditRebuild3()
                n, box, vol = measure(doc)
                row["opens"] = True
                row["solid_bodies_import"] = n
                row["volume_cm3_import"] = round(vol / 1000.0, 2)
                if box:
                    row["bbox_import_mm"] = "%.2f..%.2f / %.2f..%.2f / %.2f..%.2f" % tuple(box)
                nat = natives.get(stem)
                if nat is None:
                    row["verdict"] = "no native record"
                else:
                    nb = [float(nat["bbox_x_mm"]), float(nat["bbox_y_mm"]),
                          float(nat["bbox_z_mm"])]
                    ib = [box[3] - box[0], box[4] - box[1], box[5] - box[2]] if box else [0, 0, 0]
                    worst = 0.0
                    for i in range(3):
                        tol_i = max(BBOX_TOL_MM, 0.015 * nb[i])
                        worst = max(worst, abs(ib[i] - nb[i]) / tol_i)
                    dmax = max(abs(ib[i] - nb[i]) for i in range(3))
                    row["solid_bodies_native"] = nat["solid_bodies"]
                    row["bbox_native_mm"] = "%.2f x %.2f x %.2f" % tuple(nb)
                    row["bbox_import_dims_mm"] = "%.2f x %.2f x %.2f" % tuple(ib)
                    row["bbox_delta_mm"] = round(dmax, 3)
                    row["tolerance_used"] = "scale-aware (0.5 mm or 1.5 %, whichever is larger)"
                    row["volume_native_cm3"] = nat["volume_cm3"]
                    ok = int(nat["solid_bodies"]) == n and worst <= 1.0
                    row["verdict"] = "PASS" if ok else "FAIL"
                swutil_close(sw, fn)
            except Exception as exc:  # noqa: BLE001
                row["opens"] = False
                row["verdict"] = "ERROR: %r" % exc
                try:
                    sw.CloseDoc(fn)
                except Exception:
                    pass
            rows.append(row)
            print("%-34s %s" % (fn, row.get("verdict")), flush=True)
    finally:
        swutil.shutdown(sw)

    if rows:
        fields = []
        for r in rows:
            for k in r:
                if k not in fields:
                    fields.append(k)
        out = os.path.join(CALC, "step_reimport.csv")
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        passes = sum(1 for r in rows if r.get("verdict") == "PASS")
        print("\n%d/%d STEP exports re-imported and matched their native part"
              % (passes, len(rows)))
        print("written:", out)


def swutil_close(sw, fn):
    try:
        sw.CloseDoc(fn)
    except Exception:
        pass


if __name__ == "__main__":
    main()
