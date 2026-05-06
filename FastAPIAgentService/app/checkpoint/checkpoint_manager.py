import asyncio
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Optional, Any
from langchain_core.messages import HumanMessage, AIMessage
from app.checkpoint.checkpoint_factory import CheckpointFactory
from app.core.logger_handler import logger
from app.services import session_manager as sm


class CheckpointManager:
    """
    Checkpoint 管理器，统一管理会话历史的获取和保存
    支持 Memory、SQLite、MySQL 三种后端
    """

    def __init__(self):
        self._checkpointer = None
        self._checkpoint_type = CheckpointFactory.get_checkpoint_type()
        self._lock = asyncio.Lock()
        self._initialized = False

    @classmethod
    async def create(cls) -> "CheckpointManager":
        """异步创建并初始化 CheckpointManager"""
        instance = cls()
        await instance._init_checkpointer()
        logger.info(f"【Checkpoint 管理器】初始化完成，类型: {instance._checkpoint_type}")
        return instance

    async def _init_checkpointer(self):
        """初始化 Checkpointer"""
        try:
            checkpointer = CheckpointFactory.create_checkpointer(self._checkpoint_type)
            if self._checkpoint_type == "sqlite":
                self._checkpointer = await checkpointer()
                self._initialized = True
            else:
                self._checkpointer = checkpointer
                self._initialized = True
        except Exception as e:
            logger.error(f"【Checkpoint 管理器】初始化失败: {str(e)}")
            raise

    async def get_history(self, session_id: str, user_id: str) -> List[Tuple[str, str]]:
        """
        获取会话历史

        :param session_id: 会话 ID
        :param user_id: 用户 ID
        :return: 会话历史列表 [(user_message, assistant_message), ...]
        """
        async with self._lock:
            if self._checkpoint_type in ("memory", "sqlite") and self._initialized:
                try:
                    return await sm.session_manager.get_history(session_id, user_id)
                except Exception as e:
                    logger.warning(f"【Checkpoint 管理器】从 MySQL 获取历史失败，回退到 Checkpoint: {str(e)}")
                    return await self._get_history_from_langgraph(session_id, user_id)
            elif self._checkpoint_type == "mysql":
                return await sm.session_manager.get_history(session_id, user_id)
            else:
                return []

    async def _get_history_from_langgraph(self, session_id: str, user_id: str) -> List[Tuple[str, str]]:
        """从 LangGraph Checkpoint 获取会话历史"""
        try:
            config = {"configurable": {"thread_id": session_id, "user_id": user_id, "checkpoint_ns": ""}}

            checkpoint = await self._checkpointer.aget(config)

            if checkpoint is None:
                return []

            history = []
            if isinstance(checkpoint, dict):
                channel_values = checkpoint.get("channel_values", {})
                if isinstance(channel_values, dict) and "messages" in channel_values:
                    messages = channel_values["messages"]
                    if isinstance(messages, list):
                        i = 0
                        while i < len(messages):
                            msg = messages[i]
                            if hasattr(msg, "type") and msg.type == "human":
                                if i + 1 < len(messages):
                                    next_msg = messages[i + 1]
                                    if hasattr(next_msg, "type") and next_msg.type == "ai":
                                        history.append((msg.content, next_msg.content))
                                        i += 2
                                        continue
                                i += 1
                            else:
                                i += 1
            return history
        except Exception as e:
            logger.error(f"【Checkpoint 管理器】从 LangGraph 获取历史失败: {str(e)}")
            return []

    async def add_message(self, session_id: str, user_id: str, user_message: str, assistant_message: str):
        """
        添加消息到会话历史

        :param session_id: 会话 ID
        :param user_id: 用户 ID
        :param user_message: 用户消息
        :param assistant_message: 助手消息
        """
        async with self._lock:
            if self._checkpoint_type in ("memory", "sqlite") and self._initialized:
                await self._add_message_to_langgraph(session_id, user_id, user_message, assistant_message)

            try:
                await sm.session_manager.add_message(session_id, user_id, user_message, assistant_message)
            except Exception as e:
                logger.error(f"【Checkpoint 管理器】写入 MySQL 失败: {str(e)}")

    async def _add_message_to_langgraph(self, session_id: str, user_id: str, user_message: str, assistant_message: str):
        """向 LangGraph Checkpoint 添加消息"""
        try:
            config = {"configurable": {"thread_id": session_id, "user_id": user_id, "checkpoint_ns": ""}}

            checkpoint = await self._checkpointer.aget(config)
            metadata = {"user_id": user_id, "thread_id": session_id, "source": "update", "step": 0}

            if checkpoint is None:
                messages = [HumanMessage(content=user_message), AIMessage(content=assistant_message)]
                ts = datetime.now(timezone.utc).isoformat()
                checkpoint = {
                    "v": 1,
                    "id": f"1ef4f797-{session_id[:12]}-8001-8a1503f9b875",
                    "ts": ts,
                    "channel_values": {"messages": messages},
                    "channel_versions": {"messages": 1},
                    "versions_seen": {"__input__": {}, "__start__": {}},
                }
                await self._checkpointer.aput(config, checkpoint, metadata, {})
            else:
                channel_values = checkpoint.get("channel_values", {})
                messages = channel_values.get("messages", []) if isinstance(channel_values, dict) else []

                if isinstance(messages, list):
                    messages.append(HumanMessage(content=user_message))
                    messages.append(AIMessage(content=assistant_message))
                else:
                    messages = [HumanMessage(content=user_message), AIMessage(content=assistant_message)]

                ts = datetime.now(timezone.utc).isoformat()
                checkpoint_id_parts = checkpoint.get("id", "1ef4f797-00000000-0001-8000-000000000000").split("-")
                checkpoint_id_parts[-2] = str(int(checkpoint_id_parts[-2]) + 1).zfill(4)
                new_id = "-".join(checkpoint_id_parts)

                checkpoint = {
                    "v": 1,
                    "id": new_id,
                    "ts": ts,
                    "channel_values": {"messages": messages},
                    "channel_versions": {"messages": checkpoint.get("channel_versions", {}).get("messages", 0) + 1},
                    "versions_seen": checkpoint.get("versions_seen", {"__input__": {}, "__start__": {}}),
                }
                await self._checkpointer.aput(config, checkpoint, metadata, {})

            logger.info(f"【Checkpoint 管理器】添加消息到会话: {session_id}")
        except Exception as e:
            logger.error(f"【Checkpoint 管理器】添加消息失败: {str(e)}")
            raise

    async def clear_session(self, session_id: str, user_id: str):
        """
        清除会话

        :param session_id: 会话 ID
        :param user_id: 用户 ID
        """
        async with self._lock:
            if self._checkpoint_type in ("memory", "sqlite") and self._initialized:
                await self._clear_session_from_langgraph(session_id, user_id)

            try:
                await sm.session_manager.clear_session(session_id, user_id)
            except Exception as e:
                logger.error(f"【Checkpoint 管理器】清除 MySQL 会话失败: {str(e)}")

    async def _clear_session_from_langgraph(self, session_id: str, user_id: str):
        """从 LangGraph Checkpoint 清除会话"""
        try:
            config = {"configurable": {"thread_id": session_id, "user_id": user_id, "checkpoint_ns": ""}}
            await self._checkpointer.adelete(config)
            logger.info(f"【Checkpoint 管理器】清除会话: {session_id}")
        except Exception as e:
            logger.error(f"【Checkpoint 管理器】清除会话失败: {str(e)}")
            raise

    async def get_user_sessions(self, user_id: str) -> List[Dict]:
        """
        获取用户所有会话

        :param user_id: 用户 ID
        :return: 会话列表
        """
        if self._checkpoint_type in ("memory", "sqlite") and self._initialized:
            try:
                return await sm.session_manager.get_user_sessions(user_id)
            except Exception as e:
                logger.warning(f"【Checkpoint 管理器】从 MySQL 获取会话列表失败，回退到 Checkpoint: {str(e)}")
                return await self._get_user_sessions_from_langgraph(user_id)
        elif self._checkpoint_type == "mysql":
            return await sm.session_manager.get_user_sessions(user_id)
        else:
            return []

    async def _get_user_sessions_from_langgraph(self, user_id: str) -> List[Dict]:
        """从 LangGraph Checkpoint 获取用户会话"""
        try:
            sessions = []
            config = {"configurable": {"user_id": user_id, "checkpoint_ns": ""}}
            async for checkpoint_tuple in self._checkpointer.alist(config):
                if checkpoint_tuple and len(checkpoint_tuple) > 0:
                    checkpoint_config = checkpoint_tuple[0]
                    thread_id = checkpoint_config.get('configurable', {}).get('thread_id')
                    if thread_id:
                        sessions.append({
                            "id": thread_id,
                            "title": "新的对话",
                            "created_at": None,
                            "updated_at": None
                        })
            return sessions
        except Exception as e:
            logger.error(f"【Checkpoint 管理器】获取用户会话失败: {str(e)}")
            return []

    def get_checkpoint_type(self) -> str:
        """获取当前 Checkpoint 类型"""
        return self._checkpoint_type


checkpoint_manager = None


async def init_checkpoint_manager():
    """初始化全局 Checkpoint 管理器"""
    global checkpoint_manager
    checkpoint_manager = await CheckpointManager.create()
    return checkpoint_manager