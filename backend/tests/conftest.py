"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app_client():
    """Create FastAPI test client."""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Sample base64 image for testing."""
    # Generate a 224x224 red image (minimum size for SigLIP)
    import base64
    from PIL import Image
    import io

    img = Image.new('RGB', (224, 224), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return base64.b64encode(buffer.getvalue()).decode()


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for agent tests."""
    client = AsyncMock()
    client.chat = AsyncMock(return_value={
        "message": {
            "content": "Test response from Ollama"
        }
    })
    return client


@pytest.fixture
def sample_consultation_data():
    """Sample consultation data for testing."""
    return {
        "patient_id": "test_patient_123",
        "language": "en",
        "symptoms": ["rash", "itching", "redness"],
        "duration": "3 days"
    }


@pytest.fixture
def sample_analysis_result():
    """Sample image analysis result."""
    return {
        "visual_description": "Red, inflamed skin with raised bumps",
        "predictions": [
            {
                "condition": "Contact Dermatitis",
                "confidence": 0.85,
                "description": "Inflammatory skin condition"
            },
            {
                "condition": "Eczema",
                "confidence": 0.72,
                "description": "Chronic skin inflammation"
            }
        ],
        "risk_assessment": "Low",
        "recommendations": ["Avoid irritants", "Apply moisturizer"]
    }


@pytest.fixture
def sample_rag_cases():
    """Sample similar cases from RAG."""
    return [
        {
            "case_id": "case_001",
            "diagnosis": "Contact Dermatitis",
            "similarity_score": 0.92,
            "symptoms": ["rash", "redness"],
            "treatment": "Topical corticosteroids",
            "outcome": "Resolved in 7 days"
        },
        {
            "case_id": "case_002",
            "diagnosis": "Allergic Reaction",
            "similarity_score": 0.88,
            "symptoms": ["itching", "redness", "swelling"],
            "treatment": "Antihistamines",
            "outcome": "Improved in 3 days"
        }
    ]


# Pytest markers for integration tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "requires_ollama: marks tests as requiring Ollama server"
    )
    config.addinivalue_line(
        "markers", "requires_qdrant: marks tests as requiring Qdrant server"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
