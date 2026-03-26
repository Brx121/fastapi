# RAG 智能问答系统

## 项目简介

本项目是一个基于 FastAPI 和 RAG（Retrieval-Augmented Generation）技术的智能问答系统，支持处理 PDF、Excel、Word 等多种文档类型，提供企业级文档智能查询和知识管理能力。

## 项目结构

```
├── app/
│   ├── rag/                # RAG 模块
│   │   ├── __init__.py
│   │   ├── apis.py          # API 接口定义
│   │   ├── chunking.py      # 文本分块逻辑
│   │   ├── embedding.py     # 文本向量化
│   │   ├── llm.py           # LLM 调用
│   │   ├── qdrant_store.py  # 向量数据库操作
│   │   └── document_parser.py # 文档解析（PDF、Excel、Word）
│   ├── users/             # 用户模块
│   ├── systems/           # 系统模块
│   │   ├── gitlab_script/  # CICD GitLab 脚本
│   │   └── apis.py         # 系统接口
│   ├── public/            # 公共模块
│   ├── database/          # 数据库模块
│   └── config/            # 配置模块
├── docs/                  # 文档目录
├── logs/                  # 日志目录
├── mysql-init/            # MySQL 初始化脚本
├── main.py                # 主应用入口
├── requirements.txt       # 项目依赖
├── .env                   # 环境变量
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── supervisor.conf        # Supervisor 配置文件
├── install.sh             # 一键部署脚本
└── README.md              # 项目说明
```

## 功能特性

- **智能问答**：根据用户问题检索相关文档并生成准确回答
- **多文档类型支持**：支持 PDF、Excel、Word、TXT 等多种文档格式
- **引用追踪**：在回答中包含引用编号，支持溯源到原始文档
- **相关性排序**：按相似度排序返回最相关的文档片段
- **文档摄入**：将企业文档分块、向量化并存储到向量数据库
- **健康检查**：提供模块健康状态检查接口

## 技术栈

- **FastAPI**：高性能 Web 框架
- **Uvicorn**：ASGI 服务器
- **Qdrant**：向量数据库
- **DashScope**：大语言模型和 Embedding 服务
- **PyPDF2**：PDF 文档解析
- **openpyxl**：Excel 文档解析
- **python-docx**：Word 文档解析
- **Docker**：容器化部署
- **Docker Compose**：多容器编排

## API 接口

| 端点 | 方法 | 功能 |
|------|------|------|
| `/rag/health` | GET | 健康检查 |
| `/rag/ingest` | POST | 摄入文本文档 |
| `/rag/upload` | POST | 上传并处理文档（PDF、Excel、Word） |
| `/rag/query` | POST | 智能问答 |

### 接口详情

#### 1. 健康检查

- **请求**：`GET /rag/health`
- **响应**：
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

#### 2. 文档摄入

- **请求**：`POST /rag/ingest`
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
- **响应**：
  ```json
  {
    "collection": "rag_collection",
    "documents_ingested": 1,
    "chunks_ingested": 1
  }
  ```

#### 3. 文档上传

- **请求**：`POST /rag/upload` (multipart/form-data)
  - `doc_id`: 文档ID
  - `file`: 上传的文件（PDF、Excel、Word、TXT）
  - `metadata`: 元数据（JSON格式）
- **响应**：
  ```json
  {
    "doc_id": "pdf_001",
    "filename": "document.pdf",
    "text_extracted": true,
    "chunks_ingested": 5
  }
  ```

#### 4. 智能问答

- **请求**：`POST /rag/query`
  ```json
  {
    "question": "FastAPI是什么？它有什么特点？",
    "top_k": 8,
    "max_context_chunks": 5,
    "score_threshold": 0.3
  }
  ```
- **响应**：
  ```json
  {
    "answer": "FastAPI是一个现代的、快速的Python Web框架，用于构建API... [1]",
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

## 启动方法

### 方法一：使用 Docker Compose 部署（推荐）

1. 确保已安装 Docker 和 Docker Compose

2. 在项目根目录下执行：
   ```bash
   docker compose up -d
   ```

3. 查看服务状态：
   ```bash
   docker compose ps
   ```

### 方法二：使用 Supervisor 部署

1. 在项目根目录下执行一键部署脚本：
   ```bash
   sudo ./install.sh
   ```

2. 查看服务状态：
   ```bash
   sudo supervisorctl status fastapi-app
   ```

3. 管理服务：
   ```bash
   # 启动服务
   sudo supervisorctl start fastapi-app
   
   # 停止服务
   sudo supervisorctl stop fastapi-app
   
   # 重启服务
   sudo supervisorctl restart fastapi-app
   ```

### 方法三：本地运行

1. 激活虚拟环境：
   ```bash
   source venv/bin/activate
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 启动服务：
   ```bash
   python -m uvicorn main:app --reload --port 8001 --host 0.0.0.0
   ```

## 访问地址

- **FastAPI 应用**：http://localhost:8001
- **Swagger UI 文档**：http://localhost:8001/docs
- **ReDoc 文档**：http://localhost:8001/redoc
- **Qdrant 控制台**：http://localhost:6333/dashboard

## 配置说明

### 环境变量

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| **DASH_SCOPE_API_KEY** | - | DashScope API 密钥 |
| **MODEL** | qwen-plus | LLM 模型名称 |
| **EMBEDDING_MODEL** | text-embedding-v2 | Embedding 模型名称 |
| **QDRANT_URL** | http://localhost:6333 | Qdrant 服务地址 |
| **QDRANT_COLLECTION** | rag_collection | 向量集合名称 |

### 配置文件

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

## 使用示例

### 1. 上传文档

**上传 PDF 文档**：
```bash
curl -X POST "http://localhost:8001/rag/upload?doc_id=pdf_001" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "metadata={\"source\": \"PDF文档\", \"category\": \"技术文档\"}"
```

**上传 Excel 文档**：
```bash
curl -X POST "http://localhost:8001/rag/upload?doc_id=excel_001" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@spreadsheet.xlsx" \
  -F "metadata={\"source\": \"Excel文档\", \"category\": \"数据表格\"}"
```

**上传 Word 文档**：
```bash
curl -X POST "http://localhost:8001/rag/upload?doc_id=docx_001" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.docx" \
  -F "metadata={\"source\": \"Word文档\", \"category\": \"报告\"}"
```

### 2. 提问

```bash
curl -X POST http://localhost:8001/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "FastAPI是什么？它有什么特点？"
  }'
```

## 故障排查

| 错误 | 可能原因 | 解决方案 |
|------|----------|----------|
| **AccessDenied** | API密钥无效或模型不匹配 | 检查API密钥和模型配置 |
| **Qdrant连接失败** | Qdrant服务未启动 | 检查Qdrant服务状态 |
| **向量维度不匹配** | Embedding模型与配置不一致 | 检查EMBEDDING_DIM配置 |
| **检索结果质量差** | 文档质量或分块策略问题 | 优化文档质量和分块策略 |
| **文档解析失败** | 文件格式不支持或损坏 | 检查文件格式和完整性 |

## 性能优化

- **文本分块**：根据文档类型和长度调整分块大小和重叠部分
- **向量检索**：调整top_k和score_threshold参数以平衡精度和速度
- **模型选择**：根据生成质量和响应速度选择合适的模型
- **批量处理**：对于大量文档，使用批量上传功能提高效率

## 扩展建议

- **多模态支持**：增加对图片、视频等多媒体内容的支持
- **对话历史**：支持上下文对话，保持对话连续性
- **个性化推荐**：根据用户历史查询优化推荐结果
- **自动文档更新**：支持文档的自动更新和版本管理
- **多语言支持**：增加对多语言文档的支持

## 总结

RAG 智能问答系统是一个功能强大的企业级知识管理工具，通过向量检索和大语言模型的结合，为用户提供快速、准确的文档查询能力。系统支持多种文档类型，具有良好的扩展性和可维护性，能够满足企业各种知识管理需求。

通过合理的配置和优化，RAG 系统可以成为企业内部知识共享和决策支持的重要工具，提高员工工作效率，促进知识的有效利用。