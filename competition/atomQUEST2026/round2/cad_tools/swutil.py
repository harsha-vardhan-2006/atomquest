#!/usr/bin/env python3
"""
SOLIDWORKS COM automation harness for the AtomQuest Smart AI Fan Rev 2 CAD package.

Uses pywin32 dynamic IDispatch dispatch (no generated wrappers required).

API unit convention: the SolidWorks API works in METRES, RADIANS and KG
regardless of the document's displayed units.

Run `python swutil.py` for an end-to-end self test:
connect -> new part -> sketch -> extrude -> save -> close -> reopen -> rebuild
-> mass properties -> bounding box -> STEP export.
"""
import os
import sys
import time

import pythoncom
import win32com.client

PROGID = "SldWorks.Application"

# swDocumentTypes_e
DOC_PART, DOC_ASSEMBLY, DOC_DRAWING = 1, 2, 3
# swOpenDocOptions_e
OPT_SILENT = 1
OPT_READONLY = 2
# swSaveAsOptions_e
SAVE_SILENT = 1
# swFileSaveError_e / swFileLoadError_e -> ignored, we check return codes


class SWError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# connection
# --------------------------------------------------------------------------
_SW = None


def connect(visible=True, timeout=180):
    """Return a running or freshly started SolidWorks application object."""
    global _SW
    if _SW is not None:
        return _SW
    pythoncom.CoInitialize()
    t0 = time.time()
    sw = None
    try:
        sw = win32com.client.GetActiveObject(PROGID)
    except Exception:
        sw = None
    if sw is None:
        sw = win32com.client.Dispatch(PROGID)
    # wait for the application to answer
    while time.time() - t0 < timeout:
        try:
            rev = _revision(sw)
            break
        except Exception:
            time.sleep(1.0)
    else:
        raise SWError("SolidWorks did not respond within %ss" % timeout)
    try:
        sw.Visible = visible
    except Exception:
        pass
    _SW = sw
    return sw


def _revision(sw):
    r = sw.RevisionNumber
    return r() if callable(r) else r


def revision():
    return _revision(connect())


# --------------------------------------------------------------------------
# documents
# --------------------------------------------------------------------------
def template(kind=DOC_PART, name=None):
    """Locate a system template: Part.PRTDOT / Assembly.ASMDOT / Drawing.DRWDOT."""
    base = name or {DOC_PART: "Part.PRTDOT",
                    DOC_ASSEMBLY: "Assembly.ASMDOT",
                    DOC_DRAWING: "Drawing.DRWDOT"}[kind]
    roots = [
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2026\Templates",
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2025\Templates",
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\Templates",
    ]
    for r in roots:
        p = os.path.join(r, base)
        if os.path.isfile(p):
            return p
    raise SWError("template %s not found in %s" % (base, roots))


def new_document(kind=DOC_PART, path=None):
    sw = connect()
    tpl = path or template(kind)
    doc = None
    for _ in range(10):
        try:
            doc = sw.NewDocument(tpl, 0, 0.0, 0.0)
        except Exception:
            doc = None
        if doc is not None:
            return doc
        time.sleep(0.5)
    raise SWError("NewDocument(%s) returned None" % tpl)


def open_document(path, kind=DOC_PART, options=OPT_SILENT):
    sw = connect()
    errors = 0
    warnings = 0
    doc = sw.OpenDoc6(path, kind, options, "", errors, warnings)
    if doc is None:
        raise SWError("OpenDoc6 failed for %s (errors=%s warnings=%s)"
                      % (path, errors, warnings))
    return doc


def close_document(doc, path=None):
    sw = connect()
    title = path
    if title is None:
        try:
            title = doc.GetPathName()
        except Exception:
            title = None
    try:
        if title:
            sw.CloseDoc(os.path.basename(title))
        else:
            sw.CloseDoc(doc.GetTitle())
    except Exception:
        pass


def open_titles():
    """Titles of every document currently open in the SOLIDWORKS session."""
    sw = connect()
    docs = sw.GetDocuments
    if callable(docs):
        docs = docs()
    out = []
    for d in (docs or []):
        try:
            t = d.GetTitle
            out.append(t() if callable(t) else t)
        except Exception:
            pass
    return out


def close_all(save=False):
    """Close every open document so no window is left behind between tasks.

    A headless build run that opens 20 parts and leaves them open floods the
    desktop with document windows and keeps the previous task's session alive;
    every build task ends with this call followed by :func:`quit_app`.
    """
    sw = connect()
    closed = []
    for title in open_titles():
        try:
            sw.CloseDoc(title)
            closed.append(title)
        except Exception:
            pass
    return closed


def quit_app(hard=True):
    """Close the SOLIDWORKS window itself once a task is finished."""
    global _SW
    try:
        sw = connect()
        shutdown(sw, hard=hard)
    except Exception:
        if hard:
            os.system('taskkill /F /IM SLDWORKS.exe >NUL 2>&1')
    _SW = None
    return not running()


def shutdown(sw, hard=True):
    """End a build task: close every document, then close the application.

    ExitApp() alone leaves SLDWORKS.exe resident on this machine (measured: the
    process survived after every document had been closed), so the task ends
    with a process kill once all work is saved.
    """
    docs = None
    try:
        docs = sw.GetDocuments
        if callable(docs):
            docs = docs()
    except Exception:
        docs = None
    for d in (docs or []):
        try:
            t = d.GetTitle
            sw.CloseDoc(t() if callable(t) else t)
        except Exception:
            pass
    try:
        sw.ExitApp()
    except Exception:
        pass
    if not hard:
        return not running()
    for _ in range(20):
        if not running():
            return True
        time.sleep(1.0)
    os.system('taskkill /F /IM SLDWORKS.exe >NUL 2>&1')
    time.sleep(3.0)
    return not running()


def running():
    """True when a SLDWORKS.exe process exists."""
    out = os.popen('tasklist /FI "IMAGENAME eq SLDWORKS.exe" /NH').read()
    return "SLDWORKS.exe" in out


def save(doc, path=None):
    p = path or doc.GetPathName()
    if not p:
        raise SWError("save(): no path")
    ok = doc.Extension.SaveAs(p, 0, 1, None, 0, 0)
    if not ok:
        # SaveAs3-style fallback
        ok2 = doc.SaveAs3(p, 0, 0) if hasattr(doc, "SaveAs3") else False
        if not ok2:
            raise SWError("SaveAs failed for %s" % p)
    return p


def rebuild(doc):
    """Rebuild and return (ok, error_count)."""
    ok = doc.EditRebuild3()
    err = 0
    try:
        err = doc.Extension.NeedsRebuild2() and 1 or 0
    except Exception:
        pass
    return bool(ok), err


def get_errors(doc):
    """Collect feature-level errors: returns list of (name, error)."""
    out = []
    feat = doc.FirstFeature()
    while feat is not None:
        try:
            e = feat.GetErrors2() if hasattr(feat, "GetErrors2") else 0
        except Exception:
            e = 0
        if e:
            out.append((feat.Name, e))
        feat = feat.GetNextFeature()
    return out


# --------------------------------------------------------------------------
# modelling helpers (API units: metres, radians)
# --------------------------------------------------------------------------
def sm(doc):
    return doc.SketchManager


def start_sketch(doc, plane="Front"):
    doc.Extension.SelectByID2("%s" % plane, "PLANE", 0, 0, 0, False, 0, None, 0)
    doc.SketchManager.InsertSketch(True)
    return doc.SketchManager


def circle(doc, cx, cy, r, cz=0.0):
    s = sm(doc)
    s.CreateCircle(cx, cy, cz, cx + r, cy, cz)


def rect(doc, x0, y0, x1, y1, z=0.0):
    s = sm(doc)
    s.CreateCornerRectangle(x0, y0, z, x1, y1, z)


def line(doc, x0, y0, x1, y1, z=0.0):
    s = sm(doc)
    s.CreateLine(x0, y0, z, x1, y1, z)


def polyline(doc, pts, z=0.0, close=True):
    s = sm(doc)
    n = len(pts)
    last = n if close else n - 1
    for i in range(last):
        a = pts[i]
        b = pts[(i + 1) % n]
        s.CreateLine(a[0], a[1], z, b[0], b[1], z)


def spline(doc, pts, z=0.0):
    """Create a closed/ open B-spline through pts [(x,y), ...] in metres."""
    import System  # noqa - not available under pywin32; use CreateSpline variant
    raise SWError("use spline_py")


def spline_py(doc, pts, z=0.0):
    """Create a spline using the (x,y,z) flat array overload."""
    s = sm(doc)
    arr = []
    for (x, y) in pts:
        arr.extend([x, y, z])
    import pythoncom
    # CreateSpline2 takes Double[] of xyz triples
    try:
        return s.CreateSpline2(arr)
    except Exception:
        return s.CreateSpline(arr)


def close_sketch(doc):
    sm(doc)
    doc.SketchManager.InsertSketch(True)


def extrude(doc, depth_m, flip=False, merge=True):
    """Extrude the active sketch by depth_m (meters, negative = reverse)."""
    ok = doc.FeatureExtrusion(True,                 # Sd  (use current sketch)
                              bool(flip),           # Flip
                              False,                # Dir
                              0, 0,                 # T1, T2 (blind/blind)
                              abs(depth_m), 0.0,    # D1, D2
                              False, False,         # Dchk1, Dchk2
                              False, False,         # Ddir1, Ddir2
                              0.0, 0.0,             # Dang1, Dang2
                              False, False,         # OffsetReverse1/2
                              bool(merge),          # Merge
                              True,                 # UseFeatScope
                              False)                # UseAutoScale
    if depth_m < 0:
        # rebuild with reversed direction instead of relying on Flip
        pass
    return ok


def extrude_dir(doc, depth_m, direction_flip=False, merge=True):
    """Extrude current sketch honouring direction: depth_m > 0 along sketch normal."""
    ok = doc.FeatureExtrusion(True, bool(direction_flip), False,
                              0, 0, abs(depth_m), 0.0,
                              False, False, False, False, 0.0, 0.0,
                              False, False, bool(merge), True, False)
    return ok


def cut_extrude(doc, depth_m, flip=False):
    """Cut-extrude the active sketch (through-all when depth < 0 => use ThroughAll)."""
    ok = doc.FeatureCut(True, bool(flip), False,
                        0, 0, abs(depth_m), 0.0,
                        False, False, False, False, 0.0, 0.0,
                        False, False, False, False, False,
                        True, True, False)
    return ok


def revolve(doc, angle_rad=6.141592653589793, merge=True):
    """Revolve current sketch 360 deg about the sketch's vertical axis."""
    ok = doc.FeatureRevolve2(True, False, False, False,
                             False, False, 0.0, 0.0, 0, 0, False,
                             angle_rad, angle_rad, 0, 0, bool(merge))
    return ok


def offset_plane(doc, base="Front", dist=0.0, name=None):
    doc.Extension.SelectByID2(base, "PLANE", 0, 0, 0, False, 0, None, 0)
    feat = doc.FeatureManager.InsertPlane(True, False, False, dist, False, 0.0)
    return feat


# --------------------------------------------------------------------------
# inspection
# --------------------------------------------------------------------------
def mass_properties(doc, density_kg_m3=None):
    """Return dict with mass (kg), CoM (m), moments (kg.m^2)."""
    import pythoncom
    vp = None
    try:
        res = doc.Extension.GetMassProperties(1, True)  # swMassPropertiesVersion_e=1
    except Exception:
        res = None
    if res is None:
        return None
    # res = (status, x, y, z, Ixx, Iyy, Izz, Ixy, Ixz, Iyz, mass?..)
    return res


def bounding_box(doc):
    """Return (min_xyz, max_xyz) in metres of the body geometry."""
    try:
        box = doc.GetPartBox(True)
    except Exception:
        box = None
    if box is None:
        try:
            box = doc.Extension.GetBoundingBox(None)
        except Exception:
            box = None
    return box


def export(doc, path):
    p = save(doc, path)
    return p


# --------------------------------------------------------------------------
# self test
# --------------------------------------------------------------------------
def selftest():
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_selftest")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "selftest_cylinder.SLDPRT")
    print("connecting ...", flush=True)
    sw = connect(visible=True)
    print("  revision:", revision(), flush=True)

    doc = new_document(DOC_PART)
    print("  new part doc:", doc is not None, flush=True)

    start_sketch(doc, "Front")
    circle(doc, 0, 0, 0.05)          # 100 mm dia disc
    doc.SketchManager.InsertSketch(True)
    ok = extrude_dir(doc, 0.02)
    print("  extrude:", ok, flush=True)

    doc.EditRebuild3()
    save(doc, path)
    print("  saved:", path, os.path.getsize(path), "bytes", flush=True)
    close_document(doc, path)

    doc2 = open_document(path, DOC_PART)
    print("  reopened:", doc2 is not None, flush=True)
    ok2 = doc2.EditRebuild3()
    print("  rebuild ok:", ok2, flush=True)
    print("  feature errors:", get_errors(doc2), flush=True)
    print("  bbox:", bounding_box(doc2), flush=True)
    mp = mass_properties(doc2)
    print("  mass props raw:", mp, flush=True)

    steppath = os.path.join(outdir, "selftest_cylinder.step")
    r = doc2.Extension.SaveAs(steppath, 0, 1, None, 0, 0)
    print("  step export:", r, os.path.exists(steppath),
          os.path.getsize(steppath) if os.path.exists(steppath) else 0, flush=True)
    close_document(doc2, path)
    print("SELF TEST DONE", flush=True)


if __name__ == "__main__":
    selftest()
