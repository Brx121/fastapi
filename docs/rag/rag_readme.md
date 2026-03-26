# RAG 模块快速指南

## 什么是 RAG 模块？

RAG（Retrieval-Augmented Generation）模块是一个基于向量检索和大语言模型的智能问答系统，用于企业文档的智能查询和知识管理。

## 核心功能

- **文档摄入**：将企业文档分块、向量化并存储到向量数据库
- **智能问答**：根据用户问题检索相关文档并生成准确回答
- **引用追踪**：在回答中包含引用编号，支持溯源
- **相关性排序**：按相似度排序返回最相关的文档片段

## 技术栈

- **向量数据库**：Qdrant
- **Embedding模型**：DashScope text-embedding-v2
- **LLM模型**：DashScope qwen-plus
- **API框架**：FastAPI

## 快速开始

### 1. 启动服务

```bash
# 使用 Docker Compose 启动
docker compose up -d

# 或本地运行
python -m uvicorn main:app --reload --port 8001 --host 0.0.0.0
```

### 2. 摄入文档

```bash
curl -X POST http://localhost:8001/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "doc_id": "doc_001",
        "text": "FastAPI是一个现代的、快速的Python Web框架...",
        "metadata": {"source": "技术文档"}
      }
    ]
  }'
```

### 3. 提问

```bash
curl -X POST http://localhost:8001/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "FastAPI是什么？它有什么特点？"
  }'
```

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/rag/health` | GET | 健康检查 |
| `/rag/ingest` | POST | 摄入文档 |
| `/rag/query` | POST | 问答查询 |

## 配置

主要配置项：

- **DASH_SCOPE_API_KEY**：DashScope API 密钥
- **MODEL**：LLM 模型名称（默认：qwen-plus）
- **QDRANT_URL**：Qdrant 服务地址（默认：http://localhost:6333）
- **QDRANT_COLLECTION**：向量集合名称（默认：rag_collection）

## 详细文档

- [RAG 模块详细文档](rag_module.md)：包含完整的模块架构、代码分析和使用指南
- [部署指南](deployment.md)：详细的部署步骤和故障排查

## 故障排查

- **AccessDenied 错误**：检查 API 密钥是否有效
- **Qdrant 连接失败**：检查 Qdrant 服务是否启动
- **向量维度不匹配**：检查 Embedding 模型配置

## 扩展建议

- 增加对多模态内容的支持
- 添加对话历史功能
- 实现个性化推荐
- 优化批量文档摄入性能