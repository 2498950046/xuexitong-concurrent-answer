from utils.course import extract_course_url, xpath_literal


def test_extract_course_url_from_switch_script():
    href = "javascript:switchM(1,'https://mooc1-1.chaoxing.com/visit/interaction?s=abc')"

    assert extract_course_url(href) == "https://mooc1-1.chaoxing.com/visit/interaction?s=abc"


def test_extract_course_url_returns_none_for_invalid_href():
    assert extract_course_url("javascript:void(0)") is None


def test_xpath_literal_handles_single_and_double_quotes():
    value = 'A "quoted" course with \'single\''

    assert xpath_literal(value) == """concat('A "quoted" course with ', "'", 'single', "'")"""
