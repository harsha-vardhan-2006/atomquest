#!/usr/bin/env python3
"""Export PNG previews of the finished assemblies so appearance can be checked."""
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type
from SolidWorks.Interop.sldworks import ISldWorks, IModelDoc2
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINAL_DESIGN")
ASM = os.path.join(FD, "04_ASSEMBLIES")
REP = os.path.join(FD, "08_VERIFICATION_REPORTS")
os.makedirs(REP, exist_ok=True)

sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
sw.Visible = True
try:
    for name, view, tag in (("FD_SMART_FAN_ASSEMBLY", "*Isometric", "assembly_isometric"),
                            ("FD_SMART_FAN_ASSEMBLY", "*Front", "assembly_front"),
                            ("FD_SMART_FAN_ASSEMBLY", "*Bottom", "assembly_bottom"),
                            ("FD_TILT", "*Isometric", "tilt_isometric")):
        path = os.path.join(ASM, "%s.SLDASM" % name)
        r = sw.OpenDoc6(path, int(swDocumentTypes_e.swDocASSEMBLY),
                        int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
        md = IModelDoc2(r[0] if isinstance(r, tuple) else r)
        md.ShowNamedView2(view, 7)
        md.ViewZoomtofit2()
        png = os.path.join(REP, "%s.png" % tag)
        md.Extension.SaveAs(png, 0, 1, None, 0, 0)
        print(tag, os.path.isfile(png), os.path.getsize(png) if os.path.isfile(png) else 0,
              flush=True)
        sw.CloseDoc("%s.SLDASM" % name)
finally:
    import swutil
    swutil.shutdown(sw)
    print("closed", flush=True)
