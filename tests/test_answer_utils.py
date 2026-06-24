import pytest

from utils.answers import (
    batch_items,
    normalize_answers_for_questions,
    parse_answer_array,
    validate_answer_choices,
    validate_answer_count,
)
from utils.question_format import format_question


def test_format_question_renders_options():
    question = {
        "id": "q1",
        "type": "single",
        "text": "Pick one",
        "options": [
            {"letter": "A", "text": "Alpha"},
            {"letter": "B", "text": "Beta"},
        ],
    }

    assert format_question(question) == (
        "题目q1 (single):\n"
        "Pick one\n"
        "选项:\n"
        "A. Alpha\n"
        "B. Beta"
    )


def test_batch_items_splits_without_dropping_remainder():
    assert list(batch_items([1, 2, 3, 4, 5], batch_size=2)) == [[1, 2], [3, 4], [5]]


def test_batch_items_rejects_invalid_size():
    with pytest.raises(ValueError, match="batch_size"):
        list(batch_items([1], batch_size=0))


def test_parse_answer_array_accepts_plain_json_array():
    assert parse_answer_array('["A", "BC"]') == ["A", "BC"]


def test_parse_answer_array_accepts_json_array_inside_text():
    raw = '答案如下：\n```json\n["A", "BC", "D"]\n```'

    assert parse_answer_array(raw) == ["A", "BC", "D"]


def test_parse_answer_array_rejects_non_string_items():
    with pytest.raises(ValueError, match="strings"):
        parse_answer_array('["A", 2]')


def test_validate_answer_count_rejects_mismatch():
    with pytest.raises(ValueError, match="answer count"):
        validate_answer_count(["A"], expected_count=2)


def test_validate_answer_choices_accepts_letters_in_question_options():
    questions = [
        {"id": "q1", "options": [{"letter": "A"}, {"letter": "B"}]},
        {"id": "q2", "options": [{"letter": "A"}, {"letter": "B"}, {"letter": "C"}]},
    ]

    validate_answer_choices(questions, ["A", "BC"])


def test_validate_answer_choices_accepts_true_false_option_values():
    questions = [
        {"id": "q1", "options": [{"letter": "TRUE"}, {"letter": "FALSE"}]},
        {"id": "q2", "options": [{"letter": "TRUE"}, {"letter": "FALSE"}]},
    ]

    validate_answer_choices(questions, ["TRUE", "FALSE"])


def test_normalize_answers_maps_true_false_to_judgement_letters():
    questions = [
        {
            "id": "q1",
            "type": "判断题",
            "options": [{"letter": "A", "text": "对"}, {"letter": "B", "text": "错"}],
        },
        {
            "id": "q2",
            "type": "判断题",
            "options": [{"letter": "A", "text": "对"}, {"letter": "B", "text": "错"}],
        },
    ]

    assert normalize_answers_for_questions(questions, ["TRUE", "FALSE"]) == ["A", "B"]


def test_normalize_answers_keeps_true_false_when_they_are_real_option_values():
    questions = [
        {"id": "q1", "options": [{"letter": "TRUE", "text": "对"}, {"letter": "FALSE", "text": "错"}]},
    ]

    assert normalize_answers_for_questions(questions, ["TRUE"]) == ["TRUE"]


def test_normalize_answers_accepts_ab_for_true_false_option_values():
    questions = [
        {"id": "q1", "type": "判断题", "options": [{"letter": "TRUE", "text": "对"}, {"letter": "FALSE", "text": "错"}]},
        {"id": "q2", "type": "判断题", "options": [{"letter": "TRUE", "text": "对"}, {"letter": "FALSE", "text": "错"}]},
    ]

    normalized = normalize_answers_for_questions(questions, ["A", "B"])

    assert normalized == ["TRUE", "FALSE"]
    validate_answer_choices(questions, normalized)


def test_validate_answer_choices_rejects_invalid_letter_before_clicking():
    questions = [
        {"id": "q1", "options": [{"letter": "A"}, {"letter": "B"}]},
        {"id": "q2", "options": [{"letter": "A"}, {"letter": "B"}, {"letter": "C"}]},
    ]

    with pytest.raises(ValueError, match="question 2.*T.*allowed options: A, B, C"):
        validate_answer_choices(questions, ["A", "ABCT"])
