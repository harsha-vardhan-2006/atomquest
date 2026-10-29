#!/usr/bin/env python3
"""Build the round-2 preliminary component parts through typed SOLIDWORKS interop.

Each part is saved, reopened, rebuilt, measured for solid bodies/bounds, and
closed before starting the next document. Geometry dimensions are mm from the
source audit/legacy part intent and are converted to API metres. Parts are
preliminary; no materials or load ratings are assigned.
"""
import csv
import os
import sys
import time

RED = r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist"
sys.path.insert(0, RED)
import clr
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.sldworks.dll"))
clr.AddReference(os.path.join(RED, "SolidWorks.Interop.swconst.dll"))

from System import Activator, Type
from SolidWorks.Interop.sldworks import ISldWorks, IModelDoc2, IPartDoc, IFeature, IBody2
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Part.PRTDOT"
OUT_CSV = os.path.join(R2, "00_REQUIREMENTS_AND_SOURCE_AUDIT", "rebuilt_parts_audit.csv")

# name, dimensions in mm, profile kind. These are concept parts, not released parts.
PARTS = [
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_CeilingPlate.SLDPRT", "plate", (300, 300, 15), 2700),
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_SupportHousing.SLDPRT", "plate", (250, 250, 80), 2700),
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_OuterRing.SLDPRT", "ring", (600, 500, 80), 2700),
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_InnerRing.SLDPRT", "ring", (480, 400, 60), 2700),
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_FanCarrier.SLDPRT", "plate", (450, 450, 10), 2700),
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_MotorInterface.SLDPRT", "disc", (200, 160, 50), 2700),
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_HubCone.SLDPRT", "plate", (160, 160, 80), 2700),
    ("MODEL_1_DUAL_RING_GIMBAL", "M1_ServoMount.SLDPRT", "plate", (100, 60, 20), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_CeilingPlate.SLDPRT", "plate", (250, 250, 12), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_SupportUpper.SLDPRT", "plate", (220, 220, 60), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_InnerGimbalRing.SLDPRT", "ring", (380, 320, 50), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_XPivotHub.SLDPRT", "disc", (120, 20, 30), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_YPivotHub.SLDPRT", "disc", (100, 20, 25), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_FanCarrier.SLDPRT", "plate", (400, 400, 8), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_MotorInterface.SLDPRT", "disc", (160, 120, 40), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_HubCone.SLDPRT", "plate", (140, 140, 70), 2700),
    ("MODEL_2_SPHERICAL_GIMBAL", "M2_SphericalHousing.SLDPRT", "shell", (600, 580, 600), 1200),
]


def mm(v):
    return v / 1000.0


def feature_names(doc):
    names = []
    f = doc.FirstFeature()
    while f is not None:
        feat = IFeature(f)
        names.append((feat.Name, feat.GetTypeName2()))
        f = feat.GetNextFeature()
    return names


def clear_selection(doc):
    doc.ClearSelection2(True)


def sketch(doc, plane="Front Plane"):
    if not doc.Extension.SelectByID2(plane, "PLANE", 0.0, 0.0, 0.0, False, 0, None, 0):
        raise RuntimeError("Unable to select %s" % plane)
    doc.SketchManager.InsertSketch(True)
    return doc.SketchManager


def extrude(part, depth):
    # FeatureExtrusion3: 18 arguments; do not treat its void return as failure.
    part.FeatureExtrusion3(True, False, False, 0, 0, mm(depth), 0.0,
                           False, False, False, False, 0.0, 0.0,
                           False, False, False, False, True)


def make_geometry(doc, part, kind, dims):
    sm = sketch(doc)
    if kind == "plate":
        x, y, _z = map(mm, dims)
        sm.CreateCornerRectangle(0.0, 0.0, 0.0, x, y, 0.0)
        doc.SketchManager.InsertSketch(True)
        extrude(part, dims[2])
        if "CeilingPlate" in doc.GetTitle():
            # Preliminary 4-point mounting pattern, Ø8 mm, 50 mm edge inset.
            if not doc.Extension.SelectByRay(x / 2, y / 2, mm(dims[2]), 0.0, 0.0, -1.0,
                                             0.001, 2, False, 0, 0):
                raise RuntimeError("cannot select ceiling plate top face")
            sm = doc.SketchManager
            sm.InsertSketch(True)
            for hx, hy in ((mm(50), mm(50)), (x-mm(50), mm(50)),
                           (x-mm(50), y-mm(50)), (mm(50), y-mm(50))):
                sm.CreateCircle(hx, hy, mm(dims[2]), mm(4), hy, mm(dims[2]))
            sm.InsertSketch(True)
            doc.FeatureCut5(True, False, False, 1, 0, mm(dims[2] * 1.5), 0.0,
                            False, False, False, False, 0.0, 0.0,
                            False, False, False, False, 0, False)
    elif kind in ("ring", "shell"):
        od, id_, depth = dims
        sm.CreateCircle(0.0, 0.0, 0.0, mm(od / 2), 0.0, 0.0)
        doc.SketchManager.InsertSketch(True)
        extrude(part, depth)
        # Pick the outermost annulus so the top face is unambiguous.
        if not doc.Extension.SelectByRay(mm(od * 0.49), 0.0, mm(depth), 0.0, 0.0, -1.0,
                                         0.001, 2, False, 0, 0):
            raise RuntimeError("cannot select ring top face for bore")
        sm = doc.SketchManager
        sm.InsertSketch(True)
        sm.CreateCircle(0.0, 0.0, mm(depth), mm(id_ / 2), 0.0, mm(depth))
        sm.InsertSketch(True)
        doc.FeatureCut5(True, False, False, 1, 0, mm(depth * 1.5), 0.0,
                        False, False, False, False, 0.0, 0.0,
                        False, False, False, False, 0, False)
    elif kind == "disc":
        od, bore, depth = dims
        sm.CreateCircle(0.0, 0.0, 0.0, mm(od / 2), 0.0, 0.0)
        doc.SketchManager.InsertSketch(True)
        extrude(part, depth)
        if bore:
            if not doc.Extension.SelectByRay(mm(od * 0.49), 0.0, mm(depth), 0.0, 0.0, -1.0,
                                             0.001, 2, False, 0, 0):
                raise RuntimeError("cannot select disc top face for bore")
            sm = doc.SketchManager
            sm.InsertSketch(True)
            sm.CreateCircle(mm(od * 0.49), 0.0, mm(depth), mm(bore / 2), 0.0, mm(depth))
            sm.InsertSketch(True)
            doc.FeatureCut5(True, False, False, 1, 0, mm(depth * 1.5), 0.0,
                            False, False, False, False, 0.0, 0.0,
                            False, False, False, False, 0, False)
    else:
        raise ValueError("Unknown profile kind: %s" % kind)
    doc.EditRebuild3()


def measure(doc, density):
    part = IPartDoc(doc)
    bodies = part.GetBodies2(0, True)
    count = 0 if bodies is None else len(bodies)
    if count < 1:
        raise RuntimeError("rebuild produced no solid bodies")
    box = [float(v) for v in part.GetPartBox(True)]
    extents = [box[i + 3] - box[i] for i in range(3)]
    if min(extents) <= 0:
        raise RuntimeError("non-positive extent %r" % extents)
    props = [float(v) for v in IBody2(bodies[0]).GetMassProperties(float(density))]
    # SOLIDWORKS IBody2.GetMassProperties(density) returns centroid xyz,
    # moments, then mass at index 5; derive volume from mass / density.
    volume_m3 = props[5] / density
    if volume_m3 <= 0:
        raise RuntimeError("non-positive mass-property volume %r" % volume_m3)
    return count, extents, volume_m3, props[:3]


def main():
    records = []
    for model, filename, kind, dims, density in PARTS:
        path = os.path.join(R2, model, "01_CAD_PARTS", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
        sw.Visible = True
        try:
            doc = IModelDoc2(sw.NewDocument(TEMPLATE, 0, 0.0, 0.0))
            try:
                make_geometry(doc, IPartDoc(doc), kind, dims)
                saved = doc.Extension.SaveAs(path, 0, 1, None, 0, 0)
                if not saved[0]:
                    raise RuntimeError("native save failed: %s" % path)
            finally:
                sw.CloseDoc(doc.GetTitle())

            opened = sw.OpenDoc6(path, int(swDocumentTypes_e.swDocPART),
                                 int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
            reopened = IModelDoc2(opened[0] if isinstance(opened, tuple) else opened)
            try:
                if not reopened.EditRebuild3():
                    raise RuntimeError("reopen rebuild failed: %s" % filename)
                bodies, ext, volume, centroid = measure(reopened, density)
                feats = feature_names(reopened)
                record = {
                    "file": os.path.relpath(path, R2).replace("\\", "/"),
                    "type": kind,
                    "nominal_dims_mm": "x".join(str(x) for x in dims),
                    "solid_bodies": bodies,
                    "bbox_x_mm": round(ext[0] * 1000, 3),
                    "bbox_y_mm": round(ext[1] * 1000, 3),
                    "bbox_z_mm": round(ext[2] * 1000, 3),
                    "volume_cm3": round(volume * 1e6, 4),
                    "mass_kg_at_density": round(volume * density, 5),
                    "centroid_x_m": round(centroid[0], 6),
                    "centroid_y_m": round(centroid[1], 6),
                    "centroid_z_m": round(centroid[2], 6),
                    "feature_types": " | ".join("%s(%s)" % x for x in feats if x[1] in
                                                  ("Extrusion", "Cut", "Revolution", "ProfileFeature")),
                    "validation": "PASS solid/nonzero bounds/nonzero volume; preliminary nominal geometry",
                }
                records.append(record)
                with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
                    writer.writeheader()
                    writer.writerows(records)
                print("PASS %s saved + reopened + measured; closing SOLIDWORKS before next part" % filename, flush=True)
            finally:
                sw.CloseDoc(path)
        finally:
            sw.ExitApp()
            print("Closed SOLIDWORKS for %s" % filename, flush=True)
    print("All done; verified parts=%d; no SOLIDWORKS document/app left open" % len(records), flush=True)


if __name__ == "__main__":
    main()
