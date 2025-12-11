import openpyxl

print("\n========== RULE 86B DETAILED CALCULATOR ==========\n")

# ---------------- INPUT SECTION ------------------

turnover = float(input("Enter Current Month Taxable Value of Outward Supplies (₹): "))
tax_liability = float(input("Enter Total GST Liability Payable for the Month (₹): "))
itc_balance = float(input("Enter Available ITC Balance (₹): "))
cash_paid = float(input("Enter Cash Already Paid to Government (₹): "))

print("\n----- Additional Statutory Information ------")

govt_department = input("Is the taxpayer Government Department, PSU or Local Body? (Y/N): ").strip().upper()
refund_zero_rated = input("Has taxpayer received refund against zero-rated supplies? (Y/N): ").strip().upper()
refund_inverted = input("Has taxpayer received refund due to inverted duty structure? (Y/N): ").strip().upper()
income_tax_paid_2years = float(input("Enter total income-tax paid in last 2 financial years (₹): "))
is_first_return = input("Is this the first return after registration? (Y/N): ").strip().upper()

# ---------------- LEGAL COMPUTATIONS ------------------

rule_applicable = True
remarks = []

# 1. Basic Threshold Condition
if turnover < 5000000:
    rule_applicable = False
    remarks.append("Turnover below ₹50 lakhs in the month → Rule 86B NOT applicable.")

# 2. Mandatory Cash Requirement (1% of Output Tax)
required_cash_payment = round(tax_liability * 0.01, 2)

# 3. Check statutory exemptions
if govt_department == "Y":
    rule_applicable = False
    remarks.append("Entity is Govt. Department/PSU/Local Body → Exempt under Rule 86B.")

if refund_zero_rated == "Y":
    rule_applicable = False
    remarks.append("Received refund on exports/zero-rated supplies → Exempt.")

if refund_inverted == "Y":
    rule_applicable = False
    remarks.append("Received refund due to inverted duty structure → Exempt.")

if income_tax_paid_2years > 100000:
    rule_applicable = False
    remarks.append("Income Tax paid exceeds ₹1 lakh in preceding 2 years → Exempt.")

if is_first_return == "Y":
    rule_applicable = False
    remarks.append("This is first year return after registration → Exempt.")

# 4. Test payment already made
if cash_paid >= required_cash_payment:
    payment_condition_met = True
    remarks.append(
        f"Already paid ₹{cash_paid:.2f} in cash which satisfies minimum requirement of ₹{required_cash_payment:.2f}."
    )
else:
    payment_condition_met = False
    shortfall = required_cash_payment - cash_paid
    remarks.append(
        f"Paid only ₹{cash_paid:.2f} against minimum cash requirement of ₹{required_cash_payment:.2f}. "
        f"Shortfall = ₹{shortfall:.2f}"
    )

# Final applicability logic
if payment_condition_met:
    rule_applicable = False

# ---------------- FINAL OUTPUT ------------------

print("\n================== FINAL RESULT ==================\n")
print(f"Minimum cash payment requirement = ₹{required_cash_payment}")

if rule_applicable:
    print("\n⚠ RULE 86B IS APPLICABLE")
else:
    print("\n✔ RULE 86B IS NOT APPLICABLE")

print("\n---- JUSTIFICATIONS ----")
for r in remarks:
    print("➡", r)

# ---------------- EXCEL EXPORT ------------------

filename = "Rule_86B_Detailed_Report.xlsx"

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Rule 86B Analysis Report"

ws.append(["Particulars", "Value"])
ws.append(["Taxable Turnover for Month", turnover])
ws.append(["Total Tax Liability", tax_liability])
ws.append(["Available ITC Balance", itc_balance])
ws.append(["Cash Paid Already", cash_paid])
ws.append(["Minimum Cash Required", required_cash_payment])
ws.append(["Rule 86B Applicability", "Applicable" if rule_applicable else "Not Applicable"])

ws.append([" ", " "])
ws.append(["Reasoning / Legal Remarks", " "])
for remark in remarks:
    ws.append([remark])

wb.save(filename)

print(f"\n📁 Detailed Excel Report saved as: {filename}")

print("\n====================================================")
