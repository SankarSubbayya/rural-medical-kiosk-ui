"""
Multi-language support testing for SOAP Agent.

Tests agent's ability to handle consultations in:
- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)

Usage:
    source .venv/bin/activate
    python tests/test_multilanguage.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from agent.soap_agent import SOAPAgent


# Test messages in different languages
TEST_MESSAGES = {
    "en": {
        "greeting": "Hello, I need help",
        "consent": "Yes, I agree",
        "symptoms": "I have a red, itchy rash on my arm for 3 days",
        "language_code": "en"
    },
    "hi": {
        "greeting": "नमस्ते, मुझे मदद चाहिए",
        "consent": "हां, मैं सहमत हूं",
        "symptoms": "मेरे हाथ पर 3 दिन से लाल और खुजली वाला दाने है",
        "language_code": "hi"
    },
    "ta": {
        "greeting": "வணக்கம், எனக்கு உதவி வேண்டும்",
        "consent": "ஆம், நான் சம்மதிக்கிறேன்",
        "symptoms": "என் கையில் 3 நாட்களாக சிவப்பு, அரிப்பு சொறி உள்ளது",
        "language_code": "ta"
    },
    "te": {
        "greeting": "నమస్కారం, నాకు సహాయం కావాలి",
        "consent": "అవును, నేను అంగీకరిస్తున్నాను",
        "symptoms": "నా చేతిపై 3 రోజులుగా ఎరుపు, దురద పొక్కులు ఉన్నాయి",
        "language_code": "te"
    },
    "bn": {
        "greeting": "হ্যালো, আমার সাহায্য দরকার",
        "consent": "হ্যাঁ, আমি সম্মত",
        "symptoms": "আমার হাতে 3 দিন ধরে লাল, চুলকানি ফুসকুড়ি আছে",
        "language_code": "bn"
    }
}


async def test_language(language: str, messages: dict):
    """Test agent with specific language."""

    print("\n" + "="*70)
    print(f" TESTING: {language.upper()} ({messages['language_code']})")
    print("="*70)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ GOOGLE_API_KEY not set!")
        return False

    try:
        agent = SOAPAgent()
        patient_id = f"test-{language}-001"
        lang_code = messages['language_code']

        # Test 1: Greeting
        print(f"\n📤 Patient ({language}): {messages['greeting']}")
        response1 = await agent.process_message(
            messages['greeting'],
            patient_id=patient_id,
            language=lang_code
        )

        if 'message' in response1:
            print(f"📥 Agent: {response1['message'][:150]}...")
        else:
            print(f"📥 Agent: [No message - Error: {response1.get('error', 'Unknown')}]")

        print(f"   Stage: {response1.get('stage', 'UNKNOWN')}")
        print(f"   Success: {response1.get('success', False)}")

        if not response1.get('success', False):
            print(f"❌ Greeting failed: {response1.get('error', 'Unknown error')}")
            return False

        # Test 2: Consent
        print(f"\n📤 Patient ({language}): {messages['consent']}")
        response2 = await agent.process_message(
            messages['consent'],
            patient_id=patient_id,
            language=lang_code
        )

        if 'message' in response2:
            print(f"📥 Agent: {response2['message'][:150]}...")
        else:
            print(f"📥 Agent: [No message - Error: {response2.get('error', 'Unknown')}]")

        print(f"   Stage: {response2.get('stage', 'UNKNOWN')}")
        print(f"   Consent given: {agent.state.consent_given}")

        if response2.get('stage') != "SUBJECTIVE":
            print(f"⚠️  Expected SUBJECTIVE stage, got {response2.get('stage', 'UNKNOWN')}")

        # Test 3: Symptom extraction
        print(f"\n📤 Patient ({language}): {messages['symptoms']}")
        response3 = await agent.process_message(
            messages['symptoms'],
            patient_id=patient_id,
            language=lang_code
        )

        if 'message' in response3:
            print(f"📥 Agent: {response3['message'][:150]}...")
        else:
            print(f"📥 Agent: [No message - Error: {response3.get('error', 'Unknown')}]")

        print(f"   Stage: {response3.get('stage', 'UNKNOWN')}")
        print(f"   Extracted symptoms: {response3.get('extracted_symptoms', [])}")
        print(f"   Function calls: {[fc['name'] for fc in response3.get('function_calls', [])]}")

        # Check if symptoms were extracted
        success = len(response3.get('extracted_symptoms', [])) > 0

        if success:
            print(f"\n✅ {language.upper()}: All tests passed")
        else:
            print(f"\n⚠️  {language.upper()}: Symptom extraction failed")

        return success

    except Exception as e:
        print(f"\n❌ Error testing {language}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run multi-language tests."""

    print("\n" + "="*70)
    print(" MULTI-LANGUAGE SUPPORT TEST SUITE")
    print("="*70)
    print("\nTesting Gemini 2.0's ability to handle medical consultations in:")
    print("- English (en)")
    print("- Hindi (hi)")
    print("- Tamil (ta)")
    print("- Telugu (te)")
    print("- Bengali (bn)")

    results = {}

    # Test each language
    for language, messages in TEST_MESSAGES.items():
        results[language] = await test_language(language, messages)

    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    for language, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {language.upper()} ({TEST_MESSAGES[language]['language_code']})")

    print(f"\nTotal: {passed}/{total} languages tested successfully ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 All languages supported!")
    else:
        print(f"\n⚠️  {total - passed} language(s) need attention")

    print("\n💡 Note: Gemini 2.0 Flash has strong multilingual capabilities")
    print("   The agent should respond appropriately in the user's language")


if __name__ == "__main__":
    asyncio.run(main())
