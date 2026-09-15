import sys
import io
import requests

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://novaarc-backend.onrender.com"
FRONTEND_URL = "https://novaarc.netlify.app"

ROLES = [
    ("client_leadership@novaarc.local", "password123", "client_leadership"),
    ("ops_leadership@novaarc.local", "password123", "ops_leadership"),
    ("ops_manager@novaarc.local", "password123", "ops_manager"),
    ("team_lead@novaarc.local", "password123", "team_lead"),
    ("ar_executive@novaarc.local", "password123", "ar_executive"),
    ("qa_auditor@novaarc.local", "password123", "qa_auditor"),
]

def run_tests():
    print("=" * 60)
    print("NovaArc RCM - Live End-to-End Verification")
    print(f"Backend:  {BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print("=" * 60)

    passed = 0
    failed = 0

    # 1. Health Check
    print("\n[TEST 1] Backend Health Check")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=15)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json().get("status") == "healthy", f"Unexpected payload: {r.text}"
        print("  [PASS] /health returned 200 OK (healthy)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Health check failed: {e}")
        failed += 1

    # 2. CORS Preflight & Origin Headers
    print("\n[TEST 2] CORS Verification from Netlify Origin")
    try:
        headers = {
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type"
        }
        r = requests.options(f"{BASE_URL}/auth/login", headers=headers, timeout=15)
        cors_origin = r.headers.get("access-control-allow-origin")
        print(f"  Access-Control-Allow-Origin: {cors_origin}")
        assert cors_origin in [FRONTEND_URL, "*"], f"CORS origin not allowed: {cors_origin}"
        print("  [PASS] CORS configured correctly for Netlify frontend")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] CORS check failed: {e}")
        failed += 1

    # 3. User Authentication for All 6 Roles
    print("\n[TEST 3] Role Authentication & JWT Generation")
    tokens = {}
    for email, password, role in ROLES:
        try:
            r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=15)
            assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
            token = r.json().get("access_token")
            assert token, "No access_token returned"
            tokens[role] = token
            print(f"  [PASS] Login succeeded for {role} ({email})")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] Login failed for {email}: {e}")
            failed += 1

    primary_token = tokens.get("client_leadership") or list(tokens.values())[0]
    auth_headers = {"Authorization": f"Bearer {primary_token}"}

    # 4. Auth /me Endpoint
    print("\n[TEST 4] Current User Profile (/auth/me)")
    try:
        r = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        user_data = r.json()
        print(f"  [PASS] User profile retrieved: {user_data.get('email')} (Role: {user_data.get('role')})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] /auth/me failed: {e}")
        failed += 1

    # 5. Dashboard Metrics & Analytics
    print("\n[TEST 5] Dashboard Analytics Endpoints")
    for endpoint, name in [
        ("/dashboard/revenue-health", "Revenue Health Metrics"),
        ("/dashboard/ar-health", "AR Aging Health"),
        ("/dashboard/payer-performance", "Payer Performance"),
        ("/dashboard/denial-intelligence", "Denial Intelligence"),
    ]:
        try:
            r = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers, timeout=15)
            assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
            print(f"  [PASS] {name} ({endpoint}) returned 200 OK")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name} failed: {e}")
            failed += 1

    # 6. Claims Management
    print("\n[TEST 6] Claims Retrieval & Detail")
    try:
        r = requests.get(f"{BASE_URL}/claims?skip=0&limit=10", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        claims = r.json()
        assert isinstance(claims, list) and len(claims) > 0, "No claims returned"
        first_claim = claims[0]
        claim_id = first_claim.get("claim_id")
        print(f"  [PASS] Retrieved {len(claims)} claims (Sample Claim ID: #{claim_id})")
        passed += 1

        # Fetch single claim
        r_single = requests.get(f"{BASE_URL}/claims/{claim_id}", headers=auth_headers, timeout=15)
        assert r_single.status_code == 200, f"Status {r_single.status_code}"
        print(f"  [PASS] Single claim #{claim_id} retrieved successfully")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Claims verification failed: {e}")
        failed += 1

    # 7. Denials & AI Appeal Drafting Pipeline
    print("\n[TEST 7] Denials Management & AI Appeal Generation")
    try:
        r = requests.get(f"{BASE_URL}/denials?limit=5", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        denials = r.json()
        assert isinstance(denials, list) and len(denials) > 0, "No denials found"
        denial = denials[0]
        denial_id = denial.get("denial_id")
        code = denial.get("denial_code")
        print(f"  [PASS] Retrieved denials (Sample Denial #{denial_id}, Code: {code})")
        passed += 1

        # Test Top Codes
        r_top = requests.get(f"{BASE_URL}/denials/top-codes", headers=auth_headers, timeout=15)
        assert r_top.status_code == 200, f"Status {r_top.status_code}"
        print(f"  [PASS] Top denial codes aggregated successfully ({len(r_top.json())} codes)")
        passed += 1

        # Test AI Appeal Letter Generation
        r_appeal = requests.post(
            f"{BASE_URL}/denials/{denial_id}/draft-appeal",
            json={"additional_context": "Medical necessity verified with primary diagnosis."},
            headers=auth_headers,
            timeout=30
        )
        assert r_appeal.status_code == 200, f"Status {r_appeal.status_code}: {r_appeal.text}"
        appeal_data = r_appeal.json()
        letter = appeal_data.get("appeal_letter", "")
        confidence = appeal_data.get("confidence")
        assert letter and len(letter) > 50, "Appeal letter empty or too short"
        print(f"  [PASS] AI Appeal drafted successfully (Confidence: {confidence})")
        print(f"    Preview: {letter[:90].replace(chr(10), ' ')}...")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Denials / Appeal test failed: {e}")
        failed += 1

    # 8. Work Queues
    print("\n[TEST 8] AI Work Queues")
    try:
        r = requests.get(f"{BASE_URL}/work-queues", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        queues = r.json()
        assert isinstance(queues, list) and len(queues) > 0, "No work queues found"
        print(f"  [PASS] Retrieved {len(queues)} AI work queues")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Work queues test failed: {e}")
        failed += 1

    # 9. Payments & Remittances
    print("\n[TEST 9] Payments & Remittances")
    try:
        r = requests.get(f"{BASE_URL}/payments?limit=5", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        payments = r.json()
        assert isinstance(payments, list) and len(payments) > 0, "No payments found"
        print(f"  [PASS] Retrieved {len(payments)} payment remittance records")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Payments test failed: {e}")
        failed += 1

    # 10. Frontend Bundle Check
    print("\n[TEST 10] Frontend Bundle & API URL Check")
    try:
        r_html = requests.get(FRONTEND_URL, timeout=15)
        assert r_html.status_code == 200, f"HTML Status {r_html.status_code}"
        import re
        match = re.search(r'src="(/assets/index-[^"]+\.js)"', r_html.text)
        assert match, "Could not find index-*.js in index.html"
        js_path = match.group(1)
        r_js = requests.get(f"{FRONTEND_URL}{js_path}", timeout=15)
        assert r_js.status_code == 200, f"JS Status {r_js.status_code}"
        assert BASE_URL in r_js.text, "Backend URL not baked into bundle"
        print(f"  [PASS] Frontend bundle ({js_path}) contains production backend URL")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Frontend bundle check failed: {e}")
        failed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
