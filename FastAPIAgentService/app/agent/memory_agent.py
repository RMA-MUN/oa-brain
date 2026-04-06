from typing import Dict, Any, List, Tuple
from app.agent.base import BaseAgent
from app.core.logger_handler import logger
from app.services import session_manager as sm


class MemoryAgent(BaseAgent):
    """
    记忆管理Agent，负责管理会话记忆
    """
    
    def __init__(self):
        super().__init__("memory_agent")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，管理记忆"""
        try:
            session_id = input_data.get("session_id")
            user_id = input_data.get("user_id")
            action = input_data.get("action", "get_history")
            
            if action == "get_history":
                # 获取会话历史
                return await self._get_session_history(session_id, user_id)
            elif action == "add_memory":
                # 添加记忆
                message = input_data.get("message")
                response = input_data.get("response")
                return await self._add_memory(session_id, user_id, message, response)
            elif action == "clear_memory":
                # 清除记忆
                return await self._clear_memory(session_id, user_id)
            elif action == "get_user_sessions":
                # 获取用户所有会话
                return await self._get_user_sessions(user_id)
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作: {action}"
                }
                
        except Exception as e:
            logger.error(f"【记忆管理】失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_session_history(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """获取会话历史"""
        try:
            history = await sm.session_manager.get_history(session_id, user_id)
            
            logger.info(f"【记忆管理】获取会话历史成功，会话ID: {session_id}, 记录数: {len(history)}")
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "history": history,
                "history_length": len(history)
            }
            
        except Exception as e:
            logger.error(f"【记忆管理】获取会话历史失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _add_memory(self, session_id: str, user_id: str, message: str, response: str) -> Dict[str, Any]:
        """添加记忆"""
        try:
            await sm.session_manager.add_message(session_id, user_id, message, response)
            
            logger.info(f"【记忆管理】添加记忆成功，会话ID: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "message_added": True
            }
            
        except Exception as e:
            logger.error(f"【记忆管理】添加记忆失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _clear_memory(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """清除记忆"""
        try:
            await sm.session_manager.clear_session(session_id, user_id)
            
            logger.info(f"【记忆管理】清除记忆成功，会话ID: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "memory_cleared": True
            }
            
        except Exception as e:
            logger.error(f"【记忆管理】清除记忆失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """获取用户所有会话"""
        try:
            sessions = await sm.session_manager.get_user_sessions(user_id)
            
            logger.info(f"【记忆管理】获取用户会话成功，用户ID: {user_id}, 会话数: {len(sessions)}")
            
            return {
                "success": True,
                "user_id": user_id,
                "sessions": sessions,
                "session_count": len(sessions)
            }
            
        except Exception as e:
            logger.error(f"【记忆管理】获取用户会话失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def can_handle(self, task_type: str) -> bool:
        """判断是否能够处理特定类型的任务"""
        memory_task_types = [
            "memory_management",
            "history_query",
            "session_management",
            "memory_retrieval",
            "memory_storage"
        ]
        return task_type in memory_task_types
    
    async def get_recent_memory(self, session_id: str, user_id: str, limit: int = 10) -> List[Tuple[str, str]]:
        """获取最近的记忆"""
        try:
            history = await sm.session_manager.get_history(session_id, user_id)
            return history[-limit:] if len(history) > limit else history
            
        except Exception as e:
            logger.error(f"【记忆管理】获取最近记忆失败: {str(e)}", exc_info=True)
            return []
    
    async def search_memory(self, session_id: str, user_id: str, keyword: str) -> List[Tuple[str, str]]:
        """搜索记忆中的关键词"""
        try:
            history = await sm.session_manager.get_history(session_id, user_id)
            results = []
            
            for message, response in history:
                if keyword.lower() in message.lower() or keyword.lower() in response.lower():
                    results.append((message, response))
            
            return results
            
        except Exception as e:
            logger.error(f"【记忆管理】搜索记忆失败: {str(e)}", exc_info=True)
            return []