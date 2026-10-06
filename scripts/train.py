"""YOLO 训练脚本：在指定数据集上训练权重，产物统一落在 runs/ 下。

输入：命令行参数（数据集 yaml、轮数、批大小、设备、任务名），均有默认值
输出：runs/train/<任务名>/weights/best.pt，并打印被后端自动选中的权重路径
运行：python -m scripts.train --epochs 30
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.core.config import settings  # 先导入以确保 YOLO_CONFIG_DIR 生效


def parse_args() -> argparse.Namespace:
    """解析训练参数。"""
    parser = argparse.ArgumentParser(description="训练 YOLO 模型")
    parser.add_argument("--weights", default="yolov8n.pt", help="初始权重（默认官方 nano 预训练模型）")
    parser.add_argument("--data", default="datasets/coco128/coco128.yaml", help="数据集 yaml 路径")
    parser.add_argument("--epochs", type=int, default=30, help="训练轮数")
    parser.add_argument("--batch", type=int, default=4, help="批大小")
    parser.add_argument("--imgsz", type=int, default=640, help="输入尺寸")
    parser.add_argument("--device", default="cpu", help="cpu 或 0（NVIDIA 显卡编号）")
    parser.add_argument("--name", default="my_second_train", help="本次训练任务名")
    return parser.parse_args()


def main() -> int:
    """执行训练，返回进程退出码。"""
    args = parse_args()
    os.chdir(settings.project_root)  # ultralytics 用相对路径落盘，统一以项目根为基准

    data_path = Path(args.data)
    if not data_path.is_file():
        print(f"❌ 找不到数据集配置：{data_path}（当前目录 {os.getcwd()}）")
        return 1

    from ultralytics import YOLO  # 重量级依赖延迟导入，避免 --help 也加载 torch

    print(f"🚀 加载初始权重 {args.weights} ...")
    model = YOLO(args.weights)

    print(f"🏋️ 开始训练：data={data_path} epochs={args.epochs} batch={args.batch} device={args.device}")
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project="runs/train",
        name=args.name,
    )

    best = settings.project_root / "runs" / "train" / args.name / "weights" / "best.pt"
    print(f"✅ 训练完成，权重：{best}")
    print("💡 后端会自动优先使用该权重；也可用环境变量 YOLO_MODEL_PATH 指定其它文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
