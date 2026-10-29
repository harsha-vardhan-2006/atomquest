"""Determine which boolean/env types work with InvokeMember."""
import sys, os
sys.path.insert(0, r"E:\SOLIDWORKS Downloads\SOLIDWORKS")
import clr
clr.AddReference(r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist\SolidWorks.Interop.sldworks.dll")
clr.AddReference(r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist\SolidWorks.Interop.swcommands.dll")
clr.AddReference(r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist\SolidWorks.Interop.swconst.dll")
from System import Type, Activator, Array, Object, Boolean, Single, Double
import SolidWorks.Interop.swconst as swmod

sw = Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"))
TPL = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\templates"
OUT = r"E:\atomquest\competition\atomQUEST2026\round2\MODEL_1_DUAL_RING_GIMBAL\01_CAD_PARTS"
os.makedirs(OUT, exist_ok=True)

def mkarr(vals):
    t = type(vals[0]) if vals else Object
    n = len(vals)
    a = Array.CreateInstance(t, n)
    for i,v in enumerate(vals): a[i]=v
    return a

# NewDocument -> fails with enum in array
print("=== Test 1: NewDocument with enum in array ===")
args = mkarr([os.path.join(TPL,"Part.PRTDOT"), swmod.swDocumentTypes_e.swDocPART, 0, 0, 0])
print("  types:", [type(a).__name__ for a in args])
try:
    doc = sw.GetType().InvokeMember("NewDocument", 32769, None, sw, args)
    print("  SUCCESS:", type(doc).__name__)
    docpath = os.path.join(OUT, "TEST1.SLDPRT")
    doc.GetType().InvokeMember("SaveAs", 32769, None, doc, mkarr([docpath]))
    print("  Saved:", os.path.exists(docpath), os.path.getsize(docpath), "bytes")
except Exception as e:
    print("  FAILED:", str(e)[:200])

print()
print("=== Test 2: NewDocument with wrapped enum ===")
from System import Enum
edoc = Enum.ToObject(swmod.swDocumentTypes_e, 1)
args2 = mkarr([os.path.join(TPL,"Part.PRTDOT"), edoc, 0, 0, 0])
print("  types:", [type(a).__name__ for a in args2])
try:
    doc2 = sw.GetType().InvokeMember("NewDocument", 32769, None, sw, args2)
    print("  SUCCESS:", type(doc2).__name__)
    docpath2 = os.path.join(OUT, "TEST2.SLDPRT")
    save_args = mkarr([docpath2])
    doc2.GetType().InvokeMember("SaveAs", 32769, None, doc2, save_args)
    print("  Saved:", os.path.exists(docpath2), os.path.getsize(docpath2), "bytes")
except Exception as e:
    print("  FAILED:", str(e)[:200])

print()
print("=== Test 3: InsertSketch with bool ===")
try:
    args3 = mkarr([True])
    print("  types:", [type(a).__name__ for a in args3])
    doc3 = sw.GetType().InvokeMember("NewDocument", 32769, None, sw, mkarr([os.path.join(TPL,"Part.PRTDOT"), Enum.ToObject(swmod.swDocumentTypes_e,1), 0,0,0]))
    doc3.GetType().InvokeMember("InsertSketch", 32769, None, doc3, args3)
    print("  InsertSketch SUCCESS")
    # Now try extents with booleans
    ext = mkarr([True, False, False, 0,0,0,0,0,0,0,0,0, 20.0, 0,0,0,0])
    print("  extrude types:", [type(a).__name__ for a in ext])
    doc3.GetType().InvokeMember("InsertExtrude2", 32769, None, doc3, ext)
    docpath3 = os.path.join(OUT, "TEST3.SLDPRT")
    doc3.GetType().InvokeMember("SaveAs", 32769, None, doc3, mkarr([docpath3]))
    print("  Saved:", os.path.exists(docpath3), os.path.getsize(docpath3), "bytes")
except Exception as e:
    print("  FAILED:", str(e)[:300])

print()
print("=== Test 4: InsertExtrude2 with Boolean enum ===")
try:
    doc4 = sw.GetType().InvokeMember("NewDocument", 32769, None, sw, mkarr([os.path.join(TPL,"Part.PRTDOT"), Enum.ToObject(swmod.swDocumentTypes_e,1), 0,0,0]))
    doc4.GetType().InvokeMember("InsertSketch", 32769, None, doc4, mkarr([True]))
    sm = doc4.GetType().InvokeMember("SketchManager", 4096, None, doc4, None)
    sm.GetType().InvokeMember("CreateRectangle", 32769, None, sm, mkarr([0.0,0.0,0.0, 100.0,100.0,0.0]))
    doc4.GetType().InvokeMember("ExitSketch", 32769, None, doc4, mkarr([True]))
    # Try enums for the booleans
    swbool = swmod.swbool_e
    ext4 = mkarr([swbool.swtrue, swbool.swfalse, swbool.swfalse,
                  0,0,0,0,0,0,0,0,0,
                  20.0, 0,0,0,0])
    print("  extrude types:", [type(a).__name__ for a in ext4])
    doc4.GetType().InvokeMember("InsertExtrude2", 32769, None, doc4, ext4)
    docpath4 = os.path.join(OUT, "TEST4.SLDPRT")
    doc4.GetType().InvokeMember("SaveAs", 32769, None, doc4, mkarr([docpath4]))
    print("  Saved:", os.path.exists(docpath4), os.path.getsize(docpath4), "bytes")
    print("  SUCCESS!")
except Exception as e:
    print("  FAILED:", str(e)[:300])
