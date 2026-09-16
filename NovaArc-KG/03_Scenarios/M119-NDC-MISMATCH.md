---
scenario_id: "M119-NDC-MISMATCH"
title: "Missing or Invalid 11-Digit NDC on HCPCS J-Code"
code: "M119"
category: "Missing Information & Documentation"
severity: "moderate"
tags:
  - scenario/clinical
---

# 🩺 Missing or Invalid 11-Digit NDC on HCPCS J-Code

**CARC Code:** [[M119]]  
**Category:** [[Missing Information & Documentation]]  
**Root Cause:** Medication billed with J-code (e.g., J0131, J1745) omitted the 11-digit NDC number, unit of measure (UN, ML, GR, F2), or quantity.

---

## 🔍 Pre-Call Investigation Checklist
- [[INV_M119_NDC_MISMATCH_1]]
- [[INV_M119_NDC_MISMATCH_2]]
- [[INV_M119_NDC_MISMATCH_3]]

## 📞 Payer Call Script Questions
- [[CALL_M119_NDC_MISMATCH_question_1]]
- [[CALL_M119_NDC_MISMATCH_question_2]]

## 📋 Form & Box Requirements
- [[FORM_M119_NDC_MISMATCH]]

## ⚡ Resolution Action Plan Playbook
- [[ACT_M119_NDC_MISMATCH_1]]
- [[ACT_M119_NDC_MISMATCH_2]]
- [[ACT_M119_NDC_MISMATCH_3]]

## 📝 Standard Pre-formatted AR Caller Note
```text
STATUS: Denied M119 for NDC. Retrieved valid 11-digit NDC #[NDCNum] from drug inventory. Corrected Box 24A with N4 qualifier and UN unit. Resubmitted electronically.
```

---
*Back to [[M119]] · Category [[Missing Information & Documentation]]*
