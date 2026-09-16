---
scenario_id: "CO-16-TAXONOMY-NPI"
title: "Missing or Invalid Billing/Rendering NPI or Taxonomy"
code: "CO-16"
category: "Missing Information & Documentation"
severity: "critical"
tags:
  - scenario/clinical
---

# 🩺 Missing or Invalid Billing/Rendering NPI or Taxonomy

**CARC Code:** [[CO-16]]  
**Category:** [[Missing Information & Documentation]]  
**Root Cause:** Claim submitted with missing or mismatched provider NPI, taxonomy code, or service facility address.

---

## 🔍 Pre-Call Investigation Checklist
- [[INV_CO_16_TAXONOMY_NPI_1]]
- [[INV_CO_16_TAXONOMY_NPI_2]]

## 📞 Payer Call Script Questions
- [[CALL_CO_16_TAXONOMY_NPI_question_1]]
- [[CALL_CO_16_TAXONOMY_NPI_question_2]]

## 📋 Form & Box Requirements
- [[FORM_CO_16_TAXONOMY_NPI]]

## ⚡ Resolution Action Plan Playbook
- [[ACT_CO_16_TAXONOMY_NPI_1]]
- [[ACT_CO_16_TAXONOMY_NPI_2]]
- [[ACT_CO_16_TAXONOMY_NPI_3]]

## 📝 Standard Pre-formatted AR Caller Note
```text
STATUS: Denied CO-16 for provider taxonomy/NPI mismatch. Corrected Box 24J/33a with enrolled taxonomy code. Resubmitted claim.
```

---
*Back to [[CO-16]] · Category [[Missing Information & Documentation]]*
