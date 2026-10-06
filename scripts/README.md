# scripts — 可执行脚本

均在项目根目录运行，复用 `app/` 里的配置与服务，不重复实现逻辑。

| 脚本 | 作用 | 命令 |
| --- | --- | --- |
| `train.py` | 训练 YOLO 权重，产物落在 `runs/train/<name>/` | `python -m scripts.train --epochs 30` |
| `predict.py` | 对图片推理并保存带框结果 | `python -m scripts.predict --image <图片路径>` |
| `ask_dify.py` | Dify 配置与连通性自检（流式/阻塞） | `python -m scripts.ask_dify` |

说明：训练与推理是离线任务，不经过 HTTP，因此直接调用 ultralytics；后端服务的推理路径在 `app/services/detector.py`。
