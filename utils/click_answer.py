from __future__ import annotations

import time
from collections.abc import Sequence

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def auto_select_answers(
    driver,
    question_ids: Sequence[str],
    answers: Sequence[str],
    timeout: int = 10,
    delay_seconds: float = 0.5,
    screenshot_path: str = "error.png",
) -> None:
    if len(question_ids) != len(answers):
        raise ValueError(
            f"question count {len(question_ids)} does not match answer count {len(answers)}"
        )

    try:
        for index, (question_id, answer) in enumerate(zip(question_ids, answers), 1):
            if not question_id:
                raise ValueError(f"question id at position {index} is empty")

            question_div = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, question_id))
            )
            available_options = _available_option_values(question_div)

            for option_value in answer_option_tokens(answer, available_options):
                _click_option(question_div, option_value)
                print(f"第{index}题点击答案: {option_value}")

            time.sleep(delay_seconds)
    except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
        _save_screenshot(driver, screenshot_path)
        raise RuntimeError(f"选择答案失败，已保存截图到 {screenshot_path}: {exc}") from exc


def answer_option_tokens(answer: str, available_options: set[str]) -> list[str]:
    normalized_answer = _normalize_answer(answer)
    normalized_options = {option.upper() for option in available_options if option}

    if normalized_answer in normalized_options:
        return [normalized_answer]

    if normalized_answer == "TRUE" and {"A", "B"}.issubset(normalized_options):
        return ["A"]
    if normalized_answer == "FALSE" and {"A", "B"}.issubset(normalized_options):
        return ["B"]

    tokens = list(normalized_answer)
    invalid_tokens = [token for token in tokens if token not in normalized_options]
    if invalid_tokens:
        allowed_text = ", ".join(sorted(normalized_options))
        invalid_text = ", ".join(invalid_tokens)
        raise ValueError(
            f"answer contains unavailable option(s): {invalid_text}; allowed options: {allowed_text}"
        )
    return tokens


def _normalize_answer(answer: str) -> str:
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("answer must be a non-empty string")
    return answer.strip().upper()


def _available_option_values(question_div) -> set[str]:
    values = set()
    for option in question_div.find_elements(By.CSS_SELECTOR, "span[data]"):
        value = (option.get_attribute("data") or "").strip().upper()
        if value:
            values.add(value)
    if not values:
        raise NoSuchElementException("no selectable options found")
    return values


def _click_option(question_div, option_value: str) -> None:
    target_option = _find_option_by_data(question_div, option_value)
    if target_option is None:
        raise NoSuchElementException(f"option {option_value} not found")

    answer_div = target_option.find_element(
        By.XPATH,
        "./ancestor::div[contains(@class, 'answerBg')]",
    )
    if "active" not in (answer_div.get_attribute("class") or ""):
        answer_div.click()


def _find_option_by_data(question_div, option_value: str):
    normalized = option_value.upper()
    for option in question_div.find_elements(By.CSS_SELECTOR, "span[data]"):
        if (option.get_attribute("data") or "").strip().upper() == normalized:
            return option
    return None


def _save_screenshot(driver, screenshot_path: str) -> None:
    try:
        driver.save_screenshot(screenshot_path)
    except WebDriverException:
        pass
