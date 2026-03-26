from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.config.config import config
from app.rag.chunking import chunk_text
from app.rag.embedding import embed_text
from app.rag.llm import generate_chat
from app.rag.qdrant_store import ensure_collection, search, upsert_chunks
from app.rag.document_parser import parse_document


router = APIRouter(prefix="/rag", tags=["rag"])


class IngestDocument(BaseModel):
    doc_id: str = Field(..., description="文档ID，建议使用业务唯一键")
    text: str = Field(..., description="文档内容（纯文本，可抽取内容）")
    metadata: dict[str, Any] = Field(default_factory=dict, description="附加元数据（会随 chunk 一起存储）")


class IngestRequest(BaseModel):
    collection: str = Field(default_factory=lambda: config.QDRANT_COLLECTION)
    documents: list[IngestDocument]
    chunk_size: int = 800
    chunk_overlap: int = 120


class IngestResponse(BaseModel):
    collection: str
    documents_ingested: int
    chunks_ingested: int


class QueryRequest(BaseModel):
    collection: str = Field(default_factory=lambda: config.QDRANT_COLLECTION)
    question: str
    top_k: int = 8
    max_context_chunks: int = 5
    score_threshold: float | None = 0.3
    model: str | None = None


class Citation(BaseModel):
    index: int
    score: float
    doc_id: str | None = None
    chunk_index: int | None = None
    source: str | None = None
    text_excerpt: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    text_extracted: bool
    chunks_ingested: int


def _stable_chunk_id(doc_id: str, chunk_index: int) -> str:
    # uuid5 保证同一 doc_id + chunk_index 稳定
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{chunk_index}"))


@router.get("/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "qdrant_url": config.QDRANT_URL,
        "collection": config.QDRANT_COLLECTION,
        "embedding_model": config.EMBEDDING_MODEL,
        "model": config.MODEL,
        "has_api_key": bool(config.DASH_SCOPE_API_KEY),
        "api_key_length": len(config.DASH_SCOPE_API_KEY) if config.DASH_SCOPE_API_KEY else 0
    }


@router.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    if not req.documents:
        raise HTTPException(status_code=400, detail="documents is empty")

    vectors: list[list[float]] = []
    ids: list[str] = []
    payloads: list[dict[str, Any]] = []
    chunks_ingested = 0
    collection_ready = False

    for doc in req.documents:
        chunks = chunk_text(doc.text, chunk_size=req.chunk_size, overlap=req.chunk_overlap)
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            chunk_id = _stable_chunk_id(doc.doc_id, i)

            payload: dict[str, Any] = {
                "chunk_id": chunk_id,
                "doc_id": doc.doc_id,
                "chunk_index": i,
                "text": chunk,
            }
            # 合并元数据（避免覆盖 chunk/text 字段）
            for k, v in (doc.metadata or {}).items():
                if k in payload:
                    continue
                payload[k] = v

            try:
                vec = embed_text(chunk)
            except Exception as e:
                # 让客户端看到明确的失败原因（如 InvalidApiKey）。
                raise HTTPException(status_code=500, detail=str(e))
            # 第一次拿到 embedding 向量长度后，再创建/校验 collection 的向量维度。
            # 这样避免 embedding 模型维度与 EMBEDDING_DIM 配置不一致导致写入失败。
            if not collection_ready:
                ensure_collection(req.collection, dim=len(vec))
                collection_ready = True

            vectors.append(vec)
            ids.append(chunk_id)
            payloads.append(payload)
            chunks_ingested += 1

    if chunks_ingested:
        upsert_chunks(collection_name=req.collection, vectors=vectors, ids=ids, payloads=payloads)

    return IngestResponse(
        collection=req.collection,
        documents_ingested=len(req.documents),
        chunks_ingested=chunks_ingested,
    )


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question is empty")

    # 先生成 query embedding，再用真实向量维度创建/校验 collection。
    # 避免 embedding 模型维度与配置不一致导致检索失败。
    try:
        q_vec = embed_text(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    ensure_collection(req.collection, dim=len(q_vec))
    hits = search(collection_name=req.collection, query_vector=q_vec, top_k=req.top_k)

    if req.score_threshold is not None:
        hits = [h for h in hits if h.get("score", 0.0) >= req.score_threshold]

    hits = hits[: req.max_context_chunks]

    context_blocks: list[str] = []
    citations: list[Citation] = []

    for idx, h in enumerate(hits, start=1):
        payload = h.get("payload") or {}
        chunk_text_value = payload.get("text") or ""
        doc_id = payload.get("doc_id")
        chunk_index = payload.get("chunk_index")
        source = payload.get("source")

        context_blocks.append(
            f"[{idx}] Source: {source or ''} DocID: {doc_id or ''} ChunkIndex: {chunk_index or ''}\n{chunk_text_value}"
        )
        excerpt = chunk_text_value.strip().replace("\n", " ")
        if len(excerpt) > 300:
            excerpt = excerpt[:300] + "..."

        citations.append(
            Citation(
                index=idx,
                score=float(h.get("score", 0.0)),
                doc_id=str(doc_id) if doc_id is not None else None,
                chunk_index=int(chunk_index) if chunk_index is not None else None,
                source=str(source) if source is not None else None,
                text_excerpt=excerpt,
            )
        )

    context = "\n\n".join(context_blocks)
    system_prompt = (
        "你是一个企业文档问答助手。你必须只根据用户提供的资料回答问题，"
        "如果资料不足以回答，必须明确说：'我无法根据提供的资料回答。'"
    )
    user_prompt = (
        f"用户问题：{req.question}\n\n"
        f"资料（按相关性排序）：\n{context}\n\n"
        "请给出简洁、准确的回答，并在回答中使用引用编号（例如 [1]、[2]）。"
    )

    try:
        answer = generate_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=req.model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(answer=answer, citations=citations)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    doc_id: str,
    file: UploadFile = File(...),
    metadata: str = None
):
    """
    上传并处理文档（PDF、Excel、Word、txt 等）
    """
    import json
    
    # 解析 metadata
    metadata_dict = {}
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata format")
    
    # 保存上传的文件
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # 解析文档
        text = parse_document(file_path)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text extracted from document")
        
        # 处理文档（分块、向量化、存储）
        chunks = chunk_text(text)
        vectors = []
        ids = []
        payloads = []
        chunks_ingested = 0
        collection_ready = False
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            chunk_id = _stable_chunk_id(doc_id, i)
            
            payload: dict[str, Any] = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "chunk_index": i,
                "text": chunk,
                "filename": file.filename,
            }
            # 合并元数据
            for k, v in metadata_dict.items():
                if k in payload:
                    continue
                payload[k] = v
            
            try:
                vec = embed_text(chunk)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            
            if not collection_ready:
                ensure_collection(config.QDRANT_COLLECTION, dim=len(vec))
                collection_ready = True
            
            vectors.append(vec)
            ids.append(chunk_id)
            payloads.append(payload)
            chunks_ingested += 1
        
        if chunks_ingested:
            upsert_chunks(
                collection_name=config.QDRANT_COLLECTION,
                vectors=vectors,
                ids=ids,
                payloads=payloads
            )
        
        return DocumentUploadResponse(
            doc_id=doc_id,
            filename=file.filename,
            text_extracted=True,
            chunks_ingested=chunks_ingested
        )
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

