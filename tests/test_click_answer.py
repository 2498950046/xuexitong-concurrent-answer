import pytest

from utils.click_answer import answer_option_tokens


def test_answer_option_tokens_keeps_true_as_single_option():
    assert answer_option_tokens("TRUE", {"TRUE", "FALSE"}) == ["TRUE"]


def test_answer_option_tokens_keeps_false_as_single_option():
    assert answer_option_tokens("FALSE", {"TRUE", "FALSE"}) == ["FALSE"]


def test_answer_option_tokens_maps_true_to_a_when_page_uses_judgement_letters():
    assert answer_option_tokens("TRUE", {"A", "B"}) == ["A"]


def test_answer_option_tokens_maps_false_to_b_when_page_uses_judgement_letters():
    assert answer_option_tokens("FALSE", {"A", "B"}) == ["B"]


def test_answer_option_tokens_splits_multiple_choice_letters():
    assert answer_option_tokens("BCD", {"A", "B", "C", "D"}) == ["B", "C", "D"]


def test_answer_option_tokens_rejects_unavailable_token():
    with pytest.raises(ValueError, match="T"):
        answer_option_tokens("TRUE", {"A", "C", "D"})
