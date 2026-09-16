# NovaArc RCM — Complete API & Service Reference Manual

> **Target Audience**: AI Agents (resuming from truncated context), API Integrators, Backend & Frontend Developers.
> **Backend Base URL (Local)**: `http://localhost:8000`
> **Backend Base URL (Production)**: `https://novaarc-backend.onrender.com`
> **Authentication**: All protected endpoints require `Authorization: Bearer <access_token>`.

---

## 1. Global Conventions & Standards

### Authentication Header
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Obtained via `POST /auth/login`. Tokens are JWTs containing the user ID in the `sub` claim.

### Standard Response Formats
- **Success**: HTTP 200 (or 201 for resource creation) returning JSON response bodies.
- **Validation Error (HTTP 422)**: Pydantic v2 validation errors:
  ```json
  {
    "detail": [
      {
        "loc": ["body", "charge_amount"],
        "msg": "Input should be a valid number",
        "type": "decimal_parsing"
      }
    ]
  }
  ```
- **Error (HTTP 400, 401, 403, 404, 500)**:
  ```json
  {
    "detail": "Claim 1024 not found"
  }
  ```

---

## 2. Authentication API (`/auth`)

Defined in: [backend/app/routers/auth.py](file:///b:/Baskar/nova%20arc/backend/app/routers/auth.py)

### 2.1 Login
- **Endpoint**: `POST /auth/login`
- **Auth**: Public
- **Request Body**:
  ```json
  {
    "email": "ops_manager@novaarc.local",
    "password": "password123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer"
  }
  ```

### 2.2 Register User
- **Endpoint**: `POST /auth/register`
- **Auth**: Protected (`ops_manager`, `ops_leadership`, `client_leadership`)
- **Request Body**:
  ```json
  {
    "name": "Jane Smith",
    "email": "jane@novaarc.local",
    "password": "securepassword",
    "role": "ar_executive"
  }
  ```
- **Roles allowed**: `client_leadership`, `ops_leadership`, `ops_manager`, `team_lead`, `ar_executive`, `qa_auditor`
- **Response (201 Created)**: User record object.

### 2.3 Get Current User Profile
- **Endpoint**: `GET /auth/me`
- **Auth**: Protected (Any valid JWT)
- **Response (200 OK)**:
  ```json
  {
    "user_id": 1,
    "name": "Operations Manager",
    "role": "ops_manager",
    "email": "ops_manager@novaarc.local",
    "is_active": true,
    "created_at": "2026-09-10T12:00:00Z"
  }
  ```

### 2.4 List All Users
- **Endpoint**: `GET /auth/users`
- **Auth**: Protected (Management roles)
- **Response (200 OK)**: Array of User objects.

### 2.5 List Roles
- **Endpoint**: `GET /auth/roles`
- **Auth**: Public
- **Response (200 OK)**: `["client_leadership", "ops_leadership", "ops_manager", "team_lead", "ar_executive", "qa_auditor"]`

---

## 3. Claims API (`/claims`)

Defined in: [backend/app/routers/claims.py](file:///b:/Baskar/nova%20arc/backend/app/routers/claims.py)

### 3.1 Claims Statistics Summary
- **Endpoint**: `GET /claims/stats/summary`
- **Auth**: Protected
- **Response (200 OK)**:
  ```json
  {
    "total_claims": 50,
    "by_status": [
      { "status": "created", "count": 10, "total_charges": 14500.0 },
      { "status": "submitted", "count": 15, "total_charges": 32000.0 },
      { "status": "paid", "count": 20, "total_charges": 45000.0 },
      { "status": "denied", "count": 5, "total_charges": 8500.0 }
    ],
    "total_charges": 100000.0,
    "total_paid": 45000.0,
    "collection_rate": 45.0
  }
  ```

### 3.2 List Claims
- **Endpoint**: `GET /claims`
- **Auth**: Protected
- **Query Parameters**:
  - `status` (optional string): `created`, `submitted`, `acknowledged`, `in_process`, `paid`, `denied`, `appealed`
  - `payer_id` (optional int)
  - `provider_id` (optional int)
  - `patient_id` (optional int)
  - `date_from` (optional date: `YYYY-MM-DD`)
  - `date_to` (optional date: `YYYY-MM-DD`)
  - `skip` (optional int, default `0`)
  - `limit` (optional int, default `50`)
- **Response (200 OK)**: Array of Claim objects with eager-loaded `patient`, `provider`, and `payer`.

### 3.3 Get Reference Data
- **Endpoint**: `GET /claims/reference-data`
- **Auth**: Protected
- **Response (200 OK)**:
  ```json
  {
    "patients": [{ "patient_id": 1, "mrn": "MRN126225", "payer_id": 1 }],
    "providers": [{ "provider_id": 1, "name": "Dr. Amanda Davis, MD", "specialty": "Cardiology" }],
    "payers": [{ "payer_id": 1, "name": "Aetna Commercial" }]
  }
  ```

### 3.4 Get Claim Detail
- **Endpoint**: `GET /claims/{claim_id}`
- **Auth**: Protected
- **Response (200 OK)**: Complete ClaimDetail object including nested `patient`, `provider`, `payer`, `denials`, `payments`, and `agent_runs`.

### 3.5 Create Claim
- **Endpoint**: `POST /claims`
- **Auth**: Protected
- **Request Body**:
  ```json
  {
    "patient_id": 1,
    "provider_id": 1,
    "payer_id": 1,
    "date_of_service": "2026-09-16",
    "charge_amount": 250.00,
    "cpt_codes": ["99214"],
    "icd10_codes": ["I10", "E11.9"],
    "modifiers": ["25"]
  }
  ```
- **Side Effects**: Automatically calls `assign_claim_to_queue(db, claim_id)` to assign the new claim to the *New Claims - Review* work queue.
- **Response (201 Created)**: Created Claim object.

### 3.6 Update Claim
- **Endpoint**: `PATCH /claims/{claim_id}` and `PUT /claims/{claim_id}`
- **Auth**: Protected
- **Request Body**: Partial Claim fields (`status`, `charge_amount`, `paid_amount`, `cpt_codes`, `icd10_codes`, etc.)
- **Multi-Entity Synchronization Side Effects**:
  - If `status == "paid"`: Sets `paid_amount = charge_amount` if unset, and automatically creates a matching `Payment` record with remittance reference `ERA-<id>-<ts>`.
  - If `status == "denied"`: Automatically checks for an existing `Denial` record; if none exists, creates a `CO-16` Denial record and routes claim into the *Denials - Work* queue.
  - If `status == "submitted"`: Stamps `submitted_at` and creates `edi_837_ref`.
- **Response (200 OK)**: Updated Claim object.

### 3.7 Submit Claim
- **Endpoint**: `POST /claims/{claim_id}/submit`
- **Auth**: Protected
- **Validation**: Requires claim to be in `created` status.
- **Side Effects**:
  - Generates HIPAA EDI 837P content via `generate_837_claim(claim)`.
  - Sets `status = "submitted"`, `submitted_at = func.now()`, `edi_837_ref = "EDI837-<id>-<ts>"`.
  - Re-evaluates queue assignment.
- **Response (200 OK)**: Updated Claim object.

### 3.8 Extract Clinical Document (PDF / Superbill)
- **Endpoint**: `POST /claims/extract-document`
- **Auth**: Protected
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Uploaded file (`.pdf`, `.txt`, `.md`, etc.)
  - `patient_id` (optional string): ID of patient for clinical context
- **Implementation Details**:
  - Uses `pypdf.PdfReader` to extract textual content across all pages.
  - Automatically queries the Medical Coding Agent (`suggest_codes`) powered by Ling 3.0 Flash Santé.
  - Computes outpatient fee schedule charges based on suggested CPTs.
- **Response (200 OK)**:
  ```json
  {
    "filename": "clinical_encounter.pdf",
    "extracted_text": "CLINICAL ENCOUNTER NOTE...",
    "word_count": 84,
    "icd10_suggestions": [
      { "code": "I10", "description": "Essential (primary) hypertension", "confidence": 0.95, "rationale": "..." }
    ],
    "cpt_suggestions": [
      { "code": "99214", "description": "Office outpatient 30-39 min", "confidence": 0.92, "modifiers": ["25"], "rationale": "..." }
    ],
    "suggested_cpt": "99214",
    "suggested_icd10": "I10, E11.9",
    "suggested_charge": 215.00,
    "confidence": 0.92,
    "documentation_gaps": []
  }
  ```

---

## 4. Denials API (`/denials`)

Defined in: [backend/app/routers/denials.py](file:///b:/Baskar/nova%20arc/backend/app/routers/denials.py)

### 4.1 List Denials
- **Endpoint**: `GET /denials`
- **Auth**: Protected
- **Query Parameters**: `claim_id`, `denial_code`, `appeal_status`, `date_from`, `date_to`, `skip`, `limit`
- **Auto-Sync Side Effect**: Automatically checks for any claims in the DB marked as `denied` that lack a `Denial` record, and instantiates them on the fly.
- **Response (200 OK)**: Array of Denial objects with nested `claim.patient`, `claim.provider`, `claim.payer`.

### 4.2 Get Top Denial Codes
- **Endpoint**: `GET /denials/top-codes`
- **Auth**: Protected
- **Query Parameters**: `limit` (default `10`)
- **Response (200 OK)**:
  ```json
  [
    {
      "denial_code": "CO-16",
      "count": 12,
      "total_denied_amount": 18500.00,
      "avg_denied_amount": 1541.67
    }
  ]
  ```

### 4.3 Get Denial Detail
- **Endpoint**: `GET /denials/{denial_id}`
- **Auth**: Protected
- **Response (200 OK)**: Denial object.

### 4.4 Update Denial
- **Endpoint**: `PATCH /denials/{denial_id}` and `PUT /denials/{denial_id}`
- **Auth**: Protected
- **Request Body**: Partial Denial fields (`appeal_status`, `denial_code`, `root_cause`, etc.)
- **Auto-Sync Side Effect**:
  - If `appeal_status == "won"`: Automatically updates parent claim `status = "paid"` and sets `paid_amount = charge_amount`.
  - If `appeal_status == "submitted"`: Automatically updates parent claim `status = "appealed"`.
- **Response (200 OK)**: Updated Denial object.

### 4.5 AI Appeal Letter Drafter
- **Endpoint**: `POST /denials/{denial_id}/draft-appeal`
- **Auth**: Protected
- **Request Body**:
  ```json
  {
    "additional_context": "Provider confirmed prior authorization was obtained on 2026-09-01 ref AUTH9871"
  }
  ```
- **Service Workflow**:
  - Fetches denial, claim, patient, provider, and payer context.
  - Calls `draft_appeal_letter()` using OpenRouter clinical model.
  - Logs execution to `agent_runs` table with confidence and HITL flag.
  - Updates denial: `appeal_status = "drafted"`, `appeal_drafted_by_ai = True`.
- **Response (200 OK)**:
  ```json
  {
    "appeal_letter": "APPEAL LETTER - CLAIM 101\n\nDear Appeals Department...",
    "confidence": 0.85,
    "hitl_required": false
  }
  ```

---

## 5. Payments API (`/payments`)

Defined in: [backend/app/routers/payments.py](file:///b:/Baskar/nova%20arc/backend/app/routers/payments.py)

### 5.1 Payments Statistics Summary
- **Endpoint**: `GET /payments/stats/summary`
- **Auth**: Protected
- **Response (200 OK)**:
  ```json
  {
    "total_payments": 24,
    "total_amount": 54200.00,
    "by_payer": [
      { "payer_id": 1, "count": 10, "total_amount": 25000.00 }
    ]
  }
  ```

### 5.2 List Payments
- **Endpoint**: `GET /payments`
- **Auth**: Protected
- **Query Parameters**: `claim_id`, `payer_id`, `date_from`, `date_to`, `skip`, `limit`
- **Auto-Sync Side Effect**: Automatically scans for claims marked as `paid` that have no Payment record and generates one.
- **Response (200 OK)**: Array of Payment objects with nested `claim` and `payer`.

### 5.3 Post / Create Payment
- **Endpoint**: `POST /payments`
- **Auth**: Protected
- **Request Body**:
  ```json
  {
    "claim_id": 1,
    "amount": 250.00,
    "posted_date": "2026-09-16",
    "remittance_ref": "ERA-MANUAL-101",
    "payer_id": 1
  }
  ```
- **Side Effects**:
  - Adds `amount` to `claim.paid_amount`.
  - If `claim.paid_amount >= claim.charge_amount`, automatically sets `claim.status = "paid"`.
- **Response (201 Created)**: Created Payment object.

### 5.4 Get Payment Detail
- **Endpoint**: `GET /payments/{payment_id}`
- **Auth**: Protected
- **Response (200 OK)**: Payment object.

### 5.5 Update Payment
- **Endpoint**: `PATCH /payments/{payment_id}`
- **Auth**: Protected
- **Response (200 OK)**: Updated Payment object.

---

## 6. Dashboard & Analytics API (`/dashboard`)

Defined in: [backend/app/routers/dashboard.py](file:///b:/Baskar/nova%20arc/backend/app/routers/dashboard.py)

### 6.1 Revenue Health
- **Endpoint**: `GET /dashboard/revenue-health`
- **Response (200 OK)**:
  ```json
  {
    "ar_outstanding": 42500.00,
    "collected": 85000.00,
    "collection_rate": 66.7,
    "aging_buckets": {
      "0-30 days": 15000.0,
      "30-60 days": 12500.0,
      "60-90 days": 8000.0,
      "90-120 days": 7000.0
    }
  }
  ```

### 6.2 AR Health (Aging by Payer & Specialty)
- **Endpoint**: `GET /dashboard/ar-health`
- **Response (200 OK)**:
  ```json
  {
    "by_payer": [
      { "payer_id": 1, "payer_name": "Aetna Commercial", "ar_outstanding": 15000.0, "claim_count": 8, "avg_days_outstanding": 42.5 }
    ],
    "by_specialty": [
      { "specialty": "Cardiology", "ar_outstanding": 22000.0, "claim_count": 12, "avg_days_outstanding": 38.0 }
    ]
  }
  ```

### 6.3 Payer Performance
- **Endpoint**: `GET /dashboard/payer-performance`
- **Guaranteed Output**: Includes safe fallback logic so `collection_rate` and `denial_rate` are always valid floats (never `NaN` or `undefined`).
- **Response (200 OK)**:
  ```json
  [
    {
      "payer_id": 1,
      "payer_name": "Aetna Commercial",
      "total_charged": 50000.00,
      "total_paid": 45000.00,
      "collection_rate": 90.0,
      "avg_days_to_pay": 18.4,
      "denial_rate": 8.5
    }
  ]
  ```

### 6.4 Denial Intelligence
- **Endpoint**: `GET /dashboard/denial-intelligence`
- **Response (200 OK)**:
  ```json
  {
    "top_codes": [{ "denial_code": "CO-16", "count": 14, "total_denied": 18200.0, "avg_denied": 1300.0 }],
    "monthly_trend": [{ "month": "2026-08", "count": 12, "total_denied": 15000.0 }],
    "by_root_cause": [{ "root_cause": "Missing Information / Billing Error", "count": 10, "total_denied": 12000.0 }]
  }
  ```

---

## 7. Work Queues API (`/work-queues`)

Defined in: [backend/app/routers/work_queues.py](file:///b:/Baskar/nova%20arc/backend/app/routers/work_queues.py)

### 7.1 List Work Queues
- **Endpoint**: `GET /work-queues`
- **Response (200 OK)**:
  ```json
  [
    {
      "queue_id": 1,
      "name": "High Risk - Denial Prevention",
      "priority": "high",
      "claim_count": 4,
      "total_value": 8500.00
    }
  ]
  ```

### 7.2 Get Queue Claims
- **Endpoint**: `GET /work-queues/{queue_id}/claims`
- **Response (200 OK)**: Array of unresolved Claim objects assigned to the queue.

### 7.3 Resolve Claim in Queue
- **Endpoint**: `POST /work-queues/{queue_id}/claims/{claim_id}/resolve`
- **Side Effects**: Sets `resolved_at = datetime.utcnow()` on the `claim_queue_assignments` record.
- **Response (200 OK)**:
  ```json
  { "message": "Claim resolved in queue", "claim_id": 101, "queue_id": 1 }
  ```

---

## 8. AI Agents API (`/agents`)

Defined in: [backend/app/routers/agents.py](file:///b:/Baskar/nova%20arc/backend/app/routers/agents.py)

### 8.1 Medical Coding Assistance
- **Endpoint**: `POST /agents/coding-assist`
- **Request Body**:
  ```json
  {
    "clinical_notes": "Patient presents with uncontrolled hypertension...",
    "patient_context": { "mrn": "MRN1001", "claim_id": 101 }
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "icd10_suggestions": [{ "code": "I10", "description": "Essential hypertension", "confidence": 0.95, "rationale": "..." }],
    "cpt_suggestions": [{ "code": "99214", "description": "Office visit 30-39 min", "confidence": 0.91, "modifiers": ["25"], "rationale": "..." }],
    "confidence": 0.92,
    "hitl_required": false
  }
  ```

### 8.2 Denial Risk Prediction
- **Endpoint**: `POST /agents/denial-predict`
- **Request Body**:
  ```json
  { "claim_id": 101 }
  ```
- **Response (200 OK)**:
  ```json
  {
    "denial_probability": 0.78,
    "shap_explanation": { "payer_id": 0.22, "charge_amount": 0.15, "has_prior_denial": 0.35 },
    "risk_factors": ["Prior denial on this claim", "High charge amount (>$10,000)"],
    "hitl_required": true
  }
  ```

### 8.3 Human-in-the-Loop Review
- **Endpoint**: `POST /agents/review`
- **Request Body**:
  ```json
  {
    "run_id": 45,
    "decision": "approved",
    "edited_output": null,
    "reviewer_notes": "Verified medical necessity and clinical notes"
  }
  ```
- **Decisions**: `approved`, `rejected`, `edited`
- **Response (200 OK)**: `{ "message": "Review submitted", "run_id": 45, "decision": "approved" }`

### 8.4 Pending Reviews
- **Endpoint**: `GET /agents/pending-reviews?agent_type=coding_assist`
- **Response (200 OK)**: Array of pending `AgentRun` records requiring human oversight.

### 8.5 Agent Runs Audit Trail
- **Endpoint**: `GET /agents/runs/{claim_id}`
- **Response (200 OK)**: Complete historical record of all agent executions for a specific claim.

---

## 9. Conversational AI Assistant API (`/assistant`)

Defined in: [backend/app/routers/assistant.py](file:///b:/Baskar/nova%20arc/backend/app/routers/assistant.py)

### 9.1 Query Assistant
- **Endpoint**: `POST /assistant/query`
- **Request Body**:
  ```json
  { "query": "What is our AR over 90 days?" }
  ```
- **Supported Intents**:
  1. `ar_over_90`: Accounts receivable aging past 90 days.
  2. `denial_rate`: Percentage of denied claims vs total claims.
  3. `top_denial_codes`: Most frequent CARC denial codes and denied dollars.
  4. `payer_comparison`: Head-to-head metrics on payer performance.
  5. `collection_rate`: Total collected dollars divided by total charges.
  6. `total_ar`: Total outstanding balance across active claims.
  7. `claims_by_status`: Volume and value breakdown by claim status.
  8. `nl_to_sql`: Fallback to LLM SQL generation for ad-hoc Postgres queries.
- **Response (200 OK)**:
  ```json
  {
    "intent": "ar_over_90",
    "response": "AR over 90 days: $14,250.00 (6 claims, 33.5% of total AR)",
    "data": { "ar_over_90": 14250.0, "claim_count": 6, "percentage_of_total": 33.5, "total_ar": 42500.0 },
    "follow_up_suggestions": [
      "Show me AR aging by payer",
      "Which claims are over 90 days?",
      "What's our total AR?"
    ]
  }
  ```

---

## 10. System & Health API (`/health`)

- **Endpoint**: `GET /health`
- **Auth**: Public
- **Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "service": "novaarc-rcm",
    "version": "1.0.2"
  }
  ```

---

## 11. Backend Services Function Catalogue

### `app.services.coding_agent`
- `suggest_codes(clinical_notes: str, patient_context: dict = None) -> dict`: Sends clinical documentation to Ling 3.0 Flash Santé, extracts ICD-10 and CPT codes, parses response JSON safely, and falls back to deterministic rules if offline.
- `generate_fallback_codes(clinical_notes: str) -> dict`: Rule-based deterministic coding engine that identifies hypertension (`I10`), diabetes (`E11.9`), chest pain (`R07.9`), bronchitis (`J40`), back pain (`M54.5`), EKG (`93000`), and E/M visits (`99213`, `99214`, `99215`).
- `call_openrouter(messages: list[dict], temperature: float = 0.3) -> dict`: Manages HTTP client calls to OpenRouter with automatic model fallback from Ling 3.0 to Nemotron.

### `app.services.denial_predictor`
- `DenialPredictor`: Random Forest / XGBoost model wrapper.
- `extract_features(claim, payer_denial_rate, provider_denial_rate, has_prior_denial) -> np.ndarray`: Converts claim into a 10-dimensional feature vector.
- `predict(features) -> tuple[float, dict]`: Computes denial probability and SHAP feature importance scores.
- `get_denial_prediction(db: AsyncSession, claim_id: int) -> tuple[Decimal, dict, list[str], bool]`: High-level entry point pulling live database aggregates and returning probability, explanations, and risk factors.

### `app.services.appeal_agent`
- `draft_appeal_letter(denial: Denial, additional_context: str = None) -> tuple[str, Decimal, bool]`: Builds rich clinical context from claim, patient, provider, and payer records, prompts the LLM to generate an appeal letter citing LCD/NCD guidelines, and returns the letter, confidence, and HITL requirement.
- `generate_fallback_appeal(denial, claim, patient, provider, payer) -> str`: Produces a formal, compliant appeal letter template when external AI services are unavailable.

### `app.services.edi_parser`
- `generate_837_claim(claim: Claim) -> str`: Generates ANSI ASC X12 837P professional claim EDI segments (`ISA`, `GS`, `ST`, `BHT`, `NM1`, `CLM`, `SV1`, `HI`, `SE`, `GE`, `IEA`).
- `parse_835_remittance(edi_content: str) -> dict`: Parses ANSI ASC X12 835 Remittance files extracting `CLP` payment segments and `CAS` adjustment reason codes.

### `app.services.work_queue`
- `assign_claim_to_queue(db, claim_id) -> ClaimQueueAssignment`: Triage engine evaluating claim age, denial status, and denial prediction risk, routing the claim to the appropriate work queue.
- `determine_queue(db, claim) -> WorkQueue | None`: Evaluates priority rules across the 7 queue types.
- `reassign_claim(db, claim_id, queue_id) -> ClaimQueueAssignment`: Closes current assignment and creates a new queue assignment.

### `app.services.agent_logger`
- `log_agent_run(db, claim_id, agent_type, input_payload, output_payload, confidence, hitl_required) -> AgentRun`: Persists execution audit log.
- `review_agent_run(db, run_id, decision, edited_output, reviewer, reviewer_notes) -> AgentRun`: Updates review decision.
- `get_pending_reviews(db, agent_type = None) -> list[AgentRun]`: Queries all runs waiting for HITL approval.

---

## 12. Frontend `ApiClient` Reference (`frontend/src/services/api.ts`)

Exported instance: `import { api } from '../services/api';`

| Method | Parameters | HTTP Request | Returns |
|---|---|---|---|
| `login` | `email, password` | `POST /auth/login` | `{ access_token, token_type }` |
| `register` | `data: { name, email, password, role }` | `POST /auth/register` | `User` |
| `getMe` | none | `GET /auth/me` | `User` |
| `getRoles` | none | `GET /auth/roles` | `string[]` |
| `getUsers` | none | `GET /auth/users` | `User[]` |
| `listClaims` | `params?: ClaimFilterParams` | `GET /claims` | `Claim[]` |
| `getReferenceData` | none | `GET /claims/reference-data` | `{ patients, providers, payers }` |
| `getClaim` | `claimId: number` | `GET /claims/{id}` | `ClaimDetail` |
| `createClaim` | `data: ClaimCreateInput` | `POST /claims` | `Claim` |
| `extractClaimDocument` | `file: File, patientId?: string` | `POST /claims/extract-document` | `DocumentExtractionResult` |
| `updateClaim` | `claimId: number, data: Partial<Claim>` | `PATCH /claims/{id}` | `Claim` |
| `submitClaim` | `claimId: number` | `POST /claims/{id}/submit` | `Claim` |
| `getClaimsSummary` | none | `GET /claims/stats/summary` | `ClaimsSummary` |
| `getTopDenialCodes` | `limit = 10` | `GET /denials/top-codes` | `DenialTopCode[]` |
| `getDenial` | `denialId: number` | `GET /denials/{id}` | `Denial` |
| `updateDenial` | `denialId: number, data: Partial<Denial>`| `PATCH /denials/{id}` | `Denial` |
| `draftAppeal` | `denialId: number, context?: string` | `POST /denials/{id}/draft-appeal` | `AppealDraftResponse` |
| `listDenials` | `params?: DenialFilterParams` | `GET /denials` | `Denial[]` |
| `listPayments` | `params?: PaymentFilterParams` | `GET /payments` | `Payment[]` |
| `createPayment` | `data: PaymentCreateInput` | `POST /payments` | `Payment` |
| `getPayment` | `paymentId: number` | `GET /payments/{id}` | `Payment` |
| `updatePayment` | `paymentId: number, data: Partial<Payment>` | `PATCH /payments/{id}` | `Payment` |
| `getPaymentsSummary`| none | `GET /payments/stats/summary` | `PaymentsSummary` |
| `getRevenueHealth` | none | `GET /dashboard/revenue-health` | `DashboardRevenueHealth` |
| `getARHealth` | none | `GET /dashboard/ar-health` | `DashboardARHealth` |
| `getPayerPerformance`| none | `GET /dashboard/payer-performance`| `DashboardPayerPerformance[]` |
| `getDenialIntelligence`| none | `GET /dashboard/denial-intelligence`| `DenialIntelligence` |
| `listWorkQueues` | none | `GET /work-queues` | `WorkQueueSummary[]` |
| `createWorkQueue` | `data: { name, priority, rule_definition? }` | `POST /work-queues` | `WorkQueue` |
| `getWorkQueue` | `queueId: number` | `GET /work-queues/{id}` | `WorkQueue` |
| `updateWorkQueue` | `queueId: number, data: Partial<WorkQueue>` | `PATCH /work-queues/{id}` | `WorkQueue` |
| `getQueueClaims` | `queueId: number` | `GET /work-queues/{id}/claims` | `Claim[]` |
| `resolveClaimInQueue`| `queueId: number, claimId: number` | `POST /work-queues/{qid}/claims/{cid}/resolve` | `{ message, claim_id, queue_id }` |
| `codingAssist` | `clinicalNotes: string, context?: object` | `POST /agents/coding-assist` | `CodingAssistResponse` |
| `denialPredict` | `claimId: number` | `POST /agents/denial-predict` | `DenialPredictResponse` |
| `reviewAgentRun` | `runId, decision, editedOutput?, notes?` | `POST /agents/review` | `{ message, run_id, decision }` |
| `getPendingReviews` | `agentType?: string` | `GET /agents/pending-reviews` | `PendingReview[]` |
| `getAgentRunsForClaim`| `claimId: number` | `GET /agents/runs/{id}` | `AgentRun[]` |
| `assistantQuery` | `query: string, context?: object` | `POST /assistant/query` | `AssistantQueryResponse` |
