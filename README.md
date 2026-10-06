# AIU 二面项目：Dify 对话 + YOLO 图片识别

前后端分离的最小可运行项目：FastAPI 承担计算与服务推送，原生前端只做 UI 组织与事件订阅。

> **重构说明**：当前版本已按五项工程要求重新组织（模块化 / 文件头注释 / 前后端解耦 / README 启动命令 / 各目录 README）。
> 相对重构前的**全部改动明细见文末《本次改动说明》**，其中标注了每一处改动对应原文件的哪个部分，可直接用于答辩复查。

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

## 本次改动说明

> 本节记录「工程规范重构」（提交 `7a65871`）相对重构前（提交 `1619646`）的全部改动，供答辩与复查对照。
> 未列出的内容——`datasets/`、`daily/`、`runs/`、`yolov8n.pt`、`.env` 的内容、Dify 外部部署——**均未改动**。

### 1. 文件变动总览

| 重构前 | 重构后 | 说明 |
| --- | --- | --- |
| `main.py`（98 行单体） | `app/main.py` + `app/schemas.py` + `app/core/config.py` + `app/services/*` + `app/routers/*` | 一个文件按职责拆成 8 个模块 |
| `index.html`（内联 CSS/JS） | `web/index.html` + `web/style.css` + `web/api.js` + `web/app.js` | 结构 / 样式 / 网络 / 界面逻辑四分离 |
| `train_yolo.py` | `scripts/train.py` | 支持命令行参数，复用 `app/` 里的配置 |
| `predict_yolo.py` | `scripts/predict.py` | 修正"注释说用 best.pt、代码却加载 yolov8n.pt"的矛盾；找不到图片时给出可用提示 |
| `TAsk_1.py` | `scripts/ask_dify.py` | 改为可复用的连通性自检脚本（流式 / 阻塞两种模式） |
| — | `tests/smoke_test.py`、`tests/README.md` | **新增**：重构前无任何测试 |
| — | `.env.example` | **新增**：重构前只靠 README 口头说明环境变量 |
| — | 8 份目录 README | **新增**：`app/core`、`app/services`、`app/routers`、`web`、`scripts`、`tests`、`daily`、`datasets` |
| `README.md` | 同路径重写 | 补快速启动、接口清单、权重说明、常见问题、本节 |
| `requirements.txt` | 同路径，格式与内容变更 | UTF-16LE 带 BOM → UTF-8；整机 `pip freeze` → 11 个直接依赖 |
| `.gitignore` | 同路径重写 | 重复段落去重、编码统一 UTF-8、补 `.env.example` 例外与日志截图例外 |

### 2. 原 `main.py` 与 `index.html` 各部分的去向

| 原位置 | 现位置 | 变化 |
| --- | --- | --- |
| `main.py:1-2` 设置 `YOLO_CONFIG_DIR` | `app/core/config.py` | 原先三处重复粘贴，收敛为唯一来源 |
| `main.py:16-25` 读 `.env` 与 API Key | `app/core/config.py` | 集中为 `settings` 单例，新增模型路径、上传上限、跨域白名单 |
| `main.py:29-35` CORS 中间件 | `app/main.py` | `allow_origins=["*"]` 改为显式白名单 |
| `main.py:38-39` `ChatRequest` | `app/schemas.py` | 集中数据契约，并增加长度校验 |
| `main.py:41-66` Dify 调用与结果解析 | `app/services/llm_service.py` + `app/routers/chat.py` | 同步 `requests` → 异步 `httpx`；服务与 HTTP 分离 |
| `main.py:68-69` 加载权重 | `app/services/detector.py` + `app/core/config.py` | 模块级硬编码 → 惰性加载 + 候选路径 + `YOLO_MODEL_PATH` |
| `main.py:71-98` 图片识别 | `app/routers/detect.py` + `app/services/detector.py` | 补入参校验、错误翻译，推理由线程池执行 |
| `index.html:6-19` 内联样式 | `web/style.css` | 样式独立成文件 |
| `index.html:41-127` 内联脚本 | `web/api.js`（网络）+ `web/app.js`（界面） | 职责分离，改为事件订阅 |

### 3. 行为变化

| 项目 | 重构前 | 重构后 |
| --- | --- | --- |
| 启动命令 | `uvicorn main:app --reload` | `uvicorn app.main:app --reload` |
| 打开前端 | 双击 `index.html`（`file://`） | 浏览器访问 <http://127.0.0.1:8000>（由后端托管） |
| 对话返回方式 | 一次性 `fetch` 取回完整回复后整段显示 | 后端 SSE 推送 + 前端 `EventSource` 订阅，增量上屏 |
| 对话接口 | 仅 `POST /api/chat` | 保留原接口，另加 `GET/POST /api/chat/stream` 与 `GET /api/health` |
| 错误返回 | 一律 HTTP 200，把 Dify 报错拼进 `reply` 展示给用户 | 400 / 413 / 422 / 502 / 503 + `{"detail": ...}`，前端按状态码区分 |
| 没有权重时 | 模块导入即抛异常，服务无法启动 | 服务正常启动，识别接口返回 503 并说明修复方法 |
| 依赖未配置时 | 调用时才 500 | `/api/health` 预先报告，页面顶部直接提示 |
| 前端渲染 | `innerHTML` 拼接模型输出（XSS 风险） | 统一 `textContent` |
| 事件循环 | `async` 函数里跑同步 `requests` 与 CPU 推理，会阻塞 | `httpx.AsyncClient` + 线程池推理 |
| 新增可配置项 | — | `YOLO_MODEL_PATH`、`DIFY_USER`、`DIFY_TIMEOUT`、`DIFY_TRUST_ENV`、`MAX_UPLOAD_MB`、`CORS_ORIGINS`（见 `.env.example`） |

> 顺带纠正一处文档错误：重构前 README 建议的 `python main.py` 其实不会启动服务（原 `main.py` 没有 `__main__` 入口），
> 现已统一为 `uvicorn` 命令。

### 4. 修复的实际缺陷

1. **依赖装不上**：`requirements.txt` 是 UTF-16LE 带 BOM，pip 按 UTF-8 解析必然失败 → 已转 UTF-8，并只保留直接依赖（不再使用的 `requests` 从清单移除，改用 `httpx`）。
2. **换台机器跑不起来**：原 `main.py` 硬编码 `runs/detect/runs/train/my_second_train/weights/best.pt`，而 `runs/` 被 `.gitignore` 忽略，全新克隆必然崩溃 → 改为候选路径 + 环境变量，并写进 README。
3. **连本地 Dify 返回 404**：Windows 注册表里的系统代理会被 Python 的 `getproxies()` 读取，导致 `127.0.0.1` 请求被转发给代理并返回 404（本项目默认对 Dify 关闭代理；需要经代理访问远程 Dify 时设 `DIFY_TRUST_ENV=1`）。
4. **接口 500**：`Detection(**item)` 因 Pydantic 的序列化别名不参与校验而报错（`class` 与 `class_name` 不一致）→ 内部统一 `class_name`，对外序列化为 `class`。

### 5. 本次改动怎么验证

```powershell
python -m tests.smoke_test      # 10 项冒烟测试，含真实 YOLO 推理
uvicorn app.main:app --reload   # 再开 http://127.0.0.1:8000/docs 逐个接口试
```

实测结果：冒烟测试 10/10 通过；SSE 端到端确认逐块推送（4 个 `delta` 事件后接 `done`）；
图片识别返回 `umbrella 0.96 / person 0.84`；错误契约 422 / 400 / 503 / 502 均按预期返回。

> 开发说明：项目由作者本人设计流程与验证，编码过程大量借助 DeepSeek 完成。
