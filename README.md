# RAG 知识库

> 上传文档，基于内容智能问答。支持流式回答、多模型切换。

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + MySQL |
| 前端 | Vue3 + Vite |
| 向量数据库 | ChromaDB |
| Embedding | bge-small-zh-v1.5 |
| AI 模型 | MiMo / Claude (Anthropic 兼容 API) |
| 部署 | Docker + Nginx |

## 功能

- 支持上传 TXT、PDF、DOCX、Markdown 文档
- 自动分块并向量化存储到 ChromaDB
- 基于语义检索的智能问答（非关键词匹配）
- SSE 流式回答，打字机效果实时展示
- 支持 MiMo / Claude 模型一键切换
- 聊天历史持久化存储，页面刷新不丢失

## 项目结构

```
├── backend/
│   ├── main.py           # 核心逻辑：RAG 流程、API 路由、文档处理
│   ├── models.py         # 数据库模型
│   ├── schemas.py        # 请求/响应数据结构
│   ├── database.py       # 数据库连接配置
│   ├── requirements.txt  # Python 依赖
│   └── .env.example      # 环境变量模板
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   └── components/
│   │       └── ChatBox.vue  # 聊天界面核心组件
│   ├── vite.config.js    # Vite 配置（含 API 代理）
│   └── package.json
└── docker-compose.yml    # 一键容器化部署
```

## 本地运行

```bash
# 1. 配置环境变量
cp backend/.env.example backend/.env
```

编辑 `backend/.env`

```env
# MiMo / Claude API
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://api.xiaomimimo.com/anthropic
CLAUDE_API_KEY=your_api_key
CLAUDE_BASE_URL=https://api.anthropic.com

# MySQL
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/fastapi_db
```

```bash
# 2. 启动后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 3. 启动前端
cd frontend && npm install && npm run dev

# 打开浏览器 http://localhost:5173
```

## Docker 部署

在项目根目录创建 `.env` 文件：

```env
# MiMo / Claude API
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://api.xiaomimimo.com/anthropic
CLAUDE_API_KEY=your_api_key
CLAUDE_BASE_URL=https://api.anthropic.com
```

```bash
docker-compose up -d --build
# 访问 http://localhost
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/upload/` | 上传文档，自动分块并向量化 |
| `POST` | `/chat/` | 普通问答（返回完整回答） |
| `POST` | `/chat/stream/` | 流式问答（SSE 逐步返回） |
| `GET`  | `/history/` | 获取聊天历史记录 |
| `POST` | `/search/` | 仅检索，不调用 LLM |

## RAG 流程

```
用户提问 → 文本向量化 → ChromaDB 语义检索 Top-3
    → 构建 Prompt（指令 + 上下文 + 问题）
    → LLM 生成回答 → SSE 流式返回
```

## 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | 是 | MiMo API 密钥 |
| `ANTHROPIC_BASE_URL` | 是 | MiMo API 地址 |
| `CLAUDE_API_KEY` | 否 | Claude API 密钥 |
| `DATABASE_URL` | 否 | MySQL 连接地址 |

## 演示

[演示视频](./demo.mp4)
