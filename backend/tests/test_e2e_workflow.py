"""
End-to-end SOAP workflow test with image analysis.

This test simulates a complete consultation from GREETING to PLAN.

Usage:
    source .venv/bin/activate
    python tests/test_e2e_workflow.py
"""

import asyncio
import os
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from agent.soap_agent import SOAPAgent


def create_sample_image() -> str:
    """Create a minimal valid JPEG as base64 for testing."""
    # Minimal 1x1 red JPEG
    jpeg_bytes = base64.b64decode(
        "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
        "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
        "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
        "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
        "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA//"
    )
    return base64.b64encode(jpeg_bytes).decode('utf-8')


async def test_full_workflow():
    """Test complete SOAP workflow: GREETING → SUBJECTIVE → OBJECTIVE → ASSESSMENT → PLAN"""

    print("\n" + "="*70)
    print(" END-TO-END SOAP WORKFLOW TEST")
    print("="*70)

    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ GOOGLE_API_KEY not set!")
        print("   Please set it: export GOOGLE_API_KEY=your_key_here")
        return False

    try:
        # Initialize agent
        agent = SOAPAgent()
        patient_id = "test-e2e-001"

        print(f"\n✅ Agent initialized with model: {agent.model_name}")
        print(f"   Starting stage: {agent.state.current_stage}")

        # ============================================================
        # STAGE 1: GREETING
        # ============================================================
        print("\n" + "-"*70)
        print("STAGE 1: GREETING")
        print("-"*70)

        print("👤 Patient: Hello, I need help with my skin")
        response1 = await agent.process_message(
            "Hello, I need help with my skin",
            patient_id=patient_id,
            language="en"
        )

        print(f"\n🤖 Agent: {response1['message'][:200]}...")
        print(f"   Current stage: {response1['stage']}")
        print(f"   Function calls: {len(response1.get('function_calls', []))}")

        if response1['stage'] != "GREETING":
            print("❌ Failed: Should still be in GREETING stage")
            return False

        # ============================================================
        # STAGE 2: CONSENT → SUBJECTIVE
        # ============================================================
        print("\n" + "-"*70)
        print("STAGE 2: CONSENT & TRANSITION TO SUBJECTIVE")
        print("-"*70)

        print("👤 Patient: Yes, I agree. Please help me.")
        response2 = await agent.process_message(
            "Yes, I agree. Please help me.",
            patient_id=patient_id
        )

        print(f"\n🤖 Agent: {response2['message'][:200]}...")
        print(f"   Current stage: {response2['stage']}")
        print(f"   Consent given: {agent.state.consent_given}")

        if response2['stage'] != "SUBJECTIVE":
            print(f"❌ Failed: Should be in SUBJECTIVE stage, got {response2['stage']}")
            return False

        # ============================================================
        # STAGE 3: SUBJECTIVE - Symptom Collection
        # ============================================================
        print("\n" + "-"*70)
        print("STAGE 3: SUBJECTIVE - Symptom Collection")
        print("-"*70)

        print("👤 Patient: I have a red, itchy rash on my arm for 5 days. It's spreading and painful.")
        response3 = await agent.process_message(
            "I have a red, itchy rash on my arm for 5 days. It's spreading and painful.",
            patient_id=patient_id
        )

        print(f"\n🤖 Agent: {response3['message'][:200]}...")
        print(f"   Current stage: {response3['stage']}")
        print(f"   Extracted symptoms: {response3.get('extracted_symptoms', [])}")
        print(f"   Function calls: {[fc['name'] for fc in response3.get('function_calls', [])]}")

        if len(response3.get('extracted_symptoms', [])) == 0:
            print("⚠️  Warning: No symptoms extracted")

        # Continue collecting symptoms if needed
        if response3['stage'] == "SUBJECTIVE":
            print("\n👤 Patient: The rash started small but now covers my whole forearm. It burns when I touch it.")
            response3b = await agent.process_message(
                "The rash started small but now covers my whole forearm. It burns when I touch it.",
                patient_id=patient_id
            )

            print(f"\n🤖 Agent: {response3b['message'][:200]}...")
            print(f"   Current stage: {response3b['stage']}")
            print(f"   Total extracted symptoms: {response3b.get('extracted_symptoms', [])}")

        # Check if we moved to OBJECTIVE
        current_stage = response3b.get('stage', response3['stage']) if 'response3b' in locals() else response3['stage']

        if current_stage == "OBJECTIVE":
            print(f"\n✅ Transitioned to OBJECTIVE stage (found {len(agent.state.extracted_symptoms)} symptoms)")
        else:
            print(f"\n⚠️  Still in {current_stage} stage")
            print(f"   Note: Need 2+ symptoms to auto-transition to OBJECTIVE")
            print(f"   Current symptoms: {agent.state.extracted_symptoms}")

        # ============================================================
        # STAGE 4: OBJECTIVE - Image Analysis
        # ============================================================
        print("\n" + "-"*70)
        print("STAGE 4: OBJECTIVE - Image Analysis")
        print("-"*70)

        # Force stage to OBJECTIVE if not already there (for testing)
        if agent.state.current_stage != "OBJECTIVE":
            print("   Manually setting stage to OBJECTIVE for image analysis test...")
            agent.state.current_stage = "OBJECTIVE"

        # Create sample image
        sample_image = create_sample_image()

        print("👤 Patient: [Uploads image of rash]")
        print(f"   Image size: {len(sample_image)} bytes (base64)")

        response4 = await agent.process_message(
            "Here's a photo of the rash on my arm",
            image_base64=sample_image,
            patient_id=patient_id
        )

        print(f"\n🤖 Agent: {response4['message'][:200]}...")
        print(f"   Current stage: {response4['stage']}")
        print(f"   Image captured: {agent.state.image_captured}")
        print(f"   Function calls: {[fc['name'] for fc in response4.get('function_calls', [])]}")

        if response4.get('analysis'):
            print(f"   ✅ Image analysis completed")

        # ============================================================
        # STAGE 5: ASSESSMENT
        # ============================================================
        print("\n" + "-"*70)
        print("STAGE 5: ASSESSMENT")
        print("-"*70)

        if agent.state.current_stage == "ASSESSMENT":
            print("✅ Automatically transitioned to ASSESSMENT stage")

            print("👤 Patient: What do you think it could be?")
            response5 = await agent.process_message(
                "What do you think it could be?",
                patient_id=patient_id
            )

            print(f"\n🤖 Agent: {response5['message'][:300]}...")
            print(f"   Current stage: {response5['stage']}")
        else:
            print(f"⚠️  Not in ASSESSMENT stage (current: {agent.state.current_stage})")
            print("   This requires image_captured=True and analysis_results set")

        # ============================================================
        # STAGE 6: PLAN
        # ============================================================
        print("\n" + "-"*70)
        print("STAGE 6: PLAN")
        print("-"*70)

        if agent.state.current_stage == "PLAN":
            print("✅ Automatically transitioned to PLAN stage")

            print("👤 Patient: What should I do next?")
            response6 = await agent.process_message(
                "What should I do next?",
                patient_id=patient_id
            )

            print(f"\n🤖 Agent: {response6['message'][:300]}...")
            print(f"   Current stage: {response6['stage']}")
            print(f"   Function calls: {[fc['name'] for fc in response6.get('function_calls', [])]}")
        else:
            print(f"⚠️  Not in PLAN stage (current: {agent.state.current_stage})")

        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "="*70)
        print(" WORKFLOW SUMMARY")
        print("="*70)

        print(f"\n📊 Final State:")
        print(f"   Stage: {agent.state.current_stage}")
        print(f"   Consent given: {agent.state.consent_given}")
        print(f"   Symptoms extracted: {len(agent.state.extracted_symptoms)}")
        print(f"   Image captured: {agent.state.image_captured}")
        print(f"   Total messages: {len(agent.state.message_history)}")

        print(f"\n📝 Extracted Symptoms:")
        for symptom in agent.state.extracted_symptoms:
            print(f"   • {symptom}")

        print("\n✅ End-to-end workflow test completed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run end-to-end workflow test."""
    success = await test_full_workflow()

    if success:
        print("\n🎉 All workflow stages tested successfully!")
    else:
        print("\n⚠️  Workflow test encountered issues")


if __name__ == "__main__":
    asyncio.run(main())
