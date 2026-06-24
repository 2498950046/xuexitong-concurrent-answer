from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping, Sequence
from typing import TypeVar


T = TypeVar("T")


def batch_items(items: Sequence[T], batch_size: int = 20) -> Iterator[list[T]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")
    for index in range(0, len(items), batch_size):
        yield list(items[index : index + batch_size])


def parse_answer_array(raw_answer: str) -> list[str]:
    if not raw_answer or not raw_answer.strip():
        raise ValueError("answer content is empty")

    json_text = _extract_first_json_array(raw_answer)
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("answer content is not a valid JSON array") from exc

    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("answer array must contain only strings")

    return [item.strip().upper() for item in parsed]


def validate_answer_count(answers: Sequence[str], expected_count: int) -> None:
    if len(answers) != expected_count:
        raise ValueError(f"answer count {len(answers)} does not match question count {expected_count}")


def validate_answer_choices(
    questions: Sequence[Mapping[str, object]],
    answers: Sequence[str],
) -> None:
    validate_answer_count(answers, len(questions))

    for index, (question, answer) in enumerate(zip(questions, answers), 1):
        allowed_options = _question_option_letters(question)
        if not allowed_options:
            continue

        invalid_options = [
            token
            for token in _answer_tokens(answer, allowed_options)
            if token not in allowed_options
        ]
        if invalid_options:
            allowed_text = ", ".join(sorted(allowed_options))
            invalid_text = ", ".join(invalid_options)
            raise ValueError(
                f"question {index} answer contains invalid option(s): {invalid_text}; "
                f"allowed options: {allowed_text}; raw answer: {answer}"
            )


def normalize_answers_for_questions(
    questions: Sequence[Mapping[str, object]],
    answers: Sequence[str],
) -> list[str]:
    validate_answer_count(answers, len(questions))
    return [
        normalize_answer_for_question(question, answer)
        for question, answer in zip(questions, answers)
    ]


def normalize_answer_for_question(question: Mapping[str, object], answer: str) -> str:
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("answer must be a non-empty string")

    normalized = answer.strip().upper()
    options = _question_options(question)
    allowed_options = {letter for letter, _text in options}
    if normalized in allowed_options:
        return normalized

    if normalized in {"A", "B"}:
        mapped = _judgement_letter_alias_to_value(normalized, options)
        if mapped:
            return mapped

    if normalized in {"TRUE", "FALSE"}:
        mapped = _judgement_answer_to_option(normalized, options)
        if mapped:
            return mapped

    return normalized


def extend_validated_answers(target: list[str], raw_answer: str, expected_count: int) -> None:
    answers = parse_answer_array(raw_answer)
    validate_answer_count(answers, expected_count)
    target.extend(answers)


def _answer_tokens(answer: str, allowed_options: set[str]) -> list[str]:
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("answer must be a non-empty string")

    normalized = answer.strip().upper()
    if normalized in allowed_options:
        return [normalized]
    return list(normalized)


def _question_option_letters(question: Mapping[str, object]) -> set[str]:
    return {letter for letter, _text in _question_options(question)}


def _question_options(question: Mapping[str, object]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    options = question.get("options") or []
    for option in options:
        if not isinstance(option, Mapping):
            continue
        letter = str(option.get("letter", "")).strip().upper()
        text = str(option.get("text", "")).strip().upper()
        if letter:
            result.append((letter, text))
    return result


def _judgement_answer_to_option(answer: str, options: Sequence[tuple[str, str]]) -> str | None:
    true_words = {"对", "正确", "TRUE", "T", "YES"}
    false_words = {"错", "错误", "FALSE", "F", "NO"}
    expected_words = true_words if answer == "TRUE" else false_words

    for letter, text in options:
        if text in expected_words:
            return letter

    letters = [letter for letter, _text in options]
    if letters[:2] == ["A", "B"]:
        return "A" if answer == "TRUE" else "B"
    return None


def _judgement_letter_alias_to_value(answer: str, options: Sequence[tuple[str, str]]) -> str | None:
    letters = {letter for letter, _text in options}
    if {"TRUE", "FALSE"}.issubset(letters):
        return "TRUE" if answer == "A" else "FALSE"
    return None


def _extract_first_json_array(text: str) -> str:
    cleaned = _strip_code_fences(text.strip())
    if cleaned.startswith("[") and cleaned.endswith("]"):
        return cleaned

    match = re.search(r"\[[\s\S]*\]", cleaned)
    if not match:
        raise ValueError("answer content does not contain a JSON array")
    return match.group(0)


def _strip_code_fences(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else text
