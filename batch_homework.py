from __future__ import annotations

from utils.concurrent_runner import run_concurrent_homework_session
from utils.config import AppConfig


def main() -> int:
    print("正在读取配置...", flush=True)
    config = AppConfig.from_env()
    print(f"并发 worker 数: {config.worker_count}", flush=True)
    return run_concurrent_homework_session(config)


if __name__ == "__main__":
    raise SystemExit(main())
