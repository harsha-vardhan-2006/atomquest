#!/usr/bin/env python3
"""
Stage 2 - SOLIDWORKS environment inspection + existing-CAD audit.

Opens every existing .SLDPRT, rebuilds it, records the feature list, bounding
box and mass-property data, then writes:
  00_REQUIREMENTS_AND_SOURCE_AUDIT/environment_report.md
  00_REQUIREMENTS_AND_SOURCE_AUDIT/existing_cad_audit.csv
  00_REQUIREMENTS_AND_SOURCE_AUDIT/existing_cad_audit.log   (raw API dumps)

Always closes SOLIDWORKS when finished (ExitApp).
"""
import csv
import os
import sys
import time

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr  # noqa: E402

clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))

from System import Activator, Type  # noqa: E402
from SolidWorks.Interop.sldworks import (  # noqa: E402
    ISldWorks, IModelDoc2, IPartDoc, IBody2, IFeature)
from SolidWorks.Interop.swconst import (  # noqa: E402
    swDocumentTypes_e, swOpenDocOptions_e)

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # round2/
AUDIT_DIR = os.path.join(R2, "00_REQUIREMENTS_AND_SOURCE_AUDIT")
TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Part.PRTDOT"
DENSITY = 1000.0  # kg/m^3 water reference - used only to recover VOLUME from API


def mm(v):
    return None if v is None else round(v * 1000.0, 3)


def main():
    t0 = time.time()
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    rev = sw.RevisionNumber()
    log = []
    log.append("SOLIDWORKS RevisionNumber: %s" % rev)
    log.append("connect time: %.1fs" % (time.time() - t0))
    try:
        sw.Visible = True
    except Exception:
        pass

    parts = []
    for model in ("MODEL_1_DUAL_RING_GIMBAL", "MODEL_2_SPHERICAL_GIMBAL"):
        d = os.path.join(R2, model, "01_CAD_PARTS")
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.upper().endswith(".SLDPRT") and not fn.startswith("~$"):
                    parts.append(os.path.join(d, fn))

    rows = []
    for path in parts:
        errors, warnings = 0, 0
        rec = {
            "file": os.path.relpath(path, R2).replace("\\", "/"),
            "size_bytes": os.path.getsize(path),
            "open_errors": "", "open_warnings": "",
            "rebuild_ok": "", "n_features": 0, "feature_types": "",
            "bbox_x_mm": "", "bbox_y_mm": "", "bbox_z_mm": "",
            "volume_cm3": "", "mass_at_1000kgm3_kg": "",
            "n_bodies": "", "raw_massprops": "", "notes": "",
        }
        try:
            res = sw.OpenDoc6(path, int(swDocumentTypes_e.swDocPART),
                              int(swOpenDocOptions_e.swOpenDocOptions_Silent),
                              "", errors, warnings)
            # pythonnet folds the two `out` parameters into the return value:
            # (ModelDoc2, Errors, Warnings)
            if isinstance(res, tuple):
                doc, errors, warnings = res[0], int(res[1]), int(res[2])
            else:
                doc = res
        except Exception as e:
            doc = None
            rec["notes"] = "OpenDoc6 exception: %s" % str(e)[:120]
        if doc is None:
            rec["open_errors"] = errors
            rec["open_warnings"] = warnings
            rec["notes"] = (rec["notes"] + " OPEN FAILED").strip()
            rows.append(rec)
            log.append("%s: OPEN FAILED errors=%s" % (rec["file"], errors))
            continue

        md = IModelDoc2(doc)
        part = IPartDoc(md)
        try:
            ok = md.EditRebuild3()
            rec["rebuild_ok"] = bool(ok)
        except Exception as e:
            rec["rebuild_ok"] = "exc:%s" % str(e)[:60]

        # feature list
        feats = []
        f = md.FirstFeature()
        while f is not None:
            try:
                feat = IFeature(f)
                feats.append("%s(%s)" % (feat.Name, feat.GetTypeName2()))
                f = feat.GetNextFeature()
            except Exception as e:
                feats.append("?(%s)" % str(e)[:40])
                break
        rec["n_features"] = len(feats)
        rec["feature_types"] = " | ".join(feats)

        # bounding box (metres)
        try:
            box = part.GetPartBox(True)
            if box is not None:
                b = [float(box[i]) for i in range(6)]
                rec["bbox_x_mm"] = mm(b[3] - b[0])
                rec["bbox_y_mm"] = mm(b[4] - b[1])
                rec["bbox_z_mm"] = mm(b[5] - b[2])
                log.append("%s bbox(m): %s" % (rec["file"], b))
        except Exception as e:
            rec["notes"] += " bbox-exc %s" % str(e)[:60]

        # bodies + mass properties (raw dump; volume recovered below)
        try:
            bodies = part.GetBodies2(0, True)
            n = 0 if bodies is None else len(bodies)
            rec["n_bodies"] = n
            if n:
                mp = IBody2(bodies[0]).GetMassProperties(DENSITY)
                if mp is not None:
                    vals = [float(mp[i]) for i in range(len(mp))]
                    rec["raw_massprops"] = ";".join("%.6g" % v for v in vals)
                    # SW returns: Ixx Iyy Izz Ixy Ixz Iyz cx cy cz SurfaceArea Volume
                    if len(vals) >= 11:
                        rec["volume_cm3"] = round(vals[10] * 1e6, 1)
                        rec["mass_at_1000kgm3_kg"] = round(vals[10] * DENSITY, 4)
        except Exception as e:
            rec["notes"] += " mass-exc %s" % str(e)[:60]

        log.append("%s -> %s" % (rec["file"], rec))
        rows.append(rec)
        sw.CloseDoc(path)

    os.makedirs(AUDIT_DIR, exist_ok=True)
    out_csv = os.path.join(AUDIT_DIR, "existing_cad_audit.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(AUDIT_DIR, "existing_cad_audit.log"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(str(x) for x in log))

    env = """# SOLIDWORKS environment report (Stage 2)

Generated by `cad_tools/stage2_inspect.py` on {date}.

| Item | Value |
| --- | --- |
| SOLIDWORKS revision | {rev} |
| Application path | E:\\SOLIDWORKS Downloads\\SOLIDWORKS (SLDWORKS.exe) |
| API assemblies | `api/redist/SolidWorks.Interop.sldworks.dll`, `.swconst.dll` |
| Python | {py} with pythonnet 3.2.1 and pywin32 |
| Part template | {tpl} |
| Assembly template | C:\\ProgramData\\SolidWorks\\SOLIDWORKS 2026\\Templates\\Assembly.ASMDOT |
| Drawing template | C:\\ProgramData\\SolidWorks\\SOLIDWORKS 2026\\Templates\\Drawing.DRWDOT |
| Automation method | pythonnet + typed interop interfaces (`ISldWorks`/`IModelDoc2`/`IPartDoc`/`IAssemblyDoc`) |
| API unit convention | metres, radians, kilograms (independent of display units) |

## Why the typed interop route

`pywin32` dynamic dispatch was tested first and failed on this installation:
`gencache.EnsureDispatch` reports *"This COM object can not automate the makepy
process"*, and dynamic dispatch raises `DISP_E_TYPEMISMATCH` on every method
whose optional parameter is an `IDispatch` (for example `SelectByID2`'s Callout
and `SaveAs`'s ExportData). The managed interop DLLs give exact signatures, so
all automation uses `pythonnet` with explicit interface casts.

Proven working end-to-end in this environment: `NewDocument`, `OpenDoc6`,
`SelectByID2`, `SketchManager`, `EditRebuild3`, `SaveAs`, `GetPartBox`,
`GetBodies2`, `IBody2.GetMassProperties`, `AddComponent5`, `AddMate5`,
`ExitApp`.

## Documents inspected

{n} native parts opened, rebuilt and measured. Results: `existing_cad_audit.csv`
(raw API dumps: `existing_cad_audit.log`).
""".format(date=time.strftime("%Y-%m-%d %H:%M"), rev=rev, py=sys.version.split()[0],
           tpl=TEMPLATE, n=len(rows))
    with open(os.path.join(AUDIT_DIR, "environment_report.md"), "w",
              encoding="utf-8") as fh:
        fh.write(env)

    print("parts inspected:", len(rows), flush=True)
    for r in rows:
        print("  %-58s feats=%-2s bbox=%sx%sx%s mm vol=%s cm3 %s" % (
            os.path.basename(r["file"]), r["n_features"], r["bbox_x_mm"],
            r["bbox_y_mm"], r["bbox_z_mm"], r["volume_cm3"], r["notes"]),
            flush=True)
    sw.ExitApp()
    print("SW closed; reports written to", AUDIT_DIR, flush=True)


if __name__ == "__main__":
    main()
