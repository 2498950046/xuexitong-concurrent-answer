from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from utils.ai import get_deepseek_answer
from utils.answers import (
    batch_items,
    extend_validated_answers,
    normalize_answers_for_questions,
    validate_answer_choices,
)
from utils.click_answer import auto_select_answers
from utils.config import AppConfig
from utils.find_questions import get_questions
from utils.question_format import format_question


ANSWER_INSTRUCTION = """Answer the following single-choice, multiple-choice, and true/false questions.
Return only a JSON string array. Do not include explanations or extra text.
Each answer must use only the option values shown for that question.
For normal choices, use values like "A", "B", "AC", or "BCD".
For true/false questions shown as A 对 / B 错, TRUE will be normalized to A and FALSE to B.
Example: ["A","BC","TRUE","FALSE"]
Questions:"""


@dataclass(frozen=True)
class HomeworkRunResult:
    ok: bool
    reason: str
    question_count: int


def answer_homework(
    driver,
    url: str,
    config: AppConfig,
    get_questions_fn: Callable = get_questions,
    get_answer_fn: Callable = get_deepseek_answer,
    click_answers_fn: Callable = auto_select_answers,
    navigate_next_fn: Callable | None = None,
) -> HomeworkRunResult:
    navigate_next_fn = navigate_next_fn or go_to_next_question_page
    driver.get(url)
    answered_count = 0
    visited_pages: set[tuple[str, ...]] = set()

    while True:
        questions = get_questions_fn(driver)
        if not questions:
            if answered_count:
                return HomeworkRunResult(ok=True, reason="answered", question_count=answered_count)
            print("未获取到题目，停止当前作业")
            return HomeworkRunResult(ok=False, reason="no_questions", question_count=0)

        page_signature = _question_page_signature(questions)
        if page_signature in visited_pages:
            print("检测到题目页面重复，停止继续跳转")
            return HomeworkRunResult(ok=True, reason="answered", question_count=answered_count)
        visited_pages.add(page_signature)

        result = _answer_current_questions(
            driver,
            questions,
            config,
            get_answer_fn,
            click_answers_fn,
        )
        if not result.ok:
            return HomeworkRunResult(
                ok=False,
                reason=result.reason,
                question_count=answered_count + result.question_count,
            )

        answered_count += result.question_count
        if not navigate_next_fn(driver, questions):
            return HomeworkRunResult(ok=True, reason="answered", question_count=answered_count)


def _answer_current_questions(
    driver,
    questions: list[dict[str, object]],
    config: AppConfig,
    get_answer_fn: Callable,
    click_answers_fn: Callable,
) -> HomeworkRunResult:
    all_answers: list[str] = []
    for batch_number, batch in enumerate(batch_items(questions, batch_size=config.batch_size), 1):
        question_list = "\n\n".join(format_question(question) for question in batch)
        full_prompt = f"{ANSWER_INSTRUCTION}\n\n{question_list}"
        print(f"正在请求第 {batch_number} 批答案: {len(batch)} 道题")

        answer_text = get_answer_fn(full_prompt, config)
        if not answer_text:
            print("获取答案失败，AI 返回为空")
            return HomeworkRunResult(ok=False, reason="empty_ai_answer", question_count=len(questions))

        try:
            extend_validated_answers(all_answers, answer_text, expected_count=len(batch))
        except ValueError as exc:
            print(f"答案解析失败: {exc}")
            return HomeworkRunResult(ok=False, reason="invalid_ai_json", question_count=len(questions))

    try:
        all_answers = normalize_answers_for_questions(questions, all_answers)
        validate_answer_choices(questions, all_answers)
    except ValueError as exc:
        print(f"答案选项校验失败，尚未开始点击: {exc}")
        return HomeworkRunResult(ok=False, reason="invalid_answers", question_count=len(questions))

    print(f"已生成 {len(all_answers)} 个答案，开始点击")
    question_ids = [str(question["id"]) for question in questions]
    click_answers_fn(driver, question_ids, all_answers)
    return HomeworkRunResult(ok=True, reason="answered", question_count=len(questions))


def go_to_next_question_page(driver, questions: list[dict[str, object]], timeout: int = 15) -> bool:
    next_button = _find_next_question_button(driver)
    if next_button is None:
        return False

    old_signature = _question_page_signature(questions)
    old_url = _safe_current_url(driver)
    try:
        next_button.click()
    except WebDriverException:
        try:
            driver.execute_script("arguments[0].click();", next_button)
        except (AttributeError, WebDriverException):
            return False

    return _wait_for_question_page_change(driver, old_signature, old_url, timeout)


def _find_next_question_button(driver):
    selectors = [
        (By.XPATH, "//a[contains(normalize-space(.), '下一题')]"),
        (By.XPATH, "//button[contains(normalize-space(.), '下一题')]"),
        (By.XPATH, "//a[contains(normalize-space(.), '下一页')]"),
        (By.XPATH, "//button[contains(normalize-space(.), '下一页')]"),
    ]
    for by, selector in selectors:
        try:
            elements = driver.find_elements(by, selector)
        except (AttributeError, WebDriverException):
            continue
        for element in elements:
            if _is_enabled_next_button(element):
                return element
    return None


def _is_enabled_next_button(element) -> bool:
    try:
        if hasattr(element, "is_displayed") and not element.is_displayed():
            return False
    except WebDriverException:
        return False

    class_name = _safe_element_attr(element, "class").lower()
    disabled = _safe_element_attr(element, "disabled").lower()
    aria_disabled = _safe_element_attr(element, "aria-disabled").lower()
    if "disable" in class_name or "disabled" in class_name:
        return False
    if disabled in {"true", "disabled", "1"} or aria_disabled == "true":
        return False
    return True


def _wait_for_question_page_change(
    driver,
    old_signature: tuple[str, ...],
    old_url: str,
    timeout: int,
) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            lambda target_driver: (
                _safe_current_url(target_driver) != old_url
                or _current_dom_question_signature(target_driver) != old_signature
            )
        )
        return True
    except TimeoutException:
        return False


def _current_dom_question_signature(driver) -> tuple[str, ...]:
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "div.questionLi")
    except (StaleElementReferenceException, WebDriverException):
        return ()

    signature = []
    for element in elements:
        try:
            identity = (
                element.get_attribute("id")
                or element.get_attribute("data")
                or element.text
                or ""
            )
        except (StaleElementReferenceException, WebDriverException):
            return ()
        signature.append(identity.strip())
    return tuple(signature)


def _question_page_signature(questions: list[dict[str, object]]) -> tuple[str, ...]:
    return tuple(
        str(question.get("id") or question.get("text") or index)
        for index, question in enumerate(questions, 1)
    )


def _safe_current_url(driver) -> str:
    try:
        return driver.current_url or ""
    except (AttributeError, WebDriverException):
        return ""


def _safe_element_attr(element, name: str) -> str:
    try:
        return element.get_attribute(name) or ""
    except WebDriverException:
        return ""
