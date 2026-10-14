#!/usr/bin/env python3
"""FINAL ultimate atomQUEST 2026 submission generator.

Rules verified from official / live sources (checked 14 Oct 2026):
- Brief PDF (1789468116558-atomQUEST 2026_Tracks_&_Stage_1_Details.pdf): A/B/C/D structure,
  two/three pager (excluding intro), PDF format, file name TeamName_TrackNo.
- Grad Partners listing (gradpartners.in/e/atomquest-2026-339, LIVE, extracted in full):
  Round 1 "Abstract Submission" OPEN — 16 Sep'26 to 18 Oct'26 18:29 GMT ("3 Days Left");
  registration deadline 17 Oct'26; entries must be a "two-three page abstract
  (not exceeding 600 words)" in PDF; deadlines strict; file via submission guidelines
  (the brief's A/B/C/D structure). The brief's older 11 Oct date is superseded by the portal.
- Internshala listing: teams of 1-5 members (5 members = compliant).

Interpretation (strictest, cannot fail either reading): the uploaded
TECHNOMANCERS_Track1.pdf is 2 pages total with EVERY visible word counted
(only the repeated running header band and page footnote are excluded as boilerplate).
The countable gate hard-fails the build if it exceeds 600 words.

Output: TECHNOMANCERS_Track1.pdf  — 2-page A/B/C/D abstract, total text <= 600 words.
        TECHNOMANCERS_Track1_Annexure.pdf — companion detail (separate file; NEIT specified).
No measured results, approvals, or certification are asserted anywhere.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Flowable, PageBreak)

NAVY = HexColor("#1F3A5F")
TEAL = HexColor("#0E7C7B")
LIGHT = HexColor("#EAF3F6")
RULE = HexColor("#B9C8D3")
INK = HexColor("#16222E")

S = dict(
    title=ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=15, leading=18,
                          textColor=NAVY, alignment=TA_CENTER, spaceAfter=2),
    subtitle=ParagraphStyle("subtitle", fontName="Helvetica", fontSize=9.5, leading=12,
                             textColor=TEAL, alignment=TA_CENTER, spaceAfter=5),
    h2=ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
                       textColor=NAVY, spaceBefore=7, spaceAfter=2.5),
    body=ParagraphStyle("body", fontName="Helvetica", fontSize=8.8, leading=11.6,
                         textColor=INK, alignment=TA_JUSTIFY, spaceAfter=3),
    cell=ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=10, textColor=INK),
    cellB=ParagraphStyle("cellB", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=INK),
    head=ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=white),
    small=ParagraphStyle("small", fontName="Helvetica-Oblique", fontSize=7.6, leading=9.6,
                          textColor=HexColor("#5A6B7A"), spaceBefore=2),
)

def P(t, s="body"): return Paragraph(t, S[s])
def bullets(items): return [Paragraph(t, S["body"], bulletText="•") for t in items]

def styled_table(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0,0), (-1,-1), 0.5, RULE), ("VALIGN", (0,0), (-1,-1), "TOP"),
             ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
             ("TOPPADDING", (0,0), (-1,-1), 2.2), ("BOTTOMPADDING", (0,0), (-1,-1), 2.2)]
    if header:
        style += [("BACKGROUND", (0,0), (-1,0), NAVY), ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, LIGHT])]
    return t

class ArchDiagram(Flowable):
    def __init__(self, width=168*mm, height=58*mm):
        super().__init__(); self.width=width; self.height=height
    def draw(self):
        c = self.canv
        def box(x,y,w,h,label,fill,txtcol=white,fs=6.6):
            c.saveState(); c.setFillColor(fill); c.setStrokeColor(NAVY); c.setLineWidth(0.9)
            c.roundRect(x,y,w,h,3*mm,stroke=1,fill=1)
            c.setFillColor(txtcol); c.setFont("Helvetica-Bold",fs)
            lines = label.split("\n"); lh = fs+1.5
            y0 = y+h/2+(len(lines)-1)*lh/2-fs*0.75
            for ln in lines:
                c.drawCentredString(x+w/2, y0, ln); y0 -= lh
            c.restoreState()
        def arrow(x1,y1,x2,y2,col=NAVY):
        
            import math
            c.setStrokeColor(col); c.setLineWidth(1.0); c.line(x1,y1,x2,y2)
            ang = math.atan2(y2-y1,x2-x1)
            for s in (+0.42,-0.42):
                c.line(x2,y2, x2-3*mm*math.cos(ang+s), y2-3*mm*math.sin(ang+s))
        w,h = self.width, self.height
        box(4*mm, h-12*mm, 30*mm, 9*mm, "Temp/humidity\nsensors", TEAL, fs=6.0)
        box(40*mm, h-12*mm, 28*mm, 9*mm, "Web/app\n(TLS 1.3)", LIGHT, txtcol=NAVY, fs=6.0)
        box(73*mm, h-12*mm, 28*mm, 9*mm, "RF remote +\noverride", LIGHT, txtcol=NAVY, fs=6.0)
        box(105*mm, h-12*mm, 28*mm, 9*mm, "Encoders +\nswitches", TEAL, fs=6.0)
        box(137*mm, h-12*mm, 14*mm, 9*mm, "Safe\nload", LIGHT, txtcol=NAVY, fs=6.0)
        box(30*mm, h-33*mm, 104*mm, 12*mm, "SAFETY SUPERVISOR MCU — locked fw · raw power cut", NAVY, fs=6.0)
        box(30*mm, h-49*mm, 104*mm, 11*mm, "LOCAL CONTROLLER — comfort automation + FOC", TEAL, fs=6.0)
        box(6*mm, h-65*mm, 62*mm, 10*mm, "24 V BLDC drive\n(sensorless FOC)", NAVY, fs=6.0)
        box(73*mm, h-65*mm, 56*mm, 10*mm, "Pan/tilt worm actuator\n(12 V, self-locking)", NAVY, fs=6.0)
        box(134*mm, h-65*mm, 27*mm, 10*mm, "Connected\ndevices", LIGHT, txtcol=NAVY, fs=6.0)
        arrow(20*mm, h-23*mm, 53*mm, h-23.2*mm, TEAL)
        arrow(55*mm, h-23*mm, 62*mm, h-23.2*mm)
        arrow(90*mm, h-23*mm, 85*mm, h-23.2*mm)
        arrow(122*mm, h-23*mm, 113*mm, h-23.2*mm, TEAL)
        arrow(82*mm, h-33*mm, 82*mm, h-37.5*mm)
        c.setFillColor(NAVY); c.setFont("Helvetica", 5.8); c.drawString(84*mm, h-37*mm, "power-cut")
        arrow(60*mm, h-49*mm, 40*mm, h-56*mm)
        arrow(116*mm, h-49*mm, 104*mm, h-56*mm)
        arrow(110*mm, h-44*mm, 146*mm, h-57*mm, TEAL)

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE); canvas.setLineWidth(0.6)
    canvas.line(15*mm, 12.5*mm, A4[0]-15*mm, 12.5*mm)
    canvas.setFillColor(HexColor("#5A6B7A")); canvas.setFont("Helvetica", 7.5)
    canvas.drawString(15*mm, 9*mm, "TECHNOMANCERS · atomQUEST 2026 · Track 1 Fan")
    canvas.drawRightString(A4[0]-15*mm, 9*mm, "Page %d" % doc.page)
    canvas.restoreState()

def header_band(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY); canvas.rect(0, A4[1]-11*mm, A4[0], 11*mm, stroke=0, fill=1)
    canvas.setFillColor(TEAL); canvas.rect(0, A4[1]-12.2*mm, A4[0], 1.2*mm, stroke=0, fill=1)
    canvas.setFillColor(white); canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(15*mm, A4[1]-7.6*mm, "atomQUEST 2026 — Stage 1 Abstract · TECHNOMANCERS · T-2026")
    canvas.drawRightString(A4[0]-15*mm, A4[1]-7.6*mm, "Track 1 · Fan")
    canvas.restoreState()

def make_doc(path, title, pages_template=None):
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                          topMargin=17*mm, bottomMargin=16*mm, title=title,
                          author="TECHNOMANCERS (T-2026)")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    onPage = header_band if pages_template is None else (lambda c, d: None)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                          onPage=header_band if pages_template is None else None,
                          onPageEnd=footer if pages_template is None else footer)])
    return doc

#undersch =====================================================================================
# FILE 1: TECHNOMANCERS_Track1.pdf — 2 pages, A/B/C/D, EVERY visible word counted
# =====================================================================================
E = []
E.append(P("Smart AI Fan", "title"))

# ---- A. Team & Institutional Context ----
E.append(P("A · Team & Institutional Context", "h2"))
team = [
    [P("Team name", "head"), P("Code", "head"), P("Institution", "head"), P("Department", "head")],
    [P("TECHNOMANCERS", "cellB"), P("T-2026", "cell"),
     P("Aditya Institute of Technology and Management, Tekkali", "cell"),
     P("Electronics and Communication Engineering", "cell")],
]
E.append(styled_table(team, [34*mm, 18*mm, 74*mm, 44*mm]))
E.append(Spacer(1, 3))
E.append(P("Members (5): Harsha Vardhan Malipeddi, Dabbiru Rochan Kumar, Simhadri Sri Teja, Guluvindala Ganesh "
           "Manikanta, Nakka Ugandhar. Corresponding author: H. V. Malipeddi (harshavardhanmalipeddi1@gmail.com).", "body"))

# ---- B. Problem & Idea Framing ----
E.append(P("B · Problem & Idea Framing", "h2"))
E.append(P("Track 1 Fan — combining smart-home triggers, sensor-based multi-directional swing, and blade-design "
           "efficiency: one sensing-and-control system drives comfort automation and swing, while the blades set the "
           "operating point both act on.", "body"))
E.append(P("Proposed idea/mechanism (one paragraph): a 1,400 mm-sweep ceiling fan. A local controller reads "
           "temperature/humidity to run comfort automation with manual-override precedence and defined safe fallback; "
           "a self-locking worm pan/tilt head steers the whole airflow disc (rotor stopped before tilt; clearance ≥ 2.65 m "
           "for ±20°); quasi-isotropic [0/±45/90]s carbon/epoxy blades run on a 24 V FOC BLDC drive, overseen by a "
           "locked-firmware supervisor MCU that can cut actuator power on any anomaly.", "body"))
E.append(P("Baseline-vs-target, quantified: no measured baseline of ours exists. Versus a fixed-speed, fixed-direction, "
           "manual fan: steerable airflow (±20° tilt); automated response ≤ 5 s with ≥ 95 % success over 10–20 scenarios; "
           "a device-trigger path; defined safe fallback on sensor/network loss. Air delivery ≥ 245 m³/min and service "
           "value ≥ 4.1 m³/min/W are IS 374 targets; ≈ 8.7 m³/min/W is indicative (245 ÷ 28.3 W), not measured.", "body"))
E.append(P("Other technical detail: safety scope in C; remaining risks in D.", "body"))

# ---- C. Technical Feasibility ----
E.append(PageBreak())

# ---- C. Technical Feasibility (page 2) ----
E.append(P("C · Technical Feasibility", "h2"))
E.append(P("Sensors feed comfort automation and closed-loop FOC speed control (≤ 0.5 s). Plausibility gates "
           "(−10…+80 °C, ≤ 3 K/s) route implausible input to a safe default curve; a hardware NTC trips at 165 °C; the "
           "self-locking worm holds position on power loss, backed by encoders, limit switches and supervisor "
           "power-cut — three independent defenses. All subsystems are standard parts; a safe demonstrator is feasible "
           "now; rotor validation stays gated.", "body"))
E.append(ArchDiagram())
E.append(P("Figure 1. Priority: supervisor → local → RF → web → automation.", "small"))
E.append(P("Key specifications (paper values): 380 RPM top, tip 27.86 m/s under the 30 m/s cap; rotor energy ≈ 89.5 J; "
           "blade 165 g; worm ≥ 6/2.5 N·m; anchor demand 139.9 N vs 1,500 N ultimate; cable 6.5 kN; electrical per "
           "IS 302-2-80 — compliance not established. 456 RPM is a hazard case, never a target.", "body"))

# ---- D. Execution Feasibility ----
E.append(P("D · Execution Feasibility", "h2"))
E.append(P("Rough components: composite rotor (custom), 24 V FOC BLDC motor + controller, supervisor + local MCU pair, "
           "temp/humidity sensors, worm actuators (custom-rated) with encoders/limit switches, 24 V SMPS, optional "
           "Wi-Fi/BLE, RF remote + override, device trigger or safe test load, instrumentation, safety cable.", "body"))
E.append(P("Rough cost/BOM (order of magnitude, no quotations): ≈ INR 26,650 per fan; ≈ INR 5.8 lakh (3-fan "
           "programme). Sourcing risk: custom CFRP blades (tooling, cure, verification; no supplier datasheet yet); worm "
           "actuators need confirmation of self-lock at rated torque.", "body"))
E.append(P("Build plan to Round 2: (1) low-voltage sensing + comfort-control demonstrator; (2) verify override "
           "precedence and sensor-disconnect/network-loss fallback; (3) device trigger on a safe test load; "
           "(4) record results against predefined acceptance tests; (5) motor/rotor integration for Round 2 only after "
           "safety review and approval.", "body"))
E.append(P("Any other technical detail: paper design only — no hardware, nothing measured. No authorization for "
           "fabrication, energization, powered-rotor testing, installation, or certification.", "body"))

doc1 = make_doc("TECHNOMANCERS_Track1.pdf", "TECHNOMANCERS_Track1 - atomQUEST 2026 Stage 1 Abstract")
doc1.build(E)
print("WROTE TECHNOMANCERS_Track1.pdf")

# ---- word gate: EVERY visible word in the whole PDF (2-page doc), only the running
#      header band and page footnote excluded as boilerplate. Hard-fail > 600. ----
import pypdf, re, sys
r = pypdf.PdfReader("TECHNOMANCERS_Track1.pdf")
full = " ".join(pg.extract_text() for pg in r.pages)
full = re.sub(r"atomQUEST 2026 — Stage 1 Abstract · TECHNOMANCERS · T-2026", " ", full)
full = re.sub(r"Track 1 · Fan", " ", full)
full = re.sub(r"TECHNOMANCERS · atomQUEST 2026 · Track 1 Fan Page \d+", " ", full)
n = len(re.findall(r"\S+", full))
print("TOTAL visible words (excl. running header/footer):", n)
if n > 600:
    sys.exit(f"FAIL: abstract {n} words exceeds the 600-word rule")
if len(r.pages) > 2:
    sys.exit(f"FAIL: abstract is {len(r.pages)} pages, exceeds the two/three pager rule")

# =====================================================================================
# FILE 2: companion annexure (separate file; not the word-limited abstract)
# =====================================================================================
X = []
X.append(P("Smart AI Fan — Technical Annexure", "title"))
X.append(P("TECHNOMANCERS · atomQUEST 2026 Track 1 · companion detail to TECHNOMANCERS_Track1.pdf", "subtitle"))
X.append(P("Note: annexure for reviewers/internal use only. The required submission is TECHNOMANCERS_Track1.pdf "
           "(2 pages, A/B/C/D, ≤ 600 words); attach this only if the portal permits additional files.", "small"))

X.append(P("Live submission status (Grad Partners portal, checked 14 Oct 2026)", "h2"))
X.append(P("Round 1 Abstract Submission: OPEN, 16 Sep 2026 – 18 Oct 2026, 18:29 GMT. Registration deadline 17 Oct 2026. "
           "Portal ruling: 'two-three page abstract (not exceeding 600 words)' in PDF; deadlines strict; the brief's "
           "earlier 11 October date is superseded by the portal. Round 2 is a 90-second video (21–30 Oct).", "body"))

X.append(P("Full design-target and specification table", "h2"))
tg = [
    [P("Parameter", "head"), P("Value (target)", "head"), P("Evidence status", "head")],
    [P("Air delivery", "cell"), P("≥ 245 m³/min (IS 374:2019+Amd.1 Table 1)", "cell"), P("Design target; not measured", "cell")],
    [P("Service value", "cell"), P("≥ 4.1 m³/min/W required; ≈ 8.7 expected at ≈ 28.3 W input", "cell"), P("Indicative calculation only", "cell")],
    [P("Blade-tip speed", "cell"), P("≤ 30 m/s cap; 27.86 m/s at 380 RPM", "cell"), P("Calculated", "cell")],
    [P("Temp/humidity accuracy", "cell"), P("± 0.5 °C / ± 3 %RH vs calibrated reference", "cell"), P("Prototype acceptance target", "cell")],
    [P("Response time", "cell"), P("≤ 5 s (local mode)", "cell"), P("Prototype acceptance target", "cell")],
    [P("Automation success", "cell"), P("≥ 95 % over 10–20 defined scenarios", "cell"), P("Prototype acceptance target", "cell")],
    [P("Rotor", "cell"), P("Inertia ≈ 0.113 kg·m²; energy ≈ 89.5 J @380, 128.8 J @456 (hazard case)", "cell"), P("Calculated from target masses", "cell")],
    [P("Blades", "cell"), P("[0/±45/90]s carbon/epoxy, 2 mm skin, ≈ 1.55 g/cc, ≈ 70 GPa, 165 g/blade", "cell"), P("Assumptions pending T-01/T-05 + supplier data", "cell")],
    [P("Motor", "cell"), P("≥ 0.62 N·m cont., ≥ 2.5 N·m 5 s peak, ≥ 25 W mech; O/C ≤ 20 µs; NTC 165 °C", "cell"), P("Specified on paper", "cell")],
    [P("Suspension", "cell"), P("139.9 N demand vs 600 N working / 1,500 N ultimate; cable 6.5 kN", "cell"), P("Calculated", "cell")],
    [P("Clearance", "cell"), P("≥ 2.65 m → ±20° with 1.50 m floor clearance; below 2.60 m tilt disabled", "cell"), P("Corrected derivation", "cell")],
]
X.append(styled_table(tg, [40*mm, 78*mm, 52*mm]))

X.append(P("Unresolved risks and open items (preserved deliberately)", "h2"))
risk = [
    [P("Item", "head"), P("State", "head")],
    [P("Paper design; no hardware", "cell"), P("Nothing measured; all figures are calculated or stated targets", "cell")],
    [P("Moving-mass roll-up", "cell"), P("UNRECONCILED: 7.00 kg listed vs stated 6.80 kg; both retained pending evidence", "cell")],
    [P("CFRP strength/mass/CoM", "cell"), P("Require T-01, T-05 coupons, supplier data, failure criterion", "cell")],
    [P("Blade containment", "cell"), P("128.8 J vs 130 J rating — thin margin; BLOCKED pending basis and authorization", "cell")],
    [P("Tip deflection", "cell"), P("Requires FEA and T-04; paper ≈ 0.55–0.6 mm vs 1 mm", "cell")],
    [P("Electrical/EMC/BIS", "cell"), P("Not established; accredited-lab testing pending (T-12/T-13/T-21)", "cell")],
    [P("Validation programme", "cell"), P("22 gates T-00…T-21; production only if all pass on hardware", "cell")],
]
X.append(styled_table(risk, [55*mm, 115*mm]))

X.append(P("Remaining confirmations", "h2"))
X.extend(bullets([
    "Team code T-2026 — verify against the official portal.",
    "Submission: upload to Grad Partners portal before 18 Oct 2026, 18:29 GMT; entries editable until deadline.",
    "Filename rule TeamName_TrackNo followed (TECHNOMANCERS_Track1.pdf); confirm exact portal field on upload.",
    "Mentor requirement — not stated; supply if portal requires.",
    "Supplier quotations — none obtained; all costs are estimates.",
]))

doc2 = make_doc("TECHNOMANCERS_Track1_Annexure.pdf", "TECHNOMANCERS_Track1 - Technical Annexure (pain design review pack)")
doc2.build(X)
print("WROTE TECHNOMANCERS_Track1_Annexure.pdf")
