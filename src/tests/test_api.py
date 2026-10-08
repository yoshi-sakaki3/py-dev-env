from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import ai
from app.main import app

client = TestClient(app)


def test_health() -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_summarize_without_key(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    res = client.post("/api/summarize", json={"text": "テスト"})
    assert res.status_code == 503


def test_summarize_with_fake_client(monkeypatch) -> None:
    """実際には API を呼ばず、偽のクライアントで応答の組み立てだけ確かめる"""
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="・要点1\n・要点2")],
            )

    fake = SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages()))
    assert ai.summarize("長い文章", client=fake) == "・要点1\n・要点2"
    assert captured["model"] == "claude-opus-5-5"
    assert captured["messages"][0]["content"] == "長い文章"


def test_summarize_refusal(monkeypatch) -> None:
    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(stop_reason="refusal", content=[])

    fake = SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages()))
    try:
        ai.summarize("文章", client=fake)
    except ai.SummaryRefusedError:
        pass
    else:
        raise AssertionError("refusal のときは SummaryRefusedError になるはず")
