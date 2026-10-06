"""对话路由：把 HTTP 请求翻译成对对话服务的调用，再把结果翻译成 JSON 或 SSE 事件。

输入：ChatRequest（JSON）或 query 查询参数
输出：阻塞式为 ChatReply；订阅式为 text/event-stream，事件名 delta / done / failed
约定：前端只订阅事件流，不感知 Dify；Dify 的错误在这里被翻译成结构化错误，不外泄原始报文。
来源：原根目录 main.py 的 POST /api/chat；SSE 订阅端点为重构新增。
"""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas import ChatReply, ChatRequest
from app.services.llm_service import DifyError, llm_service

router = APIRouter(prefix="/api", tags=["chat"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # 关掉反向代理缓冲，保证增量能立刻到达前端
}


def _sse(event: str, data: dict[str, object]) -> str:
    """按 SSE 规范编码一个事件。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _event_stream(query: str) -> AsyncIterator[str]:
    """把服务层的文本增量转换成 SSE 事件流。"""
    if not llm_service.configured:
        yield _sse("failed", {"message": "后端未配置 DIFY_API_KEY，请参考 .env.example 创建 .env 后重启服务"})
        return

    try:
        async for delta in llm_service.stream(query):
            yield _sse("delta", {"text": delta})
    except DifyError as exc:
        yield _sse("failed", {"message": str(exc)})
        return
    except Exception as exc:  # noqa: BLE001 - 兜底，避免流中断时前端无提示
        yield _sse("failed", {"message": f"服务内部错误：{exc}"})
        return

    yield _sse("done", {"ok": True})


@router.post("/chat", response_model=ChatReply, summary="阻塞式对话")
async def chat(request: ChatRequest) -> ChatReply:
    """等模型生成完成后一次性返回，保留给脚本与非流式调用方。"""
    if not settings.dify_ready:
        raise HTTPException(status_code=503, detail="后端未配置 DIFY_API_KEY")
    try:
        answer = await llm_service.ask(request.query)
    except DifyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatReply(reply=answer)


@router.get("/chat/stream", summary="订阅式对话（SSE，供 EventSource 使用）")
async def chat_stream_get(query: str = Query(min_length=1, max_length=4000)) -> StreamingResponse:
    """浏览器 EventSource 的标准用法：GET + 事件订阅。"""
    return StreamingResponse(_event_stream(query), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/chat/stream", summary="订阅式对话（SSE，供长问题使用）")
async def chat_stream_post(request: ChatRequest) -> StreamingResponse:
    """问题较长、不适合放进 URL 时使用。"""
    return StreamingResponse(_event_stream(request.query), media_type="text/event-stream", headers=_SSE_HEADERS)
