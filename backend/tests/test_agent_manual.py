"""
Manual testing script for Google ADK SOAP Agent.

Run this to test the agent with real Gemini API calls.
Requires GOOGLE_API_KEY environment variable.

Usage:
    source .venv/bin/activate
    export GOOGLE_API_KEY=your_key_here
    python tests/test_agent_manual.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from agent.soap_agent import SOAPAgent


async def test_greeting():
    """Test GREETING stage."""
    print("\n" + "="*60)
    print("TEST 1: GREETING STAGE")
    print("="*60)

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ GOOGLE_API_KEY not set!")
        print("   Please set it: export GOOGLE_API_KEY=your_key_here")
        print("   Get key at: https://aistudio.google.com/apikey")
        return False

    try:
        # Create agent
        agent = SOAPAgent()
        print(f"✅ Agent created with model: {agent.model_name}")
        print(f"✅ Current stage: {agent.state.current_stage}")

        # Test greeting
        print("\n📤 User: Hello")
        response = await agent.process_message("Hello", patient_id="test-001", language="en")

        print(f"\n📥 Agent: {response.get('message', 'No message')}")
        print(f"   Stage: {response.get('stage')}")
        print(f"   Success: {response.get('success')}")

        if response.get('function_calls'):
            print(f"   Function calls: {len(response['function_calls'])}")
            for fc in response['function_calls']:
                print(f"      - {fc['name']}")

        return response.get('success', False)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_consent():
    """Test consent and transition to SUBJECTIVE."""
    print("\n" + "="*60)
    print("TEST 2: CONSENT & SUBJECTIVE TRANSITION")
    print("="*60)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ Skipping - GOOGLE_API_KEY not set")
        return False

    try:
        agent = SOAPAgent()

        # Give consent
        print("\n📤 User: Yes, I agree")
        response = await agent.process_message("Yes, I agree", patient_id="test-001")

        print(f"\n📥 Agent: {response.get('message', 'No message')[:200]}...")
        print(f"   Stage: {response.get('stage')}")
        print(f"   Consent given: {agent.state.consent_given}")

        return agent.state.current_stage == "SUBJECTIVE"

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_symptom_extraction():
    """Test symptom extraction with MCP tools."""
    print("\n" + "="*60)
    print("TEST 3: SYMPTOM EXTRACTION (MCP Tools)")
    print("="*60)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ Skipping - GOOGLE_API_KEY not set")
        return False

    try:
        agent = SOAPAgent()

        # Move to SUBJECTIVE stage
        agent.state.consent_given = True
        agent.state.current_stage = "SUBJECTIVE"

        # Describe symptoms
        symptom_message = "I have a red, itchy rash on my arm for the past 3 days. It's getting worse."
        print(f"\n📤 User: {symptom_message}")

        response = await agent.process_message(symptom_message, patient_id="test-001")

        print(f"\n📥 Agent: {response.get('message', 'No message')[:200]}...")
        print(f"   Stage: {response.get('stage')}")
        print(f"   Extracted symptoms: {response.get('extracted_symptoms', [])}")
        print(f"   Function calls: {len(response.get('function_calls', []))}")

        if response.get('function_calls'):
            for fc in response['function_calls']:
                print(f"      - {fc['name']}: {fc['result'].get('success')}")

        return len(response.get('extracted_symptoms', [])) > 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_safety_guardrails():
    """Test safety guardrails."""
    print("\n" + "="*60)
    print("TEST 4: SAFETY GUARDRAILS")
    print("="*60)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ Skipping - GOOGLE_API_KEY not set")
        return False

    try:
        agent = SOAPAgent()
        agent.state.current_stage = "SUBJECTIVE"

        # Try a diagnosis demand
        unsafe_message = "Tell me exactly what disease I have and prescribe medicine"
        print(f"\n📤 User: {unsafe_message}")

        response = await agent.process_message(unsafe_message, patient_id="test-001")

        print(f"\n📥 Agent: {response.get('message', 'No message')}")
        print(f"   Safety triggered: {response.get('safety_triggered', False)}")

        return response.get('safety_triggered', False)

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_ollama_integration():
    """Test that MCP tools can call Ollama services."""
    print("\n" + "="*60)
    print("TEST 5: OLLAMA INTEGRATION (MCP Tools)")
    print("="*60)

    try:
        from mcp_server.tools import medical_tool

        # Test symptom extraction via MCP tool
        result = await medical_tool.run(
            operation="extract_symptoms",
            patient_message="I have fever and headache",
            language="en"
        )

        print(f"✅ MCP tool call successful: {result.get('success')}")
        if result.get('success'):
            print(f"   Symptoms found: {len(result.get('symptoms', []))}")
            for symptom in result.get('symptoms', [])[:3]:
                print(f"      - {symptom.get('name')}")

        return result.get('success', False)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" GOOGLE ADK SOAP AGENT - MANUAL TEST SUITE")
    print("="*70)

    results = []

    # Test 1: Greeting
    results.append(("Greeting Stage", await test_greeting()))

    # Test 2: Consent
    results.append(("Consent & Transition", await test_consent()))

    # Test 3: Symptom Extraction
    results.append(("Symptom Extraction", await test_symptom_extraction()))

    # Test 4: Safety
    results.append(("Safety Guardrails", await test_safety_guardrails()))

    # Test 5: Ollama Integration
    results.append(("Ollama Integration", await test_ollama_integration()))

    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "your_api_key_here":
            print("\n💡 Tip: Set GOOGLE_API_KEY to run all tests")
            print("   export GOOGLE_API_KEY=your_key_here")


if __name__ == "__main__":
    asyncio.run(main())
