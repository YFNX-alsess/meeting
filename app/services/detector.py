"""YOLO 检测服务：按需加载权重、执行推理，并把结果转成纯 Python 数据。

输入：PIL.Image
输出：list[dict]（class / confidence / bbox），或在不可用时抛出 ModelUnavailable
约定：本模块不接触 FastAPI，不做上传校验（那是路由层的职责），权重缺失也不阻止进程启动。
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from PIL import Image

from app.core.config import settings  # 必须先于 ultralytics 导入，确保 YOLO_CONFIG_DIR 生效


class ModelUnavailable(RuntimeError):
    """权重文件不存在或加载失败。"""


class DetectionError(RuntimeError):
    """推理过程本身出错（图片损坏等）。"""


class Detector:
    """YOLO 模型的惰性单例包装：第一次推理时才加载权重，且同一时刻只加载一次。"""

    def __init__(self, model_path: Path | None = None) -> None:
        self._model_path = model_path if model_path is not None else settings.model_path
        self._model: Any = None
        self._lock = threading.Lock()

    @property
    def path(self) -> Path | None:
        return self._model_path

    @property
    def available(self) -> bool:
        return self._model_path is not None

    def _load_model(self) -> Any:
        """加载权重；延迟 import ultralytics 可以让服务在没有权重时也能启动。"""
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                if self._model_path is None:
                    raise ModelUnavailable(
                        "未找到 YOLO 权重文件，请设置环境变量 YOLO_MODEL_PATH，"
                        "或先运行 python -m scripts.train 生成 runs/**/weights/best.pt"
                    )
                from ultralytics import YOLO

                try:
                    self._model = YOLO(str(self._model_path))
                except Exception as exc:  # 权重损坏 / 版本不兼容
                    raise ModelUnavailable(f"加载权重失败：{self._model_path}（{exc}）") from exc
        return self._model

    def predict(self, image: Image.Image) -> list[dict[str, Any]]:
        """对单张图片推理，返回与 HTTP 无关的检测结果列表。"""
        model = self._load_model()
        try:
            results = model(image)
        except Exception as exc:
            raise DetectionError(f"推理失败：{exc}") from exc

        detections: list[dict[str, Any]] = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    {
                        # 内部用 class_name，"class" 这个对外字段名由 app/schemas.py 统一映射
                        "class_name": result.names[int(box.cls[0])],
                        "confidence": round(float(box.conf[0]), 2),
                        "bbox": [round(x1), round(y1), round(x2), round(y2)],
                    }
                )
        return detections


# 全局单例：进程内只保留一份权重
detector = Detector()
