from __future__ import annotations

from openai import OpenAI

from utils.config import AppConfig


def get_deepseek_answer(
    user_input: str,
    config: AppConfig | None = None,
    client: OpenAI | None = None,
) -> str | None:
    if not user_input or not user_input.strip():
        raise ValueError("user_input is required")

    config = config or AppConfig.from_env()
    api_key = config.require_deepseek_api_key()
    client = client or OpenAI(api_key=api_key, base_url=config.deepseek_base_url)
    response = None

    try:
        response = client.chat.completions.create(
            model=config.deepseek_model,
            messages=[{"role": "user", "content": user_input}],
            stream=True,
            timeout=30,
        )

        final_answer = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                delta_content = chunk.choices[0].delta.content
                final_answer += delta_content

        return final_answer.strip()
    except Exception as exc:
        print(f"\n请求失败: {exc}")
        return None
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
