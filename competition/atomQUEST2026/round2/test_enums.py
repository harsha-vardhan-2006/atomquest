"""Inspect swconst module imports."""
import sys, clr
sys.path.insert(0, r"E:\SOLIDWORKS Downloads\SOLIDWORKS")
clr.AddReference(r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist\SolidWorks.Interop.sldworks.dll")
clr.AddReference(r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist\SolidWorks.Interop.swcommands.dll")
clr.AddReference(r"E:\SOLIDWORKS Downloads\SOLIDWORKS\api\redist\SolidWorks.Interop.swconst.dll")
import SolidWorks.Interop.swconst as swmod
from System import Type

print("swmod:", type(swmod))
print("swmod dir:", sorted(dir(swmod)))

# Get the type from the CLR type system
for attr in dir(swmod):
    try:
        val = getattr(swmod, attr)
        tname = type(val).__name__
        if 'enum' in tname.lower() or 'metatype' in tname.lower() or 'type' in tname.lower():
            print(f"  {attr}: {tname}")
            # list members
            if hasattr(val, '__dict__'):
                members = [v for v in dir(val) if not v.startswith('_')]
                print(f"    members: {members[:10]}...")
    except: pass

# Now try to get swconst type via reflection
print("\nswconst assembly inspection:")
asm = swmod.GetType().Assembly if hasattr(swmod,'GetType') else None
if asm:
    print("  Assembly:", asm.GetName().Name)
    for t in asm.GetTypes():
        if t.IsEnum and 'bool' in t.Name.lower():
            print(f"  Bool enum: {t.Name}")
            print(f"    values: {[e.value for e in t.GetFields()]}")
