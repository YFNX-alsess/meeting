"""冒烟测试：验证接口契约与降级行为，不依赖 pytest，也不需要 Dify 在运行。

输入：无；若配置了可用权重（YOLO_MODEL_PATH 或 runs/ 下已有 best.pt）会额外验证真实推理
输出：终端逐条 PASS/FAIL，全部通过时退出码为 0
运行：python -m tests.smoke_test
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402

_client = TestClient(app)
_results: list[tuple[bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    """记录一条断言结果。"""
    _results.append((condition, f"{name}{(' — ' + detail) if detail else ''}"))


def _png_bytes() -> bytes:
    """生成一张纯色 PNG，用于测试上传链路。"""
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def main() -> int:
    """依次跑完所有冒烟用例。"""
    health = _client.get("/api/health")
    check("GET /api/health 返回 200", health.status_code == 200, str(health.status_code))
    check("健康检查包含模型与 Dify 状态", {"model", "dify"} <= set(health.json() or {}))

    page = _client.get("/")
    check("GET / 返回前端页面", page.status_code == 200 and "我的 Dify 助手" in page.text)
    check("前端资源可访问", _client.get("/app.js").status_code == 200)

    bad_chat = _client.post("/api/chat", json={"query": ""})
    check("空问题被拒绝（422）", bad_chat.status_code == 422, str(bad_chat.status_code))

    not_image = _client.post(
        "/api/detect", files={"file": ("x.png", b"not an image", "image/png")}
    )
    check("非图片文件返回 400", not_image.status_code == 400, str(not_image.status_code))

    detect = _client.post(
        "/api/detect", files={"file": ("blank.png", _png_bytes(), "image/png")}
    )
    if settings.model_ready:
        check("图片识别返回 200", detect.status_code == 200, str(detect.status_code))
        if detect.status_code == 200:
            body = detect.json()
            check("响应包含 detections 与 model", {"detections", "model"} <= set(body))
    else:
        check("无权重时优雅降级为 503", detect.status_code == 503, str(detect.status_code))

    stream = _client.get("/api/chat/stream", params={"query": "你好"})
    check("SSE 接口返回事件流", stream.status_code == 200 and "event:" in stream.text)

    stream_error = _client.post("/api/chat/stream", json={"query": ""})
    check("SSE 空问题被拒绝（422）", stream_error.status_code == 422, str(stream_error.status_code))

    failed = [name for ok, name in _results if not ok]
    for ok, name in _results:
        print(("✅ PASS " if ok else "❌ FAIL ") + name)
    print(f"\n共 {len(_results)} 项，失败 {len(failed)} 项")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
