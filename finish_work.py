from __future__ import annotations

from utils.config import AppConfig
from utils.homework_runner import answer_homework
from utils.login import login
from utils.start_browser import start_browser


def main() -> int:
    print("正在读取配置...", flush=True)
    config = AppConfig.from_env()
    phone, password = config.require_login()
    if not config.work_url:
        raise ValueError("Missing XUEXITONG_WORK_URL environment variable")

    print("配置读取完成，准备启动浏览器...", flush=True)
    driver = start_browser(config)
    print("浏览器启动完成，准备登录...", flush=True)
    if not login(driver, config.login_url, phone, password):
        return 1

    result = answer_homework(driver, config.work_url, config)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
