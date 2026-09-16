---
scenario_id: "CO-252-MISSING-ATTACHMENT"
title: "EDI 275 Attachment or Paper Attachment Not Linked to Claim"
code: "CO-252"
category: "Missing Information & Documentation"
severity: "moderate"
tags:
  - scenario/clinical
---

# 🩺 EDI 275 Attachment or Paper Attachment Not Linked to Claim

**CARC Code:** [[CO-252]]  
**Category:** [[Missing Information & Documentation]]  
**Root Cause:** Claim submitted with PWK segment indicator, but clearinghouse or payer did not link the electronic or faxed attachment to the 837 claim file.

---

## 🔍 Pre-Call Investigation Checklist
- [[INV_CO_252_MISSING_ATTACHMENT_1]]
- [[INV_CO_252_MISSING_ATTACHMENT_2]]

## 📞 Payer Call Script Questions
- [[CALL_CO_252_MISSING_ATTACHMENT_question_1]]
- [[CALL_CO_252_MISSING_ATTACHMENT_question_2]]

## 📋 Form & Box Requirements
- [[FORM_CO_252_MISSING_ATTACHMENT]]

## ⚡ Resolution Action Plan Playbook
- [[ACT_CO_252_MISSING_ATTACHMENT_1]]
- [[ACT_CO_252_MISSING_ATTACHMENT_2]]
- [[ACT_CO_252_MISSING_ATTACHMENT_3]]

## 📝 Standard Pre-formatted AR Caller Note
```text
STATUS: Denied CO-252. Attachment was not linked. Generated barcoded cover sheet with ACN#[ACN]. Resubmitted records to imaging fax. Follow-up: 10 days.
```

---
*Back to [[CO-252]] · Category [[Missing Information & Documentation]]*
