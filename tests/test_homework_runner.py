from dataclasses import dataclass

from utils.config import AppConfig
from utils.homework_runner import HomeworkRunResult, answer_homework


class FakeDriver:
    def __init__(self):
        self.opened_url = None

    def get(self, url):
        self.opened_url = url


@dataclass
class Calls:
    clicked: bool = False


def test_answer_homework_returns_no_questions_when_page_has_none():
    driver = FakeDriver()

    result = answer_homework(
        driver,
        "https://example.test/work",
        AppConfig(deepseek_api_key="sk-test"),
        get_questions_fn=lambda _driver: [],
        get_answer_fn=lambda _prompt, config: '["A"]',
        click_answers_fn=lambda _driver, _ids, _answers: None,
    )

    assert result == HomeworkRunResult(ok=False, reason="no_questions", question_count=0)
    assert driver.opened_url == "https://example.test/work"


def test_answer_homework_clicks_valid_answers():
    driver = FakeDriver()
    calls = Calls()
    questions = [
        {"id": "q1", "type": "单选题", "text": "one", "options": [{"letter": "A", "text": "Alpha"}]},
        {"id": "q2", "type": "判断题", "text": "two", "options": [{"letter": "A", "text": "对"}, {"letter": "B", "text": "错"}]},
    ]

    def click_answers(_driver, question_ids, answers):
        calls.clicked = True
        assert question_ids == ["q1", "q2"]
        assert answers == ["A", "A"]

    result = answer_homework(
        driver,
        "https://example.test/work",
        AppConfig(deepseek_api_key="sk-test"),
        get_questions_fn=lambda _driver: questions,
        get_answer_fn=lambda _prompt, config: '["A", "TRUE"]',
        click_answers_fn=click_answers,
    )

    assert result == HomeworkRunResult(ok=True, reason="answered", question_count=2)
    assert calls.clicked


def test_answer_homework_does_not_print_prompt_or_question_text(capsys):
    driver = FakeDriver()
    questions = [
        {
            "id": "q1",
            "type": "单选题",
            "text": "terminal should not show this question",
            "options": [{"letter": "A", "text": "Alpha"}],
        },
    ]

    def get_answer(prompt, config):
        assert "terminal should not show this question" in prompt
        return '["A"]'

    result = answer_homework(
        driver,
        "https://example.test/work",
        AppConfig(deepseek_api_key="sk-test"),
        get_questions_fn=lambda _driver: questions,
        get_answer_fn=get_answer,
        click_answers_fn=lambda _driver, _ids, _answers: None,
    )

    output = capsys.readouterr().out
    assert result.ok
    assert "terminal should not show this question" not in output
    assert "Answer the following" not in output
    assert "所有答案" not in output


def test_answer_homework_stops_on_invalid_ai_answer():
    driver = FakeDriver()
    questions = [
        {"id": "q1", "type": "单选题", "text": "one", "options": [{"letter": "A", "text": "Alpha"}]},
    ]

    result = answer_homework(
        driver,
        "https://example.test/work",
        AppConfig(deepseek_api_key="sk-test"),
        get_questions_fn=lambda _driver: questions,
        get_answer_fn=lambda _prompt, config: '["Z"]',
        click_answers_fn=lambda _driver, _ids, _answers: (_ for _ in ()).throw(AssertionError("should not click")),
    )

    assert not result.ok
    assert result.reason == "invalid_answers"
