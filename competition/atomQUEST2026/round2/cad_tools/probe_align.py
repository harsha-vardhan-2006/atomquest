#!/usr/bin/env python3
"""Which AddMate5 alignment constrains two coincident faces without moving parts?

The assembly build creates a mate whose faces are measured to be exactly
0.000 mm apart / coaxial, yet every created mate reports a large component
shift (60 mm and a 180 deg flip for the blade joints). That pattern is what a
flipped alignment looks like, so this probe creates the same joint with each
swMateAlign_e value and measures what each one does to the components.

Run:  py -3.13 probe_align.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_final_assemblies as B  # noqa: E402  (sets up the SolidWorks interop)
import swutil  # noqa: E402

SW_DOC_ASM = 2
SW_OPEN_SILENT = 1


def main():
    sw = B.ISldWorks(B.Activator.CreateInstance(B.Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = True
    try:
        run(sw)
    finally:
        swutil.shutdown(sw)
        print("solidworks closed", flush=True)


def run(sw):
    path = os.path.join(B.ASM_DIR, "FD_ROTOR.SLDASM")
    print("opening", path, flush=True)
    doc = B.IAssemblyDoc(sw.OpenDoc6(path, SW_DOC_ASM, SW_OPEN_SILENT, "", 0, 0)[0])
    md = B.IModelDoc2(doc)
    sd = B.SelectionMgr(md.SelectionManager).CreateSelectData()

    comps = [B.IComponent2(c) for c in (doc.GetComponents(False) or [])]
    by_name = {str(c.Name2): c for c in comps}
    print("components:", sorted(by_name), flush=True)

    hub, blade = by_name["FD_BladeHub-1"], by_name["FD_Blade-1"]
    fa, fb = B.comp_faces(blade), B.comp_faces(hub)

    for kind, mate_type in (("coincident", B.MATE_TYPES["coincident"]),
                            ("concentric", B.MATE_TYPES["concentric"])):
        m = B.match_faces(fa, fb, kind)
        if m is None:
            print(kind, "no face pair", flush=True)
            continue
        print("\n%s pair: %s" % (kind, m["detail"]), flush=True)
        for align in (0, 1, 2, 3):
            before = {str(c.Name2): [float(v) for v in c.Transform2.ArrayData]
                      for c in comps}
            md.ClearSelection2(True)
            ok1 = bool(B.IEntity(m["a"]["face"]).Select4(False, sd))
            ok2 = bool(B.IEntity(m["b"]["face"]).Select4(True, sd))
            sm = md.SelectionManager
            types = []
            for i in (1, 2):
                try:
                    types.append(int(sm.GetSelectedObjectType3(i, sd)))
                except Exception:
                    types.append(None)
            try:
                res = doc.AddMate5(mate_type, align, False,
                                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                   False, False, 0, 0)
            except Exception as exc:  # noqa: BLE001
                print("  align=%d AddMate5 raised %r" % (align, exc), flush=True)
                continue
            md.EditRebuild3()
            mate = res[0] if isinstance(res, tuple) else res
            err = res[1] if isinstance(res, tuple) else None
            dt = dr = 0.0
            for c in comps:
                after = [float(v) for v in c.Transform2.ArrayData]
                b = before[str(c.Name2)]
                dt = max(dt, max(abs(after[9 + i] - b[9 + i]) for i in range(3)) * 1000.0)
                r1 = [[b[0], b[1], b[2]], [b[3], b[4], b[5]], [b[6], b[7], b[8]]]
                r2 = [[after[0], after[1], after[2]], [after[3], after[4], after[5]],
                      [after[6], after[7], after[8]]]
                rel = [[sum(r2[i][k] * r1[j][k] for k in range(3)) for j in range(3)]
                       for i in range(3)]
                tr = rel[0][0] + rel[1][1] + rel[2][2]
                dr = max(dr, math.degrees(math.acos(max(-1.0, min(1.0, (tr - 1.0) / 2.0)))))
            print("  align=%d sel_ok=%s/%s types=%s mate=%s err=%s shift=%.3f mm %.2f deg"
                  % (align, ok1, ok2, types,
                     [str(B.IFeature(mate).Name)] if mate is not None else None,
                     err, dt, dr),
                  flush=True)
            if mate is not None:
                md.EditUndo2(1)
                md.EditRebuild3()


if __name__ == "__main__":
    main()
