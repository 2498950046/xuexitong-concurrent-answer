from queue import Queue
from threading import Event, Lock

from utils.concurrent_runner import (
    _run_worker_item,
    enqueue_new_items,
    run_concurrent_homework_session,
    wait_until_driver_closed,
)
from utils.config import AppConfig
from utils.homework_list import HomeworkItem
from utils.homework_runner import HomeworkRunResult


def test_enqueue_new_items_skips_processed_and_duplicates():
    queue = Queue()
    processed = {"1"}
    items = [
        HomeworkItem(title="done", url="https://example.test/1", work_id="1", status_text="未提交", is_openable=True),
        HomeworkItem(title="new", url="https://example.test/2", work_id="2", status_text="未提交", is_openable=True),
        HomeworkItem(title="new duplicate", url="https://example.test/other", work_id="2", status_text="未提交", is_openable=True),
    ]

    added = enqueue_new_items(queue, items, processed)

    assert added == 1
    assert queue.get_nowait().work_id == "2"
    assert processed == {"1", "2"}


class ClosingDriver:
    def __init__(self, open_counts):
        self.open_counts = open_counts

    @property
    def window_handles(self):
        self.open_counts -= 1
        return ["handle"] if self.open_counts > 0 else []


def test_wait_until_driver_closed_returns_when_no_window_handles():
    driver = ClosingDriver(open_counts=2)

    assert wait_until_driver_closed(driver, poll_seconds=0) is True


def test_wait_until_driver_closed_returns_false_when_stop_event_is_set():
    driver = ClosingDriver(open_counts=100)
    stop_event = Event()
    stop_event.set()

    assert wait_until_driver_closed(driver, poll_seconds=0, stop_event=stop_event) is False


def test_run_worker_item_records_failure_when_browser_start_fails(monkeypatch):
    item = HomeworkItem(
        title="作业",
        url="https://example.test/work?workId=1",
        work_id="1",
        status_text="未提交",
        is_openable=True,
    )
    failed = []

    def fail_start_browser(_config):
        raise RuntimeError("browser failed")

    monkeypatch.setattr("utils.concurrent_runner.start_browser", fail_start_browser)

    _run_worker_item(1, item, failed, Lock(), AppConfig())

    assert failed == [item]


class WorkerFakeDriver:
    def __init__(self):
        self.window_handles = []
        self.cookies_applied = False


def test_run_worker_item_applies_session_cookies_before_answering(monkeypatch):
    item = HomeworkItem(
        title="作业",
        url="https://example.test/work?workId=1",
        work_id="1",
        status_text="未提交",
        is_openable=True,
    )
    driver = WorkerFakeDriver()
    cookies = [{"name": "UID", "value": "123", "domain": ".chaoxing.com"}]
    failed = []

    monkeypatch.setattr("utils.concurrent_runner.start_browser", lambda _config: driver)

    def fake_apply_browser_cookies(target_driver, target_cookies):
        assert target_driver is driver
        assert target_cookies == cookies
        driver.cookies_applied = True
        return 1

    def fake_answer_homework(target_driver, url, config):
        assert target_driver is driver
        assert url == item.url
        assert driver.cookies_applied is True
        return HomeworkRunResult(ok=True, reason="answered", question_count=1)

    monkeypatch.setattr("utils.concurrent_runner.apply_browser_cookies", fake_apply_browser_cookies)
    monkeypatch.setattr("utils.concurrent_runner.answer_homework", fake_answer_homework)

    _run_worker_item(1, item, failed, Lock(), AppConfig(), session_cookies=cookies)

    assert failed == []


class StuckWorkerDriver:
    @property
    def window_handles(self):
        return ["handle"]

    def quit(self):
        self.quit_called = True


def test_run_worker_item_quits_driver_when_stop_event_interrupts_wait(monkeypatch):
    item = HomeworkItem(
        title="作业",
        url="https://example.test/work?workId=1",
        work_id="1",
        status_text="未提交",
        is_openable=True,
    )
    driver = StuckWorkerDriver()
    driver.quit_called = False
    failed = []
    stop_event = Event()

    monkeypatch.setattr("utils.concurrent_runner.start_browser", lambda _config: driver)

    def fake_answer_homework(_driver, _url, _config):
        stop_event.set()
        return HomeworkRunResult(ok=True, reason="answered", question_count=1)

    monkeypatch.setattr("utils.concurrent_runner.answer_homework", fake_answer_homework)

    _run_worker_item(1, item, failed, Lock(), AppConfig(), stop_event=stop_event)

    assert failed == []
    assert driver.quit_called is True


class ControllerDriver:
    def __init__(self):
        self.quit_called = False

    def quit(self):
        self.quit_called = True


def test_run_concurrent_homework_session_handles_keyboard_interrupt(monkeypatch, capsys):
    controller = ControllerDriver()

    monkeypatch.setattr("utils.concurrent_runner.start_browser", lambda _config: controller)
    monkeypatch.setattr("utils.concurrent_runner.login", lambda *_args: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: (_ for _ in ()).throw(KeyboardInterrupt()))

    result = run_concurrent_homework_session(AppConfig(phone="135", password="pwd", worker_count=1))

    assert result == 130
    assert controller.quit_called is True
    assert "Ctrl+C" in capsys.readouterr().out
