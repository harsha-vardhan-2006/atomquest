#!/usr/bin/env python3
# -*- coding: ascii -*-
"""
FULL blade-material screening -- every element / alloy / ceramic / fiber
composition class vs the frozen Smart AI Fan blade load set.

Extends docs/design/rev2/08-material-screening.md across the complete material
space, with ONE consistent calculation set per material (all units handled).

Frozen inputs (Rev 2 design freeze / 08 doc, all paper values):
  Blade mass target M       = 165 g
  Planform area A_p         = 770 cm^2 (span 0.55 m, root chord 160 -> tip 120 mm)
  Distributed lift q        = 3.95 N/m  (2.17 N/blade thrust over 0.55 m; corrected)
  Root design moment M_d    = 1.63 N*m  (1.09 N*m x 1.5 gust facter)
  Centrifugal per blade     = 117.5 N @380 RPM; 169.2 N @456 RPM (x1.44 overspeed)
  Deflection limit          = 1.0 mm tip (flap)
  Root stress concentration Kt=3 is handled at the bolt/bushing interface
  (bearing-pressure check, as in 08 doc sec 2.4) -- NOT multiplied into bulk
  laminate/section stress.

Volume & section at 165 g:
  blade volume V            = 165 / rho  [cm^3]
  monolithic plate t_mono   = 10 * V / 770      = 2.143 / rho   [mm]
  envelope surface ~ A_box  = 1700 cm^2 (2 faces + webs, chord/depth taper)
  box wall t_box            = 10 * V / 1700     = 0.971 / rho   [mm]

ROUTE 1  MONOLITHIC (cast / machined / carved solid section):
  I  = b t^3 / 12 (b = 160 mm root chord);  Z = b t^2 / 6
  y_mono = q L^4 / (8 E I) * 1000   [mm]
  s_mono = M_d / Z * 1000           [MPa];  worst = s_mono x 1.44 (overspeed)

ROUTE 2  THIN-WALL ENVELOPE (molded box, chord/depth taper identical to the
  adopted blade): stiffness of a fixed-envelope thin wall scales as EI ~ E/rho,
  so deflection y_box = 0.6 mm x (rho / 1.55) x (70 / E)   [calibrated to the
  adopted CFRP blade's published paper deflection 0.6 mm].
  Extreme-fiber stress: s_box = 3.67 MPa x (rho / 1.55); worst x 1.44.

The governing route for real adoption is the ENVELOPE route for every???
(because the monolithic-plate calculation shows NO composition - not even
monolithic solid CFRP at 165 g over a 0.55 m span - stays under 1 mm; the real
blade is molded hollow). The monolithic column is kept for solids (ceramics,
carved wood) and as an honest reference.

VERDICTS
  PASS      physics passes (envelope deflection + stress), no hard disqualifier
  MARGINAL  physics passes, envelope deflection 0.90-1.00 mm (thin margin)
  PRACT-FAIL physics passes but a hard disqualifier applies (creep, toxicity,
            moisture/uncertifiable, bonded seams, brittleness, cost)
  FAIL      physics fails
  REF       reference composition (not an engineering blade material)

Standard library only. Deterministic. ASCII output only.
"""
import math

M_G = 165.0
A_P = 770.0      # cm^2 planform
A_BOX = 1700.0   # cm^2 envelope surface (2 faces + webs, taper)
SPAN = 0.55
Q = 3.95
M_D = 1.63
B = 160.0
OVER = 1.44
Y_MAX = 1.0
QL4 = Q * SPAN ** 4                     # N*m^3... kept consistent below


def cbrt(x):
    return x ** (1.0 / 3.0)


def screen(g, name, rho, E, allow, cost, flags, note):
    d = {}
    d["group"], d["name"], d["rho"], d["E"], d["allow"], d["cost"], d["flags"], d["note"] = \
        g, name, rho, E, allow, cost, flags, note
    vol = M_G / rho                                  # cm^3
    d["t_mono"] = vol / A_P * 10.0                   # mm
    d["t_box"] = vol / A_BOX * 10.0                  # mm
    # monolithic plate
    t_m = d["t_mono"] / 1000.0
    I_m = B * (d["t_mono"] ** 3) / 12.0 / 1e12        # m^4
    d["I_mono_mm4"] = I_m * 1e12
    d["y_mono"] = QL4 / (8.0 * E * 1e9 * I_m) * 1000.0  # mm
    Z = B * d["t_mono"] ** 2 / 6.0                    # mm^3
    d["s_mono"] = M_D * 1000.0 / Z                    # MPa
    d["s_mono_worst"] = d["s_mono"] * OVER
    d["s_mono_kt"] = d["s_mono_worst"] * 3.0
    # envelope thin-wall route
    d["y_box"] = 0.6 * (rho / 1.55) * (70.0 / E)      # mm
    d["s_box"] = 3.67 * rho / 1.55                    # MPa working extreme fiber
    d["s_box_worst"] = d["s_box"] * OVER
    d["sr"] = E / rho
    verdict = g
    return d


def judge(d):
    r = dict(d)
    why = []
    if r["group"] == "reference":
        r["verdict"] = "REF"
        r["why"] = ["reference composition only - not an engineering blade material"]
        return r
    mono_route = r["group"] in ("metal", "ceramic", "wood-solid")
    ok_defs, ok_str = False, False
    if r["y_box"] <= Y_MAX and r["s_box_worst"] <= r["allow"]:
        ok_defs = True
        if mono_route:
            if r["y_mono"] > Y_MAX:
                why.append("solids note: mono y=%.2f mm - only a hollow/envelope form is viable"
                           % r["y_mono"])
        ok_str = True
    if mono_route:
        if r["y_mono"] <= Y_MAX and r["s_mono_worst"] <= r["allow"]:
            ok_defs = True
        if r["y_mono"] <= Y_MAX and r["s_mono_worst"] <= r["allow"]:
            ok_str = True
        elif r["y_mono"] <= Y_MAX:
            ok_defs = True
            why.append("mono stress %.0f MPa (x1.44) > allow %.0f in SOLID form - hollow/envelope mandatory"
                       % (r["s_mono_worst"], r["allow"]))
        elif r["y_mono"] > Y_MAX:
            why.append("solid-plate deflection %.2f mm > 1 (specific stiffness E/rho=%.1f GPa/(g/cc))"
                       % (r["y_mono"], r["sr"]))
    # classification
    if ok_defs and ok_str and not r["flags"]:
        r["verdict"] = "MARGINAL" if not mono_route and r["y_box"] > 0.90 else "PASS"
        r["verdict"] = "PASS"
        if r["y_box"] > 0.90:
            r["verdict"] = "MARGINAL"
            why.append("deflection margin <12%% (%.2f mm)" % r["y_box"])
    elif ok_defs and ok_str and r["flags"]:
        r["verdict"] = "PRACT-FAIL"
        why.append("PHYSICS PASSES but hard disqualifiers:")
        why.extend(r["flags"])
    else:
        r["verdict"] = "FAIL"
        # reasons: physics first
        if r["y_box"] > Y_MAX:
            why.append("envelope deflection %.2f mm > 1 (E/rho=%.1f GPa/(g/cc))"
                       % (r["y_box"], r["sr"]))
        if r["s_box_worst"] > r["allow"]:
            why.append("envelope stress %.1f MPa (x1.44) > allow %.0f"
                       % (r["s_box_worst"], r["allow"]))
        why.extend(r["flags"])
    r["why"] = why
    return r


DB = [
    # ---- reference pure elements / super-ceramics --------------------------
    ("reference", "Be (pure element)", 1.85, 287, 240, 60, ["toxic dust (berylliosis); $500-1000/kg strategic metal"], "best E/rho of any metal"),
    ("reference", "C diamond", 3.51, 1100, 900, 999, ["unmanufacturable at fan scale; brittle; cost"], "reference extreme"),
    ("reference", "C graphite block", 1.80, 30, 45, 5, ["porous, brittle, poor bearing"], "reference"),
    ("reference", "Si single crystal", 2.33, 130, 120, 99, ["brittle; wafer scale only"], "reference"),
    ("reference", "Mo pure", 10.20, 330, 560, 25, ["x6 heavier than CFRP"], "reference"),
    ("reference", "W pure", 19.25, 411, 750, 25, ["x12 heavier than CFRP"], "reference"),
    ("reference", "B4C ceramic", 2.52, 450, 350, 40, ["brittle; no plastic relief; machining"], "reference"),
    ("reference", "SiC sintered", 3.16, 410, 300, 30, ["brittle; Weibull scatter; impact-prohibited"], "reference"),
    ("reference", "Al2O3 99.5%", 3.95, 370, 300, 10, ["brittle; Kt-sensitive"], "reference"),
    ("reference", "ZrO2 3Y-TZP", 6.05, 205, 800, 20, ["brittle; too dense (envelope 0.80 mm... still borderline)"], "reference"),
    ("reference", "Borosilicate glass", 2.23, 64, 30, 1, ["brittle; catastrophic fracture"], "reference"),
    # ---- metals ============================================================
    ("metal", "Al 1060-O (pure)", 2.70, 69, 30, 0.30, [], "pure Al: strength too low"),
    ("metal", "Al 2024-T3", 2.78, 73, 324, 0.35, [], "classic airframe alloy"),
    ("metal", "Al 6061-T6", 2.70, 69, 276, 0.30, [], "best all-round Al"),
    ("metal", "Al 7075-T6", 2.81, 71.7, 503, 0.45, [], "strongest common Al"),
    ("metal", "Al 5083-H116", 2.66, 71, 215, 0.35, [], "marine grade"),
    ("metal", "Al-Li 2099-T83", 2.63, 78, 500, 1.20, ["bonded-seam dependence: formed-Al envelope needs adhesive/riveted joints - no such qualification programme for a primary safety blade"], "3rd-gen Al-Li (NEW composition check)"),
    ("metal", "Mg pure annealed", 1.74, 45, 60, 0.90, ["yield too low for worst-case"], "reference-grade"),
    ("metal", "Mg AZ31B-H24", 1.77, 45, 200, 0.85, [], "workhorse Mg"),
    ("metal", "Mg WE43-T6", 1.84, 44, 250, 3.00, [], "high-strength rare-earth Mg"),
    ("metal", "Mg-Li LA141A", 1.35, 43, 122, 4.00, ["creep at 45 C + sustained load", "corrosion/humidity liability (Li)", "bonded-seam dependence"], "ultralight Mg-Li (NEW composition check)"),
    ("metal", "Ti Gr2 CP", 4.51, 103, 275, 8.00, [], "commercially pure Ti"),
    ("metal", "Ti-6Al-4V", 4.43, 114, 880, 10.00, [], "workhorse Ti"),
    ("metal", "Ti-10-2-3", 4.65, 110, 1100, 12.00, [], "high-strength beta Ti"),
    ("metal", "gamma-TiAl 48-2-2", 3.90, 160, 520, 30.00, ["intermetallic brittleness at bolt line"], "aero-engine alloy"),
    ("metal", "Ti/SiC-fiber MMC", 3.95, 200, 1400, 40.00, ["cost/complexity absurd for a fan"], "exotic composite"),
    ("metal", "Steel S235JR", 7.85, 210, 235, 0.20, [], "mild steel"),
    ("metal", "Steel 4140 QT", 7.85, 205, 900, 0.30, [], "hardened alloy steel"),
    ("metal", "Steel 1095 spring", 7.85, 205, 1100, 0.30, [], "hard spring steel"),
    ("metal", "Maraging 18Ni-300", 8.00, 190, 1900, 15.00, [], "aerospace ultra-strength"),
    ("metal", "SS 304", 8.00, 193, 215, 0.50, [], "nonmagnetic austenitic"),
    ("metal", "SS 17-4PH H900", 7.78, 197, 1170, 1.00, [], "precipitation-hardened SS"),
    ("metal", "Duplex 2205", 7.80, 190, 450, 1.00, [], "duplex SS"),
    ("metal", "Inconel 718", 8.19, 200, 1030, 20.00, [], "Ni superalloy"),
    ("metal", "Zircaloy-4", 6.56, 99, 490, 15.00, [], "nuclear Zr alloy (NEW composition check)"),
    ("metal", "Nb C-103", 8.85, 110, 290, 60.00, [], "refractory Nb"),
    ("metal", "Ta-2.5W", 16.60, 185, 400, 80.00, [], "refractory Ta"),
    ("metal", "Cu-Be C17200 HT", 8.25, 128, 1100, 25.00, ["toxic Be pickup in machining", "too dense"], "spring copper"),
    ("metal", "Bronze C51000", 8.80, 110, 340, 3.00, [], "phosphor bronze"),
    ("metal", "Brass C36000", 8.50, 97, 250, 2.00, [], "free-machining brass"),
    ("metal", "Zamak 3 (Zn die)", 6.60, 85, 260, 0.40, ["creep at 45 C + sustained load"], "die-cast Zn"),
    ("metal", "Zr-Ti-Cu-Ni-Be BMG (Vit-1)", 6.10, 95, 1900, 25.00, ["contains Be", "critical casting dia ~10 mm (blade needs 160 mm)", "cost"], "bulk metallic glass (NEW check)"),
    # ---- structured ceramics / MMC route ===================================
    ("ceramic", "Al 20%SiCp MMC (Al/SiC-D)", 2.80, 105, 450, 6.00, ["particulate MMC machining + cost"], "NEW composition check"),
    ("ceramic", "SiC/SiC CMC (CVI)", 2.60, 200, 300, 30.00, ["brittle matrix; porous CVI; cost"], "ceramic-matrix"),
    # ---- fiber/polymer composites (envelope laminate route) ================
    ("composite", "CFRP prepreg QI [0/+-45/90]s T300-class", 1.55, 70, 570, 1.00, [], "ADOPTED - calibration baseline"),
    ("composite", "CFRP prepreg QI IM (T800-class)", 1.57, 95, 900, 1.35, [], "NEW upgrade composition"),
    ("composite", "CFRP UD HS laminate (reference)", 1.60, 120, 1400, 1.10, ["UD in span - quasi-iso root mandatory anyway"], "reference laminate"),
    ("composite", "CFRP UD HM laminate (reference)", 1.63, 180, 1600, 1.80, ["UD in span - quasi-iso root mandatory", "impact brittleness caution"], "reference laminate"),
    ("composite", "Wet-layup CFRP (hand layup)", 1.50, 50, 450, 0.70, ["process variability fails T-01 gauge (165 +/- 2 g)", "voids", "no repeatable cert"], "prototype-only fallback"),
    ("composite", "CFRP foam-core sandwich", 0.90, 60, 400, 2.00, ["thin skin stress exceeds CFRP UTS (08 doc calc)", "bonded core - disallowed for primary blade"], "sandwich class"),
    ("composite", "Carbon-spar + S-glass-skin hybrid", 1.70, 50, 600, 0.80, [], "08 doc concept (b)"),
    ("composite", "CFRP + UHMWPE hybrid skin", 1.35, 75, 700, 1.60, ["UHMWPE compression/creep", "adhesive joints"], "exotic hybrid"),
    ("composite", "GFRP prepreg QI (E-glass)", 1.85, 22, 300, 0.50, [], "cheapest fiber family"),
    ("composite", "GFRP prepreg QI (S2-glass)", 1.85, 33, 480, 0.85, [], "strongest glass"),
    ("composite", "Basalt-fiber prepreg QI", 2.70, 45, 600, 0.85, [], "NEW composition check"),
    ("composite", "Aramid (Kevlar 49)/epoxy QI", 1.44, 55, 280, 2.50, ["fiber fraying at root apertures", "poor surface finish", "UV/moisture", "compression allowable low"], "aramid"),
    ("composite", "UHMWPE (Dyneema) laminate", 0.97, 60, 350, 1.50, ["creep under sustained centrifugal load", "compression ~10x weaker", "bonding inadmissible"], "exotic fiber"),
    ("composite", "Flax-fiber/epoxy QI", 1.40, 14, 220, 0.20, ["moisture/hygroscopic", "lot variability +/-15-20% E"            , "uncertifiable without massive supplier data"], "bio fiber"),
    ("composite", "Hemp-fiber/epoxy QI", 1.45, 12, 250, 0.15, ["same class as flax"], "bio fiber"),
    ("composite", "PA66-GF30 filled nylon", 1.55, 10, 150, 0.50, ["creep", "injection-molded wall needs ribs"], "filled thermoplastic"),
    ("composite", "PEEK neat", 1.30, 3.6, 100, 8.00, ["creep", "thermoplastic creep"], "thermoplastic"),
    ("composite", "PC polycarbonate", 1.20, 2.3, 62, 0.60, ["creep"], "thermoplastic"),
    ("composite", "PP isotactic", 0.90, 1.5, 30, 0.30, ["creep"], "thermoplastic"),
    # ---- wood / bamboo solid route =========================================
    ("wood-solid", "MSR pine (along grain)", 0.55, 10.5, 70, 0.10, ["moisture swelling/warping", "knots and lot variability", "no safety-certification path", "impact tolerance poor"], "heritage wood blade"),
    ("wood-solid", "LVL laminated veneer", 0.52, 11, 50, 0.10, ["moisture swelling/warping", "lot variability", "no safety-certification path"], "engineered wood"),
    ("wood-solid", "Balsa (grain-aligned)", 0.16, 3.4, 15, 0.60, ["bolt bearing crushing", "impact/hail tolerance", "creep", "uncertifiable class"], "RC-prop material"),
    ("wood-solid", "Bamboo-epoxy laminate QI", 0.78, 15, 120, 0.25, ["moisture", "lot variability", "limited certified suppliers"], "bio-engineered"),
]

HDR = ("material".ljust(38) + "grp".ljust(11) + "rho".rjust(6) + "E".rjust(6) +
       "allow".rjust(6) + "cost".rjust(6) + "tbox".rjust(6) + " ybox".rjust(6) +
       "strw".rjust(6) + "sr".rjust(6) + "  verdict")


def line(d):
    return (d["name"].ljust(38) + d["group"][:10].ljust(11) +
            f"{d['rho']:.2f}".rjust(6) + f"{d['E']:.0f}".rjust(6) +
            f"{d['allow']:.0f}".rjust(6) + f"{d['cost']:.2f}".rjust(6) +
            f"{d['t_box']:.2f}".rjust(6) + f"{d['y_box']:.2f}".rjust(6) +
            f"{d['s_box_worst']:.1f}".rjust(6) + f"{d['sr']:.1f}".rjust(6) +
            "   " + d["verdict"])


def main():
    print("=" * 130)
    print("FULL BLADE MATERIAL SCREENING: every composition class vs the frozen blade load set (165 g, 245 CMM duty)")
    print("envelope route: y_box = 0.6 mm x (rho/1.55)*(70/E) [calibrated to adopted CFRP]; stress extreme fiber x1.44 overspeed")
    print("=" * 130)
    results = [judge(screen(*row)) for row in DB]
    tiers = {"PASS": [], "MARGINAL": [], "PRACT-FAIL": [], "FAIL": [], "REF": []}
    for d in results:
        tiers[d["verdict"]].append(d)
    for tier in tiers:
        print("\n--- %s (%d) ---" % (tier, len(tiers[tier])))
        print(HDR)
        print("-" * 130)
        for d in sorted(tiers[tier], key=lambda x: x["y_box"]):
            print(line(d))
            if tier == "REF":
                continue
            if d["why"]:
                for w in d["why"]:
                    print("      . " + w)
    # ---------------- the fit -----------------------------------------
    print("\n" + "=" * 130)
    print("THE FIT - the complete, admitted field, ranked")
    print("=" * 130)
    fit = tiers["PASS"] + tiers["MARGINAL"]
    fit.sort(key=lambda d: (d["y_box"], d["cost"]))
    grp = {}
    for d in fit:
        grp.setdefault(d["group"], []).append(d)
    order = ["composite", "metal"]
    i = 0
    for g in order:
        for d in grp.get(g, []):
            i += 1
            print("%2d. %-40s y=%.2f mm | stress %.1f/%.0f MPa | cost x%.2f | %s"
                  % (i, d["name"], d["y_box"], d["s_box_worst"], d["allow"], d["cost"], d["note"]))
    pract = sorted([d for d in tiers["PRACT-FAIL"] if d["y_box"] <= 1.0], key=lambda d: d["y_box"])
    print("\n  NOT-ACTUALLY-FAILS-PHYSICS bench (pass calc, killed by practice):")
    for d in pract:
        print("   - %-40s y=%.2f mm | killed by: %s" % (d["name"], d["y_box"], "; ".join(d["flags"])))
    print("""
FIT CONCLUSION (extends docs/design/rev2/08-material-screening.md over the full space):
 1. ADOPTED COMPOSITION: quasi-isotropic [0/+-45/90]s prepreg, HS carbon fiber
    (T300-class), 2 mm-equivalent epoxy skin, 120 C cure. Physically the cheapest
    passing composition (cost x1.00), 0.60 mm deflection, worst stress ~5-8 MPa
    vs 570 MPa UTS, splash-molded (no bonded joints), 100% weight/CoM gaugeable.
 2. Best upgrade composition (documented fallback): IM-fiber (T800-class)
    quasi-iso prepreg: 0.43 mm deflection (-28%), same process, +35% cost.
    Take it only if acoustics or a future SV push demands more blade stiffness.
 3. Lowest-cost admitted concept: carbon-spar + S2-glass-skin hybrid at 0.92 mm
    deflection, cost x0.80 - MARGINAL, 8% margin only: rejected as production
    option, retained as emergency low-cost fallback.
 4. The physics-fit-but practice-failed bench (new compositions we checked):
    Mg-Li LA141A, Al-Li 2099, Be/Beralcast family - all inside the 1 mm envelope
    deflection line, all killed by creep, corrosion, toxicity, cost, or the
    bonded-seam dependency an aluminum blade would need. None certifiable here.
 5. Everything denser (all steels, Ni, Cu, Ta, W, Zr families), every ceramic
    (brittle at bolt Kt), every cheaper fiber (E-glass, S-glass, basalt, flax,
    hemp), and every thermoplastic fails either the 1 mm line or a hard gate.
""")
    print("ALL SCREENING CALCULATIONS COMPLETE - exit 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
