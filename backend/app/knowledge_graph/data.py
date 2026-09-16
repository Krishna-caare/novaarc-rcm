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
        "description": "Claims denied due to absent clinical documentation, medical review findings, missing modifiers, invoices, or incomplete claim form fields.",
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
    # =========================================================================
    # CATEGORY: MISSING INFORMATION & DOCUMENTATION
    # =========================================================================
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

    "CO-216": {
        "code": "CO-216",
        "category_id": "CAT_MISSING_INFO",
        "description": "Claim/service denied based on the findings of a utilization review organization or medical review team due to insufficient or unsubmitted clinical records.",
        "short_name": "Review Organization / Medical Records Review",
        "scenarios": [
            {
                "id": "CO-216-ADR-AUDIT",
                "title": "Medical Records Requested in Additional Documentation Request (ADR) Not Received",
                "root_cause": "Payer medical review organization (RAC, CERT, UPIC, or Commercial Special Investigations Unit) sent an ADR notice that went unanswered or records were delayed past the deadline.",
                "investigation_steps": [
                    "Check ADR Log: Was an Additional Documentation Request letter received with an ADR Tracking ID?",
                    "Verify the deadline: Did the 30/45-day response window lapse prior to record transmission?",
                    "Check patient record: Is the complete chart available with authenticated physician notes, diagnostic results, and signed treatment plan?",
                ],
                "call_script": {
                    "question_1": "Can you verify the ADR notice generation date, the tracking number, and the specific records requested by the medical review team?",
                    "question_2": "What is the dedicated medical review fax number or secure portal upload URL to transmit these audit records?",
                    "question_3": "Can the review department grant a 14-day extension if initial records were mailed timely with delivery receipt?",
                    "question_4": "What is the representative name, call reference number, and turnaround time once records are uploaded?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500 / Medical Review ADR Packet",
                    "box_number": "Box 19 (Attachment Control #) / PWK Segment",
                    "required_documents": [
                        "Complete Clinical Chart with Attending Physician Signatures",
                        "Diagnostic Test Results & Lab Reports",
                        "ADR Cover Letter with Tracking Number & Provider NPI",
                        "Itemized Charge Breakdown"
                    ],
                },
                "action_plan": [
                    "Step 1: Retrieve complete encounter documentation, physician progress notes, and signed orders from EHR.",
                    "Step 2: Attach the original ADR notification cover letter displaying the claim control and audit tracking number.",
                    "Step 3: Upload directly via the payer's secure provider portal or fax to dedicated Medical Review department.",
                    "Step 4: Obtain confirmation transmission receipt and diary follow-up for 30-45 days for review adjudication.",
                ],
                "standard_notes": "CALL STATUS: Claim denied CO-216 per Medical Review findings. ADR issued on [ADRDate] for complete clinical notes. Pulled chart with signed physician notes and diagnostic results. Uploaded to payer medical review portal with tracking ID [TrackID]. Follow up in 30 days."
            },
            {
                "id": "CO-216-INSUFFICIENT-DOC",
                "title": "Insufficient Documentation to Support Billed Level of Service",
                "root_cause": "The clinical documentation submitted did not sufficiently substantiate the medical complexity, intensity of service, or level of E/M billed.",
                "investigation_steps": [
                    "Review clinical chart: Did physician document History of Present Illness (HPI), exam elements, and Medical Decision Making (MDM) corresponding to billed CPT?",
                    "Compare documentation against payer-specific Local Coverage Determination (LCD) or Clinical Policy Bulletin (CPB).",
                    "Check if physician addendum or peer-to-peer review is permitted for this claim.",
                ],
                "call_script": {
                    "question_1": "Which specific clinical component (MDM, time, or procedure notes) was determined insufficient by the medical reviewer?",
                    "question_2": "Does the plan allow a formal redetermination appeal with supplemental physician notes?",
                    "question_3": "What is the deadline and submission address for the formal clinical appeals department?",
                },
                "form_requirements": {
                    "form_name": "First-Level Redetermination Appeal Form",
                    "box_number": "Box 21 (Diagnosis Codes) & Box 24D (CPT/Modifiers)",
                    "required_documents": [
                        "Letter of Medical Necessity signed by Attending Physician",
                        "Physician Addendum clarifying clinical complexity",
                        "Complete Inpatient/Outpatient Chart Notes",
                        "Relevant Peer-Reviewed Literature or LCD Guidelines"
                    ],
                },
                "action_plan": [
                    "Step 1: Coordinate with billing physician to prepare a clinical addendum clarifying patient acuity and MDM.",
                    "Step 2: Draft a formal Level-1 Redetermination Appeal citing specific payer policy criteria met.",
                    "Step 3: Submit the clinical appeal packet with medical records via certified mail or portal dispute mechanism.",
                    "Step 4: Set follow-up task for 45-60 days to track appeal determination.",
                ],
                "standard_notes": "STATUS: Denied CO-216 for insufficient documentation. Coordinated with physician; clinical addendum drafted addressing medical complexity. Compiled Level-1 Redetermination Appeal with LCD citations. Submitted to appeals dept. Next follow-up: 45 days."
            }
        ]
    },

    "CO-226": {
        "code": "CO-226",
        "category_id": "CAT_MISSING_INFO",
        "description": "Information requested from the billing/rendering provider was not provided, not provided timely, or was insufficient/incomplete.",
        "short_name": "Provider Information Incomplete / Not Provided",
        "scenarios": [
            {
                "id": "CO-226-UNANSWERED-LETTER",
                "title": "Unanswered Payer Development Request / Itemized Invoice Needed",
                "root_cause": "Payer sent development questionnaire requesting manufacturer implant invoice, unlisted CPT description, or W-9 form that was not received.",
                "investigation_steps": [
                    "Check correspondence log: Was a provider development letter received requesting specific line item invoices?",
                    "Verify if unlisted CPT code (e.g., 22899, 99499) was billed without an itemized manufacturer invoice or detailed narrative.",
                ],
                "call_script": {
                    "question_1": "What specific document or information was requested in your development letter for this claim?",
                    "question_2": "What is the fax number or portal upload tab to send the requested invoice/records?",
                    "question_3": "Can the claim be reopened upon receipt of this information without filing a formal appeal?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500 / Provider Development Packet",
                    "box_number": "Box 19 (Narrative / Attachment Control) & Box 24D",
                    "required_documents": ["Manufacturer Implant/Device Acquisition Invoice", "Operative Summary detailing unlisted procedure"],
                },
                "action_plan": [
                    "Step 1: Obtain the vendor device invoice and operative summary from materials management.",
                    "Step 2: Fax the requested invoice with the original payer development letter as the cover sheet.",
                    "Step 3: Call payer in 14 days to confirm document indexing and request phone reprocessing.",
                ],
                "standard_notes": "STATUS: Denied CO-226 for missing implant invoice. Retrieved vendor invoice from materials management. Faxed with development notice to payer review. Diary set for 14 days."
            }
        ]
    },

    "CO-227": {
        "code": "CO-227",
        "category_id": "CAT_MISSING_INFO",
        "description": "Information requested from the patient/insured was not provided or was insufficient/incomplete.",
        "short_name": "Patient Information Incomplete / Not Provided",
        "scenarios": [
            {
                "id": "CO-227-PATIENT-QUESTIONNAIRE",
                "title": "Patient Failed to Respond to Accident / Subrogation Questionnaire",
                "root_cause": "Payer requires insured patient to complete trauma questionnaire determining auto liability, workers comp, or other insurance responsibility.",
                "investigation_steps": [
                    "Check diagnosis codes: Was trauma/accident ICD-10 code (e.g., V-codes, W-codes, Y-codes) billed?",
                    "Check payer eligibility portal: Is there an open casualty/subrogation hold on the member's account?",
                ],
                "call_script": {
                    "question_1": "Does the payer require the patient to complete an accident questionnaire before claim payment?",
                    "question_2": "Can provider staff submit the accident details from the clinical notes on the patient's behalf?",
                    "question_3": "What is the direct member services phone number and mailing address for the questionnaire?",
                },
                "form_requirements": {
                    "form_name": "Patient Accident / Subrogation Questionnaire",
                    "box_number": "Box 10a-c (Auto / Employment / Other Accident)",
                    "required_documents": ["Member Accident Questionnaire", "Police Report (if motor vehicle accident)"],
                },
                "action_plan": [
                    "Step 1: Contact patient via phone and portal message informing them insurance is withholding payment pending accident questionnaire.",
                    "Step 2: Provide patient with payer claim number and direct toll-free questionnaire line.",
                    "Step 3: If patient confirms injury was not work/auto related, document and notify payer.",
                    "Step 4: If patient refuses to cooperate within 30 days, transfer responsibility to patient per financial agreement.",
                ],
                "standard_notes": "STATUS: Denied CO-227. Insurer holds claim for member accident questionnaire. Contacted patient: instructed to call [PayerPhone] with Claim#[ClaimID]. Placed in 14-day hold queue."
            }
        ]
    },

    "CO-252": {
        "code": "CO-252",
        "category_id": "CAT_MISSING_INFO",
        "description": "An attachment/other documentation is required to adjudicate this claim/service, but was not received or was illegible.",
        "short_name": "Attachment / Documentation Not Received",
        "scenarios": [
            {
                "id": "CO-252-MISSING-ATTACHMENT",
                "title": "EDI 275 Attachment or Paper Attachment Not Linked to Claim",
                "root_cause": "Claim submitted with PWK segment indicator, but clearinghouse or payer did not link the electronic or faxed attachment to the 837 claim file.",
                "investigation_steps": [
                    "Check clearinghouse 277 report: Was the Attachment Control Number (ACN) reported in the PWK loop?",
                    "Verify if attachment was faxed with the mandatory Payer Attachment Barcode Cover Sheet.",
                ],
                "call_script": {
                    "question_1": "Can you check if attachment with Control#[ACN] is received in your document imaging system?",
                    "question_2": "What is the direct barcode fax number to resend the attachment linked to Claim#[ClaimID]?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500 / EDI PWK Loop 2300",
                    "box_number": "Box 19 / EDI Loop 2300 PWK Segment",
                    "required_documents": ["Payer Attachment Barcode Cover Sheet", "Clinical Records / Operative Notes"],
                },
                "action_plan": [
                    "Step 1: Generate payer barcode cover sheet displaying Claim Control # and Attachment Control #.",
                    "Step 2: Fax documentation with barcode cover sheet to dedicated claims imaging fax.",
                    "Step 3: Call representative in 7-10 business days to confirm document attachment and request reprocessing.",
                ],
                "standard_notes": "STATUS: Denied CO-252. Attachment was not linked. Generated barcoded cover sheet with ACN#[ACN]. Resubmitted records to imaging fax. Follow-up: 10 days."
            }
        ]
    },

    "M119": {
        "code": "M119",
        "category_id": "CAT_MISSING_INFO",
        "description": "Missing/incomplete/invalid/deactivated/withdrawn National Drug Code (NDC).",
        "short_name": "Missing / Invalid National Drug Code (NDC)",
        "scenarios": [
            {
                "id": "M119-NDC-MISMATCH",
                "title": "Missing or Invalid 11-Digit NDC on HCPCS J-Code",
                "root_cause": "Medication billed with J-code (e.g., J0131, J1745) omitted the 11-digit NDC number, unit of measure (UN, ML, GR, F2), or quantity.",
                "investigation_steps": [
                    "Check Box 24A shaded area: Is an 11-digit NDC present in 5-4-2 format?",
                    "Verify NDC qualifier: Is 'N4' preceding the 11-digit NDC code?",
                    "Verify unit qualifier: Is valid unit of measure (e.g. UN1, ML10) specified?",
                ],
                "call_script": {
                    "question_1": "Does your system require the NDC in 11-digit 5-4-2 configuration without hyphens?",
                    "question_2": "Can this be corrected via electronic corrected claim (Frequency 7)?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24A Shaded Top Line (N4 Qualifier + 11-Digit NDC + Unit)",
                    "required_documents": ["Corrected Claim with valid NDC from vial/packaging"],
                },
                "action_plan": [
                    "Step 1: Check medication package or inventory log for exact 11-digit NDC number.",
                    "Step 2: Format NDC with qualifier N4 in Box 24A top shaded section, followed by unit qualifier (e.g., UN) and quantity.",
                    "Step 3: Submit electronic corrected claim with Claim Frequency Code 7.",
                ],
                "standard_notes": "STATUS: Denied M119 for NDC. Retrieved valid 11-digit NDC #[NDCNum] from drug inventory. Corrected Box 24A with N4 qualifier and UN unit. Resubmitted electronically."
            }
        ]
    },

    "MA120": {
        "code": "MA120",
        "category_id": "CAT_MISSING_INFO",
        "description": "Missing/incomplete/invalid CLIA certification number.",
        "short_name": "Missing / Invalid CLIA Number",
        "scenarios": [
            {
                "id": "MA120-CLIA-MISSING",
                "title": "CLIA Certificate Number Omitted from Laboratory Claim",
                "root_cause": "In-office laboratory test (e.g., CPT 81002, 87880, 85025) billed without the 10-digit CLIA number in Box 23.",
                "investigation_steps": [
                    "Check Box 23: Is the practice's 10-character CLIA certificate number present?",
                    "Check CLIA Certificate type: Does certificate cover the specific complexity (Waived, Moderate, High) of the billed CPT?",
                ],
                "call_script": {
                    "question_1": "Can you verify if our CLIA number is on file with your provider credentialing department?",
                    "question_2": "Will adding the CLIA number to Box 23 allow claim reprocessing via electronic corrected claim?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 23 (Prior Auth / CLIA Number)",
                    "required_documents": ["CMS CLIA Certificate of Waiver / Compliance"],
                },
                "action_plan": [
                    "Step 1: Insert 10-character CLIA certificate number into Box 23 of CMS-1500.",
                    "Step 2: Append QW modifier if test is designated CLIA-waived under CMS regulations.",
                    "Step 3: Resubmit as electronic corrected claim.",
                ],
                "standard_notes": "STATUS: Denied MA120. CLIA #[CLIANum] inserted into Box 23. Appended modifier QW to lab CPT. Transmitted as corrected claim."
            }
        ]
    },

    # =========================================================================
    # CATEGORY: PRIOR AUTHORIZATION & REFERRALS
    # =========================================================================
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

    "CO-198": {
        "code": "CO-198",
        "category_id": "CAT_PRIOR_AUTH",
        "description": "Precertification/Authorization exceeded (units or days).",
        "short_name": "Authorization Exceeded",
        "scenarios": [
            {
                "id": "CO-198-UNITS-EXCEEDED",
                "title": "Billed Units Exceeded Authorized Quantity",
                "root_cause": "Authorization was granted for 4 therapy sessions or 2 drug units, but 6 were rendered and billed.",
                "investigation_steps": [
                    "Check original auth letter: How many units/visits were approved?",
                    "Check billing history: Have previous claims already consumed authorized units?",
                ],
                "call_script": {
                    "question_1": "How many units were approved under auth #[AuthNum], and how many units have been paid to date?",
                    "question_2": "Can the provider submit an authorization extension request for the additional medically necessary units?",
                },
                "form_requirements": {
                    "form_name": "Prior Authorization Modification Request",
                    "box_number": "Box 24G (Days or Units)",
                    "required_documents": ["Physician Treatment Plan", "Clinical Progress Notes showing ongoing medical necessity"],
                },
                "action_plan": [
                    "Step 1: Request an authorization amendment/extension from the clinical utilization department.",
                    "Step 2: If amended, rebill unpaid units with amended authorization ID.",
                    "Step 3: If amendment denied, appeal with documentation of unexpected surgical complexity or patient condition.",
                ],
                "standard_notes": "STATUS: Denied CO-198 for units exceeded. Submitted authorization modification request for 2 additional units with clinical chart notes. Follow-up: 14 days."
            }
        ]
    },

    "CO-15": {
        "code": "CO-15",
        "category_id": "CAT_PRIOR_AUTH",
        "description": "Payment adjusted because the submitted authorization was not obtained.",
        "short_name": "Authorization Not Obtained",
        "scenarios": [
            {
                "id": "CO-15-NO-AUTH",
                "title": "Missing Referral or Pre-Certification from Primary Care Physician (PCP)",
                "root_cause": "HMO/POS plan requires referral from assigned PCP before specialist consultation.",
                "investigation_steps": [
                    "Check if patient's policy is HMO requiring PCP referral.",
                    "Check if PCP issued a referral number prior to the specialist visit.",
                ],
                "call_script": {
                    "question_1": "Does this member have an active PCP referral on file covering the specialist consultation on [DOS]?",
                    "question_2": "Can PCP submit a retroactive referral to allow claim reprocessing?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 17 (Name of Referring Provider) & Box 17b (NPI)",
                    "required_documents": ["PCP Referral Letter / Authorization Slip"],
                },
                "action_plan": [
                    "Step 1: Contact PCP office to obtain copy of referral or request retroactive referral submission.",
                    "Step 2: Enter referral # into Box 23 and PCP NPI into Box 17b.",
                    "Step 3: Resubmit claim for adjudication.",
                ],
                "standard_notes": "STATUS: Denied CO-15. Contacted PCP office; obtained referral #[RefNum]. Updated Box 17b and Box 23. Resubmitted claim."
            }
        ]
    },

    # =========================================================================
    # CATEGORY: TIMELY FILING & DEADLINES
    # =========================================================================
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
                        "Timely Filing Rebuttal Cover Letter"
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

    # =========================================================================
    # CATEGORY: COORDINATION OF BENEFITS (COB)
    # =========================================================================
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

    "CO-23": {
        "code": "CO-23",
        "category_id": "CAT_COB",
        "description": "The impact of prior payer(s) adjudication including payments and/or adjustments.",
        "short_name": "Prior Payer Adjudication Needed",
        "scenarios": [
            {
                "id": "CO-23-MISSING-PRIMARY-EOB",
                "title": "Secondary Claim Submitted Without Primary Remittance Information",
                "root_cause": "Secondary claim submitted electronically without the 837 COB Loop 2320 primary paid amount, allowed amount, and adjustment codes.",
                "investigation_steps": [
                    "Check EDI 837 file: Was Loop 2320 (Other Subscriber Information) populated with primary payment details?",
                    "Verify if primary payer CARC/RARC codes were included in CAS segments.",
                ],
                "call_script": {
                    "question_1": "Did you receive the primary payment and adjustment breakdown with this secondary submission?",
                    "question_2": "Can we fax or upload the primary EOB directly to your secondary claims processing unit?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500 / Secondary 837P",
                    "box_number": "Box 29 (Amount Paid) & Loop 2320",
                    "required_documents": ["Complete Primary Explanation of Benefits (EOB)"],
                },
                "action_plan": [
                    "Step 1: Ensure primary EOB amounts and CARC adjustments are mapped into billing software.",
                    "Step 2: Re-transmit secondary claim electronically with complete Loop 2320 and 2430 details.",
                ],
                "standard_notes": "STATUS: Denied CO-23. Re-entered primary payment and adjustment amounts into billing software. Resubmitted clean secondary claim."
            }
        ]
    },

    # =========================================================================
    # CATEGORY: MEDICAL NECESSITY & LEVEL OF SERVICE
    # =========================================================================
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
                        "Copy of Relevant LCD / Clinical Policy Bulletin"
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

    "CO-55": {
        "code": "CO-55",
        "category_id": "CAT_MEDICAL_NECESSITY",
        "description": "Procedure/treatment/drug is deemed experimental/investigational by the payer.",
        "short_name": "Experimental / Investigational Service",
        "scenarios": [
            {
                "id": "CO-55-EXPERIMENTAL",
                "title": "Procedure Denied as Investigational / Off-Label Use",
                "root_cause": "Payer policy considers new surgical technique or off-label drug therapy experimental without FDA approval for that specific indication.",
                "investigation_steps": [
                    "Check FDA approval status and compendia listings (NCCN, Micromedex) for the billed drug/device.",
                    "Check if patient executed an Advance Beneficiary Notice (ABN) or Notice of Non-Coverage prior to treatment.",
                ],
                "call_script": {
                    "question_1": "Does the payer accept clinical appeal packets with peer-reviewed medical journals proving standard of care?",
                    "question_2": "What is the second-level external review deadline if the internal appeal is upheld?",
                },
                "form_requirements": {
                    "form_name": "Experimental Clinical Appeal Packet",
                    "box_number": "Box 24D",
                    "required_documents": ["Peer-reviewed journal studies", "Letter of Medical Necessity", "FDA approval letter / compendia excerpt"],
                },
                "action_plan": [
                    "Step 1: Gather clinical evidence and peer-reviewed oncology/surgical literature supporting efficacy.",
                    "Step 2: Submit comprehensive medical appeal packet to payer clinical review panel.",
                ],
                "standard_notes": "STATUS: Denied CO-55. Assembled medical literature and physician letter supporting efficacy. Submitted formal appeal to clinical dispute committee."
            }
        ]
    },

    # =========================================================================
    # CATEGORY: CODING, INCONSISTENCIES & MODIFIER EDITS
    # =========================================================================
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

    "CO-5": {
        "code": "CO-5",
        "category_id": "CAT_CODING_MODIFIERS",
        "description": "The procedure code/type of bill is inconsistent with the place of service.",
        "short_name": "Place of Service Inconsistent with Procedure",
        "scenarios": [
            {
                "id": "CO-5-POS-MISMATCH",
                "title": "Hospital-Only Procedure Billed with Office POS (11) or Vice Versa",
                "root_cause": "CPT code can only be performed in inpatient facility (POS 21) or ambulatory surgical center (POS 24), but was billed with POS 11 (Office).",
                "investigation_steps": [
                    "Check CPT guidelines: What are the valid CMS Place of Service codes for this procedure?",
                    "Verify Box 24B on CMS-1500 against encounter facility records.",
                ],
                "call_script": {
                    "question_1": "Can you verify the allowable Place of Service codes for CPT [CPTCode]?",
                    "question_2": "Will correcting Box 24B to the accurate facility code resolve the denial?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24B (Place of Service)",
                    "required_documents": ["Facility Encounter Log"],
                },
                "action_plan": [
                    "Step 1: Confirm exact physical location where service was rendered.",
                    "Step 2: Update Box 24B with valid POS (e.g., 22 for Outpatient Hospital, 24 for ASC).",
                    "Step 3: Resubmit corrected claim.",
                ],
                "standard_notes": "STATUS: Denied CO-5. Updated Place of Service in Box 24B from 11 to 22 per hospital records. Resubmitted corrected claim."
            }
        ]
    },

    "CO-8": {
        "code": "CO-8",
        "category_id": "CAT_CODING_MODIFIERS",
        "description": "The procedure code is inconsistent with the provider type/specialty (taxonomy).",
        "short_name": "Provider Specialty / Taxonomy Inconsistent",
        "scenarios": [
            {
                "id": "CO-8-TAXONOMY-SPECIALTY",
                "title": "Specialty Billing Restriction Mismatch",
                "root_cause": "CPT restricted to specific medical specialty (e.g., cardiology, ophthalmology) billed under a general provider taxonomy.",
                "investigation_steps": [
                    "Check NPPES NPI Registry for rendering provider primary and secondary taxonomy codes.",
                    "Verify if mid-level modifier (SA, SA, AF) is required for nurse practitioner or physician assistant.",
                ],
                "call_script": {
                    "question_1": "What specialty or taxonomy code does your enrollment department require for this procedure code?",
                    "question_2": "Can the rendering provider's secondary enrolled taxonomy be submitted in Box 24J qualifier ZZ?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24J & Box 33b (Taxonomy Code with ZZ Qualifier)",
                    "required_documents": ["Provider Specialty Board Certification"],
                },
                "action_plan": [
                    "Step 1: Check payer enrollment file for approved provider taxonomies.",
                    "Step 2: Append appropriate modifier or update Box 24J with registered taxonomy code.",
                    "Step 3: Resubmit claim.",
                ],
                "standard_notes": "STATUS: Denied CO-8. Updated Box 24J with enrolled specialty taxonomy code [TaxonomyCode]. Resubmitted claim."
            }
        ]
    },

    "CO-11": {
        "code": "CO-11",
        "category_id": "CAT_CODING_MODIFIERS",
        "description": "The diagnosis is inconsistent with the procedure.",
        "short_name": "Diagnosis Inconsistent with Procedure",
        "scenarios": [
            {
                "id": "CO-11-DX-POINTER",
                "title": "Incorrect Diagnosis Pointer in Box 24E",
                "root_cause": "The diagnosis code entered in Box 21 does not justify the CPT code on line 24, or Box 24E pointed to an unrelated diagnosis.",
                "investigation_steps": [
                    "Check Box 24E: Does diagnosis pointer letter (A-L) point to the clinical condition treated by this procedure?",
                    "Check payer LCD: Is the pointed diagnosis code listed on the covered ICD-10 list?",
                ],
                "call_script": {
                    "question_1": "Can you advise which diagnosis pointers were linked to line item [LineNum] during adjudication?",
                    "question_2": "Does your coverage policy accept ICD-10 [ICDCode] as medically justifiable for this CPT?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24E (Diagnosis Pointer) & Box 21 (ICD-10 Codes)",
                    "required_documents": ["Clinical Chart Notes verifying diagnosis"],
                },
                "action_plan": [
                    "Step 1: Review medical records and link primary symptom/disease diagnosis to procedure in Box 24E.",
                    "Step 2: Ensure correct order of diagnosis codes in Box 21.",
                    "Step 3: Resubmit as corrected claim.",
                ],
                "standard_notes": "STATUS: Denied CO-11. Corrected Box 24E diagnosis pointer from 'B' to 'A' to link covered ICD-10 code. Re-transmitted claim."
            }
        ]
    },

    # =========================================================================
    # CATEGORY: DUPLICATE, BUNDLING & NCCI EDITS
    # =========================================================================
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
                    "Compare payment received + patient copay/coinsurance against provider fee schedule contract.",
                    "Verify that write-off amount matches contractual discount percentage.",
                ],
                "call_script": {
                    "question_1": "Can you verify the allowable amount for CPT [CPTCode] under provider agreement?",
                },
                "form_requirements": {
                    "form_name": "Remittance Advice Posting",
                    "box_number": "N/A",
                    "required_documents": ["Provider Fee Schedule Matrix"],
                },
                "action_plan": [
                    "Step 1: Verify payment against contracted fee schedule.",
                    "Step 2: Post CO-45 write-off adjustment to patient ledger (cannot balance bill patient).",
                ],
                "standard_notes": "STATUS: Processed CO-45. Standard contractual adjustment verified against fee schedule. Posted adjustment to ledger. Patient balance adjusted."
            }
        ]
    },

    "CO-234": {
        "code": "CO-234",
        "category_id": "CAT_DUPLICATE_BUNDLING",
        "description": "This procedure is not paid separately.",
        "short_name": "Procedure Not Paid Separately",
        "scenarios": [
            {
                "id": "CO-234-INCIDENTAL",
                "title": "Incidental Component of Primary Procedure",
                "root_cause": "Supply, surgical tray, or incidental minor procedure deemed part of the primary operative fee.",
                "investigation_steps": [
                    "Check CMS Physician Fee Schedule Relative Value File: Is status indicator 'B' (Bundled)?",
                    "Verify if procedure was distinct and eligible for unbundling modifier.",
                ],
                "call_script": {
                    "question_1": "Is CPT [CPTCode] considered bundled under all circumstances, or is an override modifier permitted?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 24D",
                    "required_documents": ["Operative Report"],
                },
                "action_plan": [
                    "Step 1: If code has CMS Status B with no modifier exemption, adjust balance as contractual bundle.",
                    "Step 2: If clinical exception applies, submit chart notes on appeal.",
                ],
                "standard_notes": "STATUS: Denied CO-234 incidental service. CMS status verified as bundled. Posted contractual adjustment."
            }
        ]
    },

    # =========================================================================
    # CATEGORY: ELIGIBILITY, IDENTIFICATION & TERMINATION
    # =========================================================================
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

    "CO-31": {
        "code": "CO-31",
        "category_id": "CAT_ELIGIBILITY",
        "description": "Patient cannot be identified as our insured.",
        "short_name": "Patient Not Identified as Insured",
        "scenarios": [
            {
                "id": "CO-31-ID-MISMATCH",
                "title": "Member ID, Name, or Date of Birth Mismatch",
                "root_cause": "Typo in member ID, maiden name billed instead of married name, or incorrect date of birth in Box 3.",
                "investigation_steps": [
                    "Compare CMS-1500 Box 1a (Insured ID), Box 2 (Patient Name), and Box 3 (DOB) against insurance card copy.",
                    "Check clearinghouse 270/271 eligibility response for exact subscriber name spelling.",
                ],
                "call_script": {
                    "question_1": "Can you locate member using patient SSN, full legal name, and date of birth?",
                    "question_2": "What is the exact subscriber ID number and suffix active in your system?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 1a (Insured's ID Number), Box 2 (Patient Name), Box 3 (DOB)",
                    "required_documents": ["Copy of Front & Back of Insurance Card"],
                },
                "action_plan": [
                    "Step 1: Correct member ID, name spelling, or DOB in patient master file.",
                    "Step 2: Re-verify real-time 270 eligibility.",
                    "Step 3: Resubmit as clean claim.",
                ],
                "standard_notes": "STATUS: Denied CO-31. Identified typo in Member ID (transposed digits). Corrected Box 1a to [CorrectID]. Electronically rebilled."
            }
        ]
    },

    "CO-109": {
        "code": "CO-109",
        "category_id": "CAT_ELIGIBILITY",
        "description": "Claim/service not covered by this payer/contractor. You must send the claim/service to the correct payer/contractor.",
        "short_name": "Wrong Payer / Contractor",
        "scenarios": [
            {
                "id": "CO-109-WRONG-PAYER",
                "title": "Claim Sent to Wrong Payer ID or Sub-Plan",
                "root_cause": "Claim submitted to regional BCBS instead of out-of-state home plan, or submitted to commercial plan instead of Medicare Advantage carve-out.",
                "investigation_steps": [
                    "Check 3-character alpha prefix on BCBS card (BlueCard routing rules).",
                    "Verify if behavioral health, vision, or chiropractic is carved out to a third-party administrator (TPA).",
                ],
                "call_script": {
                    "question_1": "Which specific payer or sub-contractor is responsible for processing this service?",
                    "question_2": "What is the correct electronic Payer ID and mailing address?",
                },
                "form_requirements": {
                    "form_name": "CMS-1500",
                    "box_number": "Box 11c (Insurance Plan Name / Program) & EDI Payer ID",
                    "required_documents": ["Member Insurance Card with correct Payer ID"],
                },
                "action_plan": [
                    "Step 1: Update billing software with correct electronic Payer ID.",
                    "Step 2: Submit initial clean claim to the correct payer within timely filing limits.",
                ],
                "standard_notes": "STATUS: Denied CO-109 wrong payer. Carved out to [NewPayer]. Re-routed clean claim to correct Payer ID [PayerID]."
            }
        ]
    }
}
