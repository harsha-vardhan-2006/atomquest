# Round 2 · Tilt servo selection — DS3235 and why the others were rejected

> Status: **Completed** (5 Nov 2026). Supersedes the Round 1 Rev 2 "brushed DC + worm, self-locking"
> actuator family in `docs/design/rev2/03-motor-drive-power.md` §4 for the Round 2 CAD.
> Prices are Indian shop listings seen on 5 Nov 2026, **not quotations**. Specs are manufacturer
> datasheet values unless a row says otherwise.

## 1. What the servo has to do

| Input | Value | Source |
| --- | --- | --- |
| Servos per fan (layout) | 4 — X1+X2 on one axis, Y1+Y2 on the perpendicular axis | REQ-20 |
| Torque recalculation for that layout | required | REQ-35 |
| Torque need, X axis | 4.45 N·m per axis | `MASS_AND_TORQUE_REPORT.md` (2.0 design margin, 0.85 linkage efficiency, placeholder motor) |
| Torque need, Y axis | 3.62 N·m per axis | same |
| Nominal (need ÷ 2.0 margin), X / Y | 2.23 / 1.81 N·m | derived |
| Alternative torque sheet | 1.41 / 1.45 N·m | second calculation sheet |
| Mount in CAD | standard 20 × 40 mm servo footprint | `FD_TILT` |
| Control | ESP32 hardware PWM, safety supervisor can cut servo power | REQ-11, REQ-12, REQ-13 |

Because the layout is **two servos per axis**, each servo only has to carry *half* the axis need —
but REQ-35 requires that **one failed servo must not cause runaway**, so the single remaining servo
must still exceed the *nominal* torque (need ÷ its 2.0 margin).

## 2. Candidates compared

`axis` = both servos on one axis. `1 failed` = the surviving servo against the nominal figure.

| Candidate | Stall torque / servo | Servos / axis | Axis stall | vs need X / Y | 1 failed vs nominal X / Y | 20 × 40 mm mount | Cost, 4 pcs (INR) | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **DS3235 (selected)** | 3.43 N·m @ 7.4 V (35 kg-cm) | 2 | 6.86 N·m | 1.54× / 1.90× | 1.54× / 1.90× | Yes | 3,600–4,600 fitted (bulk MOQ 10); 7,200 retail | **Selected** — passes every check, same footprint as the CAD bracket |
| DS3235SSG | 3.33 N·m (34 kg-cm) | 2 | 6.66 N·m | 1.50× / 1.84× | 1.49× / 1.84× | Yes | 9,240 (2,310 ea) | Same class, stainless gears — optional upgrade if wear shows up on the bench test; +20% cost buys no extra margin |
| DS3225MG | 2.40 N·m @ 6.8 V (24.5 kg-cm) | 2 | 4.80 N·m | 1.08× / 1.33× | 1.08× / 1.33× | Yes | 3,756 (939 ea) | Cheapest that fits, but 1.08× on X and continuous torque is below the need. Fallback **only** if the weighed motor turns out light |
| MG996R | 1.08 N·m @ 6 V (11 kg-cm) | 2 | 2.16 N·m | **0.49×** / 0.60× | 0.48× / 0.60× | Yes | ~1,400–2,000 | **Rejected** — even two per axis is below the X nominal. Cannot meet the need |
| Futaba BLA21-12R3-C01 | 4.90 N·m max | 1 (as designed) | 4.90 N·m | 1.10× / 1.35× | 2.20× / 2.71× (per servo) | No (41 × 33 × 42 mm) | not listed / import | **Rejected** — torque and quality are fine, but it is a single industrial servo per axis, so it does not meet the 4-servo REQ-20 layout; import lead time and price are outside the budget line |
| Futaba BLA21A series | 4.51–4.90 N·m, IP67 | 1 | 4.51–4.90 N·m | 1.01–1.10× / 1.25–1.35× | — | No | not listed / import | **Rejected** — same reasons as above; the IP67 rating is not needed indoors |
| Festo EMMT-AS-80-M-HS-RMB | 2.6 N·m stall, 6.4 N·m peak | 1 | 2.6 N·m stall | **0.58×** on stall / 0.72× | — | No | not listed / industrial | **Rejected** — stall torque below the need, peak is transient only, and it needs an industrial servo drive and a 680 V DC bus. Not viable on a 24 V ceiling fan |

Derived values in this table were recalculated from the datasheet figures, not copied from a seller page:
`1 kg-cm = 0.0980665 N·m`, so 35 kg-cm = 3.43 N·m, 34 kg-cm = 3.33 N·m, 24.5 kg-cm = 2.40 N·m,
11 kg-cm = 1.08 N·m.

## 3. Why the DS3235 and not the cheaper or the better one

1. **It is the cheapest option that actually passes every check.** DS3225MG saves INR 3,900 on the
   set but drops to 1.08× margin on the X axis and falls below the need on continuous torque.
   MG996R saves more and fails outright.
2. **It survives one servo failing** (REQ-35). One DS3235 still gives 1.54× / 1.90× on the nominal
   X / Y torque, so a dead servo degrades the axis instead of letting it run away. The single-servo
   industrial alternatives have no equivalent redundancy because there is only one actuator per axis.
3. **It drops into the CAD as-is.** The body is 40 × 20 × 38.5 mm with a 25T spline, matching the
   20 × 40 mm mount already modelled in `FD_TILT` and the 25T horns to be added. No rework of the
   bracket or the pivot geometry.
4. **It is driven directly by the ESP32.** Standard PWM, 500–2500 µs, 50–330 Hz — hardware PWM,
   no separate servo drive, no gearbox, no encoder loop. That keeps the control box and the fault
   tree small.
5. **Metal gears, IP66, double ball bearing.** The fan is a dust-prone, long-life appliance; a
   plastic-gear servo would be the first thing to fail.
6. **Available in India at a known price, and cheap in a lot.** INR 1,800 each in stock at rees52, and
   about USD 8–10 (INR 700–880) each at the MOQ-10 manufacturer tier — roughly 55% lower per unit, see
   section 6. Two servos can be bought for a bench test before committing to the full set.
7. **The industrial servos are the wrong tool here.** Futaba BLA21/BLA21A and Festo EMMT-AS solve a
   positioning-accuracy problem this fan does not have; they cost many times more, need different
   mounting, and would still have to be replicated four times to satisfy REQ-20.

## 4. Where the DS3235 is thin

- **Continuous holding torque** is 2.31 N·m for two servos (vendor rated torque 11.8 kg-cm each)
  against nominal 2.23 / 1.81 N·m — only **1.04× on X**. This figure comes from one seller listing,
  not the manufacturer datasheet, so it is indicative. It must be re-checked after the original motor
  is weighed. If X becomes heavier, add a gear reduction or a counterweight; do **not** fit a bigger
  servo.
- **Keep the rail at 7.4 V and never above it.** At 6.0 V the X margin on that continuous basis falls
  below 1.
- Seller specs disagree for the same model (DS3225 listings range from 21 to 28 kg-cm), so buy against
  the datasheet torque and pull-test each servo on a known lever arm before fitting.

## 5. Integration notes

1. Dedicated, fused, regulated 7.4 V rail (buck from the 24 V supply) sized for 4 × 2.3 A = 9.2 A
   worst case. Never draw servo current from the ESP32 board.
2. ESP32 hardware PWM; firmware limit ±20° (REQ-12), mechanical stop at 27° (REQ-13), rotor stopped
   before any tilt (REQ-11), safety supervisor able to cut servo power.
3. The CAD still holds 2 servo brackets and 1 generic horn — add the other two brackets and the 25T
   horns.
4. The 7.4 V supply is not priced in `docs/cost_basis.md`.

## 6. Budget effect and sourcing tiers

The same servo is listed at very different prices depending on the purchase channel. Three real tiers
apply to the DS3235/DS3235MG:

| Tier | Quantity | Unit price | 4 fitted servos | Cash out | Notes |
| --- | --- | --- | --- | --- | --- |
| Retail, one-off | 1 each | INR 1,406–2,299 | INR 5,624–9,196 | same | Fastest; single-unit listings move in and out of stock |
| Retail, in stock on 5 Nov | 1 each | INR 1,800 (rees52 DS3235MG) | **INR 7,200** | INR 7,200 | Verified stock, GST included |
| **Bulk lot, MOQ 10** | 10 | **USD 8–10 ≈ INR 700–880 ex-works**, about INR 900–1,150 landed | **INR 3,600–4,600 landed** | INR 9,000–11,500 landed | Manufacturer/seller MOQ 10 on Alibaba; landed adds freight plus 18% GST |

The bulk tier is where the cost actually drops: **about INR 700–880 per servo instead of INR 1,800**,
i.e. roughly 55% off. Two honest qualifications, because they change what may be quoted:

1. There is **no bulk discount on four pieces**. Every MOQ-10 listing needs ten pieces bought at once,
   so cash out is INR 9,000–11,500 even though only four go into the fan. The saving is per unit, not
   in total, unless the other six have a job.
2. They do have a job: the project still has to pull-test each servo on a lever arm before fitting
   (section 4), and that test destroys samples. Six spares covers the bench test plus one spare set,
   so the 10-piece lot is the right buy for this build rather than padding.

On the bulk basis the four fitted servos cost **INR 3,600–4,600 landed** (INR 2,800–3,520 ex-works before
freight and GST), which sits inside the INR 3,500–6,500 line the full-fan estimate already carried for
tilt actuation. The servo update is therefore **cost-neutral** against that line: the full-fan estimate
stays at about **INR 25,000** including 10% contingency, instead of rising to INR 28,000–29,600 on the
retail-one-off basis.

Starter step: buy the 10-piece lot, bench-test one axis with two servos, then fit the remaining pair.
Shipping and the 7.4 V supply are not included above.

## 7. Sources

- DS3235 datasheet: `hajim.rochester.edu/me/sites/kelley/me240/DS3235-270_datasheet.pdf`
- DS3235 / DS3225 Indian listings and prices: rees52.com (RDS3235 INR 1,919; DS3235MG INR 1,800;
  DS3235SSG INR 2,310; DS3225MG INR 939), roboticsdna.in (DS3235MG INR 1,406 incl. GST, out of stock),
  probots.co.in (DS3225 INR 2,499 incl. GST, out of stock on 5 Nov 2026)
- Bulk / MOQ-10 tier: Alibaba listings for "Dsservo DS3235 35KG" at USD 8–10 per piece, MOQ 10, from
  Dongguan Dsservo Technology, Dongguan Sanshu Electric and Shenzhen Fengfei Electronics. Prices are
  ex-works and change with the rupee–dollar rate; the INR figures above use INR 88 = USD 1.
- DS3225 specification: bzbuas.com and racer.lt listings
- Futaba BLA21-12R3-C01 and BLA21A series: futaba.co.jp industrial-servo product pages and
  `futabairc.com` BLA21-12R3-C01 product introduction
- Festo EMMT-AS-80-M-HS-RMB: Festo datasheet 5255440
- MG996R: handsontec.com `MG996R.pdf`
- Torque need: `MASS_AND_TORQUE_REPORT.md`, `servo_sizing.csv`, `calculations_summary.json`
