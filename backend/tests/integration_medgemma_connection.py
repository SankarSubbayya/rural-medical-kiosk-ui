#!/usr/bin/env python3
"""
Test script to verify Ollama connection and MedGemma model for medical image analysis.

Run with:
    cd backend
    uv run python tests/test_medgemma_connection.py
"""
import asyncio
import sys
import base64
from pathlib import Path
from io import BytesIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import ollama
from app.config import get_settings

# Try to import PIL for image creation
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def create_test_image():
    """Create a simple test image (red square simulating a rash)."""
    if not HAS_PIL:
        return None

    # Create a 512x512 image with a red patch
    img = Image.new('RGB', (512, 512), color='beige')
    draw = ImageDraw.Draw(img)

    # Draw a red irregular patch (simulating a rash)
    draw.ellipse([150, 150, 350, 350], fill='red', outline='darkred', width=3)
    draw.ellipse([180, 180, 300, 280], fill='pink')

    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


async def test_ollama_connection():
    """Test basic Ollama server connection."""
    print("\n" + "=" * 70)
    print("TEST 1: Ollama Server Connection")
    print("=" * 70)

    settings = get_settings()

    try:
        client = ollama.AsyncClient(host=settings.ollama_base_url)
        models = await client.list()
        print(f"✓ Connected to Ollama at {settings.ollama_base_url}")
        model_count = len(models.models) if hasattr(models, 'models') else len(models['models'])
        print(f"✓ Found {model_count} available models")
        return client, models
    except Exception as e:
        print(f"✗ Failed to connect to Ollama: {e}")
        print(f"  Make sure Ollama is running: ollama serve")
        return None, None


async def test_medgemma_availability(models):
    """Test if MedGemma model is available."""
    print("\n" + "=" * 70)
    print("TEST 2: MedGemma Model Availability")
    print("=" * 70)

    settings = get_settings()

    if models is None:
        print("✗ Skipped (server not connected)")
        return False

    # Handle both dict and object responses
    try:
        if hasattr(models, 'models'):
            model_list = models.models
        else:
            model_list = models['models']

        # Extract model names
        model_names = []
        for m in model_list:
            if hasattr(m, 'model'):
                model_names.append(m.model)
            elif hasattr(m, 'name'):
                model_names.append(m.name)
            else:
                model_names.append(m.get('model', m.get('name', 'unknown')))
    except Exception as e:
        print(f"✗ Error parsing models: {e}")
        return False

    print(f"\nLooking for MedGemma models:")
    medgemma_models = [m for m in model_names if 'medgemma' in m.lower()]

    if medgemma_models:
        print(f"✓ Found {len(medgemma_models)} MedGemma model(s):")
        for model in medgemma_models:
            marker = "✓" if model == settings.ollama_medgemma_model else " "
            print(f"  {marker} {model}")
    else:
        print("✗ No MedGemma models found")

    # Check for configured model
    if settings.ollama_medgemma_model in model_names:
        print(f"\n✓ Configured model '{settings.ollama_medgemma_model}' is available")
        return True
    else:
        print(f"\n✗ Configured model '{settings.ollama_medgemma_model}' NOT found!")
        print(f"\nTo install it, run:")
        print(f"  ollama pull {settings.ollama_medgemma_model}")

        # Check for fallback
        if settings.ollama_vision_model in model_names:
            print(f"\nNote: Fallback vision model '{settings.ollama_vision_model}' is available")

        return False


async def test_vision_without_image(client):
    """Test MedGemma with a text-only medical query."""
    print("\n" + "=" * 70)
    print("TEST 3: Text-Only Medical Query")
    print("=" * 70)

    settings = get_settings()

    if client is None:
        print("✗ Skipped (server not connected)")
        return False

    medical_query = "Describe the typical appearance of eczema on skin."

    print(f"\nSending text query to {settings.ollama_medgemma_model}...")
    print(f"Query: \"{medical_query}\"")

    try:
        response = await client.chat(
            model=settings.ollama_medgemma_model,
            messages=[
                {
                    "role": "user",
                    "content": medical_query
                }
            ],
            options={"temperature": 0.3}
        )

        response_text = response['message']['content']
        print(f"\n✓ Response received ({len(response_text)} chars):")
        print(f"  {response_text[:300]}..." if len(response_text) > 300 else f"  {response_text}")

        return True

    except Exception as e:
        print(f"\n✗ Text query failed: {e}")
        return False


async def test_vision_with_image(client):
    """Test MedGemma with an image (if PIL available)."""
    print("\n" + "=" * 70)
    print("TEST 4: Image Analysis (Vision)")
    print("=" * 70)

    settings = get_settings()

    if client is None:
        print("✗ Skipped (server not connected)")
        return False

    if not HAS_PIL:
        print("✗ Skipped (PIL not available to create test image)")
        print("  Install with: uv pip install Pillow")
        return None  # Not a failure, just skipped

    # Create test image
    print("\nCreating test image (simulated skin rash)...")
    image_base64 = create_test_image()

    if not image_base64:
        print("✗ Failed to create test image")
        return False

    print("✓ Test image created")

    medical_prompt = "Analyze this skin image. What do you observe? Describe any visible characteristics."

    print(f"\nSending image + prompt to {settings.ollama_medgemma_model}...")
    print(f"Prompt: \"{medical_prompt}\"")

    try:
        response = await client.chat(
            model=settings.ollama_medgemma_model,
            messages=[
                {
                    "role": "user",
                    "content": medical_prompt,
                    "images": [image_base64]
                }
            ],
            options={"temperature": 0.3}
        )

        response_text = response['message']['content']
        print(f"\n✓ Vision response received ({len(response_text)} chars):")
        print(f"  {response_text[:300]}..." if len(response_text) > 300 else f"  {response_text}")

        return True

    except Exception as e:
        print(f"\n✗ Vision analysis failed: {e}")
        print(f"\nNote: Some MedGemma models may not support vision.")
        print(f"      Trying fallback model '{settings.ollama_vision_model}'...")

        # Try with fallback
        try:
            response = await client.chat(
                model=settings.ollama_vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": medical_prompt,
                        "images": [image_base64]
                    }
                ],
                options={"temperature": 0.3}
            )

            response_text = response['message']['content']
            print(f"\n✓ Fallback vision response received ({len(response_text)} chars):")
            print(f"  {response_text[:300]}..." if len(response_text) > 300 else f"  {response_text}")

            return True

        except Exception as e2:
            print(f"\n✗ Fallback also failed: {e2}")
            return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MEDGEMMA VISION MODEL TEST")
    print("=" * 70)

    results = []

    # Test 1: Connection
    client, models = await test_ollama_connection()
    results.append(("Ollama Connection", client is not None))

    # Test 2: Model availability
    if client:
        model_available = await test_medgemma_availability(models)
        results.append(("MedGemma Availability", model_available))

        # Test 3: Text query
        if model_available:
            text_works = await test_vision_without_image(client)
            results.append(("Text Medical Query", text_works))

            # Test 4: Vision query
            if text_works:
                vision_result = await test_vision_with_image(client)
                if vision_result is not None:
                    results.append(("Image Analysis", vision_result))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for i, (name, result) in enumerate(results, 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i}. {name}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! MedGemma is working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
