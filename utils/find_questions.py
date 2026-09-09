from __future__ import annotations

import re

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_questions(driver, timeout: int = 20) -> list[dict[str, object]]:
    questions: list[dict[str, object]] = []

    try:
        question_elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.questionLi"))
        )

        for index, question in enumerate(question_elements, 1):
            question_id = _ensure_question_id(driver, question, index)
            question_type = question.get_attribute("typename")
            question_text = _clean_question_text(question.find_element(By.TAG_NAME, "h3").text)

            options = []
            option_elements = WebDriverWait(question, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.stem_answer div.answerBg")
                )
            )

            for index, option in enumerate(option_elements):
                options.append(
                    {
                        "letter": _extract_option_letter(option, index),
                        "text": _extract_option_text(option),
                    }
                )

            questions.append(
                {
                    "id": question_id,
                    "type": question_type,
                    "text": question_text,
                    "options": options,
                }
            )

        print(f"成功获取 {len(questions)} 道题目")
        return questions
    except TimeoutException:
        print("获取题目超时")
        return []
    except WebDriverException as exc:
        print(f"获取题目失败: {exc}")
        return []


def _clean_question_text(text: str) -> str:
    cleaned = re.sub(r"^\s*\d+[.、]?\s*", "", text or "")
    return cleaned.strip()


def _ensure_question_id(driver, question, index: int) -> str:
    question_id = (question.get_attribute("id") or "").strip()
    if question_id:
        return question_id

    generated_id = _generated_question_id(question, index)
    try:
        assigned_id = driver.execute_script(
            "arguments[0].setAttribute('id', arguments[1]); return arguments[0].id;",
            question,
            generated_id,
        )
    except WebDriverException as exc:
        raise WebDriverException(
            f"Unable to assign generated question id at position {index}: {exc}"
        ) from exc

    assigned_id = (assigned_id or "").strip()
    if not assigned_id:
        raise WebDriverException(f"Unable to assign generated question id at position {index}")
    return assigned_id


def _generated_question_id(question, index: int) -> str:
    question_key = _question_key(question)
    if question_key:
        return f"question{question_key}"
    return f"xuexitong-question-{index}"


def _question_key(question) -> str | None:
    for attr_name in ("data", "qid", "questionid", "questionId"):
        value = (question.get_attribute(attr_name) or "").strip()
        if value:
            return _safe_id_part(value)

    try:
        option = question.find_element(By.CSS_SELECTOR, "span[qid]")
        value = (option.get_attribute("qid") or "").strip()
        if value:
            return _safe_id_part(value)
    except (AttributeError, NoSuchElementException):
        return None

    return None


def _safe_id_part(value: str) -> str:
    safe_value = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip())
    return safe_value.strip("-") or "generated"


def _extract_option_letter(option, index: int) -> str:
    selectors = ("span.num_option", "span.num_option_dx")
    for selector in selectors:
        try:
            letter = option.find_element(By.CSS_SELECTOR, selector).get_attribute("data")
            if letter:
                return letter.strip().upper()
        except NoSuchElementException:
            continue
    return chr(65 + index)


def _extract_option_text(option) -> str:
    try:
        return option.find_element(By.CSS_SELECTOR, "div.answer_p").get_attribute("textContent").strip()
    except NoSuchElementException:
        return ""
