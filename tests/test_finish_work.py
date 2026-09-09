from dataclasses import replace

import pytest

from finish_work import resolve_work_url
from utils.config import AppConfig


def test_resolve_work_url_prefers_terminal_input():
    config = AppConfig(work_url="https://example.test/from-env")

    result = resolve_work_url(config, input_fn=lambda _prompt: " https://example.test/from-terminal ")

    assert result == "https://example.test/from-terminal"


def test_resolve_work_url_uses_env_when_terminal_input_is_empty():
    config = AppConfig(work_url="https://example.test/from-env")

    result = resolve_work_url(config, input_fn=lambda _prompt: "   ")

    assert result == "https://example.test/from-env"


def test_resolve_work_url_requires_one_source():
    config = replace(AppConfig(), work_url=None)

    with pytest.raises(ValueError, match="no URL was entered"):
        resolve_work_url(config, input_fn=lambda _prompt: "")
