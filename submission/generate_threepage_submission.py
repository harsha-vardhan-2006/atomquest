#!/usr/bin/env python3
"""Three-page DETAILED Stage 1 abstract for atomQUEST 2026 Track 1.

Style/content modelled on TECHNOMANCERS_atomQUEST_2026_Track1_Smart_AI_Fan_Abstract.pdf
(the 4-page detail pack), tightened to 3 pages and upgraded with the evidence-repository
link (github.com/harsha-vardhan-2006/atomquest) so judges can check every calculation
and scenario directly.

Honesty: paper design; no measured results; unresolved risks preserved.
Gates hard-fail if the build is not exactly 3 pages or lacks the repo URL.
"""
import csv
import pathlib
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Flowable, PageBreak)

REPO_URL = "github.com/harsha-vardhan-2006/atomquest"
HERE = pathlib.Path(__file__).resolve().parents[1]  # repo root
OUT = pathlib.Path(__file__).resolve().parent / "TECHNOMANCERS_Track1.pdf"

NAVY = HexColor("#1F3A5F")
TEAL = HexColor("#0E7C7B")
LIGHT = HexColor("#EAF3F6")
REPOBG = HexColor("#F2F7EC")
RULE = HexColor("#B9C8D3")
INK = HexColor("#16222E")

S = dict(
    title=ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=15.5, leading=19,
                         textColor=NAVY, alignment=TA_CENTER, spaceAfter=2),
    subtitle=ParagraphStyle("subtitle", fontName="Helvetica", fontSize=9.5, leading=12,
                            textColor=TEAL, alignment=TA_CENTER, spaceAfter=5),
    h2=ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
                      textColor=NAVY, spaceBefore=7, spaceAfter=2.5),
    h3=ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=9, leading=11.5,
                      textColor=TEAL, spaceBefore=4, spaceAfter=1.5),
    body=ParagraphStyle("body", fontName="Helvetica", fontSize=8.8, leading=11.5,
                        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=3),
    bullet=ParagraphStyle("bullet", fontName="Helvetica", fontSize=8.8, leading=11.5,
                          textColor=INK, leftIndent=9, bulletIndent=3, spaceAfter=1.5),
    cell=ParagraphStyle("cell", fontName="Helvetica", fontSize=7.6, leading=9.4, textColor=INK),
    cellB=ParagraphStyle("cellB", fontName="Helvetica-Bold", fontSize=7.6, leading=9.4, textColor=INK),
    head=ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=7.6, leading=9.4, textColor=white),
    small=ParagraphStyle("small", fontName="Helvetica-Oblique", fontSize=7.4, leading=9.4,
                         textColor=HexColor("#5A6B7A"), spaceBefore=2),
    repo=ParagraphStyle("repo", fontName="Helvetica-Bold", fontSize=9.6, leading=12.5,
                        textColor=NAVY),
)


def P(t, s="body"):
    return Paragraph(t, S[s])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="•") for t in items]


def styled_table(data, widths, header=True, headings_bg=NAVY):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.5, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
             ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), headings_bg),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT])]
    return t


class ArchDiagram(Flowable):
    """System-level block diagram (Figure 1) — control priority supervisor > local > RF > web > automation."""
    def __init__(self, width=172 * mm, height=60 * mm):
        super().__init__()
        self.width, self.height = width, height

    def draw(self):
        c = self.canv

        def box(x, y, w, h, label, fill, txtcol=white, fs=6.4):
            c.saveState(); c.setFillColor(fill); c.setStrokeColor(NAVY); c.setLineWidth(0.9)
            c.roundRect(x, y, w, h, 3 * mm, stroke=1, fill=1)
            c.setFillColor(txtcol); c.setFont("Helvetica-Bold", fs)
            lines = label.split("\n"); lh = fs + 1.5
            y0 = y + h / 2 + (len(lines) - 1) * lh / 2 - fs * 0.75
            for ln in lines:
                c.drawCentredString(x + w / 2, y0, ln); y0 -= lh
            c.restoreState()

        def arrow(x1, y1, x2, y2, col=NAVY, ieee=False):
            import math
            c.setStrokeColor(col); c.setLineWidth(1.0)
            if ieee:
                c.setDash(3, 2)
            c.line(x1, y1, x2, y2)
            c.setDash()
            ang = math.atan2(y2 - y1, x2 - x1)
            for s in (+0.42, -0.42):
                c.line(x2, y2, x2 - 3 * mm * math.cos(ang + s), y2 - 3 * mm * math.sin(ang + s))

        w, h = self.width, self.height
        box(4 * mm, h - 12 * mm, 30 * mm, 9 * mm, "Temp/humidity\nsensors", TEAL, fs=6.0)
        box(38 * mm, h - 12 * mm, 27 * mm, 9 * mm, "Web/app\n(TLS 1.3)", LIGHT, txtcol=NAVY, fs=6.0)
        box(69 * mm, h - 12 * mm, 27 * mm, 9 * mm, "RF remote +\nmanual override", LIGHT, txtcol=NAVY, fs=6.0)
        box(100 * mm, h - 12 * mm, 29 * mm, 9 * mm, "Encoders,\nlimit switches", TEAL, fs=6.0)
        box(133 * mm, h - 12 * mm, 15 * mm, 9 * mm, "Safe\ntest load", LIGHT, txtcol=NAVY, fs=5.8)
        box(146 * mm, h - 12 * mm, 24 * mm, 9 * mm, "Connected\ndevices", LIGHT, txtcol=NAVY, fs=6.0)
        box(28 * mm, h - 32 * mm, 106 * mm, 12 * mm,
            "SAFETY SUPERVISOR MCU — locked firmware · 350 ms watchdog\nplausibility gates · tilt interlocks · stall · raw power cut", NAVY, fs=6.0)
        box(28 * mm, h - 48 * mm, 106 * mm, 11 * mm,
            "LOCAL CONTROLLER — comfort automation + FOC speed loops", TEAL, fs=6.0)
        box(10 * mm, h - 64 * mm, 58 * mm, 10 * mm, "24 V BLDC motor drive\n(sensorless FOC)", NAVY, fs=6.0)
        box(74 * mm, h - 64 * mm, 52 * mm, 10 * mm, "Pan/tilt worm actuators\n(12 V, self-locking)", NAVY, fs=6.0)
        box(132 * mm, h - 64 * mm, 36 * mm, 10 * mm, "Connected-device\ntrigger interface", LIGHT, txtcol=NAVY, fs=6.0)
        arrow(19 * mm, h - 22 * mm, 50 * mm, h - 22.2 * mm, TEAL)
        arrow(51 * mm, h - 22 * mm, 70 * mm, h - 22.2 * mm)
        arrow(82 * mm, h - 22 * mm, 88 * mm, h - 22.2 * mm)
        arrow(114 * mm, h - 22 * mm, 109 * mm, h - 22.2 * mm, TEAL)
        arrow(81 * mm, h - 32 * mm, 81 * mm, h - 36.5 * mm)
        c.setFillColor(NAVY); c.setFont("Helvetica", 5.7); c.drawString(83 * mm, h - 36.2 * mm, "raw power-cut path")
        arrow(55 * mm, h - 48 * mm, 40 * mm, h - 55 * mm)
        arrow(107 * mm, h - 48 * mm, 99 * mm, h - 55 * mm)
        arrow(112 * mm, h - 43 * mm, 148 * mm, h - 56 * mm, TEAL, ieee=True)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE); canvas.setLineWidth(0.6)
    canvas.line(15 * mm, 12.5 * mm, A4[0] - 15 * mm, 12.5 * mm)
    canvas.setFillColor(HexColor("#5A6B7A")); canvas.setFont("Helvetica", 7.3)
    canvas.drawString(15 * mm, 9 * mm, f"TECHNOMANCERS · atomQUEST 2026 · Track 1 Fan · Evidence repo: {REPO_URL}")
    canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, "Page %d" % doc.page)
    canvas.restoreState()


def header_band(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY); canvas.rect(0, A4[1] - 11 * mm, A4[0], 11 * mm, stroke=0, fill=1)
    canvas.setFillColor(TEAL); canvas.rect(0, A4[1] - 12.2 * mm, A4[0], 1.2 * mm, stroke=0, fill=1)
    canvas.setFillColor(white); canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(15 * mm, A4[1] - 7.6 * mm, "atomQUEST 2026 — Stage 1 Abstract")
    canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 7.6 * mm, "Track 1 · Fan")
    canvas.restoreState()


def load_csv(p):
    with (HERE / "data" / p).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


E = []
E.append(P("Smart AI Fan — Technical Abstract", "title"))
E.append(P("TECHNOMANCERS (T-2026) · Track 1 · Fan · atomQUEST 2026 · Stage 1 "
           "(Round 1 closes 18 Oct 2026, 18:29 GMT — gradpartners.in/e/atomquest-2026-339)", "subtitle"))

# ===================== A. Team & Institutional Context =====================
E.append(P("A · Team & Institutional Context", "h2"))
team = [[P("Team name", "head"), P("Code", "head"), P("Institution", "head"), P("Department", "head"),
         P("Contact / corresponding author", "head")],
        [P("TECHNOMANCERS", "cellB"), P("T-2026", "cell"),
         P("Aditya Institute of Technology and Management, Tekkali", "cell"),
         P("Electronics and Communication Engineering (ECE)", "cell"),
         P("Harsha Vardhan Malipeddi — harshavardhanmalipeddi1@gmail.com", "cell")]]
E.append(styled_table(team, [34 * mm, 16 * mm, 62 * mm, 42 * mm, 46 * mm]))
E.append(Spacer(1, 3))
mem = [[P("#", "head"), P("Name", "head"), P("Year", "head"), P("Graduating", "head")]]
for i, (n, y, g) in enumerate([("Harsha Vardhan Malipeddi", "4th year", "2027"),
                               ("Dabbiru Rochan Kumar", "4th year", "2027"),
                               ("Simhadri Sri Teja", "4th year", "2027"),
                               ("Guluvindala Ganesh Manikanta", "3rd year", "2028"),
                               ("Nakka Ugandhar", "3rd year", "2028")], 1):
    mem.append([P(str(i), "cell"), P(n, "cell"), P(y, "cell"), P(g, "cell")])
E.append(styled_table(mem, [10 * mm, 106 * mm, 42 * mm, 42 * mm]))
E.append(P("Five members — within the official 1–5 rule. Mentor and portal registration fields are not stated in this "
           "abstract; they will be supplied from the official portal if required.", "small"))

# ===================== B. Problem & Idea Framing =====================
E.append(P("B · Problem & Idea Framing", "h2"))
E.append(P("Track and specific areas of exploration — combining three:", "h3"))
E.append(P("<b>Smart-home triggers</b> (fan as enabler — ambient temperature/humidity triggers to control connected "
           "devices) · <b>sensor-based multi-directional swing</b> (pan/tilt steering of the full airflow disc) · "
           "<b>blade design for efficiency</b> (composite fan blades for higher air delivery at lower input power). "
           "Why combined: one sensing-and-control chain drives both comfort automation and swing actuation, and the "
           "blades set the operating point that both act on — a single product builds all three coherently.", "body"))
E.append(P("Proposed idea/mechanism, in one paragraph:", "h3"))
E.append(P("The Smart AI Fan is a 1,400 mm-sweep ceiling fan whose local controller reads temperature and humidity and "
           "runs comfort automation with manual-override precedence and defined safe fallback. A self-locking "
           "worm-driven pan/tilt head steers the whole airflow disc (rotor stopped before tilt; tilt clearance-gated); "
           "proposed quasi-isotropic [0/±45/90]s carbon/epoxy blades run on a 24 V sensorless-FOC BLDC drive sized to "
           "IS 374 targets; and a locked-firmware supervisor MCU enforces plausibility gates, tilt interlocks and a "
           "raw power-cut path over the motor and actuators.", "body"))
E.append(P("Baseline-vs-target performance claim, quantified:", "h3"))
bvt = [[P("Metric", "head"), P("Baseline reference", "head"), P("Proposed target", "head"), P("Evidence status", "head")],
       [P("Air delivery", "cell"), P("Fixed-speed reference fan class", "cell"),
        P("≥ 245 m³/min (IS 374 target; ≈ 8.7 m³/min/W indicative at 28.3 W)", "cell"), P("Target; not measured", "cell")],
       [P("Comfort automation", "cell"), P("Manual switching only", "cell"),
        P("Automated response ≤ 5 s; ≥ 95 % success over 10–20 defined scenarios", "cell"), P("Acceptance target", "cell")],
       [P("Airflow direction", "cell"), P("Fixed direction", "cell"),
        P("Steerable airflow ±20° tilt, clearance-gated", "cell"), P("Target; gated by geometry", "cell")],
       [P("Smart-home trigger", "cell"), P("None (no sensing)", "cell"),
        P("Connected-device trigger path (e.g. exhaust on humidity ≥ 65 %RH)", "cell"), P("Demonstrated on safe test load", "cell")],
       [P("Safety fallback", "cell"), P("None defined", "cell"),
        P("Defined safe fallback on sensor disconnect or network loss", "cell"), P("Acceptance target", "cell")]]
E.append(styled_table(bvt, [30 * mm, 42 * mm, 68 * mm, 38 * mm]))
E.append(P("No measured baseline of ours exists; no competitor numbers are invented — every target above is stated as "
           "a target and is traceable to the evidence repository (Section D).", "small"))
E.append(P("Any other technical detail (B): safety scope and boundaries are stated under C; remaining risks and "
           "unresolved items are preserved under D and in the repository's risk register.", "body"))

E.append(PageBreak())

# ===================== C. Technical Feasibility =====================
E.append(P("C · Technical Feasibility", "h2"))
E.append(P("How the product works and why it is technically feasible — core mechanism, key components and "
           "subsystems, and safety-critical handling:", "h3"))
E.append(P("Sensors feed comfort automation and closed-loop sensorless-FOC speed control (settle target ≤ 0.5 s). "
           "Plausibility gates (−10…+80 °C, ≤ 3 K/s) route implausible sensor input to a safe default curve; a hardware "
           "NTC trips at 165 °C; the supervisor enforces a 350 ms watchdog and a raw power-cut path. The self-locking "
           "worm holds pan/tilt position on power loss — backed by absolute encoders, limit switches and hard stops, "
           "so tilt failure needs three simultaneous defenses to breach. Rotor stops before any tilt motion. Every "
           "subsystem maps to standard components, so a safe smart-subsystem demonstrator (sensing, comfort logic, "
           "override, fallback, device triggering on a safe test load) is feasible immediately, while rotor "
           "fabrication and powered-rotor validation stay gated by the T-series programme.", "body"))
E.append(ArchDiagram())
E.append(P("Figure 1. System-level block diagram: sensors/inputs → supervisor MCU → local controller → "
           "FOC drive / pan-tilt worms / device-trigger interface. Priority: supervisor → local → RF remote → web → "
           "automation.", "small"))
E.append(P("Relevant numerical specifications (all values traceable to the repository; full table in the annexure):", "h3"))
rows = load_csv("design_targets.csv")
spec = [[P("Parameter", "head"), P("Value (target)", "head"), P("Evidence status", "head")]]
for r in rows[:14]:
    spec.append([P(r["parameter"], "cell"), P(r["target_value"], "cell"), P(r["evidence_status"], "cell")])
E.append(styled_table(spec, [44 * mm, 72 * mm, 54 * mm]))
E.append(P("Continued in the annexure PDF: full specification table, rotor/containment status (128.8 J vs 130 J — "
           "thin margin, BLOCKED), anchor/suspension factors, clearance derivation, T-00…T-21 validation gates.", "small"))

E.append(PageBreak())

# ===================== D. Execution Feasibility =====================
E.append(P("D · Execution Feasibility", "h2"))
E.append(P("Rough list of components for the product:", "h3"))
bom = load_csv("bom.csv")
bom_rows = [[P("Item", "head"), P("INR", "head"), P("Sourcing flag", "head")]]
for r in bom:
    bom_rows.append([P(r["item"], "cell"), P(f"{float(r['cost_inr']):,.0f}", "cell"),
                     P(r["sourcing_flag"], "cell")])
bom_rows.append([P("BOM total per fan (order of magnitude; no quotations — estimates only)", "cellB"),
                 P(f"{sum(float(r['cost_inr']) for r in bom):,.0f}", "cellB"), P("", "cell")])
E.append(styled_table(bom_rows, [100 * mm, 18 * mm, 52 * mm]))
E.append(P("python calculations/fan_design_calculations.py recomputes and asserts this exact roll-up. "
           "3-fan programme ≈ INR 5.8 lakh (3 × BOM + 10 % contingency + non-recurring programme items), planning level.", "small"))
E.append(P("System-level block diagram:", "h3"))
E.append(P("Figure 1 above (drawn directly from docs/img/system-block-diagram.svg in the repository).", "body"))
E.append(P("Component sourcing risk — custom-fabricated, imported or long-lead:", "h3"))
E.extend(bullets([
    "<b>CFRP blades — CUSTOM + LONG LEAD:</b> [0/±45/90]s prepreg needs mould tooling, autoclave/oven cure and property "
    "verification; no supplier datasheet on file; strength and mass remain assumptions.",
    "<b>Worm actuators — CUSTOM-RATED:</b> ≥ 6 N·m tilt / ≥ 2.5 N·m pan with self-locking at rated torque; "
    "supplier confirmation required (off-the-shelf units may not meet both).",
    "<b>Safety-relevant parts:</b> supervisor power-cut path, limit switches, cable/anchors — ratings must be "
    "confirmed; compliance (hipot/leakage/EMC) must be verified by accredited testing regardless of supplier claims.",
]))
E.append(P("Build plan to Round 2 — abstract to a working Level 1 prototype before the next deadline:", "h3"))
E.extend(bullets([
    "<b>M1:</b> low-voltage sensing + comfort control on a safe test bench (sensors, controller, safe load).",
    "<b>M2:</b> verify override precedence (supervisor → local → RF → web → automation) and safe fallback on sensor "
    "disconnect and network loss.",
    "<b>M3:</b> demonstrate the connected-device trigger on a safe test load.",
    "<b>M4:</b> record results against predefined acceptance tests (16-repo scenario set, accuracy, response time) — "
    "then, only after independent safety review and formal approval, motor/rotor integration for Round 2.",
]))
repo_tbl = [[P("Evidence & calculation repository — every figure in this abstract is checkable there", "head")],
            [P(f"<b>https://{REPO_URL}</b> — contains: all design calculations with formulas and assumptions "
               f"(calculations/fan_design_calculations.py, self-checking), the Round 1 scenario framework and "
               f"controller simulation with 16 acceptance scenarios (check_scenarios.py, data/scenarios.csv), "
               f"the full specification table (data/design_targets.csv), rough BOM (data/bom.csv), validation "
               f"gates T-00…T-21 (data/validation_gates.csv), the preserved risk register (data/risk_register.csv) "
               f"and the formulas document (docs/formulas.md); includes both submission PDF generators.",
               "cell")]]
rt = styled_table(repo_tbl, [170 * mm])
rt.setStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("BACKGROUND", (0, 1), (-1, -1), REPOBG),
             ("BOX", (0, 0), (-1, -1), 0.9, TEAL)])
E.append(Spacer(1, 2))
E.append(rt)

E.append(P("Any other technical detail (D):", "h3"))
E.append(P("This is a paper design — no hardware, nothing measured; targets remain targets. Round 1 covers sensing, "
           "comfort logic, override, safe fallback and device triggering on a safe test setup. Nothing here "
           "authorizes fabrication, energization, powered-rotor or overspeed testing. Unresolved items are preserved, "
           "not hidden — mass roll-up 7.00 vs 6.80 kg; containment 128.8 J vs 130 J; CFRP properties; electrical/EMC "
           "compliance (risk register, closed gate-by-gate T-00…T-21).", "body"))

doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=17 * mm, bottomMargin=16 * mm,
                      title="TECHNOMANCERS_Track1 - atomQUEST 2026 Stage 1 Abstract",
                      author="TECHNOMANCERS (T-2026)")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=header_band, onPageEnd=footer)])
doc.build(E)
print("WROTE", OUT)

# ---- gates: exactly 3 pages, repo URL present, keywords present ----
import pypdf, re
r = pypdf.PdfReader(str(OUT))
full = "\n".join(pg.extract_text() or "" for pg in r.pages)
ok = True
if len(r.pages) != 3:
    print(f"FAIL: {len(r.pages)} pages (target 3)"); ok = False
if REPO_URL not in full:
    print("FAIL: repo URL missing"); ok = False
for need in ["A · Team & Institutional Context", "B · Problem & Idea Framing", "C · Technical Feasibility",
             "D · Execution Feasibility", "Figure 1", "Harsha Vardhan Malipeddi", "Aditya Institute",
             "245 m³/min", "≥ 95 %", "BOM total per fan", "CUSTOM + LONG LEAD", "M1", "M4", "T-00"]:
    if need not in full:
        print("MISSING:", need); ok = False
sys.exit(0 if ok else 1)
