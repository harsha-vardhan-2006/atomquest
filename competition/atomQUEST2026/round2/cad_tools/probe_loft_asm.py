#!/usr/bin/env python3
"""Probe: why the loft feature and the assembly NewDocument fail."""
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr  # noqa: E402

clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))

from System import Activator, Type  # noqa: E402
from SolidWorks.Interop.sldworks import (  # noqa: E402
    ISldWorks, IModelDoc2, IPartDoc, IFeature)

TPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Part.PRTDOT"
ATPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Assembly.ASMDOT"
OUT = r"C:\tmp\sw_smoke"
os.makedirs(OUT, exist_ok=True)


def feats(md):
    out = []
    f = md.FirstFeature()
    while f is not None:
        ft = IFeature(f)
        out.append("%s(%s)" % (ft.Name, ft.GetTypeName2()))
        f = ft.GetNextFeature()
    return out


def select(md, name, typ, mark=0, append=False):
    return md.Extension.SelectByID2(name, typ, 0.0, 0.0, 0.0, bool(append), mark, None, 0)


sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
print("rev", sw.RevisionNumber(), flush=True)

# ---------------------------------------------------------------- loft probe
md = IModelDoc2(sw.NewDocument(TPL, 0, 0.0, 0.0))
part = IPartDoc(md)
select(md, "Front Plane", "PLANE")
md.SketchManager.InsertSketch(True)
md.SketchManager.CreateCircle(0.0, 0.0, 0.0, 0.05, 0.0, 0.0)
md.SketchManager.InsertSketch(True)
part.FeatureExtrusion3(True, False, False, 0, 0, 0.01, 0.0,
                       False, False, False, False, 0.0, 0.0,
                       False, False, False, False, True)
md.EditRebuild3()
print("features after boss:", feats(md), flush=True)

select(md, "Front Plane", "PLANE")
md.FeatureManager.InsertRefPlane(8, 0.06, 0, 0.0, 0, 0.0)
print("features after plane:", feats(md), flush=True)
select(md, "Plane1", "PLANE")
md.SketchManager.InsertSketch(True)
md.SketchManager.CreateCircle(0.0, 0.0, 0.06, 0.03, 0.0, 0.06)
md.SketchManager.InsertSketch(True)
select(md, "Front Plane", "PLANE")
md.SketchManager.InsertSketch(True)
md.SketchManager.CreateCircle(0.0, 0.0, 0.0, 0.045, 0.0, 0.0)
md.SketchManager.InsertSketch(True)
print("features after sketches:", feats(md), flush=True)

s3 = [n for n in feats(md) if n.startswith("Sketch")]
print("sections available:", s3, flush=True)
sec = [n.split("(")[0] for n in s3][-2:]
print("using sections:", sec, flush=True)

for label, method in (("blend marks", "A"), ("AddLoftSection", "B")):
    if method == "A":
        md.Extension.SelectByID2(sec[0], "SKETCH", 0.0, 0.0, 0.0, False, 1, None, 0)
        md.Extension.SelectByID2(sec[1], "SKETCH", 0.0, 0.0, 0.0, True, 2, None, 0)
    else:
        md.Extension.SelectByID2(sec[0], "SKETCH", 0.0, 0.0, 0.0, False, 0, None, 0)
        try:
            md.AddLoftSection()
        except Exception as e:
            print("  AddLoftSection exc", e, flush=True)
        md.Extension.SelectByID2(sec[1], "SKETCH", 0.0, 0.0, 0.0, False, 0, None, 0)
        try:
            md.AddLoftSection()
        except Exception as e:
            print("  AddLoftSection exc", e, flush=True)
    try:
        f1 = md.FeatureManager.InsertProtrusionBlend(False, True, False, 0.01, 0, 0, 0.0, 0.0,
                                                     False, False, False, 0.0, 0.0, 0, True, True, True)
        print("InsertProtrusionBlend(%s) -> %s" % (label, f1), flush=True)
    except Exception as e:
        print("InsertProtrusionBlend(%s) EXC %s: %s" % (label, type(e).__name__, str(e)[:200]), flush=True)
    print("  features:", feats(md), flush=True)
    if any("Loft" in x or "Blend" in x for x in feats(md)):
        break
    try:
        f2 = md.FeatureManager.InsertProtrusionBlend2(False, True, False, 0.01, 0, 0, 0.0, 0.0,
                                                      False, False, False, 0.0, 0.0, 0, True, True, True, 0)
        print("InsertProtrusionBlend2(%s) -> %s" % (label, f2), flush=True)
    except Exception as e:
        print("InsertProtrusionBlend2(%s) EXC %s: %s" % (label, type(e).__name__, str(e)[:200]), flush=True)
    print("  features:", feats(md), flush=True)

print("bbox:", part.GetPartBox(True), flush=True)
md.Extension.SaveAs(os.path.join(OUT, "loft_probe.SLDPRT"), 0, 2, None, 0, 0)
sw.CloseDoc(md.GetPathName())

# ---------------------------------------------------------- assembly probe
print("\n--- assembly creation ---", flush=True)
for label, fn in (
    ("NewDocument int", lambda: sw.NewDocument(ATPL, 0, 0, 0)),
    ("NewDocument float", lambda: sw.NewDocument(ATPL, 0, 0.0, 0.0)),
    ("NewDocument2", lambda: sw.NewDocument2(ATPL, 0, 0, 0)),
    ("CreateAssembly", lambda: sw.CreateAssembly()),
):
    try:
        r = fn()
        print("%-20s -> %s %s" % (label, type(r).__name__, repr(r)[:100]), flush=True)
        if r is not None:
            try:
                a = IModelDoc2(r)
                print("   cast OK, features:", feats(a)[:6], flush=True)
                a.Extension.SaveAs(os.path.join(OUT, "asm_probe.SLDASM"), 0, 2, None, 0, 0)
                print("   saved:", os.path.exists(os.path.join(OUT, "asm_probe.SLDASM")), flush=True)
                break
            except Exception as e:
                print("   cast failed:", str(e)[:100], flush=True)
    except Exception as e:
        print("%-20s EXC %s: %s" % (label, type(e).__name__, str(e)[:200]), flush=True)

sw.ExitApp()
print("done", flush=True)
