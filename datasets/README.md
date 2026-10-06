# datasets — 数据集

只保留数据集的说明文件（`*.yaml`），图片与标签体积大，不入库（见根目录 `.gitignore`）。

| 数据集 | 用途 | 规模 |
| --- | --- | --- |
| `coco8/` | 第一次训练 | 8 张图片，用于跑通流程 |
| `coco128/` | 第二次训练 | 128 张图片 |

目录约定（ultralytics 标准布局）：`images/{train,val}` 放图片，`labels/{train,val}` 放同名 `.txt` 标注。
缺失图片时可用 ultralytics 自带下载脚本重新获取，或用 `scripts/train.py --data` 指向别的 yaml。
