from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.messages import BaseMessage


class BaseAgent(ABC):
    """
    Agent 基类，定义所有 Agent 的基本接口
    """
    
    def __init__(self, name: str):
        """
        初始化 Agent
        
        :param name: Agent 名称
        """
        self.name = name
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        :param input_data: 输入数据字典
        :return: 处理结果字典
        """
        pass
    
    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        """
        判断是否能够处理特定类型的任务
        
        :param task_type: 任务类型
        :return: 是否能够处理
        """
        pass
    
    def get_name(self) -> str:
        """
        获取 Agent 名称
        
        :return: Agent 名称
        """
        return self.name


class AgentState:
    """
    Agent 状态管理类
    """
    
    def __init__(self):
        self.user_input: Optional[str] = None
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.chat_history: Optional[list] = None
        self.task_type: Optional[str] = None
        self.task_subtasks: Optional[list] = None
        self.selected_agent: Optional[str] = None
        self.agent_results: Dict[str, Any] = {}
        self.final_response: Optional[str] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        :return: 状态字典
        """
        return {
            "user_input": self.user_input,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "chat_history": self.chat_history,
            "task_type": self.task_type,
            "task_subtasks": self.task_subtasks,
            "selected_agent": self.selected_agent,
            "agent_results": self.agent_results,
            "final_response": self.final_response,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """
        从字典创建状态
        
        :param data: 状态字典
        :return: AgentState 实例
        """
        state = cls()
        state.user_input = data.get("user_input")
        state.session_id = data.get("session_id")
        state.user_id = data.get("user_id")
        state.chat_history = data.get("chat_history")
        state.task_type = data.get("task_type")
        state.task_subtasks = data.get("task_subtasks")
        state.selected_agent = data.get("selected_agent")
        state.agent_results = data.get("agent_results", {})
        state.final_response = data.get("final_response")
        state.error = data.get("error")
        return state