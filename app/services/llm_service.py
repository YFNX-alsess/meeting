"""Dify 对话服务：全项目唯一与 Dify 通信的地方，支持流式与阻塞两种模式。

输入：用户问题字符串
输出：stream() 逐个产出文本增量（异步生成器）；ask() 返回完整回答
约定：不接触 FastAPI 的 Request/Response，所有失败统一抛 DifyError，由路由层翻译成 HTTP/SSE 事件。
注意：默认绕过系统代理（trust_env=False）。Windows 注册表里的系统代理会劫持 127.0.0.1 请求，
      表现为"连接本地 Dify 却返回 404"；确实需要经代理访问远程 Dify 时设 DIFY_TRUST_ENV=1。
来源：原根目录 main.py 第 41-66 行的 Dify 调用，由同步 requests 改为异步 httpx 并支持流式。
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.core.config import settings


class DifyError(RuntimeError):
    """Dify 调用失败，携带上游状态码与可读信息。"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _extract_upstream_message(raw: str) -> str:
    """从 Dify 的错误响应里尽量抽取一句人话。"""
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return raw.strip()[:300] or "上游未返回错误详情"
    if isinstance(payload, dict):
        for key in ("message", "error", "code"):
            if payload.get(key):
                return str(payload[key])
    return str(payload)[:300]


class DifyService:
    """Dify chat-messages 接口客户端。"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        user: str | None = None,
        timeout: float | None = None,
        trust_env: bool | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.dify_api_key
        self._base_url = (base_url or settings.dify_base_url).rstrip("/")
        self._user = user or settings.dify_user
        self._timeout = timeout or settings.dify_timeout
        self._trust_env = settings.dify_trust_env if trust_env is None else trust_env

    def _client(self) -> httpx.AsyncClient:
        """统一的 HTTP 客户端：默认忽略环境/注册表代理，避免本地请求被劫持。"""
        return httpx.AsyncClient(timeout=self._timeout, trust_env=self._trust_env)

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, query: str, response_mode: str) -> dict[str, object]:
        return {
            "inputs": {},
            "query": query,
            "response_mode": response_mode,
            "user": self._user,
        }

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise DifyError("后端未配置 DIFY_API_KEY，请参考 .env.example 创建 .env 后重启服务")

    async def ask(self, query: str) -> str:
        """阻塞模式：等 Dify 生成完成后一次性返回完整回答。"""
        self._ensure_configured()
        async with self._client() as client:
            try:
                response = await client.post(
                    f"{self._base_url}/chat-messages",
                    headers=self._headers(),
                    json=self._payload(query, "blocking"),
                )
            except httpx.HTTPError as exc:
                raise DifyError(f"无法连接 Dify（{self._base_url}）：{exc}") from exc

        if response.status_code != 200:
            raise DifyError(
                f"Dify 返回 {response.status_code}：{_extract_upstream_message(response.text)}",
                status_code=response.status_code,
            )
        return response.json().get("answer") or "（Dify 没有返回文本内容）"

    async def stream(self, query: str) -> AsyncIterator[str]:
        """流式模式：逐个产出文本增量，供上层做服务推送。"""
        self._ensure_configured()
        async with self._client() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/chat-messages",
                    headers=self._headers(),
                    json=self._payload(query, "streaming"),
                ) as response:
                    if response.status_code != 200:
                        body = (await response.aread()).decode("utf-8", "replace")
                        raise DifyError(
                            f"Dify 返回 {response.status_code}：{_extract_upstream_message(body)}",
                            status_code=response.status_code,
                        )

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue  # 跳过空行与 event: 行
                        chunk = line[len("data:") :].strip()
                        if not chunk:
                            continue
                        try:
                            event = json.loads(chunk)
                        except ValueError:
                            continue

                        event_type = event.get("event")
                        if event_type in ("message", "agent_message"):
                            delta = event.get("answer") or ""
                            if delta:
                                yield delta
                        elif event_type == "error":
                            raise DifyError(
                                f"Dify 流式报错：{event.get('message') or event.get('code') or '未知错误'}"
                            )
                        elif event_type == "message_end":
                            break
            except httpx.HTTPError as exc:
                raise DifyError(f"无法连接 Dify（{self._base_url}）：{exc}") from exc


# 全局单例：路由层直接复用
llm_service = DifyService()
