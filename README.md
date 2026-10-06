# AIU 二面项目：Dify 对话 + YOLO 图片识别

前后端分离的最小可运行项目：FastAPI 承担计算与服务推送，原生前端只做 UI 组织与事件订阅。

## 快速开始

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

然后打开 <http://127.0.0.1:8000> 即可（前端由后端托管，不要双击 html 文件打开）。

图片识别只需有 YOLO 权重即可使用；聊天功能需要额外配置 Dify，未配置时接口会返回明确的 503 提示而不是报错堆栈。

## 首次配置

1. 建虚拟环境并激活：`python -m venv .venv` → `.\.venv\Scripts\Activate.ps1`
2. 安装依赖：`pip install -r requirements.txt`
3. 复制配置模板：`Copy-Item .env.example .env`，填入 `DIFY_API_KEY`（留空也能启动）
4. 准备权重：仓库自带 `yolov8n.pt`；想用自己的模型就运行 `python -m scripts.train --epochs 30`
5. 启动：`uvicorn app.main:app --reload`
6. 自检（可选）：`python -m tests.smoke_test`

## 目录结构

```
.
├── README.md              # 本文件：启动方式与接口约定
├── .env.example           # 环境变量模板（复制为 .env）
├── requirements.txt       # 直接依赖清单（版本已锁定）
├── app/                   # 后端
│   ├── main.py            # 装配入口：中间件 + 路由 + 静态前端，无业务逻辑
│   ├── schemas.py         # 接口数据契约
│   ├── core/              # 配置层（唯一读写环境变量处）  → core/README.md
│   ├── services/          # 服务层：detector / llm_service → services/README.md
│   └── routers/           # 接口层：health / detect / chat → routers/README.md
├── web/                   # 前端：index.html + style.css + api.js + app.js → web/README.md
├── scripts/               # 离线脚本：train / predict / ask_dify → scripts/README.md
├── tests/                 # 冒烟测试 → tests/README.md
├── daily/                 # 工程日志 → daily/README.md
├── datasets/              # 数据集说明（图片不入库） → datasets/README.md
├── runs/                  # 训练与推理产物（gitignore）
└── yolov8n.pt             # 官方预训练权重（兜底用）
```

## 接口

| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/health` | GET | 后端、YOLO 权重、Dify 三者的就绪状态 |
| `/api/detect` | POST | 上传图片（字段 `file`）返回检测框 |
| `/api/chat` | POST | 阻塞式对话，返回 `{reply}` |
| `/api/chat/stream` | GET / POST | SSE 订阅式对话，事件 `delta` / `done` / `failed` |

错误约定：非图片 400、超过 `MAX_UPLOAD_MB` 413、没有权重 503、Dify 上游失败 502，响应体统一为 `{"detail": "..."}`。
接口文档在 <http://127.0.0.1:8000/docs>。

## 外部依赖：Dify

聊天功能依赖本地部署的 Dify，属于外部服务，不在本仓库内：

1. 安装 Docker Desktop、LM Studio、WSL；
2. 在 LM Studio 中加载本地模型；（可选）在 WSL 中执行 `docker compose up -d` 启动 Dify；
3. 打开 <http://localhost/install> 配置管理员与模型，创建 chat 应用并取得 API Key；
4. 把 Key 写入 `.env`：

```ini
DIFY_API_KEY=你的_dify_api_key
DIFY_BASE_URL=http://localhost/v1
```

## 权重说明后端按以下顺序自动查找权重，找到第一个即用（权重未入库，克隆后请确认第 4 步）：

1. `runs/detect/runs/train/my_second_train/weights/best.pt`
2. `runs/train/my_second_train/weights/best.pt`
3. `runs/detect/train/weights/best.pt`
4. `yolov8n.pt`（仓库自带）

也可以用环境变量显式指定：`$env:YOLO_MODEL_PATH="D:\models\best.pt"`。

## 常见问题

- **聊天返回 404/502，但 Dify 明明在运行**：系统代理劫持了本机请求。Windows 注册表里的代理会被 Python 读取，
  `http://localhost` 会被转发给代理并返回 404。本项目默认对 Dify 关闭代理（`trust_env=False`）；
  若确实要经代理访问远程 Dify，设 `DIFY_TRUST_ENV=1`。可在代理设置里把 `127.0.0.1;localhost` 加入例外。
- **图片识别返回 503**：没有找到权重。把模型放到候选路径，或设 `YOLO_MODEL_PATH`；
  `GET /api/health` 会直接告诉你当前用的是哪个权重。
- **前端提示连接中断**：确认后端已启动，并用 <http://127.0.0.1:8000> 打开页面，不要双击 html 文件。

## 五项工程要求对照

| 要求 | 落地位置 |
| --- | --- |
| 模块化封装，主程序只负责组装 | `app/main.py` 只有 `create_app()`；计算在 `app/services`，接口在 `app/routers`，配置在 `app/core` |
| 代码顶部写简明注释 | 所有自有 `.py` / `.js` 文件首行为 docstring 或块注释，说明职责、输入、输出、约定 |
| 前后端高度解耦 | 后端以 SSE 推送（`/api/chat/stream`），前端用 `EventSource` 订阅；网络细节收在 `web/api.js`，界面逻辑在 `web/app.js` |
| 根目录 README 带启动命令 | 见上方「快速开始」两行命令 |
| 每个功能文件夹有简短 README | `app/core`、`app/services`、`app/routers`、`web`、`scripts`、`tests`、`daily`、`datasets` 各一份 |

## 任务完成情况

1. 本地部署模型并搭建智能体，接入 Web 对话（现支持流式推送）；
2. 跑通 YOLO 训练两次：coco8 十轮、coco128 三十轮；
3. 图像识别接入 Web，并给出类别、置信度与坐标。

## 变更记录

- `main.py` → `app/main.py`（拆分配置 / 服务 / 路由），启动命令改为 `uvicorn app.main:app --reload`；
- `index.html` → `web/`（HTML / CSS / JS 分离），前端改由后端托管，避免 `file://` 跨域；
- `train_yolo.py` / `predict_yolo.py` / `TAsk_1.py` → `scripts/train.py` / `scripts/predict.py` / `scripts/ask_dify.py`；
- `requirements.txt` 由 UTF-16 改为 UTF-8，并只保留直接依赖。

> 开发说明：项目由作者本人设计流程与验证，编码过程大量借助 DeepSeek 完成。
