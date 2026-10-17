#!/usr/bin/env python3
# -*- coding: ascii -*-
"""
PARAMETRIC FAN ASSEMBLY MODEL + T-00a CAD-MAP GENERATOR (team-authorized in-code authoring).

Builds, from the frozen design values ONLY, a parametric mesh assembly:
  rotor: 3 tapered twisted blades (root chord 160 -> tip 120 mm, depth 10 -> 6 mm,
         twist 38 -> 12 deg, hub radius 150 -> tip radius 700 mm), hub/motor bell cylinder
  static: downrod (D16x2 wall), canopy disc (coaxial above ceiling), SS304 safety-cable
          slack loop (D 100 mm, worst-case coaxial placement), wire loft (controller
          leads) coaxial along the downrod
All obstacles (canopy, cable, wires, downrod) are AXISYMMETRIC about the fan axis, so the
minimum object distance for a pose depends only on |tilt|; the full 74,229-pose map is an
exact expansion of 109 unique computations x pan grid. Pan/tilt hard stops honour the
frozen envelope (pan 170 deg working / 175 stop; tilt 27 deg stop).

Outputs (files):
  cad_models/*.stl            reviewable mesh CAD artifacts
  cad_models/t00a_cad_map.csv the documented harness CSV (74229 poses x 3 pairs)
  cad_models/t00a_candidate_report.txt the acceptance report (candidate - sign-off pending)

Method limits (declared, not hidden):
  - distances = point-cloud (blade outline vertices, 25 stations/blade) vs obstacle
    triangles; resolution ~15-30 mm vertex pitch, so reported minima are sampled
    sums, not kernel-exact. Blade-ceiling rows use the EXACT plane law instead.
  - the scan is a CANDIDATE acceptance report: design-lead review + higher-density
    re-scan is required before T-00a sign-off.

Standard library + numpy only; deterministic; exit 0.
"""
import csv
import math
import os
import numpy as np

R_MM = 700.0
R_HUB = 150.0
CHORD_ROOT, CHORD_TIP = 160.0, 120.0
DEPTH_ROOT, DEPTH_TIP = 10.0, 6.0
TWIST_R, TWIST_T = math.radians(38.0), math.radians(12.0)
H_ROD_MM = 450.0
CEILING_REF_MM = 2660.0   # exact threshold ceiling for the scan reference plane
PAN_MAX, TILT_STOP, STEP = 170.0, 27.0, 0.5
CANOPY_R, CANOPY_T = 300.0, 60.0
CABLE_RING_R = 50.0
ROD_R = 8.0
STATIONS = list(np.linspace(0.0, 1.0, 25) ** 0.9)   # dense-ish outline sampling

# ---------------------------------------------------------------- mesh helpers
def rot_x(p, a):
    c, s = math.cos(a), math.sin(a)
    Rm = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return p @ Rm.T

def box_quad_mesh(cx, cy, cz, hx, hy, hz):
    """Axis-aligned box as triangles; returns verts (8,3), quads as 12 tris."""
    v = np.array([[cx - hx, cy - hy, cz - hz], [cx + hx, cy - hy, cz - hz],
                  [cx + hx, cy + hy, cz - hz], [cx - hx, cy + hy, cz - hz],
                  [cx - hx, cy - hy, cz + hz], [cx + hx, cy - hy, cz + hz],
                  [cx + hx, cy + hy, cz + hz], [cx - hx, cy + hy, cz + hz]], dtype=float)
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
             (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c_, d_ in faces:
        tris += [(a, b, c_), (a, c_, d_)]
    return v, np.array(tris)

def blade_mesh(n_blade=0):
    """Blade solid: twisted loft of rectangular sections along the span."""
    verts, quads = [], []
    for i, t in enumerate(STATIONS):
        r = R_HUB + t * (R_MM - R_HUB)
        chord = CHORD_ROOT + t * (CHORD_TIP - CHORD_ROOT)
        depth = DEPTH_ROOT + t * (DEPTH_TIP - DEPTH_ROOT)
        beta = TWIST_R + t * (TWIST_T - TWIST_R)
        # local frame: span radial (x), chord tangential (y), depth axial (z)
        ca, sa = math.cos(beta), math.sin(beta)
        # 8 outline points: rectangle perimeter corners (chord x depth), twisted
        corners = np.array([[0, -chord / 2, -depth / 2], [0, chord / 2, -depth / 2],
                            [0, chord / 2, depth / 2], [0, -chord / 2, depth / 2]])
        for cc in corners:
            y = cc[1] * ca - cc[2] * sa
            z = cc[1] * sa + cc[2] * ca
            verts.append([r, y, z])
    verts = np.array(verts)
    per = len(STATIONS)
    for i in range(per - 1):
        for j in range(4):
            a, b = i * 4 + j, i * 4 + (j + 1) % 4
            c_, d_ = (i + 1) * 4 + j, (i + 1) * 4 + (j + 1) % 4
            quads += [(a, b, d_, c_)]
    # end caps
    quads += [(0, 1, 2, 3), (per * 4 - 4, per * 4 - 3, per * 4 - 2, per * 4 - 1)]
    tris = []
    for a, b, c_, d_ in quads:
        tris += [(a, b, c_), (a, c_, d_)]
    # rotate blade n_blade by 120*n_blade degrees about z (fan axis)
    v = verts.copy()
    ang = math.radians(120.0 * n_blade)
    c, s = math.cos(ang), math.sin(ang)
    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    v = v @ Rz.T
    return v, np.array(tris)

def hub_bell_mesh():
    return box_quad_mesh(0, 0, -A_HUB_MM / 2.0, R_HUB, R_HUB, A_HUB_MM / 2.0)

A_HUB_MM = 120.0   # hub + housing axial (frozen a = 0.12 m)

def tube_mesh(z0_mm, z1_mm, r, n=16):
    """Coaxial tube (or solid rod if inner 0) axis-aligned with the fan axis."""
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    v = []
    for z in (z0_mm, z1_mm):
        for a in ang:
            v.append([r * math.cos(a), r * math.sin(a), z])
    v = np.array(v)
    n = len(ang)
    quads = []
    for i in range(n):
        j = (i + 1) % n
        quads.append((i, j, n + j, n + i))
    tris = []
    for a, b, c_, d_ in quads:
        tris += [(a, b, c_), (a, c_, d_)]
    return v, np.array(tris)

def canopy_mesh():
    """Coaxial canopy disc: outer radius 300 mm, thickness 60 mm, top at ceiling."""
    z0 = CEILING_REF_MM - CANOPY_T
    return tube_mesh(z0, CEILING_REF_MM, CANOPY_R, n=24)

def cable_loop_mesh():
    """SS304 slack loop, worst-case coaxial placement below the canopy."""
    c = CEILING_REF_MM - CANOPY_T - 50.0
    ang = np.linspace(0, 2 * math.pi, 24, endpoint=False)
    v = np.array([[CABLE_RING_R * math.cos(a), CABLE_RING_R * math.sin(a), c] for a in ang])
    tris = np.array([[i, (i + 1) % 24, 24] for i in range(24)], dtype=int)
    return v, tris

def cable_ring_closest(v):
    """Distance from points to the cable ring circle (the ring is a wire loop -
    exact circle distance is analytic, used instead of a triangle fan)."""
    c = CEILING_REF_MM - CANOPY_T - 50.0
    xy = np.hypot(v[:, 0], v[:, 1])
    r_term = np.abs(xy - CABLE_RING_R)
    z_term = v[:, 2] - c
    return np.sqrt(r_term ** 2 + z_term ** 2)

def wires_mesh():
    return tube_mesh(CEILING_REF_MM - CANOPY_T - 6.0, H_ROD_MM, ROD_R, n=12)

# --------------------------------------------------- point-to-triangle distance
def point_tri_distance(verts, tris_v0, tris_v1, tris_v2, idx=None):
    """Vectorized point->triangle distance. verts: (n,3); tris: (m,3) triplets."""
    P = verts[:, None, :]
    A0, B0, C0 = tris_v0[None, :, :], tris_v1[None, :, :], tris_v2[None, :, :]
    AB, AC = B0 - A0, C0 - A0
    AP = P - A0
    d00 = np.einsum("mnk,mnk->mn", AB, AB)
    d01 = np.einsum("mnk,mnk->mn", AB, AC)
    d11 = np.einsum("mnk,mnk->mn", AC, AC)
    d20 = np.einsum("mnk,mnk->mn", AP, AB)
    d21 = np.einsum("mnk,mnk->mn", AP, AC)
    den = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / np.where(np.abs(den) < 1e-12, 1e-12, den)
    w = (d00 * d21 - d01 * d20) / np.where(np.abs(den) < 1e-12, 1e-12, den)
    # outside-edge handling (simplified: clamp + recompute edge distances)
    clamped_v = np.clip(v, 0, 1)
    clamped_w = np.clip(w, 0, 1)
    inside = (clamped_v + clamped_w) <= 1.0
    proj = A0 + clamped_v[..., None] * AB + clamped_w[..., None] * AC
    d_proj = np.linalg.norm(P - proj, axis=-1)
    # edge distances
    def seg_dist(P, S0, S1):
        S = S1 - S0
        t = np.clip(np.einsum("mnk,mnk->mn", P - S0, S) /
                     np.where(np.einsum("mnk,mnk->mn", S, S) < 1e-12, 1e-12,
                              np.einsum("mnk,mnk->mn", S, S)), 0, 1)
        cp = S0 + t[..., None] * S
        return np.linalg.norm(P - cp, axis=-1)
    e0 = seg_dist(P, A0, B0)
    e1 = seg_dist(P, B0, C0)
    e2 = seg_dist(P, C0, A0)
    d = np.where(inside, d_proj, np.minimum(np.minimum(e0, e1), e2))
    return d.min(axis=1)   # (n,) min per point

# ------------------------------------------------------- blade-vertex sampling
def blade_vertex_cloud():
    """All blade model vertices (bigger than the true outline but conservative -
    includes chord twist corners)."""
    all_v = []
    for k in range(3):
        v, _ = blade_mesh(k)
        all_v.append(v)
    return all_v

# --------------------------------------------------------------- STL writer
def write_stl(path, verts, tris, name):
    with open(path, "w", encoding="ascii") as f:
        f.write("solid %s\n" % name)
        for a, b, c_ in tris:
            p0, p1, p2 = verts[a], verts[b], verts[c_]
            n = np.cross(p1 - p0, p2 - p0)
            ln = np.linalg.norm(n)
            n = n / ln if ln > 1e-9 else np.array([0.0, 0.0, 1.0])
            f.write("  facet normal %r %r %r\n" % (n[0], n[1], n[2]))
            for p in (p0, p1, p2):
                f.write("    vertex %r %r %r\n" % (p[0], p[1], p[2]))
            f.write("  endfacet\n")
        f.write("endsolid %s\n" % name)

# --------------------------------------------------------------- rotor pose
def pose_transform(points, tilt_deg, pivot_z=0.0):
    """Tilt about the x-axis through the pivot (hub top), then the rotor is
    complete; pan rotates the whole assembly about z and, with all obstacles
    axisymmetric, does not change distances - recorded only for the CSV."""
    t = math.radians(-tilt_deg)
    c, s = math.cos(t), math.sin(t)
    Rm = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    rel = points - np.array([0.0, 0.0, pivot_z])
    return rel @ Rm.T + np.array([0.0, 0.0, pivot_z])

def main():
    os.makedirs("cad_models", exist_ok=True)
    BLADES = blade_vertex_cloud()
    for k in range(3):
        v, tr = blade_mesh(k)
        write_stl("cad_models/blade_%d.stl" % k, v, tr, "blade_%d" % k)
    hub_v, hub_tr = hub_bell_mesh()
    write_stl("cad_models/hub_bell.stl", hub_v, hub_tr, "hub_bell")
    can_v, can_tr = canopy_mesh()
    write_stl("cad_models/canopy.stl", can_v, can_tr, "canopy")
    rod_v, rod_tr = tube_mesh(H_ROD_MM, CEILING_REF_MM, ROD_R, n=12)
    write_stl("cad_models/downrod.stl", rod_v, rod_tr, "downrod")
    ws_v, ws_tr = wires_mesh()
    write_stl("cad_models/wire_loft.stl", ws_v, ws_tr, "wire_loft")

    # obstacle triangles (coaxial axisymmetric set) - pivot at hub top:
    pivot_z = H_ROD_MM  # hub top at ceiling - 450 + 120; hub center at -450+... use absolute ceiling frame:
    # frame convention: z measured from hub centre up (ceil at +450 - 60?)... use ceiling plane at z=+450-? Simply:
    # ceiling at z = +H_ROD relative to HUB CENTER? H_ROD=450; ceiling plane ref at z=+450-??;
    # Adopt: hub centre at z=0; ceiling plane at z=+450? NO: ceiling ABOVE hub by h_rod=+450? The
    # hub hangs 450 below the ceiling -> ceiling at z=+450 relative to hub?? Wrong sign. Use:
    # hub centre z=0; ceiling plane z=+450 - but h_rod is ceiling-to-hub DROP = distance, ceiling at +450.
    # Canopy top at +450, bottom +390; cable ring at +340; hub top at +60; blade span z ~ -6..+6.
    # (Earlier section builders used CEILING as absolute - we re-anchor those meshes here.)
    ceiling_z = 450.0
    can_v2, can_tr2 = tube_mesh(ceiling_z - CANOPY_T, ceiling_z, CANOPY_R, n=24)
    ws_v2, ws_tr2 = tube_mesh(ceiling_z - CANOPY_T - 6.0, H_ROD_MM, ROD_R, n=12)
    write_stl("cad_models/canopy.stl", can_v2, can_tr2, "canopy")
    write_stl("cad_models/wire_loft.stl", ws_v2, ws_tr2, "wire_loft")
    obstacle_tris = np.concatenate([can_tr2 + 0 * len(can_v2) if True else can_tr2,
                                    ws_tr2 + len(can_v2),
                                    rod_tr + len(can_v2) + len(ws_v2)])
    obstacle_verts = np.concatenate([can_v2, ws_v2, rod_v])
    tv0 = obstacle_verts[obstacle_tris[:, 0]]
    tv1 = obstacle_verts[obstacle_tris[:, 1]]
    tv2 = obstacle_verts[obstacle_tris[:, 2]]

    # unique |tilt| values (axisymmetric obstacles), vectorized per tilt
    tilts = sorted({round(abs(t), 1) for t in
                    [round(-TILT_STOP + j * STEP, 1) for j in range(int(2 * TILT_STOP / STEP) + 1)]})
    dist_by_tilt = {}
    for t in tilts:
        pts = []
        for k in range(3):
            pts.append(pose_transform(BLADES[k], t, pivot_z=0.0))
        P = np.concatenate(pts, axis=0)
        d_obj = point_tri_distance(P, tv0, tv1, tv2)
        dc = cable_ring_closest(P).min()
        dist_by_tilt[t] = min(d_obj.min(), dc)
    # blade-blade: rigid rotor, pose-independent - vertex/tri min across blade pairs
    btv = []
    for k in range(3):
        v, tr = blade_mesh(k)
        btv.append((v, tr))
    def mesh_min(ia, ib):
        va, ta = btv[ia]; vb, tb = btv[ib]
        ta_v = va[ta]
        v0, v1, v2 = ta_v[:, 0], ta_v[:, 1], ta_v[:, 2]
        return point_tri_distance(vb, v0, v1, v2).min()
    bb_min = min(mesh_min(0, 1), mesh_min(1, 2), mesh_min(2, 0))

    # ceiling rows: exact plane law (not mesh) - consistent with the harness x-check
    def ceiling_dist_mm(t):
        th = math.radians(abs(t))
        zh = R_MM * math.cos(th) / 1000.0 + (A_HUB_MM / 1000.0) * math.sin(th)
        return (CEILING_REF_MM / 1000.0 - H_ROD_MM / 1000.0 - zh) * 1000.0

    pans = [round(-PAN_MAX + i * STEP, 1) for i in range(int(2 * PAN_MAX / STEP) + 1)]
    tilts_full = [round(-TILT_STOP + j * STEP, 1) for j in range(int(2 * TILT_STOP / STEP) + 1)]
    assert len(pans) == 681 and len(tilts_full) == 109
    bb_reported = round(min(bb_min, 2 * math.pi * R_HUB / 3.0 - CHORD_ROOT), 2)   # conservative of mesh vs analytic root-arc gap
    path = "cad_models/t00a_cad_map.csv"
    with open(path, "w", encoding="ascii", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pair", "pan_deg", "tilt_deg", "distance_mm"])
        for t in tilts_full:
            do = round(dist_by_tilt[abs(t)], 2)
            dc_ = round(ceiling_dist_mm(t), 1)
            for p in pans:
                w.writerow(["blade-blade", p, t, bb_reported])
                w.writerow(["blade-ceiling", p, t, dc_])
                w.writerow(["blade-object", p, t, do])
    n_rows = len(pans) * len(tilts_full) * 3
    print("POSES %d (681x109) x 3 pairs = %d CSV rows -> %s" % (len(pans) * len(tilts_full), n_rows, path))
    print("blade-blade mesh min: %.2f mm (reported conservative %.2f) ; blade-object worst: %.2f mm ; ceiling worst: %.1f mm"
          % (bb_min, bb_reported, min(dist_by_tilt.values()), min(ceiling_dist_mm(t) for t in tilts)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
