from typing import Dict, Any, List, Optional
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.agent.base import BaseAgent
from app.core.logger_handler import logger


class AgentRouteResult(BaseModel):
    """Agent路由结果模型"""
    selected_agent: str = Field(..., description="选择的Agent名称")
    confidence: float = Field(..., description="选择的置信度")
    reason: str = Field(..., description="选择理由")


class AgentRouter(BaseAgent):
    """
    Agent路由器，负责根据任务类型和内容智能选择合适的Agent
    """
    
    def __init__(self):
        super().__init__("agent_router")
        
        # 定义可用的Agent及其能力
        self.available_agents = {
            "tool_agent": {
                "name": "工具执行Agent",
                "description": "负责调用外部工具执行任务，如OA系统操作、API调用等",
                "task_types": ["tool_execution", "oa_operation", "api_call"]
            },
            "knowledge_agent": {
                "name": "知识库Agent",
                "description": "负责查询和检索知识库信息，处理RAG相关任务",
                "task_types": ["knowledge_query", "rag_query", "information_retrieval"]
            },
            "memory_agent": {
                "name": "记忆管理Agent",
                "description": "负责管理会话记忆，处理历史记录相关任务",
                "task_types": ["memory_management", "history_query", "session_management"]
            },
            "task_decomposer": {
                "name": "任务拆解Agent",
                "description": "负责将复杂任务分解为子任务",
                "task_types": ["task_decomposition", "complex_task"]
            }
        }
        
        self.llm = None
        self.prompt_template = self._create_prompt_template()
        self.parser = JsonOutputParser(pydantic_object=AgentRouteResult)
    
    def _create_llm(self):
        """创建大模型实例"""
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        base_url = os.getenv("ALIYUN_BASE_URL")

        try:
            from langchain_community.chat_models import ChatTongyi
        except Exception as e:  # pragma: no cover
            logger.error(f"【Agent路由】大模型依赖加载失败: {e}", exc_info=True)
            return None

        return ChatTongyi(
            model="qwen3-max",
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,
        )
    
    def _create_prompt_template(self):
        """创建提示词模板"""
        agents_info = "\n".join([
            f"- {agent_id}: {info['name']} - {info['description']} (任务类型: {', '.join(info['task_types'])})"
            for agent_id, info in self.available_agents.items()
        ])
        
        prompt = f"""
你是一个智能Agent路由器，负责根据任务类型和内容选择最合适的Agent来执行任务。

可用的Agent列表：
{agents_info}

请根据以下信息选择最合适的Agent：
1. 任务类型：{{task_type}}
2. 子任务描述：{{subtask_description}}
3. 需要的参数：{{required_params}}

选择标准：
- 根据任务类型匹配Agent的能力
- 考虑任务的具体需求和复杂度
- 选择最适合完成该任务的Agent

输出格式必须是JSON，包含以下字段：
- selected_agent: 选择的Agent ID
- confidence: 选择的置信度（0-1之间）
- reason: 选择理由

请做出最佳选择。
        """
        return ChatPromptTemplate.from_messages([
            ("system", prompt),
            ("human", "任务类型: {task_type}\n子任务描述: {subtask_description}\n需要的参数: {required_params}")
        ])
    
    def _rule_based_routing(self, task_type: str) -> Optional[str]:
        """规则路由：task_type → agent_id 一对一映射，O(1) 匹配"""
        mapping = {
            "tool_execution": "tool_agent",
            "oa_operation": "tool_agent",
            "api_call": "tool_agent",
            "attendance": "tool_agent",
            "department": "tool_agent",
            "user": "tool_agent",
            "inform": "tool_agent",
            "knowledge_query": "knowledge_agent",
            "rag_query": "knowledge_agent",
            "information_retrieval": "knowledge_agent",
            "document_search": "knowledge_agent",
            "memory_management": "memory_agent",
            "history_query": "memory_agent",
            "session_management": "memory_agent",
            "task_decomposition": "task_decomposer",
            "complex_task": "task_decomposer",
        }
        return mapping.get(task_type)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，选择合适的Agent"""
        try:
            task_type = input_data.get("task_type", "")
            subtask_description = input_data.get("subtask_description", "")
            required_params = input_data.get("required_params", [])

            # 先走规则路由，避免不必要的 LLM 调用
            rule_based = self._rule_based_routing(task_type)
            if rule_based:
                logger.info(f"【Agent路由】规则命中: {task_type} → {rule_based}")
                return {
                    "success": True,
                    "selected_agent": rule_based,
                    "confidence": 1.0,
                    "reason": f"任务类型 '{task_type}' 由规则路由匹配",
                }

            # 规则未命中，降级到 LLM 路由
            if self.llm is None:
                self.llm = self._create_llm()
            if self.llm is None:
                return {
                    "success": False,
                    "error": "大模型客户端不可用，请检查 langchain/通义千问 依赖版本或环境配置"
                }

            chain = self.prompt_template | self.llm | self.parser
            result = await chain.ainvoke({
                "task_type": task_type,
                "subtask_description": subtask_description,
                "required_params": ", ".join(required_params)
            })

            if isinstance(result, dict):
                selected_agent = result.get("selected_agent")
                confidence = result.get("confidence")
                reason = result.get("reason")
                logger.info(f"【Agent路由】LLM 选择了: {selected_agent}, 置信度: {confidence}")
                return {
                    "success": True,
                    "selected_agent": selected_agent,
                    "confidence": confidence,
                    "reason": reason
                }
            else:
                logger.info(f"【Agent路由】LLM 选择了: {result.selected_agent}, 置信度: {result.confidence}")
                return {
                    "success": True,
                    "selected_agent": result.selected_agent,
                    "confidence": result.confidence,
                    "reason": result.reason
                }

        except Exception as e:
            logger.error(f"【Agent路由】失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def can_handle(self, task_type: str) -> bool:
        """判断是否能够处理特定类型的任务"""
        return task_type == "agent_routing"
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的Agent列表"""
        return self.available_agents
    
    def get_agent_by_type(self, task_type: str) -> str:
        """根据任务类型获取最合适的Agent"""
        for agent_id, info in self.available_agents.items():
            if task_type in info["task_types"]:
                return agent_id
        return "tool_agent"  # 默认返回工具执行Agent