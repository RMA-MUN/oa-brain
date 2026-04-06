import pytest
from unittest.mock import patch, MagicMock
from app.config import settings


@pytest.fixture(autouse=True)
def mock_settings():
    """模拟配置"""
    with patch('app.config.settings') as mock_settings:
        mock_settings.DATABASE_URL = "sqlite:///:memory:"
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.DJANGO_API_URL = "http://localhost:8000/api/v1"
        mock_settings.DJANGO_API_TOKEN = "test_token"
        mock_settings.QWEN_API_KEY = "test_key"
        mock_settings.QWEN_MODEL = "qwen-plus"
        mock_settings.SECRET_KEY = "test_secret"
        mock_settings.CORS_ORIGINS = ["*"]
        yield mock_settings


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    mock_db = MagicMock()
    yield mock_db
