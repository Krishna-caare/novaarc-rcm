"""
Comprehensive Denial Knowledge Graph Dataset
Ingested and structured from ARLearningOnline (https://www.arlearningonline.com/p/denial.html)
and official CMS/HIPAA CARC/RARC guidelines.
"""

from typing import Dict, List, Any

# 8 Core Categories
CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "CAT_MISSING_INFO",
        "name": "Missing Information & Documentation",
        "description": "Claims denied due to absent clinical documentation, invoices, missing modifiers, or incomplete claim form fields.",
        "color": "#3b82f6",  # Blue
    },
    {
        "id": "CAT_PRIOR_AUTH",
        "name": "Prior Authorization & Referrals",
        "description": "Denials related to lack of pre-certification, missing referral numbers, authorization validity date mismatches, or retro-auths.",
        "color": "#8b5cf6",  # Purple
    },
    {
        "id": "CAT_TIMELY_FILING",
        "name": "Timely Filing & Deadlines",
        "description": "Denials where submission exceeded payer timely filing limits, requiring proof of timely filing or contractual write-off.",
        "color": "#ef4444",  # Red
    },
    {
        "id": "CAT_COB",
        "name": "Coordination of Benefits & Third Party Liability",
        "description": "Cross-payer disputes, primary vs secondary coverage, Medicare Secondary Payer (MSP), or patient COB update requirements.",
        "color": "#f59e0b",  # Amber
    },
    {
        "id": "CAT_MEDICAL_NECESSITY",
        "name": "Medical Necessity & Level of Service",
        "description": "Clinical denials where service was deemed non-covered, experimental, or downcoded, requiring physician appeals or peer-to-peer reviews.",
        "color": "#10b981",  # Emerald
    },
    {
        "id": "CAT_CODING_MODIFIERS",
        "name": "Coding, Inconsistencies & Modifier Edits",
        "description": "Inconsistencies between diagnosis and procedure, patient age/gender mismatches, missing/invalid modifiers, or provider specialty rules.",
        "color": "#06b6d4",  # Cyan
    },
    {
        "id": "CAT_DUPLICATE_BUNDLING",
        "name": "Duplicate, Bundling & NCCI Edits",
        "description": "Exact duplicate claims, services included in payment for another procedure (inclusive/bundled), or global period violations.",
        "color": "#ec4899",  # Pink
    },
    {
        "id": "CAT_ELIGIBILITY",
        "name": "Eligibility, Identification & Termination",
        "description": "Patient not identified, expenses incurred prior to/after coverage dates, incorrect member ID, or demographic mismatches.",
        "color": "#6366f1",  # Indigo
    },
]

# Complete Knowledge Base of Denial Scenarios
DENIAL_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "CO-16": {
        "code": "CO-16",
        "category_id": "CAT_MISSING_INFO",
        "description": "Claim/service lacks information or has submission/billing error(s).",
        "short_name": "Lacks Information / Billing Error",
        "scenarios": [
            {
                "id": "CO-16-OP-NOTE",
                "title": "Missing Operative Report / Surgical Notes",
                "root_cause": "Payer requested signed operative or procedure report to substantiate surgical CPT code.",
                "investigation_steps": [
                    "Check EHR: Is the operative note dictated, finalized, and electronically signed by the surgeon?",
                    "Verify if the operative note has already been transmitted via clearinghouse attachment or fax.",
                    "Verify if a remark code (RARC) accompanied the denial (e.g., M127, N29).",
                ],
                "call_script": {
                    "question_1": "May I know the exact denial date and the specific documents requested by your review department?",
                    "question_2": "What is the dedicated fax number or mailing address with department attention to send the operative report?",
                    "question_3": "What is the time limit from the denial date to submit these records before the claim is closed?",
                    "question_4": "May I please have the claim number, call reference number, and your name?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500 / EDI 275 Attachment",
                    "box_number": "PWK Segment (EDI 837) / Attachment Control Number in Box 19",
                    "required_documents": ["Signed Operative Report", "Pathology Report (if biopsy/excision)", "Claim Cover Sheet with Claim ID & NPI"],
                },
                "action_plan": [
                    "Step 1: Pull the signed operative note and clinical record from EHR.",
                    "Step 2: Check time limit. If within deadline, fax documents with claim cover sheet to the payer's medical review fax number.",
                    "Step 3: Document the fax transmission receipt / confirmation page.",
                    "Step 4: Set follow-up task for 21-30 days to verify document receipt and claim re-adjudication.",
                ],
                "standard_notes": "CALL STATUS: Claim denied CO-16 for Operative Report. Spoke with Rep: [RepName] | Call Ref#: [CallRef]. Verified fax#: [FaxNumber]. Time limit: [TimeLimit] days from [DenialDate]. Sent signed operative report via fax with confirmation. Next follow-up: 21 days."
            },
            {
                "id": "CO-16-MOD-25",
                "title": "Missing Modifier 25 on Evaluation & Management (E/M)",
                "root_cause": "E/M service billed on the same date of service as a minor surgical procedure or injection without modifier 25.",
                "investigation_steps": [
                    "Check Box 24D: Was an E/M code (99212-99215) billed alongside a procedure (e.g., 20610, 17000, 93000)?",
                    "Verify clinical notes: Does documentation reflect a separately identifiable medical evaluation?",
                ],
                "call_script": {
                    "question_1": "Can you confirm if adding modifier 25 to the E/M code will allow claim reprocessing?",
                    "question_2": "Does your payer require medical records with the corrected claim, or can it be resubmitted electronically?",
                    "question_3": "What is your timely filing limit for corrected claims (Claim Frequency Code 7)?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24D (Modifier Column)",
                    "required_documents": ["Corrected Claim (Frequency Code 7 / Resubmission Code in Box 22)"],
                },
                "action_plan": [
                    "Step 1: Confirm medical necessity for separate E/M in documentation.",
                    "Step 2: Append Modifier 25 to the E/M procedure code in billing software.",
                    "Step 3: Set Claim Frequency Code to '7' (Replacement of Prior Claim) and include original Payer Claim Control # in Box 22.",
                    "Step 4: Submit electronically to clearinghouse and verify 277 acknowledgement.",
                ],
                "standard_notes": "STATUS: Denied CO-16 for missing modifier 25. Reviewed notes; separate E/M validated. Corrected claim generated with Modifier 25 appended to CPT in Box 24D and Frequency Code 7 in Box 22. Electronically resubmitted."
            },
            {
                "id": "CO-16-TAXONOMY-NPI",
                "title": "Missing or Invalid Billing/Rendering NPI or Taxonomy",
                "root_cause": "Claim submitted with missing or mismatched provider NPI, taxonomy code, or service facility address.",
                "investigation_steps": [
                    "Check Box 24J (Rendering NPI), Box 32a (Facility NPI), and Box 33a (Billing NPI).",
                    "Check NPPES registry: Does the taxonomy code match the specialty enrolled with this payer?",
                ],
                "call_script": {
                    "question_1": "Which specific provider field is missing or invalid on this claim (Rendering, Billing, or Facility)?",
                    "question_2": "Is the provider's taxonomy code required in Box 33b / 24J qualifier ZZ?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24J (Rendering), Box 32a (Facility), Box 33a (Billing Provider)",
                    "required_documents": ["W-9 Form / Provider Enrollment Confirmation"],
                },
                "action_plan": [
                    "Step 1: Correct the NPI or add ZZ qualifier with appropriate taxonomy code in Box 33b/24J.",
                    "Step 2: Verify provider enrollment status in payer portal.",
                    "Step 3: Rebill as corrected claim.",
                ],
                "standard_notes": "STATUS: Denied CO-16 for provider taxonomy/NPI mismatch. Corrected Box 24J/33a with enrolled taxonomy code. Resubmitted claim."
            }
        ]
    },

    "CO-197": {
        "code": "CO-197",
        "category_id": "CAT_PRIOR_AUTH",
        "description": "Precertification/Authorization/Notification/Pre-treatment absent.",
        "short_name": "Prior Authorization Absent",
        "scenarios": [
            {
                "id": "CO-197-AUTH-ON-FILE",
                "title": "Authorization Obtained but Missing from Claim",
                "root_cause": "Prior authorization was approved prior to the procedure, but the auth number was omitted from Box 23 or had a typo.",
                "investigation_steps": [
                    "Check authorization log / EHR: Was prior auth issued for this patient, DOS, CPT, and provider?",
                    "Check CMS-1500 Box 23 / EDI 2300 REF*G1 segment on the original 837 file.",
                ],
                "call_script": {
                    "question_1": "We have prior authorization #[AuthNumber] approved on [AuthDate]. Can you reprocess the claim on call with this auth number?",
                    "question_2": "If reprocessing on call is not permitted, should we submit a corrected claim or a formal dispute with the approval letter?",
                    "question_3": "What is the representative name, call reference number, and turnaround time for reprocessing?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 23 (Prior Authorization Number)",
                    "required_documents": ["Payer Prior Authorization Approval Letter"],
                },
                "action_plan": [
                    "Step 1: Obtain copy of the authorization approval letter showing valid date range and CPT.",
                    "Step 2: If payer representative allows phone adjustment, request reprocessing and record Call Ref#.",
                    "Step 3: If rebill is required, insert auth # into Box 23, set Frequency Code 7 in Box 22, and transmit.",
                    "Step 4: If appeal is required, attach auth approval letter to dispute form and submit.",
                ],
                "standard_notes": "STATUS: Denied CO-197. Verified prior auth #[AuthNumber] valid on DOS. Spoke with Rep: [RepName], Ref#: [CallRef]. Claim sent for phone reprocessing / corrected claim sent with auth in Box 23. Follow up: 30 days."
            },
            {
                "id": "CO-197-RETRO-AUTH",
                "title": "Authorization Not Obtained Prior to Service (Retro-Auth Needed)",
                "root_cause": "Service rendered without pre-certification due to urgent clinical circumstances or intake oversight.",
                "investigation_steps": [
                    "Check payer policy: Does this payer accept retroactive authorization requests within 14/30 days of DOS?",
                    "Was the encounter an emergency or urgent admission meeting retrospective review criteria?",
                ],
                "call_script": {
                    "question_1": "Does the payer permit retrospective authorization requests for urgent/emergent circumstances for this service?",
                    "question_2": "What is the deadline and submission portal/fax number for the retro-authorization department?",
                },
                "form_requirements": {
                    "form_name": "Payer Retro-Authorization Request Form",
                    "box_number": "N/A (Clinical Appeal Packet)",
                    "required_documents": ["Retro-Auth Form", "Emergency Room / Urgent Clinical Notes", "Letter of Medical Urgency from Physician"],
                },
                "action_plan": [
                    "Step 1: Contact provider/intake to submit an expedited retrospective authorization request.",
                    "Step 2: If retro-auth is approved, submit corrected claim with auth in Box 23.",
                    "Step 3: If retro-auth is denied or not allowed by contract, file clinical appeal with proof of medical emergency.",
                    "Step 4: If all appeals exhausted and no patient waiver exists, contractual write-off per provider agreement.",
                ],
                "standard_notes": "STATUS: Denied CO-197. Auth was not on file. Initiated retrospective authorization request with payer clinical intake. Attached emergent documentation. Awaiting auth decision."
            }
        ]
    },

    "CO-29": {
        "code": "CO-29",
        "category_id": "CAT_TIMELY_FILING",
        "description": "The time limit for filing has expired.",
        "short_name": "Timely Filing Limit Expired",
        "scenarios": [
            {
                "id": "CO-29-PROOF-AVAILABLE",
                "title": "Initial Claim Submitted Timely (Proof of Timely Filing Available)",
                "root_cause": "Claim was submitted within payer deadline (e.g., 90/180/365 days), but payer delayed adjudication or lost initial transmission.",
                "investigation_steps": [
                    "Calculate days between Date of Service and initial submission date.",
                    "Search clearinghouse archive for EDI 999 (Functional Acknowledgement) and EDI 277 (Claim Acceptance).",
                    "Check for payer electronic batch confirmation number, certified mail tracking, or fax receipt.",
                ],
                "call_script": {
                    "question_1": "What is the contractual timely filing limit for this provider and plan (90, 180, or 365 days)?",
                    "question_2": "We show initial electronic submission on [InitialDate] with Batch/Trace#[TraceID]. Do you have record of this transmission?",
                    "question_3": "What is the dedicated fax number or address for the Timely Filing Dispute Department?",
                },
                "form_requirements": {
                    "form_name": "Timely Filing Appeal Packet",
                    "box_number": "N/A",
                    "required_documents": [
                        "Clearinghouse EDI 999 Acceptance Report",
                        "EDI 277 Claim Acknowledgement Report",
                        "CMS-1500 Form copy stamped with original submission date",
                        "Timely Filing Rebuttal Cover Letter",
                    ],
                },
                "action_plan": [
                    "Step 1: Download EDI 999 and 277 acceptance reports showing payer-assigned trace ID.",
                    "Step 2: Draft Timely Filing Appeal Letter citing initial transmission date vs contractual deadline.",
                    "Step 3: Submit complete proof package to payer timely filing appeals department via certified mail or secure portal.",
                    "Step 4: Track certified receipt and follow up within 30-45 days.",
                ],
                "standard_notes": "STATUS: Denied CO-29. Verified initial submission on [InitialDate] within [Limit] day deadline. Retrieved EDI 277 Acceptance proof (Trace#[TraceID]). Compiled timely filing appeal package. Faxed to appeals dept. Next follow-up: 30 days."
            },
            {
                "id": "CO-29-NO-PROOF",
                "title": "Claim Submitted Past Timely Filing Deadline (Write-Off Evaluation)",
                "root_cause": "Initial submission was delayed past deadline without qualifying extenuating circumstances.",
                "investigation_steps": [
                    "Verify if primary payer delay applies (secondary timely filing runs from primary EOB date).",
                    "Check if patient retroactive Medicaid enrollment or system outage occurred.",
                ],
                "call_script": {
                    "question_1": "Can secondary timely filing be calculated from the primary payment date rather than DOS?",
                    "question_2": "Does the plan accept late filing exceptions for retroactive member eligibility?",
                },
                "form_requirements": {
                    "form_name": "Financial Adjustment Form",
                    "box_number": "N/A",
                    "required_documents": ["Primary EOB showing late adjudication (if secondary claim)"],
                },
                "action_plan": [
                    "Step 1: If secondary claim, appeal with primary EOB showing timely submission from primary ERA date.",
                    "Step 2: If genuine provider filing delay with in-network contract, write off balance as contractual adjustment (cannot bill patient).",
                ],
                "standard_notes": "STATUS: Denied CO-29. Confirmed claim submitted past filing limit without valid proof. Adjustment required per provider network agreement."
            }
        ]
    },

    "CO-22": {
        "code": "CO-22",
        "category_id": "CAT_COB",
        "description": "This care may be covered by another payer per coordination of benefits.",
        "short_name": "Coordination of Benefits (COB) Required",
        "scenarios": [
            {
                "id": "CO-22-PATIENT-UPDATE",
                "title": "Patient Must Update COB with Payer",
                "root_cause": "Payer requires insured patient to complete annual Coordination of Benefits questionnaire confirming other insurance.",
                "investigation_steps": [
                    "Check payer portal: Is the policy flagged for 'COB Update Needed'?",
                    "Verify if patient has secondary commercial insurance, Medicare, or spouse coverage.",
                ],
                "call_script": {
                    "question_1": "Can provider update COB on the patient's behalf, or must the member call directly?",
                    "question_2": "What is the direct member services phone number and web portal link for the patient to update COB?",
                    "question_3": "Once the member updates COB, will the claim automatically reprocess or should we call back?",
                },
                "form_requirements": {
                    "form_name": "Patient COB Verification Form",
                    "box_number": "Box 11d (Another Health Benefit Plan)",
                    "required_documents": ["Payer Member Services Phone Number", "Patient Demographic Sheet"],
                },
                "action_plan": [
                    "Step 1: Contact patient via phone and billing portal alert explaining insurance holds claim pending COB update.",
                    "Step 2: Provide patient with payer's direct toll-free member number and policy ID.",
                    "Step 3: Allow 7-10 business days for patient to call insurer.",
                    "Step 4: Check payer portal for updated COB status and request claim reprocessing.",
                ],
                "standard_notes": "STATUS: Denied CO-22. Insurer requires member COB update. Contacted patient: advised to call [PayerPhone] to complete COB questionnaire. Placed claim in follow-up queue for 10 days."
            },
            {
                "id": "CO-22-PRIMARY-DISPUTE",
                "title": "Billed as Primary but Payer is Secondary",
                "root_cause": "Claim submitted to secondary insurance as primary, or Medicare Secondary Payer (MSP) rules apply.",
                "investigation_steps": [
                    "Check patient registration: Is another insurer listed as primary coverage?",
                    "Review Medicare MSP questionnaire: Is patient employed, covered under spouse group health plan, or ESRD?",
                ],
                "call_script": {
                    "question_1": "Who does your system show as the primary carrier on this date of service?",
                    "question_2": "What is the primary policy number, group number, and effective date listed in your records?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500 / Secondary EDI 837",
                    "box_number": "Box 9 (Other Insured) and Box 11 (Insured Policy)",
                    "required_documents": ["Primary Payer EOB / ERA Remittance"],
                },
                "action_plan": [
                    "Step 1: Bill the verified primary insurance carrier with clean initial claim.",
                    "Step 2: Once primary pays and issues EOB/ERA, attach EOB and bill secondary carrier.",
                ],
                "standard_notes": "STATUS: Denied CO-22. Payer is secondary to [PrimaryPayer]. Re-routed claim to primary carrier with original DOS. Secondary claim held pending primary ERA."
            }
        ]
    },

    "CO-4": {
        "code": "CO-4",
        "category_id": "CAT_CODING_MODIFIERS",
        "description": "The procedure code is inconsistent with the modifier used or a required modifier is missing.",
        "short_name": "Modifier Inconsistent / Missing",
        "scenarios": [
            {
                "id": "CO-4-ANATOMICAL",
                "title": "Missing Anatomical Modifier (RT/LT/E1-E4/FA-F9)",
                "root_cause": "Procedure performed on paired organ or extremity billed without lateral modifier.",
                "investigation_steps": [
                    "Check operative/clinical note: Was procedure performed on Left, Right, or Bilateral site?",
                    "Check CPT guidelines: Does procedure require RT, LT, or 50 modifier?",
                ],
                "call_script": {
                    "question_1": "Does this CPT require anatomical modifier RT/LT or bilateral modifier 50?",
                    "question_2": "Can this be corrected via electronic corrected claim (Frequency 7)?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24D (Modifier 1-4)",
                    "required_documents": ["Corrected Claim", "Clinical Documentation"],
                },
                "action_plan": [
                    "Step 1: Verify documentation for exact anatomical site.",
                    "Step 2: Append RT, LT, or 50 in Box 24D.",
                    "Step 3: Resubmit as Frequency Code 7 corrected claim.",
                ],
                "standard_notes": "STATUS: Denied CO-4 for anatomical modifier. Appended modifier [RT/LT] per operative report. Resubmitted as corrected claim."
            }
        ]
    },

    "CO-18": {
        "code": "CO-18",
        "category_id": "CAT_DUPLICATE_BUNDLING",
        "description": "Exact duplicate claim/service.",
        "short_name": "Duplicate Claim / Service",
        "scenarios": [
            {
                "id": "CO-18-ALREADY-PAID",
                "title": "Service Already Adjudicated / Paid on Previous Claim",
                "root_cause": "Claim was submitted multiple times in error, and the first submission was already paid or processed.",
                "investigation_steps": [
                    "Search billing system and payer portal for same patient, DOS, CPT, and charge amount.",
                    "Check if an ERA / payment was posted to another claim control number.",
                ],
                "call_script": {
                    "question_1": "Can you provide the original claim number and payment date where this service was processed?",
                    "question_2": "What was the check/EFT number and amount paid on the original claim?",
                },
                "form_requirements": {
                    "form_name": "Payment Reconciliation Ledger",
                    "box_number": "N/A",
                    "required_documents": ["Original EOB / ERA showing prior payment"],
                },
                "action_plan": [
                    "Step 1: If original claim paid correctly, void/close duplicate claim in system and cross-reference check number.",
                    "Step 2: If original claim was denied incorrectly, pursue appeal on the original claim ID, not the duplicate.",
                ],
                "standard_notes": "STATUS: Denied CO-18 duplicate. Verified original claim #[OrigClaimID] paid on [PaidDate] under Check#[CheckNum]. Adjusted duplicate claim balance to zero."
            },
            {
                "id": "CO-18-REPEAT-PROCEDURE",
                "title": "Legitimate Repeat Procedure on Same Date of Service",
                "root_cause": "Distinct procedural session occurred on same day (e.g. repeat EKG, bilateral x-ray, multiple lesions) without repeat modifier.",
                "investigation_steps": [
                    "Check clinical records: Was procedure repeated at a separate encounter or distinct anatomical site?",
                    "Verify if Modifier 76 (Repeat procedure by same physician) or Modifier 59/X(EPSU) is justified.",
                ],
                "call_script": {
                    "question_1": "This was a distinct repeat procedure at [Time]. Will appending Modifier 76 allow payment?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24D (Modifier Column)",
                    "required_documents": ["Medical records showing distinct encounter times"],
                },
                "action_plan": [
                    "Step 1: Append Modifier 76 or 59 to duplicate line item.",
                    "Step 2: Submit corrected claim with medical records showing separate sessions.",
                ],
                "standard_notes": "STATUS: Denied CO-18. Verified distinct repeat procedure in chart. Appended modifier 76. Resubmitted with encounter records."
            }
        ]
    },

    "CO-26": {
        "code": "CO-26",
        "category_id": "CAT_ELIGIBILITY",
        "description": "Expenses incurred prior to coverage.",
        "short_name": "Prior to Coverage Effective Date",
        "scenarios": [
            {
                "id": "CO-26-VERIFY-DATES",
                "title": "Date of Service Precedes Policy Inception",
                "root_cause": "Care rendered before insurance policy was active.",
                "investigation_steps": [
                    "Check payer eligibility portal: What was the effective start date of coverage?",
                    "Check if patient had previous active insurance on DOS (e.g., prior employer coverage).",
                ],
                "call_script": {
                    "question_1": "Can you verify the policy effective date for member #[MemberID]?",
                    "question_2": "Was there any retroactive enrollment or grace period covering DOS [DOS]?",
                },
                "form_requirements": {
                    "form_name": "Eligibility Verification Sheet",
                    "box_number": "Box 11a (Insured's DOB/Gender) / Box 12",
                    "required_documents": ["Prior Insurance Card Copy", "Patient Financial Responsibility Waiver"],
                },
                "action_plan": [
                    "Step 1: If patient had prior active insurance, obtain card details and bill the prior carrier.",
                    "Step 2: If no active insurance existed on DOS, transfer balance to patient responsibility with itemized statement.",
                ],
                "standard_notes": "STATUS: Denied CO-26. Policy effective date is [EffDate], DOS was [DOS]. Contacted patient for prior coverage details. Bill transferred to patient if no prior coverage."
            }
        ]
    },

    "CO-27": {
        "code": "CO-27",
        "category_id": "CAT_ELIGIBILITY",
        "description": "Expenses incurred after coverage terminated.",
        "short_name": "Coverage Terminated Prior to Service",
        "scenarios": [
            {
                "id": "CO-27-TERM-CHECK",
                "title": "Patient Policy Terminated Prior to Date of Service",
                "root_cause": "Patient changed jobs, aged off parent plan, or failed to pay premium resulting in policy termination.",
                "investigation_steps": [
                    "Check payer portal: What is the exact termination date?",
                    "Check if patient enrolled in COBRA, Medicaid, or new commercial insurance on DOS.",
                ],
                "call_script": {
                    "question_1": "Can you confirm the policy termination date for member #[MemberID]?",
                    "question_2": "Is there any COBRA coverage pending or new group policy on record?",
                },
                "form_requirements": {
                    "form_name": "Patient Statement",
                    "box_number": "N/A",
                    "required_documents": ["New Insurance Card", "COBRA Election Notice"],
                },
                "action_plan": [
                    "Step 1: Contact patient to request new insurance card or COBRA verification.",
                    "Step 2: If new insurance provided, bill new carrier with clean claim.",
                    "Step 3: If no coverage active on DOS, convert claim to Self-Pay and issue patient statement.",
                ],
                "standard_notes": "STATUS: Denied CO-27. Policy terminated on [TermDate]. Reached out to patient for updated insurance information. Placed in self-pay queue if no coverage provided."
            }
        ]
    },

    "CO-50": {
        "code": "CO-50",
        "category_id": "CAT_MEDICAL_NECESSITY",
        "description": "These are non-covered services because this is not deemed a 'medical necessity' by the payer.",
        "short_name": "Not Deemed Medically Necessary",
        "scenarios": [
            {
                "id": "CO-50-LCD-NCD-APPEAL",
                "title": "Medical Necessity Dispute Citing LCD/NCD Coverage Policies",
                "root_cause": "Billed diagnosis code is not covered under the payer's Local Coverage Determination (LCD) or clinical policy bulletin.",
                "investigation_steps": [
                    "Search CMS Medicare Coverage Database or payer policy bulletin for CPT and allowable ICD-10 codes.",
                    "Review physician encounter notes: Did patient exhibit qualifying symptoms/diagnoses that were omitted?",
                ],
                "call_script": {
                    "question_1": "Which specific Clinical Policy Bulletin or LCD was applied to deny this service?",
                    "question_2": "What is the deadline and fax number for physician peer-to-peer review or formal clinical appeal?",
                },
                "form_requirements": {
                    "form_name": "Formal Clinical Appeal Packet",
                    "box_number": "Box 21 (Diagnosis Codes)",
                    "required_documents": [
                        "Letter of Medical Necessity signed by Physician",
                        "Complete Clinical Chart Notes & Diagnostic Lab/Imaging Reports",
                        "Copy of Relevant LCD / Clinical Policy Bulletin",
                    ],
                },
                "action_plan": [
                    "Step 1: Review clinical notes to determine if a secondary covered diagnosis code was documented but unbilled.",
                    "Step 2: If unbilled covered diagnosis exists in chart, submit corrected claim.",
                    "Step 3: If coding was accurate, generate clinical appeal citing physician rationale and peer-reviewed guidelines.",
                    "Step 4: Offer attending physician the option for peer-to-peer review with payer medical director.",
                ],
                "standard_notes": "STATUS: Denied CO-50 medical necessity. Reviewed chart notes and LCD guidelines. Drafted clinical appeal packet with physician letter of necessity and clinical notes. Submitted to payer appeals dept."
            }
        ]
    },

    "CO-97": {
        "code": "CO-97",
        "category_id": "CAT_DUPLICATE_BUNDLING",
        "description": "The benefit for this service is included in the payment/allowance for another service/procedure that has already been adjudicated.",
        "short_name": "Bundled / Inclusive Service (NCCI Edit)",
        "scenarios": [
            {
                "id": "CO-97-UNBUNDLING-MOD-59",
                "title": "Separate Procedure Eligible for Modifier 59 / X(EPSU)",
                "root_cause": "Procedure bundled under NCCI PTP (Procedure-to-Procedure) edits, but was performed at a distinct anatomical site or session.",
                "investigation_steps": [
                    "Check NCCI edit table: Is the edit modifier indicator '1' (modifier permitted)?",
                    "Verify chart: Did procedure occur at a separate lesion, distinct incision, or separate encounter?",
                ],
                "call_script": {
                    "question_1": "Is this code bundled with CPT [PrimaryCPT] under CMS NCCI edits?",
                    "question_2": "If supported by chart notes as a distinct site, will appending Modifier 59/XS allow unbundling?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24D (Modifier Column)",
                    "required_documents": ["Operative Report with distinct site highlighted"],
                },
                "action_plan": [
                    "Step 1: Verify NCCI indicator allows modifier (Modifier indicator 1).",
                    "Step 2: Append Modifier 59 or specific X-modifier (XE, XS, XP, XU) to secondary procedure.",
                    "Step 3: Submit corrected claim with frequency code 7.",
                ],
                "standard_notes": "STATUS: Denied CO-97 bundled service. NCCI indicator allows modifier. Documentation confirms separate site. Appended Modifier 59 in Box 24D and resubmitted corrected claim."
            }
        ]
    },

    "CO-45": {
        "code": "CO-45",
        "category_id": "CAT_DUPLICATE_BUNDLING",
        "description": "Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement.",
        "short_name": "Contractual Fee Schedule Adjustment",
        "scenarios": [
            {
                "id": "CO-45-CONTRACTUAL-ADJUSTMENT",
                "title": "Normal In-Network Contractual Write-Off",
                "root_cause": "The difference between provider billed charge and payer negotiated allowable fee.",
                "investigation_steps": [
                    "Compare payment received + patient copay/coinsurance against fee schedule.",
                    "Verify that the contractual allowance matches provider in-network fee agreement.",
                ],
                "call_script": {
                    "question_1": "Can you verify if allowable calculation is based on standard in-network fee schedule?",
                },
                "form_requirements": {
                    "form_name": "Remittance Advice ERA Posting",
                    "box_number": "N/A",
                    "required_documents": ["ERA / 835 Remittance File"],
                },
                "action_plan": [
                    "Step 1: Post the CO-45 amount as a contractual adjustment in the billing system.",
                    "Step 2: Ensure the adjusted amount is NOT billed to the patient (protected under in-network contract).",
                ],
                "standard_notes": "STATUS: Processed CO-45. Standard contractual adjustment verified against fee schedule. Posted adjustment to ledger. Patient balance adjusted."
            }
        ]
    },

    "CO-31": {
        "code": "CO-31",
        "category_id": "CAT_ELIGIBILITY",
        "description": "Patient cannot be identified as our insured.",
        "short_name": "Patient Cannot Be Identified",
        "scenarios": [
            {
                "id": "CO-31-ID-MISMATCH",
                "title": "Typo in Member ID, Name, or Date of Birth",
                "root_cause": "Member ID missing alpha prefix, typo in policy number, or mismatch in patient legal name / DOB.",
                "investigation_steps": [
                    "Check physical copy of insurance card in EHR.",
                    "Compare Cardholder ID, Group #, and Patient DOB against claim Box 1a, Box 2, Box 3.",
                ],
                "call_script": {
                    "question_1": "Can you search for the member using their SSN, DOB, and legal name?",
                    "question_2": "Is there an active alpha prefix or suffix required for member ID [MemberID]?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 1a (Insured's ID), Box 2 (Patient Name), Box 3 (DOB)",
                    "required_documents": ["Front & Back Insurance Card Copy"],
                },
                "action_plan": [
                    "Step 1: Verify correct member ID format with payer or patient.",
                    "Step 2: Update patient master file in billing system.",
                    "Step 3: Resubmit clean corrected claim.",
                ],
                "standard_notes": "STATUS: Denied CO-31. Identified typo in Member ID (missing alpha prefix). Corrected Box 1a with [CorrectedID]. Claim resubmitted."
            }
        ]
    }
}
