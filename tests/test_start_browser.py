from pathlib import Path

from selenium.common.exceptions import WebDriverException

from utils.config import AppConfig
from utils.start_browser import (
    _CHROMEDRIVER_START_ATTEMPTS,
    _FastFailChromeService,
    start_browser,
)


class _FakeService:
    def __init__(self, executable_path):
        self.executable_path = executable_path


class _FakeOptions:
    def __init__(self):
        self.experimental_options = {}

    def add_experimental_option(self, name, value):
        self.experimental_options[name] = value


def _service_path(service):
    return getattr(service, "executable_path", getattr(service, "_path"))


def test_start_browser_uses_existing_driver_before_version_check(monkeypatch):
    calls = []

    def fake_chrome(service, options):
        calls.append(_service_path(service))
        return "driver"

    monkeypatch.setattr("utils.start_browser.Service", _FakeService)
    monkeypatch.setattr("utils.start_browser.webdriver.ChromeOptions", _FakeOptions)
    monkeypatch.setattr("utils.start_browser.webdriver.Chrome", fake_chrome)
    monkeypatch.setattr(
        "utils.start_browser.ensure_project_chromedriver",
        lambda _path: (_ for _ in ()).throw(AssertionError("should not check version before launch")),
    )

    config = AppConfig(chromedriver_path="D:/xuexitong/.drivers/chromedriver.exe")

    assert start_browser(config) == "driver"
    assert [Path(call) for call in calls] == [Path("D:/xuexitong/.drivers/chromedriver.exe")]


def test_start_browser_repairs_driver_after_initial_launch_failure(monkeypatch):
    calls = []
    repair_calls = []

    def fake_chrome(service, options):
        calls.append(_service_path(service))
        if len(calls) == 1:
            raise WebDriverException("session not created")
        return "driver"

    monkeypatch.setattr("utils.start_browser.Service", _FakeService)
    monkeypatch.setattr("utils.start_browser.webdriver.ChromeOptions", _FakeOptions)
    monkeypatch.setattr("utils.start_browser.webdriver.Chrome", fake_chrome)

    def fake_ensure(path, force_refresh=False):
        repair_calls.append((path, force_refresh))
        return "D:/xuexitong/.drivers/fixed-chromedriver.exe"

    monkeypatch.setattr("utils.start_browser.ensure_project_chromedriver", fake_ensure)

    config = AppConfig(chromedriver_path="D:/xuexitong/.drivers/chromedriver.exe")

    assert start_browser(config) == "driver"
    assert [Path(call) for call in calls] == [
        Path("D:/xuexitong/.drivers/chromedriver.exe"),
        Path("D:/xuexitong/.drivers/fixed-chromedriver.exe"),
    ]
    assert repair_calls == [("D:/xuexitong/.drivers/chromedriver.exe", True)]


class _NeverConnectsService(_FastFailChromeService):
    def __init__(self):
        super().__init__(executable_path="chromedriver.exe")
        self.connect_attempts = 0
        self.stopped = False

    def _start_process(self, path):
        self.process = object()

    def assert_process_still_running(self):
        return None

    def is_connectable(self):
        self.connect_attempts += 1
        return False

    def stop(self):
        self.stopped = True


def test_fast_fail_service_limits_startup_connect_attempts():
    service = _NeverConnectsService()

    try:
        service.start()
    except WebDriverException as exc:
        assert "Can not connect" in str(exc)
    else:
        raise AssertionError("expected service start to fail")

    assert service.connect_attempts == _CHROMEDRIVER_START_ATTEMPTS
    assert service.stopped is True
