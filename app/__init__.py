"""AIU 二面项目后端包。

分层约定：
- app/core      配置（唯一读写环境变量的地方）
- app/services  计算与服务（Dify 对话、YOLO 检测），不感知 HTTP
- app/routers   HTTP 接口（参数校验 + 调用 service + 组装响应）
- app/main.py   装配入口，只负责 create_app()
"""
