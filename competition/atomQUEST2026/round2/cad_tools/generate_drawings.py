#!/usr/bin/env python3
"""Create preliminary concept assembly drawings and PDFs, one SW session each."""
import os
import sys
import clr

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
from System import Activator, Type
from SolidWorks.Interop.sldworks import ISldWorks, IModelDoc2, IDrawingDoc, IView

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Drawing.DRWDOT"
DRAWINGS = [
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_DualRingGimbal_Assembly.SLDASM", "M1_DualRingGimbal_Overview"),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_SphericalGimbal_Assembly.SLDASM", "M2_SphericalGimbal_Overview"),
]


def main():
    for model, assembly, stem in DRAWINGS:
        sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
        sw.Visible = True
        doc = None
        outdir = os.path.join(R2, model, "03_DRAWINGS")
        source = os.path.abspath(os.path.join(R2, model, "02_CAD_ASSEMBLIES", assembly))
        drawing_path = os.path.join(outdir, stem + ".SLDDRW")
        pdf_path = os.path.join(outdir, stem + ".pdf")
        try:
            os.makedirs(outdir, exist_ok=True)
            raw = sw.NewDocument(TEMPLATE, 0, 0.0, 0.0)
            doc = IModelDoc2(raw[0] if isinstance(raw, tuple) else raw)
            drawing = IDrawingDoc(doc)
            view = drawing.CreateDrawViewFromModelView3(source, "*Isometric", 0.22, 0.15, 0.0)
            if view is None:
                raise RuntimeError("Could not create assembly isometric view: %s" % source)
            print("created view %s (%s)" % (IView(view).Name, IView(view).GetOrientationName()), flush=True)
            if not doc.EditRebuild3():
                raise RuntimeError("Drawing rebuild failed: %s" % stem)
            result = doc.Extension.SaveAs(drawing_path, 0, 1, None, 0, 0)
            if not result[0] or not os.path.isfile(drawing_path) or os.path.getsize(drawing_path) < 1000:
                raise RuntimeError("Native drawing save failed: %s (%s)" % (drawing_path, result))
            pdf = doc.Extension.SaveAs(pdf_path, 0, 1, None, 0, 0)
            if not pdf[0] or not os.path.isfile(pdf_path) or os.path.getsize(pdf_path) < 1000:
                raise RuntimeError("PDF drawing export failed: %s (%s)" % (pdf_path, pdf))
            with open(pdf_path, "rb") as fh:
                if not fh.read(8).startswith(b"%PDF-"):
                    raise RuntimeError("Invalid PDF signature: %s" % pdf_path)
            print("PASS %s saved (%d bytes) and PDF (%d bytes)" %
                  (stem, os.path.getsize(drawing_path), os.path.getsize(pdf_path)), flush=True)
        finally:
            if doc is not None:
                sw.CloseDoc(doc.GetTitle())
            sw.ExitApp()
            print("CLOSED SOLIDWORKS after %s" % stem, flush=True)


if __name__ == "__main__":
    main()
