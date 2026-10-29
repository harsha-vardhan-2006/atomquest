#!/usr/bin/env python3
"""Export each concept part and assembly to AP203 STEP, one SW session each."""
import os
import sys
import clr

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type
from SolidWorks.Interop.sldworks import ISldWorks, IModelDoc2
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = [
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_DualRingGimbal_Assembly.SLDASM", [
        "M1_CeilingPlate.SLDPRT", "M1_SupportHousing.SLDPRT", "M1_OuterRing.SLDPRT",
        "M1_InnerRing.SLDPRT", "M1_FanCarrier.SLDPRT", "M1_MotorInterface.SLDPRT",
        "M1_HubCone.SLDPRT", "M1_ServoMount.SLDPRT",
    ]),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_SphericalGimbal_Assembly.SLDASM", [
        "M2_CeilingPlate.SLDPRT", "M2_SupportUpper.SLDPRT", "M2_InnerGimbalRing.SLDPRT",
        "M2_XPivotHub.SLDPRT", "M2_YPivotHub.SLDPRT", "M2_FanCarrier.SLDPRT",
        "M2_MotorInterface.SLDPRT", "M2_HubCone.SLDPRT", "M2_SphericalHousing.SLDPRT",
    ]),
]


def main():
    for model, assembly, parts in MODELS:
        export_dir = os.path.join(R2, model, "11_NEUTRAL_EXPORTS")
        os.makedirs(export_dir, exist_ok=True)
        items = [(name, "part") for name in parts] + [(assembly, "assembly")]
        for filename, kind in items:
            sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
            sw.Visible = True
            doc = None
            try:
                folder = "02_CAD_ASSEMBLIES" if kind == "assembly" else "01_CAD_PARTS"
                source = os.path.join(R2, model, folder, filename)
                doc_type = swDocumentTypes_e.swDocASSEMBLY if kind == "assembly" else swDocumentTypes_e.swDocPART
                opened = sw.OpenDoc6(source, int(doc_type),
                                     int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
                doc = IModelDoc2(opened[0] if isinstance(opened, tuple) else opened)
                if doc is None or not doc.EditRebuild3():
                    raise RuntimeError("Open/rebuild failed: %s" % source)
                target = os.path.join(export_dir, os.path.splitext(filename)[0] + ".STEP")
                result = doc.Extension.SaveAs(target, 0, 1, None, 0, 0)
                if not result[0] or not os.path.isfile(target) or os.path.getsize(target) < 1000:
                    raise RuntimeError("STEP SaveAs failed: %s (%s)" % (target, result))
                with open(target, "rb") as fh:
                    step = fh.read()
                if b"ISO-10303-21;" not in step[:128] or b"END-ISO-10303-21;" not in step[-256:]:
                    raise RuntimeError("Export does not have valid STEP exchange-file delimiters: %s" % target)
                print("PASS %s %s %d bytes" % (kind, filename, len(step)), flush=True)
            finally:
                if doc is not None:
                    sw.CloseDoc(doc.GetTitle())
                sw.ExitApp()
                print("CLOSED SOLIDWORKS after %s" % filename, flush=True)


if __name__ == "__main__":
    main()
