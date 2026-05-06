import os
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CheckpointFactory:
    """Checkpoint 工厂类，根据配置创建对应后端的 Checkpointer"""

    @staticmethod
    def create_checkpointer(checkpoint_type: Optional[str] = None):
        """
        根据配置创建 Checkpointer 实例

        :param checkpoint_type: Checkpoint 类型 (memory, sqlite, mysql)
        :return: Checkpointer 实例
        """
        checkpoint_type = checkpoint_type or os.getenv("CHECKPOINT_TYPE", "memory").lower()

        if checkpoint_type == "sqlite":
            return CheckpointFactory._create_sqlite_checkpointer()
        elif checkpoint_type == "memory":
            return CheckpointFactory._create_memory_checkpointer()
        elif checkpoint_type == "mysql":
            return CheckpointFactory._create_mysql_checkpointer()
        else:
            raise ValueError(f"不支持的 Checkpoint 类型: {checkpoint_type}")

    @staticmethod
    def _create_memory_checkpointer():
        """创建内存 Checkpointer"""
        from langgraph.checkpoint.memory import InMemorySaver
        return InMemorySaver()

    @staticmethod
    def _create_sqlite_checkpointer():
        """创建 SQLite Checkpointer"""
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        import aiosqlite

        sqlite_path = os.getenv("CHECKPOINT_SQLITE_PATH", None)

        if sqlite_path is None:
            sqlite_path = os.path.join(PROJECT_ROOT, "logs", "checkpoint", "checkpoints.db")
        elif not os.path.isabs(sqlite_path):
            sqlite_path = os.path.join(PROJECT_ROOT, sqlite_path)

        sqlite_path = os.path.normpath(sqlite_path)

        db_dir = os.path.dirname(sqlite_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # debug内容，保留，方便后续复用
        # print(f"[DEBUG] PROJECT_ROOT: {PROJECT_ROOT}")
        # print(f"[DEBUG] sqlite_path (normpath): {sqlite_path}")
        # print(f"[DEBUG] sqlite_path exists: {os.path.exists(sqlite_path)}")
        # print(f"[DEBUG] db_dir exists: {os.path.exists(db_dir)}")
        # print(f"[DEBUG] db_dir: {db_dir}")

        async def create_checkpointer():
            conn = await aiosqlite.connect(sqlite_path)
            saver = AsyncSqliteSaver(conn)
            return saver

        return create_checkpointer

    @staticmethod
    def _create_mysql_checkpointer():
        """创建 MySQL Checkpointer（使用 SQLAlchemy 包装）"""
        from app.services.database_session_manager import database_session_manager
        return database_session_manager

    @staticmethod
    def get_checkpoint_type() -> str:
        """获取当前配置的 Checkpoint 类型"""
        return os.getenv("CHECKPOINT_TYPE", "memory").lower()