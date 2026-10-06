import os
# 强制将 ultralytics 的配置目录设置到当前项目下的 .ultralytics 文件夹
os.environ['YOLO_CONFIG_DIR'] = os.path.join(os.getcwd(), '.ultralytics')
from ultralytics import YOLO

def main():
    print("🚀 开始加载 YOLO 预训练模型...")
    # 加载官方最小的预训练模型 (YOLOv8 nano版，只有 3MB 左右)
    model = YOLO("yolov8n.pt") 

    print("🏋️ 开始训练模型 (使用官方内置的 coco8 极小数据集)...")
    # 开始训练
    model.train(
        data="datasets/coco8/coco8.yaml",    # 使用官方内置的 8 张图片小数据集
        epochs=10,            # 训练 10 轮 (自己决定的参数，训练很快)
        imgsz=640,            # 图片尺寸缩放为 640x640
        batch=4,              # 每次处理 4 张图片
        device="cpu",         # 用 CPU 训练 (如果电脑有 NVIDIA 显卡，可以改成 device=0)
        project="runs/train", # 训练结果保存的文件夹
        name="my_first_train" # 本次训练任务的名称
    )
    print("✅ 训练完成！请查看 runs/train/my_first_train 文件夹下的结果。")

if __name__ == '__main__':
    main()