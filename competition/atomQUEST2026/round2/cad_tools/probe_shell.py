#!/usr/bin/env python3
"""Probe: can this session hollow a part and export a PNG preview?

Two questions only:
  1. FeatureManager.InsertFeatureShell(thickness, outward) on an existing solid.
  2. SaveAs a PNG so the model appearance can actually be inspected.
"""
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type
from SolidWorks.Interop.sldworks import ISldWorks, IModelDoc2, IPartDoc, IBody2, IFeatureManager
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINAL_DESIGN")
BLADE = os.path.join(FD, "01_NATIVE_PARTS", "FD_Blade.SLDPRT")
ASM = os.path.join(FD, "04_ASSEMBLIES", "FD_SMART_FAN_ASSEMBLY.SLDASM")
OUT = os.path.join(FD, "08_VERIFICATION_REPORTS")
os.makedirs(OUT, exist_ok=True)

sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
sw.Visible = True
try:
    r = sw.OpenDoc6(BLADE, int(swDocumentTypes_e.swDocPART),
                    int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
    md = IModelDoc2(r[0] if isinstance(r, tuple) else r)
    part = IPartDoc(md)
    b = [IBody2(x) for x in part.GetBodies2(0, True)]
    vol0 = float(b[0].GetMassProperties(1000.0)[5])
    print("solid volume before = %.1f cm3" % (vol0 * 1e6), flush=True)

    fm = IFeatureManager(md.FeatureManager)
    print("has InsertFeatureShell:", hasattr(fm, "InsertFeatureShell"), flush=True)
    f = fm.InsertFeatureShell(0.0012, False)
    md.EditRebuild3()
    b2 = [IBody2(x) for x in part.GetBodies2(0, True)]
    vol1 = float(b2[0].GetMassProperties(1000.0)[5]) if b2 else 0.0
    print("feature:", f is not None, "bodies:", len(b2),
          "volume after = %.1f cm3" % (vol1 * 1e6), flush=True)

    # undo so the on-disk part is untouched
    md.EditUndo2(1)
    md.EditRebuild3()
    b3 = [IBody2(x) for x in part.GetBodies2(0, True)]
    print("volume after undo = %.1f cm3"
          % (float(b3[0].GetMassProperties(1000.0)[5]) * 1e6), flush=True)

    # PNG preview of the assembly
    sw.CloseDoc(os.path.basename(BLADE))
    px = os.path.join(OUT, "preview_probe.png")
    a = sw.OpenDoc6(ASM, int(swDocumentTypes_e.swDocASSEMBLY),
                    int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
    amd = IModelDoc2(a[0] if isinstance(a, tuple) else a)
    amd.ShowNamedView2("*Isometric", 7)
    amd.ViewZoomtofit2()
    try:
        res = amd.Extension.SaveAs(px, 0, 1, None, 0, 0)
        print("png save result:", res, os.path.isfile(px),
              os.path.getsize(px) if os.path.isfile(px) else 0, flush=True)
    except Exception as exc:  # noqa: BLE001
        print("png save raised:", repr(exc), flush=True)
finally:
    sw.ExitApp()
    print("closed", flush=True)
