from typing import Dict, Any, List
import os
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.agent.base import BaseAgent
from app.core.logger_handler import logger


class SubTask(BaseModel):
    """子任务模型"""
    task_id: str = Field(..., description="子任务ID")
    task_name: str = Field(..., description="子任务名称")
    task_type: str = Field(..., description="任务类型")
    priority: int = Field(..., description="优先级，数字越小优先级越高")
    dependencies: List[str] = Field(default_factory=list, description="依赖的子任务ID列表")
    required_params: List[str] = Field(default_factory=list, description="需要的参数列表")
    description: str = Field(..., description="子任务描述")


class TaskDecompositionResult(BaseModel):
    """任务分解结果模型"""
    main_task_type: str = Field(..., description="主任务类型")
    subtasks: List[SubTask] = Field(..., description="子任务列表")
    total_tasks: int = Field(..., description="子任务总数")


class TaskDecomposer(BaseAgent):
    """
    任务拆解组件，负责将复杂任务分解为可执行的子任务
    """
    
    def __init__(self):
        super().__init__("task_decomposer")
        self.llm = self._create_llm()
        self.prompt_template = self._create_prompt_template()
        self.parser = JsonOutputParser(pydantic_object=TaskDecompositionResult)
    
    def _create_llm(self):
        """创建大模型实例"""
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        base_url = os.getenv("ALIYUN_BASE_URL")
        
        return ChatTongyi(
            model="qwen3-max",
            api_key=api_key,
            base_url=base_url,
            temperature=0.3,
        )
    
    def _create_prompt_template(self):
        """创建提示词模板"""
        prompt = """
你是一个智能任务分解专家，负责将用户的复杂请求分解为一系列可执行的子任务。

请根据用户的输入，分析任务类型并分解为具体的子任务。每个子任务都应该有明确的目标、所需参数和执行顺序。

任务类型包括：
- tool_execution: 需要调用外部工具的任务
- knowledge_query: 需要查询知识库的任务
- memory_management: 需要管理会话记忆的任务
- information_summary: 需要总结信息的任务
- user_interaction: 需要与用户交互获取更多信息的任务

请按照以下要求进行分解：
1. 分析用户意图，确定主任务类型
2. 将任务分解为最小可执行单元
3. 定义子任务的优先级和依赖关系
4. 明确每个子任务需要的参数
5. 如果需要更多信息，请创建一个user_interaction类型的子任务

输出格式必须是JSON，包含以下字段：
- main_task_type: 主任务类型
- subtasks: 子任务列表，每个子任务包含：
  - task_id: 唯一标识符
  - task_name: 子任务名称
  - task_type: 任务类型
  - priority: 优先级（数字越小优先级越高）
  - dependencies: 依赖的子任务ID列表
  - required_params: 需要的参数列表
  - description: 子任务描述
- total_tasks: 子任务总数

用户输入：{user_input}
        """
        return ChatPromptTemplate.from_messages([
            ("system", prompt),
            ("human", "{user_input}")
        ])
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，分解任务"""
        try:
            user_input = input_data.get("user_input", "")
            
            # 创建链
            chain = self.prompt_template | self.llm | self.parser
            
            # 执行任务分解
            result = await chain.ainvoke({"user_input": user_input})
            
            # 检查 result 类型，处理字典情况
            if isinstance(result, dict):
                main_task_type = result.get("main_task_type")
                total_tasks = result.get("total_tasks")
                subtasks = result.get("subtasks", [])
                logger.info(f"【任务分解】成功分解任务: {main_task_type}, 子任务数: {total_tasks}")
                
                return {
                    "success": True,
                    "task_type": main_task_type,
                    "subtasks": subtasks,
                    "total_tasks": total_tasks
                }
            else:
                # 正常情况，result 是 TaskDecompositionResult 对象
                logger.info(f"【任务分解】成功分解任务: {result.main_task_type}, 子任务数: {result.total_tasks}")
                
                return {
                    "success": True,
                    "task_type": result.main_task_type,
                    "subtasks": [subtask.model_dump() for subtask in result.subtasks],
                    "total_tasks": result.total_tasks
                }
            
        except Exception as e:
            logger.error(f"【任务分解】失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def can_handle(self, task_type: str) -> bool:
        """判断是否能够处理特定类型的任务"""
        return task_type == "task_decomposition"