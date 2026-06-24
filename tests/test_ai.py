from utils.ai import get_deepseek_answer
from utils.config import AppConfig


class FakeDelta:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.delta = FakeDelta(content)


class FakeChunk:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeResponse:
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def __iter__(self):
        return iter(self.chunks)

    def close(self):
        self.closed = True


class FakeCompletions:
    def __init__(self, response):
        self.response = response

    def create(self, **_kwargs):
        return self.response


class FakeChat:
    def __init__(self, response):
        self.completions = FakeCompletions(response)


class FakeClient:
    def __init__(self, response):
        self.chat = FakeChat(response)


def test_get_deepseek_answer_collects_stream_without_printing(capsys):
    response = FakeResponse([FakeChunk('["A"'), FakeChunk(',"B"]')])
    client = FakeClient(response)

    answer = get_deepseek_answer(
        "question prompt",
        AppConfig(deepseek_api_key="sk-test"),
        client=client,
    )

    assert answer == '["A","B"]'
    assert capsys.readouterr().out == ""
    assert response.closed
