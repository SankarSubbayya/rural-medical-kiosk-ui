#!/usr/bin/env python3
"""
Test script to verify Ollama connection and gpt-oss:20b model.

Run with:
    cd backend
    uv run python tests/test_ollama_connection.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import ollama
from app.config import get_settings


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


async def test_model_availability(models):
    """Test if gpt-oss:20b is available."""
    print("\n" + "=" * 70)
    print("TEST 2: Model Availability (gpt-oss:20b)")
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

        # Extract model names (handle both dict and object)
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
        print(f"  Models structure: {models}")
        return False

    print(f"\nAvailable models:")
    for name in model_names:
        marker = "✓" if name == settings.ollama_chat_model else " "
        print(f"  {marker} {name}")

    if settings.ollama_chat_model in model_names:
        print(f"\n✓ Model '{settings.ollama_chat_model}' is available")
        return True
    else:
        print(f"\n✗ Model '{settings.ollama_chat_model}' NOT found!")
        print(f"\nTo install it, run:")
        print(f"  ollama pull {settings.ollama_chat_model}")
        return False


async def test_chat_completion(client):
    """Test chat completion with gpt-oss:20b."""
    print("\n" + "=" * 70)
    print("TEST 3: Chat Completion")
    print("=" * 70)

    settings = get_settings()

    if client is None:
        print("✗ Skipped (server not connected)")
        return False

    test_prompt = "Say 'Hello from the medical kiosk backend!' in one sentence."

    print(f"\nSending test prompt to {settings.ollama_chat_model}...")
    print(f"Prompt: \"{test_prompt}\"")

    try:
        response = await client.chat(
            model=settings.ollama_chat_model,
            messages=[
                {
                    "role": "user",
                    "content": test_prompt
                }
            ],
            options={"temperature": 0.7}
        )

        response_text = response['message']['content']
        print(f"\n✓ Response received:")
        print(f"  \"{response_text}\"")

        return True

    except Exception as e:
        print(f"\n✗ Chat completion failed: {e}")
        return False


async def test_medical_prompt(client):
    """Test with a medical-related prompt."""
    print("\n" + "=" * 70)
    print("TEST 4: Medical Context Understanding")
    print("=" * 70)

    settings = get_settings()

    if client is None:
        print("✗ Skipped (server not connected)")
        return False

    medical_prompt = "A patient reports a red, itchy rash on their arm for 3 days. What information would be helpful to gather?"

    print(f"\nSending medical prompt to {settings.ollama_chat_model}...")
    print(f"Prompt: \"{medical_prompt}\"")

    try:
        response = await client.chat(
            model=settings.ollama_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful medical assistant helping gather information for a doctor."
                },
                {
                    "role": "user",
                    "content": medical_prompt
                }
            ],
            options={"temperature": 0.3}
        )

        response_text = response['message']['content']
        print(f"\n✓ Response received:")
        print(f"  {response_text[:200]}..." if len(response_text) > 200 else f"  {response_text}")

        return True

    except Exception as e:
        print(f"\n✗ Medical prompt test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("OLLAMA GPT-OSS CONNECTION TEST")
    print("=" * 70)

    results = []

    # Test 1: Connection
    client, models = await test_ollama_connection()
    results.append(client is not None)

    # Test 2: Model availability
    if client:
        model_available = await test_model_availability(models)
        results.append(model_available)

        # Test 3: Basic chat
        if model_available:
            chat_works = await test_chat_completion(client)
            results.append(chat_works)

            # Test 4: Medical prompt
            if chat_works:
                medical_works = await test_medical_prompt(client)
                results.append(medical_works)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    test_names = [
        "Ollama Connection",
        "Model Availability",
        "Chat Completion",
        "Medical Context"
    ]

    for i, (name, result) in enumerate(zip(test_names[:len(results)], results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i}. {name}: {status}")

    passed = sum(results)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! gpt-oss:20b is working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
