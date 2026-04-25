import json
import os
from typing import Dict, Any, List, Optional

from app.agent.base import BaseAgent, AgentState
from app.agent.task_decomposer import TaskDecomposer
from app.agent.agent_router import AgentRouter
from app.agent.tool_agent import ToolAgent
from app.agent.knowledge_agent import KnowledgeAgent
from app.agent.memory_agent import MemoryAgent
from app.agent.param_extraction_agent import ParamExtractionAgent
from app.core.logger_handler import logger


class MainAgent(BaseAgent):
    """
    主调度Agent，负责协调各个子Agent的工作流程
    """
    
    def __init__(self):
        super().__init__("main_agent")
        self.task_decomposer = TaskDecomposer()
        self.agent_router = AgentRouter()
        self.tool_agent = ToolAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.memory_agent = MemoryAgent()
        self.param_extraction_agent = ParamExtractionAgent()
        
        # 创建Agent映射
        self.agent_map = {
            "task_decomposer": self.task_decomposer,
            "agent_router": self.agent_router,
            "tool_agent": self.tool_agent,
            "knowledge_agent": self.knowledge_agent,
            "memory_agent": self.memory_agent,
            "param_extraction_agent": self.param_extraction_agent,
        }
    
    async def process_input(self, user_input: str, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        处理用户输入，协调工作流程
        
        :param user_input: 用户输入
        :param session_id: 会话ID
        :param user_id: 用户ID
        :return: 处理结果
        """
        try:
            # 初始化状态
            state = AgentState()
            state.user_input = user_input
            state.session_id = session_id
            state.user_id = user_id
            
            logger.info(f"【主Agent】开始处理请求，用户ID: {user_id}, 会话ID: {session_id}, 输入: {user_input[:50]}...")
            
            # 步骤1: 获取会话历史
            state = await self._get_session_history(state)
            
            # 步骤2: 任务分解
            state = await self._decompose_task(state)
            
            # 如果任务分解失败，返回错误
            if not state.task_subtasks:
                return {
                    "response": "抱歉，无法理解您的请求。请重新描述您的需求。",
                    "error": "任务分解失败"
                }
            
            # 步骤3: 执行子任务
            state = await self._execute_subtasks(state)
            
            # 步骤4: 整合结果
            # 如果 final_response 已经被设置（例如，因为参数不完整而需要向用户询问），则跳过整合结果
            if not state.final_response:
                state = await self._integrate_results(state)
            
            # 步骤5: 保存记忆
            await self._save_memory(state)
            
            logger.info(f"【主Agent】处理完成，会话ID: {session_id}")
            
            return {
                "response": state.final_response or "处理完成",
                "steps": state.agent_results,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"【主Agent】处理失败: {str(e)}", exc_info=True)
            return {
                "response": f"抱歉，处理您的请求时出现了错误: {str(e)}",
                "error": str(e)
            }
    
    async def _get_session_history(self, state: AgentState) -> AgentState:
        """获取会话历史"""
        memory_result = await self.memory_agent.process({
            "session_id": state.session_id,
            "user_id": state.user_id,
            "action": "get_history"
        })
        
        if memory_result.get("success"):
            state.chat_history = memory_result.get("history", [])
            logger.info(f"【主Agent】获取会话历史成功，记录数: {len(state.chat_history)}")
        
        return state
    
    async def _decompose_task(self, state: AgentState) -> AgentState:
        """分解任务"""
        decomposition_result = await self.task_decomposer.process({
            "user_input": state.user_input
        })
        
        if decomposition_result.get("success"):
            state.task_type = decomposition_result.get("task_type")
            state.task_subtasks = decomposition_result.get("subtasks", [])
            logger.info(f"【主Agent】任务分解成功，任务类型: {state.task_type}, 子任务数: {len(state.task_subtasks)}")
        else:
            logger.error(f"【主Agent】任务分解失败: {decomposition_result.get('error')}")
        
        return state
    
    async def _execute_subtasks(self, state: AgentState) -> AgentState:
        """执行子任务"""
        ordered_subtasks = self._sort_subtasks(state.task_subtasks or [])
        for idx, subtask in enumerate(ordered_subtasks):
            # 检查参数是否完整（尝试从历史会话和用户输入中提取参数）
            if not await self._check_params_complete(subtask, state):
                # 如果参数不完整，已经在_check_params_complete中设置了final_response
                return state
            
            # 路由到合适的Agent
            route_result = await self.agent_router.process({
                "task_type": subtask["task_type"],
                "subtask_description": subtask["description"],
                "required_params": subtask["required_params"]
            })
            
            if route_result.get("success"):
                selected_agent_id = route_result.get("selected_agent")
                agent = self.agent_map.get(selected_agent_id)
                
                if agent:
                    # 执行子任务
                    task_input = {
                        "task_description": subtask["description"],
                        "params": subtask.get("params", {}),
                        "session_id": state.session_id,
                        "user_id": state.user_id
                    }
                    
                    # 根据不同的Agent添加特定参数
                    if selected_agent_id == "knowledge_agent":
                        task_input["query"] = subtask.get("query", subtask["description"])
                    elif selected_agent_id == "memory_agent":
                        task_input["action"] = subtask.get("action", "get_history")
                    
                    agent_result = await agent.process(task_input)
                    
                    # 保存Agent执行结果
                    state.agent_results[subtask["task_id"]] = {
                        "task": subtask,
                        "agent": selected_agent_id,
                        "result": agent_result
                    }
                    
                    logger.info(f"【主Agent】子任务执行成功: {subtask['task_name']}")

                    # 若当前结果已足以回答用户问题，则直接结束，避免继续无效调用（如多余RAG）
                    if self._can_finalize_after_subtask(subtask, selected_agent_id, agent_result):
                        state.final_response = self._extract_response_from_agent_result(selected_agent_id, agent_result)
                        logger.info("【主Agent】任务已满足，提前结束后续子任务")
                        return state
                else:
                    logger.error(f"【主Agent】未找到路由到的Agent: {selected_agent_id}")
                    state.agent_results[subtask.get("task_id", "unknown")] = {
                        "task": subtask,
                        "agent": selected_agent_id,
                        "result": {"success": False, "error": f"未找到Agent: {selected_agent_id}"}
                    }
            else:
                logger.error(f"【主Agent】子任务路由失败: {route_result.get('error')}")
                state.agent_results[subtask.get("task_id", "unknown")] = {
                    "task": subtask,
                    "agent": None,
                    "result": {"success": False, "error": route_result.get("error", "路由失败")}
                }

            # 最后一个子任务执行后自然退出
            if idx == len(ordered_subtasks) - 1:
                continue
        
        return state

    def _sort_subtasks(self, subtasks: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        按依赖与优先级排序子任务。
        - **先依赖后执行**：dependencies 满足后才执行
        - **同层按 priority 升序**
        若存在依赖缺失/循环依赖，退化为按 priority 升序 + 原顺序，避免整个流程卡死。
        """
        if not subtasks:
            return []

        task_by_id: Dict[str, Dict[str, Any]] = {}
        for t in subtasks:
            tid = t.get("task_id")
            if tid:
                task_by_id[tid] = t

        # 计算入度
        indeg: Dict[str, int] = {t.get("task_id"): 0 for t in subtasks if t.get("task_id")}
        dependents: Dict[str, list[str]] = {tid: [] for tid in indeg.keys()}

        missing_dep = False
        for t in subtasks:
            tid = t.get("task_id")
            if not tid:
                continue
            deps = t.get("dependencies") or []
            for dep in deps:
                if dep not in indeg:
                    missing_dep = True
                    continue
                indeg[tid] += 1
                dependents[dep].append(tid)

        def _priority_key(tid: str):
            t = task_by_id.get(tid, {})
            pr = t.get("priority")
            return (pr if isinstance(pr, int) else 9999)

        # Kahn
        ready = sorted([tid for tid, d in indeg.items() if d == 0], key=_priority_key)
        ordered_ids: list[str] = []
        while ready:
            tid = ready.pop(0)
            ordered_ids.append(tid)
            for nxt in dependents.get(tid, []):
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    ready.append(nxt)
                    ready.sort(key=_priority_key)

        # 检查循环依赖/缺失依赖
        if missing_dep or len(ordered_ids) != len(indeg):
            logger.warning("【主Agent】检测到依赖缺失或循环依赖，退化为按priority排序执行")
            return sorted(subtasks, key=lambda t: (t.get("priority", 9999), subtasks.index(t)))

        # 保留没有 task_id 的子任务（放到最后，按 priority）
        ordered = [task_by_id[tid] for tid in ordered_ids]
        no_id = [t for t in subtasks if not t.get("task_id")]
        if no_id:
            ordered.extend(sorted(no_id, key=lambda t: (t.get("priority", 9999))))
        return ordered
    
    def _strict_params_enabled(self) -> bool:
        return os.getenv("MAIN_AGENT_STRICT_REQUIRED_PARAMS", "false").lower() in (
            "1",
            "true",
            "yes",
        )

    async def _check_params_complete(self, subtask: Dict[str, Any], state: AgentState) -> bool:
        """检查参数是否完整：由参数提取Agent独立完成提取；缺参时默认放行（可严格拦截）。"""
        task_type = subtask.get("task_type", "")
        # 这些类型由子 Agent / 对话本身处理，不在此用 required_params 卡死
        if task_type in (
            "knowledge_query",
            "rag_query",
            "information_summary",
            "user_interaction",
            "memory_management",
        ):
            return True

        required_params = subtask.get("required_params") or []
        if not required_params:
            return True

        extraction_result = await self.param_extraction_agent.process({
            "required_params": list(required_params),
            "existing_params": subtask.get("params") or {},
            "subtask_description": subtask.get("description") or "",
            "task_type": task_type,
            "user_input": state.user_input,
            "chat_history": state.chat_history or [],
        })

        merged_params = extraction_result.get("params") or {}
        if merged_params:
            subtask["params"] = merged_params

        missing_params = extraction_result.get("missing_params") or []
        if not missing_params:
            logger.info(f"【参数检查】所有参数已提取完成: {merged_params}")
            return True

        logger.info(f"【参数检查】仍缺参数: {missing_params}")

        if self._strict_params_enabled():
            state.final_response = (
                f"我需要更多信息来完成任务：{', '.join(missing_params)}"
            )
            return False

        # 默认：不阻断，交给 tool_agent 等用自然语言 + 部分 params 继续推理/调工具
        logger.warning(
            "【参数检查】缺参但未启用 STRICT，继续执行子任务；子 Agent 可结合完整描述补全"
        )
        return True

    def _extract_response_from_agent_result(self, agent_id: str, agent_result: Dict[str, Any]) -> str:
        if agent_id == "tool_agent":
            return str(agent_result.get("output", "")).strip()
        if agent_id == "knowledge_agent":
            return str(agent_result.get("knowledge_content", "")).strip()
        if agent_id == "memory_agent":
            return "记忆操作成功"
        return ""

    def _can_finalize_after_subtask(
        self,
        subtask: Dict[str, Any],
        selected_agent_id: str,
        agent_result: Dict[str, Any],
    ) -> bool:
        """判断单个子任务结果是否已足够生成最终回答。"""
        if not agent_result.get("success"):
            return False

        output = self._extract_response_from_agent_result(selected_agent_id, agent_result)
        if not output:
            return False

        task_type = (subtask.get("task_type") or "").lower()
        # OA/工具类查询拿到明确结果后直接结束，避免继续触发无关RAG
        if task_type in ("oa_operation", "attendance", "department", "user", "inform", "api_call"):
            return True
        # tool_execution 只在非“无结果/失败”时结束
        if task_type == "tool_execution":
            bad_signals = ("失败", "错误", "error", "无结果", "未找到")
            return not any(s in output.lower() for s in bad_signals)
        return False
    
    async def _integrate_results(self, state: AgentState) -> AgentState:
        """整合结果"""
        # 整合所有Agent的执行结果
        results = []
        
        for task_id, task_data in state.agent_results.items():
            result = task_data.get("result", {})
            if result.get("success"):
                # 根据不同的Agent提取结果
                agent_id = task_data.get("agent")
                if agent_id == "tool_agent":
                    results.append(result.get("output", ""))
                elif agent_id == "knowledge_agent":
                    results.append(result.get("knowledge_content", ""))
                elif agent_id == "memory_agent":
                    results.append("记忆操作成功")
        
        # 生成最终回复
        if results:
            state.final_response = "\n\n".join(results)
        else:
            state.final_response = "任务执行完成，但没有返回结果。"
        
        return state
    
    async def _save_memory(self, state: AgentState) -> None:
        """保存记忆"""
        if state.user_input and state.final_response:
            await self.memory_agent.process({
                "session_id": state.session_id,
                "user_id": state.user_id,
                "action": "add_memory",
                "message": state.user_input,
                "response": state.final_response
            })
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据"""
        try:
            user_input = input_data.get("user_input") or input_data.get("query")
            session_id = input_data.get("session_id")
            user_id = input_data.get("user_id")
            
            if not all([user_input, session_id, user_id]):
                return {
                    "success": False,
                    "error": "缺少必要参数",
                    "final_response": "处理失败：缺少必要参数"
                }
            
            result = await self.process_input(user_input, session_id, user_id)
            response = result.get("response", "处理完成")
            
            return {
                "success": True,
                "response": response,
                "final_response": response,
                "steps": result.get("steps", []),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"【主Agent】处理失败: {str(e)}", exc_info=True)
            error_msg = f"处理失败：{str(e)}"
            return {
                "success": False,
                "error": str(e),
                "final_response": error_msg
            }
    
    def can_handle(self, task_type: str) -> bool:
        """判断是否能够处理特定类型的任务"""
        return True  # 主Agent可以处理所有任务