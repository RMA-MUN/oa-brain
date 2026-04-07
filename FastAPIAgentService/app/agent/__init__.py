"""
多智能体架构模块
"""

# 注意：这里避免在 import-time 直接加载依赖大模型/向量库的模块，
# 防止在仅做类型引用或工具脚本加载时触发沉重依赖/环境变量要求。
from app.agent.base import BaseAgent, AgentState

__all__ = [
    "BaseAgent",
    "AgentState",
    "TaskDecomposer",
    "AgentRouter",
    "ToolAgent",
    "KnowledgeAgent",
    "MemoryAgent",
    "MainAgent",
    "run_agent_workflow",
]


def __getattr__(name: str):
    if name == "TaskDecomposer":
        from app.agent.task_decomposer import TaskDecomposer as _T
        return _T
    if name == "AgentRouter":
        from app.agent.agent_router import AgentRouter as _T
        return _T
    if name == "ToolAgent":
        from app.agent.tool_agent import ToolAgent as _T
        return _T
    if name == "KnowledgeAgent":
        from app.agent.knowledge_agent import KnowledgeAgent as _T
        return _T
    if name == "MemoryAgent":
        from app.agent.memory_agent import MemoryAgent as _T
        return _T
    if name == "MainAgent":
        from app.agent.main_agent import MainAgent as _T
        return _T
    if name == "run_agent_workflow":
        from app.agent.workflow import run_agent_workflow as _T
        return _T
    raise AttributeError(name)