import sys
import io
import requests
import json
import time
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://novaarc-backend.onrender.com"
FRONTEND_NETLIFY = "https://novaarc-rcm-app.netlify.app"
FRONTEND_GH_PAGES = "https://krishna-caare.github.io/novaarc-rcm/"

def create_sample_pdf_bytes():
    """Generate a clean clinical encounter note PDF in memory"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "CLINICAL ENCOUNTER NOTE - AMBULATORY OUTPATIENT")
    c.setFont("Helvetica", 10)
    c.drawString(50, 730, "Patient: John Doe | MRN: MRN126225 | DOB: 1968-04-12 | DOS: 2026-09-16")
    c.drawString(50, 715, "Provider: Dr. Amanda Davis, MD | Specialty: Cardiology")
    c.drawString(50, 690, "CHIEF COMPLAINT: Follow-up hypertension and type 2 diabetes mellitus management.")
    c.drawString(50, 675, "HISTORY OF PRESENT ILLNESS:")
    c.drawString(50, 660, "Patient is a 58-year-old male presenting for follow-up of essential hypertension and type 2 diabetes.")
    c.drawString(50, 645, "Blood pressure today is elevated at 148/92 mmHg. Recent HbA1c is 7.8% indicating suboptimal control.")
    c.drawString(50, 630, "Reports mild exertional dyspnea without active chest pain.")
    c.drawString(50, 605, "PHYSICAL EXAMINATION & ASSESSMENT:")
    c.drawString(50, 590, "1. Essential (primary) hypertension - Lisinopril increased to 20mg daily.")
    c.drawString(50, 575, "2. Type 2 diabetes mellitus without acute complications - Metformin continued, lifestyle counseling given.")
    c.drawString(50, 560, "3. Outpatient EKG ordered to evaluate rhythm.")
    c.drawString(50, 535, "PLAN: Moderate complexity medical decision making (CPT 99214). Follow up in 3 months.")
    c.save()
    buf.seek(0)
    return buf.getvalue()

def run():
    print("=" * 75)
    print("NovaArc RCM - Comprehensive Demo & System Verification Suite")
    print(f"Backend API:     {BASE_URL}")
    print(f"Netlify App:     {FRONTEND_NETLIFY}")
    print(f"GitHub Pages:    {FRONTEND_GH_PAGES}")
    print("=" * 75)

    passed = 0
    failed = 0

    # 1. Health Checks
    print("\n[STEP 1] Testing Backend & Production Frontend Live Availability...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=15)
        assert r.status_code == 200 and r.json().get("status") == "healthy"
        print("  ✓ Backend API /health: 200 OK (healthy)")
        passed += 1
    except Exception as e:
        print(f"  ✗ Backend health failed: {e}")
        failed += 1

    try:
        r_net = requests.get(FRONTEND_NETLIFY, timeout=15)
        assert r_net.status_code == 200
        print("  ✓ Netlify Production Site: 200 OK")
        passed += 1
    except Exception as e:
        print(f"  ✗ Netlify site check failed: {e}")
        failed += 1

    try:
        r_gh = requests.get(FRONTEND_GH_PAGES, timeout=15)
        assert r_gh.status_code == 200
        print("  ✓ GitHub Pages Production Site: 200 OK")
        passed += 1
    except Exception as e:
        print(f"  ✗ GitHub Pages check failed: {e}")
        failed += 1

    # 2. Authentication
    print("\n[STEP 2] Testing Authentication for Demo Users...")
    auth_res = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "ops_manager@novaarc.local", "password": "password123"},
        timeout=15
    )
    assert auth_res.status_code == 200, f"Login failed: {auth_res.text}"
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  ✓ Logged in successfully as ops_manager@novaarc.local (Bearer JWT retrieved)")
    passed += 1

    # 3. Dashboard Analytics & Payer Performance Verification
    print("\n[STEP 3] Testing Dashboard Endpoints & Payer Performance Calculation...")
    try:
        payers_res = requests.get(f"{BASE_URL}/dashboard/payer-performance", headers=headers, timeout=15)
        assert payers_res.status_code == 200
        payers = payers_res.json()
        assert len(payers) > 0, "No payers returned"
        print(f"  ✓ Payer Performance returned {len(payers)} payers:")
        for p in payers[:3]:
            assert p.get("collection_rate") is not None, "collection_rate is None!"
            print(f"    • {p['payer_name']}: Collection Rate: {p['collection_rate']}%, Denial Rate: {p['denial_rate']}%, Avg Days: {p['avg_days_to_pay']}")
        passed += 1
    except Exception as e:
        print(f"  ✗ Payer Performance failed: {e}")
        failed += 1

    # 4. PDF Document Scraping & AI Coding Ingestion (/claims/extract-document)
    print("\n[STEP 4] Testing PDF Upload, Text Extraction & AI Auto-Coding...")
    try:
        pdf_bytes = create_sample_pdf_bytes()
        files = {"file": ("clinical_encounter_test.pdf", pdf_bytes, "application/pdf")}
        data = {"patient_id": "1"}
        extract_res = requests.post(f"{BASE_URL}/claims/extract-document", files=files, data=data, headers=headers, timeout=60)
        assert extract_res.status_code == 200, f"Status {extract_res.status_code}: {extract_res.text}"
        ext = extract_res.json()
        print(f"  ✓ PDF Scraped successfully: {ext['word_count']} words extracted from {ext['filename']}")
        print(f"  ✓ AI Suggested ICD-10: {ext['suggested_icd10']}")
        print(f"  ✓ AI Suggested CPT:    {ext['suggested_cpt']}")
        print(f"  ✓ AI Estimated Charge: ${ext['suggested_charge']}")
        assert "I10" in ext['suggested_icd10'], "Expected I10 for hypertension"
        assert len(ext.get('icd10_suggestions', [])) > 0, "No ICD-10 suggestions list"
        passed += 1
    except Exception as e:
        print(f"  ✗ PDF extract failed: {e}")
        failed += 1

    # 5. End-to-End Claim Lifecycle & Status Transitions
    print("\n[STEP 5] Testing End-to-End Claim Lifecycle & Multi-Entity Sync...")
    new_claim_id = None
    try:
        # A: Create Claim
        claim_payload = {
            "patient_id": 1,
            "provider_id": 1,
            "payer_id": 1,
            "date_of_service": "2026-09-16",
            "charge_amount": 250.00,
            "cpt_codes": ["99214"],
            "icd10_codes": ["I10", "E11.9"],
            "modifiers": ["25"]
        }
        create_res = requests.post(f"{BASE_URL}/claims", json=claim_payload, headers=headers, timeout=15)
        assert create_res.status_code == 201, f"Create failed: {create_res.text}"
        claim_data = create_res.json()
        new_claim_id = claim_data["claim_id"]
        assert claim_data["status"] == "created"
        print(f"  ✓ Step A: Claim CLM-{new_claim_id} created with status 'created'")
        passed += 1

        # B: Submit Claim (EDI 837)
        submit_res = requests.post(f"{BASE_URL}/claims/{new_claim_id}/submit", headers=headers, timeout=15)
        assert submit_res.status_code == 200
        assert submit_res.json()["status"] == "submitted"
        assert submit_res.json().get("edi_837_ref") is not None
        print(f"  ✓ Step B: Claim CLM-{new_claim_id} submitted (EDI ref: {submit_res.json()['edi_837_ref']})")
        passed += 1

        # C: Move Claim to Denied -> Auto-create Denial Record
        deny_res = requests.patch(f"{BASE_URL}/claims/{new_claim_id}", json={"status": "denied"}, headers=headers, timeout=15)
        assert deny_res.status_code == 200, f"Deny failed: {deny_res.text}"
        assert deny_res.json()["status"] == "denied"
        print(f"  ✓ Step C: Claim CLM-{new_claim_id} status updated to 'denied'")

        # Verify Denial record auto-created
        denials_res = requests.get(f"{BASE_URL}/denials?claim_id={new_claim_id}", headers=headers, timeout=15)
        denials = [d for d in denials_res.json() if d.get("claim_id") == new_claim_id]
        assert len(denials) > 0, "No denial record auto-created for denied claim!"
        denial_id = denials[0]["denial_id"]
        print(f"  ✓ Step C Sync: Denial record #{denial_id} auto-created for CLM-{new_claim_id} (Code: {denials[0]['denial_code']})")
        passed += 1

        # D: Draft AI Appeal Letter
        appeal_res = requests.post(
            f"{BASE_URL}/denials/{denial_id}/draft-appeal",
            json={"additional_context": "Clinical encounter notes attached confirming medical necessity for outpatient care."},
            headers=headers,
            timeout=60
        )
        assert appeal_res.status_code == 200
        appeal_data = appeal_res.json()
        assert appeal_data.get("appeal_letter"), "No appeal letter generated"
        print(f"  ✓ Step D: AI Appeal Letter drafted (Confidence: {appeal_data.get('confidence')})")
        passed += 1

        # E: Submit Appeal -> Claim moves to 'appealed'
        sub_app_res = requests.patch(f"{BASE_URL}/denials/{denial_id}", json={"appeal_status": "submitted"}, headers=headers, timeout=15)
        assert sub_app_res.status_code == 200
        chk_claim = requests.get(f"{BASE_URL}/claims/{new_claim_id}", headers=headers, timeout=15).json()
        assert chk_claim["status"] == "appealed", f"Expected 'appealed', got {chk_claim['status']}"
        print(f"  ✓ Step E: Appeal submitted -> Claim CLM-{new_claim_id} status automatically synchronized to 'appealed'")
        passed += 1

        # F: Overturn / Win Appeal -> Claim moves to 'paid' & Payment record auto-created
        win_app_res = requests.patch(f"{BASE_URL}/denials/{denial_id}", json={"appeal_status": "won"}, headers=headers, timeout=15)
        assert win_app_res.status_code == 200
        chk_claim_won = requests.get(f"{BASE_URL}/claims/{new_claim_id}", headers=headers, timeout=15).json()
        assert chk_claim_won["status"] == "paid", f"Expected 'paid', got {chk_claim_won['status']}"
        assert float(chk_claim_won["paid_amount"]) == 250.00, f"Paid amount mismatch: {chk_claim_won['paid_amount']}"
        print(f"  ✓ Step F: Appeal marked 'won' -> Claim CLM-{new_claim_id} automatically switched to 'paid' ($250.00)")

        # Verify Payment record auto-created
        payments_res = requests.get(f"{BASE_URL}/payments?claim_id={new_claim_id}", headers=headers, timeout=15)
        payments = [p for p in payments_res.json() if p.get("claim_id") == new_claim_id]
        assert len(payments) > 0, "No payment record auto-created for paid claim!"
        print(f"  ✓ Step F Sync: Payment #{payments[0]['payment_id']} automatically logged for ${payments[0].get('amount')}")
        passed += 1

    except Exception as e:
        import traceback
        print(f"  ✗ Claim lifecycle failed: {e}")
        traceback.print_exc()
        failed += 1

    # 6. Work Queues Resolution
    print("\n[STEP 6] Testing Work Queues & Queue Claim Resolution...")
    try:
        queues_res = requests.get(f"{BASE_URL}/work-queues", headers=headers, timeout=15)
        assert queues_res.status_code == 200
        queues = queues_res.json()
        assert len(queues) == 7, f"Expected 7 work queues, got {len(queues)}"
        print(f"  ✓ All 7 Work Queues active: {[q['name'] for q in queues]}")
        
        # Test resolving claim in queue 1 if any claims exist
        q1_claims = requests.get(f"{BASE_URL}/work-queues/1/claims", headers=headers, timeout=15).json()
        if len(q1_claims) > 0:
            target_claim_id = q1_claims[0]["claim_id"]
            res_claim = requests.post(f"{BASE_URL}/work-queues/1/claims/{target_claim_id}/resolve", headers=headers, timeout=15)
            assert res_claim.status_code == 200
            print(f"  ✓ Successfully resolved claim CLM-{target_claim_id} in Queue #1")
        passed += 1
    except Exception as e:
        import traceback
        print(f"  ✗ Work Queues check failed: {e}")
        traceback.print_exc()
        failed += 1

    # 7. AI Agents Full Test
    print("\n[STEP 7] Testing All Specialized AI Agents...")
    # Denial Predictor AI (takes claim_id)
    try:
        target_claim_id = new_claim_id or 1
        pred_payload = {"claim_id": target_claim_id}
        pred_res = requests.post(f"{BASE_URL}/agents/denial-predict", json=pred_payload, headers=headers, timeout=30)
        assert pred_res.status_code == 200, f"Status {pred_res.status_code}: {pred_res.text}"
        pred_data = pred_res.json()
        print(f"  ✓ Denial Predictor AI: Denial Probability: {pred_data.get('denial_probability')}, Risk Factors: {pred_data.get('risk_factors')}")
        passed += 1
    except Exception as e:
        import traceback
        print(f"  ✗ Denial Predictor failed: {e}")
        traceback.print_exc()
        failed += 1

    # NL Analytics Query Assistant
    try:
        query_payload = {"query": "What is our current collection rate and top denial reasons?"}
        query_res = requests.post(f"{BASE_URL}/assistant/query", json=query_payload, headers=headers, timeout=40)
        assert query_res.status_code == 200
        query_data = query_res.json()
        print(f"  ✓ NL-to-SQL Analytics Assistant answered: \"{query_data.get('response', '')[:100]}...\"")
        passed += 1
    except Exception as e:
        print(f"  ✗ Analytics Assistant failed: {e}")
        failed += 1

    # HITL Pending Reviews
    try:
        reviews_res = requests.get(f"{BASE_URL}/agents/pending-reviews", headers=headers, timeout=15)
        assert reviews_res.status_code == 200
        print(f"  ✓ HITL Review Agent: {len(reviews_res.json())} pending agent runs queued for auditor review")
        passed += 1
    except Exception as e:
        print(f"  ✗ Pending reviews failed: {e}")
        failed += 1

    print("\n" + "=" * 75)
    print(f"SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 75)
    if failed == 0:
        print("🎉 ALL SYSTEMS, FLOWS, AI AGENTS, AND STATUS TRANSITIONS ARE 100% OPERATIONAL & DEMO READY!")
    return failed == 0

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
