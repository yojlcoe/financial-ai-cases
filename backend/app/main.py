from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.v1.router import api_router
from app.core.database import engine, Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時処理
    # Note: 本番環境ではマイグレーションファイルを使用するため、
    # 自動テーブル作成は無効化しています
    # ローカル開発環境で自動作成が必要な場合は、以下のコメントを外してください:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    # 終了時
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="事例調査AIエージェント API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Case Study Agent API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
