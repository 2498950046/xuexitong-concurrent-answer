from utils.homework_list import (
    HomeworkItem,
    build_homework_list_url,
    dedupe_homework_items,
    ensure_homework_list_page,
    extract_work_id,
    filter_unfinished,
    is_submitted_status,
    scan_homework_list,
)
from selenium.webdriver.common.by import By


def test_extract_work_id_from_url():
    url = "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/dowork?courseId=1&workId=53136307&answerId=0"

    assert extract_work_id(url) == "53136307"


def test_submitted_status_detection():
    assert is_submitted_status("已提交")
    assert is_submitted_status("已完成")
    assert not is_submitted_status("未提交")
    assert not is_submitted_status("待完成")


def test_filter_unfinished_keeps_open_unsubmitted_items():
    items = [
        HomeworkItem(title="done", url="https://example.test/1", work_id="1", status_text="已提交", is_openable=True),
        HomeworkItem(title="todo", url="https://example.test/2", work_id="2", status_text="未提交", is_openable=True),
        HomeworkItem(title="closed", url=None, work_id=None, status_text="未提交", is_openable=False),
    ]

    assert filter_unfinished(items) == [items[1]]


def test_dedupe_homework_items_prefers_work_id_then_url():
    items = [
        HomeworkItem(title="a", url="https://example.test/a?workId=1", work_id="1", status_text="未提交", is_openable=True),
        HomeworkItem(title="a duplicate", url="https://example.test/other?workId=1", work_id="1", status_text="未提交", is_openable=True),
        HomeworkItem(title="b", url="https://example.test/b", work_id=None, status_text="未提交", is_openable=True),
        HomeworkItem(title="b duplicate", url="https://example.test/b", work_id=None, status_text="未提交", is_openable=True),
    ]

    assert dedupe_homework_items(items) == [items[0], items[2]]


def test_build_homework_list_url_appends_course_params():
    url = build_homework_list_url(
        "https://mooc1.chaoxing.com/mooc2/work/list",
        {
            "courseid": "260920142",
            "clazzid": "142754771",
            "cpi": "352094458",
            "ut": "s",
        },
    )

    assert url == (
        "https://mooc1.chaoxing.com/mooc2/work/list?"
        "courseId=260920142&classId=142754771&clazzId=142754771&cpi=352094458&ut=s"
    )


def test_build_homework_list_url_preserves_existing_query():
    url = build_homework_list_url(
        "https://mooc1.chaoxing.com/mooc2/work/list?foo=bar",
        {"courseid": "1", "clazzid": "2", "cpi": "3", "ut": "s"},
    )

    assert url == (
        "https://mooc1.chaoxing.com/mooc2/work/list?"
        "foo=bar&courseId=1&classId=2&clazzId=2&cpi=3&ut=s"
    )


class _FakeSwitchTo:
    def __init__(self, driver):
        self.driver = driver

    def default_content(self):
        self.driver.in_default_content = True
        self.driver.default_content_calls += 1
        if hasattr(self.driver, "switch_default_content"):
            self.driver.switch_default_content()

    def window(self, handle):
        self.driver.switch_window(handle)

    def frame(self, frame):
        if hasattr(self.driver, "switch_frame"):
            self.driver.switch_frame(frame)


class _FakeElement:
    def __init__(self, attrs=None, text="", on_click=None):
        self.attrs = attrs or {}
        self.text = text
        self.clicked = False
        self.on_click = on_click

    def get_attribute(self, name):
        return self.attrs.get(name)

    def find_element(self, by, value):
        return self

    def click(self):
        self.clicked = True
        if self.on_click:
            self.on_click()


class _CourseShellDriver:
    def __init__(self):
        self.in_default_content = False
        self.default_content_calls = 0
        self.opened_urls = []
        self.switch_to = _FakeSwitchTo(self)
        self.context = {
            "courseid": "260920142",
            "clazzid": "142754771",
            "cpi": "352094458",
            "heardUt": "s",
        }
        self.show_homework_frame = False
        self.homework_frame = _FakeElement(
            {
                "id": "frame_content-zy",
                "name": "frame_content-zy",
                "src": (
                    "https://mooc1.chaoxing.com/mooc2/work/list?"
                    "courseId=260920142&classId=142754771&cpi=352094458"
                    "&stuenc=fake-stuenc&enc=fake-work-enc"
                ),
            }
        )
        self.homework_nav = _FakeElement(
            {"data-url": "https://mooc1.chaoxing.com/mooc2/work/list"},
            on_click=self._show_homework_frame,
        )

    def _show_homework_frame(self):
        self.show_homework_frame = True

    def find_elements(self, by, value):
        if not self.in_default_content:
            return []
        if by == By.TAG_NAME and value == "iframe" and self.show_homework_frame:
            return [self.homework_frame]
        if by == By.CSS_SELECTOR and value == 'li[dataname="zy"] a[data-url]':
            return [self.homework_nav]
        if by == By.ID and value in self.context:
            return [_FakeElement({"value": self.context[value]})]
        return []

    def get(self, url):
        self.opened_urls.append(url)


class _MultiTabCourseDriver(_CourseShellDriver):
    def __init__(self):
        super().__init__()
        self.window_handles = ["space", "course"]
        self.current_window_handle = "space"
        self.current_handle = "space"
        self.urls = {
            "space": "https://i.mooc.chaoxing.com/space/index?ws=1&t=1782213136798",
            "course": (
                "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?"
                "courseid=260920142&clazzid=142754771&cpi=352094458"
            ),
        }
        self.opened_urls = []

    @property
    def current_url(self):
        return self.urls[self.current_handle]

    def switch_window(self, handle):
        self.current_handle = handle
        self.current_window_handle = handle
        self.in_default_content = False

    def find_elements(self, by, value):
        if self.current_handle == "space":
            return []
        return super().find_elements(by, value)

    def get(self, url):
        self.opened_urls.append((self.current_window_handle, url))


def test_ensure_homework_list_page_switches_to_default_content_before_nav_lookup():
    driver = _CourseShellDriver()

    assert ensure_homework_list_page(driver) is True
    assert driver.default_content_calls >= 1
    assert driver.homework_nav.clicked is True
    assert driver.opened_urls == []


def test_ensure_homework_list_page_switches_from_space_tab_to_course_tab():
    driver = _MultiTabCourseDriver()

    assert ensure_homework_list_page(driver) is True
    assert driver.current_window_handle == "course"
    assert driver.homework_nav.clicked is True
    assert driver.opened_urls == []


class _IframeHomeworkDriver(_CourseShellDriver):
    def __init__(self):
        super().__init__()
        self.context_name = "top"
        self.frame_element = _FakeElement(
            {
                "id": "frame_content-zy",
                "name": "frame_content-zy",
                "src": (
                    "https://mooc1.chaoxing.com/mooc2/work/list?"
                    "courseId=260920142&classId=142754771&cpi=352094458"
                    "&stuenc=aac3de3281dda74d8b2c5e3572e74305&enc=941a6cce75745ba3054b016236b5a78c"
                ),
            }
        )
        self.homework_item = _FakeElement(
            {
                "data": (
                    "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?"
                    "courseId=260920142&classId=142754771&cpi=352094458"
                    "&workId=53136624&answerId=55911557&enc=03ec7d5177d922284081c870f3ec50d8"
                ),
                "onclick": "goTask(this);",
            },
            "第十章习题库\n\n未提交\n\n剩余52小时26分钟",
        )

    def switch_frame(self, frame):
        if frame is self.frame_element:
            self.context_name = "homework_frame"
            self.in_default_content = False

    def switch_default_content(self):
        self.context_name = "top"

    def find_elements(self, by, value):
        if self.context_name == "top":
            if by == By.TAG_NAME and value == "iframe":
                return [self.frame_element]
            return []
        if self.context_name == "homework_frame":
            if by == By.CSS_SELECTOR and value in ("[data*='workId=']", "[data*='workid=']"):
                return [self.homework_item]
            return []
        return []


def test_scan_homework_list_reads_items_inside_homework_iframe():
    driver = _IframeHomeworkDriver()

    items = scan_homework_list(driver)

    assert items == [
        HomeworkItem(
            title="第十章习题库",
            url=(
                "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?"
                "courseId=260920142&classId=142754771&cpi=352094458"
                "&workId=53136624&answerId=55911557&enc=03ec7d5177d922284081c870f3ec50d8"
            ),
            work_id="53136624",
            status_text="第十章习题库\n\n未提交\n\n剩余52小时26分钟",
            is_openable=True,
        )
    ]


class _PaginatedIframeHomeworkDriver(_IframeHomeworkDriver):
    def __init__(self):
        super().__init__()
        self.page = 1
        self.page_two_item = _FakeElement(
            {
                "data": (
                    "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?"
                    "courseId=260920142&classId=142754771&cpi=352094458"
                    "&workId=53136625&answerId=55911558&enc=page2"
                ),
            },
            "第十一章习题库\n\n未提交\n\n剩余52小时26分钟",
        )
        self.next_button = _FakeElement({"class": "next"}, "下一页", on_click=self._next_page)
        self.previous_button = _FakeElement({"class": "prev"}, "上一页", on_click=self._previous_page)

    def _next_page(self):
        self.page = 2

    def _previous_page(self):
        self.page = 1

    def find_elements(self, by, value):
        if self.context_name == "homework_frame":
            if by == By.CSS_SELECTOR and value in ("[data*='workId=']", "[data*='workid=']"):
                return [self.homework_item] if self.page == 1 else [self.page_two_item]
            if by == By.XPATH and "下一页" in value and self.page == 1:
                return [self.next_button]
            if by == By.XPATH and "上一页" in value and self.page == 2:
                return [self.previous_button]
        return super().find_elements(by, value)


def test_scan_homework_list_reads_all_paginated_homework_pages():
    driver = _PaginatedIframeHomeworkDriver()

    items = scan_homework_list(driver)

    assert [item.work_id for item in items] == ["53136624", "53136625"]
    assert [item.title for item in items] == ["第十章习题库", "第十一章习题库"]


def test_scan_homework_list_starts_from_first_page_when_current_page_is_later():
    driver = _PaginatedIframeHomeworkDriver()
    driver.page = 2

    items = scan_homework_list(driver)

    assert [item.work_id for item in items] == ["53136624", "53136625"]
