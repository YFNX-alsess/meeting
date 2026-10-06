"""健康检查路由：报告模型与 Dify 的可用状态，前端启动时据此决定是否提示用户。

输入：无
输出：HealthResponse（两个依赖服务是否就绪）
约定：不做任何重型操作，保证毫秒级返回。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.schemas import HealthResponse, ServiceStatus

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="服务与依赖状态")
async def health() -> HealthResponse:
    """返回后端自身、YOLO 权重、Dify 配置三者的状态。"""
    return HealthResponse(
        status="ok",
        model=ServiceStatus(
            ready=settings.model_ready,
            detail=settings.describe_model(),
        ),
        dify=ServiceStatus(
            ready=settings.dify_ready,
            detail=settings.dify_base_url if settings.dify_ready else "缺少 DIFY_API_KEY",
        ),
    )
