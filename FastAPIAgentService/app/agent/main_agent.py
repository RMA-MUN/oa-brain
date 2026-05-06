import json
import os
from typing import Dict, Any, List, Optional, AsyncGenerator

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
    
    async def process_input(self, user_input: str, session_id: str, user_id: str, jwt_token: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户输入，协调工作流程
        
        :param user_input: 用户输入
        :param session_id: 会话ID
        :param user_id: 用户ID
        :param jwt_token: JWT令牌
        :return: 处理结果
        """
        try:
            # 初始化状态
            state = AgentState()
            state.user_input = user_input
            state.session_id = session_id
            state.user_id = user_id
            state.jwt_token = jwt_token
            
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
                        "user_id": state.user_id,
                        "jwt_token": state.jwt_token
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

        # 将 jwt_token 注入到 existing_params 中，避免参数提取 Agent 重复询问
        existing_params = subtask.get("params") or {}
        if state.jwt_token and "jwt_token" not in existing_params:
            existing_params["jwt_token"] = state.jwt_token

        extraction_result = await self.param_extraction_agent.process({
            "required_params": list(required_params),
            "existing_params": existing_params,
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
            if agent_result.get("success"):
                history = agent_result.get("history", [])
                if history:
                    return self._generate_memory_response(history)
                else:
                    return "当前会话暂无历史记录"
            return "记忆操作失败"
        return ""
    
    def _generate_memory_response(self, history: List[tuple]) -> str:
        """使用大模型根据会话历史生成自然语言回复"""
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        base_url = os.getenv("ALIYUN_BASE_URL")
        
        if not api_key or not base_url:
            history_lines = []
            for idx, (user_msg, assistant_msg) in enumerate(history, 1):
                history_lines.append(f"对话 {idx}：")
                history_lines.append(f"您：{user_msg}")
                history_lines.append(f"我：{assistant_msg}")
                history_lines.append("")
            return "\n".join(history_lines).strip()
        
        try:
            from langchain_community.chat_models import ChatTongyi
            from langchain_core.messages import HumanMessage, SystemMessage
            
            llm = ChatTongyi(
                model="qwen3-max",
                api_key=api_key,
                base_url=base_url,
                temperature=0.7,
            )
            
            history_str = "\n".join([
                f"用户: {user_msg}\n助手: {assistant_msg}"
                for user_msg, assistant_msg in history
            ])
            
            prompt = f"""
            你是一个会话记忆助手。用户问你"你还记得我刚才说了什么吗"或类似的问题，
            需要你根据以下会话历史用自然、友好的语言总结给用户。
            
            会话历史：
            {history_str}
            
            请用自然、口语化的方式总结给用户，不要使用格式标记，就像正常对话一样回答。
            如果只有一轮对话，可以直接复述；如果有多轮对话，请简要总结。
            """
            
            messages = [
                SystemMessage(content="你是一个友好的AI助手，擅长总结对话历史。"),
                HumanMessage(content=prompt)
            ]
            
            response = llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"【记忆回复生成】调用大模型失败，使用模板备份: {str(e)}")
            history_lines = []
            for idx, (user_msg, assistant_msg) in enumerate(history, 1):
                history_lines.append(f"对话 {idx}：")
                history_lines.append(f"您：{user_msg}")
                history_lines.append(f"我：{assistant_msg}")
                history_lines.append("")
            return "\n".join(history_lines).strip()

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
        # tool_execution 使用LLM来判断是否可以结束
        if task_type == "tool_execution":
            return self._llm_decide_finalize(subtask, output)
        return False
    
    def _llm_decide_finalize(self, subtask: Dict[str, Any], output: str) -> bool:
        """使用LLM判断子任务结果是否已足够生成最终回答。"""
        import os
        from langchain_community.chat_models import ChatTongyi
        from langchain_core.messages import HumanMessage
        
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        base_url = os.getenv("ALIYUN_BASE_URL")
        
        try:
            llm = ChatTongyi(
                model="qwen3-max",
                api_key=api_key,
                base_url=base_url,
                temperature=0.1,
            )
            
            prompt = f"""
            请判断以下子任务的执行结果是否已经足够回答用户的原始请求，不需要继续执行后续子任务。
            
            用户原始请求: {subtask.get('description', '')}
            
            当前子任务名称: {subtask.get('task_name', '')}
            
            当前子任务执行结果: {output}
            
            请仔细分析：
            1. 该结果是否直接回答了用户的核心问题？
            2. 用户是否还需要更多信息才能完成其请求？
            3. 是否还有必要继续执行其他子任务？
            
            请只输出 "YES" 或 "NO"，不要输出其他任何内容。
            """
            
            response = llm.invoke([HumanMessage(content=prompt)])
            result = response.content.strip().upper()
            
            logger.info(f"【LLM决策】是否可以提前结束: {result}")
            
            return result == "YES"
        except Exception as e:
            logger.error(f"【LLM决策】调用失败: {str(e)}")
            # 如果LLM调用失败，使用简单的关键词判断作为后备
            bad_signals = ("失败", "错误", "error", "无结果", "未找到")
            if any(s in output.lower() for s in bad_signals):
                return False
            success_signals = ("提交成功", "审批通过", "创建成功", "申请成功", "已完成", "已批准", "success")
            return any(s in output for s in success_signals)
    
    async def _integrate_results(self, state: AgentState) -> AgentState:
        """整合结果"""
        # 整合所有Agent的执行结果
        results = []
        success_count = 0
        failed_tasks = []
        
        for task_id, task_data in state.agent_results.items():
            result = task_data.get("result", {})
            agent_id = task_data.get("agent")
            task_description = task_data.get("task", {}).get("description", "")
            
            if result.get("success"):
                success_count += 1
                # 根据不同的Agent提取结果
                if agent_id == "tool_agent":
                    output = result.get("output", "")
                    if output:
                        results.append(output)
                elif agent_id == "knowledge_agent":
                    content = result.get("knowledge_content", "")
                    if content:
                        results.append(content)
                elif agent_id == "memory_agent":
                    history = result.get("history", [])
                    if history:
                        results.append(self._generate_memory_response(history))
                    else:
                        results.append("当前会话暂无历史记录")
            else:
                failed_tasks.append(task_description)
        
        # 生成最终回复
        if results:
            state.final_response = "\n\n".join(results)
        else:
            # 根据不同情况给出有意义的回复
            user_input = state.user_input or ""
            
            # 检查是否是问候或闲聊
            greetings = ["你好", "您好", "嗨", "hello", "hi", "早上好", "下午好", "晚上好"]
            praises = ["聪明", "厉害", "真棒", "真聪明", "太棒了"]
            
            is_greeting = any(g in user_input for g in greetings)
            is_praise = any(p in user_input for p in praises)
            
            if is_greeting:
                state.final_response = "你好！我是您的智能办公助手，请问有什么可以帮助您的吗？"
            elif is_praise:
                state.final_response = "谢谢夸奖！很高兴能帮到您。如果还有其他问题，随时告诉我。"
            elif failed_tasks:
                state.final_response = f"任务执行过程中遇到一些问题，以下任务未能成功完成：\n{chr(10).join(f'- {task}' for task in failed_tasks)}\n\n请检查您的请求是否正确，或者稍后再试。"
            elif success_count > 0:
                state.final_response = "任务已执行完成，但暂时没有获取到相关数据。这可能是因为：\n- 当前没有相关记录\n- 查询条件可能需要调整\n\n请问您需要查询其他内容吗？"
            else:
                state.final_response = "抱歉，我暂时无法为您提供帮助。请您重新描述您的需求，我会尽力为您解答。"
        
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
            jwt_token = input_data.get("jwt_token")
            
            if not all([user_input, session_id, user_id]):
                return {
                    "success": False,
                    "error": "缺少必要参数",
                    "final_response": "处理失败：缺少必要参数"
                }
            
            result = await self.process_input(user_input, session_id, user_id, jwt_token)
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
    
    async def process_stream(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理输入数据，实时返回中间结果
        :param input_data: 输入数据
        :return: 异步生成器，产生中间结果
        """
        try:
            user_input = input_data.get("user_input") or input_data.get("query")
            session_id = input_data.get("session_id")
            user_id = input_data.get("user_id")
            jwt_token = input_data.get("jwt_token")
            
            if not all([user_input, session_id, user_id]):
                yield {"type": "final", "content": "处理失败：缺少必要参数"}
                return
            
            # 初始化状态
            state = AgentState()
            state.user_input = user_input
            state.session_id = session_id
            state.user_id = user_id
            state.jwt_token = jwt_token
            
            logger.info(f"【主Agent流式】开始处理请求，用户ID: {user_id}, 会话ID: {session_id}, 输入: {user_input[:50]}...")
            
            # 步骤1: 获取会话历史
            yield {"type": "thinking", "content": "获取会话历史..."}
            state = await self._get_session_history(state)
            
            # 步骤2: 任务分解
            yield {"type": "thinking", "content": "任务分解Agent正在分析您的请求..."}
            state = await self._decompose_task(state)
            
            # 如果任务分解失败，返回错误
            if not state.task_subtasks:
                yield {"type": "final", "content": "抱歉，无法理解您的请求。请重新描述您的需求。"}
                return
            
            # 输出任务分解结果
            yield {"type": "thinking", "content": f"任务分解完成，共识别到{len(state.task_subtasks)}个子任务"}
            
            # 步骤3: 执行子任务
            ordered_subtasks = self._sort_subtasks(state.task_subtasks or [])
            for idx, subtask in enumerate(ordered_subtasks):
                # 检查参数是否完整
                yield {"type": "thinking", "content": f"参数提取Agent正在检查子任务「{subtask.get('task_name', '未知')}」的参数..."}
                if not await self._check_params_complete(subtask, state):
                    if state.final_response:
                        yield {"type": "final", "content": state.final_response}
                    return
                
                # 路由到合适的Agent
                yield {"type": "thinking", "content": f"Agent路由器正在选择处理子任务「{subtask.get('task_name', '未知')}」的最佳Agent..."}
                route_result = await self.agent_router.process({
                    "task_type": subtask["task_type"],
                    "subtask_description": subtask["description"],
                    "required_params": subtask["required_params"]
                })
                
                if route_result.get("success"):
                    selected_agent_id = route_result.get("selected_agent")
                    agent = self.agent_map.get(selected_agent_id)
                    
                    if agent:
                        # 输出路由选择结果
                        yield {"type": "thinking", "content": f"选择了{selected_agent_id}处理该子任务，置信度: {route_result.get('confidence', 0)}"}
                        
                        # 发送工具调用信息
                        yield {"type": "tool_call", "tool_name": selected_agent_id, "tool_input": subtask.get("params", {})}
                        
                        # 执行子任务
                        task_input = {
                            "task_description": subtask["description"],
                            "params": subtask.get("params", {}),
                            "session_id": state.session_id,
                            "user_id": state.user_id,
                            "jwt_token": state.jwt_token
                        }
                        
                        if selected_agent_id == "knowledge_agent":
                            task_input["query"] = subtask.get("query", subtask["description"])
                        elif selected_agent_id == "memory_agent":
                            task_input["action"] = subtask.get("action", "get_history")
                        
                        # 获取工具执行结果
                        agent_result = await agent.process(task_input)
                        
                        # 保存Agent执行结果
                        state.agent_results[subtask["task_id"]] = {
                            "task": subtask,
                            "agent": selected_agent_id,
                            "result": agent_result
                        }
                        
                        # 如果工具执行成功，发送结果（作为thinking类型输出）
                        if agent_result.get("success"):
                            output = self._extract_response_from_agent_result(selected_agent_id, agent_result)
                            if output:
                                yield {"type": "thinking", "content": f"{selected_agent_id}执行结果: {output}"}
                            
                            # 检查是否可以提前结束
                            if self._can_finalize_after_subtask(subtask, selected_agent_id, agent_result):
                                state.final_response = output
                                break
            
            # 步骤4: 整合结果
            if not state.final_response:
                yield {"type": "thinking", "content": "整合所有子任务的执行结果..."}
                state = await self._integrate_results(state)
            
            # 发送最终响应
            if state.final_response:
                yield {"type": "final", "content": state.final_response}
            
            # 步骤5: 保存记忆（在后台异步执行，不阻塞流式输出）
            await self._save_memory(state)
            
            logger.info(f"【主Agent流式】处理完成，会话ID: {session_id}")
            
        except Exception as e:
            logger.error(f"【主Agent流式】处理失败: {str(e)}", exc_info=True)
            yield {"type": "final", "content": f"处理失败：{str(e)}"}