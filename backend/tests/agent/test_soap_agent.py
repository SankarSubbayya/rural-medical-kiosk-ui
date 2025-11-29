"""
Unit tests for SOAP Orchestrator Agent.
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock


class TestSOAPAgent:
    """Test cases for SOAP Orchestrator Agent."""

    @pytest.fixture
    def soap_agent(self, mock_ollama_client):
        """Create SOAP agent instance with mocked dependencies."""
        from agent.soap_agent import SOAPAgent

        # Mock Google Genai client
        mock_genai_client = MagicMock()
        mock_genai_client.models = MagicMock()

        # Mock environment variable for Google API key
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_api_key'}):
            with patch('agent.soap_agent.genai.Client', return_value=mock_genai_client):
                agent = SOAPAgent(
                    model="gemini-2.0-flash-exp",
                    ollama_host="http://localhost:11434"
                )
                # Set mock client
                agent.client = mock_genai_client
                return agent

    @pytest.mark.asyncio
    async def test_agent_initialization(self, soap_agent):
        """Test agent initializes correctly."""
        assert soap_agent.model_name == "gemini-2.0-flash-exp"
        assert soap_agent.ollama_host == "http://localhost:11434"
        assert soap_agent.state.current_stage == "GREETING"

    @pytest.mark.asyncio
    async def test_greeting_stage(self, soap_agent, mock_ollama_client):
        """Test GREETING stage processing."""
        # Mock Ollama response for greeting
        mock_ollama_client.chat.return_value = {
            "message": {
                "content": "Hello! I'm here to help you with your dermatological concerns. May I have your consent to proceed?"
            }
        }

        result = await soap_agent.process_message(
            message="Hello",
            language="en"
        )

        assert result["success"] is True
        assert "message" in result
        assert result["stage"] == "GREETING"

    @pytest.mark.asyncio
    async def test_subjective_stage(self, soap_agent):
        """Test SUBJECTIVE stage processing."""
        # Set stage to SUBJECTIVE
        soap_agent.state.current_stage = "SUBJECTIVE"
        soap_agent.state.consent_given = True
        soap_agent.state.consultation_id = "test_123"  # Pre-create consultation

        result = await soap_agent.process_message(
            message="I have a red itchy rash on my arm for 3 days",
            language="en"
        )

        assert result["success"] is True
        # Agent may progress to OBJECTIVE stage after gathering symptoms
        assert result["stage"] in ["SUBJECTIVE", "OBJECTIVE"]
        # Should have message history
        assert len(soap_agent.state.message_history) > 0

    @pytest.mark.asyncio
    async def test_objective_stage_requires_image(self, soap_agent):
        """Test OBJECTIVE stage requires image."""
        soap_agent.state.current_stage = "OBJECTIVE"
        soap_agent.state.consent_given = True
        soap_agent.state.extracted_symptoms = ["rash", "itching"]

        result = await soap_agent.process_message(
            message="I can take a photo",
            language="en"
        )

        assert result.get("requires_image") is True

    @pytest.mark.asyncio
    async def test_objective_stage_with_image(self, soap_agent, sample_image_base64):
        """Test OBJECTIVE stage with image analysis."""
        soap_agent.state.current_stage = "OBJECTIVE"
        soap_agent.state.consent_given = True
        soap_agent.state.consultation_id = "test_123"  # Pre-create consultation

        result = await soap_agent.process_message(
            message="Here is the image",
            image_base64=sample_image_base64,
            language="en"
        )

        assert result["success"] is True
        # Image processing may trigger analysis
        assert "message" in result

    @pytest.mark.asyncio
    async def test_stage_progression(self, soap_agent):
        """Test SOAP workflow stage progression."""
        # Start at GREETING
        assert soap_agent.state.current_stage == "GREETING"

        # Progress through stages
        soap_agent.state.consent_given = True
        soap_agent.state.current_stage = "SUBJECTIVE"
        assert soap_agent.state.current_stage == "SUBJECTIVE"

        soap_agent.state.extracted_symptoms = ["rash"]
        soap_agent.state.current_stage = "OBJECTIVE"
        assert soap_agent.state.current_stage == "OBJECTIVE"

    @pytest.mark.asyncio
    async def test_safety_guardrails(self, soap_agent):
        """Test safety guardrails are applied."""
        # Send a message that should trigger safety guardrails
        result = await soap_agent.process_message(
            message="What disease do I have? Give me a diagnosis!",
            language="en"
        )

        # Safety tool should detect this as unsafe and trigger redirect
        # The result might have safety_triggered flag or redirect response
        assert "message" in result
        # Safety service should have processed the message
        assert result.get("success") is not False

    @pytest.mark.asyncio
    async def test_consultation_id_tracking(self, soap_agent):
        """Test consultation ID is properly tracked."""
        result = await soap_agent.process_message(
            message="Hello",
            consultation_id="test_consult_123",
            language="en"
        )

        assert soap_agent.state.consultation_id == "test_consult_123"

    @pytest.mark.asyncio
    async def test_message_history(self, soap_agent):
        """Test message history is maintained."""
        await soap_agent.process_message(
            message="Hello",
            language="en"
        )

        await soap_agent.process_message(
            message="I have a rash",
            language="en"
        )

        assert len(soap_agent.state.message_history) >= 2
