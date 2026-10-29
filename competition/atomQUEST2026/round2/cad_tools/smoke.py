#!/usr/bin/env python3
"""
Stage 3 smoke test - prove the risky SOLIDWORKS API calls before the real build.

Tests (each prints PASS/FAIL):
  1  IPartDoc.FeatureExtrusion3            solid boss
  2  IModelDoc2.FeatureCut5                through bore
  3  IFeatureManager.InsertRefPlane        offset plane
  4  IFeatureManager.InsertProtrusionBlend2 loft between two sections
  5  IModelDoc2.InsertAxis                 reference axis from two planes
  6  IAssemblyDoc.AddComponent5            place component
  7  mate: entity selection + AddMate5      coincident mate

Runs in a scratch folder (C:\\tmp\\sw_smoke), never in the repository.
Closes SOLIDWORKS (ExitApp) when finished.
"""
import os
import sys
import time

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr  # noqa: E402

clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))

from System import Activator, Type, Array, Object, Double  # noqa: E402
from SolidWorks.Interop.sldworks import (  # noqa: E402
    ISldWorks, IModelDoc2, IPartDoc, IAssemblyDoc, IFeature, IEntity, IComponent2)
from SolidWorks.Interop.swconst import (  # noqa: E402
    swDocumentTypes_e, swOpenDocOptions_e, swBodyType_e,
    swMateType_e, swMateAlign_e)

OUT = r"C:\tmp\sw_smoke"
TPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Part.PRTDOT"
ATPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Assembly.ASMDOT"
os.makedirs(OUT, exist_ok=True)

RESULTS = []


def t(name, fn):
    try:
        r = fn()
        RESULTS.append((name, "PASS", str(r)[:120]))
        print("PASS %-42s -> %s" % (name, str(r)[:120]), flush=True)
        return r
    except Exception as e:
        RESULTS.append((name, "FAIL", "%s: %s" % (type(e).__name__, str(e)[:200])))
        print("FAIL %-42s -> %s: %s" % (name, type(e).__name__, str(e)[:200]), flush=True)
        return None


def select(md, name, typ="PLANE", mark=0, append=False):
    return md.Extension.SelectByID2(name, typ, 0.0, 0.0, 0.0, bool(append), mark, None, 0)


def start_sketch(md, plane_name):
    select(md, plane_name, "PLANE")
    md.SketchManager.InsertSketch(True)


def close_sketch(md):
    md.SketchManager.InsertSketch(True)


def n_bodies(part):
    b = part.GetBodies2(int(swBodyType_e.swSolidBody), True)
    return 0 if b is None else len(b)


def main():
    t0 = time.time()
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    print("rev", sw.RevisionNumber(), flush=True)
    try:
        sw.Visible = True
    except Exception:
        pass

    # ---- part with boss + bore ------------------------------------------------
    md = IModelDoc2(sw.NewDocument(TPL, 0, 0.0, 0.0))
    part = IPartDoc(md)

    def tx_boss():
        start_sketch(md, "Front Plane")
        md.SketchManager.CreateCircle(0.0, 0.0, 0.0, 0.05, 0.0, 0.0)
        close_sketch(md)
        part.FeatureExtrusion3(True, False, False, 0, 0, 0.01, 0.0,
                               False, False, False, False, 0.0, 0.0,
                               False, False, False, False, True)
        md.EditRebuild3()
        return "bodies=%d bbox=%s" % (n_bodies(part), part.GetPartBox(True))
    t("1 FeatureExtrusion3 boss", tx_boss)

    def tx_bore():
        start_sketch(md, "Front Plane")
        md.SketchManager.CreateCircle(0.0, 0.0, 0.0, 0.02, 0.0, 0.0)
        close_sketch(md)
        md.FeatureCut5(True, False, False, 1, 0, 0.0, 0.0,
                       False, False, False, False, 0.0, 0.0,
                       False, False, False, False, 0, False)
        md.EditRebuild3()
        return "bodies=%d" % n_bodies(part)
    t("2 FeatureCut5 bore", tx_bore)

    def tx_plane():
        select(md, "Front Plane", "PLANE")
        # swRefPlaneReferenceConstraint_Distance = 8
        f = md.FeatureManager.InsertRefPlane(8, 0.06, 0, 0.0, 0, 0.0)
        name = IFeature(f).Name if f is not None else None
        return "plane=%s" % name
    plane_name = t("3 InsertRefPlane offset", tx_plane)

    def tx_loft():
        # section 1 on the offset plane (name reported by test 3), section 2 on Front Plane
        pn = (plane_name or "plane=Front Plane").split("=", 1)[-1]
        if not select(md, pn, "PLANE"):
            raise RuntimeError("cannot select offset plane %r" % pn)

        md.SketchManager.InsertSketch(True)
        md.SketchManager.CreateCircle(0.0, 0.0, 0.06, 0.03, 0.0, 0.06)
        md.SketchManager.InsertSketch(True)
        # second section on the Front Plane (this becomes Sketch4)
        select(md, "Front Plane", "PLANE", 0, False)
        md.SketchManager.InsertSketch(True)
        md.SketchManager.CreateCircle(0.0, 0.0, 0.0, 0.045, 0.0, 0.0)
        md.SketchManager.InsertSketch(True)
        # select both sections with marks 1 and 2 (Sketch3 on offset, Sketch4 front)
        sel1 = select(md, "Sketch3", "SKETCH", 1)
        sel2 = select(md, "Sketch4", "SKETCH", 2)
        if not (sel1 and sel2):
            return "section selection failed (%s/%s)" % (sel1, sel2)
        feat = md.FeatureManager.InsertProtrusionBlend2(
            False, True, False, 0.01, 0, 0, 0.0, 0.0, False, False,
            False, 0.0, 0.0, 0, True, True, True, 0)
        md.EditRebuild3()
        return "feature=%s bodies=%d" % (
            IFeature(feat).Name if feat is not None else None, n_bodies(part))
    t("4 InsertProtrusionBlend2 loft", tx_loft)

    def tx_axis():
        select(md, "Front Plane", "PLANE", 1, False)
        sel_ok = select(md, "Top Plane", "PLANE", 2, True)
        ok = md.InsertAxis() if sel_ok else False
        ax = None
        f = md.FirstFeature()
        while f is not None:
            feat = IFeature(f)
            if "Axis" in feat.Name:
                ax = feat.Name
                break
            f = feat.GetNextFeature()
        return "ok=%s axis=%s" % (ok, ax)
    t("5 InsertAxis from two planes", tx_axis)

    part_path = os.path.join(OUT, "smoke_part.SLDPRT")
    md.Extension.SaveAs(part_path, 0, 2, None, 0, 0)
    sw.CloseDoc(part_path)

    # second, simpler part so the mate test is unambiguous
    md2 = IModelDoc2(sw.NewDocument(TPL, 0, 0.0, 0.0))

    def tx_p2():
        start_sketch(md2, "Front Plane")
        md2.SketchManager.CreateCircle(0.0, 0.0, 0.0, 0.04, 0.0, 0.0)
        close_sketch(md2)
        IPartDoc(md2).FeatureExtrusion3(True, False, False, 0, 0, 0.01, 0.0,
                                        False, False, False, False, 0.0, 0.0,
                                        False, False, False, False, True)
        md2.EditRebuild3()
        return "bodies=%d" % n_bodies(IPartDoc(md2))
    t("1b second part boss", tx_p2)
    p2_path = os.path.join(OUT, "smoke_part2.SLDPRT")
    md2.Extension.SaveAs(p2_path, 0, 2, None, 0, 0)
    sw.CloseDoc(p2_path)

    # ---- assembly ------------------------------------------------------------
    raw_asm = sw.NewDocument(ATPL, 0, 0.0, 0.0)
    print("assembly NewDocument raw:", type(raw_asm).__name__,
          repr(raw_asm)[:120], flush=True)
    if isinstance(raw_asm, tuple):
        raw_asm = raw_asm[0]
    asm_md = IModelDoc2(raw_asm)
    asm = IAssemblyDoc(asm_md)

    def tx_add():
        c1 = asm.AddComponent5(part_path, 0, "", False, "", 0.0, 0.0, 0.0)
        c2 = asm.AddComponent5(p2_path, 0, "", False, "", 0.2, 0.0, 0.0)
        return "components=%d" % asm.GetComponentCount(True)
    t("6 AddComponent5 x2", tx_add)

    comps = asm.GetComponents(False)
    c1name = IComponent2(comps[0]).Name2 if comps is not None and len(comps) else None
    c2name = IComponent2(comps[1]).Name2 if comps is not None and len(comps) > 1 else None
    print("component names:", c1name, c2name, flush=True)

    def tx_mate():
        # candidate selection strings for a component plane in assembly context
        candidates = [
            "Front Plane@%s" % c1name,
            "Front Plane@%s@%s" % (c1name, os.path.basename(asm_md.GetPathName())),
            "Front Plane@%s" % os.path.basename(part_path),
        ]
        ok1 = False
        used1 = None
        for cand in candidates:
            if asm_md.Extension.SelectByID2(cand, "PLANE", 0.0, 0.0, 0.0, False, 1, None, 0):
                ok1, used1 = True, cand
                break
        if not ok1:
            # fallback: select through the entity interface of the component document
            doc1 = IModelDoc2(IComponent2(comps[0]).GetModelDocument())
            f = doc1.FirstFeature()
            while f is not None:
                feat = IFeature(f)
                if feat.GetTypeName2() == "RefPlane" and feat.Name == "Front Plane":
                    ok1 = bool(IEntity(feat).Select2(False, 1))
                    used1 = "IEntity.Select2 on component doc (%s)" % ok1
                    break
                f = feat.GetNextFeature()
        # second selection
        ok2 = False
        used2 = None
        for cand in ["Front Plane@%s" % c2name,
                     "Front Plane@%s@%s" % (c2name, os.path.basename(asm_md.GetPathName()))]:
            if asm_md.Extension.SelectByID2(cand, "PLANE", 0.0, 0.0, 0.0, False, 2, None, 0):
                ok2, used2 = True, cand
                break
        if not ok2:
            doc2 = IModelDoc2(IComponent2(comps[1]).GetModelDocument())
            f = doc2.FirstFeature()
            while f is not None:
                feat = IFeature(f)
                if feat.GetTypeName2() == "RefPlane" and feat.Name == "Front Plane":
                    ok2 = bool(IEntity(feat).Select2(False, 2))
                    used2 = "IEntity.Select2 on component doc (%s)" % ok2
                    break
                f = feat.GetNextFeature()
        if not (ok1 and ok2):
            return "selection failed: %s | %s" % (used1, used2)
        res = asm.AddMate5(int(swMateType_e.swMateCOINCIDENT),
                           int(swMateAlign_e.swMateAlignCLOSEST), False,
                           0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                           False, False, 0, 0)
        mate, err = (res[0], res[1]) if isinstance(res, tuple) else (res, 0)
        return "sel1=%s sel2=%s mate=%s err=%s" % (
            used1, used2, mate is not None, err)
    t("7 AddMate5 coincident", tx_mate)

    asm_path = os.path.join(OUT, "smoke_asm.SLDASM")
    r = asm_md.Extension.SaveAs(asm_path, 0, 2, None, 0, 0)
    print("assembly saved:", r, os.path.exists(asm_path),
          os.path.getsize(asm_path) if os.path.exists(asm_path) else 0, flush=True)

    print("\n=== SUMMARY ===", flush=True)
    for n, s, d in RESULTS:
        print("%-4s %-42s %s" % (s, n, d), flush=True)
    sw.ExitApp()
    print("SW closed in %.1fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
