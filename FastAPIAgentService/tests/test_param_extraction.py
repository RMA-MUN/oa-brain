import pytest
from app.agent.main_agent import MainAgent
from app.agent.base import AgentState


def test_param_extraction_from_text():
    """测试从文本中提取参数"""
    agent = MainAgent()
    
    # 测试用例1：包含日期和地点的文本
    text = "我想在明天下午3点在会议室A开会"
    required_params = ["日期", "地点"]
    extracted = agent._extract_params_from_text(text, required_params)
    
    assert "日期" in extracted
    assert "地点" in extracted
    assert "明天下午3点" in extracted["日期"]
