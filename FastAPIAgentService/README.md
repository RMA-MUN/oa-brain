# FastAPIAgentService - AI智能服务

基于FastAPI的多Agent协作系统，通过自然语言理解用户需求，自动调用OA系统工具完成任务。

## 背景

FastAPIAgentService 与 DjangoOfficeProject 实现**解耦设计**，各自独立运行，通过API通信。

用户只需用自然语言描述需求，AI系统会自动：
1. 理解用户意图
2. 分解任务
3. 提取参数
4. 调用工具执行
5. 返回结果

## 环境要求

- Python 3.10+
- MySQL 5.7+（存储会话记忆）
- Redis 6.0+（缓存）
- Ollama 或 阿里云百炼（LLM支持）

## 技术栈

| 技术 | 说明 |
|------|------|
| FastAPI 0.100+ | 高性能异步API框架 |
| LangGraph | Agent工作流编排 |
| LangChain | Agent创建 |
| ChromaDB | 向量数据库 |
| Redis | 记忆存储 |
| MySQL | 会话数据存储 |
| Qwen3-Reranker | 重排序模型 |

## 项目结构

```
FastAPIAgentService/
├── app/
│   ├── agent/              # Agent实现
│   │   ├── main_agent.py           # 主调度
│   │   ├── task_decomposer.py      # 任务分解
│   │   ├── agent_router.py          # 路由选择
│   │   ├── tool_agent.py            # 工具执行
│   │   ├── knowledge_agent.py        # 知识库
│   │   ├── memory_agent.py          # 记忆管理
│   │   └── param_extraction_agent.py # 参数提取
│   ├── rag/                # RAG服务
│   │   ├── vector_store.py          # 向量存储
│   │   └── reorder_service.py       # 重排序
│   ├── tools/              # 工具定义
│   │   ├── oa_tools.py             # OA业务工具
│   │   └── rag_tools.py            # 知识库工具
│   └── router/             # API路由
├── data/chromadb/         # 向量数据
├── main.py                 # 应用入口
└── .env.example           # 环境变量模板
```

## 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/RMA-MUN/oa-brain
cd FastAPIAgentService
```

### 2. 创建环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM配置
DEEPSEEK_BASE_URL=http://localhost:11434
ALIYUN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ALIYUN_ACCESS_KEY_SECRET=your_key

# Django后端API
DJANGO_API_URL=http://127.0.0.1:8000

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=oa_agent

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 重排序模型（首次启动自动下载）
RERANKER_MODEL_PATH=D:\Hugging_Face\models\Qwen3-Reranker-0.6B
```

### 3. 安装依赖

```bash
pip install uv
uv sync
```

### 4. 启动服务

```bash
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

服务运行于：http://127.0.0.1:8001
API文档：http://127.0.0.1:8001/docs

离线api文档：[api.json](api.json)

## Agent架构

### 协作流程

```
用户请求
    │
    ▼
MainAgent ──────────────────────────┐
    │                               │
    ▼                               │
TaskDecomposer                      │
    │                               │
    ▼                               │
ParamExtractionAgent                │
    │                               │
    ▼                               │
AgentRouter ────┬───┬───┐           │
    │            │   │   │           │
    ▼            ▼   ▼   ▼           │
ToolAgent  Knowledge  Memory        │
    │       Agent    Agent          │
    │        │        │              │
    ▼        ▼        ▼              │
Django API  RAG    Redis            │
    │        │        │              │
    └────────┴────────┘              │
              │                      │
              ▼                      │
         MemoryAgent                  │
         (保存记忆)                   │
              │                      │
              ▼
         返回结果
```

### Agent职责

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **MainAgent** | 主调度，协调流程 | 用户请求 | 最终响应 |
| **TaskDecomposer** | 分解复杂任务 | 原始任务 | 子任务列表 |
| **ParamExtractionAgent** | 提取参数 | 任务上下文 | 结构化参数 |
| **AgentRouter** | 选择执行Agent | 任务类型 | 目标Agent |
| **ToolAgent** | 调用OA API | 参数 | API响应 |
| **KnowledgeAgent** | RAG检索 | 查询内容 | 知识片段 |
| **MemoryAgent** | 会话记忆 | 会话ID | 历史记录 |

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/agent/chat/` | POST | 对话请求 |
| `/api/agent/tools/list` | GET | 可用工具列表 |
| `/api/agent/tools/execute` | POST | 执行工具 |
| `/api/agent/knowledge/search` | POST | 知识库检索 |
| `/api/agent/knowledge/add` | POST | 添加知识文档 |
| `/api/agent/knowledge/{doc_id}` | DELETE | 删除知识文档 |
| `/api/agent/memory/{session_id}` | GET | 获取会话记忆 |
| `/api/agent/memory/{session_id}` | DELETE | 删除会话记忆 |
| `/api/health/` | GET | 健康检查 |

## 注意事项

1. **首次启动**：Reranker模型会自动下载，需确保网络畅通
2. **Ollama服务**：如使用Ollama，需先运行 `ollama serve`
3. **依赖服务**：确保MySQL和Redis服务正常运行
4. **Django依赖**：ToolAgent调用OA API前，需先启动Django服务
5. **Python版本**：推荐使用Python 3.12.4
