# Tilt servo package — Round 2

Everything behind the one-line claim in the status report: *four DSSERVO DS3235 servos, two per
axis, cover the 4.45 / 3.62 N·m per-axis need and fit the 20 × 40 mm mount in the CAD.*

| File | What it holds |
| --- | --- |
| `SERVO_SELECTION.md` | The decision: requirements, datasheet, margins, alternatives, sourcing tiers, integration notes, sources |
| `servo_sizing.csv` | The same comparison as machine-readable rows — torque, margins, retail and bulk price per candidate |
| `TECHNOMANCERS_Round2_Project_Status_v3.pdf` | Generated status report (4 pages) with this cost basis |
| `generate_status_report.py` | Regenerates that PDF — run `python servo/generate_status_report.py` |
| `fig/` | The two assembly video frames re-embedded in the report |

## The decision in five lines

1. Needs: 4.45 N·m (X) and 3.62 N·m (Y) per axis, from a 2.0 design margin over the nominal duty.
   With two servos per axis (REQ-20), each servo carries half.
2. One servo must survive alone (REQ-35): 3.43 N·m against a nominal 2.23 / 1.81 N·m is 1.54× / 1.90×.
3. Two servos on the axis give 6.86 N·m against 4.45 / 3.62 — 1.54× / 1.90×.
4. Cheaper servos fail on torque, not on price: DS3225MG drops to 1.08× on X, MG996R to 0.49×.
   Industrial Futaba/Festo units are one-per-axis, so they fail the four-servo layout.
5. Cost: bought as one 10-piece manufacturer lot at INR 700–880 each (about INR 900–1,150 landed),
   the four fitted servos cost INR 3,600–4,600 — inside the INR 3,500–6,500 line the full-fan
   estimate already carried. Cash out for the lot is INR 9,000–11,500; the six spares pay for the
   lever-arm pull tests the document requires.

## Still open

- Weigh the original motor, then re-check the continuous-holding margin (currently 1.04× on X and
  that figure comes from a seller listing, not the datasheet).
- The CAD holds 2 servo brackets and 1 horn; it needs 4 brackets and 25T horns.
- Keep the rail at 7.4 V. At 6.0 V the X margin on the continuous basis falls below 1.

Prices are Indian shop listings and Alibaba MOQ-10 listings seen on 5 Nov 2026 — not quotations.
