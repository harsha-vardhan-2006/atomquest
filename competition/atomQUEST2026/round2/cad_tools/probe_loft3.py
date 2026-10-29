#!/usr/bin/env python3
"""Probe 3: isolate why InsertProtrusionBlend (loft) returns null."""
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr  # noqa: E402

clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))

from System import Activator, Type  # noqa: E402
from SolidWorks.Interop.sldworks import ISldWorks, IModelDoc2, IFeature  # noqa: E402

TPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Part.PRTDOT"


def feats(md):
    out, f = [], md.FirstFeature()
    while f is not None:
        ft = IFeature(f)
        if ft.GetTypeName2() == "ProfileFeature" or "RefPlane" in ft.GetTypeName2():
            out.append(ft.Name)
        f = ft.GetNextFeature()
    return out


def sel_count(md):
    try:
        return md.SelectionManager.GetSelectedObjectCount2(-1)
    except Exception as e:
        return "err:%s" % str(e)[:60]


def sel_names(md):
    n = md.SelectionManager.GetSelectedObjectCount2(-1)
    out = []
    for i in range(1, n + 1):
        try:
            out.append(md.SelectionManager.GetSelectedObject3(i))
        except Exception as e:
            out.append("err:%s" % str(e)[:40])
    return out


sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
print("rev", sw.RevisionNumber(), flush=True)
md = IModelDoc2(sw.NewDocument(TPL, 0, 0, 0))

md.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, None, 0)
md.SketchManager.InsertSketch(True)
md.SketchManager.CreateCircle(0.0, 0.0, 0.0, 0.045, 0.0, 0.0)
md.SketchManager.InsertSketch(True)

md.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, None, 0)
print("refplane:", md.FeatureManager.InsertRefPlane(8, 0.06, 0, 0.0, 0, 0.0) is not None, flush=True)
md.Extension.SelectByID2("Plane1", "PLANE", 0.0, 0.0, 0.0, False, 0, None, 0)
md.SketchManager.InsertSketch(True)
md.SketchManager.CreateCircle(0.0, 0.0, 0.06, 0.03, 0.0, 0.06)
md.SketchManager.InsertSketch(True)
print("features:", feats(md), flush=True)
md.EditRebuild3()

VARIANTS = [
    ("marks 1/2, tangency False, tess 0.01", (False, False, False, 0.01, 0, 0, 0.0, 0.0,
                                               False, False, False, 0.0, 0.0, 0, True, True, True),
     (1, 2), True),
    ("marks 1/2, tangency False, tess 1.0", (False, False, False, 1.0, 0, 0, 0.0, 0.0,
                                              False, False, False, 0.0, 0.0, 0, True, True, True),
     (1, 2), True),
    ("marks 1/1", (False, False, False, 0.01, 0, 0, 0.0, 0.0,
                   False, False, False, 0.0, 0.0, 0, True, True, True),
     (1, 1), True),
    ("no marks, merge False", (False, False, False, 0.01, 0, 0, 0.0, 0.0,
                               False, False, False, 0.0, 0.0, 0, False, True, True),
     (0, 0), True),
    ("marks 1/2 merge False", (False, False, False, 0.01, 0, 0, 0.0, 0.0,
                               False, False, False, 0.0, 0.0, 0, False, True, True),
     (1, 2), True),
    ("closed True", (True, False, False, 0.01, 0, 0, 0.0, 0.0,
                     False, False, False, 0.0, 0.0, 0, True, True, True),
     (1, 2), True),
]

for label, args, marks, append in VARIANTS:
    md.Extension.SelectByID2("Sketch1", "SKETCH", 0.0, 0.0, 0.0, False, marks[0], None, 0)
    md.Extension.SelectByID2("Sketch2", "SKETCH", 0.0, 0.0, 0.0, append, marks[1], None, 0)
    cnt = sel_count(md)
    try:
        f = md.FeatureManager.InsertProtrusionBlend(*args)
    except Exception as e:
        f = "EXC %s: %s" % (type(e).__name__, str(e)[:120])
    names = feats(md)
    got = [n for n in names if n not in ("Front Plane", "Top Plane", "Right Plane", "Origin",
                                         "Sketch1", "Sketch2", "Plane1")]
    print("%-42s sel=%s -> %s | new=%s" % (label, cnt, f, got), flush=True)
    if got:
        break

print("final features:", feats(md), flush=True)
print("bbox:", md.GetPartBox(True) if hasattr(md, "GetPartBox") else "-", flush=True)
sw.ExitApp()
print("done", flush=True)
