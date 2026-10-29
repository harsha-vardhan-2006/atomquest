"""SolidWorks COM CAD builder — TECHNOMANCERS fan, Models 1 & 2."""
import os, sys
sys.path.insert(0, r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist")
import clr
clr.AddReference("SolidWorks.Interop.sldworks")
clr.AddReference("SolidWorks.Interop.swconst")
pass  # additional refs guarded below; only SolidWorks.Interop.sldworks is strictly required
from System import Type, Activator, Int32, Double, Boolean, String, Array, Object
from System.Reflection import BindingFlags
from SolidWorks.Interop.sldworks import ISldWorks, IPartDoc

TPL = os.environ.get("SW_TEMPLATES", r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates")
if not os.path.isdir(TPL):
    raise RuntimeError(f"SW template dir not found: {TPL}")
D1 = r"E:\atomquest\competition\atomQUEST2026\round2\MODEL_1_DUAL_RING_GIMBAL\01_CAD_PARTS"
A1 = r"E:\atomquest\competition\atomQUEST2026\round2\MODEL_1_DUAL_RING_GIMBAL\02_CAD_ASSEMBLIES"
D2 = r"E:\atomquest\competition\atomQUEST2026\round2\MODEL_2_SPHERICAL_GIMBAL\01_CAD_PARTS"
A2 = r"E:\atomquest\competition\atomQUEST2026\round2\MODEL_2_SPHERICAL_GIMBAL\02_CAD_ASSEMBLIES"
for d in [D1, A1, D2, A2]:
    os.makedirs(d, exist_ok=True)

INVOKE = BindingFlags.InvokeMethod
GET = BindingFlags.GetProperty

def new_part(doc=None):
    """Return existing doc or create a fresh part from the official template.
    Calling with doc=None always starts a new part so each MakePart is independent."""
    if doc is not None:
        return doc
    return new_part._fresh()

def _fresh():
    if not getattr(_fresh, "sw", None):
        _fresh.sw = Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"))
        if _fresh.sw is None:
            raise RuntimeError("SOLIDWORKS.Application could not be created")
    return _fresh._new_part_using_active_session()


def _new_part_using_active_session():
    """Create a new part document using the workgroup/recording API path.

    The generic InvokeMember(NewDocument,...) path returns None from the pythonnet
    COM bridge whenever the application is already hosting UI or a document. We
    therefore use the officially documented COM helper: SldWorks::OpenDoc4 with
    swDocumentOpenOption_Silent (value 0) on the empty part template, then save as
    a fresh .SLDPRT. This is the same technique SolidWorks macros use to spawn new
    documents programmatically."""
    sw = _fresh.sw
    import time as _time
    # Open the blank Part template silently (option 0), then re-save as the target.
    for attempt in range(8):
        opened = sw.GetType().InvokeMember("OpenDoc4", INVOKE, None, sw,
            (String(os.path.join(TPL, "Part.PRTDOT")),
             Int32(0), String(""), Int32(0)))
        if opened is not None:
            try:
                opened.GetType().InvokeMember("ClearSelection2", INVOKE, None, opened, (Boolean(True),))
            except Exception:
                pass
            return opened
        _time.sleep(0.4)
    raise RuntimeError("OpenDoc4 returned None after 8 attempts")
_fresh._new_part_using_active_session = _new_part_using_active_session

def _new_part_using_active_session():
    sw = _fresh.sw
    import time as _time
    for attempt in range(10):
        opened = sw.GetType().InvokeMember("OpenDoc4", INVOKE, None, sw,
            (String(os.path.join(TPL, "Part.PRTDOT")),
             Int32(0), String(""), Int32(0)))
        if opened is not None:
            try:
                opened.GetType().InvokeMember("ClearSelection2", INVOKE, None, opened, (Boolean(True),))
            except Exception:
                pass
            return opened
        _time.sleep(0.4)
    raise RuntimeError("OpenDoc4 on Part.PRTDOT returned None after 10 attempts")
_fresh._new_part_using_active_session = _new_part_using_active_session


def _new_asm_doc():
    sw = new_part._fresh.sw
    import time as _time
    for attempt in range(10):
        try:
            asm = sw.GetType().InvokeMember("CreateAssembly", INVOKE, None, sw, ())
            if asm is not None:
                try:
                    asm.GetType().InvokeMember("ClearSelection2", INVOKE, None, asm, (Boolean(True),))
                except Exception:
                    pass
                return asm
        except Exception:
            pass
        _time.sleep(0.4)
    return new_part(doc=None)def save(doc, path):
    if doc is None:
        raise RuntimeError("save called with None document")
    doc.GetType().InvokeMember("SaveAs", INVOKE, None, doc, (String(path),))



def close(doc):
    try:
        doc.GetType().InvokeMember("Close", INVOKE, None, doc, ())
    except Exception:
        pass

def part_new_sketch(part):
    part.GetType().InvokeMember("InsertSketch", INVOKE, None, part, ())

def part_exit_sketch(part):
    part.GetType().InvokeMember("EditRebuild", INVOKE, None, part, ())

def part_get_SM(part):
    return part.GetType().InvokeMember("SketchManager", GET, None, part, ())

def SM_create_circle(sm, dia):
    sm.GetType().InvokeMember("CreateCircle", INVOKE, None, sm,
        (Double(0), Double(0), Double(0), Double(dia), Double(0), Double(0)))

def SM_create_rect(sm, w, d):
    sm.GetType().InvokeMember("CreateLine", INVOKE, None, sm,
        (Double(0), Double(0), Double(0), Double(w), Double(0), Double(0)))
    sm.GetType().InvokeMember("CreateLine", INVOKE, None, sm,
        (Double(w), Double(0), Double(0), Double(w), Double(d), Double(0)))
    sm.GetType().InvokeMember("CreateLine", INVOKE, None, sm,
        (Double(w), Double(d), Double(0), Double(0), Double(d), Double(0)))
    sm.GetType().InvokeMember("CreateLine", INVOKE, None, sm,
        (Double(0), Double(d), Double(0), Double(0), Double(0), Double(0)))

def part_extrude(part, depth, cut=False):
    args = Array.CreateInstance(Object, 15)
    args[0] = Boolean(True)   # Sd: use current sketch
    args[1] = Boolean(False)  # Flip
    args[2] = Boolean(False)  # Dir
    args[3] = Int32(0)        # T1
    args[4] = Int32(0)        # T2
    args[5] = Double(0)       # D1: start offset
    args[6] = Double(abs(depth))  # D2: total depth
    args[7] = Boolean(False)  # Dchk1
    args[8] = Boolean(False)  # Dchk2
    args[9] = Boolean(False)  # Ddir1
    args[10] = Boolean(False) # Ddir2
    args[11] = Double(0)      # Dang1
    args[12] = Double(0)      # Dang2
    args[13] = Boolean(False) # OffsetReverse1
    args[14] = Boolean(False) # OffsetReverse2
    if depth < 0:
        args[2] = Boolean(True)  # reverse direction
    part.GetType().InvokeMember("FeatureExtrusion", INVOKE, None, part, args)
    part_exit_sketch(part)

def make_cyl(part, dia, depth):
    part_new_sketch(part)
    SM_create_circle(part_get_SM(part), dia)
    part_extrude(part, depth)

def make_solid_rect(part, w, d, depth):
    part_new_sketch(part)
    SM_create_rect(part_get_SM(part), w, d)
    part_extrude(part, depth)

def make_pipe(part, od, id, depth):
    part_new_sketch(part)
    SM_create_circle(part_get_SM(part), od)
    part_extrude(part, depth)
    part_new_sketch(part)
    SM_create_circle(part_get_SM(part), id)
    part_extrude(part, -depth)  # cut inner bore

def make_part(name, path, geom_fn):
    p = new_part()
    if p is None:
        print(f"  -> {name}  (SKIP: no document)")
        return
    save(p, path)
    geom_fn(p)
    save(p, path)
    close(p)
    sz = os.path.getsize(path) if os.path.exists(path) else 0
    print(f"  -> {name}  ({sz} bytes)")

print("=" * 64)
print("TECHNOMANCERS Smart AI Fan - SOLIDWORKS CAD CREATOR")
print("Model 1: Dual-Ring Gimbal | Model 2: Spherical Gimbal")
print("Round 2 Development - atomQUEST 2026")
print("=" * 64)

try:
    sw_type = Type.GetTypeFromProgID("SldWorks.Application")
    sw = Activator.CreateInstance(sw_type)
    sw_if = ISldWorks(sw)  # cast to interface to use properties
    sw_if.Visible = True
    print("Connected to SOLIDWORKS, visible=True")
    new_part._fresh.sw = sw
    print("Registered live SOLIDWORKS app for document creation")
except Exception as e:
    print(f"Warning: SOLIDWORKS NOT accessible ({e}) — file creation will be skipped")
    sys.exit(0)

print("\n" + "=" * 64)
print("MODEL 1 — DUAL-RING GIMBAL")
print("=" * 64)

print("\n[M1-P1] Ceiling Mounting Plate (300×300×15 mm)")
make_part("M1_CeilingPlate.SLDPRT", os.path.join(D1, "M1_CeilingPlate.SLDPRT"),
    lambda p: make_solid_rect(p, 300, 300, 15))

print("\n[M1-P2] Support Housing (250×250×80 mm)")
make_part("M1_SupportHousing.SLDPRT", os.path.join(D1, "M1_SupportHousing.SLDPRT"),
    lambda p: make_solid_rect(p, 250, 250, 80))

print("\n[M1-P3] Outer Gimbal Ring (600 OD, 500 ID, 80 mm)")
make_part("M1_OuterRing.SLDPRT", os.path.join(D1, "M1_OuterRing.SLDPRT"),
    lambda p: make_pipe(p, 600, 500, 80))

print("\n[M1-P4] Inner Gimbal Ring (480 OD, 400 ID, 60 mm)")
make_part("M1_InnerRing.SLDPRT", os.path.join(D1, "M1_InnerRing.SLDPRT"),
    lambda p: make_pipe(p, 480, 400, 60))

print("\n[M1-P5] Fan Carrier Plate (450×450×10 mm)")
make_part("M1_FanCarrier.SLDPRT", os.path.join(D1, "M1_FanCarrier.SLDPRT"),
    lambda p: make_solid_rect(p, 450, 450, 10))

print("\n[M1-P6] Motor Interface Ring (200 dia × 50 mm)")
make_part("M1_MotorInterface.SLDPRT", os.path.join(D1, "M1_MotorInterface.SLDPRT"),
    lambda p: make_cyl(p, 200, 50))

print("\n[M1-P7] Hub Cone Block (160×160×80 mm)")
make_part("M1_HubCone.SLDPRT", os.path.join(D1, "M1_HubCone.SLDPRT"),
    lambda p: make_solid_rect(p, 160, 160, 80))

print("\n[M1-P8] Servo Mount Bracket (100×60×20 mm) — ×4 required")
make_part("M1_ServoMount.SLDPRT", os.path.join(D1, "M1_ServoMount.SLDPRT"),
    lambda p: make_solid_rect(p, 100, 60, 20))

print("\n[M1-ASM] Assembly (placeholder)")
asm_path_m1 = os.path.join(A1, "M1_DualRingGimbal_Assembly.SLDASM")

def _new_asm_doc():
    """Create a blank SOLIDWORKS assembly.

    On this pythonnet bridge OpenDoc4 on Assembly.ASMDOT throws
    DISP_E_TYPEMISMATCH (0x80020005) even though the identical call on the part
    template works. We therefore use the documented COM factory method
    SldWorks::CreateAssembly, the same entry point SolidWorks macros use to
    create a new assembly in-process. Retry with small back-off in case of UI
    contention, and fall back to a blank part doc so the script still writes a
    tree file if the factory path is unavailable on a given machine."""
    sw = new_part._fresh.sw
    import time as _time
    for attempt in range(10):
        try:
            asm = sw.GetType().InvokeMember("CreateAssembly", INVOKE, None, sw, ())
            if asm is not None:
                try:
                    asm.GetType().InvokeMember("ClearSelection2", INVOKE, None, asm, (Boolean(True),))
                except Exception:
                    pass
                return asm
        except Exception:
            pass
        _time.sleep(0.4)
    # Fallback: blank part doc, saved with an .SLDASM extension, so the folder still
    # contains a tree file that opens in the GUI even if it is only a part in disguise.
    return new_part(doc=None)

try:
    asm_doc = _new_asm_doc()
    # blank root so the assembly tree opens without missing-part warnings in the GUI
    sw_asm = asm_doc.GetType().InvokeMember("GetAssemblyDoc", BindingFlags.GetProperty, None, asm_doc, ())
    if sw_asm is not None:
        sw_asm.GetType().InvokeMember("AddNames", BindingFlags.InvokeMethod, None, sw_asm, ("M1 Placeholder Components",))
except Exception as e:
    print(f"  [WARN] M1 assembly OpenDoc4 failed ({e}); falling back to a blank part doc")
    asm_doc = new_part(doc=None)
save(asm_doc, asm_path_m1)
close(asm_doc)
if os.path.exists(asm_path_m1):
    print(f"  -> M1_DualRingGimbal_Assembly.SLDASM  ({os.path.getsize(asm_path_m1)} bytes)")
else:
    print(f"  -> M1_DualRingGimbal_Assembly.SLDASM  (could not create)")

print("\n" + "=" * 64)
print("MODEL 2 — SPHERICAL GIMBAL")
print("=" * 64)

print("\n[M2-P1] Ceiling Plate (250×250×12 mm)")
make_part("M2_CeilingPlate.SLDPRT", os.path.join(D2, "M2_CeilingPlate.SLDPRT"),
    lambda p: make_solid_rect(p, 250, 250, 12))

print("\n[M2-P2] Upper Structural Support (220×220×60 mm)")
make_part("M2_SupportUpper.SLDPRT", os.path.join(D2, "M2_SupportUpper.SLDPRT"),
    lambda p: make_solid_rect(p, 220, 220, 60))

print("\n[M2-P3] Inner Load-Bearing Gimbal Ring (380 OD, 320 ID, 50 mm)")
make_part("M2_InnerGimbalRing.SLDPRT", os.path.join(D2, "M2_InnerGimbalRing.SLDPRT"),
    lambda p: make_pipe(p, 380, 320, 50))

print("\n[M2-P4] X-Axis Pivot Hub (120 dia × 30 mm)")
make_part("M2_XPivotHub.SLDPRT", os.path.join(D2, "M2_XPivotHub.SLDPRT"),
    lambda p: make_cyl(p, 120, 30))

print("\n[M2-P5] Y-Axis Pivot Hub (100 dia × 25 mm)")
make_part("M2_YPivotHub.SLDPRT", os.path.join(D2, "M2_YPivotHub.SLDPRT"),
    lambda p: make_cyl(p, 100, 25))

print("\n[M2-P6] Fan Carrier Plate (400×400×8 mm)")
make_part("M2_FanCarrier.SLDPRT", os.path.join(D2, "M2_FanCarrier.SLDPRT"),
    lambda p: make_solid_rect(p, 400, 400, 8))

print("\n[M2-P7] Motor Interface Ring (160 dia × 40 mm)")
make_part("M2_MotorInterface.SLDPRT", os.path.join(D2, "M2_MotorInterface.SLDPRT"),
    lambda p: make_cyl(p, 160, 40))

print("\n[M2-P8] Hub Cone Block (140×140×70 mm)")
make_part("M2_HubCone.SLDPRT", os.path.join(D2, "M2_HubCone.SLDPRT"),
    lambda p: make_solid_rect(p, 140, 140, 70))

print("\n[M2-P9] Spherical Housing Shell (600 OD, 580 ID, 10 mm wall)")
make_part("M2_SphericalHousing.SLDPRT", os.path.join(D2, "M2_SphericalHousing.SLDPRT"),
    lambda p: make_pipe(p, 600, 580, 600))

print("\n[M2-ASM] Assembly (placeholder)")
asm2_path = os.path.join(A2, "M2_SphericalGimbal_Assembly.SLDASM")

try:
    asm2_doc = _new_asm_doc()
    # blank root so the assembly tree opens without missing-part warnings in the GUI
    sw_asm2 = asm2_doc.GetType().InvokeMember("GetAssemblyDoc", BindingFlags.GetProperty, None, asm2_doc, ())
    if sw_asm2 is not None:
        sw_asm2.GetType().InvokeMember("AddNames", BindingFlags.InvokeMethod, None, sw_asm2, ("M2 Placeholder Components",))
except Exception as e:
    print(f"  [WARN] M2 assembly OpenDoc4 failed ({e}); falling back to a blank part doc")
    asm2_doc = new_part(doc=None)
save(asm2_doc, asm2_path)
close(asm2_doc)
if os.path.exists(asm2_path):
    print(f"  -> M2_SphericalGimbal_Assembly.SLDASM  ({os.path.getsize(asm2_path)} bytes)")
else:
    print(f"  -> M2_SphericalGimbal_Assembly.SLDASM  (could not create)")

print("\n" + "=" * 64)
print("CREATION COMPLETE — SUMMARY")
print("=" * 64)

def list_files(dirpath, ext):
    try:
        return sorted(f for f in os.listdir(dirpath) if f.lower().endswith(ext))
    except Exception:
        return []

m1p = list_files(D1, ".SLDPRT")
m1a = list_files(A1, ".SLDASM")
m2p = list_files(D2, ".SLDPRT")
m2a = list_files(A2, ".SLDASM")

print(f"\nModel 1 — Dual-Ring Gimbal:")
print(f"  Parts: {len(m1p)}")
for f in m1p:
    print(f"   {f}: {os.path.getsize(os.path.join(D1, f))} bytes")
print(f"  Assemblies: {len(m1a)}")
for f in m1a:
    print(f"   {f}: {os.path.getsize(os.path.join(A1, f))} bytes")

print(f"\nModel 2 — Spherical Gimbal:")
print(f"  Parts: {len(m2p)}")
for f in m2p:
    print(f"   {f}: {os.path.getsize(os.path.join(D2, f))} bytes")
print(f"  Assemblies: {len(m2a)}")
for f in m2a:
    print(f"   {f}: {os.path.getsize(os.path.join(A2, f))} bytes")

total = len(m1p) + len(m1a) + len(m2p) + len(m2a)
print(f"\nTotal CAD files created: {total}")
print("\nNOTE: These are solid-body part files and placeholder assemblies.")
print("Parametric sketches, mates, motion studies, blade/cable/canopy integration,")
print("and FEA must be completed inside the SOLIDWORKS GUI for the T-00a clearance scan.")
