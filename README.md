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
- 聊天历史持久化存储

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
# 编辑 .env 填入你的 API Key

# 2. 启动后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 3. 启动前端
cd frontend && npm install && npm run dev

# 打开浏览器 http://localhost:5173
```

## Docker 部署

```bash
# 在项目根目录创建 .env，填入 API Key
docker-compose up -d --build
# 访问 http://localhost
```

## 演示

[演示视频](./demo.mp4)
