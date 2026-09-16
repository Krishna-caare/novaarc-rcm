---
scenario_id: "CO-23-MISSING-PRIMARY-EOB"
title: "Secondary Claim Submitted Without Primary Remittance Information"
code: "CO-23"
category: "Coordination of Benefits & Third Party Liability"
severity: "moderate"
tags:
  - scenario/clinical
---

# 🩺 Secondary Claim Submitted Without Primary Remittance Information

**CARC Code:** [[CO-23]]  
**Category:** [[Coordination of Benefits & Third Party Liability]]  
**Root Cause:** Secondary claim submitted electronically without the 837 COB Loop 2320 primary paid amount, allowed amount, and adjustment codes.

---

## 🔍 Pre-Call Investigation Checklist
- [[INV_CO_23_MISSING_PRIMARY_EOB_1]]
- [[INV_CO_23_MISSING_PRIMARY_EOB_2]]

## 📞 Payer Call Script Questions
- [[CALL_CO_23_MISSING_PRIMARY_EOB_question_1]]
- [[CALL_CO_23_MISSING_PRIMARY_EOB_question_2]]

## 📋 Form & Box Requirements
- [[FORM_CO_23_MISSING_PRIMARY_EOB]]

## ⚡ Resolution Action Plan Playbook
- [[ACT_CO_23_MISSING_PRIMARY_EOB_1]]
- [[ACT_CO_23_MISSING_PRIMARY_EOB_2]]

## 📝 Standard Pre-formatted AR Caller Note
```text
STATUS: Denied CO-23. Re-entered primary payment and adjustment amounts into billing software. Resubmitted clean secondary claim.
```

---
*Back to [[CO-23]] · Category [[Coordination of Benefits & Third Party Liability]]*
