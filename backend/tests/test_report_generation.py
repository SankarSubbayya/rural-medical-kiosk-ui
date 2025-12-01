"""
Test Report Generation with MedGemma and Qdrant Results

This test demonstrates generating both patient and physician reports
with MedGemma analysis and Qdrant similar cases.
"""
import httpx
import asyncio
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


async def test_report_generation():
    """Test generating patient and physician reports with AI analysis data."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "="*80)
        print("TESTING SOAP REPORT GENERATION")
        print("="*80)

        # Step 1: Start a consultation
        print("\n[1/6] Creating new consultation...")
        create_response = await client.post(
            f"{BASE_URL}/agent/message",
            json={
                "message": "Hello, I need help with a skin condition",
                "patient_id": "test_patient_123",
                "language": "en"
            }
        )

        if not create_response.is_success:
            print(f"❌ Failed to create consultation: {create_response.text}")
            return

        result = create_response.json()
        consultation_id = result.get("consultationId")

        if not consultation_id:
            print("❌ No consultation ID returned")
            return

        print(f"✅ Consultation created: {consultation_id}")

        # Step 2: Provide consent
        print("\n[2/6] Providing consent...")
        await client.post(
            f"{BASE_URL}/agent/message",
            json={
                "message": "Yes, I consent",
                "patient_id": "test_patient_123",
                "language": "en",
                "consultation_id": consultation_id
            }
        )
        print("✅ Consent provided")

        # Step 3: Describe symptoms
        print("\n[3/6] Describing symptoms...")
        await client.post(
            f"{BASE_URL}/agent/message",
            json={
                "message": "I have red, itchy rashes on my arm for 2 weeks",
                "patient_id": "test_patient_123",
                "language": "en",
                "consultation_id": consultation_id
            }
        )
        print("✅ Symptoms described")

        # Step 4: Upload image (using a small placeholder)
        print("\n[4/6] Uploading test image...")
        # Small test image (1x1 PNG, base64 encoded)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

        upload_response = await client.post(
            f"{BASE_URL}/agent/message",
            json={
                "message": "Here is the image of my condition",
                "patient_id": "test_patient_123",
                "language": "en",
                "consultation_id": consultation_id,
                "image_base64": test_image
            }
        )

        if upload_response.is_success:
            result = upload_response.json()
            print(f"✅ Image uploaded successfully")
            print(f"   Response: {result.get('message', '')[:100]}...")
        else:
            print(f"❌ Image upload failed: {upload_response.text}")
            return

        # Step 5: Generate Patient Report
        print("\n[5/6] Generating PATIENT REPORT...")
        print("-" * 80)

        patient_report_response = await client.post(
            f"{BASE_URL}/report/patient",
            json={
                "consultation_id": consultation_id,
                "language": "en"
            }
        )

        if patient_report_response.is_success:
            patient_data = patient_report_response.json()
            print("\n📄 PATIENT REPORT (Simple Language):")
            print("=" * 80)
            print(patient_data.get("report_text", "No report text"))
            print("=" * 80)
        else:
            print(f"❌ Patient report failed: {patient_report_response.text}")

        # Step 6: Generate Physician Report
        print("\n[6/6] Generating PHYSICIAN REPORT...")
        print("-" * 80)

        physician_report_response = await client.post(
            f"{BASE_URL}/report/physician",
            json={
                "consultation_id": consultation_id,
                "language": "en"
            }
        )

        if physician_report_response.is_success:
            physician_data = physician_report_response.json()
            print("\n📋 PHYSICIAN REPORT (Medical Format with AI Analysis):")
            print("=" * 80)
            print(physician_data.get("report_text", "No report text"))
            print("=" * 80)

            # Check if MedGemma and Qdrant sections are included
            report_text = physician_data.get("report_text", "")
            if "MedGemma" in report_text:
                print("\n✅ MedGemma AI Analysis section FOUND in physician report")
            else:
                print("\n⚠️  MedGemma AI Analysis section NOT found in physician report")

            if "Qdrant" in report_text or "Similar Historical Cases" in report_text:
                print("✅ Qdrant Similar Cases section FOUND in physician report")
            else:
                print("⚠️  Qdrant Similar Cases section NOT found in physician report")
        else:
            print(f"❌ Physician report failed: {physician_report_response.text}")

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Consultation ID: {consultation_id}")
        print(f"Patient Report: {'✅ Generated' if patient_report_response.is_success else '❌ Failed'}")
        print(f"Physician Report: {'✅ Generated' if physician_report_response.is_success else '❌ Failed'}")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(test_report_generation())
