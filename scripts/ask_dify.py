"""Dify 连通性自检脚本：向 Dify 发一条测试消息，验证 .env 配置是否可用。

输入：--query 要问的问题；--blocking 切换为一次性返回（默认流式逐段打印）
输出：终端打印回答；配置或网络异常时打印可读原因并以非 0 退出
运行：python -m scripts.ask_dify --query "你好"
来源：原根目录 TAsk_1.py，改为复用 app/services 的 Dify 客户端并支持流式输出。
"""

from __future__ import annotations

import argparse
import asyncio

from app.core.config import settings
from app.services.llm_service import DifyError, llm_service


def parse_args() -> argparse.Namespace:
    """解析自检参数。"""
    parser = argparse.ArgumentParser(description="检查 Dify 配置与连通性")
    parser.add_argument("--query", default="你好，请用一句话介绍一下你自己。", help="要发送的问题")
    parser.add_argument("--blocking", action="store_true", help="使用阻塞模式，一次性打印完整回答")
    return parser.parse_args()


async def run(query: str, blocking: bool) -> int:
    """执行一次对话请求。"""
    if not settings.dify_ready:
        print("❌ 未读取到 DIFY_API_KEY：请复制 .env.example 为 .env 并填写后重试。")
        return 1

    print(f"正在向 {settings.dify_base_url} 发送请求（{'阻塞' if blocking else '流式'}模式）...")
    try:
        if blocking:
            print("\n--- Dify 回答 ---")
            print(await llm_service.ask(query))
        else:
            print("\n--- Dify 回答（流式） ---")
            async for delta in llm_service.stream(query):
                print(delta, end="", flush=True)
            print()
    except DifyError as exc:
        print(f"\n❌ {exc}")
        return 1
    return 0


def main() -> int:
    """脚本入口。"""
    args = parse_args()
    return asyncio.run(run(args.query, args.blocking))


if __name__ == "__main__":
    raise SystemExit(main())
