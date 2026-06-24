from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
) -> HomeworkRunResult:
    driver.get(url)
    questions = get_questions_fn(driver)
    if not questions:
        print("未获取到题目，停止当前作业")
        return HomeworkRunResult(ok=False, reason="no_questions", question_count=0)

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
