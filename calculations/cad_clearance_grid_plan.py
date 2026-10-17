#!/usr/bin/env python3
# -*- coding: ascii -*-
"""
T-00a CAD clearance grid plan -- geometric acceptance reference.

Computes, from the frozen geometry (04-clearance / 06-test-plan T-00a):
  1. the exact scan grid size (pan x tilt poses),
  2. the lowest blade-tip drop z_low(theta) = R cos(t) + a sin(t), including
     the EXACT worst case at theta* = atan(a/R) (~9.74 deg) where
     z_low = sqrt(R^2 + a^2) (~0.7102 m) -- deeper than level (0.700 m),
     resolving the 1 cm tension in the 04 clearance rule,
  3. the corrected firmware tilt rule, which is BINARY:
       ceiling >= H_ROD + sqrt(R^2+a^2) + 1.50 = 2.660 m -> full +/-20 deg tilt
       2.650 <= ceiling < 2.660 m                               -> level only
        ceiling <  2.650 m                                      -> not qualified
     (no intermediate caps exist: every tilt in 0 < |theta| < ~19.8 deg dips
      deeper than level, so a ceiling that only just passes level cannot host
      any intermediate tilt either -- the old tiered 3.20/3.00/2.60 table was
      already superseded; this now also fixes the ~10 deg cap wording in 04.)
  4. assertion checks vs the published 04 numbers, then exit 0.

Standard library only, deterministic.
"""
import math

R = 0.70          # blade tip radius, m
A = 0.12          # hub + motor housing half-height, m (axial)
H_ROD = 0.45      # ceiling-to-hub drop, m
FLOOR_REQ = 1.50  # floor clearance rule, m
TILT_MAX = 20.0   # working tilt limit, deg
TILT_STOP = 27.0  # mechanical hard stop, deg
PAN_MAX = 170.0   # working pan limit, deg
STEP = 0.5        # deg, T-00a grid step
CEILINGS = [2.55, 2.65, 2.70, 2.85, 3.00]

def pan_points():
    return int(round((2.0 * PAN_MAX) / STEP)) + 1                 # 681

def tilt_points():
    return int(round((2.0 * TILT_STOP) / STEP)) + 1               # 109

def z_low(theta_deg):
    t = math.radians(theta_deg)
    return R * math.cos(t) + A * math.sin(t)

def worst_case():
    t_star = math.degrees(math.atan(A / R))       # ~9.74 deg
    return t_star, math.hypot(R, A)               # 0.7102 m

def min_ceiling_full_tilt():
    return H_ROD + math.hypot(R, A) + FLOOR_REQ   # 2.660 m

def classify_ceiling(ceiling):
    """Binary rule with exact-boundary tolerance; returns (label, cap_deg).
    Boundaries are inclusive: a ceiling that allows EXACTLY the level drop
    (budget == 0.700) qualifies for LEVEL ONLY; exact 2.6602 unlocks full tilt.
    """
    EPS = 1e-9
    budget = ceiling - H_ROD - FLOOR_REQ          # allowed z_low
    level = z_low(0.0)                            # 0.700
    peak = math.hypot(R, A)                       # 0.7102
    if budget < level - EPS:
        return ("NOT QUALIFIED - level clearance %0.2f m < %0.2f m even level"
                % (ceiling - H_ROD - level, FLOOR_REQ)), None
    if budget < peak - EPS:
        return ("LEVEL ONLY - cap = 0 deg (any 0<|theta|<~19.8 deg dips deeper)", 0.0)
    return ("full +/-20 deg working tilt", TILT_MAX)

def main():
    print("=" * 96)
    print("T-00a CAD CLEARANCE GRID PLAN -- geometric acceptance reference (paper-exact)")
    print("=" * 96)
    np_, nt = pan_points(), tilt_points()
    print(f"scan grid: pan -170.0..+170.0 deg step {STEP} -> {np_} points")
    print(f"           tilt -27.0..+27.0 deg step {STEP} -> {nt} points")
    print(f"           total poses {np_ * nt:,}  (3 blade-pairs checked per pose)")
    t_star, z_peak = worst_case()
    print(f"\nlowest-tip worst case: theta* = {t_star:.2f} deg (atan(a/R)); z_low* = {z_peak:.4f} m")
    print(f"  vs level z_low = {z_low(0.0):.4f} m and +/-20 deg z_low = {z_low(20.0):.4f} m")
    print("  worst drop is ~10 mm DEEPER than level -- the binding tilt is ~10 deg, not 0 or 20")
    print(f"\nbinary firmware rule (floor clearance >= {FLOOR_REQ} m, R={R}, a={A}, h_rod={H_ROD}):")
    print(f"  ceiling >= {min_ceiling_full_tilt():.3f} m -> full +-{TILT_MAX:.0f} deg tilt")
    print("  ceiling in [2.650, 2.660) -> LEVEL ONLY (cap 0 deg)")
    print("  ceiling < 2.650           -> not qualified for this installation")
    print("\n  ceiling | max allowed z_low | clearance verdict")
    for c in CEILINGS:
        label, cap = classify_ceiling(c)
        print(f"  {c:5.2f} m | {c - H_ROD - FLOOR_REQ:10.4f} m | {label}")
    print(f"\nEXACT THRESHOLD: unlimited tilt needs ceiling >= {min_ceiling_full_tilt():.3f} m")
    print("  ('2.65 passes everywhere' was ~1 cm short near theta ~ 10 deg; superseded)\n")
    print("acceptance thresholds (T-00a): blade-blade >= +1 mm; blade-ceiling >= 50 mm;")
    print("blade-object (cable loop, wires, canopy) >= 50 mm; scan reports worst-10 poses per pair.\n")
    print("T-17 note: arrested-tip height check must use the WORST-CASE theta* geometry.")
    # assertions vs published numbers and the corrected rule
    assert pan_points() == 681 and tilt_points() == 109, "grid must match 04 sect 6"
    assert abs(z_low(0.0) - 0.700) < 1e-3, "level drop must match 04 sect 2.1 (0.700 m)"
    assert abs(z_low(10.0) - 0.710) < 2e-3, "10 deg drop must match 04 sect 2.2 (0.710 m)"
    assert abs(z_low(20.0) - 0.699) < 1e-3, "20 deg drop must match 04 sect 2.2 (0.699 m)"
    assert 9.0 < t_star < 10.5, "worst-case tilt must sit near 10 deg"
    assert abs(min_ceiling_full_tilt() - 2.6602) < 1e-3, "exact threshold 2.660 m"
    assert classify_ceiling(2.55)[1] is None, "2.55 m: not qualified"
    assert classify_ceiling(2.65)[1] == 0.0, "2.65 m: level only (cap 0)"
    assert classify_ceiling(2.70)[1] == TILT_MAX, "2.70 m: full tilt"
    print("ASSERTIONS OK (grid 681x109; 0.700/0.710/0.699 m vs 04; peak 9.74 deg; caps: 2.55 none / 2.65 level / 2.70 full)")
    print("ALL T-00a GEOMETRY PLAN CALCULATIONS COMPLETE - exit 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
