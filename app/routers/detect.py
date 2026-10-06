"""图片识别路由：校验上传文件，交给检测服务推理，返回检测框数据。

输入：multipart/form-data，字段名 file（图片）
输出：DetectResponse；错误时返回带 HTTP 状态码的标准错误体
错误约定：非图片 400 / 超过大小限制 413 / 无权重 503 / 推理异常 500
来源：原根目录 main.py 的 POST /api/detect，重构后补齐入参校验与标准错误状态码。
"""

from __future__ import annotations

import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.schemas import DetectResponse, Detection
from app.services.detector import DetectionError, ModelUnavailable, detector

router = APIRouter(prefix="/api", tags=["detect"])

_ALLOWED_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def _load_image(raw: bytes) -> Image.Image:
    """把上传字节解码成 RGB 图片；失败时抛出可读的 400。"""
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail=f"无法解析该文件，请上传 jpg/png 等图片（{exc}）") from exc
    return image.convert("RGB")


@router.post("/detect", response_model=DetectResponse, summary="YOLO 图片识别")
async def detect_objects(file: UploadFile = File(...)) -> DetectResponse:
    """接收图片，返回识别到的目标列表。"""
    if not detector.available:
        raise HTTPException(
            status_code=503,
            detail="后端没有可用的 YOLO 权重，请设置 YOLO_MODEL_PATH 或先运行 python -m scripts.train",
        )

    if file.filename and not file.filename.lower().endswith(_ALLOWED_SUFFIXES):
        raise HTTPException(status_code=400, detail="仅支持 jpg / jpeg / png / bmp / webp 格式")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="上传内容为空")
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"图片超过 {settings.max_upload_mb}MB 限制")

    image = _load_image(raw)

    try:
        # 推理是 CPU 密集型同步调用，放到线程池里执行，避免阻塞事件循环
        raw_detections = await run_in_threadpool(detector.predict, image)
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DetectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DetectResponse(
        detections=[Detection(**item) for item in raw_detections],
        model=settings.describe_model(),
    )
