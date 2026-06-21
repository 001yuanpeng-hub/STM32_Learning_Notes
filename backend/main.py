from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PyPDF2 import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from anthropic import Anthropic
from database import engine, SessionLocal
import models
import schemas
import chromadb
import os
import json

load_dotenv()

app = FastAPI()

# 模型配置（都是 Anthropic 兼容 API）
MODEL_CONFIGS = {
    "mimo": {
        "model_name": "mimo-v2.5-pro",
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "base_url": os.getenv("ANTHROPIC_BASE_URL"),
    },
    "claude": {
        "model_name": "claude-sonnet-4-20250514",
        "api_key": os.getenv("CLAUDE_API_KEY"),
        "base_url": os.getenv("CLAUDE_BASE_URL"),  # 可选，默认官方地址
    },
}

def get_ai_client(model_name: str):
    """根据模型名称返回对应的 AI 客户端"""
    config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["mimo"])
    return Anthropic(api_key=config["api_key"], base_url=config["base_url"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="documents")

def get_embedding(text: str) -> list[float]:
    vector = model.encode(text)
    return vector.tolist()

def extract_text(filepath: str) -> str:
    if filepath.endswith((".txt", ".md")):
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()
    elif filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif filepath.endswith(".docx"):
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

def split_text(text: str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_text(text)
    return texts

def search(query: str, top_k: int = 3) -> list[dict]:
    vector = get_embedding(query)
    results = collection.query(
        query_embeddings = [vector],
        n_results = top_k
    )

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    return [
        {"text": doc, "filename": (meta or {}).get("filename", "鏈�鐭�")}
        for doc, meta in zip(documents, metadatas)
    ]

def build_prompt(question: str, chunks: list[dict]) -> str:
    context_parts = []
    for chunk in chunks:
        context_parts.append(f"[鏉ユ簮: {chunk['filename']}]\n{chunk['text']}")
    context = "\n\n---\n\n".join(context_parts)
    prompt = f"""浣犳槸涓€涓�涓撲笟鐨勬枃妗ｅ垎鏋愬姪鎵嬨€傝�锋牴鎹�浠ヤ笅鍙傝€冭祫鏂欏洖绛旂敤鎴风殑闂�棰樸€�

鍥炵瓟鏍煎紡瑕佹眰锛�
1. 浣跨敤 Markdown 鏍煎紡杈撳嚭
2. 闀挎�佃惤浣跨敤椤圭洰绗﹀彿鎷嗚В锛岀�佹�㈣緭鍑轰竴澶ф�垫枃瀛�
3. 澶氫釜瑕佺偣浣跨敤鍔犵矖鏍囬�樻垨鏁板瓧鍒楄〃
4. 鐩存帴缁欏嚭缁撹�猴紝閬垮厤鍐椾綑搴熻瘽
5. 涓嶈�佹爣娉ㄥ紩鐢ㄦ潵婧愶紝鐩存帴闄堣堪浜嬪疄

鍥炵瓟缁撴瀯锛�
- 鍏堢粰鍑烘牳蹇冩€荤粨锛堜竴鍙ヨ瘽缁撹�猴級
- 鍐嶈�︾粏鎷嗚В锛堝垎鐐归檲杩帮級
- 鏈€鍚庤ˉ鍏呭缓璁�锛堝�傛灉閫傜敤锛�

瑙勫垯锛�
- 鍙�鍩轰簬鎻愪緵鐨勫弬鑰冭祫鏂欏洖绛旓紝涓嶈�佺紪閫犱俊鎭�
- 濡傛灉鍙傝€冭祫鏂欎腑娌℃湁鐩稿叧淇℃伅锛岃�风洿鎺ヨ��"鏍规嵁鐜版湁璧勬枡锛屾棤娉曞洖绛旇繖涓�闂�棰�"

鍙傝€冭祫鏂欙細
{context}

鐢ㄦ埛闂�棰橈細{question}"""
    return prompt

@app.get("/history/")
async def get_history():
    db = SessionLocal()
    records = db.query(models.ChatHistory).order_by(models.ChatHistory.created_at.desc()).all()
    db.close()

    return [
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]

@app.post("/chat/", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest):
    question = request.question
    model_name = request.model or "mimo"

    # 1. 妫€绱㈢浉鍏虫枃妗�
    chunks = search(question, top_k=3)

    # 2. 鏋勫缓 prompt
    prompt = build_prompt(question, chunks)

    # 3. 璋冪敤 API
    config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["mimo"])
    client = get_ai_client(model_name)
    response = client.messages.create(
        model=config["model_name"],
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.content[0].text

    # 4. 瀛樺叆鏁版嵁搴�
    db = SessionLocal()
    try:
        db.add(models.ChatHistory(question=question, answer=answer))
        db.commit()
    finally:
        db.close()

    # 5. 杩斿洖缁撴灉
    return {
        "question": question,
        "answer": answer,
        "references": [c["text"] for c in chunks]
    }

@app.post("/chat/stream/")
async def chat_stream(request: schemas.ChatRequest):
    question = request.question
    model_name = request.model or "mimo"

    # 1. 妫€绱㈢浉鍏虫枃妗�
    chunks = search(question, top_k=3)

    # 2. 鏋勫缓 prompt
    prompt = build_prompt(question, chunks)

    # 3. 璋冪敤 API (娴佸紡)
    config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["mimo"])
    client = get_ai_client(model_name)

    async def generate():
        full_answer = ""
        with client.messages.stream(
            model=config["model_name"],
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                full_answer += text
                yield f"data: {json.dumps({'text': text, 'done': False})}\n\n"

        # 瀛樺叆鏁版嵁搴�
        db = SessionLocal()
        try:
            db.add(models.ChatHistory(question=question, answer=full_answer))
            db.commit()
        finally:
            db.close()

        # 鍙戦€佸畬鎴愪俊鍙�
        yield f"data: {json.dumps({'text': '', 'done': True, 'references': [c['text'] for c in chunks]})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/upload/")
async def upload_file(file: UploadFile):
    content = await file.read()
    filepath = f"uploads/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(content)

    text = extract_text(filepath)
    chunks = split_text(text)

    # 鍒犻櫎鍚屼竴鏂囦欢鐨勬棫鏁版嵁锛堝�傛灉閲嶆柊涓婁紶锛�
    try:
        ids_to_delete = []
        for i in range(100):
            doc_id = f"{file.filename}_{i}"
            try:
                collection.get(ids=[doc_id])
                ids_to_delete.append(doc_id)
            except Exception:
                break
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
    except Exception:
        pass

    # 鎶婃瘡鍧楀彉鎴愬悜閲忓苟瀛樺叆 ChromaDB
    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        collection.add(
            ids = [f"{file.filename}_{i}"],
            documents = [chunk],
            embeddings = [vector],
            metadatas = [{"filename": file.filename}]
        )

    return {
        "filename": file.filename,
        "chunks_count": len(chunks),
        "message": "宸插瓨鍏ュ悜閲忔暟鎹�搴�"
    }

@app.post("/search/")
async def search_data(question: str):
    results = search(question)
    return {
        "question": question,
        "results": results
    }
    


