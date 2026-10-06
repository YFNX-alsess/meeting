"""全局配置：全项目唯一读写环境变量与文件路径的地方。

输入：根目录 .env 文件 + 进程环境变量
输出：settings 单例（Dify 凭证、模型路径、静态目录、上传上限、跨域白名单）
约定：其它模块一律 ``from app.core.config import settings``，不得再直接调用 os.environ。
来源：原根目录 main.py 第 1-2 行与第 16-25 行；原先散落在三个脚本里的 YOLO_CONFIG_DIR 收敛到这里。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# app/core/config.py -> app/core -> app -> 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 读取根目录 .env（已存在的真实环境变量优先，不会被覆盖）
load_dotenv(PROJECT_ROOT / ".env")

# ultralytics 默认把配置写进用户目录，这里统一收敛到项目内。
# 必须在任何 `from ultralytics import ...` 之前执行，因此本模块要最先被导入。
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / ".ultralytics"))

# 权重查找顺序：自训练结果优先，官方预训练模型兜底
_MODEL_CANDIDATE_PATHS = (
    "runs/detect/runs/train/my_second_train/weights/best.pt",
    "runs/train/my_second_train/weights/best.pt",
    "runs/detect/train/weights/best.pt",
    "yolov8n.pt",
)


def _resolve_model_path() -> Path | None:
    """确定实际可用的权重文件：显式配置优先，否则按候选顺序找第一个存在的。"""
    explicit = os.getenv("YOLO_MODEL_PATH", "").strip()
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate if candidate.is_file() else None

    for relative in _MODEL_CANDIDATE_PATHS:
        candidate = PROJECT_ROOT / relative
        if candidate.is_file():
            return candidate
    return None


def _csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """读取逗号分隔的列表型环境变量。"""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _bool_env(name: str, default: bool = False) -> bool:
    """读取布尔型环境变量（1/true/yes/on 视为真）。"""
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """项目运行期配置快照。"""

    project_root: Path
    web_dir: Path
    dify_api_key: str | None
    dify_base_url: str
    dify_user: str
    dify_timeout: float
    dify_trust_env: bool
    model_path: Path | None
    max_upload_mb: int
    cors_origins: tuple[str, ...]

    @property
    def dify_ready(self) -> bool:
        """Dify 是否配置完整（未配置时对话接口应给出明确提示而不是 500）。"""
        return bool(self.dify_api_key)

    @property
    def model_ready(self) -> bool:
        """权重文件是否就位。"""
        return self.model_path is not None

    def describe_model(self) -> str:
        """给接口返回用的模型描述。"""
        if self.model_path is None:
            return "未找到权重文件（可用 YOLO_MODEL_PATH 指定，或先运行 scripts/train.py）"
        try:
            return str(self.model_path.relative_to(self.project_root))
        except ValueError:
            return str(self.model_path)


settings = Settings(
    project_root=PROJECT_ROOT,
    web_dir=PROJECT_ROOT / "web",
    dify_api_key=os.getenv("DIFY_API_KEY") or None,
    dify_base_url=(os.getenv("DIFY_BASE_URL") or "http://localhost/v1").rstrip("/"),
    dify_user=os.getenv("DIFY_USER") or "web-user-001",
    dify_timeout=float(os.getenv("DIFY_TIMEOUT") or 120),
    # 默认不走系统代理：Dify 通常部署在本机，而 Windows 注册表里的代理会劫持
    # 127.0.0.1 的请求并返回 404。需要经代理访问远程 Dify 时设 DIFY_TRUST_ENV=1。
    dify_trust_env=_bool_env("DIFY_TRUST_ENV", False),
    model_path=_resolve_model_path(),
    max_upload_mb=int(os.getenv("MAX_UPLOAD_MB") or 10),
    cors_origins=_csv_env(
        "CORS_ORIGINS",
        ("http://127.0.0.1:8000", "http://localhost:8000", "http://localhost:5173"),
    ),
)
