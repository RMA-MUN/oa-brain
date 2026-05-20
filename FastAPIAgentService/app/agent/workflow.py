from typing import Dict, Any, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, END
from app.agent.main_agent import MainAgent
from app.agent.base import AgentState
from app.core.logger_handler import logger


class WorkflowState(TypedDict):
    user_input: str
    session_id: str
    user_id: str
    jwt_token: Optional[str]
    chat_history: Optional[list]
    task_type: Optional[str]
    task_subtasks: Optional[list]
    agent_results: dict
    final_response: Optional[str]
    error: Optional[str]


class AgentWorkflow:
    def __init__(self, main_agent: Optional[MainAgent] = None):
        self.main_agent = main_agent or MainAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(WorkflowState)

        graph.add_node("get_session_history", self._node_get_session_history)
        graph.add_node("decompose_task", self._node_decompose_task)
        graph.add_node("execute_subtasks", self._node_execute_subtasks)
        graph.add_node("integrate_results", self._node_integrate_results)
        graph.add_node("save_memory", self._node_save_memory)

        graph.set_entry_point("get_session_history")
        graph.add_edge("get_session_history", "decompose_task")

        graph.add_conditional_edges(
            "decompose_task",
            self._route_after_decompose,
            {
                "execute_subtasks": "execute_subtasks",
                "integrate_results": "integrate_results",
            },
        )

        graph.add_conditional_edges(
            "execute_subtasks",
            self._route_after_execute,
            {
                "integrate_results": "integrate_results",
                "save_memory": "save_memory",
            },
        )

        graph.add_edge("integrate_results", "save_memory")
        graph.add_edge("save_memory", END)

        return graph.compile()

    @staticmethod
    def _to_agent_state(state: WorkflowState) -> AgentState:
        s = AgentState()
        s.user_input = state["user_input"]
        s.session_id = state["session_id"]
        s.user_id = state["user_id"]
        s.jwt_token = state.get("jwt_token")
        s.chat_history = state.get("chat_history")
        s.task_type = state.get("task_type")
        s.task_subtasks = state.get("task_subtasks")
        s.agent_results = state.get("agent_results", {})
        s.final_response = state.get("final_response")
        s.error = state.get("error")
        return s

    @staticmethod
    def _from_agent_state(s: AgentState) -> Dict[str, Any]:
        return {
            "chat_history": s.chat_history,
            "task_type": s.task_type,
            "task_subtasks": s.task_subtasks,
            "agent_results": s.agent_results,
            "final_response": s.final_response,
            "error": s.error,
        }

    async def _node_get_session_history(self, state: WorkflowState) -> Dict[str, Any]:
        s = self._to_agent_state(state)
        s = await self.main_agent._get_session_history(s)
        return self._from_agent_state(s)

    async def _node_decompose_task(self, state: WorkflowState) -> Dict[str, Any]:
        s = self._to_agent_state(state)
        s = await self.main_agent._decompose_task(s)
        return self._from_agent_state(s)

    async def _node_execute_subtasks(self, state: WorkflowState) -> Dict[str, Any]:
        s = self._to_agent_state(state)
        s = await self.main_agent._execute_subtasks(s)
        return self._from_agent_state(s)

    async def _node_integrate_results(self, state: WorkflowState) -> Dict[str, Any]:
        s = self._to_agent_state(state)
        s = await self.main_agent._integrate_results(s)
        return self._from_agent_state(s)

    async def _node_save_memory(self, state: WorkflowState) -> Dict[str, Any]:
        s = self._to_agent_state(state)
        await self.main_agent._save_memory(s)
        return {}

    @staticmethod
    def _route_after_decompose(state: WorkflowState) -> Literal["execute_subtasks", "integrate_results"]:
        if state.get("task_subtasks"):
            return "execute_subtasks"
        return "integrate_results"

    @staticmethod
    def _route_after_execute(state: WorkflowState) -> Literal["integrate_results", "save_memory"]:
        if state.get("final_response"):
            return "save_memory"
        return "integrate_results"

    async def run(
        self, user_input: str, session_id: str, user_id: str, jwt_token: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            initial_state: WorkflowState = {
                "user_input": user_input,
                "session_id": session_id,
                "user_id": user_id,
                "jwt_token": jwt_token,
                "chat_history": None,
                "task_type": None,
                "task_subtasks": None,
                "agent_results": {},
                "final_response": None,
                "error": None,
            }

            result = await self.graph.ainvoke(initial_state)

            return {
                "response": result.get("final_response") or "处理完成",
                "steps": result.get("agent_results", {}),
                "session_id": session_id,
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"【工作流】运行失败: {str(e)}", exc_info=True)
            return {
                "response": f"工作流执行失败: {str(e)}",
                "steps": [],
                "session_id": session_id,
                "error": str(e),
            }

workflow = AgentWorkflow()


async def run_agent_workflow(
    user_input: str, session_id: str, user_id: str, jwt_token: Optional[str] = None
) -> Dict[str, Any]:
    return await workflow.run(user_input, session_id, user_id, jwt_token)
