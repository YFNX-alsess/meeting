# app/services — 服务层（纯计算与外部调用）

本层不感知 HTTP：不导入 FastAPI，不碰 `Request`/`Response`，错误统一以异常抛出，由 `app/routers` 翻译成 HTTP。

| 文件 | 职责 | 输入 → 输出 |
| --- | --- | --- |
| `detector.py` | YOLO 权重惰性加载与推理 | `PIL.Image` → `list[dict]`（class / confidence / bbox） |
| `llm_service.py` | 唯一与 Dify 通信的地方 | 问题字符串 → 文本增量（异步生成器）或完整回答 |

异常约定：`ModelUnavailable`（无权重）、`DetectionError`（推理失败）、`DifyError`（上游或网络失败，含 `status_code`）。
