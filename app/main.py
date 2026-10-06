"""应用装配入口：只做 create_app（中间件 + 路由 + 静态前端），不含任何业务逻辑。

输入：环境变量 / .env（经由 app/core/config.py）
输出：FastAPI 应用实例
启动：uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import chat, detect, health


def create_app() -> FastAPI:
    """组装整个后端：先挂中间件，再挂 API 路由，最后挂前端静态资源。"""
    app = FastAPI(
        title="AIU 二面项目",
        description="Dify 对话（SSE 推送）+ YOLO 图片识别",
        version="2.0.0",
    )

    # 只放行明确列出的来源，不用 "*" 搭配 allow_credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 装配顺序即路由优先级：API 在前，静态前端兜底
    for module in (health, detect, chat):
        app.include_router(module.router)

    if settings.web_dir.is_dir():
        # 前端与接口同源，彻底避免 file:// 打开页面导致的跨域问题
        app.mount("/", StaticFiles(directory=settings.web_dir, html=True), name="web")

    return app


app = create_app()
