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

# 创建配置实例
config = Config()