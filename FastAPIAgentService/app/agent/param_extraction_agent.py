import json
import os
import re
from typing import Dict, Any, List

from app.agent.base import BaseAgent
from app.core.logger_handler import logger


class ParamExtractionAgent(BaseAgent):
    """参数提取Agent：专门从上下文中抽取子任务所需参数。"""

    def __init__(self):
        super().__init__("param_extraction_agent")
        self._llm = None

    def _create_llm(self):
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        base_url = os.getenv("ALIYUN_BASE_URL")
        try:
            from langchain_community.chat_models import ChatTongyi
        except Exception as e:
            logger.error(f"【参数提取Agent】大模型依赖加载失败: {e}", exc_info=True)
            return None
        return ChatTongyi(
            model=os.getenv("MAIN_AGENT_PARAM_MODEL", "qwen3-max"),
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        )

    @staticmethod
    def _build_context(user_input: str, chat_history: list | None) -> str:
        parts: List[str] = []
        if user_input:
            parts.append(f"【当前用户输入】\n{user_input.strip()}")
        if chat_history:
            lines = []
            for user_msg, assistant_msg in chat_history:
                if user_msg:
                    lines.append(f"用户: {user_msg}")
                if assistant_msg:
                    lines.append(f"助手: {assistant_msg}")
            if lines:
                parts.append("【历史对话】\n" + "\n".join(lines))
        return "\n\n".join(parts).strip()

    def _extract_params_from_text(self, text: str, required_params: list[str]) -> Dict[str, str]:
        """
        轻量规则提取（不调用 LLM）
        
        Args:
            text: 文本内容
            required_params: 需要提取的参数列表
        
        Returns:
            提取的参数字典
        """
        # 由于我们现在完全使用LLM进行参数提取，此方法不再使用
        # 保留此方法是为了向后兼容性
        return {}

    async def _llm_extract_params(
        self,
        *,
        required_params: List[str],
        subtask_description: str,
        task_type: str,
        context: str,
        merged_so_far: Dict[str, str],
    ) -> Dict[str, str]:
        missing_keys = [k for k in required_params if k not in merged_so_far or not str(merged_so_far.get(k, "")).strip()]
        if not missing_keys or not context.strip():
            return {}

        if self._llm is None:
            self._llm = self._create_llm()
        if self._llm is None:
            return {}

        keys_json = json.dumps(missing_keys, ensure_ascii=False)
        prompt = f"""你是参数抽取助手。根据「上下文」和「子任务说明」，为下列参数名填写取值。

规则：
1. 只输出一个 JSON 对象，不要 markdown 代码块，不要其它解释。
2. JSON 的键必须且只能来自下面「待填参数名」列表，键名逐字一致。
3. 若某参数在上下文中不存在或无法合理推断，该键值使用 null。
4. 若已有参数里某键已有非空值，不覆盖。

待填参数名：
{keys_json}

子任务类型：{task_type}
子任务说明：{subtask_description}
已有参数：{json.dumps(merged_so_far, ensure_ascii=False)}
上下文：
{context}
"""
        try:
            from langchain_core.messages import HumanMessage

            msg = await self._llm.ainvoke([HumanMessage(content=prompt)])
            raw = (msg.content or "").strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```\s*$", "", raw)
            data = json.loads(raw)
            if not isinstance(data, dict):
                return {}
            out: Dict[str, str] = {}
            for k in missing_keys:
                if k not in data:
                    continue
                v = data[k]
                if v is None:
                    continue
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, ensure_ascii=False)
                s = str(v).strip()
                if s:
                    out[k] = s
            return out
        except Exception as e:
            logger.warning(f"【参数提取Agent】LLM 抽取失败: {e}")
            return {}

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理参数提取任务
        
        Args:
            input_data: 输入数据，包含以下字段：
                - required_params: 需要提取的参数列表
                - existing_params: 已有的参数
                - user_input: 当前用户输入
                - chat_history: 历史对话记录
                - subtask_description: 子任务描述
                - task_type: 任务类型
        
        Returns:
            包含提取结果的字典，包含以下字段：
                - success: 是否成功
                - params: 提取的参数
                - missing_params: 缺失的参数
                - complete: 是否提取完成
        """
        required_params = input_data.get("required_params") or []
        existing_params = input_data.get("existing_params") or {}
        if not required_params:
            return {
                "success": True,
                "params": dict(existing_params),
                "missing_params": [],
                "complete": True,
            }

        context = self._build_context(
            input_data.get("user_input", ""),
            input_data.get("chat_history"),
        )

        merged_params = dict(existing_params)
        
        # 完全使用LLM进行参数提取，不使用规则匹配
        llm_extra = await self._llm_extract_params(
            required_params=list(required_params),
            subtask_description=input_data.get("subtask_description", ""),
            task_type=input_data.get("task_type", ""),
            context=context,
            merged_so_far=dict(merged_params),
        )
        if llm_extra:
            merged_params.update(llm_extra)
            logger.info(f"【参数提取Agent】LLM 提取: {llm_extra}")

        missing_params = [
            p for p in required_params
            if p not in merged_params or not str(merged_params.get(p, "")).strip()
        ]
        return {
            "success": True,
            "params": merged_params,
            "missing_params": missing_params,
            "complete": len(missing_params) == 0,
        }

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("param_extraction", "parameter_extraction")