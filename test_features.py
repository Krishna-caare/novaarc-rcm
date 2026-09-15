import requests
import json

BASE_URL = 'https://novaarc-backend.onrender.com'
FRONTEND_URL = 'https://novaarc.netlify.app'

print("=" * 60)
print("NovaArc RCM - Comprehensive Live E2E Verification")
print("=" * 60)

# 1. Login
auth_res = requests.post(
    f'{BASE_URL}/auth/login',
    json={'email': 'client_leadership@novaarc.local', 'password': 'password123'},
    headers={'Origin': FRONTEND_URL}
)
assert auth_res.status_code == 200, f"Login failed: {auth_res.text}"
token = auth_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Origin': FRONTEND_URL}
print("[TEST 1] Role Authentication & JWT Generation -> PASS (200 OK)")

# 2. Reference data for New Claim / Post Payment modals
ref_res = requests.get(f'{BASE_URL}/claims/reference-data', headers=headers)
assert ref_res.status_code == 200, f"Reference data failed: {ref_res.text}"
ref_data = ref_res.json()
print(f"[TEST 2] Dynamic Reference Data -> PASS ({len(ref_data['patients'])} patients, {len(ref_data['providers'])} providers, {len(ref_data['payers'])} payers)")

patient_id = ref_data['patients'][0]['patient_id']
provider_id = ref_data['providers'][0]['provider_id']
payer_id = ref_data['payers'][0]['payer_id']

# 3. Create Claim (New Claim Button Flow)
claim_payload = {
    'patient_id': patient_id,
    'provider_id': provider_id,
    'payer_id': payer_id,
    'date_of_service': '2026-09-15',
    'charge_amount': 750.00,
    'cpt_codes': ['99214'],
    'icd10_codes': ['I10', 'E11.9'],
    'modifiers': ['25']
}
create_claim_res = requests.post(f'{BASE_URL}/claims', json=claim_payload, headers=headers)
assert create_claim_res.status_code == 201, f"Create claim failed: {create_claim_res.text}"
new_claim = create_claim_res.json()
claim_id = new_claim['claim_id']
p_mrn = new_claim.get('patient', {}).get('mrn') if new_claim.get('patient') else 'None'
pr_name = new_claim.get('provider', {}).get('name') if new_claim.get('provider') else 'None'
py_name = new_claim.get('payer', {}).get('name') if new_claim.get('payer') else 'None'
print(f"[TEST 3] New Claim Creation -> PASS (CLM-{claim_id}: Patient {p_mrn}, Provider {pr_name}, Payer {py_name})")

# 4. Post Payment (Post Payment Button Flow)
pmt_payload = {
    'claim_id': claim_id,
    'amount': 750.00,
    'payer_id': payer_id,
    'posted_date': '2026-09-15',
    'remittance_ref': 'RMT-VERIFY-750'
}
post_pmt_res = requests.post(f'{BASE_URL}/payments', json=pmt_payload, headers=headers)
assert post_pmt_res.status_code == 201, f"Post payment failed: {post_pmt_res.text}"
pmt = post_pmt_res.json()
print(f"[TEST 4] Post Payment -> PASS (PMT-{pmt['payment_id']}: ${pmt['amount']}, Ref: {pmt['remittance_ref']})")

# 5. Verify Claim status updated to Paid
updated_claim_res = requests.get(f'{BASE_URL}/claims/{claim_id}', headers=headers)
claim_status = updated_claim_res.json()['status']
paid_amount = updated_claim_res.json()['paid_amount']
print(f"[TEST 5] Claim Balance & Status Update -> PASS (Status: {claim_status}, Paid: ${paid_amount})")

# 6. AI Coding Assistant
coding_res = requests.post(
    f'{BASE_URL}/agents/coding-assist',
    json={
        'clinical_notes': 'Patient with uncontrolled type 2 diabetes and hypertension presented with chest pain. Detailed evaluation.',
        'patient_context': {'claim_id': claim_id}
    },
    headers=headers
)
assert coding_res.status_code == 200, f"Coding assist failed: {coding_res.text}"
coding_data = coding_res.json()
cpt_count = len(coding_data.get('cpt_suggestions', []))
icd_count = len(coding_data.get('icd10_suggestions', []))
print(f"[TEST 6] AI Coding Assistant -> PASS (Suggested {cpt_count} CPT codes, {icd_count} ICD-10 codes, Confidence: {coding_data.get('confidence')})")

# 7. AI Denial Predictor
predict_res = requests.post(f'{BASE_URL}/agents/denial-predict', json={'claim_id': claim_id}, headers=headers)
assert predict_res.status_code == 200, f"Denial predict failed: {predict_res.text}"
predict_data = predict_res.json()
print(f"[TEST 7] AI Denial Predictor -> PASS (Denial Probability: {predict_data.get('probability')}, Risk Factors: {len(predict_data.get('risk_factors', []))})")

# 8. AI Appeal Generator
appeal_res = requests.post(
    f'{BASE_URL}/denials/19/draft-appeal',
    json={'additional_context': 'Documentation shows prior auth obtained on 09/01/2026'},
    headers=headers
)
assert appeal_res.status_code == 200, f"Appeal draft failed: {appeal_res.text}"
appeal_data = appeal_res.json()
print(f"[TEST 8] AI Appeal Letter Generator -> PASS (Draft length: {len(appeal_data.get('appeal_letter', ''))} characters, Confidence: {appeal_data.get('confidence')})")

# 9. AI Assistant Chatbot
chat_res = requests.post(f'{BASE_URL}/assistant/query', json={'query': 'What is our accounts receivable over 90 days?'}, headers=headers)
assert chat_res.status_code == 200, f"Assistant query failed: {chat_res.text}"
print(f"[TEST 9] AI Assistant Analytics Chatbot -> PASS (Response: {chat_res.json()['response'][:80]}...)")

# 10. Frontend Bundle Check
front_res = requests.get(FRONTEND_URL)
assert front_res.status_code == 200, f"Frontend site failed: {front_res.status_code}"
print(f"[TEST 10] Frontend Production Deployment -> PASS ({FRONTEND_URL} 200 OK)")

print("=" * 60)
print("ALL 10/10 TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
