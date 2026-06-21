# RAG 知识库系统

> 基于检索增强生成（RAG）的智能问答系统，支持上传文档并基于文档内容进行问答。

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy |
| 前端 | Vue3 + Vite + Axios |
| 向量数据库 | ChromaDB |
| 关系数据库 | MySQL |
| Embedding | sentence-transformers (bge-small-zh) |
| AI 模型 | MiMo API (Anthropic 兼容) |
| 部署 | Docker + Nginx |

## 本地运行

```bash
# 1. 启动后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 2. 启动前端
cd frontend && npm install && npm run dev

# 3. 访问
http://localhost:5173
```

## 演示视频

[点击观看演示视频](./demo.mp4)

**功能演示：**
1. 上传文档（支持 TXT、PDF、DOCX）
2. 输入问题
3. AI 基于文档内容进行流式回答
4. 支持多文件同时检索
