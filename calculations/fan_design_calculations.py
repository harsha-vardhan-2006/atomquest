"""All headline design calculations for the Smart AI Fan (Track 1) — pure standard library.

Every calculation prints its formula, inputs (with assumptions), and output, then asserts
consistency with the figures quoted in the submission PDF so a judge can re-derive each number
by reading one screen of code. Nothing here is measured data; evidence status is stated per value.
"""

import math

MM = 1e-3
PI = math.pi


def rpm_to_rad_s(rpm):
    return rpm * 2.0 * PI / 60.0


def show(title, formula, inputs, value, unit, status):
    print(f"\n{title}")
    print(f"  formula : {formula}")
    for k, v in inputs.items():
        print(f"  input   : {k} = {v}")
    print(f"  output  : {value:g} {unit}  [{status}]")


# ---------------------------------------------------------------------------
# 1. Blade-tip speed vs the IS-benchmark 30 m/s cap
#    (30 m/s cap appears in IS 374:2019+Amd.1 treatment of ceiling-fan tip speed)
# ---------------------------------------------------------------------------
def tip_speed(rpm, diameter_m):
    omega = rpm_to_rad_s(rpm)
    return omega * diameter_m / 2.0


ts = tip_speed(380, 1.4)
show("1. Blade-tip speed at target top speed",
     "v_tip = omega * R ; omega = 2*pi*N/60",
     {"N": 380, "diameter": "1.4 m", "R": 0.7}, ts, "m/s", "calculated")
print("  check   : 30 m/s cap")
assert round(ts, 2) == 27.86, ts
assert ts < 30.0

hazard_ts = tip_speed(456, 1.4)
show("1b. Tip speed at 456 RPM (HAZARD CASE ONLY — never an operating target)",
     "v_tip = omega * R", {"N": 456, "R": 0.7}, hazard_ts, "m/s", "calculated")
assert round(hazard_ts, 1) == 33.4, hazard_ts
print("  note    : this is why 456 RPM is treated as a failure/hazard case, not a target.")


# ---------------------------------------------------------------------------
# 2. Rotor inertia and stored kinetic energy (moving-mass roll-up)
#    Mass roll-up is UNRECONCILED: component list sums 7.00 kg; the earlier stated
#    figure was 6.80 kg. Both are retained; energy is computed for the heavier pole.
# ---------------------------------------------------------------------------
def rotor_energy(inertia, rpm):
    omega = rpm_to_rad_s(rpm)
    return 0.5 * inertia * omega ** 2


I = 0.113  # kg*m^2, inertia estimate from CAD mass roll-up (assumption pending CAD sign-off)
e380 = rotor_energy(I, 380)
e456 = rotor_energy(I, 456)
show("2. Rotor stored energy at 380 RPM (design top speed)",
     "E = 0.5 * I * omega^2", {"I": "0.113 kg*m^2 (CAD estimate)", "N": 380}, e380, "J", "calculated from target masses")
print("  check   : PDF quotes 89.5 J")
assert abs(e380 - 89.5) < 0.2, e380
show("2b. Rotor stored energy at 456 RPM (hazard case)",
     "E = 0.5 * I * omega^2", {"I": "0.113 kg*m^2", "N": 456}, e456, "J", "calculated")
print("  check   : PDF quotes 128.8 J; blade-containment rating basis is 130 J -> thin margin")
assert abs(e456 - 128.8) < 0.2, e456
print("  RISK    : 128.8 J vs 130 J containment rating = thin margin; BLOCKED pending test basis and authorization.")
print("            Mass roll-up UNRECONCILED: 7.00 kg (component sum) vs 6.80 kg (earlier stated); both retained.")


# ---------------------------------------------------------------------------
# 3. Service value (indicative energy-efficiency check vs IS 374 requirement)
# ---------------------------------------------------------------------------
input_power_w = 28.3  # assumed total input power for the target operating point (assumption; not measured)
service_value = 245.0 / input_power_w  # m^3/min per W
show("3. Indicative service value",
     "SV = air_delivery / input_power", {"air_delivery": "245 m^3/min (IS 374 target)",
                                          "input_power": "28.3 W (assumed)"}, service_value, "m^3/min/W", "indicative calculation ONLY")
print("  check   : PDF quotes ~8.7 m^3/min/W; IS 374 requirement >= 4.1 m^3/min/W")
assert round(service_value, 1) == 8.7, service_value
assert service_value >= 4.1
print("  note    : air delivery >= 245 m^3/min is a DESIGN TARGET, not a measured result.")


# ---------------------------------------------------------------------------
# 4. Suspension/anchor demand vs ratings and safety-cable strength
# ---------------------------------------------------------------------------
anchor_demand = 139.9  # N, worst-case static + dynamic pull-out demand from the load analysis (documented assumption set)
working = 600.0
ultimate = 1500.0
show("4. Anchor pull-out demand vs anchor ratings",
     "factor = rating / demand", {"anchor_demand": "139.9 N (load analysis)", "working": "600 N",
                                   "ultimate": "1500 N"}, ultimate / anchor_demand, "x (ultimate factor)", "calculated")
assert anchor_demand < working and anchor_demand < ultimate
cable_kN = 6.5
print(f"  cable   : 0.11 mm-class SS safety cable rated {cable_kN} kN -> factor {cable_kN*1e3/anchor_demand:.1f}x vs demand [calculated]")
assert cable_kN * 1e3 > 10 * anchor_demand


# ---------------------------------------------------------------------------
# 5. Pan/tilt clearance geometry (self-locking worm, tilt gated by floor clearance)
# ---------------------------------------------------------------------------
R = 0.7            # m, rotor radius
tilt_deg = 20.0    # max design tilt
drop = R * math.sin(math.radians(tilt_deg))
floor_clearance_available = 2.65 - (R + drop)  # disc centre set so that static floor clearance is 2.65 m
show("5. Tilt clearance check",
     "lowest_tip = H - (R + R*sin(tilt)) ; floor_clearance = lowest_tip",
     {"H (floor clearance, untilted)": "2.65 m", "R": 0.7, "tilt": "20 deg"}, floor_clearance_available, "m (floor clearance at full tilt)", "geometric derivation on stated mounting geometry")
print("  check   : requirement >= 1.50 m floor clearance at full tilt")
assert floor_clearance_available >= 1.50
print("  control : tilt is DISABLED below 2.60 m floor clearance (supervisor interlock).")


# ---------------------------------------------------------------------------
# 6. Comfort plausibility gates and protection levels (supervisor definition)
# ---------------------------------------------------------------------------
gates = {"temperature_range_C": (-10.0, 80.0), "rate_of_change_K_per_s": 3.0,
         "motor_NTC_trip_C": 165.0, "supervisor_watchdog_ms": 350.0}
print("\n6. Supervisor plausibility gates and hard protection (definition values)")
for k, v in gates.items():
    print(f"    {k} = {v}")
assert gates["motor_NTC_trip_C"] == 165.0 and gates["supervisor_watchdog_ms"] == 350.0
print("  defense chain (3 independent): self-locking worm (holds on power loss) | encoders+limit switches+hard stops | supervisor raw power cut")
print("  response target: <= 5 s automated response ; >= 95 % success over the defined scenario set (targets)")


# ---------------------------------------------------------------------------
# 7. BOM roll-up vs stated order-of-magnitude values (no quotations)
# ---------------------------------------------------------------------------
import csv, pathlib
bom_path = pathlib.Path(__file__).resolve().parents[1] / "data" / "bom.csv"
rows = list(csv.DictReader(bom_path.open(encoding="utf-8")))
total = sum(float(r["cost_inr"]) for r in rows)
NRE_PROGRAMME = 490_000.0  # INR, planning estimate: CFRP tooling/cure development, accredited-lab testing, fixtures, iterations (no quotations)
three_fan = total * 3 * 1.10 + NRE_PROGRAMME  # 3 fans + 10 % BOM contingency + programme NRE
print("\n7. BOM roll-up (planning estimates — NO quotations obtained)")
for r in rows:
    print(f"    {r['item']:<62} {float(r['cost_inr']):>8,.0f} INR  [flag: {r['sourcing_flag']}]")
print(f"    {'BOM TOTAL per fan':<62} {total:>8,.0f} INR")
print(f"    {'NRE programme (tooling, accredited testing, fixtures)':<62} {NRE_PROGRAMME:>8,.0f} INR")
print(f"    {'3-fan programme (3x BOM + 10% conting. + NRE)':<62} {three_fan:>8,.0f} INR  (~{three_fan/1e5:.1f} lakh)")
print("  check   : PDF quotes ~26,650 per fan and ~5.8 lakh for the 3-fan programme")
assert abs(total - 26650) < 1, total
assert abs(three_fan - 5.8e5) / 5.8e5 < 0.02, three_fan

print("\nALL DESIGN CALCULATIONS CONSISTENT WITH THE SUBMISSION PDF.\n")
