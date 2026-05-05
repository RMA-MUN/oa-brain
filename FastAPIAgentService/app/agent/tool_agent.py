import re
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta

from langchain_classic.agents import create_tool_calling_agent, AgentExecutor, AgentOutputParser
from langchain_core.messages import ToolCall
from langchain_core.tools import BaseTool
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

    @staticmethod
    def _fix_json_format(json_str: str) -> str:
        """修复JSON格式错误"""
        import re
        
        # 去除首尾空白字符
        json_str = json_str.strip()
        
        # 确保所有键名都用双引号包围
        json_str = re.sub(r'(\{|,\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)
        
        # 修复单引号为双引号
        json_str = re.sub(r':\s*\'([^\']*)\'', r': "\1"', json_str)
        
        # 修复未加引号的字符串值
        json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_\s\u4e00-\u9fa5]*)(,|\s*\})', r': "\1"\2', json_str)
        
        # 修复数字值周围的引号
        json_str = re.sub(r':\s*"(\d+\.?\d*)"', r': \1', json_str)
        
        # 移除尾部逗号
        json_str = re.sub(r',\s*([\}\]])', r' \1', json_str)
        
        # 确保JSON以{开头以}结尾
        if not (json_str.startswith('{') and json_str.endswith('}')):
            if '{' in json_str and '}' not in json_str:
                json_str += '}'
            elif '}' in json_str and '{' not in json_str:
                json_str = '{' + json_str
            else:
                json_str = '{' + json_str + '}'
        
        return json_str
    
    def _force_json_conversion(self, data: Any) -> str:
        """强制将数据转换为严格的JSON格式"""
        if isinstance(data, str):
            # 如果是字符串，尝试修复并解析
            try:
                fixed_json = self._fix_json_format(data)
                parsed = json.loads(fixed_json)
                return json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
            except json.JSONDecodeError:
                # 如果无法解析，返回空JSON对象
                return '{}'
        elif isinstance(data, (dict, list)):
            # 如果是字典或列表，直接转换
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        else:
            # 其他类型，返回空JSON对象
            return '{}'

    def _normalize_for_strict_json(self, value: Any) -> Any:
        """递归规范化对象，尽量将可解析字符串转换为JSON对象。"""
        if isinstance(value, dict):
            return {str(k): self._normalize_for_strict_json(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._normalize_for_strict_json(item) for item in value]
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    return self._normalize_for_strict_json(parsed)
                except json.JSONDecodeError:
                    return value
            return value
        return value

    def _build_strict_json_block(self, params: Dict[str, Any]) -> str:
        """将参数统一转换为严格JSON字符串（双引号、可解析）。"""
        normalized_params = self._normalize_for_strict_json(params)
        # 使用更严格的JSON序列化选项
        return json.dumps(normalized_params, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    
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
            get_department_staff_count,
            
            # RAG工具
            rag_summary_tools,
            what_time_is_now,
            get_user_info_tools,
            reorder_documents_tools
        ]

    @staticmethod
    def _resolve_date_expr(date_expr: str, is_end_time: bool = False) -> str:
        """将相对日期表达式转换为标准时间字符串。"""
        if date_expr == "today":
            return datetime.now().strftime("%Y-%m-%dT23:59:59" if is_end_time else "%Y-%m-%dT00:00:00")
        if date_expr == "tomorrow":
            base = datetime.now() + timedelta(days=1)
            return base.strftime("%Y-%m-%dT23:59:59" if is_end_time else "%Y-%m-%dT00:00:00")
        return date_expr

    def _build_leave_tool_args(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        从上游参数中提取并标准化请假工具调用参数。
        返回空字典表示参数不足或格式不可用，继续走通用Agent流程。
        """
        jwt_token = params.get("jwt_token") or params.get("token")
        raw_leave = params.get("leave_request_payload") or params.get("leave_request_data")
        if not jwt_token or not raw_leave:
            return {}

        leave_data: Dict[str, Any] = {}
        if isinstance(raw_leave, str):
            try:
                # 尝试直接解析
                leave_data = json.loads(raw_leave)
            except json.JSONDecodeError:
                # 尝试修复JSON格式
                try:
                    fixed_json = self._fix_json_format(raw_leave)
                    leave_data = json.loads(fixed_json)
                except json.JSONDecodeError:
                    return {}
        elif isinstance(raw_leave, dict):
            leave_data = raw_leave
        else:
            return {}

        # 提取字段，支持多种命名方式
        start_raw = leave_data.get("start_time") or leave_data.get("start_date") or leave_data.get("start")
        end_raw = leave_data.get("end_time") or leave_data.get("end_date") or leave_data.get("end")
        reason = leave_data.get("reason") or leave_data.get("description") or leave_data.get("cause")
        leave_type = leave_data.get("type", leave_data.get("leave_type"))

        if not start_raw or not end_raw or not reason:
            return {}

        start_time = self._resolve_date_expr(str(start_raw), is_end_time=False)
        end_time = self._resolve_date_expr(str(end_raw), is_end_time=True)

        if leave_type is None:
            # 缺少明确type时，不走确定性分支，交由通用工具流程先查询类型再创建。
            return {}

        # 处理请假类型
        leave_type_str = str(leave_type).strip()
        if not leave_type_str.isdigit():
            # 尝试映射中文请假类型到ID（需要根据实际后端配置调整）
            type_mapping = {
                "事假": 1,
                "病假": 2,
                "年假": 3,
                "婚假": 4,
                "产假": 5,
                "陪产假": 6,
                "丧假": 7,
                "工伤假": 8
            }
            if leave_type_str in type_mapping:
                leave_type_id = type_mapping[leave_type_str]
            else:
                # 未知类型，交由通用流程处理
                return {}
        else:
            try:
                leave_type_id = int(leave_type_str)
            except ValueError:
                return {}

        return {
            "token": str(jwt_token),
            "type": leave_type_id,
            "start_time": start_time,
            "end_time": end_time,
            "reason": str(reason)
        }
    
    def _create_agent_executor(self, jwt_token: Optional[str] = None):
        """创建Agent执行器"""
        from app.utils.prompt_loader import load_prompt
        
        # 创建聊天模型
        import os
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        base_url = os.getenv("ALIYUN_BASE_URL")

        try:
            from langchain_community.chat_models import ChatTongyi
        except Exception as e:
            raise RuntimeError(
                "大模型客户端不可用，请检查 langchain/通义千问 依赖版本或环境配置"
            ) from e

        # 配置通义千问模型，确保工具调用参数格式正确
        llm = ChatTongyi(
            model="qwen3-max", 
            api_key=api_key, 
            base_url=base_url, 
            temperature=0.3,
            # 开启自动工具选择；不强制 json_object，避免 Tongyi 对 messages 的 json 关键词校验报错
            tool_choice="auto"
        )
        
        # 创建提示词模板，支持注入 jwt_token
        system_prompt = load_prompt('tool_agent_prompt')
        
        # 如果提供了 jwt_token，将其注入到系统Prompt中
        if jwt_token:
            system_prompt += f"\n\n你拥有以下身份验证令牌，在调用需要身份验证的工具时使用：\nJWT_TOKEN: {jwt_token}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建Agent
        agent = create_tool_calling_agent(
            llm, 
            self.tools, 
            prompt
        )

        # 自定义错误处理函数
        def custom_error_handler(e):
            error_str = str(e)
            logger.error(f"Tool parsing error: {error_str}")

            # 尝试从错误消息中提取工具调用信息并修复JSON格式
            try:
                # 提取工具名称和参数
                import re
                tool_name_match = re.search(r'name\s*:\s*["\']([^"\']+)["\']', error_str)
                arguments_match = re.search(r'arguments\s*:\s*([\s\S]*?)(?=}$|$)', error_str)
                
                if tool_name_match and arguments_match:
                    tool_name = tool_name_match.group(1)
                    arguments_str = arguments_match.group(1)
                    
                    # 修复JSON格式
                    fixed_arguments = ToolAgent._fix_json_format(arguments_str)
                    # 解析JSON
                    arguments = json.loads(fixed_arguments)
                    
                    # 构建修复后的工具调用字符串
                    fixed_tool_call = f"\n工具调用:\n```\n{{\n  \"toolcall\": {{\n    \"name\": \"{tool_name}\",\n    \"args\": {json.dumps(arguments, ensure_ascii=False)}\n  }}\n}}\n```\n"
                    return f"Error: {error_str}. I've fixed the JSON format. Please use this format: {fixed_tool_call}"
            except Exception as fix_error:
                logger.error(f"修复JSON格式失败: {fix_error}")

            # 如果无法修复，返回错误消息
            return f"Error: {error_str}. Please make sure to use valid JSON format for tool arguments."


        # 创建Executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=custom_error_handler)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，执行工具调用"""
        try:
            task_description = input_data.get("task_description", "")
            params = input_data.get("params", {})

            # 对“请假申请创建”场景走确定性调用，避免LLM工具参数JSON格式不稳定导致失败。
            deterministic_leave_args = self._build_leave_tool_args(params)
            if deterministic_leave_args:
                logger.info(f"【工具执行】命中确定性请假流程，参数: {deterministic_leave_args}")
                direct_result = await create_attendance_record.ainvoke(deterministic_leave_args)
                return {
                    "success": True,
                    "output": direct_result,
                    "steps": [{
                        "tool": "create_attendance_record",
                        "tool_input": deterministic_leave_args,
                        "tool_output": direct_result,
                        "thought": "使用确定性流程直接创建请假考勤记录，避免工具参数JSON格式错误。"
                    }],
                    "tool_used": ["create_attendance_record"]
                }

            # 对“创建通知”场景走确定性调用
            if "create_inform" in task_description or "创建通知" in task_description:
                token = params.get("jwt_token") or params.get("token")
                inform_data = params.get("inform_data") or params.get("notification_data")
                if token and inform_data:
                    try:
                        # 确保inform_data是字典格式
                        if isinstance(inform_data, str):
                            inform_data = json.loads(inform_data)
                        
                        # 验证必需字段
                        if all(key in inform_data for key in ["title", "content"]):
                            from app.schemas.oa_schemas import InformCreateRequest
                            inform_request = InformCreateRequest(
                                title=inform_data["title"],
                                content=inform_data["content"],
                                public=inform_data.get("public", False),
                                department_ids=inform_data.get("department_ids", [])
                            )
                            logger.info(f"【工具执行】命中确定性创建通知流程，参数: {{'token': '***', 'title': '{inform_data['title']}'}}")
                            direct_result = await create_inform.ainvoke({"token": token, "inform_data": inform_request})
                            return {
                                "success": True,
                                "output": direct_result,
                                "steps": [{
                                    "tool": "create_inform",
                                    "tool_input": {"token": token, "title": inform_data["title"]},
                                    "tool_output": direct_result,
                                    "thought": "使用确定性流程直接创建通知，避免工具参数JSON格式错误。"
                                }],
                                "tool_used": ["create_inform"]
                            }
                    except Exception as e:
                        logger.warning(f"确定性创建通知流程失败: {str(e)}")
                        # 失败后继续走通用流程

            # 对“更新考勤记录”场景走确定性调用
            if "update_attendance" in task_description or "更新考勤" in task_description:
                token = params.get("jwt_token") or params.get("token")
                record_id = params.get("record_id") or params.get("id")
                update_data = params.get("update_data") or params.get("status")
                if token and record_id:
                    try:
                        from app.schemas.oa_schemas import AttendanceUpdateRequest
                        # 构建更新数据
                        if isinstance(update_data, dict):
                            attendance_update = AttendanceUpdateRequest(**update_data)
                        elif isinstance(update_data, str):
                            # 简单处理：如果只是状态字符串
                            attendance_update = AttendanceUpdateRequest(status=update_data)
                        else:
                            attendance_update = AttendanceUpdateRequest(status="approved" if "通过" in task_description else "rejected")
                        
                        logger.info(f"【工具执行】命中确定性更新考勤流程，参数: {{'token': '***', 'record_id': {record_id}}}")
                        direct_result = await update_attendance_record.ainvoke({"token": token, "record_id": record_id, "update_data": attendance_update})
                        return {
                            "success": True,
                            "output": direct_result,
                            "steps": [{
                                "tool": "update_attendance_record",
                                "tool_input": {"token": token, "record_id": record_id},
                                "tool_output": direct_result,
                                "thought": "使用确定性流程直接更新考勤记录，避免工具参数JSON格式错误。"
                            }],
                            "tool_used": ["update_attendance_record"]
                        }
                    except Exception as e:
                        logger.warning(f"确定性更新考勤流程失败: {str(e)}")
                        # 失败后继续走通用流程

            
            # 每次请求创建全新的 executor，避免跨会话状态污染
            agent_executor = self._create_agent_executor()

            # 构建工具调用输入：附带严格JSON参数块，减少模型生成非法arguments的概率
            tool_input = task_description
            if params:
                strict_json_params = self._build_strict_json_block(params)
                tool_input += (
                    "\n参数（严格JSON，仅可使用该格式组装工具arguments）：\n"
                    f"{strict_json_params}"
                )
            
            logger.info(f"【工具执行】开始执行工具，输入: {tool_input}")
            logger.info(f"【工具执行】参数: {params}")

        except Exception as e:
            logger.error(f"【工具执行】工具调用失败: {str(e)}")
            return {"success": False, "message": f"工具调用失败: {str(e)}"}

    def _build_attendance_args(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """构建考勤记录参数"""
        token = params.get("jwt_token") or params.get("token") or params.get("auth_token")
        start_date = params.get("start_date") or params.get("start_time")
        end_date = params.get("end_date") or params.get("end_time")
        leave_type = params.get("leave_type") or params.get("type")
        reason = params.get("reason")
        
        if not (token and start_date and end_date and reason):
            return {}
        
        # 解析请假类型
        leave_type_id = 1  # 默认事假
        if isinstance(leave_type, str):
            type_mapping = {
                "事假": 1,
                "病假": 2,
                "年假": 3,
                "婚假": 4,
                "产假": 5,
                "陪产假": 6,
                "丧假": 7,
                "工伤假": 8
            }
            if leave_type in type_mapping:
                leave_type_id = type_mapping[leave_type]
        elif isinstance(leave_type, int):
            leave_type_id = leave_type
        
        # 解析日期
        start_time = self._resolve_date_expr(str(start_date), is_end_time=False)
        end_time = self._resolve_date_expr(str(end_date), is_end_time=True)
        
        return {
            "token": token,
            "type": leave_type_id,
            "start_time": start_time,
            "end_time": end_time,
            "reason": reason
        }
    
    async def _try_direct_attendance_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """尝试直接调用考勤记录工具"""
        attendance_args = self._build_attendance_args(params)
        if not attendance_args:
            return {}
        
        try:
            direct_result = await create_attendance_record.ainvoke(attendance_args)
            return {
                "success": True,
                "output": direct_result,
                "steps": [{
                    "tool": "create_attendance_record",
                    "tool_input": attendance_args,
                    "tool_output": direct_result,
                    "thought": "使用确定性流程直接创建请假考勤记录，避免工具参数JSON格式错误。"
                }],
                "tool_used": ["create_attendance_record"]
            }
        except Exception as direct_error:
            logger.error(f"直接调用工具失败: {str(direct_error)}")
            return {}

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，执行工具调用"""
        try:
            task_description = input_data.get("task_description", "")
            params = input_data.get("params", {})
            jwt_token = input_data.get("jwt_token")

            # 如果 params 中没有 jwt_token，但 input_data 中有，则添加到 params
            if jwt_token and "jwt_token" not in params:
                params["jwt_token"] = jwt_token

            # 对“请假申请创建”场景走确定性调用，避免LLM工具参数JSON格式不稳定导致失败。
            deterministic_leave_args = self._build_leave_tool_args(params)
            if deterministic_leave_args:
                logger.info(f"【工具执行】命中确定性请假流程，参数: {deterministic_leave_args}")
                direct_result = await create_attendance_record.ainvoke(deterministic_leave_args)
                return {
                    "success": True,
                    "output": direct_result,
                    "steps": [{
                        "tool": "create_attendance_record",
                        "tool_input": deterministic_leave_args,
                        "tool_output": direct_result,
                        "thought": "使用确定性流程直接创建请假考勤记录，避免工具参数JSON格式错误。"
                    }],
                    "tool_used": ["create_attendance_record"]
                }

            # 对“创建通知”场景走确定性调用
            if "create_inform" in task_description or "创建通知" in task_description:
                token = params.get("jwt_token") or params.get("token")
                inform_data = params.get("inform_data") or params.get("notification_data")
                if token and inform_data:
                    try:
                        # 确保inform_data是字典格式
                        if isinstance(inform_data, str):
                            inform_data = json.loads(inform_data)
                        
                        # 验证必需字段
                        if all(key in inform_data for key in ["title", "content"]):
                            from app.schemas.oa_schemas import InformCreateRequest
                            inform_request = InformCreateRequest(
                                title=inform_data["title"],
                                content=inform_data["content"],
                                public=inform_data.get("public", False),
                                department_ids=inform_data.get("department_ids", [])
                            )
                            logger.info(f"【工具执行】命中确定性创建通知流程，参数: {{'token': '***', 'title': '{inform_data['title']}'}}")
                            direct_result = await create_inform.ainvoke({"token": token, "inform_data": inform_request})
                            return {
                                "success": True,
                                "output": direct_result,
                                "steps": [{
                                    "tool": "create_inform",
                                    "tool_input": {"token": token, "title": inform_data["title"]},
                                    "tool_output": direct_result,
                                    "thought": "使用确定性流程直接创建通知，避免工具参数JSON格式错误。"
                                }],
                                "tool_used": ["create_inform"]
                            }
                    except Exception as e:
                        logger.warning(f"确定性创建通知流程失败: {str(e)}")
                        # 失败后继续走通用流程

            # 对“更新考勤记录”场景走确定性调用
            if "update_attendance" in task_description or "更新考勤" in task_description:
                token = params.get("jwt_token") or params.get("token")
                record_id = params.get("record_id") or params.get("id")
                update_data = params.get("update_data") or params.get("status")
                if token and record_id:
                    try:
                        from app.schemas.oa_schemas import AttendanceUpdateRequest
                        # 构建更新数据
                        if isinstance(update_data, dict):
                            attendance_update = AttendanceUpdateRequest(**update_data)
                        elif isinstance(update_data, str):
                            # 简单处理：如果只是状态字符串
                            attendance_update = AttendanceUpdateRequest(status=update_data)
                        else:
                            attendance_update = AttendanceUpdateRequest(status="approved" if "通过" in task_description else "rejected")
                        
                        logger.info(f"【工具执行】命中确定性更新考勤流程，参数: {{'token': '***', 'record_id': {record_id}}}")
                        direct_result = await update_attendance_record.ainvoke({"token": token, "record_id": record_id, "update_data": attendance_update})
                        return {
                            "success": True,
                            "output": direct_result,
                            "steps": [{
                                "tool": "update_attendance_record",
                                "tool_input": {"token": token, "record_id": record_id},
                                "tool_output": direct_result,
                                "thought": "使用确定性流程直接更新考勤记录，避免工具参数JSON格式错误。"
                            }],
                            "tool_used": ["update_attendance_record"]
                        }
                    except Exception as e:
                        logger.warning(f"确定性更新考勤流程失败: {str(e)}")
                        # 失败后继续走通用流程

            # 每次请求创建全新的 executor，避免跨会话状态污染
            agent_executor = self._create_agent_executor(jwt_token)

            # 构建工具调用输入：附带严格JSON参数块，减少模型生成非法arguments的概率
            tool_input = task_description
            if params:
                strict_json_params = self._build_strict_json_block(params)
                tool_input += (
                    "\n参数（严格JSON，仅可使用该格式组装工具arguments）：\n"
                    f"{strict_json_params}"
                )
            
            logger.info(f"【工具执行】开始执行工具，输入: {tool_input}")
            logger.info(f"【工具执行】参数: {params}")

            # 执行工具调用
            max_retries = 2
            retry_count = 0
            last_error = None
            
            while retry_count <= max_retries:
                try:
                    result = await agent_executor.ainvoke({
                        "input": tool_input,
                        "chat_history": []
                    })
                    break
                except Exception as e:
                    error_str = str(e)
                    last_error = e
                    retry_count += 1
                    
                    logger.error(f"【工具执行】执行失败 (尝试 {retry_count}/{max_retries}): {error_str}")

                    # 检查是否是JSON格式错误
                    if "JSON format" in error_str or "function.arguments" in error_str:
                        logger.warning(f"JSON格式错误，尝试修复并重新执行 (尝试 {retry_count}/{max_retries})")
                        
                        # 尝试直接从参数构建工具调用，而不是依赖LLM
                        if "create_attendance_record" in task_description or "请假" in task_description:
                            logger.info("【工具执行】尝试使用确定性方式构建请假申请参数")
                            direct_result = await self._try_direct_attendance_call(params)
                            if direct_result:
                                return direct_result
                        
                        # 如果直接构建失败，重新构建工具输入，强调JSON格式要求
                        retry_input = (
                            tool_input
                            + "\n\n重要提示：\n"
                            + "1. function.arguments必须是严格有效的JSON格式\n"
                            + "2. 所有键名和字符串值必须使用双引号包围\n"
                            + "3. 不允许出现注释、单引号、尾逗号\n"
                            + "4. 仅从上面的'参数（严格JSON）'中选取字段构造arguments\n"
                            + "5. 创建考勤记录仅需: token, type, start_time, end_time, reason\n"
                            + "6. 示例格式：{\"token\": \"your_token\", \"type\": 1, \"start_time\": \"2026-04-26T00:00:00\", \"end_time\": \"2026-04-27T23:59:59\", \"reason\": \"请假原因\"}\n"
                        )
                        tool_input = retry_input
                    elif "缺少必需参数" in error_str:
                        logger.warning(f"缺少必需参数，尝试重新执行 (尝试 {retry_count}/{max_retries})")
                        # 重新构建工具输入，强调必需参数
                        retry_input = tool_input + "\n\n重要提示：\n创建考勤记录时，必须提供以下所有参数：\n- token: JWT token字符串\n- type: 考勤类型ID（整数）\n- start_time: 开始时间（格式：2026-04-26T00:00:00）\n- end_time: 结束时间（格式：2026-04-27T23:59:59）\n- reason: 请假原因（字符串）\n\n审批人由系统自动获取，无需传入responser参数。"
                        tool_input = retry_input
                    elif "400" in error_str or "InvalidParameter" in error_str:
                        logger.warning(f"参数错误，尝试重新执行 (尝试 {retry_count}/{max_retries})")
                        # 重新构建工具输入，强调参数格式
                        retry_input = tool_input + "\n\n重要提示：\n请确保所有参数格式正确：\n- token: 必须是有效的JWT字符串\n- type: 必须是整数类型的考勤类型ID\n- start_time和end_time: 必须是ISO格式的时间字符串\n- reason: 必须是非空字符串\n"
                        tool_input = retry_input
                    else:
                        # 其他错误，直接抛出
                        raise
            else:
                # 达到最大重试次数仍失败，尝试最后一次确定性调用
                logger.error(f"【工具执行】达到最大重试次数，尝试确定性调用")
                if "create_attendance_record" in task_description or "请假" in task_description:
                    direct_result = await self._try_direct_attendance_call(params)
                    if direct_result:
                        return direct_result
                
                # 如果所有尝试都失败，抛出原始错误
                logger.error(f"【工具执行】所有尝试都失败，执行失败: {str(last_error)}")
                raise last_error
            
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