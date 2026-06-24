from __future__ import annotations

from dataclasses import dataclass
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By


@dataclass(frozen=True)
class HomeworkItem:
    title: str
    url: str | None
    work_id: str | None
    status_text: str
    is_openable: bool

    @property
    def identity(self) -> str:
        return self.work_id or self.url or self.title


SUBMITTED_MARKERS = ("已提交", "已完成", "已批阅")
UNSUBMITTED_MARKERS = ("未提交", "待完成", "未完成", "进行中")
HOMEWORK_NAV_SELECTORS = [
    (By.CSS_SELECTOR, 'li[dataname="zy"] a[data-url]'),
    (By.CSS_SELECTOR, 'a[data-url*="/mooc2/work/list"]'),
    (By.CSS_SELECTOR, 'a[title="作业"][data-url]'),
    (By.XPATH, '//li[@dataname="zy"]//a[@data-url]'),
    (By.XPATH, '//a[contains(@data-url, "/mooc2/work/list")]'),
]
HOMEWORK_ITEM_SELECTORS = [
    "a[href*='workId=']",
    "a[href*='workid=']",
    "[data*='workId=']",
    "[data*='workid=']",
    "[onclick*='workId=']",
    "[onclick*='workid=']",
]
NEXT_PAGE_SELECTORS = [
    (By.XPATH, "//*[self::a or self::button][contains(normalize-space(.), '下一页')]"),
    (By.XPATH, "//*[self::a or self::button][contains(@title, '下一页')]"),
    (By.XPATH, "//*[self::a or self::button][contains(@aria-label, '下一页')]"),
    (By.CSS_SELECTOR, "a.layui-laypage-next"),
    (By.CSS_SELECTOR, ".layui-laypage-next"),
    (By.CSS_SELECTOR, "a[lay-page-next]"),
    (By.CSS_SELECTOR, "a.next"),
    (By.CSS_SELECTOR, ".next"),
]
PREVIOUS_PAGE_SELECTORS = [
    (By.XPATH, "//*[self::a or self::button][contains(normalize-space(.), '上一页')]"),
    (By.XPATH, "//*[self::a or self::button][contains(@title, '上一页')]"),
    (By.XPATH, "//*[self::a or self::button][contains(@aria-label, '上一页')]"),
    (By.CSS_SELECTOR, "a.layui-laypage-prev"),
    (By.CSS_SELECTOR, ".layui-laypage-prev"),
    (By.CSS_SELECTOR, "a[lay-page-prev]"),
    (By.CSS_SELECTOR, "a.prev"),
    (By.CSS_SELECTOR, ".prev"),
]
MAX_HOMEWORK_PAGES = 20


def extract_work_id(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    values = query.get("workId") or query.get("workid")
    return values[0] if values else None


def is_submitted_status(status_text: str) -> bool:
    text = status_text or ""
    if any(marker in text for marker in UNSUBMITTED_MARKERS):
        return False
    return any(marker in text for marker in SUBMITTED_MARKERS)


def filter_unfinished(items: list[HomeworkItem]) -> list[HomeworkItem]:
    return [
        item
        for item in items
        if item.is_openable and item.url and not is_submitted_status(item.status_text)
    ]


def dedupe_homework_items(items: list[HomeworkItem]) -> list[HomeworkItem]:
    seen = set()
    result = []
    for item in items:
        key = item.work_id or item.url
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def scan_homework_list(driver) -> list[HomeworkItem]:
    _switch_to_homework_window(driver)
    _switch_to_default_content(driver)
    items = _scan_homework_items_with_pagination(driver)
    if not items:
        items = _scan_homework_items_in_iframes(driver)
    _switch_to_default_content(driver)
    return dedupe_homework_items(items)


def _scan_homework_items_with_pagination(driver) -> list[HomeworkItem]:
    _reset_to_first_homework_page(driver)

    items: list[HomeworkItem] = []
    seen_pages: set[tuple[str, ...]] = set()

    for _page_index in range(MAX_HOMEWORK_PAGES):
        page_items = _scan_homework_items_in_current_context(driver)
        signature = _homework_page_signature(page_items)
        if signature in seen_pages:
            break
        seen_pages.add(signature)
        items.extend(page_items)

        if not page_items or not _click_next_homework_page(driver, signature):
            break

    return dedupe_homework_items(items)


def _scan_homework_items_in_current_context(driver) -> list[HomeworkItem]:
    candidates = []

    for selector in HOMEWORK_ITEM_SELECTORS:
        try:
            candidates.extend(driver.find_elements(By.CSS_SELECTOR, selector))
        except WebDriverException:
            continue

    items = []
    for index, element in enumerate(candidates, 1):
        try:
            url = _element_url(element)
            title = _element_title(element, index)
            container_text = _container_text(element)
            items.append(
                HomeworkItem(
                    title=title,
                    url=url,
                    work_id=extract_work_id(url),
                    status_text=container_text,
                    is_openable=bool(url),
                )
            )
        except WebDriverException:
            continue

    return dedupe_homework_items(items)


def _scan_homework_items_in_iframes(driver) -> list[HomeworkItem]:
    items = []
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
    except WebDriverException:
        return items

    for iframe in iframes:
        try:
            driver.switch_to.frame(iframe)
            items.extend(_scan_homework_items_with_pagination(driver))
        except WebDriverException:
            continue
        finally:
            _switch_to_default_content(driver)
    return dedupe_homework_items(items)


def _homework_page_signature(items: list[HomeworkItem]) -> tuple[str, ...]:
    return tuple(item.identity for item in items)


def _click_next_homework_page(driver, previous_signature: tuple[str, ...]) -> bool:
    next_element = _find_page_element(driver, NEXT_PAGE_SELECTORS, blocked_text="上一页")
    if next_element is None:
        return False

    return _click_page_element(driver, next_element, previous_signature)


def _reset_to_first_homework_page(driver) -> None:
    seen_pages: set[tuple[str, ...]] = set()
    for _page_index in range(MAX_HOMEWORK_PAGES):
        signature = _homework_page_signature(_scan_homework_items_in_current_context(driver))
        if signature in seen_pages:
            break
        seen_pages.add(signature)

        previous_element = _find_page_element(driver, PREVIOUS_PAGE_SELECTORS, blocked_text="下一页")
        if previous_element is None:
            break
        if not _click_page_element(driver, previous_element, signature):
            break


def _click_page_element(driver, element, previous_signature: tuple[str, ...]) -> bool:
    try:
        element.click()
    except WebDriverException:
        try:
            driver.execute_script("arguments[0].click();", element)
        except (AttributeError, WebDriverException):
            return False

    _wait_for_homework_page_change(driver, previous_signature)
    return True


def _find_page_element(driver, selectors: list[tuple[str, str]], blocked_text: str):
    for by, selector in selectors:
        try:
            elements = driver.find_elements(by, selector)
        except WebDriverException:
            continue
        for element in elements:
            if _is_enabled_page_element(element, blocked_text):
                return element
    return None


def _is_enabled_page_element(element, blocked_text: str) -> bool:
    try:
        if hasattr(element, "is_displayed") and not element.is_displayed():
            return False
    except WebDriverException:
        return False

    class_name = _safe_element_attr(element, "class").lower()
    disabled = _safe_element_attr(element, "disabled").lower()
    aria_disabled = _safe_element_attr(element, "aria-disabled").lower()
    text = (getattr(element, "text", "") or "").strip()

    disabled_markers = ("disabled", "layui-disabled", "pagebtn_unable", "disable")
    if any(marker in class_name for marker in disabled_markers):
        return False
    if disabled in {"true", "disabled", "1"} or aria_disabled == "true":
        return False
    if blocked_text in text:
        return False
    return True


def _safe_element_attr(element, name: str) -> str:
    try:
        return element.get_attribute(name) or ""
    except WebDriverException:
        return ""


def _wait_for_homework_page_change(
    driver,
    previous_signature: tuple[str, ...],
    timeout_seconds: float = 5.0,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        current_signature = _homework_page_signature(_scan_homework_items_in_current_context(driver))
        if current_signature != previous_signature:
            return True
        time.sleep(0.25)
    return False


def ensure_homework_list_page(driver) -> bool:
    if scan_homework_list(driver):
        return True

    iframe_src = _find_homework_iframe_src(driver)
    if iframe_src:
        print(f"已发现真实作业列表 iframe: {iframe_src}")
        return True

    nav_element = find_homework_nav(driver)
    url = find_homework_list_url(driver)
    if not nav_element and not url:
        print("当前页面没有发现作业列表，也没有找到作业导航 data-url。请手动点击左侧“作业”进入列表页后再继续。")
        return False

    if nav_element and _click_homework_nav(driver, nav_element):
        print("当前是课程外壳页，正在点击左侧“作业”导航进入真实作业列表页。")
        _wait_for_homework_list_ready(driver)
        return True

    iframe_src = _find_homework_iframe_src(driver)
    target_url = iframe_src or url
    if not target_url:
        return False

    print(f"点击作业导航失败，正在使用页面已有作业地址进入: {target_url}")
    driver.get(target_url)
    _wait_for_homework_list_ready(driver)
    return True


def find_homework_list_url(driver) -> str | None:
    nav_element = find_homework_nav(driver)
    if not nav_element:
        return None
    data_url = nav_element.get_attribute("data-url")
    if not data_url:
        return None
    return build_homework_list_url(data_url, _course_context(driver))


def find_homework_nav(driver):
    _switch_to_homework_window(driver)
    _switch_to_default_content(driver)
    for by, selector in HOMEWORK_NAV_SELECTORS:
        try:
            elements = driver.find_elements(by, selector)
        except WebDriverException:
            continue
        for element in elements:
            if element.get_attribute("data-url"):
                return element
    return None


def build_homework_list_url(base_url: str, context: dict[str, str]) -> str:
    parsed = urlparse(base_url)
    query = parse_qs(parsed.query, keep_blank_values=True)

    course_id = context.get("courseid") or context.get("courseId")
    clazz_id = context.get("clazzid") or context.get("classId")
    cpi = context.get("cpi")
    ut = context.get("ut") or context.get("heardUt")

    if course_id:
        query["courseId"] = [course_id]
    if clazz_id:
        query["classId"] = [clazz_id]
        query["clazzId"] = [clazz_id]
    if cpi:
        query["cpi"] = [cpi]
    if ut:
        query["ut"] = [ut]

    encoded = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, encoded, parsed.fragment))


def print_homework_items(items: list[HomeworkItem]) -> None:
    print(f"扫描到作业 {len(items)} 个")
    for index, item in enumerate(items, 1):
        status = item.status_text.replace("\n", " ")[:80]
        print(f"{index}. {item.title} | workId={item.work_id} | 状态片段={status}")


def _element_url(element) -> str | None:
    for attr_name in ("href", "data", "data-url", "onclick"):
        value = element.get_attribute(attr_name)
        if value:
            return value
    return None


def _element_title(element, index: int) -> str:
    text = (element.text or "").strip()
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return f"作业{index}"


def _container_text(element) -> str:
    for xpath in ("./ancestor-or-self::li[1]", "./ancestor::div[1]", "."):
        try:
            return element.find_element(By.XPATH, xpath).text.strip()
        except WebDriverException:
            continue
    return ""


def _course_context(driver) -> dict[str, str]:
    context = {}
    for field_id in ("courseid", "clazzid", "cpi", "ut", "heardUt"):
        try:
            elements = driver.find_elements(By.ID, field_id)
        except WebDriverException:
            continue
        for element in elements:
            value = element.get_attribute("value")
            if value:
                context[field_id] = value
                break
    return context


def _switch_to_default_content(driver) -> bool:
    try:
        driver.switch_to.default_content()
        return True
    except (AttributeError, WebDriverException):
        return False


def _click_homework_nav(driver, element) -> bool:
    try:
        element.click()
        return True
    except WebDriverException:
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except (AttributeError, WebDriverException):
            return False


def _wait_for_homework_list_ready(driver, timeout_seconds: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if scan_homework_list(driver) or _find_homework_iframe_src(driver):
            return True
        time.sleep(0.25)
    return False


def _find_homework_iframe_src(driver, switch_window: bool = True) -> str | None:
    if switch_window:
        _switch_to_homework_window(driver)
    _switch_to_default_content(driver)
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
    except WebDriverException:
        return None

    for iframe in iframes:
        try:
            frame_id = iframe.get_attribute("id") or ""
            frame_name = iframe.get_attribute("name") or ""
            src = iframe.get_attribute("src") or ""
        except WebDriverException:
            continue
        if "frame_content-zy" in (frame_id, frame_name) or "/mooc2/work/list" in src:
            return src or None
    return None


def _switch_to_homework_window(driver) -> bool:
    try:
        handles = list(driver.window_handles)
    except (AttributeError, WebDriverException):
        return False
    if not handles:
        return False

    try:
        original = driver.current_window_handle
    except WebDriverException:
        original = None

    best_handle = None
    best_score = 0
    best_url = ""
    for handle in reversed(handles):
        try:
            driver.switch_to.window(handle)
            _switch_to_default_content(driver)
            score = _homework_window_score(driver)
            if score > best_score:
                best_handle = handle
                best_score = score
                best_url = _safe_current_url(driver)
            if score >= 100:
                break
        except WebDriverException:
            continue

    if best_handle:
        try:
            driver.switch_to.window(best_handle)
            _switch_to_default_content(driver)
            if original and best_handle != original:
                print(f"已切换到课程/作业标签页: {best_url}")
            return True
        except WebDriverException:
            return False

    if original and original in handles:
        try:
            driver.switch_to.window(original)
            _switch_to_default_content(driver)
        except WebDriverException:
            pass
    return False


def _homework_window_score(driver) -> int:
    url = _safe_current_url(driver).lower()
    if "mooc2/work/list" in url or "mooc-ans/mooc2/work" in url:
        return 100

    if _find_homework_iframe_src(driver, switch_window=False):
        return 95

    selectors = [(By.CSS_SELECTOR, selector) for selector in HOMEWORK_ITEM_SELECTORS]
    selectors.extend(HOMEWORK_NAV_SELECTORS[:2])
    if _has_any_element(driver, selectors):
        return 90

    if "mooc2-ans/mycourse/stu" in url or "mycourse/stu" in url:
        return 50
    if _has_any_element(driver, [(By.ID, "courseid"), (By.ID, "clazzid")]):
        return 20
    return 0


def _has_any_element(driver, selectors: list[tuple[str, str]]) -> bool:
    for by, selector in selectors:
        try:
            if driver.find_elements(by, selector):
                return True
        except WebDriverException:
            continue
    return False


def _safe_current_url(driver) -> str:
    try:
        return driver.current_url or ""
    except (AttributeError, WebDriverException):
        return ""
