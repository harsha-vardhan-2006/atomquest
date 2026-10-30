#!/usr/bin/env python3
"""Add real dimension annotations to every finished drawing sheet.

The first drawing build called IDrawingDoc::InsertModelAnnotations4, which inserted
zero dimensions: the parts are built from extruded primitives whose sketches carry
no dimension constraints, so there is nothing for SOLIDWORKS to import. That left
21 sheets with views and a size note but no dimension entities.

This pass dimensions the sheets from the drawing side instead, using only public
API calls:

* ``IView::GetVisibleEntities2`` collects the vertices and edges a view actually
  shows.
* ``IView::SelectEntity`` selects a pair of them (probe: 18/18 edges selectable in
  a blade view).
* ``IModelDoc2::AddHorizontalDimension2`` / ``AddVerticalDimension2`` /
  ``AddDimension2`` measures the pair. ``AddDimension2`` (smart dimension) is the
  only one that succeeds on all entity types; the oriented variants are tried
  first because they read better on a sheet.

The extremes are found in model space (min/max X, Y and Z vertices) rather than by
mapping to sheet space, so the measurement is of real geometry. Because a given
view projects two of the three model axes, each pair is offered to the horizontal,
vertical and aligned dimension calls in turn and the first one SOLIDWORKS accepts
is kept. A dimension is only counted when ``IView::GetDimensionCount4`` actually
increases, so the report states measured counts, not intended ones.
"""
import json
import math
import os
import sys

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))
from System import Activator, Type
from SolidWorks.Interop.sldworks import (
    ISldWorks, IModelDoc2, IDrawingDoc, IView, IEdge, ICurve, IVertex,
    ISelectionMgr,
)
from SolidWorks.Interop.swconst import (
    swDocumentTypes_e, swOpenDocOptions_e, swSelectType_e,
)

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINAL_DESIGN")
OUT = os.path.join(FD, "06_DRAWINGS")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
REP = os.path.join(FD, "08_VERIFICATION_REPORTS")

MAX_LINEAR_PER_VIEW = 2
MAX_DIAMETER_PER_VIEW = 2
BASE_GAP = 0.014   # metres from the view outline to the first dimension line
STACK_STEP = 0.016  # metres between stacked dimension lines


def views_of(draw):
    out = []
    view = draw.GetFirstView()
    while view is not None:
        v = IView(view)
        out.append(v)
        view = v.GetNextView()
    return out


def vertex_point(vert):
    try:
        p = IVertex(vert).GetPoint()
        return [float(v) for v in p]
    except Exception:  # noqa: BLE001
        return None


def circle_of(edge):
    """Return (centre xyz, radius mm) if the edge is a full circular edge."""
    try:
        crv = IEdge(edge).GetCurve()
        if crv is None:
            return None
        c = ICurve(crv)
        if not c.IsCircle():
            return None
        if not c.IsTrimmedCurve():
            pass
        prm = c.CircleParams
        if prm is None or len(prm) < 7:
            return None
        center = [float(prm[0]), float(prm[1]), float(prm[2])]
        radius = float(prm[6])
        if radius <= 0.0:
            return None
        return center, radius
    except Exception:  # noqa: BLE001
        return None


def add_pair(md, iv, ents, slot, outline):
    """Select two entities and add one dimension. Returns the call that worked."""
    before = int(iv.GetDimensionCount4())
    off = BASE_GAP + STACK_STEP * slot
    for kind, placer in (
        ("horizontal", lambda k: md.AddHorizontalDimension2(
            (outline[0] + outline[2]) / 2.0, outline[1] - off, 0.0)),
        ("vertical", lambda k: md.AddVerticalDimension2(
            outline[2] + off, (outline[1] + outline[3]) / 2.0, 0.0)),
        ("smart", lambda k: md.AddDimension2(
            outline[2] + off, outline[1] - off, 0.0)),
    ):
        md.ClearSelection2(True)
        picked = 0
        for e in ents:
            try:
                if iv.SelectEntity(e, True):
                    picked += 1
            except Exception:  # noqa: BLE001
                pass
        if picked != len(ents):
            md.ClearSelection2(True)
            continue
        try:
            res = placer(slot)
        except Exception:  # noqa: BLE001
            md.ClearSelection2(True)
            continue
        md.EditRebuild3()
        md.ClearSelection2(True)
        if int(iv.GetDimensionCount4()) > before:
            return kind
    return None


def line_edges(edges):
    """Model-space endpoints and unit direction of every straight edge."""
    out = []
    for e in edges:
        try:
            p = IEdge(e).GetCurveParams2()
        except Exception:  # noqa: BLE001
            continue
        if p is None or len(p) < 9:
            continue
        p0 = [float(p[1]), float(p[2]), float(p[3])]
        p1 = [float(p[4]), float(p[5]), float(p[6])]
        d = [float(p[7]), float(p[8]), float(p[9])] if len(p) > 9 else [0.0, 0.0, 0.0]
        n = math.sqrt(sum(c * c for c in d))
        if n < 1e-9:
            continue
        length = math.sqrt(sum((p1[i] - p0[i]) ** 2 for i in range(3)))
        if length < 1e-6:
            continue
        out.append({"edge": e, "p0": p0, "p1": p1, "dir": [c / n for c in d],
                    "length": length})
    return out


def parallel_pairs(lines, min_sep=0.0005):
    """Pairs of parallel edges, ordered by their perpendicular separation."""
    pairs = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            a, b = lines[i], lines[j]
            dot = abs(sum(a["dir"][k] * b["dir"][k] for k in range(3)))
            if dot < 0.995:
                continue
            v = [b["p0"][k] - a["p0"][k] for k in range(3)]
            along = sum(v[k] * a["dir"][k] for k in range(3))
            perp = math.sqrt(max(0.0, sum(c * c for c in v) - along * along))
            if perp < min_sep:
                continue
            pairs.append((perp, i, j))
    pairs.sort(key=lambda t: -t[0])
    return pairs


def dimension_view(md, iv, want_diameter=True):
    """Add linear and diameter dimensions to one view; returns their records."""
    added = []
    outline = [float(x) for x in iv.GetOutline()]
    if outline[2] - outline[0] < 1e-4:
        return added

    edges = iv.GetVisibleEntities2(None, int(swSelectType_e.swSelEDGES)) or []

    # --- linear dimensions between parallel edges ------------------------
    # Two edges of a part are parallel when they bound the same feature (a boss
    # wall, a slot, a plate thickness), so the widest such pair is the overall
    # size of the feature. Pairs are offered widest first and the first accepted
    # pair fills each of the two available slots.
    lines = line_edges(edges)
    slot = 0
    for sep, i, j in parallel_pairs(lines)[:12]:
        if slot >= MAX_LINEAR_PER_VIEW:
            break
        kind = add_pair(md, iv, [lines[i]["edge"], lines[j]["edge"]], slot, outline)
        if kind:
            added.append({"type": "linear", "separation_mm": round(sep * 1000.0, 2),
                          "edge_lengths_mm": [round(lines[i]["length"] * 1000.0, 1),
                                              round(lines[j]["length"] * 1000.0, 1)],
                          "call": kind})
            slot += 1

    # --- diameter dimensions for the largest circles ----------------------
    if not want_diameter:
        return added
    circles = []
    seen = []
    for e in edges:
        got = circle_of(e)
        if got is None:
            continue
        radius = got[1]
        # A view shows the same hole once per visible arc; dimensioning the same
        # diameter twice just clutters the sheet.
        if any(abs(radius - r) < 5e-5 for r in seen):
            continue
        seen.append(radius)
        circles.append((radius, e, got[0]))
    circles.sort(key=lambda t: -t[0])
    placed = 0
    for radius, edge, center in circles:
        if placed >= MAX_DIAMETER_PER_VIEW:
            break
        before = int(iv.GetDimensionCount4())
        md.ClearSelection2(True)
        try:
            ok = iv.SelectEntity(edge, True)
        except Exception:  # noqa: BLE001
            ok = False
        if not ok:
            md.ClearSelection2(True)
            continue
        try:
            md.AddDiameterDimension2(outline[2] + BASE_GAP + STACK_STEP * placed,
                                     outline[3] + BASE_GAP + STACK_STEP * placed, 0.0)
        except Exception:  # noqa: BLE001
            pass
        md.EditRebuild3()
        md.ClearSelection2(True)
        if int(iv.GetDimensionCount4()) > before:
            placed += 1
            added.append({"type": "diameter", "value_mm": round(radius * 2000.0, 2),
                          "call": "AddDiameterDimension2"})
    return added


def main():
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = False
    # A filtered run must not erase the counts of the sheets it did not touch, so
    # the previous report is loaded and updated rather than replaced.
    report_path = os.path.join(CALC, "dimensions_report.json")
    report = {}
    if os.path.isfile(report_path):
        with open(report_path, encoding="utf-8") as fh:
            report = json.load(fh)
    # --recount opens each sheet read-only and records its dimension count without
    # adding anything, so the totals can be measured without stacking duplicates.
    recount_only = "--recount" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sheets = sorted(f for f in os.listdir(OUT)
                    if f.upper().endswith(".SLDDRW") and not f.startswith("~$"))
    # Optional name filters: `add_drawing_dimensions.py FD_Downrod` re-dimensions
    # only the sheets whose name matches, so a single rebuild does not stack a
    # second set of dimensions on the sheets that are already done.
    only = [a.lower() for a in args]
    if only:
        sheets = [s for s in sheets if any(o in s.lower() for o in only)]
    for name in sheets:
        path = os.path.join(OUT, name)
        entry = {"before": 0, "after": 0, "views": []}
        try:
            r = sw.OpenDoc6(path, int(swDocumentTypes_e.swDocDRAWING),
                            int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
            doc = r[0] if isinstance(r, tuple) else r
            if doc is None:
                raise RuntimeError("cannot open drawing")
            md = IModelDoc2(doc)
            draw = IDrawingDoc(doc)
            views = views_of(draw)
            entry["before"] = sum(int(v.GetDimensionCount4()) for v in views)
            if recount_only:
                entry["after"] = entry["before"]
                entry["recounted"] = True
                report[name] = entry
                sw.CloseDoc(os.path.basename(path))
                print("%-42s (recount) %2d" % (name, entry["after"]), flush=True)
                continue
            for iv in views[1:]:
                # A sheet already carrying a diameter from the first pass only
                # needs the missing linear dimensions added.
                added = dimension_view(md, iv, want_diameter=(entry["before"] == 0))
                entry["views"].append({"view": str(iv.GetName2()),
                                       "dimensions": added})
            entry["after"] = sum(int(v.GetDimensionCount4()) for v in views)
            md.EditRebuild3()
            saved = md.Extension.SaveAs(path, 0, 1, None, 0, 0)
            entry["saved"] = bool(saved[0] if isinstance(saved, tuple) else saved)
            entry["bytes"] = os.path.getsize(path)
            sw.CloseDoc(os.path.basename(path))
        except Exception as exc:  # noqa: BLE001
            entry["error"] = repr(exc)
        report[name] = entry
        print("%-42s %2d -> %2d  %s" % (name, entry["before"], entry["after"],
                                        entry.get("error", "")), flush=True)

    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    # --- visual evidence: one part sheet and one assembly sheet as PNG ----
    pngs = {}
    for target in ("FD_Blade_DRAWING.SLDDRW", "FD_SMART_FAN_ASSEMBLY_DRAWING.SLDDRW"):
        src = os.path.join(OUT, target)
        if not os.path.isfile(src):
            continue
        try:
            r = sw.OpenDoc6(src, int(swDocumentTypes_e.swDocDRAWING),
                            int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
            doc = r[0] if isinstance(r, tuple) else r
            md = IModelDoc2(doc)
            md.ViewZoomtofit2()
            png = os.path.join(REP, os.path.splitext(target)[0] + ".png")
            md.Extension.SaveAs(png, 0, 1, None, 0, 0)
            pngs[target] = {"path": os.path.basename(png),
                            "bytes": os.path.getsize(png) if os.path.isfile(png) else 0}
            sw.CloseDoc(os.path.basename(src))
        except Exception as exc:  # noqa: BLE001
            pngs[target] = {"error": repr(exc)}
    report["_png"] = pngs
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    import swutil
    swutil.shutdown(sw)
    total = sum(e.get("after", 0) for k, e in report.items() if not k.startswith("_"))
    print("sheets=%d dimensions=%d (documents closed)" % (len(sheets), total), flush=True)


if __name__ == "__main__":
    main()
