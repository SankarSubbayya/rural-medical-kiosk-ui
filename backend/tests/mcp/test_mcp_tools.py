"""
Comprehensive tests for all 7 MCP tools.
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestConsultationTool:
    """Tests for consultation_tool."""

    @pytest.mark.asyncio
    async def test_create_consultation(self):
        """Test creating a new consultation."""
        from mcp_server.tools import consultation_tool

        result = await consultation_tool.run(
            operation="create",
            patient_id="test_patient_123",
            language="en"
        )

        assert result["success"] is True
        assert "consultation_id" in result
        assert result["patient_id"] == "test_patient_123"
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_get_consultation(self):
        """Test retrieving consultation details."""
        from mcp_server.tools import consultation_tool

        # First create
        create_result = await consultation_tool.run(
            operation="create",
            patient_id="test_patient_456"
        )

        # Then retrieve
        result = await consultation_tool.run(
            operation="get",
            consultation_id=create_result["consultation_id"]
        )

        assert result["success"] is True
        assert result["consultation_id"] == create_result["consultation_id"]


class TestMedicalTool:
    """Tests for medical_tool."""

    @pytest.mark.asyncio
    @pytest.mark.requires_ollama
    async def test_extract_symptoms(self):
        """Test symptom extraction from patient message."""
        from mcp_server.tools import medical_tool

        result = await medical_tool.run(
            operation="extract_symptoms",
            patient_message="I have a red itchy rash on my arm for 3 days",
            language="en"
        )

        assert result["success"] is True
        assert "symptoms" in result
        assert isinstance(result["symptoms"], list)

    @pytest.mark.asyncio
    @pytest.mark.requires_ollama
    async def test_common_sense_check(self):
        """Test common sense medical check."""
        from mcp_server.tools import medical_tool

        result = await medical_tool.run(
            operation="check_common_sense",
            symptom_description="itchy rash on forearm",
            language="en"
        )

        assert result["success"] is True
        assert "is_sensible" in result or "makes_sense" in result


class TestMedGemmaTool:
    """Tests for medgemma_tool."""

    @pytest.mark.asyncio
    @pytest.mark.requires_ollama
    async def test_analyze_image(self, sample_image_base64):
        """Test image analysis with MedGemma."""
        from mcp_server.tools import medgemma_tool

        result = await medgemma_tool.run(
            operation="analyze_image",
            image_base64=sample_image_base64,
            clinical_context="Patient reports itchy rash",
            language="en"
        )

        assert result["success"] is True
        assert "analysis" in result
        assert "predictions" in result["analysis"]


class TestRAGTool:
    """Tests for rag_tool."""

    @pytest.mark.asyncio
    @pytest.mark.requires_qdrant
    async def test_find_similar_cases(self):
        """Test finding similar cases via RAG."""
        from mcp_server.tools import rag_tool

        result = await rag_tool.run(
            operation="find_similar_cases",
            symptoms=["rash", "itching"],
            top_k=3
        )

        assert result["success"] is True
        assert "similar_cases" in result
        assert isinstance(result["similar_cases"], list)


class TestSafetyTool:
    """Tests for safety_tool."""

    @pytest.mark.asyncio
    async def test_check_message_safety(self):
        """Test message safety check."""
        from mcp_server.tools import safety_tool

        result = await safety_tool.run(
            operation="check_message",
            message="I have a mild rash",
            language="en"
        )

        assert result["success"] is True
        assert "is_safe" in result
        assert "flags" in result

    @pytest.mark.asyncio
    async def test_check_condition_criticality(self):
        """Test condition criticality check."""
        from mcp_server.tools import safety_tool

        result = await safety_tool.run(
            operation="check_critical",
            conditions=["Contact Dermatitis", "Eczema"]
        )

        assert result["success"] is True
        assert "is_critical" in result
        assert "has_critical" in result
        assert "critical_conditions" in result


class TestSigLIPRAGTool:
    """Tests for siglip_rag_tool."""

    @pytest.mark.asyncio
    @pytest.mark.requires_qdrant
    async def test_search_by_image(self, sample_image_base64):
        """Test image-based case search."""
        from mcp_server.tools import siglip_rag_tool

        result = await siglip_rag_tool.run(
            operation="search_by_image",
            image_base64=sample_image_base64,
            top_k=3,
            min_score=0.7
        )

        assert result["success"] is True
        assert "similar_cases" in result
        assert result["embedding_model"] == "google/siglip-base-patch16-224"


class TestSpeechTool:
    """Tests for speech_tool."""

    @pytest.mark.asyncio
    async def test_synthesize_speech(self):
        """Test text-to-speech synthesis."""
        from mcp_server.tools import speech_tool

        result = await speech_tool.run(
            operation="synthesize",
            text="Hello, how can I help you today?",
            language="en"
        )

        assert result["success"] is True
        assert "audio_base64" in result

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires real audio file, not fake base64")
    async def test_transcribe_audio(self):
        """Test speech-to-text transcription."""
        from mcp_server.tools import speech_tool

        # This test is skipped because it requires a real audio file
        # Whisper validates the audio format before processing
        pass
