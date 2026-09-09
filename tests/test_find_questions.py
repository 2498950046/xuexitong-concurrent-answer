import pytest
from selenium.common.exceptions import WebDriverException

from utils.find_questions import _ensure_question_id


class FakeQuestionElement:
    def __init__(self, element_id=""):
        self.attrs = {"id": element_id}

    def get_attribute(self, name):
        return self.attrs.get(name)

    def set_id(self, value):
        self.attrs["id"] = value


class FakeDriver:
    def __init__(self, assigned_id="xuexitong-question-1"):
        self.assigned_id = assigned_id
        self.script_calls = []

    def execute_script(self, script, element, generated_id):
        self.script_calls.append((script, element, generated_id))
        element.set_id(self.assigned_id)
        return self.assigned_id


def test_ensure_question_id_keeps_existing_page_id():
    driver = FakeDriver()
    question = FakeQuestionElement("question214733056")

    assert _ensure_question_id(driver, question, 1) == "question214733056"
    assert driver.script_calls == []


def test_ensure_question_id_assigns_generated_id_when_page_id_is_empty():
    driver = FakeDriver("xuexitong-question-1")
    question = FakeQuestionElement("")

    assert _ensure_question_id(driver, question, 1) == "xuexitong-question-1"
    assert question.get_attribute("id") == "xuexitong-question-1"
    assert driver.script_calls[0][2] == "xuexitong-question-1"


def test_ensure_question_id_raises_when_empty_id_cannot_be_assigned():
    class FailingDriver:
        def execute_script(self, *_args):
            raise WebDriverException("script failed")

    with pytest.raises(WebDriverException, match="Unable to assign generated question id"):
        _ensure_question_id(FailingDriver(), FakeQuestionElement(""), 1)


def test_ensure_question_id_uses_question_data_attribute_when_available():
    driver = FakeDriver("question886711088")
    question = FakeQuestionElement("")
    question.attrs["data"] = "886711088"

    assert _ensure_question_id(driver, question, 1) == "question886711088"
    assert driver.script_calls[0][2] == "question886711088"
