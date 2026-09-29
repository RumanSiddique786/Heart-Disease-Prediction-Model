from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Flowable,
                                 Image as RLImage, KeepTogether, PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
import random, string, os
 
# ==============================================================================
# COLORS
# ==============================================================================
DARK_BLUE    = colors.HexColor("#1A3A6B")
MED_BLUE     = colors.HexColor("#2E6DA4")
LIGHT_BLUE   = colors.HexColor("#EAF2FB")
CRED         = colors.HexColor("#C0392B")
LIGHT_RED    = colors.HexColor("#FDEDEC")
CGREEN       = colors.HexColor("#1A7A4A")
LIGHT_GREEN  = colors.HexColor("#EAFAF1")
CORANGE      = colors.HexColor("#D35400")
CGRAY        = colors.HexColor("#F4F6F7")
DARK_GRAY    = colors.HexColor("#5D6D7E")
CWHITE       = colors.white
CBLACK       = colors.HexColor("#1C2833")
BORDER       = colors.HexColor("#BFC9CA")
 
# ==============================================================================
# PROGRESS BAR
# ==============================================================================
class ProgressBar(Flowable):
    def __init__(self, width, height, pct, bar_color):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.pct = pct
        self.bar_color = bar_color
 
    def draw(self):
        self.canv.setFillColor(colors.HexColor("#D5D8DC"))
        self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
        fw = max(12, self.width * (self.pct / 100))
        self.canv.setFillColor(self.bar_color)
        self.canv.roundRect(0, 0, fw, self.height, 5, fill=1, stroke=0)
        self.canv.setFillColor(CWHITE)
        self.canv.setFont("Helvetica-Bold", 8)
        self.canv.drawCentredString(self.width / 2, 3.5, f"{self.pct:.1f}%")
 
# ==============================================================================
# HELPERS
# ==============================================================================
def S(name, font='Helvetica', size=9, color=None, align=TA_LEFT,
      bold=False, leading=14, italic=False):
    if color is None:
        color = CBLACK
    if bold: fn = 'Helvetica-Bold'
    elif italic: fn = 'Helvetica-Oblique'
    else: fn = font
    return ParagraphStyle(name, fontName=fn, fontSize=size,
                          textColor=color, alignment=align, leading=leading)
 
def sec_hdr(title, color=None):
    if color is None:
        color = DARK_BLUE
    t = Table([[Paragraph(f"  {title}",
                           S('sh', bold=True, size=9.5, color=CWHITE))]],
              colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), color),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]))
    return t
 
def sc(status):
    s = status.upper()
    if any(w in s for w in ["NORMAL","GOOD","LOWER","HEALTHY"]): return CGREEN
    if any(w in s for w in ["HIGH","ABNORMAL","DEFECT","ELEVATED"]): return CRED
    if any(w in s for w in ["BORDER","MILD","MODERATE","FLAT","LOW"]): return CORANGE
    return DARK_GRAY
 
def pc(text, bold=False, size=8.5, color=None, align=TA_LEFT):
    if color is None:
        color = CBLACK
    return Paragraph(text, S(f'pc{text[:4]}', bold=bold, size=size,
                               color=color, align=align, leading=13))
 
# ==============================================================================
# MAIN FUNCTION
# ==============================================================================
def create_cardioguard_report(age, sex, cp, trestbps, chol, thalach,
                               exang, oldpeak, slope, ca, thal,
                               fbs, restecg,
                               risk_level, probability, model_name,
                               logo_path=None, patient_name="[Patient Name]"):
 
    buffer   = BytesIO()
    W        = 170 * mm
    is_high  = (risk_level == "High Risk")
    prob_val = float(probability)
    rep_id   = "CG-" + "".join(random.choices(string.digits, k=8))
    rep_date = datetime.now().strftime("%d %B %Y")
    rep_time = datetime.now().strftime("%I:%M %p")
 
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=10*mm, bottomMargin=10*mm)
    story = []
 
    # ── HEADER ────────────────────────────────────────────────────
    if logo_path and os.path.exists(logo_path):
        logo_cell = RLImage(logo_path, width=55*mm, height=25*mm)
    else:
        logo_cell = Paragraph("CardioGuard",
                               S('lg', bold=True, size=16, color=DARK_BLUE))
 
    hdr_right = Table([
        [Paragraph("CardioGuard AI Healthcare Report",
                    S('h1', bold=True, size=13, color=DARK_BLUE))],
        [Paragraph("Cardiac Risk Assessment  |  AI & Machine Learning Division",
                    S('h2', size=8, color=DARK_GRAY, leading=12))],
        [Paragraph("KMCLU Medical Center, Lucknow  |  cardio@kmclu.ac.in",
                    S('h3', size=7.5, color=DARK_GRAY, leading=12))],
        [Paragraph("www.cardioguard.health  |  Helpline: 1800-CARDIO",
                    S('h4', size=7.5, color=DARK_GRAY, leading=12))],
    ], colWidths=[108*mm])
    hdr_right.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 1),
        ('BOTTOMPADDING', (0,0),(-1,-1), 1),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
    ]))
 
    hdr = Table([[logo_cell, hdr_right]], colWidths=[60*mm, 110*mm])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), LIGHT_BLUE),
        ('BOX',           (0,0),(-1,-1), 2,   DARK_BLUE),
        ('LINEAFTER',     (0,0),(0,-1),  1,   BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 1*mm))
    story.append(Table(
        [[Paragraph("CARDIAC RISK ASSESSMENT REPORT",
                     S('tt', bold=True, size=11, color=CWHITE, align=TA_CENTER))]],
        colWidths=[W],
        style=[('BACKGROUND',(0,0),(-1,-1),DARK_BLUE),
               ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]
    ))
    story.append(Spacer(1, 2*mm))
 
    # ── PATIENT INFO ──────────────────────────────────────────────
    def lbl(t): return Paragraph(t, S('l', bold=True, size=8.5, color=DARK_GRAY))
    def val(t): return Paragraph(str(t), S('v', size=8.5, leading=13))
 
    pi = Table([
        [lbl("Patient Name:"), val(patient_name), lbl("Report ID:"),   val(rep_id)],
        [lbl("Age / Gender:"), val(f"{age} yrs / {sex}"), lbl("Report Date:"), val(rep_date)],
        [lbl("Doctor:"),       val("[Doctor Name]"), lbl("Report Time:"),  val(rep_time)],
    ], colWidths=[36*mm, 49*mm, 36*mm, 49*mm])
    pi.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[CGRAY,CWHITE]),
        ('BOX',          (0,0),(-1,-1),1,BORDER),
        ('INNERGRID',    (0,0),(-1,-1),0.3,BORDER),
        ('TOPPADDING',   (0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',  (0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
    ]))
    story.append(KeepTogether([sec_hdr("PATIENT INFORMATION"),
                                Spacer(1,2*mm), pi, Spacer(1,3*mm)]))
 
    # ── CLINICAL PARAMETERS ───────────────────────────────────────
    cp_map   = {"1":"Typical Angina","2":"Atypical Angina","3":"Non-Anginal Pain",
                "4":"Asymptomatic (No Chest Pain)",
                "Typical Angina (1)":"Typical Angina","Atypical Angina (2)":"Atypical Angina",
                "Non-anginal Pain (3)":"Non-Anginal Pain","Asymptomatic (4)":"Asymptomatic (No Chest Pain)"}
    slope_map= {"1":"Upsloping","2":"Flat","3":"Downsloping",
                "Upsloping (1)":"Upsloping","Flat (2)":"Flat","Downsloping (3)":"Downsloping"}
    thal_map = {"3":"Normal","6":"Fixed Defect","7":"Reversible Defect",
                "Normal (3)":"Normal","Fixed Defect (6)":"Fixed Defect",
                "Reversible Defect (7)":"Reversible Defect"}
    recg_map = {"0":"Normal","1":"ST-T Wave Abnormality","2":"LV Hypertrophy",
                "Normal (0)":"Normal","ST-T Abnormality (1)":"ST-T Wave Abnormality",
                "LV Hypertrophy (2)":"LV Hypertrophy"}
 
    fbs_str   = "High (> 120 mg/dl)" if str(fbs) in ["1","Yes"] else "Normal"
    fbs_st    = "Abnormal" if str(fbs) in ["1","Yes"] else "Normal"
    exang_str = "Yes" if str(exang) in ["1","Yes"] else "No"
    exang_st  = "Abnormal" if str(exang) in ["1","Yes"] else "Normal"
    cp_str    = cp_map.get(str(cp), str(cp))
    thal_str  = thal_map.get(str(thal), str(thal))
    thal_raw  = thal_map.get(str(thal), "Normal")
    recg_str  = recg_map.get(str(restecg), str(restecg))
    slope_str = slope_map.get(str(slope), str(slope))
 
    def bps(v):
        v=int(v)
        return "Low" if v<90 else "Normal" if v<=120 else "Elevated" if v<=139 else "High"
    def chols(v):
        v=int(v)
        return "Normal" if v<200 else "Borderline" if v<=239 else "High"
    def hrs(v):
        v=int(v)
        return "Low" if v<100 else "Normal" if v<=170 else "High"
    def ops(v):
        v=float(str(v))
        return "Normal" if v<=0 else "Mild" if v<=1.0 else "Moderate" if v<=2.0 else "High"
 
    status_list = [
        bps(trestbps), chols(chol), hrs(thalach), fbs_st,
        "Normal" if str(restecg) in ["0","Normal (0)"] else "Abnormal",
        "Normal" if str(cp) in ["1","Typical Angina (1)"] else "Abnormal",
        exang_st, ops(oldpeak),
        "Normal" if str(slope) in ["1","Upsloping (1)"] else "Abnormal",
        "Normal" if str(ca)=="0" else "Abnormal",
        "Normal" if thal_raw=="Normal" else "Abnormal",
    ]
 
    param_rows = [
        [pc("Resting Blood Pressure"), pc(f"{trestbps} mm Hg"), pc("90 – 120 mm Hg")],
        [pc("Serum Cholesterol"),       pc(f"{chol} mg/dl"),    pc("Below 200 mg/dl")],
        [pc("Maximum Heart Rate"),      pc(f"{thalach} bpm"),   pc("100 – 170 bpm")],
        [pc("Fasting Blood Sugar"),     pc(fbs_str),            pc("Below 120 mg/dl")],
        [pc("Resting ECG"),             pc(recg_str),           pc("Normal")],
        [pc("Chest Pain Type"),         pc(cp_str),             pc("Typical Angina")],
        [pc("Exercise-Induced Angina"), pc(exang_str),          pc("No")],
        [pc("ST Depression (Oldpeak)"), pc(f"{oldpeak} mm"),    pc("0 – 1.0 mm")],
        [pc("Slope of ST Segment"),     pc(slope_str),          pc("Upsloping")],
        [pc("Major Vessels Blocked"),   pc(str(ca)),            pc("0 (None)")],
        [pc("Thalassemia"),             pc(thal_str),           pc("Normal")],
    ]
    # Add status column
    for i, sv in enumerate(status_list):
        param_rows[i].append(
            Paragraph(sv, S(f'st{i}', bold=True, size=8.5,
                             color=sc(sv), align=TA_CENTER, leading=13))
        )
 
    pt = Table(
        [[pc("Parameter",True), pc("Value Recorded",True),
          pc("Normal Range",True), pc("Status",True)]] + param_rows,
        colWidths=[54*mm, 48*mm, 40*mm, 28*mm]
    )
    pt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  DARK_BLUE),
        ('TEXTCOLOR',     (0,0),(-1,0),  CWHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0),  9),
        ('ALIGN',         (0,0),(-1,0),  'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [CGRAY,CWHITE]),
        ('BOX',           (0,0),(-1,-1), 1,BORDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.3,BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',         (3,1),(-1,-1), 'CENTER'),
    ]))
 
    story.append(KeepTogether([sec_hdr("CLINICAL PARAMETERS"),
                                Spacer(1,2*mm), pt, Spacer(1,3*mm)]))
 
    # ── AI PREDICTION RESULT ──────────────────────────────────────
    rc    = CRED if is_high else CGREEN
    rbg   = LIGHT_RED if is_high else LIGHT_GREEN
    rlbl  = "HIGH RISK"  if is_high else "LOW RISK"
    rrslt = "HEART DISEASE DETECTED" if is_high else "NO HEART DISEASE DETECTED"
    rsub  = ("Multiple clinical indicators suggest a high probability of heart disease. "
             "Immediate medical attention is strongly recommended."
             if is_high else
             "Your clinical indicators are within acceptable ranges. "
             "Continue regular health monitoring and preventive care.")
    conf  = "High Confidence"
 
    # Left panel — risk label stacked above result label with clear spacing
    left_panel = Table([
        [Paragraph(rlbl,  S('rl', bold=True, size=20, color=rc,
                              align=TA_CENTER, leading=28))],
        [Spacer(1, 3*mm)],
        [Paragraph(rrslt, S('rr', bold=True, size=8, color=rc,
                              align=TA_CENTER, leading=13))],
    ], colWidths=[42*mm])
    left_panel.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]))
 
    banner = Table([[
        left_panel,
        Paragraph(rsub, S('rs', size=9, color=DARK_GRAY,
                           align=TA_JUSTIFY, leading=15)),
    ]], colWidths=[44*mm, 126*mm])
    banner.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), rbg),
        ('BOX',           (0,0),(-1,-1), 2, rc),
        ('LINEAFTER',     (0,0),(0,-1),  1, BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
 
    prob_row = Table([[
        Paragraph("Risk Probability",
                   S('rp', bold=True, size=8.5, color=DARK_GRAY)),
        ProgressBar(88*mm, 16, prob_val, rc),
        Paragraph(conf, S('cl', bold=True, size=8.5, color=rc, align=TA_CENTER)),
    ]], colWidths=[34*mm, 96*mm, 40*mm])
    prob_row.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CGRAY),
        ('BOX',           (0,0),(-1,-1), 0.5, BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',         (2,0),(-1,-1), 'CENTER'),
    ]))
 
    model_row = Table([[
        Paragraph("AI Model Used:", S('ml', bold=True, size=8, color=DARK_GRAY)),
        Paragraph(model_name,       S('mv', size=8, color=CBLACK)),
        Paragraph(f"Generated: {rep_date}  {rep_time}",
                   S('md', size=8, color=DARK_GRAY, align=TA_CENTER)),
    ]], colWidths=[30*mm, 80*mm, 60*mm])
    model_row.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), LIGHT_BLUE),
        ('BOX',           (0,0),(-1,-1), 0.5, BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
 
    story.append(KeepTogether([
        sec_hdr("AI PREDICTION RESULT", color=rc),
        Spacer(1, 2*mm), banner,
        Spacer(1, 1*mm), prob_row,
        Spacer(1, 1*mm), model_row,
        Spacer(1, 3*mm),
    ]))
 
    risk_rows = []
    if str(cp) in ["4","Asymptomatic (4)"]:
        risk_rows.append(("No Chest Pain (Asymptomatic)",
            "No chest pain felt even when heart disease is present — a silent but serious warning sign.", "High"))
    if str(ca) not in ["0"]:
        risk_rows.append((f"{ca} Blood Vessel(s) Blocked",
            f"{ca} major heart vessel(s) are narrowed or blocked, reducing blood supply to the heart.", "High"))
    if thal_raw == "Reversible Defect":
        risk_rows.append(("Reversible Thalassemia Defect",
            "Blood flow to the heart reduces during activity but recovers at rest — a strong sign of coronary artery disease.", "High"))
    elif thal_raw == "Fixed Defect":
        risk_rows.append(("Fixed Thalassemia Defect",
            "A part of the heart has permanently reduced blood flow, possibly from previous damage.", "Moderate"))
    if float(str(oldpeak)) > 2.0:
        risk_rows.append(("High ST Depression",
            f"ST depression of {oldpeak} mm during exercise means the heart is not getting enough blood under physical effort.", "High"))
    elif float(str(oldpeak)) > 1.0:
        risk_rows.append(("Mild ST Depression",
            f"ST depression of {oldpeak} mm is slightly above normal — the heart shows mild stress during exercise.", "Moderate"))
    if int(trestbps) > 139:
        risk_rows.append(("High Blood Pressure",
            f"BP of {trestbps} mm Hg is above normal. High blood pressure puts constant extra strain on the heart.", "High"))
    elif int(trestbps) > 120:
        risk_rows.append(("Elevated Blood Pressure",
            f"BP of {trestbps} mm Hg is slightly above normal and gradually increases heart workload.", "Moderate"))
    if int(chol) > 239:
        risk_rows.append(("High Cholesterol",
            f"Cholesterol of {chol} mg/dl is high and builds plaque in arteries, reducing blood flow to the heart.", "High"))
    elif int(chol) > 199:
        risk_rows.append(("Borderline Cholesterol",
            f"Cholesterol of {chol} mg/dl is slightly above ideal. Diet changes can bring it under control.", "Moderate"))
    if str(exang) in ["1","Yes"]:
        risk_rows.append(("Chest Pain During Exercise",
            "Chest discomfort during physical activity means the heart is not getting enough blood when working harder.", "High"))
    if int(thalach) < 100:
        risk_rows.append(("Low Maximum Heart Rate",
            f"Max heart rate of {thalach} bpm is below the expected range — indicates reduced cardiac fitness.", "Moderate"))
    if str(fbs) in ["1","Yes"]:
        risk_rows.append(("High Fasting Blood Sugar",
            "Blood sugar above 120 mg/dl may indicate diabetes, which significantly increases heart disease risk.", "Moderate"))
    if not risk_rows:
        risk_rows.append(("No Major Risk Factors Found",
            "All clinical values are within acceptable ranges. Maintain a healthy lifestyle.", "Normal"))
 
    rf_hdr_row = [
        Paragraph("Risk Factor",    S('rfh1', bold=True, size=9, color=CWHITE)),
        Paragraph("What It Means",  S('rfh2', bold=True, size=9, color=CWHITE)),
        Paragraph("Level",          S('rfh3', bold=True, size=9, color=CWHITE, align=TA_CENTER)),
    ]
    rf_data = []
    for nm, exp, lv in risk_rows:
        rf_data.append([
            Paragraph(nm,  S(f'rfn{nm[:4]}', bold=True, size=8.5,
                              color=DARK_BLUE, leading=13)),
            Paragraph(exp, S(f'rfe{nm[:4]}', size=8.5, leading=13,
                              color=CBLACK, align=TA_JUSTIFY)),
            Paragraph(lv,  S(f'rfl{nm[:4]}', bold=True, size=8.5,
                              color=sc(lv), align=TA_CENTER, leading=13)),
        ])
 
    rf = Table([rf_hdr_row] + rf_data,
               colWidths=[44*mm, 106*mm, 20*mm])
    rf.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  MED_BLUE),
        ('TEXTCOLOR',     (0,0),(-1,0),  CWHITE),
        ('ALIGN',         (0,0),(-1,0),  'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [CGRAY,CWHITE]),
        ('BOX',           (0,0),(-1,-1), 1,BORDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.3,BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('ALIGN',         (2,1),(-1,-1), 'CENTER'),
        ('VALIGN',        (2,1),(-1,-1), 'MIDDLE'),
    ]))
 
    story.append(KeepTogether([
        sec_hdr("KEY RISK FACTORS IDENTIFIED", color=CORANGE),
        Spacer(1, 2*mm), rf, Spacer(1, 3*mm),
    ]))
 
    # ── DOCTOR'S RECOMMENDATIONS ──────────────────────────────────
    if is_high:
        recs = [
            (CRED,     "See a Heart Doctor Soon",
             "Please visit a cardiologist as soon as possible. "
             "The AI found multiple warning signs. Early treatment gives the best results. "
             "Do not ignore chest discomfort, unusual tiredness, or shortness of breath."),
            (MED_BLUE, "Tests Your Doctor May Advise",
             "12-lead ECG  |  Echocardiogram  |  Treadmill Stress Test (TMT)  "
             "|  Lipid Profile  |  Blood Sugar Test  |  Coronary Angiography if needed"),
            (MED_BLUE, "Change Your Daily Habits",
             "Eat less oily, salty, and sugary food. Add fruits and vegetables. "
             "Walk 30 minutes daily. Avoid smoking. Limit alcohol. Keep weight healthy."),
            (CORANGE,  "Take Medicines Carefully",
             "Take all medicines on time every day as prescribed. "
             "Never stop or change medicines without consulting your doctor. "
             "Tell your doctor about every other medicine you are taking."),
            (CRED,     "Emergency Signs — Go to Hospital Immediately",
             "Sudden chest pain  |  Pain in arm or jaw  |  Difficulty breathing  "
             "|  Cold sweat with dizziness  |  Sudden fainting"),
            (MED_BLUE, "Follow-Up Schedule",
             "Check blood pressure daily. Get cholesterol and blood sugar every 3 months. "
             "Visit your heart doctor every month until condition is stable."),
        ]
    else:
        recs = [
            (CGREEN,   "Your Heart Looks Healthy",
             "Your test values show low risk of heart disease. Great news! "
             "Keep your healthy habits and continue regular checkups."),
            (MED_BLUE, "Keep Eating Well",
             "Eat fruits, vegetables, whole grains, and low-fat proteins. "
             "Reduce oily food, excess salt, and sugary drinks."),
            (MED_BLUE, "Stay Physically Active",
             "Exercise 30 minutes a day, 5 days a week. "
             "Walking, cycling, swimming, or yoga all help keep your heart strong."),
            (MED_BLUE, "Annual Heart Checkup",
             "Get a heart checkup every year especially after age 40. "
             "Annual tests: blood pressure, cholesterol, blood sugar, and ECG."),
            (CORANGE,  "Manage Stress and Sleep",
             "Practice relaxation through deep breathing or yoga. "
             "Get 7 to 8 hours of sleep. Avoid smoking and limit alcohol."),
            (MED_BLUE, "When to See a Doctor",
             "Follow-up checkup in 6 months. See doctor sooner if you notice "
             "chest tightness, unusual fatigue, breathlessness, or swollen ankles."),
        ]
 
    rec_rows = []
    for tc, title, text in recs:
        rec_rows.append([
            Paragraph(title, S(f'rt{title[:5]}', bold=True, size=8.5,
                                color=tc, leading=13)),
            Paragraph(text,  S(f'rb{title[:5]}', size=8.5, leading=13,
                                color=CBLACK, align=TA_JUSTIFY)),
        ])
 
    rec_t = Table(rec_rows, colWidths=[44*mm, 126*mm])
    rec_t.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[CGRAY,CWHITE]),
        ('BOX',          (0,0),(-1,-1),1,BORDER),
        ('INNERGRID',    (0,0),(-1,-1),0.3,BORDER),
        ('TOPPADDING',   (0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',  (0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('VALIGN',       (0,0),(-1,-1),'TOP'),
        ('LINEAFTER',    (0,0),(0,-1), 0.5,BORDER),
    ]))
 
    story.append(KeepTogether([
        sec_hdr("DOCTOR'S RECOMMENDATIONS", color=MED_BLUE),
        Spacer(1, 2*mm), rec_t, Spacer(1, 3*mm),
    ]))
 
    # ── SIGNATURE ─────────────────────────────────────────────────
    sig = Table([[
        Paragraph("AI System Verified\nCardioGuard Engine v2.0\n" + rep_date,
                   S('s1', size=8, color=DARK_GRAY, align=TA_CENTER, leading=14)),
        Paragraph("_______________________\n[Doctor Name]\nCardiology Dept, KMCLU",
                   S('s2', size=8, align=TA_CENTER, leading=14)),
        Paragraph("_______________________\nHead of Department\nCardiac Sciences, KMCLU",
                   S('s3', size=8, align=TA_CENTER, leading=14)),
    ]], colWidths=[W/3, W/3, W/3])
    sig.setStyle(TableStyle([
        ('BOX',          (0,0),(-1,-1),0.5,BORDER),('INNERGRID',(0,0),(-1,-1),0.3,BORDER),
        ('BACKGROUND',   (0,0),(-1,-1),CGRAY),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',   (0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    story.append(sig)
    story.append(Spacer(1, 2*mm))
 
    # ── FOOTER ────────────────────────────────────────────────────
    footer = Table([[
        Paragraph(
            "<b>Developed by: Ruman Tanveer</b><br/>"
            "B.Tech CSE (AI &amp; ML)  |  Machine Learning Project",
            S('fd', size=8.5, color=DARK_BLUE, align=TA_LEFT, leading=14)
        ),
        Paragraph(
            "<b>DISCLAIMER:</b> This report is generated by an AI system for academic "
            "screening purposes only. It is NOT a replacement for professional medical "
            "diagnosis. Always consult a qualified doctor for final advice.",
            S('disc', size=7.5, italic=True, color=DARK_GRAY,
              align=TA_JUSTIFY, leading=11)
        ),
    ]], colWidths=[62*mm, 108*mm])
    footer.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1),LIGHT_BLUE),
        ('BOX',          (0,0),(-1,-1),1.5,DARK_BLUE),
        ('LINEAFTER',    (0,0),(0,-1), 0.5,BORDER),
        ('TOPPADDING',   (0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('LEFTPADDING',  (0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
    ]))
    story.append(footer)
 
    doc.build(story)
    buffer.seek(0)
    return buffer
 
 
# ==============================================================================
# TEST
# ==============================================================================
if __name__ == "__main__":
    buf = create_cardioguard_report(
        age=63, sex="Male", cp="4", trestbps=155, chol=260,
        thalach=95, exang="1", oldpeak=2.8, slope="2", ca="2",
        thal="7", fbs="1", restecg="1",
        risk_level="High Risk", probability=82.5,
        model_name="Stacking Classifier (RF + SVM + XGBoost)",
        logo_path="/home/claude/logo_clean.png"
    )
    with open("/mnt/user-data/outputs/CardioGuard_AI_Healthcare_Report.pdf", "wb") as f:
        f.write(buf.read())
    print("PDF saved!")