# NovaArc RCM — Upcoming Enterprise Roadmap (4 Strategic Phases)

This document tracks the **4 strategic enterprise upgrades** scheduled for future implementation to transition NovaArc RCM into a commercial-grade autonomous revenue cycle platform.

---

## 🗺️ Execution Roadmap Summary

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Neo4j AuraDB Migration (Graph Database & Cypher Queries)      │
│   └─ Replace in-memory dictionary with cloud graph database & Cypher   │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 2: ML Denial Predictor (XGBoost Real-Time Risk Scoring)          │
│   └─ Replace static IF/THEN rules with trained ML model & risk bar     │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Stedi EDI Gateway (Live 837P & 835 Remittance Webhooks)       │
│   └─ Connect to real clearinghouse API for live claims transmission    │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 4: SMART on FHIR Integration (Direct EHR Intake)                 │
│   └─ One-click encounter & diagnosis import from Epic / Cerner         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Neo4j AuraDB Migration

### The Problem
The current Knowledge Graph engine runs as an in-memory Python data structure (`graph_engine.py`) holding 354 nodes and 354 edges. While fast, an in-memory dictionary cannot easily support:
- Multi-hop semantic traversal (e.g. 3-hop ancestry queries)
- Dynamic graph versioning and payer policy updates across 50,000+ codes without server restarts
- Natural language to Cypher translation via LLMs

### The Solution
Migrate the Denial Knowledge Graph to **Neo4j AuraDB** (cloud graph database) and rewrite the retrieval layer to execute Cypher queries.

### Implementation Blueprint
1. **Neo4j AuraDB Setup**: Provision a cloud instance on Neo4j Aura.
2. **Cypher Batch Importer (`export_to_neo4j_cypher.py`)**:
   - Ingest the 354 nodes into labeled graph entities: `:Category`, `:DenialCode`, `:Scenario`, `:InvestigationStep`, `:PayerQuestion`, `:FormRequirement`, `:ActionPlan`.
   - Build typed relationships: `[:INCLUDES]`, `[:MANIFESTS_AS]`, `[:REQUIRES_CHECK]`, `[:CALL_SCRIPT]`, `[:REQUIRES_FORM]`, `[:RESOLVED_BY]`, `[:RELATED_TO]`.
3. **Backend Service (`neo4j_service.py`)**:
   - Connect via the official `neo4j` Python driver.
   - Example query for scenario and playbook extraction:
     ```cypher
     MATCH (d:DenialCode {code: $code})-[:MANIFESTS_AS]->(s:Scenario)
     OPTIONAL MATCH (s)-[:REQUIRES_CHECK]->(i:InvestigationStep)
     OPTIONAL MATCH (s)-[:CALL_SCRIPT]->(c:PayerQuestion)
     OPTIONAL MATCH (s)-[:REQUIRES_FORM]->(f:FormRequirement)
     OPTIONAL MATCH (s)-[:RESOLVED_BY]->(a:ActionPlan)
     RETURN s, collect(DISTINCT i) as checks, collect(DISTINCT c) as questions,
            collect(DISTINCT f) as forms, collect(DISTINCT a) as actions
     ```
4. **LangChain GraphCypherQAChain**:
   - Allow natural language queries ("What is the procedure for an Aetna CO-16 denial on a surgical claim?") to be translated directly into Cypher queries executed against Neo4j.

**🛠️ Tech Stack**: Neo4j AuraDB (Free Tier), `neo4j` Python driver, LangChain, Cypher query language.

---

## Phase 2: ML Denial Predictor (XGBoost)

### The Problem
Rule-based pre-scrubbers catch obvious syntax errors (missing NPI, empty diagnosis), but fail to detect nuanced, multi-variable payer behavior patterns (e.g., *"Aetna denies CPT 99214 with Modifier 25 80% of the time on outpatient claims over $300"*).

### The Solution
Train an **XGBoost Classification Model** on historical claim features and integrate a real-time **Denial Probability Risk Meter** into the claim creation modal.

### Implementation Blueprint
1. **Dataset Generation / Ingestion (`train_xgboost_predictor.py`)**:
   - 10,000+ historical claims with features:
     - `payer_id`
     - `provider_specialty`
     - `charge_amount`
     - `num_cpt_codes` & CPT ranges (E/M vs Surgery vs Radiology vs Lab)
     - `has_modifier_25`, `has_modifier_59`, `modifiers_list`
     - `day_of_week`
     - `target`: `is_denied` (1 or 0)
2. **Model Training**:
   - Train an `xgboost.XGBClassifier` with cross-validation and feature importance extraction (SHAP values).
   - Export model artifact to `backend/models/xgboost_denial_predictor.json`.
3. **API Endpoint (`POST /claims/predict-denial`)**:
   - Accepts claim form parameters before submission.
   - Returns:
     - `denial_probability`: e.g. `0.84` (84%)
     - `risk_level`: `"HIGH" | "MEDIUM" | "LOW"`
     - `top_risk_factors`: e.g. `["Missing Modifier 25 on separate E/M procedure", "High denial frequency for Aetna on surgical line"]`
     - `suggested_fix`: e.g. `"Append Modifier 25 to Box 24D"`
4. **Frontend UI Enhancement (`ClaimsPage.tsx`)**:
   - Live **AI Denial Risk Meter** in the New Claim Modal.
   - Progress bar with green/amber/red indicators.
   - One-click **"Apply Recommended Fix"** button that updates claim fields before electronic submission.

**🛠️ Tech Stack**: Python, Pandas, Scikit-Learn, XGBoost, FastAPI, React.

---

## Phase 3: Stedi EDI Gateway & Webhooks

### The Problem
The current system simulates the clearinghouse step via internal X12 837P text generation and simulated adjudication clicks. Real-world hospitals require actual electronic connections to payers.

### The Solution
Integrate a modern, developer-friendly clearinghouse API gateway such as **Stedi** or **Availity**.

### Implementation Blueprint
1. **Stedi Gateway Integration**:
   - Instead of manual X12 parsing, send clean JSON payloads from FastAPI to Stedi's API.
   - Stedi converts JSON to HIPAA-compliant X12 837P format and routes to the target commercial/government payer.
2. **Real-time ERA 835 Webhook (`/webhooks/era-835`)**:
   - Set up an incoming webhook receiver endpoint in FastAPI.
   - When a payer processes or denies a claim, Stedi converts the raw 835 EDI remit into structured JSON and hits the webhook.
3. **Automated GraphRAG Trigger**:
   - The webhook parses the CARC code (e.g. `CO-16`, `CO-197`) and remark codes (RARC).
   - Automatically initializes the GraphRAG playbook and queues the denial in the AR worklist with pre-filled appeal documentation.

**🛠️ Tech Stack**: Stedi API Gateway / Availity API, FastAPI Webhooks, X12 837P / 835 standards.

---

## Phase 4: SMART on FHIR Integration (Direct EHR Intake)

### The Problem
Manual data entry of patient MRNs, CPT codes, and ICD-10 diagnosis codes is slow and prone to typographical errors, which are a major root cause of front-end billing denials.

### The Solution
Implement the **SMART on FHIR** global healthcare standard to enable a one-click **"Import Encounter from EHR"** button.

### Implementation Blueprint
1. **EHR Sandbox Access**:
   - Register for Epic Showroom (formerly App Orchard) or Cerner Code developer sandbox.
2. **SMART on FHIR OAuth2 Authentication**:
   - Implement the OAuth2 launch flow allowing providers to authenticate against their hospital EHR.
3. **FHIR REST API Endpoints**:
   - `GET /Patient/{id}` $\rightarrow$ Auto-populates patient demographics, MRN, and insurance policy ID.
   - `GET /Encounter/{id}` $\rightarrow$ Auto-fills date of service and place of service (POS).
   - `GET /Condition?patient={id}` $\rightarrow$ Ingests ICD-10 diagnosis codes.
   - `GET /Procedure?patient={id}` $\rightarrow$ Ingests CPT procedure codes.
4. **UI Integration**:
   - Add an **"Import Encounter from EHR"** button in `ClaimsPage.tsx` that pulls active patient charts directly into the claim form with zero manual typing.

**🛠️ Tech Stack**: `fhir-client` (TypeScript), `fhirpy` (Python), Epic / Cerner SMART-on-FHIR sandboxes.

---

## 📌 Status & Tracking

| Phase | Title | Complexity | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Neo4j AuraDB Migration | Moderate | High | 📋 Documented & Ready |
| **Phase 2** | ML Denial Predictor (XGBoost) | Moderate | High | 📋 Documented & Ready |
| **Phase 3** | Stedi EDI Gateway & Webhooks | High | Medium | 📋 Documented & Ready |
| **Phase 4** | SMART on FHIR Integration | High | Long-term | 📋 Documented & Ready |
