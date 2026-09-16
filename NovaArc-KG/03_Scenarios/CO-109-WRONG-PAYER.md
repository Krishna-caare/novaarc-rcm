---
scenario_id: "CO-109-WRONG-PAYER"
title: "Claim Sent to Wrong Payer ID or Sub-Plan"
code: "CO-109"
category: "Eligibility, Identification & Termination"
severity: "moderate"
tags:
  - scenario/clinical
---

# 🩺 Claim Sent to Wrong Payer ID or Sub-Plan

**CARC Code:** [[CO-109]]  
**Category:** [[Eligibility, Identification & Termination]]  
**Root Cause:** Claim submitted to regional BCBS instead of out-of-state home plan, or submitted to commercial plan instead of Medicare Advantage carve-out.

---

## 🔍 Pre-Call Investigation Checklist
- [[INV_CO_109_WRONG_PAYER_1]]
- [[INV_CO_109_WRONG_PAYER_2]]

## 📞 Payer Call Script Questions
- [[CALL_CO_109_WRONG_PAYER_question_1]]
- [[CALL_CO_109_WRONG_PAYER_question_2]]

## 📋 Form & Box Requirements
- [[FORM_CO_109_WRONG_PAYER]]

## ⚡ Resolution Action Plan Playbook
- [[ACT_CO_109_WRONG_PAYER_1]]
- [[ACT_CO_109_WRONG_PAYER_2]]

## 📝 Standard Pre-formatted AR Caller Note
```text
STATUS: Denied CO-109 wrong payer. Carved out to [NewPayer]. Re-routed clean claim to correct Payer ID [PayerID].
```

---
*Back to [[CO-109]] · Category [[Eligibility, Identification & Termination]]*
