# RAG 知识库

一个基于 RAG（检索增强生成）的文档问答系统。上传 PDF/TXT/DOCX 等文档，系统自动分块向量化，之后可以用自然语言提问，AI 会基于文档内容回答。

## 为什么做这个

想动手理解 RAG 的完整链路：文档解析 → 分块 → Embedding → 向量检索 → Prompt 构建 → LLM 生成。不只是调 API，而是把每个环节串起来跑通，踩一遍坑。

## 技术选型及原因

**Embedding 模型：bge-small-zh-v1.5**
- 试过几个中文 Embedding 模型，bge-small 在中文语义检索上效果够用，且模型体积小（~90MB），CPU 也能跑，不用 GPU
- 没选更大的 bge-large 是因为个人项目数据量小，小模型性价比更高

**向量数据库：ChromaDB**
- 选 ChromaDB 而不是 Milvus/Weaviate，因为它是嵌入式的，不需要额外部署服务，本地开发友好
- 缺点是数据量大了性能会下降，但个人项目够用

**分块策略：chunk_size=500, overlap=50**
- 试过 200/300/500/1000 不同大小。200 太碎，语义断裂严重；1000 太大，检索召回的内容不够精确
- 500 字大约是一两个段落的长度，问答效果和检索精度的平衡点
- overlap=50 是为了防止在句子中间切断导致语义丢失

**LLM：MiMo / Claude 双模型**
- MiMo 是小米的模型，中文效果不错且便宜
- Claude 作为备选，回答质量更稳定
- 两个都走 Anthropic 兼容 API，代码层面统一处理

## 踩过的坑

### SSE 流式输出

Anthropic Python SDK 的 `messages.stream()` 是同步的，但 FastAPI 的 `StreamingResponse` 需要 async generator。直接用会阻塞事件循环。

解决方案：用 `queue.Queue` 做线程间通信，后台线程跑同步流式调用，把 chunk 塞进队列，async generator 从队列取数据 yield 给前端。再用 `run_in_executor` 把队列的 `get()` 放到线程池避免阻塞。

```python
# 简化示意
async def generate():
    q = queue.Queue()
    def worker():
        with client.messages.stream(...) as stream:
            for text in stream.text_stream:
                q.put(text)
        q.put(None)  # 结束标记
    
    loop.run_in_executor(None, worker)
    while True:
        chunk = await loop.run_in_executor(None, q.get)
        if chunk is None: break
        yield f"data: {json.dumps({'text': chunk})}\n\n"
```

### Vite 代理 SSE 不生效

开发模式下 Vite 的 http-proxy 会缓冲 SSE 响应，导致前端收不到流式数据。

解决：在 vite.config.js 的 proxy 配置里加 `onProxyReq` 把 `Connection` header 设为空字符串，阻止代理接管连接。

### Nginx SSE 缓冲

生产环境 Nginx 默认会缓冲 proxy 响应，SSE 同样失效。

解决：nginx.conf 里对 `/api/` 路径关闭 `proxy_buffering` 和 `proxy_cache`。

### Redis decode 问题

一开始 Redis 连接没设 `decode_responses=True`，存进去的是 bytes，取出来需要 `.decode()`，但某些操作（比如 `hgetall`）返回的嵌套结构 decode 很麻烦。加上 `decode_responses=True` 后统一返回 str，省了很多处理。

## 功能

- 上传文档（TXT/PDF/DOCX/MD），自动分块存入 ChromaDB
- 基于语义检索的问答，不是关键词匹配
- SSE 流式回答，打字机效果
- MiMo / Claude 模型切换
- 对话历史持久化（MySQL），页面刷新不丢
- 侧边栏对话管理（新建/切换/重命名/删除）
- Redis 缓存（相同问题 60s 内直接返回）+ IP 限流（10次/分钟）

## 项目结构

```
backend/
├── main.py           # 核心逻辑：RAG 流程、API 路由、文档处理
├── models.py         # SQLAlchemy 数据库模型
├── schemas.py        # Pydantic 请求/响应结构
├── database.py       # MySQL 连接配置
└── requirements.txt

frontend/
├── src/
│   ├── App.vue
│   └── components/
│       ├── ChatBox.vue   # 聊天界面核心（含 SSE 流式读取）
│       └── Sidebar.vue   # 侧边栏对话管理
├── vite.config.js        # 含 API 代理 + SSE workaround
└── nginx.conf            # 生产环境 Nginx（SSE 优化）

docker-compose.yml        # MySQL + Redis + Backend + Frontend
```

## 本地运行

```bash
# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 填入 API Key

# 启动 Redis
docker run -d -p 6379:6379 redis:7

# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## Docker 部署

```bash
# 根目录创建 .env，填入 API Key
docker-compose up -d --build
# 访问 http://localhost
```

## 已知问题

- 文件上传没有做文件名消毒，存在路径遍历风险
- CORS 设为 `*`，生产环境需要收紧
- 错误处理用了大量 `except Exception: pass`，调试时不好定位问题
- 没有用户认证，所有人共享同一个知识库
