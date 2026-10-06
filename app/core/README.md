# app/core — 配置层

- **职责**：全项目唯一读写环境变量和文件路径的地方。读取根目录 `.env`，产出 `settings` 单例。
- **对外接口**：`from app.core.config import settings`（`dify_ready` / `model_ready` / `describe_model()`）。
- **注意**：`YOLO_CONFIG_DIR` 在本模块导入时设置，因此它必须先于任何 `ultralytics` 导入执行，不要调整 `app/core` 的导入顺序。
- **配置项**：见根目录 [.env.example](../.env.example)。
