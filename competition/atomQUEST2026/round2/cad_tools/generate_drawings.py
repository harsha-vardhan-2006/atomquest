#!/usr/bin/env python3
"""Create drawing sheets for every native part and assembly.

Uses IDrawingDoc::Create3rdAngleViews2, which builds the standard view set from a
document path without any interactive picking. Each drawing is opened, saved and
closed before the next one is created.

The resulting sheets carry model views, not fully dimensioned manufacturing
drawings: model-annotation insertion and manual dimensioning need the selection
path that is unavailable in this session.
"""
import json
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type
from SolidWorks.Interop.sldworks import ISldWorks, IModelDoc2, IDrawingDoc
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINAL_DESIGN")
PARTS = os.path.join(FD, "01_NATIVE_PARTS")
ASM = os.path.join(FD, "04_ASSEMBLIES")
OUT = os.path.join(FD, "06_DRAWINGS")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
TPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Drawing.DRWDOT"


def main():
    os.makedirs(OUT, exist_ok=True)
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = True
    report = {}
    sources = [(os.path.join(PARTS, f), swDocumentTypes_e.swDocPART)
               for f in sorted(os.listdir(PARTS)) if f.upper().endswith(".SLDPRT")]
    sources += [(os.path.join(ASM, f), swDocumentTypes_e.swDocASSEMBLY)
                for f in sorted(os.listdir(ASM)) if f.upper().endswith(".SLDASM")]

    for path, kind in sources:
        name = os.path.splitext(os.path.basename(path))[0]
        target = os.path.join(OUT, "%s_VIEWS.SLDDRW" % name)
        entry = {"source": os.path.basename(path)}
        try:
            r = sw.OpenDoc6(path, int(kind),
                            int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
            src = r[0] if isinstance(r, tuple) else r
            if src is None:
                raise RuntimeError("cannot open source %s" % path)
            doc = sw.NewDocument(TPL, 0, 0.0, 0.0)
            if doc is None:
                raise RuntimeError("cannot create drawing from template")
            draw = IDrawingDoc(IModelDoc2(doc))
            ok = draw.Create3rdAngleViews2(path)
            entry["views_created"] = bool(ok)
            if not ok:
                ok2 = draw.CreateDrawViewFromModelView3(path, "*Front",
                                                         0.06, 0.06, 0.0)
                entry["front_view_created"] = ok2 is not None
                ok = bool(ok2)
            md = IModelDoc2(doc)
            md.EditRebuild3()
            saved = md.Extension.SaveAs(target, 0, 1, None, 0, 0)
            saved_ok = saved[0] if isinstance(saved, tuple) else saved
            entry["saved"] = bool(saved_ok) and os.path.isfile(target)
            entry["bytes"] = os.path.getsize(target) if os.path.isfile(target) else 0
            sw.CloseDoc(os.path.basename(target) if entry["saved"] else md.GetTitle())
            sw.CloseDoc(os.path.basename(path))
        except Exception as exc:  # noqa: BLE001
            entry["error"] = repr(exc)
        report[name] = entry
        print(entry, flush=True)

    with open(os.path.join(CALC, "drawing_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    sw.ExitApp()


if __name__ == "__main__":
    main()
