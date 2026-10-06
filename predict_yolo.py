import os
os.environ['YOLO_CONFIG_DIR'] = os.path.join(os.getcwd(), '.ultralytics')

from ultralytics import YOLO
import os
import glob

def main():
    print("🚀 加载我们刚刚训练好的模型...")
    # ⚠️ 注意：路径指向你刚才训练结果里的 best.pt
    # 如果你找不到这个路径，去左侧 runs 文件夹里翻一下，确认 best.pt 的具体位置
    model_path = "yolov8n.pt"
    
    if not os.path.exists(model_path):
        print(f"❌ 找不到模型文件: {model_path}")
        print("💡 请检查 runs 文件夹，确认 best.pt 的具体路径。")
        return

    model = YOLO(model_path)

    print("🖼️ 开始寻找图片进行推理...")
    # 自动在 coco8 数据集里找一张图片来测试
    image_files = glob.glob("datasets/coco8/images/val/*.jpg")
    if not image_files:
        print("❌ 找不到测试图片，请确认 datasets/coco8/images/val 下有没有图片。")
        return
    
    test_image = image_files[0] # 拿第一张图来测试
    print(f"🎯 正在识别图片: {test_image}")

    # 开始推理，save=True 会把画好框的图片保存下来
    results = model(test_image, save=True, project="runs/detect", name="predict_test")

    print("✅ 推理完成！")
    print("📂 请去 runs/detect/predict_test/ 文件夹下查看画好框的图片。")

if __name__ == '__main__':
    main()