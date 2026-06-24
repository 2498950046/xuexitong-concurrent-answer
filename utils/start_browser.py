from __future__ import annotations

from pathlib import Path
import threading
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service

from utils.chromedriver_manager import ensure_project_chromedriver, project_driver_path
from utils.config import AppConfig


_CHROMEDRIVER_REPAIR_LOCK = threading.Lock()
_CHROMEDRIVER_START_ATTEMPTS = 4


def start_browser(config: AppConfig | None = None):
    config = config or AppConfig.from_env()
    chromedriver_path = _preferred_chromedriver_path(config)
    try:
        return _launch_browser(config, chromedriver_path)
    except WebDriverException as exc:
        print(f"Chrome 启动失败，正在检查并修复 ChromeDriver 后重试: {exc}", flush=True)
        with _CHROMEDRIVER_REPAIR_LOCK:
            repaired_path = ensure_project_chromedriver(
                config.chromedriver_path,
                force_refresh=True,
            )
        return _launch_browser(config, repaired_path)


def _preferred_chromedriver_path(config: AppConfig) -> str:
    if config.chromedriver_path:
        return str(Path(config.chromedriver_path))
    return str(project_driver_path())


def _launch_browser(config: AppConfig, chromedriver_path: str):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", config.browser_detach)
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    print(f"正在启动浏览器，使用 ChromeDriver: {chromedriver_path}", flush=True)
    service = _FastFailChromeService(executable_path=chromedriver_path)
    return webdriver.Chrome(service=service, options=options)


class _FastFailChromeService(Service):
    def start(self) -> None:
        if self._path is None:
            raise WebDriverException("Service path cannot be None.")
        self._start_process(self._path)

        for count in range(_CHROMEDRIVER_START_ATTEMPTS):
            self.assert_process_still_running()
            if self.is_connectable():
                return
            sleep(min(0.01 + 0.05 * count, 0.2))

        self.stop()
        raise WebDriverException(f"Can not connect to the Service {self._path}")
