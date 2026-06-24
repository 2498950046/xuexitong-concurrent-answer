from __future__ import annotations

from queue import Queue
import threading
import time

from selenium.common.exceptions import WebDriverException

from utils.browser_cookies import apply_browser_cookies, capture_browser_cookies, cookie_domains
from utils.config import AppConfig
from utils.homework_list import (
    HomeworkItem,
    ensure_homework_list_page,
    filter_unfinished,
    print_homework_items,
    scan_homework_list,
)
from utils.homework_runner import answer_homework
from utils.login import login
from utils.start_browser import start_browser


STOP = object()


def enqueue_new_items(queue: Queue, items: list[HomeworkItem], processed: set[str]) -> int:
    added = 0
    for item in items:
        key = item.work_id or item.url
        if not key or key in processed:
            continue
        processed.add(key)
        queue.put(item)
        added += 1
    return added


def wait_until_driver_closed(
    driver,
    poll_seconds: float = 1.0,
    stop_event: threading.Event | None = None,
) -> bool:
    while True:
        if stop_event is not None and stop_event.is_set():
            return False
        try:
            if not driver.window_handles:
                return True
        except WebDriverException:
            return True
        time.sleep(poll_seconds)


def run_concurrent_homework_session(config: AppConfig) -> int:
    controller = None
    workers: list[threading.Thread] = []
    task_queue: Queue = Queue()
    stop_event = threading.Event()
    interrupted = False
    failed: list[HomeworkItem] = []

    phone, password = config.require_login()
    try:
        controller = start_browser(config)
        if not login(controller, config.login_url, phone, password):
            return 1

        input("请在主控浏览器中手动进入作业列表页，完成后输入 y 继续: ")
        session_cookies = capture_browser_cookies(controller)
        domains = ", ".join(cookie_domains(session_cookies)) or "无"
        print(f"已从主控浏览器读取登录态 cookie: {len(session_cookies)} 个，域名: {domains}")

        processed: set[str] = set()
        failed_lock = threading.Lock()

        workers = [
            threading.Thread(
                target=_worker_loop,
                args=(
                    worker_index + 1,
                    task_queue,
                    failed,
                    failed_lock,
                    config,
                    session_cookies,
                    stop_event,
                ),
                daemon=True,
                name=f"homework-worker-{worker_index + 1}",
            )
            for worker_index in range(config.worker_count)
        ]
        for worker in workers:
            worker.start()

        while True:
            if stop_event.is_set():
                break
            ensure_homework_list_page(controller)
            items = filter_unfinished(scan_homework_list(controller))
            print_homework_items(items)
            added = enqueue_new_items(task_queue, items, processed)
            print(f"发现未提交作业 {len(items)} 个，本轮新增 {added} 个")

            if added == 0 and task_queue.empty():
                answer = input("没有新的未提交作业。刷新作业列表后输入 y 继续，输入 q 结束: ").strip().lower()
                if answer == "q":
                    break
                _refresh_controller(controller)
                continue

            task_queue.join()
            answer = input("当前队列已完成。请在主控页刷新作业列表后输入 y 继续，输入 q 结束: ").strip().lower()
            if answer == "q":
                break
            _refresh_controller(controller)
    except KeyboardInterrupt:
        interrupted = True
        stop_event.set()
        print("\n收到 Ctrl+C，正在中断并清理浏览器...")
    finally:
        stop_event.set()
        for _worker in workers:
            task_queue.put(STOP)
        for worker in workers:
            worker.join(timeout=5)
        if interrupted and controller is not None:
            _quit_driver(controller)

    if failed:
        print("以下作业处理失败，请手动检查:")
        for item in failed:
            print(f"- {item.title}: {item.url}")
    return 130 if interrupted else 0


def _refresh_controller(controller) -> None:
    try:
        controller.refresh()
    except WebDriverException:
        print("主控页面刷新失败，请手动刷新后继续。")


def _worker_loop(
    worker_id: int,
    task_queue: Queue,
    failed: list[HomeworkItem],
    failed_lock: threading.Lock,
    config: AppConfig,
    session_cookies: list[dict] | None = None,
    stop_event: threading.Event | None = None,
) -> None:
    while True:
        item = task_queue.get()
        try:
            if item is STOP:
                return
            if stop_event is not None and stop_event.is_set():
                return
            _run_worker_item(
                worker_id,
                item,
                failed,
                failed_lock,
                config,
                session_cookies,
                stop_event,
            )
        finally:
            task_queue.task_done()


def _run_worker_item(
    worker_id: int,
    item: HomeworkItem,
    failed: list[HomeworkItem],
    failed_lock: threading.Lock,
    config: AppConfig,
    session_cookies: list[dict] | None = None,
    stop_event: threading.Event | None = None,
) -> None:
    print(f"worker-{worker_id} 开始作业: {item.title}")
    driver = None
    try:
        if stop_event is not None and stop_event.is_set():
            return
        driver = start_browser(config)
        if session_cookies:
            applied = apply_browser_cookies(driver, session_cookies)
            print(f"worker-{worker_id} 已注入登录态 cookie: {applied} 个")
        if not item.url:
            print(f"worker-{worker_id} 作业缺少 URL: {item.title}")
            _record_failed(failed, failed_lock, item)
            return

        result = answer_homework(driver, item.url, config)
        if result.ok:
            print(f"worker-{worker_id} 已完成自动答题: {item.title}")
            print("请检查并手动提交，提交后关闭该 worker 窗口。")
        else:
            _record_failed(failed, failed_lock, item)
            print(f"worker-{worker_id} 自动答题失败: {item.title} ({result.reason})")
            print("请在该窗口中手动处理，处理后关闭窗口。")
        if not wait_until_driver_closed(driver, stop_event=stop_event):
            _quit_driver(driver)
    except Exception as exc:
        _record_failed(failed, failed_lock, item)
        print(f"worker-{worker_id} 异常: {item.title}: {exc}")
        if driver is not None:
            if not wait_until_driver_closed(driver, stop_event=stop_event):
                _quit_driver(driver)


def _record_failed(failed: list[HomeworkItem], failed_lock: threading.Lock, item: HomeworkItem) -> None:
    with failed_lock:
        failed.append(item)


def _quit_driver(driver) -> None:
    try:
        driver.quit()
    except (AttributeError, WebDriverException):
        pass
