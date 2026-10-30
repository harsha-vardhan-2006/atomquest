#!/usr/bin/env python3
"""Create drawing sheets for every native part and assembly, with dimensions.

Per part: Create3rdAngleViews2 builds the standard view set without interactive
picking, then IDrawingDoc::InsertModelAnnotations4 inserts the model dimensions
and notes into every view in one call. Per assembly: the same view set, plus a
BOM table (IView::InsertBomTable5) and auto balloons (IDrawingDoc::AutoBalloon5).

The dimension count per view is read back and written to drawing_report.json, so
"this sheet is dimensioned" is a measured claim rather than an assumption.

A PNG of the main assembly is also exported so the assembled appearance can be
inspected directly.
"""
import csv
import json
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type
from SolidWorks.Interop.sldworks import (
    ISldWorks, IModelDoc2, IDrawingDoc, IView, IAnnotation,
)
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINAL_DESIGN")
PARTS = os.path.join(FD, "01_NATIVE_PARTS")
ASM = os.path.join(FD, "04_ASSEMBLIES")
OUT = os.path.join(FD, "06_DRAWINGS")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
REP = os.path.join(FD, "08_VERIFICATION_REPORTS")
TPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Drawing.DRWDOT"


def views_of(draw):
    out = []
    view = draw.GetFirstView()
    while view is not None:
        v = IView(view)
        out.append(v)
        view = v.GetNextView()
    return out


def measured_dims():
    """Overall dimensions, material and mass per part, from the part audit."""
    path = os.path.join(CALC, "part_measurements.csv")
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("part"):
                out[row["part"].replace(".SLDPRT", "")] = row
    return out


def add_note(md, text, x=0.02, y=0.02):
    """Put a text note on the active sheet (sheet space is metres).

    IModelDoc2::InsertNote returns an object that the COM projection exposes
    without GetAnnotation(), so the note itself is used as the annotation; only a
    failed placement is treated as an error, because the note is already in the
    document once InsertNote returns an object.
    """
    try:
        note = md.InsertNote(text)
    except Exception:  # noqa: BLE001
        return False
    if note is None:
        return False
    for target in (note, getattr(note, "GetAnnotation", None)):
        if target is None:
            continue
        try:
            IAnnotation(target).SetPosition(x, y, 0.0)
            break
        except Exception:  # noqa: BLE001
            continue
    return True


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(REP, exist_ok=True)
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = True
    report = {}
    measured = measured_dims()
    asm_report = {}
    report_path = os.path.join(CALC, "assembly_report.json")
    if os.path.isfile(report_path):
        with open(report_path, encoding="utf-8") as fh:
            asm_report = json.load(fh)
    sources = [(os.path.join(PARTS, f), swDocumentTypes_e.swDocPART)
               for f in sorted(os.listdir(PARTS)) if f.upper().endswith(".SLDPRT")]
    sources += [(os.path.join(ASM, f), swDocumentTypes_e.swDocASSEMBLY)
                for f in sorted(os.listdir(ASM)) if f.upper().endswith(".SLDASM")]

    for path, kind in sources:
        name = os.path.splitext(os.path.basename(path))[0]
        target = os.path.join(OUT, "%s_DRAWING.SLDDRW" % name)
        entry = {"source": os.path.basename(path)}
        try:
            r = sw.OpenDoc6(path, int(kind),
                            int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
            src = r[0] if isinstance(r, tuple) else r
            if src is None:
                raise RuntimeError("cannot open source")
            doc = sw.NewDocument(TPL, 0, 0.0, 0.0)
            draw = IDrawingDoc(IModelDoc2(doc))
            entry["views_created"] = bool(draw.Create3rdAngleViews2(path))
            md = IModelDoc2(doc)
            md.EditRebuild3()

            ann = draw.InsertModelAnnotations4(0, 0, True, False, False, False, True, False)
            entry["annotations_inserted"] = ann is not None
            md.EditRebuild3()

            dims = []
            for v in views_of(draw):
                try:
                    dims.append(int(v.GetDimensionCount()))
                except Exception:  # noqa: BLE001
                    dims.append(0)
            entry["dimension_counts"] = dims
            entry["dimensions_total"] = sum(dims)

            # The parts are built from undimensioned sketch geometry, so there are
            # no model dimensions for InsertModelAnnotations4 to carry into the
            # views (measured: 0 dimensions on every sheet). Each sheet therefore
            # states the CAD-measured overall size, material and mass as a note,
            # so the drawing carries real numbers instead of looking dimensioned.
            dim = measured.get(name)
            if dim:
                text = ("OVERALL %.1f x %.1f x %.1f mm   |   %s   |   mass %.3f kg"
                        "   |   CAD-derived"
                        % (float(dim["bbox_x_mm"]), float(dim["bbox_y_mm"]),
                           float(dim["bbox_z_mm"]), dim["material"],
                           float(dim["mass_kg"])))
            elif name in asm_report:
                info = asm_report[name]
                if "error" in info:
                    text = "ASSEMBLY BUILD FAILED: %s" % info["error"]
                else:
                    text = ("ASSEMBLY: %d components, %d mate features, "
                            "volume-mass %.3f kg at 1000 kg/m3"
                            % (info["components"]["component_count"],
                               info["mate_features_created"],
                               info["components"]["sw_mass_kg_at_1000kgm3"]))
            else:
                text = "NO MEASURED DIMENSIONS AVAILABLE"
            entry["note_inserted"] = add_note(md, text)
            entry["note_text"] = text
            md.EditRebuild3()

            if kind == swDocumentTypes_e.swDocASSEMBLY:
                try:
                    sheet = views_of(draw)[0]
                    bom = sheet.InsertBomTable5(False, 0.30, 0.05, 1, 1, "", "", False,
                                                0, False, True)
                    entry["bom_table"] = bom is not None
                    md.EditRebuild3()
                    opts = draw.CreateAutoBalloonOptions() if hasattr(
                        draw, "CreateAutoBalloonOptions") else None
                    entry["balloons"] = bool(draw.AutoBalloon5(opts)) if opts else False
                except Exception as exc:  # noqa: BLE001
                    entry["bom_error"] = repr(exc)

            saved = md.Extension.SaveAs(target, 0, 1, None, 0, 0)
            saved_ok = saved[0] if isinstance(saved, tuple) else saved
            entry["saved"] = bool(saved_ok) and os.path.isfile(target)
            entry["bytes"] = os.path.getsize(target) if os.path.isfile(target) else 0
            sw.CloseDoc(os.path.basename(target) if entry["saved"] else md.GetTitle())
            sw.CloseDoc(os.path.basename(path))
        except Exception as exc:  # noqa: BLE001
            entry["error"] = repr(exc)
        report[name] = entry
        print(name, entry.get("dimensions_total"), entry.get("bom_table"),
              entry.get("error", ""), flush=True)

    # ---- appearance preview of the finished assembly ----
    try:
        r = sw.OpenDoc6(os.path.join(ASM, "FD_SMART_FAN_ASSEMBLY.SLDASM"),
                        int(swDocumentTypes_e.swDocASSEMBLY),
                        int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
        md = IModelDoc2(r[0] if isinstance(r, tuple) else r)
        md.ShowNamedView2("*Isometric", 7)
        md.ViewZoomtofit2()
        png = os.path.join(REP, "assembly_isometric.png")
        res = md.Extension.SaveAs(png, 0, 1, None, 0, 0)
        report["_preview"] = {"saved": os.path.isfile(png),
                              "bytes": os.path.getsize(png) if os.path.isfile(png) else 0,
                              "result": str(res)}
        sw.CloseDoc("FD_SMART_FAN_ASSEMBLY.SLDASM")
    except Exception as exc:  # noqa: BLE001
        report["_preview"] = {"error": repr(exc)}

    with open(os.path.join(CALC, "drawing_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    import swutil
    swutil.shutdown(sw)
    print("drawings done (documents closed)", flush=True)


if __name__ == "__main__":
    main()
