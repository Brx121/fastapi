import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class Config:
    # 数据库配置
    DB_HOST = os.getenv("DB_HOST", "10.0.3.170")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "dev")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "blogdb")
    
    # 构建数据库连接字符串，对密码进行URL编码
    if DB_PASSWORD:
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # 密码未设置时，使用默认值（仅用于开发环境）
        DATABASE_URL = "mysql+pymysql://dev:Dev%401234@10.0.3.170:3306/blogdb"

    # DashScope（阿里免费/商用模型）配置
    # 兼容你现有 docker-compose 里使用的 API_KEY 环境变量。
    DASH_SCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("API_KEY")
    # MODEL = os.getenv("MODEL", "glm-4.7-flash")
    MODEL = os.getenv("MODEL", "qwen-plus")

    # Embedding 配置（用于向量检索）
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

    # Qdrant 配置
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_collection")

# 创建配置实例
config = Config()