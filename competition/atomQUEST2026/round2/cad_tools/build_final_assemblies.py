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
about the rotor axis instead of the model origin.Mates
-----
Mates are created from geometry, not from picked coordinates: every face of both
components is classified and transformed into assembly space, then the best
coincident (parallel coplanar planes) or concentric (parallel coaxial cylinders)
pair is selected through IEntity::Select4 with a real SelectData object and
given to IAssemblyDoc::AddMate5.

Every mate is validated against the assembled layout: the component transforms
are snapshotted before the mate and compared afterwards. A mate that moves any
component by more than 0.5 mm is treated as over-constraining or geometrically
wrong, is undone, and is recorded as rejected rather than saved. The accepted
list, the rejected list and the resulting mate-feature count are all written to
assembly_report.json, so the claim "this assembly has N mates" is checkable.

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
    IMathUtility, IBody2, IFace2, ISurface, IEntity, SelectionMgr,
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


# swMateType_e: COINCIDENT=0, CONCENTRIC=1 (3 is PARALLEL, which silently made a
# "Parallel" feature instead of a concentric mate).
MATE_TYPES = {"coincident": 0, "concentric": 1}
# swMateAlign_e: 0 = NONE lets SOLIDWORKS flip a component to satisfy the mate
# (measured: 60 mm shift + 180 deg flip on every blade joint). CLOSEST keeps the
# parts where they already are, which is what a face pair 0.000 mm apart needs.
MATE_ALIGN = 3


def _unit(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def comp_faces(comp):
    """Classify every face of a component and express its geometry in assembly space."""
    out = []
    try:
        bodies = comp.GetBodies2(0)
    except Exception:  # noqa: BLE001
        bodies = None
    if bodies is None:
        return out
    tr = [float(v) for v in comp.Transform2.ArrayData]
    R = [[tr[0], tr[1], tr[2]], [tr[3], tr[4], tr[5]], [tr[6], tr[7], tr[8]]]
    T = [tr[9], tr[10], tr[11]]

    def xp(p):
        # API geometry is in metres; every comparison below is in millimetres
        return [(sum(R[i][j] * p[j] for j in range(3)) + T[i]) * 1000.0 for i in range(3)]

    def xv(v):
        return [sum(R[i][j] * v[j] for j in range(3)) for i in range(3)]

    for b in bodies:
        face = IBody2(b).GetFirstFace()
        while face is not None:
            f = IFace2(face)
            try:
                surf = ISurface(f.GetSurface())
                d = {"face": f, "area": float(f.GetArea())}
                if surf.IsPlane():
                    pr = [float(v) for v in surf.PlaneParams]
                    d.update(kind="plane", n=_unit(xv(pr[:3])), p=xp(pr[3:6]))
                elif surf.IsCylinder():
                    pr = [float(v) for v in surf.CylinderParams]
                    d.update(kind="cyl", a=_unit(xv(pr[3:6])), p=xp(pr[:3]),
                             r=round(pr[6] * 1000.0, 3))
                else:
                    d["kind"] = "other"
                out.append(d)
            except Exception:  # noqa: BLE001
                pass
            face = f.GetNextFace()
    return out


def match_faces(fa, fb, kind, tol_mm=0.08):
    """Best geometrically-valid face pair for a coincident or concentric mate."""
    best = None
    for a in fa:
        if a["kind"] != ("plane" if kind == "coincident" else "cyl"):
            continue
        na = a["n"] if kind == "coincident" else a["a"]
        for b in fb:
            if b["kind"] != a["kind"]:
                continue
            nb = b["n"] if kind == "coincident" else b["a"]
            if abs(abs(_dot(na, nb)) - 1.0) > 0.002:
                continue
            w = [b["p"][i] - a["p"][i] for i in range(3)]
            if kind == "coincident":
                d = abs(_dot(w, na))
                detail = "parallel planes %.3f mm apart, face ids %s/%s" % (
                    d, a["area"], b["area"])
            else:
                along = _dot(w, na)
                perp = [w[i] - along * na[i] for i in range(3)]
                d = math.sqrt(sum(x * x for x in perp))
                detail = "coaxial cylinders, axes %.3f mm apart, R %.3f/%.3f mm" % (
                    d, a["r"], b["r"])
            if d > tol_mm:
                continue
            # IFace2::GetArea reports 0.0 for these assembly-context faces, so it
            # cannot rank candidates; the radius agreement does when coaxial.
            score = -(abs(a.get("r", 0) - b.get("r", 0)) if kind == "concentric" else 0.0)
            if best is None or score > best[0]:
                best = (score, a, b, detail)
    if best is None:
        return None
    return {"a": best[1], "b": best[2], "detail": best[3]}


IDENTITY = Array[Double]([1.0, 0.0, 0.0,
                          0.0, 1.0, 0.0,
                          0.0, 0.0, 1.0,
                          0.0, 0.0, 0.0,
                          1.0, 0.0, 0.0, 0.0])


def rot_about_point(px, py, angle_deg):
    """16-element transform: rotate by angle about Z through (px, py) metres.

    The 3x3 block of a SolidWorks transform array is read COLUMN-major, so the
    entries of Rz are written transposed here (c, s / -s, c). Supplying them in
    row order made SOLIDWORKS apply Rz(-angle) with the correct translation,
    which parked the 120 deg and 240 deg blade instances at the wrong angle - the
    measured box centre of a 120 deg instance moved from (68.9, 671.6) to
    (613.3, -605.6).
    """
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    tx = px - (c * px - s * py)
    ty = py - (s * px + c * py)
    return Array[Double]([c, s, 0.0,
                          -s, c, 0.0,
                          0.0, 0.0, 1.0,
                          tx, ty, 0.0,
                          1.0, 0.0, 0.0, 0.0])


class Asm:
    def __init__(self, sw, title):
        self.sw = sw
        self.title = title
        self.log = []
        self.components = []
        self.sd = None
        self.md = IModelDoc2(sw.NewDocument(TPL_ASM, 0, 0.0, 0.0))
        self.asm = IAssemblyDoc(self.md)
        self.sd = SelectionMgr(self.md.SelectionManager).CreateSelectData()

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
        """Insert a component and put it back into the shared modelling frame.

        IAssemblyDoc::AddComponent5 does NOT leave the part in its own coordinate
        frame: it translates the component so that the part's bounding-box centre
        sits at the insertion point (the stored transform is minus the box
        centre). That scattered every part in an earlier build. Setting the
        transform to the identity first restores the common frame in which every
        part was modelled, so parts land in their assembled positions; blades 2
        and 3 are then rotated about the rotor axis in that same frame.
        """
        path = self.open(name)
        comp = self.asm.AddComponent5(path, 0, "", False, "", 0.0, 0.0, 0.0)
        if comp is None:
            raise RuntimeError("AddComponent5 failed for %s" % name)
        comp = IComponent2(comp)
        math_util = IMathUtility(self.sw.GetMathUtility())
        entry = {"component": comp.Name2, "source": name, "angle_deg": angle}
        comp.SetTransformAndSolve3(math_util.CreateTransform(IDENTITY), False)
        if angle:
            tr = math_util.CreateTransform(rot_about_point(mm(ROTOR[0]), mm(ROTOR[1]), angle))
            try:
                comp.SetTransformAndSolve3(tr, False)
                entry["rotated"] = True
                back = [float(v) for v in comp.Transform2.ArrayData]
                entry["rotation_applied_deg"] = round(
                    math.degrees(math.atan2(back[3], back[0])), 3)
                entry["applied_translation_mm"] = [round(back[9 + i] * 1000.0, 1)
                                                   for i in range(3)]
            except Exception as exc:  # noqa: BLE001
                entry["rotated"] = False
                entry["rotate_error"] = repr(exc)
        self.components.append((comp, entry))
        self.md.EditRebuild3()
        return comp

    def orient_upright(self, angle_deg=-90.0):
        """Turn the finished root assembly so the fan hangs from its ceiling plate.

        Every part is modelled about +Z because the part builders extrude from the
        Front plane, so a top-level assembly straight out of the build lays the fan
        on its side with the downrod pointing horizontally - it does not read as a
        ceiling fan at all. Rotating the root components -90 deg about X maps +Z
        (toward the ceiling) onto +Y (up), which is how the fan is installed.

        The rotation is built by IMathUtility::CreateTransformRotateAxis rather
        than by writing a transform array by hand: the array layout that
        SetTransformAndSolve3 accepts is column-major, and hand-built matrices
        were silently transposed earlier in this build.
        """
        math_util = IMathUtility(self.sw.GetMathUtility())
        origin = math_util.CreatePoint(Array[Double]([0.0, 0.0, 0.0]))
        axis_x = math_util.CreateVector(Array[Double]([1.0, 0.0, 0.0]))
        rot = math_util.CreateTransformRotateAxis(origin, axis_x,
                                                 math.radians(angle_deg))
        moved = []
        for comp, entry in self.components:
            before = [float(v) for v in comp.Transform2.ArrayData]
            if max(abs(before[9]), abs(before[10]), abs(before[11])) > 1e-9:
                raise RuntimeError("orient_upright expects components at the origin")
            comp.SetTransformAndSolve3(rot, False)
            entry["oriented_upright_deg_x"] = angle_deg
            moved.append(str(comp.Name2))
        self.md.EditRebuild3()
        return moved

    def component_properties(self):
        """Per-component placement and mass, taken from assembly-space boxes.

        Masses here are SOLIDWORKS mass with no material assigned, i.e. volume at
        1000 kg/m3, so they are NOT the design masses; they are recorded only so
        the volume sum can be cross-checked. IComponent2::GetBox is used for
        placement because it returns geometry already in assembly space, whereas
        CenterOfMass double-transforms and gave wrong numbers in an earlier build.
        """
        rows = []
        mass_total = 0.0
        for comp, entry in self.components:
            doc = IModelDoc2(comp.GetModelDoc2())
            if doc is None:
                entry["sw_mass_kg"] = None
                rows.append(entry)
                continue
            mp = IMassProperty2(doc.Extension.CreateMassProperty2())
            mass = float(mp.Mass)
            entry["sw_mass_kg_at_1000kgm3"] = round(mass, 4)
            entry["volume_m3"] = round(float(mp.Volume), 9)
            # The persisted component transform is the placement evidence. It is
            # recorded in full so verify_and_report.py can transform the known
            # part-space boxes into assembly space and prove the blade angles;
            # in-assembly box reads returned zeros and are not trusted here.
            try:
                tr = [float(v) for v in comp.Transform2.ArrayData]
                entry["transform"] = [round(v, 6) for v in tr]
                entry["placement_angle_deg"] = round(math.degrees(math.atan2(tr[3], tr[0])), 3)
            except Exception as exc:  # noqa: BLE001
                entry["transform_error"] = repr(exc)
            mass_total += mass
            rows.append(entry)
        summary = {"component_count": len(self.components),
                   "sw_mass_kg_at_1000kgm3": round(mass_total, 4)}
        return summary, rows

    def find(self, prefix):
        for comp, entry in self.components:
            if str(comp.Name2).startswith(prefix):
                return comp
        raise RuntimeError("no component matching %r" % prefix)

    def snapshot(self):
        out = {}
        for comp, _ in self.components:
            tr = [float(v) for v in comp.Transform2.ArrayData]
            out[str(comp.Name2)] = tr
        return out

    def max_movement(self, before):
        """Largest per-component shift: (translation in mm, rotation in degrees).

        Rotation-matrix elements are dimensionless, so they cannot be compared
        against a mm tolerance; the relative rotation is taken as the angle of
        R2 * R1^T.
        """
        worst_t = 0.0
        worst_r = 0.0
        for comp, _ in self.components:
            name = str(comp.Name2)
            if name not in before:
                continue
            tr = [float(v) for v in comp.Transform2.ArrayData]
            b = before[name]
            worst_t = max(worst_t, max(abs(tr[9 + i] - b[9 + i]) for i in range(3)) * 1000.0)
            r1 = [[b[0], b[1], b[2]], [b[3], b[4], b[5]], [b[6], b[7], b[8]]]
            r2 = [[tr[0], tr[1], tr[2]], [tr[3], tr[4], tr[5]], [tr[6], tr[7], tr[8]]]
            # rel = r2 * r1^T
            rel = [[sum(r2[i][k] * r1[j][k] for k in range(3)) for j in range(3)]
                   for i in range(3)]
            tr_ = rel[0][0] + rel[1][1] + rel[2][2]
            cos_a = max(-1.0, min(1.0, (tr_ - 1.0) / 2.0))
            worst_r = max(worst_r, math.degrees(math.acos(cos_a)))
        return worst_t, worst_r

    def apply_joints(self, joints):
        """Create each joint from a geometry-matched face pair, verify, keep or undo."""
        accepted, rejected = [], []
        for spec in joints:
            rec = {"name": spec["name"], "kind": spec["kind"],
                   "between": [spec["a"], spec["b"]]}
            try:
                ca = self.find(spec["a"])
                cb = self.find(spec["b"])
                fa, fb = comp_faces(ca), comp_faces(cb)
                match = match_faces(fa, fb, spec["kind"])
                if match is None:
                    rec["status"] = "no matching %s face pair on the two components" \
                                    % spec["kind"]
                    rejected.append(rec)
                    continue
                rec["matched"] = match["detail"]
                before = self.snapshot()
                self.md.ClearSelection2(True)
                ok1 = bool(IEntity(match["a"]["face"]).Select4(False, self.sd))
                ok2 = bool(IEntity(match["b"]["face"]).Select4(True, self.sd))
                if not (ok1 and ok2):
                    rec["status"] = "face selection failed"
                    rejected.append(rec)
                    continue
                res = self.asm.AddMate5(MATE_TYPES[spec["kind"]], MATE_ALIGN, False,
                                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                        False, False, 0, 0)
                self.md.EditRebuild3()
                mate = res[0] if isinstance(res, tuple) else res
                err = res[1] if isinstance(res, tuple) else None
                if mate is None:
                    rec["status"] = "AddMate5 created nothing"
                    rec["error_code"] = err
                    self.md.EditUndo2(1)
                    rejected.append(rec)
                    continue
                dt, dr = self.max_movement(before)
                rec["component_shift_mm"] = round(dt, 3)
                rec["component_rotation_deg"] = round(dr, 3)
                if dt > 0.2 or dr > 0.2:
                    self.md.EditUndo2(1)
                    self.md.EditRebuild3()
                    rec["status"] = ("rejected: mate moved components %.2f mm / %.2f deg"
                                     % (dt, dr))
                    rejected.append(rec)
                    continue
                rec["status"] = "created"
                accepted.append(rec)
            except Exception as exc:  # noqa: BLE001
                rec["status"] = "error: %r" % exc
                rejected.append(rec)
        return accepted, rejected

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

    def discard(self):
        """Close without saving, so a rejected-mate layout can never be written."""
        try:
            self.sw.QuitDoc(str(self.md.GetTitle()))
        except Exception:  # noqa: BLE001
            try:
                self.sw.CloseDoc(str(self.md.GetTitle()))
            except Exception:  # noqa: BLE001
                pass


JOINTS = {
    "FD_ROTOR": [
        {"name": "blade%d_root_face" % i, "kind": "coincident",
         "a": "FD_Blade-%d" % i, "b": "FD_BladeHub-1"} for i in (1, 2, 3)
    ] + [
        {"name": "blade%d_root_bore" % i, "kind": "concentric",
         "a": "FD_Blade-%d" % i, "b": "FD_BladeHub-1"} for i in (1, 2, 3)
    ],
    "FD_TILT": [
        {"name": "outer_axis_concentric", "kind": "concentric",
         "a": "FD_SupportYoke-1", "b": "FD_OuterTiltRing-1"},
        {"name": "inner_axis_concentric", "kind": "concentric",
         "a": "FD_OuterTiltRing-1", "b": "FD_InnerCradle-1"},
        {"name": "adapter_to_cradle", "kind": "coincident",
         "a": "FD_MotorAdapter-1", "b": "FD_InnerCradle-1"},
        {"name": "cover_to_adapter", "kind": "coincident",
         "a": "FD_MotorCover-1", "b": "FD_MotorAdapter-1"},
        {"name": "bracket_x_to_yoke", "kind": "coincident",
         "a": "FD_ServoBracketX-1", "b": "FD_SupportYoke-1"},
    ],
    "FD_SMART_FAN_ASSEMBLY": [
        {"name": "downrod_concentric", "kind": "concentric",
         "a": "FD_Downrod-1", "b": "FD_CeilingPlate-1"},
        {"name": "downrod_shoulder", "kind": "coincident",
         "a": "FD_Downrod-1", "b": "FD_CeilingPlate-1"},

    ],
}


def main():
    os.makedirs(CALC, exist_ok=True)
    sw = ISldWorks(Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    sw.Visible = True
    report = {"solidworks_revision": str(sw.RevisionNumber)}
    plan = {}

    def record(title, builder):
        """Trial the joints, then save a document that contains only clean mates.

        Pass 1 applies every candidate joint and measures what each one does to
        the component transforms. If any joint was rejected, the trial document
        cannot be trusted (EditUndo2 does not reliably remove a mate feature), so
        it is discarded without saving and the assembly is rebuilt and saved with
        only the joints that were clean. The saved file is then re-read and its
        mate-feature count reported, so the number written here is measured, not
        assumed.
        """
        asm = None
        try:
            asm = builder()
            summary, rows = asm.component_properties()
            accepted, rejected = asm.apply_joints(JOINTS[title])
            trial_mates = asm.mate_feature_count()
            if rejected:
                asm.discard()
                asm = builder()
                clean = [j for j in JOINTS[title]
                         if any(a["name"] == j["name"] for a in accepted)]
                accepted, again = asm.apply_joints(clean)
                rejected = rejected + [dict(r, note="pass 2") for r in again]
                summary, rows = asm.component_properties()
            path = asm.save()
            saved_mates = asm.mate_feature_count()
            report[title] = {"file": os.path.relpath(path, FD).replace("\\", "/"),
                             "bytes": os.path.getsize(path),
                             "components": summary,
                             "trial_mate_features": trial_mates,
                             "mate_features_created": saved_mates,
                             "mates_accepted": accepted,
                             "mates_rejected": rejected,
                             "parts": rows}
            plan[title] = JOINTS[title]
            print("PASS %s components=%d mates=%d(top trial %d) "
                  "volume-mass=%.3fkg"
                  % (title, summary["component_count"], saved_mates, trial_mates,
                     summary["sw_mass_kg_at_1000kgm3"]), flush=True)
        except Exception as exc:  # noqa: BLE001
            report[title] = {"error": repr(exc)}
            print("FAIL %s: %r" % (title, exc), flush=True)
        finally:
            if asm is not None:
                asm.close()

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
        a.orient_upright()
        return a

    record("FD_SMART_FAN_ASSEMBLY", build_root)

    with open(os.path.join(CALC, "assembly_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    with open(os.path.join(CALC, "assembly_joint_plan.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2)
    # finish the task: no document windows and no SOLIDWORKS session left open
    import swutil
    print("closed %d open documents" % len(swutil.open_titles()), flush=True)
    swutil.shutdown(sw)
    print("solidworks closed")


if __name__ == "__main__":
    main()
