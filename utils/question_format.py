from __future__ import annotations

from collections.abc import Mapping


def format_question(question: Mapping[str, object]) -> str:
    options = question.get("options") or []
    option_lines = []
    for option in options:
        if not isinstance(option, Mapping):
            continue
        letter = str(option.get("letter", "")).strip()
        text = str(option.get("text", "")).strip()
        option_lines.append(f"{letter}. {text}")

    return (
        f"题目{question.get('id')} ({question.get('type')}):\n"
        f"{str(question.get('text', '')).strip()}\n"
        "选项:\n"
        + "\n".join(option_lines)
    )
