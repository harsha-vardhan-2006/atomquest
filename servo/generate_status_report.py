"""Generate TECHNOMANCERS Round 2 project status report (v3).

Rebuilds the 3-page status report with the servo cost section updated to the
bulk-sourcing tiers in servo/SERVO_SELECTION.md. Figure frames are the ones
extracted from the v2 PDF (servo/fig/), so the images are the original frames.

    python servo/generate_status_report.py

Writes servo/TECHNOMANCERS_Round2_Project_Status_v3.pdf
"""

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "TECHNOMANCERS_Round2_Project_Status_v3.pdf")

FOOTER = "TECHNOMANCERS | atomQUEST 2026 Round 2 | Project status report | 5 Nov 2026"

styles = getSampleStyleSheet()
BODY = ParagraphStyle(
    "body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.6,
    leading=11.2, spaceAfter=3.5, alignment=TA_LEFT,
)
SMALL = ParagraphStyle(
    "small", parent=BODY, fontSize=7.4, leading=9.4, textColor=colors.HexColor("#333333"),
)
H1 = ParagraphStyle(
    "h1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=13,
    leading=15.5, spaceBefore=2, spaceAfter=5, textColor=colors.HexColor("#111111"),
)
H2 = ParagraphStyle(
    "h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10,
    leading=12.5, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#111111"),
)
TITLE = ParagraphStyle(
    "title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17,
    leading=20, spaceBefore=2, spaceAfter=6, textColor=colors.HexColor("#111111"),
)
META = ParagraphStyle("meta", parent=BODY, fontSize=8.2, leading=10.6)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=7.6, leading=9.4, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="Helvetica-Bold")
HEAD = ParagraphStyle("head", parent=CELL, fontName="Helvetica-Bold")

GREEN = colors.HexColor("#1a7f37")
GREY = colors.HexColor("#f2f2f2")
LINE = colors.HexColor("#c9c9c9")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(18 * mm, 12 * mm, FOOTER)
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, "Page %d" % doc.page)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, 15.5 * mm, A4[0] - 18 * mm, 15.5 * mm)
    canvas.restoreState()


def table(rows, widths, header=True, zebra=False, font_col=None):
    data = []
    for i, row in enumerate(rows):
        line = []
        for j, cell in enumerate(row):
            st = HEAD if (header and i == 0) else CELL
            line.append(Paragraph(str(cell), st))
        data.append(line)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), GREY))
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafa")))
    if font_col:
        style.append(("TEXTCOLOR", font_col, (0, 1), font_col, (-1, -1), GREEN))
    t.setStyle(TableStyle(style))
    return t


# ---------------------------------------------------------------- content ----

work_status = [
    ["Item", "Status", "Detail"],
    ["Native SolidWorks parts", "Completed",
     "18 parts, each one solid body, reopened and rebuilt through the API."],
    ["Assemblies", "Completed",
     "FD_ROTOR (4 components), FD_TILT (11), FD_SMART_FAN_ASSEMBLY (7); blades placed at 0/120/240 deg."],
    ["STEP and STL exports", "Completed",
     "18 STEP and 7 STL files; 17 of 18 STEP files match the native parts within 0.5 mm after re-import."],
    ["Drawing sheets", "Completed",
     "21 sheets with third-angle views and 172 dimension entities."],
    ["Engineering calculations", "Completed",
     "Mass, inertia, tilt torque, blade root loads, ceiling anchor loads and tilt clearance (analytical estimates)."],
    ["Tilt motion study", "Completed",
     "45 poses checked with interference detection. It found overlap between the tilt group and the top shroud, "
     "so geometry rework is listed below."],
    ["Servo selection", "Completed",
     "4 x DSSERVO DS3235, 35 kg-cm class, run at 7.4 V (2 per axis). Stall torque 6.9 N.m per axis against the "
     "4.45 N.m (X) and 3.62 N.m (Y) need; 40 x 20 x 38.5 mm body fits the 20 x 40 mm mount. Bought as a 10-piece "
     "lot at about INR 700 to 880 per servo (about INR 900 to 1,150 landed), so the four fitted servos cost about "
     "INR 3,600 to 4,600 and the six remaining are spares for the pull tests. Details and alternatives in section 5."],
    ["Safety and test plan", "Completed",
     "Compliance gap matrix and a 9-stage test plan documented."],
    ["Walkthrough video", "Completed",
     "Screen recording of the three assemblies plus a short clip of the original fan hardware."],
    ["Tilt geometry rework", "Pending",
     "Open up the shroud or lower the tilt group, move the travel stop, clear 7 rest-pose overlaps, then re-run the "
     "motion study (target travel +/-20 deg and +/-15 deg)."],
    ["Mass reduction", "Pending",
     "Moving mass is 10.37 kg against the 6.80 kg budget; blade is 0.330 kg against the 0.165 kg target. Hollow or rib "
     "the blade and lighten the yoke and cradle."],
    ["Servo torque confirmation", "Pending",
     "Re-check the servo margin once the original motor is weighed. Bench-test one servo on a lever arm, and extend the "
     "CAD from 2 brackets and 1 horn to 4 servos with 25T horns."],
    ["Original motor measurement", "Pending",
     "Motor envelope, mounting PCD, shaft and bearings are assumed values until measured."],
    ["Assembly mate clean-up", "Pending",
     "Repair or suppress the failed mates shown by error markers in the FD_TILT and FD_ROTOR trees, then re-record the "
     "video if needed."],
    ["Drawing completion", "Pending", "GD&amp;T, fit tolerances, title block and BOM table."],
    ["Material assignment", "Pending",
     "Assign SolidWorks materials so CAD mass matches the calculation sheet."],
    ["Print and fit test", "Pending",
     "Print small fit-check parts (shroud, cover, brackets, collar) and check the unpowered tilt by hand."],
    ["Aerodynamics and containment", "Pending",
     "No CFD or test yet; rotor containment (130 J basis) is unconfirmed. Powered running stays unapproved until these "
     "are done."],
]

key_figures = [
    ["Parameter", "Current value", "Target / basis", "Status"],
    ["Blade tip speed at 380 RPM", "27.86 m/s", "30 m/s cap", "Completed"],
    ["Ceiling anchor load (4 anchors)", "122 N static, 367 N dynamic, 980 N abuse",
     "Anchor rating to be confirmed", "Completed"],
    ["Blade centrifugal load at 380 RPM", "190 N, 0.36 N.m root bending", "Blade strength test", "Completed"],
    ["Blade-tip to ceiling at 20 deg tilt", "112 mm", "Hard stop at 27 deg", "Completed"],
    ["Servo torque per axis", "6.9 N.m stall (2 x DS3235 at 7.4 V)",
     "Need 1.4 to 4.5 N.m (two calculation sheets)", "Completed"],
    ["Tilt servo cost, 4 fitted", "INR 3,600 to 4,600 (bulk lot of 10)",
     "INR 3,500 to 6,500 actuator line", "Completed"],
    ["Moving mass", "10.37 kg (total 12.49 kg)", "6.80 kg", "Pending"],
    ["Rotor energy at 380 RPM", "69 J (calculation) / 77 J (CAD)", "130 J containment basis", "Pending"],
    ["Tilt travel", "Rework in progress", "+/-20 deg and +/-15 deg", "Pending"],
]

datasheet = [
    ["DS3235 datasheet item", "Value (manufacturer datasheet)"],
    ["Size / weight", "40 x 20 x 38.5 mm, 60 g, 25T output spline, double ball bearing, 300 mm lead"],
    ["Supply voltage", "5 to 7.4 V; operating temperature -15 to 70 C"],
    ["Stall torque at 5 / 6 / 7.4 V", "29 / 32 / 35 kg-cm = 2.84 / 3.14 / 3.43 N.m"],
    ["Stall current at 5 / 6 / 7.4 V", "1.9 / 2.1 / 2.3 A (idle 5 mA)"],
    ["Speed at 5 / 6 / 7.4 V", "0.13 / 0.12 / 0.11 s per 60 deg (no load)"],
    ["Control", "PWM 500 to 2500 us, 1500 us neutral, 50 to 330 Hz, 180 or 270 deg travel, dead band 2 us"],
]

requirements = [
    ["Check", "Result", "Margin X / Y", "Verdict"],
    ["Number of servos (REQ-20)", "4 servos, 2 per axis", "-", "Met"],
    ["Both servos on an axis, stall torque", "6.86 N.m vs 4.45 (X) and 3.62 (Y)", "1.54x / 1.90x", "Met"],
    ["One servo failed, no runaway (REQ-35)",
     "3.43 N.m vs nominal 2.23 (X) and 1.81 (Y)", "1.54x / 1.90x", "Met"],
    ["Mount fit", "40 x 20 x 38.5 mm body in the 20 x 40 mm mount", "-", "Met"],
    ["Continuous holding, 2 servos",
     "2.31 N.m (vendor rated torque 11.8 kg-cm each) vs nominal 2.23 / 1.81", "1.04x / 1.28x",
     "Thin on X; confirm after weighing the motor"],
]

alternatives = [
    ["Option", "Stall torque per servo", "Cost, 4 pieces", "Assessment"],
    ["DS3225MG (25 kg-cm class)", "2.40 N.m at 6.8 V (24.5 kg-cm)", "INR 3,756 (INR 939 each)",
     "Fits the old INR 3,500 to 6,500 actuator line, but stall margin is only 1.08x on X and continuous torque is below "
     "the need. Fallback only if the motor weighs little."],
    ["DS3235 (selected)", "3.43 N.m at 7.4 V (35 kg-cm)",
     "INR 3,600 to 4,600 fitted (10-piece lot); INR 7,200 at retail",
     "Meets every row above; same footprint as the CAD mount; seven checks pass without gearing."],
    ["DS3235SSG (stainless gear)", "3.43 N.m class (seller lists 34 kg-cm)", "INR 9,240 (INR 2,310 each)",
     "Same torque class with stronger gears; optional upgrade for the final fan."],
    ["MG996R (hobby class)", "1.08 N.m at 6 V (11 kg-cm)", "about INR 1,600",
     "Rejected: two per axis is still below the nominal X torque, so it cannot meet the need at any price."],
    ["Futaba BLA21-12R3-C01 (industrial)", "4.90 N.m max", "not listed; import",
     "Rejected: torque is adequate but it is one servo per axis, which fails the 4-servo REQ-20 layout; import cost "
     "and lead time are outside the line."],
    ["Futaba BLA21A series (industrial)", "4.51 to 4.90 N.m, IP67", "not listed; import",
     "Rejected for the same layout and sourcing reason; IP67 is not needed indoors."],
    ["Festo EMMT-AS-80-M-HS-RMB", "2.60 N.m stall (6.4 N.m peak)", "not listed; industrial",
     "Rejected: stall is below the need, the peak is transient only, and it needs an industrial drive on a 680 V DC bus."],
]

sourcing = [
    ["Sourcing tier", "Quantity", "Unit price", "4 fitted servos", "Cash out"],
    ["Retail, one-off", "1 each", "INR 1,406 to 2,299", "INR 5,624 to 9,196", "same"],
    ["Retail, in stock on 5 Nov", "1 each", "INR 1,800", "INR 7,200", "INR 7,200"],
    ["Bulk lot (selected)", "10", "INR 700 to 880 ex-works; about INR 900 to 1,150 landed",
     "INR 3,600 to 4,600 landed", "INR 9,000 to 11,500 landed"],
]

where = [
    ["Content", "Location in the repository"],
    ["Status report, servo decision and sizing",
     "servo/ (this report, SERVO_SELECTION.md, servo_sizing.csv, generate_status_report.py)"],
    ["Final design report, limitations, changelog",
     "competition/atomQUEST2026/round2/FINAL_DESIGN/ (FINAL_DESIGN_REPORT.md, KNOWN_LIMITATIONS.md, CHANGELOG.md)"],
    ["Parts, assemblies, STEP, STL, drawings",
     "01_NATIVE_PARTS, 04_ASSEMBLIES, 02_STEP_EXPORTS, 03_PRINT_STL, 06_DRAWINGS (inside FINAL_DESIGN)"],
    ["Calculations and reports",
     "07_ENGINEERING_CALCULATIONS (servo_sizing.csv, mass_and_torque.csv), 08_VERIFICATION_REPORTS, "
     "MASS_AND_TORQUE_REPORT.md"],
    ["Safety and test plan", "FINAL_DESIGN/11_TEST_PLAN/SAFETY_AND_TEST_PLAN.md"],
    ["Round 1 evidence and cost basis", "docs/, data/, calculations/, submission/ at the repository root"],
]

story = []
story.append(Paragraph("Smart AI Fan: Round 2 Project Status", TITLE))
story.append(Paragraph(
    "TECHNOMANCERS (T-2026) | atomQUEST 2026, Track 1 Fan | Aditya Institute of Technology and Management, Tekkali, "
    "Dept. of ECE", META))
story.append(Paragraph(
    "Team: Harsha Vardhan Malipeddi, Dabbiru Rochan Kumar, Simhadri Sri Teja, Guluvindala Ganesh Manikanta, "
    "Nakka Ugandhar", META))
story.append(Paragraph(
    "Status date: 5 November 2026 | Accompanies the submitted walkthrough video (about 1 min 29 s) | Repository: "
    "github.com/harsha-vardhan-2006/atomquest", META))
story.append(Spacer(1, 6))

story.append(Paragraph("1. Summary", H1))
story.append(Paragraph(
    "The Round 1 concept (a 1,400 mm ceiling fan with a two-axis tilt head, sensor-based comfort control and a safety "
    "supervisor) now has a complete native SolidWorks design package: 18 parts, 3 assemblies, 18 STEP exports, 7 "
    "printable STL meshes and 21 drawing sheets, with the mass, torque, load and clearance calculations behind them. "
    "The original motor, rotor, shaft and bearings are retained and shown only as a reference envelope. The new "
    "hardware is a ceiling plate, downrod, stationary yoke, outer tilt ring, inner cradle, servo brackets, pivots, "
    "shroud and a three-blade rotor.", BODY))
story.append(Paragraph(
    "Update in this version: the tilt servo is selected and its cost is closed out. Four DSSERVO DS3235 (35 kg-cm "
    "class) servos, two per axis, cover the 4.5 N.m per-axis torque need with margin and fit the 20 x 40 mm mount in "
    "the CAD. Bought as a single 10-piece lot from the manufacturer tier, the four fitted servos cost about INR 3,600 "
    "to 4,600 instead of INR 7,200 at retail, and the six spare servos cover the lever-arm pull tests that section 5 "
    "requires. The servo line therefore stays inside the INR 3,500 to 6,500 that the full-fan estimate already "
    "carried, and the full-fan estimate does not rise.", BODY))
story.append(Paragraph(
    "Every item below is marked Completed or Pending. Pending items are the remaining engineering work before any "
    "hardware is built. No powered operation is approved.", BODY))

story.append(Paragraph("2. Work status", H2))
story.append(table(work_status, [36 * mm, 17 * mm, 121 * mm]))

story.append(Paragraph("3. Key figures", H2))
story.append(table(key_figures, [48 * mm, 54 * mm, 45 * mm, 27 * mm]))
story.append(Spacer(1, 3))
story.append(Paragraph(
    "Two scripts estimate mass and inertia with different groupings, which is why two energy values and two "
    "servo-torque figures are shown; they will be reconciled after the motor is weighed.", SMALL))

story.append(Paragraph("4. What the video shows", H2))
story.append(Paragraph(
    "The recording (1280 x 720, about 89 s) rotates and inspects FD_SMART_FAN_ASSEMBLY, then FD_ROTOR (hub with "
    "three blades) and FD_TILT (yoke, outer ring, inner cradle, motor adapter and cover, bushings, servo brackets, "
    "travel stop), and returns to the full assembly. Short clips show the original fan hardware (motor housing and "
    "wiring), the part the design keeps.", BODY))

fig1 = os.path.join(HERE, "fig", "page2_5.jpeg")
fig2 = os.path.join(HERE, "fig", "page2_6.jpeg")
if os.path.exists(fig1) and os.path.exists(fig2):
    w = 78 * mm
    h = w * 600.0 / 1280.0
    figs = Table(
        [[Image(fig1, width=w, height=h), Image(fig2, width=w, height=h)],
         [Paragraph("Fig. 1: FD_SMART_FAN_ASSEMBLY (video frame)", SMALL),
          Paragraph("Fig. 2: FD_TILT assembly (video frame)", SMALL)]],
        colWidths=[w + 6 * mm, w + 6 * mm], hAlign="LEFT",
    )
    figs.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(Spacer(1, 3))
    story.append(figs)

story.append(Paragraph("5. Servo selection (Completed)", H1))
story.append(Paragraph(
    "<b>Why four servos.</b> REQ-20 asks for four servos (X1+X2 on one axis, Y1+Y2 on the perpendicular axis) and "
    "REQ-35 asks for the actuator torque to be recalculated for that layout. The torque need comes from the "
    "repository: 4.45 N.m (X) and 3.62 N.m (Y) per axis in MASS_AND_TORQUE_REPORT.md (includes a 2.0 design margin, "
    "0.85 linkage efficiency and a placeholder motor mass), and 1.41 / 1.45 N.m in the second calculation sheet. The "
    "servo mount in the CAD is a standard 20 x 40 mm servo footprint.", BODY))
story.append(Paragraph(
    "<b>Selected:</b> 4 x DSSERVO DS3235 (35 kg-cm class coreless digital servo, metal gears, IP66), powered at "
    "7.4 V, two servos per axis.", BODY))
story.append(table(datasheet, [46 * mm, 128 * mm]))
story.append(Spacer(1, 5))
story.append(Paragraph(
    "How it meets the requirements (7.4 V; need = repository figure; \"nominal\" = the need divided by its 2.0 "
    "design margin: X 2.23, Y 1.81 N.m).", BODY))
story.append(table(requirements, [52 * mm, 60 * mm, 30 * mm, 32 * mm]))
story.append(Spacer(1, 3))
story.append(Paragraph(
    "The continuous-torque row uses a rated-torque figure from one seller listing, not the manufacturer datasheet, "
    "so treat it as indicative. If the weighed motor makes the X axis too heavy, add a gear reduction or a "
    "counterweight rather than a bigger servo. At 6.0 V the X margin falls below 1 on that basis, so keep the rail at "
    "7.4 V and not above it.", SMALL))
story.append(Spacer(1, 4))
story.append(Paragraph("Alternatives considered", H2))
story.append(Paragraph(
    "INR from Indian shop listings found on 5 Nov 2026; listings, not quotations.", SMALL))
story.append(table(alternatives, [34 * mm, 33 * mm, 36 * mm, 71 * mm]))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "The DS3235 wins on three counts. It is the cheapest part that passes every check, so the cheaper DS3225MG and "
    "the hobby-class MG996R are ruled out on torque rather than cost. It survives one servo failing, which the "
    "single-servo industrial options cannot offer because they have no second actuator on the axis. And it drops "
    "into the bracket already modelled in the CAD with a 25T spline, on ESP32 hardware PWM with no separate drive. "
    "The Futaba and Festo units solve a positioning-accuracy problem this fan does not have, at many times the "
    "price and on an import lead time.", BODY))

story.append(Paragraph("Sourcing and cost", H2))
story.append(table(sourcing, [38 * mm, 17 * mm, 51 * mm, 34 * mm, 34 * mm]))
story.append(Spacer(1, 3))
story.append(Paragraph(
    "The manufacturer tier is where the price actually falls: about INR 700 to 880 per servo ex-works instead of "
    "INR 1,800 at retail, roughly 55 per cent lower. Two points keep that honest. First, no MOQ-10 listing sells "
    "four pieces, so the lot has to be ten and cash out is INR 9,000 to 11,500 even though four servos go into the "
    "fan. Second, the other six are not padding: section 5 requires each servo to be pull-tested on a known lever "
    "arm before fitting, and that test destroys samples, so six covers the bench test plus one spare set. Landed "
    "figures add freight and 18 per cent GST at INR 88 to the US dollar; prices move with the exchange rate and must "
    "be confirmed with the seller before ordering.", SMALL))
story.append(Spacer(1, 3))
story.append(Paragraph(
    "<b>Budget effect.</b> The full-fan estimate carried INR 3,500 to 6,500 for the tilt actuator set. The four "
    "fitted DS3235 come to INR 3,600 to 4,600 landed, which sits inside that line, so the full-fan estimate stays at "
    "about INR 25,000 including 10 per cent contingency instead of rising to INR 28,000 to 29,600 on the "
    "retail-one-off basis. The 7.4 V supply is not priced here.", BODY))

story.append(Paragraph("Integration notes", H2))
story.append(Paragraph(
    "(1) Power the four servos from a dedicated, fused, regulated 7.4 V rail (buck from the 24 V supply) sized for "
    "4 x 2.3 A = 9.2 A worst case; do not draw it from the ESP32 board. (2) Drive from ESP32 hardware PWM; firmware "
    "limit +/-20 deg (REQ-12), mechanical stop at 27 deg (REQ-13), rotor stopped before any tilt (REQ-11), and the "
    "safety supervisor can cut servo power. (3) The CAD still holds 2 servo brackets and 1 generic horn; add the "
    "other two brackets and 25T horns. (4) Seller specs differ for the same model (for example DS3225 listings range "
    "from 21 to 28 kg-cm), so buy against the datasheet torque and pull-test each servo on a known lever arm before "
    "fitting.", BODY))

story.append(Paragraph("6. Cost basis and next steps", H1))
story.append(Paragraph(
    "Cost (planning estimates, not quotations; docs/cost_basis.md): Round 2 Level 1 control demonstrator about INR "
    "10,700 (7,040-14,300); one full-fan prototype about INR 25,000 (17,160-32,890), unchanged by the servo update "
    "because the selected 10-piece lot lands inside the actuator line it replaces. Tooling, test equipment, "
    "certification and shipping are excluded.", BODY))
story.append(Paragraph(
    "Next steps: (1) repair tilt geometry and mates, then re-run the motion study; (2) weigh and measure the "
    "original motor, then re-check the servo margin; (3) cut mass and re-run the calculations; (4) order the "
    "10-piece DS3235 lot and a 7.4 V supply, bench-test one axis with two servos, then extend the CAD to four "
    "servos; (5) print fit-check parts and test the unpowered tilt by hand; (6) complete drawings and materials.",
    BODY))

story.append(Paragraph("7. Where to find things", H2))
story.append(table(where, [52 * mm, 122 * mm]))

story.append(Paragraph("8. Sources for the servo research", H2))
story.append(Paragraph(
    "DS3235 manufacturer datasheet: hajim.rochester.edu/me/sites/kelley/me240/DS3235-270_datasheet.pdf. Indian "
    "listings and prices: rees52.com (DS3235 INR 1,919; DS3235MG INR 1,800; DS3235SSG INR 2,310; DS3225MG INR 939), "
    "roboticsdna.in (DS3235MG INR 1,406 incl. GST, out of stock), probots.co.in (DS3225 INR 2,499 incl. GST, out of "
    "stock at the time). Bulk tier: Alibaba listings for Dsservo DS3235 35KG at USD 8 to 10 per piece, MOQ 10, from "
    "Dongguan Dsservo Technology, Dongguan Sanshu Electric and Shenzhen Fengfei Electronics, ex-works. DS3225 "
    "specification: bzbuas.com and racer.lt listings. Torque conversion: 1 kg-cm = 0.0980665 N.m. Torque need: "
    "repository files MASS_AND_TORQUE_REPORT.md, servo_sizing.csv and calculations_summary.json. Futaba "
    "BLA21-12R3-C01 and BLA21A series: futaba.co.jp industrial servo pages and futabairc.com product introduction. "
    "Festo EMMT-AS-80-M-HS-RMB: Festo datasheet 5255440. MG996R: handsontec.com MG996R.pdf. Prices change; confirm "
    "with the seller before ordering.", SMALL))


def build():
    doc = BaseDocTemplate(
        OUT, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=20 * mm,
        title="TECHNOMANCERS - atomQUEST 2026 Round 2 - Project Status (v3)",
        author="TECHNOMANCERS",
        subject="Project Status Report - Smart AI Fan, servo cost at bulk tier",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)
    return OUT


if __name__ == "__main__":
    path = build()
    print("wrote", path)
