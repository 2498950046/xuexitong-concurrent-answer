from dataclasses import dataclass

from selenium.webdriver.common.by import By

from utils.config import AppConfig
from utils.homework_runner import HomeworkRunResult, answer_homework, go_to_next_question_page


class FakeDriver:
    def __init__(self):
        self.opened_url = None

    def get(self, url):
        self.opened_url = url


@dataclass
class Calls:
    clicked: bool = False


class FakeNextButton:
    text = "下一题"

    def __init__(self):
        self.clicked = False
        self.attrs = {}

    def get_attribute(self, name):
        return self.attrs.get(name)

    def is_displayed(self):
        return True

    def click(self):
        self.clicked = True


class FakeNextDriver:
    def __init__(self):
        self.current_url = "https://example.test/exam?start=0"
        self.next_button = FakeNextButton()

    def find_elements(self, by, selector):
        if by == By.XPATH and "下一题" in selector:
            return [self.next_button]
        if by == By.CSS_SELECTOR and selector == "div.questionLi":
            return []
        return []


def test_go_to_next_question_page_clicks_next_question_button(monkeypatch):
    driver = FakeNextDriver()

    monkeypatch.setattr(
        "utils.homework_runner._wait_for_question_page_change",
        lambda *_args: True,
    )

    assert go_to_next_question_page(driver, [{"id": "question1"}]) is True
    assert driver.next_button.clicked is True


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


def test_answer_homework_clicks_question_with_generated_exam_page_id():
    driver = FakeDriver()
    calls = Calls()
    questions = [
        {
            "id": "question886711088",
            "type": "单选题",
            "text": "exam style question",
            "options": [{"letter": "A", "text": "Alpha"}, {"letter": "B", "text": "Beta"}],
        }
    ]

    def click_answers(_driver, question_ids, answers):
        calls.clicked = True
        assert question_ids == ["question886711088"]
        assert answers == ["A"]

    result = answer_homework(
        driver,
        "https://example.test/exam",
        AppConfig(deepseek_api_key="sk-test"),
        get_questions_fn=lambda _driver: questions,
        get_answer_fn=lambda _prompt, config: '["A"]',
        click_answers_fn=click_answers,
    )

    assert result == HomeworkRunResult(ok=True, reason="answered", question_count=1)
    assert calls.clicked


def test_answer_homework_continues_through_single_question_pages():
    driver = FakeDriver()
    pages = [
        [{"id": "question1", "type": "单选题", "text": "one", "options": [{"letter": "A", "text": "Alpha"}]}],
        [{"id": "question2", "type": "单选题", "text": "two", "options": [{"letter": "B", "text": "Beta"}]}],
        [{"id": "question3", "type": "单选题", "text": "three", "options": [{"letter": "C", "text": "Gamma"}]}],
    ]
    current_page = {"index": 0}
    clicked = []

    def get_questions(_driver):
        return pages[current_page["index"]]

    def get_answer(prompt, _config):
        if "one" in prompt:
            return '["A"]'
        if "two" in prompt:
            return '["B"]'
        return '["C"]'

    def click_answers(_driver, question_ids, answers):
        clicked.append((question_ids, answers))

    def navigate_next(_driver, _questions):
        if current_page["index"] >= len(pages) - 1:
            return False
        current_page["index"] += 1
        return True

    result = answer_homework(
        driver,
        "https://example.test/exam",
        AppConfig(deepseek_api_key="sk-test"),
        get_questions_fn=get_questions,
        get_answer_fn=get_answer,
        click_answers_fn=click_answers,
        navigate_next_fn=navigate_next,
    )

    assert result == HomeworkRunResult(ok=True, reason="answered", question_count=3)
    assert clicked == [
        (["question1"], ["A"]),
        (["question2"], ["B"]),
        (["question3"], ["C"]),
    ]


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
