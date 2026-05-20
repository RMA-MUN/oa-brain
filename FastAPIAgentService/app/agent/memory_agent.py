from typing import Dict, Any, List, Tuple
from app.agent.base import BaseAgent
from app.core.logger_handler import logger
from app.services import session_manager as sm
from app.checkpoint import checkpoint_manager as cm


class MemoryAgent(BaseAgent):
    """记忆管理Agent，负责管理会话记忆"""

    def __init__(self):
        super().__init__("memory_agent")

    @staticmethod
    def _get_storage():
        """返回 checkpoint_manager 或 fallback 到 session_manager"""
        return cm.checkpoint_manager if cm.checkpoint_manager else sm.session_manager

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            session_id = input_data.get("session_id")
            user_id = input_data.get("user_id")
            action = input_data.get("action", "get_history")

            if action == "get_history":
                return await self._get_session_history(session_id, user_id)
            elif action == "add_memory":
                message = input_data.get("message")
                response = input_data.get("response")
                return await self._add_memory(session_id, user_id, message, response)
            elif action == "clear_memory":
                return await self._clear_memory(session_id, user_id)
            elif action == "get_user_sessions":
                return await self._get_user_sessions(user_id)
            else:
                return {"success": False, "error": f"不支持的操作: {action}"}

        except Exception as e:
            logger.error(f"【记忆管理】失败: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _get_storage_history(self, session_id: str, user_id: str):
        storage = self._get_storage()
        return await storage.get_history(session_id, user_id)

    async def _get_session_history(self, session_id: str, user_id: str) -> Dict[str, Any]:
        try:
            history = await self._get_storage_history(session_id, user_id)
            logger.info(f"【记忆管理】获取会话历史成功，会话ID: {session_id}, 记录数: {len(history)}")
            return {"success": True, "session_id": session_id, "user_id": user_id, "history": history, "history_length": len(history)}
        except Exception as e:
            logger.error(f"【记忆管理】获取会话历史失败: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _add_memory(self, session_id: str, user_id: str, message: str, response: str) -> Dict[str, Any]:
        try:
            storage = self._get_storage()
            await storage.add_message(session_id, user_id, message, response)
            logger.info(f"【记忆管理】添加记忆成功，会话ID: {session_id}")
            return {"success": True, "session_id": session_id, "user_id": user_id, "message_added": True}
        except Exception as e:
            logger.error(f"【记忆管理】添加记忆失败: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _clear_memory(self, session_id: str, user_id: str) -> Dict[str, Any]:
        try:
            storage = self._get_storage()
            await storage.clear_session(session_id, user_id)
            logger.info(f"【记忆管理】清除记忆成功，会话ID: {session_id}")
            return {"success": True, "session_id": session_id, "user_id": user_id, "memory_cleared": True}
        except Exception as e:
            logger.error(f"【记忆管理】清除记忆失败: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        try:
            storage = self._get_storage()
            sessions = await storage.get_user_sessions(user_id)
            logger.info(f"【记忆管理】获取用户会话成功，用户ID: {user_id}, 会话数: {len(sessions)}")
            return {"success": True, "user_id": user_id, "sessions": sessions, "session_count": len(sessions)}
        except Exception as e:
            logger.error(f"【记忆管理】获取用户会话失败: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def can_handle(self, task_type: str) -> bool:
        memory_task_types = ["memory_management", "history_query", "session_management", "memory_retrieval", "memory_storage"]
        return task_type in memory_task_types

    async def get_recent_memory(self, session_id: str, user_id: str, limit: int = 10) -> List[Tuple[str, str]]:
        try:
            history = await self._get_storage_history(session_id, user_id)
            return history[-limit:] if len(history) > limit else history
        except Exception as e:
            logger.error(f"【记忆管理】获取最近记忆失败: {str(e)}", exc_info=True)
            return []

    async def search_memory(self, session_id: str, user_id: str, keyword: str) -> List[Tuple[str, str]]:
        try:
            history = await self._get_storage_history(session_id, user_id)
            results = []
            for message, response in history:
                if keyword.lower() in message.lower() or keyword.lower() in response.lower():
                    results.append((message, response))
            return results
        except Exception as e:
            logger.error(f"【记忆管理】搜索记忆失败: {str(e)}", exc_info=True)
            return []