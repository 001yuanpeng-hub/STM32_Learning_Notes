# CLAUDE.md — RAG 知识库项目规范

## 项目简介

基于 RAG（检索增强生成）的智能知识库系统。用户上传文档后，系统自动分块、向量化存储，支持基于语义检索的流式问答。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + MySQL + Redis + ChromaDB
- **前端**: Vue3 + Vite + Axios
- **Embedding**: bge-small-zh-v1.5 (sentence-transformers)
- **AI 模型**: MiMo / Claude (Anthropic 兼容 API)
- **部署**: Docker Compose + Nginx

## Claude 行为指引

- 修改代码前先读取目标文件，确认当前状态
- 后端改动后提示用户重启后端，前端改动后提示刷新浏览器
- Redis 操作必须用 `try/except` 保护，不能因 Redis 故障导致接口 500
- 数据库模型变更时提醒用户执行 `ALTER TABLE`
- 不要动 `#app` 的 `text-align`、`width`、`margin` 等全局布局属性
- SSE 相关代码不要用同步迭代，必须用异步或线程池
- 组件代码拆分到独立文件，不要全部堆在 ChatBox.vue

## 项目结构

```
backend/
├── main.py           # 核心逻辑：RAG 流程、API 路由、Redis 缓存/限流
├── models.py         # SQLAlchemy 数据库模型
├── schemas.py        # Pydantic 请求/响应结构
├── database.py       # MySQL 连接配置
├── requirements.txt  # Python 依赖
└── .env.example      # 环境变量模板

frontend/
├── src/
│   ├── main.js                # 前端入口文件
│   ├── App.vue                # 根组件
│   ├── style.css              # 全局样式
│   └── components/
│       ├── ChatBox.vue        # 聊天界面核心（含 SSE 流式读取）
│       └── Sidebar.vue        # 侧边栏对话管理
├── vite.config.js             # Vite 配置（含 API 代理）
└── nginx.conf                 # 生产环境 Nginx（SSE 优化）

docker-compose.yml             # MySQL + Redis + Backend + Frontend
```

## 开发规范

### 后端 (Python/FastAPI)

- 所有接口使用 `try/finally` 确保数据库连接关闭
- Redis 操作用 `try/except` 包裹，Redis 故障时跳过缓存，走正常流程
- SSE 流式接口使用 `async generator` + `StreamingResponse`
- Anthropic SDK 的同步流式调用通过 `run_in_executor` 放到线程执行，避免阻塞事件循环
- 数据库模型变更后需手动执行 `ALTER TABLE`，`create_all` 只建新表不加列

### 前端 (Vue3)

- 使用 Composition API (`<script setup>`)
- SSE 请求开发模式直连 `localhost:8000`（绕过 Vite 代理缓冲），生产模式走 `/api`
- 其他请求统一走 Vite 代理 (`/api` → `localhost:8000`)
- 组件拆分：`ChatBox.vue` 负责聊天逻辑，`Sidebar.vue` 负责对话管理

### Redis 使用

- **String**: 接口缓存 (`chat:{hash}`, TTL 60s)、限流计数 (`rate:{ip}`, TTL 60s)
- **Hash**: 对话元数据缓存 (`conv:{id}`, 字段: title, created_at)
- **Set**: 对话 ID 集合 (`conv:ids`)
- **List**: 对话消息缓存 (`conv:{id}:messages`, 最近 50 条)
- **Sorted Set**: 最近活跃对话 (`conv:active`, score 为时间戳)
- Redis 操作全部用 `try/except` 保护，故障时跳过缓存，走正常流程
- Redis 本地运行，连接命令：`redis-cli`

### API 路由表

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| `POST` | `/upload/` | 上传文档 | file: UploadFile |
| `POST` | `/chat/` | 普通问答 | question, model?, conversation_id? |
| `POST` | `/chat/stream/` | 流式问答 (SSE) | question, model?, conversation_id? |
| `POST` | `/search/` | 语义检索 | question |
| `GET` | `/conversations/` | 获取对话列表 | - |
| `POST` | `/conversations/` | 创建对话 | title? |
| `GET` | `/conversations/{id}/messages` | 获取对话消息 | - |
| `DELETE` | `/conversations/{id}` | 删除对话 | - |
| `PATCH` | `/conversations/{id}` | 重命名对话 | title |
| `GET` | `/history/` | 获取历史记录 | conversation_id? |

SSE 响应格式: `data: {"text": "...", "done": false}\n\n`

### 环境变量

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `ANTHROPIC_API_KEY` | 是 | MiMo API 密钥 | `sk-xxx` |
| `ANTHROPIC_BASE_URL` | 是 | MiMo API 地址 | `https://api.xiaomimimo.com/anthropic` |
| `CLAUDE_API_KEY` | 否 | Claude API 密钥 | `sk-ant-xxx` |
| `CLAUDE_BASE_URL` | 否 | Claude API 地址 | `https://api.anthropic.com` |
| `DATABASE_URL` | 否 | MySQL 连接地址 | `mysql+pymysql://root:root@localhost:3306/fastapi_db` |
| `REDIS_URL` | 否 | Redis 连接地址 | `redis://localhost:6379/0` |

## 本地启动

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

依赖服务: MySQL (3306)、Redis (6379)

### 数据库迁移

当 `models.py` 添加新字段后，需手动执行 `ALTER TABLE`（`create_all` 只建新表不加列）：

```sql
-- 连接 MySQL
mysql -u root -p fastapi_db

-- 添加字段
ALTER TABLE conversations ADD COLUMN new_field VARCHAR(200) NULL;
ALTER TABLE chat_history ADD COLUMN new_field TEXT NULL;

-- 查看表结构
DESCRIBE conversations;
```

当前表结构：
- **conversations**: id (INT), title (VARCHAR 200), created_at (DATETIME)
- **chat_history**: id (INT), conversation_id (INT FK), question (VARCHAR 500), answer (VARCHAR 2000), created_at (DATETIME)

## Docker 部署

```bash
docker-compose up -d --build
# 访问 http://localhost
```

环境变量配置在根目录 `.env` 文件。

## 代码风格

### Python

- 函数命名: `snake_case`，如 `build_prompt`、`get_ai_client`
- 字符串: 单引号为主，长字符串用三引号
- 类型提示: 函数参数和返回值使用 type hints
- 错误处理: `try/except Exception`，不吞掉异常，至少 `pass`

### Vue

- 组件命名: `PascalCase`，如 `ChatBox.vue`、`Sidebar.vue`
- 事件命名: `kebab-case`，如 `new-chat`、`select`
- 响应式变量: `ref()` 和 `reactive()`
- 样式: `<style scoped>` 避免全局污染

### Redis Key 命名

- 缓存: `chat:{md5_hash}`
- 限流: `rate:{ip}`
- 对话 Hash: `conv:{id}`
- 对话集合: `conv:ids`
- 对话消息: `conv:{id}:messages`
- 活跃对话: `conv:active`

## 注意事项

- `frontend/src/style.css` 的 `#app` 样式会影响全局布局，修改时注意不要加 `text-align: center` 或固定 `width`
- SSE 流式输出依赖 Nginx 的 `proxy_buffering off`，修改 nginx.conf 需谨慎
- PyTorch 安装使用 CPU 版本 (`pip install torch --index-url https://download.pytorch.org/whl/cpu`)，避免 Docker 镜像过大
