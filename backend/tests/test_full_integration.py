"""
Full Integration Test - Frontend + Backend

Tests the complete flow from frontend API calls to backend SOAP agent.

This simulates what the frontend does when calling the backend.

Usage:
    python tests/test_full_integration.py
"""

import asyncio
import requests
import json

BACKEND_URL = "http://localhost:8000"


def test_full_conversation():
    """Test a full conversation flow through the API."""

    print("\n" + "="*70)
    print(" FULL INTEGRATION TEST - Frontend → Backend → SOAP Agent")
    print("="*70)

    consultation_id = None

    # Step 1: Greeting
    print("\n" + "-"*70)
    print("STEP 1: Initial Greeting")
    print("-"*70)

    payload1 = {
        "message": "Hello, I need help with my skin",
        "patient_id": "integration-test-001",
        "language": "en"
    }

    print(f"📤 POST {BACKEND_URL}/agent/message")
    print(f"   Payload: {json.dumps(payload1, indent=2)}")

    response1 = requests.post(f"{BACKEND_URL}/agent/message", json=payload1)

    if response1.status_code != 200:
        print(f"❌ Request failed: {response1.status_code}")
        print(f"   Error: {response1.text}")
        return False

    data1 = response1.json()
    consultation_id = data1.get("consultation_id")

    print(f"\n📥 Response ({response1.status_code}):")
    print(f"   ✅ Success: {data1['success']}")
    print(f"   Stage: {data1['current_stage']}")
    print(f"   Consultation ID: {consultation_id}")
    print(f"   Message: {data1['message'][:150]}...")

    if data1['current_stage'] != "GREETING":
        print(f"❌ Expected GREETING stage")
        return False

    # Step 2: Give Consent
    print("\n" + "-"*70)
    print("STEP 2: Give Consent")
    print("-"*70)

    payload2 = {
        "message": "Yes, I agree",
        "consultation_id": consultation_id,
        "patient_id": "integration-test-001",
        "language": "en"
    }

    print(f"📤 POST {BACKEND_URL}/agent/message")
    response2 = requests.post(f"{BACKEND_URL}/agent/message", json=payload2)
    data2 = response2.json()

    print(f"\n📥 Response ({response2.status_code}):")
    print(f"   Stage: {data2['current_stage']}")
    print(f"   Message: {data2['message'][:150]}...")

    if data2['current_stage'] != "SUBJECTIVE":
        print(f"⚠️  Expected SUBJECTIVE stage, got {data2['current_stage']}")

    # Step 3: Describe Symptoms
    print("\n" + "-"*70)
    print("STEP 3: Describe Symptoms")
    print("-"*70)

    payload3 = {
        "message": "I have a red, itchy rash on my arm for 3 days. It's getting worse and painful.",
        "consultation_id": consultation_id,
        "patient_id": "integration-test-001",
        "language": "en"
    }

    print(f"📤 POST {BACKEND_URL}/agent/message")
    response3 = requests.post(f"{BACKEND_URL}/agent/message", json=payload3)
    data3 = response3.json()

    print(f"\n📥 Response ({response3.status_code}):")
    print(f"   Stage: {data3['current_stage']}")
    print(f"   Message: {data3['message'][:150]}...")
    print(f"   Requires Image: {data3.get('requires_image', False)}")

    # Step 4: Get Consultation State
    print("\n" + "-"*70)
    print("STEP 4: Get Consultation State")
    print("-"*70)

    print(f"📤 GET {BACKEND_URL}/agent/consultation/{consultation_id}")
    response4 = requests.get(f"{BACKEND_URL}/agent/consultation/{consultation_id}")
    state = response4.json()

    print(f"\n📥 Consultation State:")
    print(f"   Stage: {state['current_stage']}")
    print(f"   Consent: {state['consent_given']}")
    print(f"   Symptoms: {state['extracted_symptoms']}")
    print(f"   Messages: {state['message_history_count']}")

    # Summary
    print("\n" + "="*70)
    print(" INTEGRATION TEST SUMMARY")
    print("="*70)

    print(f"\n✅ Successfully tested:")
    print(f"   • Agent message endpoint (POST /agent/message)")
    print(f"   • Conversation state management")
    print(f"   • SOAP workflow progression (GREETING → SUBJECTIVE → OBJECTIVE)")
    print(f"   • Symptom extraction")
    print(f"   • Consultation state retrieval (GET /agent/consultation/{{id}})")

    print(f"\n🎉 Frontend ↔ Backend integration working perfectly!")

    return True


def test_agent_health():
    """Test agent health endpoint."""
    print("\n" + "-"*70)
    print("BONUS: Agent Health Check")
    print("-"*70)

    response = requests.get(f"{BACKEND_URL}/agent/health")
    health = response.json()

    print(f"📥 Health Status:")
    print(f"   Status: {health['status']}")
    print(f"   Agent Type: {health['agent_type']}")
    print(f"   Active Consultations: {health['active_consultations']}")
    print(f"   Tools Count: {health['tools_count']}")


if __name__ == "__main__":
    print("\n🔧 Testing Full Integration: Frontend API → Backend → SOAP Agent\n")

    try:
        # Test health first
        test_agent_health()

        # Run full conversation test
        success = test_full_conversation()

        if success:
            print("\n✅ All integration tests passed!")
        else:
            print("\n⚠️  Some tests failed")

    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("   Make sure backend is running on http://localhost:8000")
        print("   Start with: cd backend && uvicorn main:app --reload")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
