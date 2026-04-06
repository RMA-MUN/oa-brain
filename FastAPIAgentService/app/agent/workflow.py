from typing import Dict, Any, TypedDict, Literal
from langgraph.graph import StateGraph, END
from app.agent.main_agent import MainAgent
from app.core.logger_handler import logger


class WorkflowState(TypedDict):
    """工作流状态定义"""
    user_input: str
    session_id: str
    user_id: str
    response: str
    steps: list
    error: str


class AgentWorkflow:
    """
    多智能体工作流管理器
    """
    
    def __init__(self):
        self.main_agent = MainAgent()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """构建工作流"""
        graph = StateGraph(WorkflowState)
        
        # 添加节点
        graph.add_node("process_input", self._process_input)
        
        # 添加边
        graph.set_entry_point("process_input")
        graph.add_edge("process_input", END)
        
        return graph.compile()
    
    async def _process_input(self, state: WorkflowState) -> Dict[str, Any]:
        """处理用户输入"""
        try:
            logger.info(f"【工作流】开始处理输入，用户ID: {state['user_id']}, 会话ID: {state['session_id']}")
            
            # 调用主Agent处理输入
            result = await self.main_agent.process_input(
                user_input=state["user_input"],
                session_id=state["session_id"],
                user_id=state["user_id"]
            )
            
            logger.info(f"【工作流】处理完成，会话ID: {state['session_id']}")
            
            return {
                "response": result.get("response", "处理完成"),
                "steps": result.get("steps", []),
                "error": result.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"【工作流】处理失败: {str(e)}", exc_info=True)
            return {
                "response": f"处理失败: {str(e)}",
                "steps": [],
                "error": str(e)
            }
    
    async def run(self, user_input: str, session_id: str, user_id: str) -> Dict[str, Any]:
        """运行工作流"""
        try:
            # 初始化状态
            initial_state = {
                "user_input": user_input,
                "session_id": session_id,
                "user_id": user_id,
                "response": "",
                "steps": [],
                "error": ""
            }
            
            # 执行工作流
            result = await self.workflow.ainvoke(initial_state)
            
            return {
                "response": result.get("response"),
                "steps": result.get("steps"),
                "session_id": session_id,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"【工作流】运行失败: {str(e)}", exc_info=True)
            return {
                "response": f"工作流执行失败: {str(e)}",
                "steps": [],
                "session_id": session_id,
                "error": str(e)
            }


# 全局工作流实例
workflow = AgentWorkflow()


async def run_agent_workflow(user_input: str, session_id: str, user_id: str) -> Dict[str, Any]:
    """
    运行Agent工作流
    
    :param user_input: 用户输入
    :param session_id: 会话ID
    :param user_id: 用户ID
    :return: 处理结果
    """
    return await workflow.run(user_input, session_id, user_id)