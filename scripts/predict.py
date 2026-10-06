"""YOLO 推理脚本：对图片做检测并把画框结果保存到 runs/detect 下。

输入：--image 图片路径；缺省时自动取 datasets/coco8/images/val 里的第一张
输出：runs/detect/<任务名>/ 下的带框图片 + 终端打印的类别与置信度
运行：python -m scripts.predict --image datasets/coco8/images/val/000000000042.jpg
"""

from __future__ import annotations

import argparse
import glob
import os

from app.core.config import settings  # 先导入以确保 YOLO_CONFIG_DIR 生效


def parse_args() -> argparse.Namespace:
    """解析推理参数。"""
    parser = argparse.ArgumentParser(description="用 YOLO 权重对图片做推理并保存结果")
    parser.add_argument("--image", default=None, help="待检测图片路径，缺省时自动在 coco8 里找一张")
    parser.add_argument("--model", default=None, help="权重路径，缺省时用配置里解析出的权重")
    parser.add_argument("--name", default="predict_test", help="结果子目录名")
    return parser.parse_args()


def _pick_image(explicit: str | None) -> str | None:
    """确定要检测的图片。"""
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    candidates = sorted(glob.glob(str(settings.project_root / "datasets/coco8/images/val/*.jpg")))
    return candidates[0] if candidates else None


def main() -> int:
    """执行推理，返回进程退出码。"""
    args = parse_args()
    os.chdir(settings.project_root)

    model_path = args.model or (str(settings.model_path) if settings.model_path else None)
    if not model_path:
        print("❌ 没有可用权重：请先运行 python -m scripts.train，或用 --model 指定文件。")
        return 1

    image_path = _pick_image(args.image)
    if not image_path:
        print("❌ 找不到待检测图片：请用 --image 指定，或先在 datasets/coco8/images/val 放入图片。")
        return 1

    from ultralytics import YOLO

    print(f"🚀 加载权重 {model_path}")
    model = YOLO(model_path)

    print(f"🎯 正在识别 {image_path}")
    results = model(image_path, save=True, project="runs/detect", name=args.name)

    for result in results:
        for box in result.boxes:
            print(f"  - {result.names[int(box.cls[0])]}：置信度 {float(box.conf[0]):.2f}")

    print(f"✅ 完成，带框图片在 runs/detect/{args.name}/ 下。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
