import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


def test_health_check(client):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch('app.api.chat.MainAgent')
def test_chat_endpoint(mock_main_agent, client):
    """测试对话接口"""
    mock_agent_instance = MagicMock()
    mock_main_agent.return_value = mock_agent_instance
    mock_agent_instance.process_input.return_value = {
        "response": "Test response",
        "timestamp": "2024-01-01T00:00:00"
    }
    
    response = client.post(
        "/api/agent/chat/",
        json={"message": "test", "session_id": "session123"},
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    assert response.json()["response"] == "Test response"
