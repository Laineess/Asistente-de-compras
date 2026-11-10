from app.llm import build_llm, content_to_text, invoke_json, invoke_text, parse_json


class FakeResponse:
    def __init__(self, content) -> None:
        self.content = content


class FakeLLM:
    def __init__(self, content=None, error: Exception | None = None) -> None:
        self.content = content
        self.error = error

    def invoke(self, prompt: str) -> FakeResponse:
        if self.error is not None:
            raise self.error
        return FakeResponse(self.content)


def test_content_to_text_handles_strings_lists_and_other_values() -> None:
    assert content_to_text("hola") == "hola"
    assert content_to_text(["uno", {"text": "dos"}, 3]) == "uno\ndos"
    assert content_to_text(42) == "42"


def test_parse_json_handles_plain_fenced_and_embedded_json() -> None:
    assert parse_json('{"score": 8.5}') == {"score": 8.5}
    assert parse_json('```json\n{"score": 8.5}\n```') == {"score": 8.5}
    assert parse_json('Respuesta: {"score": 8.5} fin') == {"score": 8.5}
    assert parse_json("[1, 2, 3]") is None
    assert parse_json("sin json") is None


def test_invoke_text_and_json_without_llm() -> None:
    assert invoke_text(None, "prompt") is None
    assert invoke_json(None, "prompt") is None


def test_invoke_text_strips_content_and_handles_errors() -> None:
    assert invoke_text(FakeLLM("  respuesta  "), "prompt") == "respuesta"
    assert invoke_text(FakeLLM("   "), "prompt") is None
    assert invoke_text(FakeLLM(error=RuntimeError("fallo")), "prompt") is None


def test_invoke_json_parses_fenced_response() -> None:
    llm = FakeLLM('```json\n{"score": 9}\n```')

    assert invoke_json(llm, "prompt") == {"score": 9}
    assert invoke_json(FakeLLM("no json"), "prompt") is None


def test_build_llm_without_key_returns_none(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.settings.gemini_api_key", "")

    assert build_llm() is None


def test_build_llm_uses_configured_model_and_key(monkeypatch) -> None:
    captured = {}

    class FakeChatModel:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("app.llm.settings.gemini_api_key", "clave")
    monkeypatch.setattr("app.llm.settings.gemini_model", "modelo-prueba")
    monkeypatch.setattr("app.llm.settings.gemini_timeout_seconds", 12.5)
    monkeypatch.setattr("app.llm.settings.gemini_retries", 2)
    monkeypatch.setattr("app.llm.ChatGoogleGenerativeAI", FakeChatModel)

    model = build_llm()

    assert isinstance(model, FakeChatModel)
    assert captured["model"] == "modelo-prueba"
    assert captured["google_api_key"] == "clave"
    assert captured["request_timeout"] == 12.5
    assert captured["retries"] == 2
    assert captured["model_kwargs"] == {"transport": "rest"}
