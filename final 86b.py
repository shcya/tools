# app.py
import streamlit as st
import pandas as pd
import io
import json
from datetime import datetime
from PIL import Image, ImageEnhance

# PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# Excel generation
from pandas import ExcelWriter

# -----------------------
# App configuration
# -----------------------
st.set_page_config(page_title="Shavan — Rule 86B Calculator", layout="wide", page_icon="🧾")
BRAND = "Shavan"
LOGO_FILE = "logo.png"  # must be present in repo

st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:12px;">
      <img src="data:image/png;base64,{''}" style="height:60px; display:none;">
      <h1 style="margin:0">{BRAND} — Rule 86B Calculator</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# load logo for UI (if present)
logo_img = None
try:
    logo_img = Image.open(LOGO_FILE)
    # display small logo on top-right
    st.image(logo_img.resize((120, 60)), width=120)
except Exception:
    st.warning("Logo not found. Put your logo file named 'logo.png' alongside app.py to show branding and watermark.")

st.write("Use this tool to test applicability of Rule 86B and export neat reports (Excel / PDF / JSON).")

# --------------------------------
# Inputs (user-friendly layout)
# --------------------------------
st.header("1. Enter amounts (₹)")

col1, col2, col3 = st.columns(3)
with col1:
    taxable_value = st.number_input("Taxable value of supplies (month, excl. exempt & zero-rated)", min_value=0.0, format="%.2f", step=1000.0)
    cum_output_tax_prev = st.number_input("Cumulative output tax liability in FY (till previous month)", min_value=0.0, format="%.2f", step=500.0)
with col2:
    output_tax = st.number_input("This month's output tax liability (CGST+SGST+IGST)", min_value=0.0, format="%.2f", step=500.0)
    cum_cash_paid_prev = st.number_input("Cumulative cash paid in FY (till previous month)", min_value=0.0, format="%.2f", step=500.0)
with col3:
    available_itc = st.number_input("Available ITC balance", min_value=0.0, format="%.2f", step=500.0)
    refund_prev_fy = st.number_input("Refund prev FY (unutilised ITC on zero-rated/inverted) (₹)", min_value=0.0, format="%.2f", step=100.0)

st.markdown("---")
st.header("2. Exceptions & facts (tick as applicable)")
col4, col5, col6 = st.columns(3)
with col4:
    is_govt = st.checkbox("Government department / PSU / Local body")
    income_tax_flag = st.checkbox("Income-tax paid > ₹1,00,000 in each of 2 preceding FYs")
with col5:
    first_return = st.checkbox("First return after registration")
    received_export_refund = st.checkbox("Refund for zero-rated exports (LUT/paid refund) in prev FY")
with col6:
    received_inverted_refund = st.checkbox("Refund due to inverted duty structure in prev FY")
    # option to use cumulative method vs month-only (practical)
    use_cumulative_logic = st.checkbox("Use cumulative (FY-to-date) 1% test (practical)", value=True)

st.markdown("---")

# --------------------------------
# Computation logic (detailed)
# --------------------------------
APPLICABILITY_THRESHOLD = 50_00_000  # ₹50 lakh
applies_by_turnover = taxable_value > APPLICABILITY_THRESHOLD

# compute required cash
if use_cumulative_logic:
    required_cumulative_cash_after_month = 0.01 * (cum_output_tax_prev + output_tax)
    required_cumulative_cash_before_month = 0.01 * max(0.0, cum_output_tax_prev)
    # shortfall to be paid in this month
    min_additional_cash_required = max(0.0, required_cumulative_cash_after_month - cum_cash_paid_prev)
else:
    # month-by-month: at least 1% of this month's output tax must be paid in cash
    required_cumulative_cash_after_month = None
    required_cumulative_cash_before_month = None
    min_additional_cash_required = max(0.0, 0.01 * output_tax - cum_cash_paid_prev)  # conservative

# enforce that min additional cash cannot exceed output tax
min_additional_cash_required = min(min_additional_cash_required, output_tax)
max_itc_usable = max(0.0, output_tax - min_additional_cash_required)

# Exceptions
exceptions = []
if refund_prev_fy > 100000 or received_export_refund or received_inverted_refund:
    exceptions.append("Refund exception: refund > ₹1,00,000 in prev FY (zero-rated/inverted).")
if income_tax_flag:
    exceptions.append("Income-tax > ₹1,00,000 in each of two preceding FYs (practical exception).")
if is_govt:
    exceptions.append("Govt/PSU/Local body — exempt.")
if first_return:
    exceptions.append("First return after registration — exempt.")

# final applicability
if not applies_by_turnover:
    final_applicability = False
    applicability_reason = "Monthly taxable value ≤ ₹50,00,000 (threshold not met)."
elif exceptions:
    # if any statutory exemption present, treat as not applicable (show to user)
    final_applicability = False
    applicability_reason = "One or more statutory/practical exceptions found: " + "; ".join(exceptions)
elif cum_cash_paid_prev >= (required_cumulative_cash_after_month if required_cumulative_cash_after_month is not None else 0.01*output_tax):
    final_applicability = False
    applicability_reason = "Cumulative cash already meets 1% test (no additional cash needed)."
else:
    final_applicability = True
    applicability_reason = "Rule 86B applies (no exemptions, threshold met and shortfall exists)."

# display results
st.header("3. Result")
st.write(f"- Monthly taxable value test: **{'Exceeded' if applies_by_turnover else 'Not exceeded'}** (₹{taxable_value:,.2f})")
if use_cumulative_logic:
    st.write(f"- Cumulative 1% required after this month: **₹{required_cumulative_cash_after_month:,.2f}**")
st.write(f"- Minimum additional cash required this month (practical) : **₹{min_additional_cash_required:,.2f}**")
st.write(f"- Maximum ITC usable this month (practical) : **₹{max_itc_usable:,.2f}**")
st.markdown(f"**Final conclusion:** {'🔴 RULE 86B APPLIES' if final_applicability else '🟢 RULE 86B DOES NOT APPLY'}")
st.caption(applicability_reason)

st.markdown("---")

# --------------------------------
# Prepare report data
# --------------------------------
report = {
    "brand": BRAND,
    "timestamp": datetime.now().isoformat(),
    "inputs": {
        "taxable_value": taxable_value,
        "output_tax": output_tax,
        "available_itc": available_itc,
        "cum_output_tax_prev": cum_output_tax_prev,
        "cum_cash_paid_prev": cum_cash_paid_prev,
        "refund_prev_fy": refund_prev_fy,
        "is_govt": bool(is_govt),
        "income_tax_flag": bool(income_tax_flag),
        "first_return": bool(first_return),
        "received_export_refund": bool(received_export_refund),
        "received_inverted_refund": bool(received_inverted_refund),
        "use_cumulative_logic": bool(use_cumulative_logic),
    },
    "computations": {
        "required_cumulative_cash_after_month": required_cumulative_cash_after_month,
        "min_additional_cash_required": min_additional_cash_required,
        "max_itc_usable": max_itc_usable,
    },
    "final_applicability": "APPLICABLE" if final_applicability else "NOT APPLICABLE",
    "remarks": exceptions + [applicability_reason]
}

# --------------------------------
# Export buttons: JSON, Excel, PDF
# --------------------------------
st.header("4. Export Report")

# JSON
json_bytes = json.dumps(report, indent=4).encode("utf-8")
st.download_button("Download JSON", json_bytes, file_name="rule86b_shavan_report.json", mime="application/json")

# Excel - prepare DataFrame and write to BytesIO
df_inputs = pd.DataFrame(list(report["inputs"].items()), columns=["Particular", "Value"])
df_comps = pd.DataFrame(list(report["computations"].items()), columns=["Computation", "Value"])
df_meta = pd.DataFrame([{"Result": report["final_applicability"], "Timestamp": report["timestamp"]}])

towrite = io.BytesIO()
with ExcelWriter(towrite, engine="openpyxl") as writer:
    df_inputs.to_excel(writer, sheet_name="Inputs", index=False)
    df_comps.to_excel(writer, sheet_name="Computations", index=False)
    df_meta.to_excel(writer, sheet_name="Summary", index=False)
    # remarks sheet
    pd.DataFrame(report["remarks"], columns=["Remarks"]).to_excel(writer, sheet_name="Remarks", index=False)
writer.save()
towrite.seek(0)
st.download_button("Download Excel (.xlsx)", towrite, file_name="rule86b_shavan_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# PDF generation with watermark logo
def make_pdf_bytes(report_dict, logo_path=LOGO_FILE):
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)

    # watermark: try to create semi-transparent logo image using PIL
    try:
        pil_logo = Image.open(logo_path).convert("RGBA")
        # scale logo
        max_w = int(width * 0.4)
        ratio = min(max_w / pil_logo.width, 1.0)
        new_w = int(pil_logo.width * ratio)
        new_h = int(pil_logo.height * ratio)
        pil_logo = pil_logo.resize((new_w, new_h), Image.ANTIALIAS)

        # reduce opacity
        alpha = pil_logo.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.18)  # make it very faint
        pil_logo.putalpha(alpha)
        pil_logo.save("temp_wm.png")
        # draw watermark centered
        wm_x = (width - new_w) / 2
        wm_y = (height - new_h) / 2
        c.drawImage("temp_wm.png", wm_x, wm_y, width=new_w, height=new_h, mask='auto')
    except Exception:
        pass

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2.2*cm, f"{BRAND} — Rule 86B Compliance Report")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.8*cm, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Draw a table-like listing (simple)
    y = height - 4.2*cm
    left = 2*cm
    line_h = 12

    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Inputs")
    y -= 1.2*line_h

    c.setFont("Helvetica", 10)
    for k, v in report_dict["inputs"].items():
        # format booleans nicely
        val = v
        if isinstance(v, bool):
            val = "Yes" if v else "No"
        elif isinstance(v, float):
            val = f"₹{v:,.2f}"
