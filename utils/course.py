from __future__ import annotations

import re
from collections.abc import Sequence

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def extract_course_url(href: str | None) -> str | None:
    if not href:
        return None
    match = re.search(r"switchM\([^,]+,['\"](https?://[^'\"]+)", href)
    return match.group(1) if match else None


def xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    expressions = []
    parts = value.split("'")
    for index, part in enumerate(parts):
        if part:
            expressions.append(f"'{part}'")
        if index != len(parts) - 1:
            expressions.append('"\'"')
    return "concat(" + ", ".join(expressions) + ")"


def find_course_url(driver, timeout: int = 10) -> bool:
    try:
        course_link = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "zne_kc_icon"))
        )
        url = extract_course_url(course_link.get_attribute("href"))
        if not url:
            print("未匹配到课程URL")
            return False

        print("提取的课程URL:", url)
        driver.get(url)
        WebDriverWait(driver, timeout).until(EC.url_contains("mooc1-1"))
        print("进入课程成功，当前URL:", driver.current_url)
        return True
    except TimeoutException:
        print("查找课程入口超时")
        return False
    except WebDriverException as exc:
        print(f"提取课程URL失败: {exc}")
        return False


def find_course_name(driver, timeout: int = 15) -> str | None:
    try:
        course_elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".course-name"))
        )
        course_names = [course.text.strip() for course in course_elements if course.text.strip()]
        return choose_from_list(course_names, "请输入要选择的课程编号")
    except TimeoutException:
        print("课程列表加载超时")
        return None
    except WebDriverException as exc:
        print(f"获取课程列表出错: {exc}")
        return None


def choose_from_list(items: Sequence[str], prompt: str) -> str | None:
    if not items:
        print("没有可选择的项目")
        return None

    print("\n列表:")
    for index, item in enumerate(items, 1):
        print(f"{index}. {item}")

    while True:
        try:
            selected = int(input(f"\n{prompt} (1-{len(items)}): "))
        except ValueError:
            print("请输入有效数字")
            continue

        if 1 <= selected <= len(items):
            return items[selected - 1]
        print(f"请输入有效编号(1-{len(items)})")


def enter_target_course(driver, target_course: str | None, timeout: int = 10) -> bool:
    if not target_course:
        print("未选择课程")
        return False

    try:
        original_window = driver.current_window_handle
        target = xpath_literal(target_course)
        target_link = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//*[contains(@class, 'course-name') and contains(text(), {target})]/ancestor::a",
                )
            )
        )
        target_link.click()
        print(f"\n选择进入课程: {target_course}")

        WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        print("新窗口URL:", driver.current_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), {target})]"))
        )
        print("成功进入该课程")
        return True
    except TimeoutException:
        print(f"错误：未找到课程 '{target_course}'")
        return False
    except WebDriverException as exc:
        print(f"进入课程失败: {exc}")
        return False


def click_homework_tab(driver, timeout: int = 15) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-content.stuNavigationList"))
        )
        homework_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[@class="nav_content" and text()="作业"]'))
        )
        homework_tab.click()
        print("成功点击作业标签")
        return True
    except TimeoutException:
        print("查找或点击作业标签超时")
        return False
    except WebDriverException as exc:
        print(f"点击作业标签时出错: {exc}")
        return False


def print_iframe(driver) -> None:
    try:
        print("当前所有iframe的ID和名称:")
        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            print(f"ID: {iframe.get_attribute('id')}, Name: {iframe.get_attribute('name')}")
    except WebDriverException as exc:
        print(f"读取iframe失败: {exc}")


def enter_iframe(driver, timeout: int = 20) -> bool:
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if not iframes:
            print("未找到任何iframe")
            return False

        first_iframe = iframes[0]
        iframe_id = first_iframe.get_attribute("id")
        iframe_name = first_iframe.get_attribute("name")
        print(f"ID: {iframe_id}, Name: {iframe_name}")

        if iframe_id:
            locator = (By.ID, iframe_id)
        elif iframe_name:
            locator = (By.NAME, iframe_name)
        else:
            driver.switch_to.frame(first_iframe)
            print("已切换到当前iframe")
            return True

        WebDriverWait(driver, timeout).until(EC.frame_to_be_available_and_switch_to_it(locator))
        print("已切换到当前iframe")
        return True
    except WebDriverException as exc:
        print(f"切换iframe失败: {exc}")
        driver.switch_to.default_content()
        return False


def get_all_exercise(driver, timeout: int = 20) -> list[dict[str, object]]:
    try:
        section = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="bottomList"]/ul'))
        )
        exercises = section.find_elements(By.XPATH, "./li")
        print(f"成功找到 {len(exercises)} 个练习")

        exercises_info = []
        for index, exercise in enumerate(exercises, 1):
            try:
                item = _parse_exercise_item(exercise, index)
                _print_exercise(item)
                exercises_info.append(item)
            except WebDriverException as exc:
                print(f"解析第{index}个练习时出错: {exc}")
        return exercises_info
    except TimeoutException:
        print("未找到练习列表")
        return []
    except WebDriverException as exc:
        print(f"获取练习列表失败: {exc}")
        return []


def enter_exercise(driver, exercise: dict[str, object], timeout: int = 15) -> bool:
    active_id = exercise.get("activeid")
    if not active_id:
        print("练习缺少activeid，无法进入")
        return False

    try:
        target_xpath = f'//div[@class="bottomList"]/ul/li[contains(@data, "workId={active_id}")]'
        target_element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, target_xpath))
        )
        target_element.click()
        print("成功进入该练习页")
        return True
    except TimeoutException:
        print("页面跳转超时")
        return False
    except WebDriverException as exc:
        print(f"进入练习失败: {exc}")
        return False


def switch_to_target_iframe(driver, timeout: int = 10) -> bool:
    driver.switch_to.default_content()
    locators = [
        (By.ID, "frame_content-hd"),
        (By.NAME, "frame_content-hd"),
        (By.XPATH, "//iframe[contains(@id, 'frame_content')]"),
    ]
    for locator in locators:
        try:
            iframe = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
            driver.switch_to.frame(iframe)
            print("成功切换到目标iframe")
            return True
        except TimeoutException:
            continue
    print("所有iframe定位方式均失败")
    return False


def select_exercise_interactively(exercises_info: Sequence[dict[str, object]]) -> dict[str, object] | None:
    if not exercises_info:
        print("没有可选择的练习")
        return None

    while True:
        try:
            selected = int(input(f"请输入要查看的练习序号 (1-{len(exercises_info)}): "))
        except ValueError:
            print("请输入有效数字")
            continue

        if 1 <= selected <= len(exercises_info):
            return exercises_info[selected - 1]
        print("序号超出范围，请重新输入")


def _parse_exercise_item(exercise, index: int) -> dict[str, object]:
    item = {
        "index": index,
        "activeid": _extract_work_id(exercise.get_attribute("data")),
        "title": _optional_text(exercise, './/p[contains(@class, "overHidden2")]'),
        "status": _extract_status(exercise),
        "end_time": _extract_end_time(exercise),
        "analysis_url": _extract_analysis_url(exercise),
    }
    title = str(item["title"] or "")
    item["activity_type"] = "随堂练习" if "随堂练习" in title else "其他活动"
    return item


def _extract_work_id(data_url: str | None) -> str | None:
    if not data_url or "workId=" not in data_url:
        return None
    return data_url.split("workId=", 1)[1].split("&", 1)[0]


def _optional_text(element, xpath: str) -> str:
    try:
        return element.find_element(By.XPATH, xpath).text.strip()
    except NoSuchElementException:
        return ""


def _extract_status(exercise) -> str:
    status = _optional_text(exercise, './/p[contains(@class, "status")]')
    if status:
        return status
    time_text = _optional_text(exercise, './/div[contains(@class, "time")]')
    return "进行中" if "剩余" in time_text else "未知状态"


def _extract_end_time(exercise) -> str:
    time_text = _optional_text(exercise, './/div[contains(@class, "time")]')
    if not time_text:
        return "无时间信息"
    return time_text.replace("剩余", "").replace("结束时间：", "").strip()


def _extract_analysis_url(exercise) -> str | None:
    try:
        return exercise.find_element(By.XPATH, './/a[contains(@class, "insightBtn")]').get_attribute("href")
    except NoSuchElementException:
        return None


def _print_exercise(item: dict[str, object]) -> None:
    print(f"{item['index']}. [{item['activity_type']}] {item['title']}")
    print(f"   状态: {item['status']} | 结束时间: {item['end_time']}")
    print(f"   活动ID: {item['activeid']}")
    if item["analysis_url"]:
        print(f"   分析链接: {item['analysis_url']}")
