import requests
import json
import time

BASE_URL = 'https://novaarc-backend.onrender.com'
FRONTEND_URL = 'https://novaarc.netlify.app'

print("=" * 70)
print("NovaArc RCM - Live AI Models Verification with New OpenRouter Key")
print("=" * 70)

# 1. Login
auth_res = requests.post(
    f'{BASE_URL}/auth/login',
    json={'email': 'client_leadership@novaarc.local', 'password': 'password123'},
    headers={'Origin': FRONTEND_URL}
)
assert auth_res.status_code == 200, f"Login failed: {auth_res.text}"
token = auth_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Origin': FRONTEND_URL}
print("[AUTH] Logged in successfully as client_leadership@novaarc.local\n")

# 2. Medical Coding Assistant (Ling 3.0 Flash Sante)
print("[TEST 1] Testing Medical Coding Assistant (Model: Ling 3.0 Flash Sante)...")
t0 = time.time()
coding_payload = {
    'clinical_notes': 'Patient is a 58-year-old male with poorly controlled type 2 diabetes mellitus with diabetic polyneuropathy, essential hypertension, and hyperlipidemia. Presenting for follow-up and medication adjustment. Comprehensive examination performed.',
    'patient_context': {'mrn': 'MRN-TEST-AI'}
}
coding_res = requests.post(f'{BASE_URL}/agents/coding-assist', json=coding_payload, headers=headers, timeout=60)
dt = round(time.time() - t0, 2)
print(f"Coding Assist Response [{coding_res.status_code}] in {dt}s:")
if coding_res.status_code == 200:
    c_data = coding_res.json()
    print("  Overall Confidence:", c_data.get('confidence'))
    print("  ICD-10 Codes:")
    for icd in c_data.get('icd10_suggestions', []):
        print(f"    - {icd.get('code')}: {icd.get('description')} (conf: {icd.get('confidence')})")
    print("  CPT Codes:")
    for cpt in c_data.get('cpt_suggestions', []):
        print(f"    - {cpt.get('code')}: {cpt.get('description')} (conf: {cpt.get('confidence')})")
else:
    print("  Error:", coding_res.text)

print("-" * 70)

# 3. Denial Appeal Letter Drafting (Ling 3.0 Flash Sante / Nemotron 3.5)
print("[TEST 2] Testing Denial Appeal Letter Drafting (Ling 3.0 Flash Sante / Nemotron 3.5)...")
t0 = time.time()
appeal_payload = {
    'additional_context': 'Prior authorization was previously obtained under auth number PA-8923412. Medical necessity documentation attached showing failed conservative therapy for 6 months.'
}
appeal_res = requests.post(f'{BASE_URL}/denials/19/draft-appeal', json=appeal_payload, headers=headers, timeout=60)
dt = round(time.time() - t0, 2)
print(f"Appeal Generator Response [{appeal_res.status_code}] in {dt}s:")
if appeal_res.status_code == 200:
    a_data = appeal_res.json()
    print("  Confidence:", a_data.get('confidence'))
    print("  Recoverable Amount:", a_data.get('expected_recovery_amount'))
    print("  Appeal Letter Snippet:\n", "\n".join("    " + line for line in a_data.get('appeal_letter', '').split("\n")[:8]))
else:
    print("  Error:", appeal_res.text)

print("-" * 70)

# 4. NL-to-SQL / Analytics Assistant (Laguna S 2.1 / Nex-N2.5-Mini)
print("[TEST 3] Testing NL-to-SQL / Analytics Assistant (Laguna S 2.1 / Nex-N2.5-Mini)...")
queries = [
    "What is our total AR balance?",
    "Show me the top 5 highest charge claims",
    "What are our top denial codes and amounts?"
]
for q in queries:
    t0 = time.time()
    nl_res = requests.post(f'{BASE_URL}/assistant/query', json={'query': q}, headers=headers, timeout=60)
    dt = round(time.time() - t0, 2)
    print(f"Query: \"{q}\" -> Status {nl_res.status_code} in {dt}s")
    if nl_res.status_code == 200:
        ans = nl_res.json()
        print("  Intent:", ans.get('intent'))
        print("  Response:", ans.get('response')[:150].replace('\n', ' ') + "...")
        if ans.get('data') and 'sql' in ans.get('data'):
            print("  Generated SQL:", ans['data']['sql'])
    else:
        print("  Error:", nl_res.text)
    print()

print("=" * 70)
