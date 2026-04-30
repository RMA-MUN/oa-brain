# 智能办公自动化系统 (AI-Powered OA System)

一个前后端分离的智能办公自动化系统，深度集成AI能力，提供智能化的办公体验。

## 项目解决了什么问题

传统OA系统功能单一，无法满足AI时代的智能化需求。本项目对原有DjangoOA系统进行重构，融入人工智能技术，实现：

- **智能问答**：通过自然语言与系统交互，自动理解用户意图
- **知识库问答**：基于RAG技术实现企业知识的智能检索和问答
- **自动化任务处理**：AI自动分解任务、调用工具、执行操作
- **会话记忆管理**：支持多轮对话，上下文理解更准确

## 项目做了什么

系统采用**微服务架构**，将传统OA功能与AI能力解耦：

- **Django后端**：提供核心业务API（用户认证、考勤管理、员工管理、通知系统等）
- **Vue 3前端**：提供现代化用户界面
- **FastAPI AI服务**：提供多Agent协作、RAG知识库等智能服务

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端层 (Vue 3)                      │
└───────────────────────────┬─────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Django后端    │   │ FastAPI AI服务 │   │   RAG知识库   │
│  (业务API)     │◄──│  (多Agent协作)  │───│  (向量存储)    │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │
        ▼                   ▼
   ┌─────────┐        ┌─────────┐
   │  MySQL  │        │  Redis  │
   └─────────┘        └─────────┘
```

### 多Agent协作流程

```
用户请求 → MainAgent(主调度)
              ├── TaskDecomposer(任务分解)
              ├── ParamExtractionAgent(参数提取)
              ├── AgentRouter(路由选择)
              │       ├── ToolAgent(工具执行) → Django OA API
              │       ├── KnowledgeAgent(知识库) → RAG检索
              │       └── MemoryAgent(记忆管理) → Redis存储
              └── MemoryAgent(记忆保存)
```

## 核心Agent职责

| Agent | 职责 |
|-------|------|
| **MainAgent** | 主调度Agent，协调各子Agent工作流程 |
| **TaskDecomposer** | 将复杂任务分解为可执行的子任务 |
| **AgentRouter** | 根据任务类型智能选择合适的Agent |
| **ToolAgent** | 调用OA系统API执行具体业务操作 |
| **KnowledgeAgent** | 通过RAG技术查询知识库信息 |
| **MemoryAgent** | 管理会话记忆，支持多轮对话 |
| **ParamExtractionAgent** | 从用户话语中提取任务所需参数 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Django 5.2.6 + Django REST Framework |
| AI服务框架 | FastAPI + LangChain + LangGraph |
| 前端框架 | Vue 3 + Vite + Pinia + Element Plus |
| 业务数据库 | MySQL |
| 缓存/记忆存储 | Redis |
| 向量数据库 | ChromaDB |
| 异步任务 | Celery |
| 认证机制 | JWT |
| LLM支持 | Ollama / 阿里云百炼 |

## 功能模块

| 模块 | 功能说明 |
|------|----------|
| **officeAuth** | 用户注册登录、JWT认证、部门管理 |
| **officeAttendance** | 请假申请、审批流程、考勤记录查询 |
| **staff** | 员工信息管理、批量导出、异步邮件通知 |
| **file** | 文件上传下载、分类管理 |
| **inform** | 通知发布、部门可见性控制、阅读状态跟踪 |
| **home** | 首页信息展示、数据统计 |

## 项目结构

```
OAProject/
├── DjangoOfficeProject/      # Django后端服务
│   ├── apps/                # 业务应用模块
│   ├── DjangoOfficeProject/ # 项目配置
│   └── manage.py
│
├── oa-vue-project/          # Vue前端项目
│   ├── src/
│   │   ├── components/     # AI聊天组件
│   │   ├── views/          # 页面组件
│   │   └── stores/         # 状态管理
│   └── package.json
│
└── FastAPIAgentService/      # FastAPI AI微服务
    ├── app/
    │   ├── agent/          # Agent实现
    │   ├── rag/            # RAG服务
    │   ├── tools/          # 工具定义
    │   └── memory/         # 记忆管理
    └── main.py
```

## 快速启动

项目启动涉及三个服务，请参考各子项目的README：

- [DjangoOfficeProject/README.md](DjangoOfficeProject/README.md) - 后端服务启动
- [FastAPIAgentService/README.md](FastAPIAgentService/README.md) - AI服务启动
- [oa-vue-project/README.md](oa-vue-project/README.md) - 前端服务启动

## API接口

| 服务 | 模块 | 端点 |
|------|------|------|
| Django | 用户认证 | `/officeAuth/` |
| Django | 考勤管理 | `/Attendance/` |
| Django | 员工管理 | `/staff/` |
| Django | 文件管理 | `/file/` |
| Django | 通知管理 | `/inform/` |
| Django | 首页功能 | `/home/` |
| FastAPI | AI对话 | `/api/agent/chat/` |
| FastAPI | 工具调用 | `/api/agent/tools/` |
| FastAPI | 知识库 | `/api/agent/knowledge/` |
| FastAPI | 记忆管理 | `/api/agent/memory/` |
