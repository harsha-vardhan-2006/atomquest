#!/usr/bin/env python3
"""Build the AtomQuest final-design native SOLIDWORKS parts.

Every part is modelled in the GLOBAL assembly frame (origin on the rotor axis,
+Z toward the ceiling) so components insert at (0,0,0) and ray/face selection
coordinates are predictable.

Sketch-plane axis mapping is measured at run time by calibrating each base
plane, so no hard-coded guess about the Right/Top plane orientation can corrupt
the geometry. Units: millimetres in this file, metres to the API.

Each document is saved, reopened, rebuilt, measured and closed before the next
one starts; SOLIDWORKS exits when the run finishes.
"""
import csv
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
    ISldWorks, IModelDoc2, IPartDoc, IFeature, IBody2,
)
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "FINAL_DESIGN")
PARTS_DIR = os.path.join(FD, "01_NATIVE_PARTS")
STEP_DIR = os.path.join(FD, "02_STEP_EXPORTS")
STL_DIR = os.path.join(FD, "03_PRINT_STL")
CALC_DIR = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
TPL_PART = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Part.PRTDOT"

FRONT, RIGHT, TOP = "Front Plane", "Right Plane", "Top Plane"

# Reference-plane offsets cannot be negative through this COM route (a negative
# InsertRefPlane distance silently returns a plane coincident with the base
# plane), so the whole design is modelled in a frame shifted into the positive
# octant. The rotor axis therefore sits at (SHIFT[0], SHIFT[1]) in part space;
# every part is inserted at the assembly origin, so the assembly frame carries
# the same offset. Geometry, masses and clearances are unaffected by the shift.
SHIFT = {0: 300.0, 1: 300.0, 2: 0.0}

DENSITY = {
    "printed_body": 1270.0,
    "printed_blade": 1350.0,
    "aluminium": 2700.0,
    "steel": 8000.0,
}

BLADE_STATIONS = [(260, 160, 26.0, 0.14), (330, 152, 22.0, 0.13),
                  (420, 142, 18.0, 0.12), (510, 133, 15.0, 0.11),
                  (610, 125, 13.0, 0.10), (700, 120, 12.0, 0.09)]
BLADE_ROOT_Z = 36.0


def mm(v):
    return v / 1000.0


class Builder:
    def __init__(self, sw):
        self.sw = sw
        self.calib = {}

    def _sel(self, md, name, typ="PLANE"):
        md.ClearSelection2(True)
        return bool(md.Extension.SelectByID2(name, typ, 0.0, 0.0, 0.0, False, 0, None, 0))

    def calibrate(self):
        """Measure sketch-axis signs and extrusion direction for each base plane."""
        out = {}
        for plane in (FRONT, RIGHT, TOP):
            md = IModelDoc2(self.sw.NewDocument(TPL_PART, 0, 0.0, 0.0))
            try:
                self._sel(md, plane)
                md.SketchManager.InsertSketch(True)
                md.SketchManager.CreateCircle(0.030, 0.0, 0.0, 0.040, 0.0, 0.0)
                md.SketchManager.CreateCircle(0.030, 0.040, 0.0, 0.040, 0.040, 0.0)
                md.SketchManager.InsertSketch(True)
                IPartDoc(md).FeatureExtrusion3(True, False, False, 0, 0, 0.006, 0.0,
                                               False, False, False, False, 0.0, 0.0,
                                               False, False, False, False, True)
                md.EditRebuild3()
                box = [float(v) for v in IPartDoc(md).GetPartBox(True)]
                lo, hi = box[:3], box[3:]
                ext = [hi[i] - lo[i] for i in range(3)]
                i_ext = min(range(3), key=lambda i: ext[i])
                others = [i for i in range(3) if i != i_ext]
                i_v = max(others, key=lambda i: ext[i])
                i_u = min(others, key=lambda i: ext[i])
                out[plane] = {
                    "u": i_u, "su": 1.0 if lo[i_u] > 0 else -1.0,
                    "v": i_v, "sv": 1.0 if lo[i_v] > -0.02 else -1.0,
                    "e": i_ext, "se": 1.0 if hi[i_ext] > 0 else -1.0,
                    "ext": [round(x, 4) for x in ext],
                }
            finally:
                self.sw.CloseDoc(md.GetTitle())
        self.calib = out
        return out

    def offset_plane(self, md, base, dist_mm):
        if not self._sel(md, base):
            raise RuntimeError("cannot select base plane %s" % base)
        f = md.FeatureManager.InsertRefPlane(8, mm(dist_mm), 0, 0.0, 0, 0.0)
        if f is None:
            raise RuntimeError("InsertRefPlane failed for %s @ %s mm" % (base, dist_mm))
        return IFeature(f).Name

    def _sk_uv(self, plane, a, b):
        c = self.calib[plane]
        return (c["su"] * mm(a + SHIFT[c["u"]]),
                c["sv"] * mm(b + SHIFT[c["v"]]))

    def _extrude(self, md, plane, depth_mm, extra_flip=False):
        flip = (self.calib[plane]["se"] < 0) != extra_flip
        IPartDoc(md).FeatureExtrusion3(True, flip, False, 0, 0, mm(abs(depth_mm)), 0.0,
                                       False, False, False, False, 0.0, 0.0,
                                       False, False, False, False, True)
        md.EditRebuild3()

    def _start_plane(self, md, plane, start_mm):
        e = self.calib[plane]["e"]
        d = (0.0 if start_mm is None else start_mm) + SHIFT[e]
        if abs(d) < 1e-9:
            return plane
        return self.offset_plane(md, plane, self.calib[plane]["se"] * d)

    def cyl(self, md, plane, a, b, r_mm, depth_mm, start_mm=None, flip=False):
        target = self._start_plane(md, plane, start_mm)
        if not self._sel(md, target):
            raise RuntimeError("cannot select %s" % target)
        md.SketchManager.InsertSketch(True)
        u, v = self._sk_uv(plane, a, b)
        md.SketchManager.CreateCircle(u, v, 0.0, u + mm(r_mm), v, 0.0)
        md.SketchManager.InsertSketch(True)
        self._extrude(md, plane, depth_mm, flip)

    def rect(self, md, plane, a0, b0, a1, b1, depth_mm, start_mm=None):
        target = self._start_plane(md, plane, start_mm)
        if not self._sel(md, target):
            raise RuntimeError("cannot select %s" % target)
        md.SketchManager.InsertSketch(True)
        u0, v0 = self._sk_uv(plane, a0, b0)
        u1, v1 = self._sk_uv(plane, a1, b1)
        md.SketchManager.CreateCornerRectangle(u0, v0, 0.0, u1, v1, 0.0)
        md.SketchManager.InsertSketch(True)
        self._extrude(md, plane, depth_mm)

    def poly(self, md, plane, pts, depth_mm, start_mm=None):
        target = self._start_plane(md, plane, start_mm)
        if not self._sel(md, target):
            raise RuntimeError("cannot select %s" % target)
        md.SketchManager.InsertSketch(True)
        uv = [self._sk_uv(plane, a, b) for a, b in pts]
        for i in range(len(uv)):
            (u1, v1), (u2, v2) = uv[i], uv[(i + 1) % len(uv)]
            md.SketchManager.CreateLine(u1, v1, 0.0, u2, v2, 0.0)
        md.SketchManager.InsertSketch(True)
        self._extrude(md, plane, depth_mm)

    def cut(self, md, plane, a, b, r_mm, hit=None):
        """Blind circular cut starting on a real face found by ray.

        A through-all cut sketched on a base plane that does not intersect the
        body silently removes nothing (observed in this build), so the face is
        selected first and the cut is applied from that face inwards.
        """
        bodies = IPartDoc(md).GetBodies2(0, True)
        if not bodies:
            raise RuntimeError("cut before any body exists")
        box = [float(v) for v in IBody2(bodies[0]).GetBodyBox()]
        c = self.calib[plane]
        e, se, au, av = c["e"], c["se"], c["u"], c["v"]
        ha, hb = hit if hit else (a, b)
        o = [0.0, 0.0, 0.0]
        o[e] = box[3 + e] + 0.05 if se > 0 else box[e] - 0.05
        o[au] = mm(ha + SHIFT[au])
        o[av] = mm(hb + SHIFT[av])
        d = [0.0, 0.0, 0.0]
        d[e] = -se
        md.ClearSelection2(True)
        if not md.Extension.SelectByRay(o[0], o[1], o[2], d[0], d[1], d[2],
                                        0.001, 2, False, 0, 0):
            raise RuntimeError("cut ray missed %s at (%.1f, %.1f)" % (plane, ha, hb))
        md.SketchManager.InsertSketch(True)
        u, v = self._sk_uv(plane, a, b)
        md.SketchManager.CreateCircle(u, v, 0.0, u + mm(r_mm), v, 0.0)
        md.SketchManager.InsertSketch(True)
        depth = mm((box[3 + e] - box[e]) * 1000 + 20)
        md.FeatureCut5(True, False, False, 0, 0, depth, 0.0,
                       False, False, False, False, 0.0, 0.0,
                       False, False, False, False, 0, False)
        md.EditRebuild3()

    def loft(self, md, names):
        if not self._sel(md, names[0], "SKETCH"):
            raise RuntimeError("cannot select %s" % names[0])
        for n in names[1:]:
            if not md.Extension.SelectByID2(n, "SKETCH", 0.0, 0.0, 0.0, True, 0, None, 0):
                raise RuntimeError("cannot append section %s" % n)
        f = md.FeatureManager.InsertProtrusionBlend2(
            False, True, False, 0.01, 0, 0, 0.0, 0.0, False, False,
            False, 0.0, 0.0, 0, True, True, True, 0)
        if f is None:
            raise RuntimeError("loft failed")
        md.EditRebuild3()


def naca_section(chord_mm, thick_pct, twist_deg, n=4):
    """Closed section in (chord, thickness) mm, twisted about the span axis.

    Provisional symmetric NACA-4 style thickness distribution with n points per
    surface (9-point closed section). Denser sections were tested and fail to
    loft through this API route, so the section is faceted; aerodynamic
    performance of this section has NOT been validated.
    """
    pts = []
    for i in range(n + 1):
        s = 0.5 * (1.0 - math.cos(math.pi * i / n))
        yt = (thick_pct * chord_mm / 0.2) * (
            0.2969 * math.sqrt(max(s, 1e-9)) - 0.1260 * s - 0.3516 * s ** 2
            + 0.2843 * s ** 3 - 0.1015 * s ** 4)
        pts.append((s * chord_mm, yt))
    for i in range(n - 1, 0, -1):
        s = 0.5 * (1.0 - math.cos(math.pi * i / n))
        yt = (thick_pct * chord_mm / 0.2) * (
            0.2969 * math.sqrt(max(s, 1e-9)) - 0.1260 * s - 0.3516 * s ** 2
            + 0.2843 * s ** 3 - 0.1015 * s ** 4)
        pts.append((s * chord_mm, -yt))
    dedup = []
    for pt in pts:
        if not dedup or abs(pt[0] - dedup[-1][0]) > 1e-6 or abs(pt[1] - dedup[-1][1]) > 1e-6:
            dedup.append(pt)
    if len(dedup) > 1 and abs(dedup[0][0] - dedup[-1][0]) < 1e-6 \
            and abs(dedup[0][1] - dedup[-1][1]) < 1e-6:
        dedup.pop()
    ang = math.radians(twist_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for xc, yt in dedup:
        c = xc - 0.40 * chord_mm  # quarter-chord at 40 % for this preliminary layout
        out.append((c * ca - yt * sa, c * sa + yt * ca))
    return out


def build_parts(B):
    P = []

    def part(fn, mat, fn_build, printable, note, post=None):
        P.append({"file": fn, "material": mat, "build": fn_build,
                  "printable": printable, "note": note, "post": post})

    def ceiling(md):
        B.cyl(md, FRONT, 0, 0, 115, 8, start_mm=462)
        for a, b in ((85, 0), (-85, 0), (0, 85), (0, -85)):
            B.cut(md, FRONT, a, b, 4.25)
        B.cut(md, FRONT, 0, 0, 13.5)
    part("FD_CeilingPlate.SLDPRT", "aluminium", ceiling, False,
         "ceiling interface plate; 4 x 8.5 mm anchors on 170 PCD (provisional)")

    def downrod(md):
        B.cyl(md, FRONT, 0, 0, 12.5, 232, start_mm=230)
        B.cut(md, FRONT, 0, 0, 9.5)
    part("FD_Downrod.SLDPRT", "aluminium", downrod, False, "25 x 19 tube, 232 mm")

    def yoke(md):
        B.cyl(md, FRONT, 0, 0, 75, 40, start_mm=190)
        B.rect(md, FRONT, -241, -58, 241, 58, 16, start_mm=182)
        for x0 in (225, -241):
            B.rect(md, RIGHT, 40, -58, 187, 58, 16, start_mm=x0)

    def yoke_bores(md):
        B.cut(md, RIGHT, 157, 0, 8)
    part("FD_SupportYoke.SLDPRT", "aluminium", yoke, False,
         "stationary yoke: downrod boss, web, two arm plates with X pivot bores",
         yoke_bores)

    def ring(md):
        B.cyl(md, FRONT, 0, 0, 210, 34, start_mm=140)
        B.cut(md, FRONT, 0, 0, 190, hit=(200, 0))
        B.cyl(md, RIGHT, 157, 0, 7.9, 482, start_mm=-241)

    def ring_bores(md):
        B.cut(md, TOP, 0, 157, 6, hit=(0, 157))
    part("FD_OuterTiltRing.SLDPRT", "aluminium", ring, False,
         "outer tilt ring: X trunnions and Y pivot bores", ring_bores)

    def cradle(md):
        B.rect(md, FRONT, -95, -85, 95, 85, 10, start_mm=123)
        for y0 in (85, -97):
            B.rect(md, TOP, -95, 123, 95, 182, 12, start_mm=y0)
        for y0 in (85, -190):
            B.cyl(md, TOP, 0, 157, 5.9, 105, start_mm=y0)
    part("FD_InnerCradle.SLDPRT", "aluminium", cradle, False,
         "inner cradle: platform, two fins, Y pivot pins")

    def adapter(md):
        B.cyl(md, FRONT, 0, 0, 75, 10, start_mm=113)
        B.cut(md, FRONT, 0, 0, 16)
        for a, b in ((45, 0), (-45, 0), (0, 45), (0, -45)):
            B.cut(md, FRONT, a, b, 2.25)
    part("FD_MotorAdapter.SLDPRT", "aluminium", adapter, False,
         "adapter plate; PLACEHOLDER 4 x 4.5 mm on 90 PCD must be measured")

    def cover(md):
        B.cyl(md, FRONT, 0, 0, 90, 83, start_mm=30)
        B.cut(md, FRONT, 0, 0, 84, hit=(87, 0))
        for i in range(8):
            ang = 2 * math.pi * i / 8
            B.cut(md, FRONT, 87 * math.cos(ang), 87 * math.sin(ang), 3)
    part("FD_MotorCover.SLDPRT", "printed_body", cover, True,
         "ventilated motor cover over the retained original motor")

    def shroud(md):
        B.cyl(md, FRONT, 0, 0, 250, 40, start_mm=174)
        B.cut(md, FRONT, 0, 0, 246, hit=(248, 0))
        B.cyl(md, FRONT, 0, 0, 250, 5, start_mm=214)
    part("FD_TopShroud.SLDPRT", "printed_body", shroud, True,
         "stationary shroud enclosing the tilt mechanism")

    def brx(md):
        B.rect(md, RIGHT, 130, -30, 180, 30, 12, start_mm=213)
        B.cut(md, RIGHT, 157, 0, 11)
    part("FD_ServoBracketX.SLDPRT", "printed_body", brx, True,
         "X-axis servo mount on the +X yoke arm")

    def bry(md):
        B.rect(md, TOP, -25, 130, 25, 180, 14, start_mm=178)
        B.cut(md, TOP, 0, 157, 11)
    part("FD_ServoBracketY.SLDPRT", "printed_body", bry, True,
         "Y-axis servo mount carried on the outer ring")

    def horn(md):
        B.cyl(md, FRONT, 0, 0, 10, 4, start_mm=-2)
        B.cut(md, FRONT, 0, 0, 3)
        B.rect(md, FRONT, -4, 0, 4, 26, 4, start_mm=-2)
    part("FD_ServoHorn.SLDPRT", "aluminium", horn, False,
         "generic servo horn; no servo model selected yet")

    def hub(md):
        B.cyl(md, FRONT, 0, 0, 85, 12)
        B.cut(md, FRONT, 0, 0, 75.2, hit=(80, 0))
        for i in range(3):
            ang = math.radians(120 * i)
            ca, sa = math.cos(ang), math.sin(ang)
            poly = [(x * ca - y * sa, x * sa + y * ca)
                    for x, y in ((60, -45), (210, -45), (210, 45), (60, 45))]
            B.poly(md, FRONT, poly, 16, start_mm=8)
            for py in (-32, 32):
                B.cut(md, FRONT, 180 * ca - py * sa, 180 * sa + py * ca, 3)
    part("FD_BladeHub.SLDPRT", "aluminium", hub, False,
         "clamp hub over the ORIGINAL rotor flange with 3 blade pads")

    def blade(md):
        names = []
        for idx, (x, chord, twist, th) in enumerate(BLADE_STATIONS):
            pts = naca_section(chord, th, twist)
            zmin = min(z for _, z in pts)
            pts = [(y, z - zmin + BLADE_ROOT_Z) for y, z in pts]
            plane = B._start_plane(md, RIGHT, x)
            B._sel(md, plane)
            md.SketchManager.InsertSketch(True)
            uv = [B._sk_uv(RIGHT, z, y) for y, z in pts]
            for i in range(len(uv)):
                (u1, v1), (u2, v2) = uv[i], uv[(i + 1) % len(uv)]
                md.SketchManager.CreateLine(u1, v1, 0.0, u2, v2, 0.0)
            md.SketchManager.InsertSketch(True)
            names.append("Sketch%d" % (idx + 1))
        B.loft(md, names)
        B.rect(md, FRONT, 145, -85, 265, 85, 16, start_mm=24)
        for b in (-32, 32):
            B.cut(md, FRONT, 180, b, 3)
    part("FD_Blade.SLDPRT", "printed_blade", blade, True,
         "lofted twisted blade with flat-bottom root; aerodynamics NOT validated")

    def bushx(md):
        B.cyl(md, RIGHT, 157, 0, 8, 20, start_mm=221)
        B.cut(md, RIGHT, 157, 0, 6)
    part("FD_PivotBushingX.SLDPRT", "steel", bushx, False,
         "outer tilt bushing; provisional, replace with a rated bearing")

    def bushy(md):
        B.cyl(md, TOP, 0, 157, 6, 20, start_mm=170)
        B.cut(md, TOP, 0, 157, 4.1)
    part("FD_PivotBushingY.SLDPRT", "steel", bushy, False,
         "inner tilt bushing; provisional")

    def stop(md):
        B.rect(md, TOP, -120, 148, 120, 156, 8, start_mm=190)
    part("FD_TravelStop.SLDPRT", "printed_body", stop, True,
         "outer-axis hard stop bar; final angle set after motion verification")

    def clamp(md):
        B.rect(md, FRONT, -32, -32, 32, 32, 8, start_mm=300)
        for a, b in ((0, 0), (0, 14), (0, -14)):
            B.cut(md, FRONT, a, b, 3)
    part("FD_CableCollar.SLDPRT", "printed_body", clamp, True,
         "downrod cable strain-relief collar")

    def motor(md):
        B.cyl(md, FRONT, 0, 0, 62.5, 58, start_mm=55)
        B.cyl(md, FRONT, 0, 0, 6, 113)
        B.cyl(md, FRONT, 0, 0, 75, 10)
        for a, b in ((45, 0), (-45, 0), (0, 45), (0, -45)):
            B.cut(md, FRONT, a, b, 2.25)
    part("FD_REF_MotorEnvelope.SLDPRT", "aluminium", motor, False,
         "REFERENCE ONLY placeholder for the retained original motor")

    return P


def main():
    for d in (PARTS_DIR, STEP_DIR, STL_DIR, CALC_DIR):
        if not os.path.isdir(d):
            os.makedirs(d)
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = True
    records = []
    failures = []
    try:
        B = Builder(sw)
        calib = B.calibrate()
        print("plane calibration:", json.dumps(calib), flush=True)
        with open(os.path.join(CALC_DIR, "plane_calibration.json"), "w", encoding="utf-8") as fh:
            json.dump(calib, fh, indent=2)
        for spec in build_parts(B):
            fn = spec["file"]
            path = os.path.join(PARTS_DIR, fn)
            try:
                md = IModelDoc2(sw.NewDocument(TPL_PART, 0, 0.0, 0.0))
                try:
                    spec["build"](md)
                    if spec.get("post"):
                        spec["post"](md)
                    md.EditRebuild3()
                    saved = md.Extension.SaveAs(path, 0, 1, None, 0, 0)
                    if not saved[0] or not os.path.isfile(path):
                        raise RuntimeError("save failed")
                finally:
                    sw.CloseDoc(os.path.basename(path))

                opened = sw.OpenDoc6(path, int(swDocumentTypes_e.swDocPART),
                                     int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
                doc = IModelDoc2(opened[0] if isinstance(opened, tuple) else opened)
                try:
                    ok = doc.EditRebuild3()
                    part = IPartDoc(doc)
                    bodies = part.GetBodies2(0, True)
                    body_list = [] if bodies is None else [IBody2(b) for b in bodies]
                    n_solid = len(body_list)
                    surf = part.GetBodies2(1, True)
                    n_surf = 0 if surf is None else len(surf)
                    boxes = [[float(v) for v in b.GetBodyBox()] for b in body_list]
                    if n_solid != 1:
                        raise RuntimeError("expected 1 solid body, got %d at %s" % (
                            n_solid,
                            [[round(v * 1000, 1) for v in bx] for bx in boxes]))
                    box = boxes[0]
                    ext = [(box[i + 3] - box[i]) * 1000 for i in range(3)]
                    props = [float(v) for v in body_list[0].GetMassProperties(1000.0)]
                    vol = props[5] / 1000.0
                    feats = []
                    f = doc.FirstFeature()
                    while f is not None:
                        ft = IFeature(f)
                        feats.append(ft.GetTypeName2())
                        f = ft.GetNextFeature()
                    step = os.path.join(STEP_DIR, fn.replace(".SLDPRT", ".STEP"))
                    doc.Extension.SaveAs(step, 0, 1, None, 0, 0)
                    stl = None
                    if spec["printable"]:
                        stl = os.path.join(STL_DIR, fn.replace(".SLDPRT", ".STL"))
                        doc.Extension.SaveAs(stl, 0, 1, None, 0, 0)
                    dens = DENSITY[spec["material"]]
                    records.append({
                        "part": fn, "material": spec["material"],
                        "density_kg_m3": dens,
                        "solid_bodies": n_solid, "surface_bodies": n_surf,
                        "bbox_x_mm": round(ext[0], 2), "bbox_y_mm": round(ext[1], 2),
                        "bbox_z_mm": round(ext[2], 2),
                        "z_min_mm": round(box[2] * 1000, 2),
                        "z_max_mm": round(box[5] * 1000, 2),
                        "volume_cm3": round(vol * 1e6, 2),
                        "mass_kg": round(vol * dens, 4),
                        "features": len(feats),
                        "feature_types": "|".join(sorted(set(feats))),
                        "rebuild": "PASS" if ok else "FAIL",
                        "step_bytes": os.path.getsize(step) if os.path.isfile(step) else 0,
                        "stl_bytes": os.path.getsize(stl) if stl and os.path.isfile(stl) else "",
                        "printable": "yes" if spec["printable"] else "no",
                        "note": spec["note"],
                    })
                    print("PASS %-26s vol=%7.1fcm3 m=%6.3fkg x=%7.1f..%6.1f y=%7.1f..%6.1f z=%6.1f..%6.1f"
                          % (fn, vol * 1e6, vol * dens, box[0] * 1000, box[3] * 1000,
                             box[1] * 1000, box[4] * 1000, box[2] * 1000, box[5] * 1000),
                          flush=True)
                finally:
                    sw.CloseDoc(os.path.basename(path))
            except Exception as exc:  # noqa: BLE001 - recorded, run continues
                failures.append({"part": fn, "error": str(exc)})
                print("FAIL %-28s %s" % (fn, exc), flush=True)
            finally:
                with open(os.path.join(CALC_DIR, "part_measurements.csv"), "w",
                          newline="", encoding="utf-8") as fh:
                    if records:
                        w = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
                        w.writeheader()
                        w.writerows(records)
    finally:
        sw.ExitApp()
        print("SOLIDWORKS closed after part build", flush=True)
    with open(os.path.join(CALC_DIR, "part_build_failures.json"), "w", encoding="utf-8") as fh:
        json.dump(failures, fh, indent=2)
    print("parts built: %d, failures: %d" % (len(records), len(failures)), flush=True)


if __name__ == "__main__":
    main()
