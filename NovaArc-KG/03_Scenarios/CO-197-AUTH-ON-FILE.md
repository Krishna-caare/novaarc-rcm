---
scenario_id: "CO-197-AUTH-ON-FILE"
title: "Authorization Obtained but Missing from Claim"
code: "CO-197"
category: "Prior Authorization & Referrals"
severity: "critical"
tags:
  - scenario/clinical
---

# 🩺 Authorization Obtained but Missing from Claim

**CARC Code:** [[CO-197]]  
**Category:** [[Prior Authorization & Referrals]]  
**Root Cause:** Prior authorization was approved prior to the procedure, but the auth number was omitted from Box 23 or had a typo.

---

## 🔍 Pre-Call Investigation Checklist
- [[INV_CO_197_AUTH_ON_FILE_1]]
- [[INV_CO_197_AUTH_ON_FILE_2]]

## 📞 Payer Call Script Questions
- [[CALL_CO_197_AUTH_ON_FILE_question_1]]
- [[CALL_CO_197_AUTH_ON_FILE_question_2]]
- [[CALL_CO_197_AUTH_ON_FILE_question_3]]

## 📋 Form & Box Requirements
- [[FORM_CO_197_AUTH_ON_FILE]]

## ⚡ Resolution Action Plan Playbook
- [[ACT_CO_197_AUTH_ON_FILE_1]]
- [[ACT_CO_197_AUTH_ON_FILE_2]]
- [[ACT_CO_197_AUTH_ON_FILE_3]]
- [[ACT_CO_197_AUTH_ON_FILE_4]]

## 📝 Standard Pre-formatted AR Caller Note
```text
STATUS: Denied CO-197. Verified prior auth #[AuthNumber] valid on DOS. Spoke with Rep: [RepName], Ref#: [CallRef]. Claim sent for phone reprocessing / corrected claim sent with auth in Box 23. Follow up: 30 days.
```

---
*Back to [[CO-197]] · Category [[Prior Authorization & Referrals]]*
