import pytest
from unittest.mock import patch, MagicMock
from app.agents.main_agent import MainAgent


@pytest.mark.asyncio
async def test_main_agent_process_input():
    """测试主Agent处理输入"""
    with patch('app.agents.main_agent.workflow') as mock_workflow:
        mock_workflow.ainvoke.return_value = {
            "response": "Test response",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        agent = MainAgent()
        result = await agent.process_input("test input", "session123", "user456")
        
        assert result["response"] == "Test response"
        assert result["timestamp"] == "2024-01-01T00:00:00"
        mock_workflow.ainvoke.assert_called_once_with({
            "user_input": "test input",
            "session_id": "session123",
            "user_id": "user456"
        })
