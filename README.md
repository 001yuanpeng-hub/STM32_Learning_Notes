# RAG 知识库

> 上传文档，基于内容智能问答。支持流式回答、多模型切换。

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + MySQL + Redis |
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
- 侧边栏对话管理，支持新建、切换、重命名、删除

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
│   │       ├── ChatBox.vue  # 聊天界面核心组件
│   │       └── Sidebar.vue  # 侧边栏对话管理
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

# Redis（可选，默认 localhost:6379）
REDIS_URL=redis://localhost:6379/0
```

```bash
# 2. 启动 Redis（本地安装或 Docker）
docker run -d -p 6379:6379 redis:7

# 3. 启动后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 4. 启动前端
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
| `POST` | `/chat/stream/` | 流式问答（SSE 逐步返回） |
| `GET` | `/conversations/` | 获取对话列表 |
| `POST` | `/conversations/` | 创建新对话 |
| `GET` | `/conversations/{id}/messages` | 获取对话消息 |
| `DELETE` | `/conversations/{id}` | 删除对话 |
| `PATCH` | `/conversations/{id}` | 重命名对话 |

## RAG 流程

```
用户提问 → 文本向量化 → ChromaDB 语义检索 Top-3
    → 构建 Prompt（指令 + 上下文 + 问题）
    → LLM 生成回答 → SSE 流式返回
```

## Redis 缓存

**为什么用 Redis？**
- 减少重复调用 AI API，节省 token 成本
- 提升接口响应速度（缓存命中时）
- 防止接口被滥用（限流）

**Redis 使用场景**：

| 数据类型 | Key | 用途 | TTL |
|----------|-----|------|-----|
| String | `chat:{hash}` | 接口缓存（相同问题 60s 内直接返回） | 60s |
| String | `rate:{ip}` | IP 限流（每分钟最多 10 次请求） | 60s |
| Hash | `conv:{id}` | 对话元数据（标题、创建时间） | 无 |
| Set | `conv:ids` | 对话 ID 集合 | 无 |
| List | `conv:{id}:messages` | 对话消息缓存（最近 50 条） | 无 |
| Sorted Set | `conv:active` | 最近活跃对话排序 | 无 |

**工作原理**：
```
用户提问 → 检查 Redis 缓存 → 命中？直接返回
                          → 未命中？调用 AI → 结果写入缓存 → 返回
```

## 演示

![demo](./demo.gif)
