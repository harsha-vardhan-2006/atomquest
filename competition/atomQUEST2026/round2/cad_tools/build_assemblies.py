#!/usr/bin/env python3
"""Build preliminary free-positioned concept assemblies; close each SW app.

The parts have no reviewed mating interfaces. Component positions are indicative
only; they are not constrained, load-rated, or motion-ready. Clearance is not
verified. Do not treat these assemblies as released mechanisms.
"""
import os
import sys
import clr

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type, Array, Double
from SolidWorks.Interop.sldworks import ISldWorks, IMathUtility, IModelDoc2, IAssemblyDoc, IComponent2, ISelectionMgr
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e, swMateType_e, swMateAlign_e

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSEMBLIES = [
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_DualRingGimbal_Assembly.SLDASM", [
        ("M1_CeilingPlate.SLDPRT", (0.0, 0.0, 0.0)),
        ("M1_SupportHousing.SLDPRT", (0.025, 0.025, 0.450)),
        ("M1_OuterRing.SLDPRT", (-0.150, -0.150, 0.370)),
        ("M1_InnerRing.SLDPRT", (-0.090, -0.090, 0.280)),
        ("M1_FanCarrier.SLDPRT", (-0.075, -0.075, 0.200)),
        ("M1_MotorInterface.SLDPRT", (-0.100, -0.100, 0.145)),
        ("M1_HubCone.SLDPRT", (-0.080, -0.080, 0.065)),
        ("M1_ServoMount.SLDPRT", (-0.050, -0.030, 0.320)),
    ]),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_SphericalGimbal_Assembly.SLDASM", [
        ("M2_CeilingPlate.SLDPRT", (0.0, 0.0, 0.0)),
        ("M2_SupportUpper.SLDPRT", (0.015, 0.015, 0.450)),
        ("M2_InnerGimbalRing.SLDPRT", (-0.190, -0.190, 0.340)),
        ("M2_XPivotHub.SLDPRT", (-0.060, -0.060, 0.315)),
        ("M2_YPivotHub.SLDPRT", (-0.050, -0.050, 0.325)),
        ("M2_FanCarrier.SLDPRT", (-0.200, -0.200, 0.250)),
        ("M2_MotorInterface.SLDPRT", (-0.080, -0.080, 0.205)),
        ("M2_HubCone.SLDPRT", (-0.070, -0.070, 0.135)),
        ("M2_SphericalHousing.SLDPRT", (-0.300, -0.300, 0.050)),
    ]),
]
TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Assembly.ASMDOT"


def main():
    for model, asm_name, parts in ASSEMBLIES:
        sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
        sw.Visible = True
        asm_path = os.path.join(R2, model, "02_CAD_ASSEMBLIES", asm_name)
        try:
            for filename, _ in parts:
                path = os.path.join(R2, model, "01_CAD_PARTS", filename)
                result = sw.OpenDoc6(path, int(swDocumentTypes_e.swDocPART),
                                     int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
                doc = result[0] if isinstance(result, tuple) else result
                if doc is None:
                    raise RuntimeError("Cannot open required part %s" % path)
            md = IModelDoc2(sw.NewDocument(TEMPLATE, 0, 0.0, 0.0))
            asm = IAssemblyDoc(md)
            math = IMathUtility(sw.GetMathUtility())
            comps = []
            for index, (filename, (tx, ty, tz)) in enumerate(parts):
                path = os.path.join(R2, model, "01_CAD_PARTS", filename)
                comp = asm.AddComponent5(path, 0, "", False, "", tx, ty, tz)
                if comp is None:
                    raise RuntimeError("AddComponent5 failed for %s" % filename)
                # Use AddComponent5's nominal insertion coordinates without adding
                # mates. The currently available concept geometry has no reviewed
                # mating interfaces, so this is not an articulated assembly.
                comps.append(IComponent2(comp))
            # Rebuild and verify the component list; transform placement and
            # relative fit remain preliminary and are not treated as a clearance check.
            mates_added = 0
            md.EditRebuild3()
            expected = len(parts)
            got = asm.GetComponentCount(True)
            if got != expected:
                raise RuntimeError("Assembly component count %s != %s" % (got, expected))
            os.makedirs(os.path.dirname(asm_path), exist_ok=True)
            saved = md.Extension.SaveAs(asm_path, 0, 1, None, 0, 0)
            if not saved[0] or not os.path.isfile(asm_path) or os.path.getsize(asm_path) < 10000:
                raise RuntimeError("Assembly save failed or unexpectedly small: %s" % asm_path)
            print("PASS %s components=%d mates=%d saved=%d bytes; concept layout only" % (asm_name, got, mates_added, os.path.getsize(asm_path)), flush=True)
            sw.CloseDoc(os.path.basename(asm_path))
        finally:
            sw.ExitApp()
            print("SOLIDWORKS closed after %s" % asm_name, flush=True)


if __name__ == "__main__":
    main()
