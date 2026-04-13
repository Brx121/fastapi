from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.users.apis import router as users_router
from app.systems.apis import router as systems_router
from app.public.apis import router as public_router
from app.rag.apis import router as rag_router

app = FastAPI()

# 允许前端（Vite）跨域调用后端接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# 尝试创建数据库表
try:
    from app.database.db import engine, Base
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功")
except Exception as e:
    print(f"数据库连接失败: {e}")
    print("服务器将在没有数据库的情况下启动")

app.include_router(users_router)
app.include_router(systems_router)
app.include_router(public_router)
app.include_router(rag_router)