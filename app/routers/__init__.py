"""路由层：唯一的 HTTP 入口，负责参数校验、调用 service、组装响应。

每个模块暴露一个 ``router``，由 app/main.py 统一装配。
"""

from . import chat, detect, health

__all__ = ["chat", "detect", "health"]
