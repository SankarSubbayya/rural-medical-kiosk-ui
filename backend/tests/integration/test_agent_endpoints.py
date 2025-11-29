"""
Integration tests for /agent endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock


class TestAgentEndpoints:
    """Test cases for agent FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_agent_message_text_only(self, app_client):
        """Test /agent/message with text-only input."""
        with patch('app.routers.agent.create_soap_agent') as mock_create_agent:
            # Mock agent
            mock_agent = AsyncMock()
            mock_agent.process_message.return_value = {
                "success": True,
                "message": "Hello! I'm here to help.",
                "stage": "GREETING",
                "suggested_actions": [],
                "requires_image": False
            }
            mock_agent.state.consultation_id = "test_123"
            mock_agent.state.current_stage = "GREETING"
            mock_agent.state.language = "en"
            mock_create_agent.return_value = mock_agent

            response = app_client.post(
                "/agent/message",
                json={
                    "message": "Hello",
                    "language": "en"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert data["current_stage"] == "GREETING"

    @pytest.mark.asyncio
    async def test_agent_message_with_image(self, app_client, sample_image_base64):
        """Test /agent/message with image input."""
        with patch('app.routers.agent.create_soap_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_agent.process_message.return_value = {
                "success": True,
                "message": "I've analyzed the image.",
                "stage": "OBJECTIVE",
                "analysis": {
                    "visual_description": "Red lesion",
                    "predictions": [{
                        "condition": "Contact Dermatitis",
                        "confidence": 0.85
                    }]
                },
                "requires_image": False
            }
            mock_agent.state.consultation_id = "test_123"
            mock_agent.state.current_stage = "OBJECTIVE"
            mock_agent.state.language = "en"
            mock_create_agent.return_value = mock_agent

            response = app_client.post(
                "/agent/message",
                json={
                    "message": "Here is the affected area",
                    "image_base64": sample_image_base64,
                    "language": "en"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data

    @pytest.mark.asyncio
    async def test_agent_consultation_state(self, app_client):
        """Test GET /agent/consultation/{id} endpoint."""
        # Create a proper mock agent with ConsultationState
        from agent.soap_agent import ConsultationState
        mock_agent = AsyncMock()
        mock_agent.state = ConsultationState()
        mock_agent.state.consultation_id = "test_123"
        mock_agent.state.patient_id = "patient_456"
        mock_agent.state.language = "en"
        mock_agent.state.current_stage = "SUBJECTIVE"
        mock_agent.state.consent_given = True

        with patch('app.routers.agent._agents', {"test_123": mock_agent}):
            response = app_client.get("/agent/consultation/test_123")

        assert response.status_code == 200
        data = response.json()
        assert data["consultation_id"] == "test_123"
        assert data["current_stage"] == "SUBJECTIVE"

    @pytest.mark.asyncio
    async def test_agent_health_check(self, app_client):
        """Test GET /agent/health endpoint."""
        response = app_client.get("/agent/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agent_type" in data
        assert "tools_count" in data

    @pytest.mark.asyncio
    async def test_end_consultation(self, app_client):
        """Test DELETE /agent/consultation/{id} endpoint."""
        with patch('app.routers.agent._agents', {"test_123": AsyncMock()}):
            response = app_client.delete("/agent/consultation/test_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_consultation_not_found(self, app_client):
        """Test 404 when consultation doesn't exist."""
        response = app_client.get("/agent/consultation/nonexistent")

        assert response.status_code == 404
