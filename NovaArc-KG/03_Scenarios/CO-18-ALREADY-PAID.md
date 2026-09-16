---
scenario_id: "CO-18-ALREADY-PAID"
title: "Service Already Adjudicated / Paid on Previous Claim"
code: "CO-18"
category: "Duplicate, Bundling & NCCI Edits"
severity: "moderate"
tags:
  - scenario/clinical
---

# 🩺 Service Already Adjudicated / Paid on Previous Claim

**CARC Code:** [[CO-18]]  
**Category:** [[Duplicate, Bundling & NCCI Edits]]  
**Root Cause:** Claim was submitted multiple times in error, and the first submission was already paid or processed.

---

## 🔍 Pre-Call Investigation Checklist
- [[INV_CO_18_ALREADY_PAID_1]]
- [[INV_CO_18_ALREADY_PAID_2]]

## 📞 Payer Call Script Questions
- [[CALL_CO_18_ALREADY_PAID_question_1]]
- [[CALL_CO_18_ALREADY_PAID_question_2]]

## 📋 Form & Box Requirements
- [[FORM_CO_18_ALREADY_PAID]]

## ⚡ Resolution Action Plan Playbook
- [[ACT_CO_18_ALREADY_PAID_1]]
- [[ACT_CO_18_ALREADY_PAID_2]]

## 📝 Standard Pre-formatted AR Caller Note
```text
STATUS: Denied CO-18 duplicate. Verified original claim #[OrigClaimID] paid on [PaidDate] under Check#[CheckNum]. Adjusted duplicate claim balance to zero.
```

---
*Back to [[CO-18]] · Category [[Duplicate, Bundling & NCCI Edits]]*
