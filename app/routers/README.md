# app/routers — 接口层

每个模块暴露一个 `router`，由 [app/main.py](../main.py) 统一 `include_router`。本层只做三件事：校验入参、调用 `app/services`、组装响应。

| 端点 | 方法 | 说明 | 成功 | 失败 |
| --- | --- | --- | --- | --- |
| `/api/health` | GET | 模型与 Dify 就绪状态 | 200 | — |
| `/api/detect` | POST | 上传图片做 YOLO 识别（字段名 `file`） | 200 | 400 非图片 / 413 过大 / 503 无权重 / 500 推理异常 |
| `/api/chat` | POST | 阻塞式对话 | 200 `{reply}` | 422 参数错误 / 503 未配置 / 502 上游错误 |
| `/api/chat/stream` | GET | SSE 订阅式对话（供 `EventSource`） | 200 事件流 | 422 参数错误 |
| `/api/chat/stream` | POST | SSE 订阅式对话（长问题用） | 200 事件流 | 422 参数错误 |

SSE 事件：`delta`（文本增量）、`done`（结束）、`failed`（错误，含 `message`）。事件名不用 `error`，因为 `EventSource` 自身的 error 事件会与它重名。
