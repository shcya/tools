import openpyxl
import pandas as pd
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from PIL import Image as PILImage


# ====================================
# BRANDING DETAILS
# ====================================
BRAND_NAME = "Shavan"
LOGO_PATH = "logo.png"
EXCEL_FILE = "Rule_86B_Shavan_Report.xlsx"
PDF_FILE = "Rule_86B_Shavan_Report.pdf"
JSON_FILE = "Rule_86B_Shavan_Report.json"


print(f"\n========== {BRAND_NAME.upper()} - RULE 86B PROFESSIONAL TOOL ==========\n")


# ---------------- INPUTS ------------------
turnover = float(input("Enter Taxable Value of Outward Supplies for the Month (₹): "))
tax_liability = float(input("Enter Total GST Tax Liability (₹): "))
available_itc = float(input("Enter Available ITC (₹): "))
cash_paid = float(input("Tax Already Paid in Cash (₹): "))

print("\nAdditional eligibility questions:\n")

is_govt = input("Taxpayer is Government Department/PSU/Local Body? (Y/N): ").upper()
refund_zero = input("Refund received on Zero-rated supplies? (Y/N): ").upper()
refund_inverted = input("Refund received due to inverted duty structure? (Y/N): ").upper()
income_tax_paid = float(input("Total Income Tax paid last 2 years (₹): "))
first_return = input("Is this the first return after registration? (Y/N): ").upper()


# ---------------- CALCULATIONS ------------------
minimum_cash = round(tax_liability * 0.01, 2)

applicable = True
comments = []
