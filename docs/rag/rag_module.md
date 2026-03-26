# RAG 模块文档

## 1. 模块概述

RAG（Retrieval-Augmented Generation）模块是一个基于向量检索和大语言模型的智能问答系统，用于企业文档的智能查询和知识管理。

### 1.1 核心功能

- **文档摄入**：将企业文档分块、向量化并存储到向量数据库
- **智能问答**：根据用户问题检索相关文档并生成准确回答
- **引用追踪**：在回答中包含引用编号，支持溯源
- **相关性排序**：按相似度排序返回最相关的文档片段

## 2. 技术架构

### 2.1 系统架构

```
用户提问 → 向量化 → 向量检索 → 上下文构建 → LLM生成答案 → 返回答案+引用
```

### 2.2 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| **向量数据库** | Qdrant | 存储和检索文档向量 |
| **Embedding模型** | DashScope text-embedding-v2 | 文本向量化（1536维） |
| **LLM模型** | DashScope qwen-plus | 生成答案 |
| **API框架** | FastAPI | 提供 REST API |
| **文本分块** | 自定义字符级切分 | 文档分块 |

## 3. 目录结构

```
app/
└── rag/
    ├── __init__.py
    ├── apis.py          # API 接口定义
    ├── chunking.py      # 文本分块逻辑
    ├── embedding.py     # 文本向量化
    ├── llm.py           # LLM 调用
    ├── qdrant_store.py  # 向量数据库操作
```

## 4. 核心模块详解

### 4.1 文档摄入流程

**入口**: `POST /rag/ingest`

**处理步骤**:

1. **接收文档** - 接收包含 `doc_id`、`text` 和 `metadata` 的文档列表
2. **文本分块** - 按 `chunk_size`（默认800字符）切分文本，使用 `overlap`（默认120字符）保留边界信息
3. **向量化** - 调用 DashScope 的 `text-embedding-v2` 模型将每个文本块转换为 1536 维向量
4. **存储到向量数据库** - 自动创建/校验 Qdrant collection，存储向量、ID 和 payload

**代码示例**:

```python
# 文本分块
def chunk_text(text: str, *, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """按字符长度切分文本，并使用 overlap 保留边界信息"""
    # 实现逻辑...

# 向量化
def embed_text(text: str) -> list[float]:
    """调用 DashScope 的 TextEmbedding 获取向量"""
    # 实现逻辑...

# 存储到向量数据库
def upsert_chunks(*, collection_name: str, vectors: list[list[float]], ids: list[str], payloads: list[dict[str, Any]]) -> None:
    """将向量、ID 和 payload 存储到 Qdrant"""
    # 实现逻辑...
```

### 4.2 问答查询流程

**入口**: `POST /rag/query`

**处理步骤**:

1. **问题向量化** - 将用户问题转换为向量（使用相同的 embedding 模型）
2. **向量检索** - 在 Qdrant 中进行余弦相似度搜索，返回最相关的文档块
3. **构建上下文** - 将检索到的文档块组织成上下文格式
4. **生成答案** - 调用 LLM 模型生成答案，要求在答案中使用引用编号
5. **返回结果** - 返回答案和引用列表

**代码示例**:

```python
# 向量检索
def search(*, collection_name: str, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
    """在 Qdrant 中搜索相关向量"""
    # 实现逻辑...

# 生成答案
def generate_chat(messages: list[dict], *, model: str | None = None) -> str:
    """使用 DashScope Generation 生成回复"""
    # 实现逻辑...
```

## 5. API 接口

### 5.1 健康检查

- **端点**: `GET /rag/health`
- **功能**: 检查 RAG 模块的健康状态
- **响应示例**:
  ```json
  {
    "status": "healthy",
    "qdrant_url": "http://localhost:6333",
    "collection": "rag_collection",
    "embedding_model": "text-embedding-v2",
    "model": "qwen-plus",
    "has_api_key": true,
    "api_key_length": 35
  }
  ```

### 5.2 文档摄入

- **端点**: `POST /rag/ingest`
- **功能**: 摄入文档到向量数据库
- **请求示例**:
  ```json
  {
    "documents": [
      {
        "doc_id": "doc_001",
        "text": "FastAPI是一个现代的、快速的Python Web框架...",
        "metadata": {"source": "技术文档", "category": "框架"}
      }
    ],
    "chunk_size": 800,
    "chunk_overlap": 120
  }
  ```
- **响应示例**:
  ```json
  {
    "collection": "rag_collection",
    "documents_ingested": 1,
    "chunks_ingested": 1
  }
  ```

### 5.3 问答查询

- **端点**: `POST /rag/query`
- **功能**: 根据问题检索相关文档并生成答案
- **请求示例**:
  ```json
  {
    "question": "FastAPI是什么？它有什么特点？",
    "top_k": 8,
    "max_context_chunks": 5
  }
  ```
- **响应示例**:
  ```json
  {
    "answer": "FastAPI是一个现代的、快速的Python Web框架，专门用于构建API... [1]",
    "citations": [
      {
        "index": 1,
        "score": 0.7893498,
        "doc_id": "doc_001",
        "chunk_index": 0,
        "source": "技术文档",
        "text_excerpt": "FastAPI是一个现代的、快速的Python Web框架..."
      }
    ]
  }
  ```

## 6. 配置说明

### 6.1 环境变量

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| **DASH_SCOPE_API_KEY** | - | DashScope API 密钥 |
| **MODEL** | qwen-plus | LLM 模型名称 |
| **EMBEDDING_MODEL** | text-embedding-v2 | Embedding 模型名称 |
| **EMBEDDING_DIM** | 1536 | 向量维度 |
| **QDRANT_URL** | http://localhost:6333 | Qdrant 服务地址 |
| **QDRANT_COLLECTION** | rag_collection | 向量集合名称 |

### 6.2 配置文件

```python
# app/config/config.py
class Config:
    # DashScope 配置
    DASH_SCOPE_API_KEY = os.getenv("DASH_SCOPE_API_KEY") or os.getenv("API_KEY")
    MODEL = os.getenv("MODEL", "qwen-plus")
    
    # Embedding 配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
    
    # Qdrant 配置
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_collection")
```

## 7. 部署与运行

### 7.1 Docker Compose 部署

**配置**:

```yaml
# docker-compose.yml
qdrant:
  image: qdrant/qdrant:latest
  container_name: qdrant
  ports:
    - "6333:6333"
  volumes:
    - qdrant-data:/qdrant/storage
  restart: always
  networks:
    - app-network

fastapi-app:
  build: .
  container_name: fastapi-app
  ports:
    - "8001:8001"
  environment:
    - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    - MODEL=qwen-plus
    - QDRANT_URL=http://qdrant:6333
    - QDRANT_COLLECTION=rag_collection
    - EMBEDDING_MODEL=text-embedding-v2
  volumes:
    - .:/app
  restart: always
  depends_on:
    - qdrant
  networks:
    - app-network
```

**启动命令**:

```bash
docker compose up -d
```

### 7.2 本地运行

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **启动服务**:
   ```bash
   python -m uvicorn main:app --reload --port 8001 --host 0.0.0.0
   ```

## 8. 使用示例

### 8.1 摄入文档

```bash
curl -X POST http://localhost:8001/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "doc_id": "doc_001",
        "text": "FastAPI是一个现代的、快速的Python Web框架，用于构建API。它基于标准Python类型提示，具有自动API文档生成功能。FastAPI支持异步处理，性能优异，是构建API的理想选择。",
        "metadata": {"source": "技术文档", "category": "框架"}
      }
    ]
  }'
```

### 8.2 提问

```bash
curl -X POST http://localhost:8001/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "FastAPI是什么？它有什么特点？"
  }'
```

## 9. 性能优化

### 9.1 文本分块优化

- **调整 chunk_size**：根据文档类型和长度调整分块大小
- **优化 overlap**：合理设置重叠部分，确保上下文连续性

### 9.2 向量检索优化

- **调整 top_k**：根据文档数量和相关性要求调整返回的文档数量
- **设置 score_threshold**：过滤低质量的检索结果

### 9.3 模型选择

- **Embedding模型**：根据精度和速度要求选择合适的模型
- **LLM模型**：根据生成质量和响应速度选择合适的模型

## 10. 故障排查

### 10.1 常见错误

| 错误 | 可能原因 | 解决方案 |
|------|----------|----------|
| **AccessDenied** | API密钥无效或模型不匹配 | 检查API密钥和模型配置 |
| **Qdrant连接失败** | Qdrant服务未启动 | 检查Qdrant服务状态 |
| **向量维度不匹配** | Embedding模型与配置不一致 | 检查EMBEDDING_DIM配置 |
| **检索结果质量差** | 文档质量或分块策略问题 | 优化文档质量和分块策略 |

### 10.2 日志查看

```bash
# 查看FastAPI服务日志
docker logs fastapi-app

# 查看Qdrant服务日志
docker logs qdrant
```

## 11. 扩展与未来规划

### 11.1 功能扩展

- **多模态支持**：增加对图片、视频等多媒体内容的支持
- **对话历史**：支持上下文对话，保持对话连续性
- **个性化推荐**：根据用户历史查询优化推荐结果
- **自动文档更新**：支持文档的自动更新和版本管理

### 11.2 性能优化

- **缓存机制**：增加查询缓存，提高响应速度
- **批量处理**：优化大批量文档的摄入性能
- **分布式部署**：支持多节点分布式部署，提高系统 scalability

## 12. 总结

RAG模块是一个功能强大的智能问答系统，通过向量检索和大语言模型的结合，为企业提供了高效的文档查询和知识管理能力。系统具有以下特点：

- **准确性**：基于检索到的文档生成答案，确保信息的准确性
- **可追溯性**：提供详细的引用信息，支持答案溯源
- **灵活性**：支持自定义配置和扩展
- **易于部署**：提供Docker容器化部署方案

通过合理的配置和优化，RAG模块可以成为企业知识管理的重要工具，为员工提供快速、准确的信息获取渠道。