import pytest
from unittest.mock import patch, MagicMock
from app.tools.attendance_tool import AttendanceTool


def test_attendance_tool_run():
    """测试考勤工具运行"""
    with patch('app.tools.attendance_tool.DjangoAPIClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.call_api.return_value = {"success": True}
        
        tool = AttendanceTool()
        result = tool.run("apply", "user123", date="2024-01-01")
        
        assert result == {"success": True}
        mock_client.call_api.assert_called_once_with(
            "attendance/apply",
            {"user_id": "user123", "date": "2024-01-01"}
        )


def test_attendance_tool_invalid_action():
    """测试考勤工具无效操作"""
    tool = AttendanceTool()
    result = tool.run("invalid_action", "user123")
    
    assert result == {"error": "Invalid action"}
