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

        for question in question_elements:
            question_id = question.get_attribute("id")
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
