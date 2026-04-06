from typing import Dict, Any, List

from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import BaseTool
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agent.base import BaseAgent
from app.core.logger_handler import logger
from app.tools.oa_tools import (
    get_attendance_types,
    get_attendance_responser,
    get_attendance_records,
    create_attendance_record,
    update_attendance_record,
    get_departments,
    get_users,
    get_informs,
    create_inform,
    update_inform,
    get_latest_informs,
    get_latest_attendance,
    get_department_staff_count
)
from app.tools.rag_tools import (
    rag_summary_tools,
    what_time_is_now,
    get_user_info_tools,
    reorder_documents_tools
)


class ToolAgent(BaseAgent):
    """
    工具执行Agent，负责调用外部工具执行任务
    """
    
    def __init__(self):
        super().__init__("tool_agent")
        self.tools = self._get_all_tools()
        self.agent_executor = None
    
    def _get_all_tools(self) -> List[BaseTool]:
        """获取所有可用的工具"""
        return [
            # OA工具
            get_attendance_types,
            get_attendance_responser,
            get_attendance_records,
            create_attendance_record,
            update_attendance_record,
            get_departments,
            get_users,
            get_informs,
            create_inform,
            update_inform,
            get_latest_informs,
            get_latest_attendance,
            get_department_staff_count,
            
            # RAG工具
            rag_summary_tools,
            what_time_is_now,
            get_user_info_tools,
            reorder_documents_tools
        ]
    
    def _create_agent_executor(self):
        """创建Agent执行器"""
        from app.utils.prompt_loader import load_prompt
        
        # 创建聊天模型
        import os
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        base_url = os.getenv("ALIYUN_BASE_URL")
        
        llm = ChatTongyi(
            model="qwen3-max",
            api_key=api_key,
            base_url=base_url,
            temperature=0.3,
        )
        
        # 创建提示词模板
        system_prompt = load_prompt('main_prompt')
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建Agent
        agent = create_tool_calling_agent(llm, self.tools, prompt)
        
        # 创建Executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，执行工具调用"""
        try:
            if not self.agent_executor:
                self.agent_executor = self._create_agent_executor()
            
            task_description = input_data.get("task_description", "")
            params = input_data.get("params", {})
            
            # 构建工具调用输入
            tool_input = task_description
            if params:
                tool_input += f"\n参数: {params}"
            
            # 执行工具调用
            result = await self.agent_executor.ainvoke({
                "input": tool_input,
                "chat_history": []
            })
            
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # 记录工具调用步骤
            steps = []
            for action, observation in intermediate_steps:
                steps.append({
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                    "tool_output": observation,
                    "thought": action.log
                })
            
            logger.info(f"【工具执行】成功执行工具，输出: {output[:100]}...")
            
            return {
                "success": True,
                "output": output,
                "steps": steps,
                "tool_used": [step["tool"] for step in steps]
            }
            
        except Exception as e:
            logger.error(f"【工具执行】失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def can_handle(self, task_type: str) -> bool:
        """判断是否能够处理特定类型的任务"""
        tool_task_types = [
            "tool_execution",
            "oa_operation",
            "api_call",
            "attendance",
            "department",
            "user",
            "inform",
            "rag_query"
        ]
        return task_type in tool_task_types
    
    def get_available_tools(self) -> List[BaseTool]:
        """获取可用的工具列表"""
        return self.tools