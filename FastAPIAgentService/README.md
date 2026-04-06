# FastAPI AI Agent 微服务

企业级AI智能办公Agent微服务，基于FastAPI和LangChain构建。

## 功能特性

- 🤖 **多智能体协作**: 使用LangGraph实现复杂的Agent协作流程
- 🛠️ **工具调用系统**: 标准化的工具定义和调用机制
- 🧠 **记忆管理**: 支持长短期记忆，提供上下文理解
- 📚 **RAG增强**: 集成企业知识库，提高回答准确性
- 🔐 **安全认证**: JWT认证机制，保障API安全
- 🐳 **容器化**: 支持Docker部署，便于环境管理

## 项目结构

```
FastAPIAgentService/
├── app/                          # 应用主目录
│   ├── api/                     # API路由
│   ├── agents/                  # Agent智能体
│   ├── tools/                   # 工具定义
│   ├── memory/                  # 记忆管理
│   ├── rag/                     # RAG知识库
│   ├── clients/                 # 客户端
│   └── utils/                   # 工具函数
├── tests/                       # 测试目录
├── scripts/                     # 脚本目录
├── requirements.txt             # Python依赖
├── Dockerfile                   # Docker构建文件
├── docker-compose.yml           # Docker Compose配置
└── .env.example                 # 环境变量示例
```

## 快速开始

### 环境准备

1. 创建环境变量文件：
```bash
cp .env.example .env
# 编辑.env文件，填入实际配置
```

2. 使用Docker启动：
```bash
docker-compose up --build
```

3. 本地开发启动：
```bash
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境
venv\Scripts\activate  # Windows
# 安装依赖
pip install -r requirements.txt
# 启动应用
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### API文档

- API文档: http://localhost:8001/docs
- ReDoc文档: http://localhost:8001/redoc

## API接口

### 对话接口
- `POST /api/agent/chat/` - 处理用户对话请求

### 工具接口
- `POST /api/agent/tools/` - 执行工具调用
- `GET /api/agent/tools/list` - 获取可用工具列表

### 记忆接口
- `POST /api/agent/memory/` - 保存记忆
- `GET /api/agent/memory/{session_id}` - 获取记忆
- `DELETE /api/agent/memory/{session_id}` - 清除记忆

### 知识库接口
- `POST /api/agent/knowledge/search` - 搜索知识库
- `POST /api/agent/knowledge/add` - 添加文档到知识库
- `GET /api/agent/knowledge/stats` - 获取知识库统计信息

## 技术栈

- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **缓存**: Redis
- **AI框架**: LangChain, LangGraph
- **向量数据库**: ChromaDB
- **认证**: JWT
- **部署**: Docker, Docker Compose

## 开发指南

### 运行测试

```bash
pytest
```

### 代码风格

```bash
black .
flake8 .
mypy .
```

## 扩展建议

- 添加更多办公场景工具（邮件、日程、会议等）
- 集成更多大模型服务
- 添加多语言支持
- 实现服务自动扩缩容
- 添加机器学习模型优化
