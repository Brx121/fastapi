# RAG 模块多文档类型支持

## 1. 概述

本指南介绍如何扩展 RAG 模块，使其支持处理 PDF、Excel、Docs 等不同类型的文档，实现更全面的企业文档智能问答系统。

## 2. 技术方案

### 2.1 文档处理流程

```
文档输入 → 文档解析 → 文本提取 → 文本分块 → 向量化 → 存储到向量数据库
```

### 2.2 所需依赖

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| **PyPDF2** | 最新 | PDF 文档解析 |
| **openpyxl** | 最新 | Excel 文档解析 |
| **python-docx** | 最新 | Word 文档解析 |
| **langchain** | 最新 | 文档处理工具（可选） |

## 3. 代码实现

### 3.1 文档解析模块

创建 `app/rag/document_parser.py` 文件：

```python
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import PyPDF2
from docx import Document
from openpyxl import load_workbook


def parse_pdf(file_path: str) -> str:
    """
    解析 PDF 文档并提取文本
    """
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text() + "\n"
    return text


def parse_excel(file_path: str) -> str:
    """
    解析 Excel 文档并提取文本
    """
    text = ""
    wb = load_workbook(file_path)
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        text += f"Sheet: {sheet_name}\n"
        for row in sheet.iter_rows(values_only=True):
            row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
            if row_text.strip():
                text += row_text + "\n"
        text += "\n"
    return text


def parse_docx(file_path: str) -> str:
    """
    解析 Word 文档并提取文本
    """
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"
    return text


def parse_document(file_path: str) -> str:
    """
    根据文件扩展名自动选择解析器
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return parse_pdf(file_path)
    elif ext in ['.xlsx', '.xls']:
        return parse_excel(file_path)
    elif ext == '.docx':
        return parse_docx(file_path)
    else:
        # 对于其他文件类型，尝试直接读取文本
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            raise ValueError(f"Unsupported file type: {ext}")
```

### 3.2 文档上传 API

修改 `app/rag/apis.py` 文件，添加文档上传接口：

```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

# ... 现有代码 ...

class DocumentUploadRequest(BaseModel):
    doc_id: str = Field(..., description="文档ID，建议使用业务唯一键")
    metadata: dict[str, Any] = Field(default_factory=dict, description="附加元数据")


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    text_extracted: bool
    chunks_ingested: int


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    doc_id: str,
    file: UploadFile = File(...),
    metadata: dict[str, Any] = None
):
    """
    上传并处理文档（PDF、Excel、Word 等）
    """
    if metadata is None:
        metadata = {}
    
    # 保存上传的文件
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # 解析文档
        from app.rag.document_parser import parse_document
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
            for k, v in (metadata or {}).items():
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
```

### 3.3 依赖安装

在 `requirements.txt` 文件中添加新的依赖：

```
fastapi
uvicorn
sqlalchemy
pymysql
python-dotenv
requests
dashscope
qdrant-client
PyPDF2
openpyxl
python-docx
```

## 4. 使用方法

### 4.1 上传文档

**使用 curl 上传 PDF 文档**：

```bash
curl -X POST "http://localhost:8001/rag/upload?doc_id=pdf_001" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf" \
  -F "metadata={\"source\": \"PDF文档\", \"category\": \"技术文档\"}"
```

**使用 curl 上传 Excel 文档**：

```bash
curl -X POST "http://localhost:8001/rag/upload?doc_id=excel_001" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/spreadsheet.xlsx" \
  -F "metadata={\"source\": \"Excel文档\", \"category\": \"数据表格\"}"
```

**使用 curl 上传 Word 文档**：

```bash
curl -X POST "http://localhost:8001/rag/upload?doc_id=docx_001" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.docx" \
  -F "metadata={\"source\": \"Word文档\", \"category\": \"报告\"}"
```

### 4.2 提问

上传文档后，可以像之前一样使用 `/rag/query` 接口提问：

```bash
curl -X POST http://localhost:8001/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档中关于FastAPI的内容是什么？"
  }'
```

## 5. 高级配置

### 5.1 文档处理优化

#### 5.1.1 PDF 处理优化

- **OCR 支持**：对于扫描的 PDF，可以集成 OCR 工具（如 Tesseract）
- **页面范围**：支持指定处理的页面范围
- **表格提取**：优化 PDF 中表格的提取

#### 5.1.2 Excel 处理优化

- **工作表过滤**：支持只处理指定的工作表
- **数据类型识别**：优化不同数据类型的处理
- **公式处理**：处理 Excel 中的公式

#### 5.1.3 Word 处理优化

- **样式保留**：保留文档的标题、列表等样式信息
- **表格处理**：优化 Word 中表格的提取
- **图片处理**：支持图片的描述提取

### 5.2 批量处理

对于大量文档的处理，可以实现批量上传和处理功能：

```python
@router.post("/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    metadata: dict[str, Any] = None
):
    """
    批量上传并处理文档
    """
    results = []
    for file in files:
        # 生成唯一的 doc_id
        doc_id = f"{os.path.splitext(file.filename)[0]}_{int(time.time())}"
        # 处理单个文件
        result = await upload_document(doc_id, file, metadata)
        results.append(result)
    return {"results": results}
```

## 6. 性能考虑

### 6.1 内存管理

- **大文件处理**：对于大文件，考虑使用流式处理
- **临时文件**：及时清理临时文件，避免磁盘空间占用
- **并行处理**：对于批量文档，考虑使用并行处理

### 6.2 处理速度

- **PDF 处理**：PDF 解析相对较慢，考虑使用异步处理
- **缓存机制**：对于重复处理的文档，考虑使用缓存
- **分块策略**：根据文档类型调整分块策略

## 7. 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| **PDF 解析失败** | PDF 加密或损坏 | 检查 PDF 文件是否可正常打开 |
| **Excel 解析失败** | 版本不兼容 | 确保使用最新版本的 openpyxl |
| **Word 解析失败** | 格式不支持 | 确保文档是 .docx 格式 |
| **内存不足** | 文件过大 | 增加服务器内存或优化文件处理逻辑 |
| **处理超时** | 文档过大或复杂 | 增加超时时间或优化处理逻辑 |

## 8. 扩展建议

### 8.1 多语言支持

- 增加对多语言文档的支持
- 优化不同语言的文本提取和向量化

### 8.2 文档版本管理

- 实现文档版本管理，支持版本对比
- 跟踪文档的更新历史

### 8.3 智能分类

- 自动对上传的文档进行分类
- 基于文档内容生成标签

### 8.4 多模态支持

- 增加对图片、视频等多媒体内容的支持
- 实现图文结合的问答能力

## 9. 总结

通过扩展 RAG 模块，添加对 PDF、Excel、Docs 等文档类型的支持，可以构建一个更全面、更强大的企业文档智能问答系统。系统能够自动解析不同类型的文档，提取文本内容，然后通过向量检索和大语言模型生成准确的回答。

这种方案不仅提高了系统的实用性，也为企业提供了更高效的知识管理工具，帮助员工快速获取所需信息，提高工作效率。