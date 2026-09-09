from __future__ import annotations

from utils.config import AppConfig
from utils.homework_runner import answer_homework
from utils.login import login
from utils.start_browser import start_browser


def resolve_work_url(config: AppConfig, input_fn=None) -> str:
    input_fn = input_fn or input
    entered_url = input_fn("请输入作业网址（直接回车使用 .env 默认值）: ").strip()
    work_url = entered_url or config.work_url
    if not work_url:
        raise ValueError("Missing XUEXITONG_WORK_URL environment variable and no URL was entered")
    return work_url


def main() -> int:
    print("正在读取配置...", flush=True)
    config = AppConfig.from_env()
    phone, password = config.require_login()
    work_url = resolve_work_url(config)

    print("配置读取完成，准备启动浏览器...", flush=True)
    driver = start_browser(config)
    print("浏览器启动完成，准备登录...", flush=True)
    if not login(driver, config.login_url, phone, password):
        return 1

    result = answer_homework(driver, work_url, config)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
