import json

import httpx
import pytest

from second_brain.config import Settings
from second_brain.muse import Muse, MuseFailure

VALID = {"reply": "Review", "importance_score": 70, "subtasks": []}


def configure(monkeypatch, handler):
    original_client = httpx.Client
    monkeypatch.setattr(
        "second_brain.muse.httpx.Client",
        lambda **kw: original_client(
            transport=httpx.MockTransport(handler),
            **kw,
        ),
    )
    return Muse(Settings(_env_file=None, meta_api_key="test-secret", vercel=None))


def test_meta_request_contract(monkeypatch):
    def handler(request):
        assert str(request.url) == "https://api.meta.ai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-secret"
        body = json.loads(request.content)
        assert body["model"] == "muse-spark-1.3"
        assert body["response_format"]["type"] == "json_schema"
        assert body["store"] is False
        assert json.loads(body["messages"][1]["content"])["state"] == {
            "task": {"title": "Homework"}
        }
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(VALID)}}
                ]
            },
        )

    muse = configure(monkeypatch, handler)
    assert muse.plan({"task": {"title": "Homework"}}, "plan").importance_score == 70


@pytest.mark.parametrize(
    "case",
    [
        "401",
        "429",
        "500",
        "redirect",
        "malformed",
        "truncated",
        "invalid_schema",
        "timeout",
    ],
)
def test_meta_failure_is_safe(monkeypatch, case):
    def handler(request):
        if case == "timeout":
            raise httpx.ReadTimeout("test-secret provider details", request=request)
        if case.isdigit():
            return httpx.Response(int(case), text="test-secret provider details")
        if case == "redirect":
            return httpx.Response(302, headers={"Location": "https://other.example/"})
        if case == "malformed":
            return httpx.Response(200, text="not JSON test-secret")
        proposal = VALID if case == "truncated" else {**VALID, "importance_score": True}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "length" if case == "truncated" else "stop",
                        "message": {"content": json.dumps(proposal)},
                    }
                ]
            },
        )

    with pytest.raises(MuseFailure) as error:
        configure(monkeypatch, handler).plan({}, "plan")
    assert "test-secret" not in str(error.value)


def test_no_key_no_network(monkeypatch):
    monkeypatch.delenv("META_API_KEY", raising=False)
    with pytest.raises(MuseFailure):
        Muse(Settings(_env_file=None, meta_api_key=None)).plan({}, "plan")


def test_hosted_demo_requires_persistence_and_token():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            vercel="1",
            database_url="sqlite:///./test.db",
            mock_auth_token="token",
        ).validate_hosted()
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            vercel="1",
            database_url="postgresql://unused/db",
            mock_auth_token=None,
        ).validate_hosted()
    Settings(
        _env_file=None,
        vercel="1",
        database_url="postgresql://unused/db",
        mock_auth_token="token",
    ).validate_hosted()


def test_blank_env_uses_defaults(tmp_path):
    env = tmp_path / ".env"
    env.write_text("META_BASE_URL=\nMETA_MODEL=\nDATABASE_URL=\n")
    settings = Settings(_env_file=env)
    assert settings.meta_model == "muse-spark-1.3"
    assert settings.meta_base_url == "https://api.meta.ai/v1"
    assert settings.database_url.startswith("sqlite:")
