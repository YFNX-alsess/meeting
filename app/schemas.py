"""接口数据契约：请求体与响应体的类型定义（前后端共同遵守的唯一约定）。

输入：HTTP 请求体
输出：Pydantic 模型实例，供路由层做校验与序列化
约定：所有对外字段名都在这里，路由层不得临时拼装未声明的字段。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """POST /api/chat 的请求体。"""

    query: str = Field(min_length=1, max_length=4000, description="用户问题")


class ChatReply(BaseModel):
    """阻塞式对话的响应体。"""

    reply: str


class Detection(BaseModel):
    """单个检测框。

    内部字段名是 class_name；序列化时输出为 "class"，作为前后端约定的线格式。
    """

    model_config = ConfigDict(populate_by_name=True)

    class_name: str = Field(serialization_alias="class", description="类别名称")
    confidence: float = Field(description="置信度 0~1")
    bbox: list[int] = Field(description="左上右下坐标 [x1, y1, x2, y2]")


class DetectResponse(BaseModel):
    """POST /api/detect 的响应体。"""

    detections: list[Detection]
    model: str


class ServiceStatus(BaseModel):
    """单个依赖服务的状态。"""

    ready: bool
    detail: str


class HealthResponse(BaseModel):
    """GET /api/health 的响应体。"""

    status: str
    model: ServiceStatus
    dify: ServiceStatus
