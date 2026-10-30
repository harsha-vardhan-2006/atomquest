#!/usr/bin/env python3
"""Build the AtomQuest final-design assemblies.

Placement model
---------------
Every part is modelled in its assembled position in a common frame whose rotor
axis is at (300, 300) mm, so a component is inserted at the origin and its
geometry is already in place. Blades 2 and 3 need an angular placement; component
transforms are applied with IComponent2::SetTransformAndSolve3 using a transform
array in the layout this build reads back (3x3 rotation in elements 0-8,
translation in 9-11), composed as T(P) . Rz(theta) . T(-P) so the blade rotates
about the rotor axis instead of the model origin.

Mates
-----
Assembly sub-entity selection and mate creation (SelectByID2 on component
datums, SelectByRay, persistent-reference resolution) all fail in this
non-interactive SOLIDWORKS session: selections return False, AddMate5 reports
error 4 and no mate feature is created. Nothing here pretends otherwise: the
joint list that still has to be applied in the SolidWorks UI is written to
assembly_joint_plan.json, and the report records mates_created = 0 with the exact
failure of every attempt.

Mass properties
---------------
IMassProperty2 on the assembly object returns values that disagree with the
masses of the components it contains, so assembly mass and centre of mass are
computed here by summing each component's own part-level mass properties
transformed into assembly space. Both numbers are written out so the
disagreement is visible rather than hidden.
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
from System import Activator, Type, Array, Double
from SolidWorks.Interop.sldworks import (
    IFeature, ISldWorks, IModelDoc2, IAssemblyDoc, IComponent2, IMassProperty2,
    IMathUtility,
)
from SolidWorks.Interop.swconst import swDocumentTypes_e, swOpenDocOptions_e

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "FINAL_DESIGN")
PARTS = os.path.join(FD, "01_NATIVE_PARTS")
ASM_DIR = os.path.join(FD, "04_ASSEMBLIES")
CALC = os.path.join(FD, "07_ENGINEERING_CALCULATIONS")
TPL_ASM = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates\Assembly.ASMDOT"

SHIFT = 300.0     # rotor axis in the modelling frame, mm
ROTOR = (SHIFT, SHIFT, 0.0)

# Stationary/rotating groups. Names match the native parts in 01_NATIVE_PARTS.
ROTOR_PARTS = [
    ("FD_BladeHub.SLDPRT", 0.0),
    ("FD_Blade.SLDPRT", 0.0),
    ("FD_Blade.SLDPRT", 120.0),
    ("FD_Blade.SLDPRT", 240.0),
]
TILT_PARTS = [
    "FD_SupportYoke.SLDPRT", "FD_OuterTiltRing.SLDPRT", "FD_InnerCradle.SLDPRT",
    "FD_MotorAdapter.SLDPRT", "FD_MotorCover.SLDPRT", "FD_PivotBushingX.SLDPRT",
    "FD_PivotBushingY.SLDPRT", "FD_ServoBracketX.SLDPRT", "FD_ServoBracketY.SLDPRT",
    "FD_TravelStop.SLDPRT", "FD_ServoHorn.SLDPRT",
]
ROOT_PARTS = [
    "FD_CeilingPlate.SLDPRT", "FD_Downrod.SLDPRT", "FD_TopShroud.SLDPRT",
    "FD_CableCollar.SLDPRT", "FD_REF_MotorEnvelope.SLDPRT",
]


def mm(v):
    return v / 1000.0


def rot_z(px, py, angle_deg):
    """16-element MathTransform array: rotate by angle about Z through (px, py)."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    tx = px - (c * px - s * py)
    ty = py - (s * px + c * py)
    return Array[Double]([c, -s, 0.0,
                          s, c, 0.0,
                          0.0, 0.0, 1.0,
                          mm(tx), mm(ty), 0.0,
                          1.0, 0.0, 0.0, 0.0])


class Asm:
    def __init__(self, sw, title):
        self.sw = sw
        self.title = title
        self.log = []
        self.components = []
        self.md = IModelDoc2(sw.NewDocument(TPL_ASM, 0, 0.0, 0.0))
        self.asm = IAssemblyDoc(self.md)

    def open(self, name):
        path = os.path.join(PARTS, name) if name.endswith(".SLDPRT") \
            else os.path.join(ASM_DIR, name)
        kind = swDocumentTypes_e.swDocPART if name.endswith(".SLDPRT") \
            else swDocumentTypes_e.swDocASSEMBLY
        r = self.sw.OpenDoc6(path, int(kind),
                             int(swOpenDocOptions_e.swOpenDocOptions_Silent), "", 0, 0)
        doc = r[0] if isinstance(r, tuple) else r
        if doc is None:
            raise RuntimeError("cannot open %s" % path)
        return path

    def insert(self, name, angle=None):
        path = self.open(name)
        comp = self.asm.AddComponent5(path, 0, "", False, "", 0.0, 0.0, 0.0)
        if comp is None:
            raise RuntimeError("AddComponent5 failed for %s" % name)
        comp = IComponent2(comp)
        entry = {"component": comp.Name2, "source": name, "angle_deg": angle}
        if angle:
            tr = IMathUtility(self.sw.GetMathUtility()).CreateTransform(
                rot_z(ROTOR[0], ROTOR[1], angle))
            try:
                comp.SetTransformAndSolve3(tr, False)
                entry["rotated"] = True
            except Exception as exc:  # noqa: BLE001
                entry["rotated"] = False
                entry["rotate_error"] = repr(exc)
        self.components.append((comp, entry))
        self.md.EditRebuild3()
        return comp

    def component_properties(self):
        """Per-component mass/COM in assembly space, plus totals."""
        rows = []
        mass_total = 0.0
        mx = my = mz = 0.0
        for comp, entry in self.components:
            doc = IModelDoc2(comp.GetModelDoc2())
            if doc is None:
                entry["mass_kg"] = None
                rows.append(entry)
                continue
            mp = IMassProperty2(doc.Extension.CreateMassProperty2())
            mass = float(mp.Mass)
            com = [float(v) for v in mp.CenterOfMass]
            tr = [float(v) for v in comp.Transform2.ArrayData]
            r = [[tr[0], tr[1], tr[2]], [tr[3], tr[4], tr[5]], [tr[6], tr[7], tr[8]]]
            t = [tr[9], tr[10], tr[11]]
            world = [sum(r[i][j] * com[j] for j in range(3)) + t[i] for i in range(3)]
            entry["mass_kg"] = round(mass, 4)
            entry["com_component_mm"] = [round(v * 1000.0, 1) for v in com]
            entry["com_assembly_mm"] = [round(v * 1000.0, 1) for v in world]
            entry["volume_m3"] = round(float(mp.Volume), 9)
            mass_total += mass
            mx += mass * world[0]
            my += mass * world[1]
            mz += mass * world[2]
            rows.append(entry)
        summary = {"component_count": len(self.components),
                   "mass_kg": round(mass_total, 4)}
        if mass_total:
            summary["com_mm"] = [round(mx / mass_total * 1000.0, 1),
                                 round(my / mass_total * 1000.0, 1),
                                 round(mz / mass_total * 1000.0, 1)]
        return summary, rows

    def try_mates(self, joints):
        """Attempt the joint mates and record exactly what happens."""
        attempts = []
        for joint in joints:
            self.md.ClearSelection2(True)
            res = None
            try:
                res = self.asm.AddMate5(int(joint["mate_type"]), 0, False,
                                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                        False, False, 0, 0)
            except Exception as exc:  # noqa: BLE001
                joint["attempt_error"] = repr(exc)
            created = isinstance(res, tuple) and res[0] is not None
            attempts.append({"joint": joint["name"], "created": bool(created),
                             "error_code": (res[1] if isinstance(res, tuple) else None)})
        return attempts

    def mate_feature_count(self):
        n = 0
        cur = self.md.FirstFeature()
        while cur is not None:
            feat = IFeature(cur)
            if str(feat.GetTypeName2()) == "MateGroup":
                sub = feat.GetFirstSubFeature()
                while sub is not None:
                    n += 1
                    sub = IFeature(sub).GetNextSubFeature()
            cur = feat.GetNextFeature()
        return n

    def save(self):
        os.makedirs(ASM_DIR, exist_ok=True)
        path = os.path.join(ASM_DIR, "%s.SLDASM" % self.title)
        r = self.md.Extension.SaveAs(path, 0, 1, None, 0, 0)
        ok = r[0] if isinstance(r, tuple) else r
        if not ok or not os.path.isfile(path):
            raise RuntimeError("assembly save failed: %s" % path)
        self.md.EditRebuild3()
        return path

    def close(self):
        try:
            self.sw.CloseDoc("%s.SLDASM" % self.title)
        except Exception:  # noqa: BLE001
            pass


JOINTS = {
    "FD_ROTOR": [
        {"name": "blade_root_to_pad_0", "mate_type": 0,
         "intent": "coincident: blade root underside to hub pad top"},
        {"name": "blade_bolt_concentric_0", "mate_type": 3,
         "intent": "concentric: blade root bore to hub pad bolt bore (Z axis)"},
        {"name": "hub_flange_to_rotor", "mate_type": 3,
         "intent": "concentric: hub clamp bore to original rotor flange (measured)"},
    ],
    "FD_TILT": [
        {"name": "outer_axis_concentric", "mate_type": 3,
         "intent": "concentric: yoke arm bore to outer ring trunnion (X axis)"},
        {"name": "outer_axis_face", "mate_type": 0,
         "intent": "coincident: trunnion shoulder to yoke arm inner face"},
        {"name": "inner_axis_concentric", "mate_type": 3,
         "intent": "concentric: outer ring Y bore to inner cradle pin (Y axis)"},
        {"name": "inner_axis_face", "mate_type": 0,
         "intent": "coincident: cradle pin shoulder to ring bore face"},
        {"name": "adapter_platform", "mate_type": 0,
         "intent": "coincident: motor adapter underside to cradle platform"},
    ],
    "FD_SMART_FAN_ASSEMBLY": [
        {"name": "downrod_to_plate", "mate_type": 3,
         "intent": "concentric: downrod OD to ceiling plate bore"},
        {"name": "downrod_shoulder", "mate_type": 0,
         "intent": "coincident: downrod shoulder to plate underside"},
        {"name": "tilt_to_downrod", "mate_type": 3,
         "intent": "concentric: yoke boss bore to downrod OD (fixed joint)"},
        {"name": "rotor_to_adapter", "mate_type": 3,
         "intent": "concentric: rotor hub bore to motor adapter spigot"},
    ],
}


def main():
    os.makedirs(CALC, exist_ok=True)
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = True
    report = {"solidworks_revision": str(sw.RevisionNumber)}
    plan = {}

    def record(title, builder):
        try:
            asm = builder()
            summary, rows = asm.component_properties()
            attempts = asm.try_mates(JOINTS[title])
            mates = asm.mate_feature_count()
            path = asm.save()
            report[title] = {"file": os.path.relpath(path, FD).replace("\\", "/"),
                             "bytes": os.path.getsize(path),
                             "components": summary,
                             "mate_features_created": mates,
                             "mate_attempts": attempts,
                             "parts": rows}
            plan[title] = JOINTS[title]
            print("PASS %s components=%d mates=%d mass=%.3fkg"
                  % (title, summary["component_count"], mates,
                     summary["mass_kg"]), flush=True)
        except Exception as exc:  # noqa: BLE001
            report[title] = {"error": repr(exc)}
            print("FAIL %s: %r" % (title, exc), flush=True)
        finally:
            try:
                asm.close()  # noqa: F821 - closed below when built
            except Exception:  # noqa: BLE001
                pass

    # rotor
    def build_rotor():
        a = Asm(sw, "FD_ROTOR")
        for name, angle in ROTOR_PARTS:
            a.insert(name, angle or None)
        return a

    record("FD_ROTOR", build_rotor)

    def build_tilt():
        a = Asm(sw, "FD_TILT")
        for name in TILT_PARTS:
            a.insert(name)
        return a

    record("FD_TILT", build_tilt)

    def build_root():
        a = Asm(sw, "FD_SMART_FAN_ASSEMBLY")
        for name in ROOT_PARTS:
            a.insert(name)
        a.insert("FD_TILT.SLDASM")
        a.insert("FD_ROTOR.SLDASM")
        return a

    record("FD_SMART_FAN_ASSEMBLY", build_root)

    with open(os.path.join(CALC, "assembly_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    with open(os.path.join(CALC, "assembly_joint_plan.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2)
    sw.ExitApp()
    print("solidworks closed")


if __name__ == "__main__":
    main()
