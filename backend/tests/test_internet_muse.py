import json

import httpx
import pytest

from second_brain.config import Settings
from second_brain.muse import Muse, MuseFailure


def model(monkeypatch, payload, status=200):
    requests = []

    def post(self, url, **kwargs):
        requests.append((url, kwargs))
        return httpx.Response(status, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.Client, "post", post)
    return Muse(Settings(_env_file=None, meta_api_key="fake-key")), requests


def message(text, annotations=None):
    return {
        "type": "message",
        "content": [
            {"type": "output_text", "text": text, "annotations": annotations or []}
        ],
    }


def test_native_search_progress_and_sources_are_not_confused_with_final_json(
    monkeypatch,
):
    data = {
        "status": "completed",
        "output": [
            message("I will search."),
            {"type": "web_search_call", "status": "completed"},
            message("I found a source."),
            message(
                json.dumps(
                    {
                        "reply": "The source says this. 【4311417271938779975†L40-L44】",
                        "tasks": [],
                        "chat_task_id": None,
                    }
                ),
                [
                    {
                        "type": "url_citation",
                        "url": "https://www.iana.org/help/example-domains",
                        "title": "IANA",
                    },
                    {
                        "type": "url_citation",
                        "url": "javascript:alert(1)",
                        "title": "Not a source",
                    },
                ],
            ),
        ],
    }
    muse, requests = model(monkeypatch, data)
    reply = muse.converse(
        {"web_enabled": True, "tasks": []}, "Find the official source"
    )
    assert reply.web_search_used is True and len(reply.sources) == 1
    assert (
        "4311417271938779975" not in reply.reply
        and "The source says this." in reply.reply
    )
    assert reply.sources[0].title == "IANA"
    url, request = requests[0]
    assert url.endswith("/responses") and request["json"]["tools"] == [
        {"type": "web_search"}
    ]
    assert request["json"]["store"] is False
    assert request["json"]["reasoning"] == {"effort": "low"}
    schema = request["json"]["text"]["format"]["schema"]
    assert (
        "sources" not in schema["properties"]
        and "web_search_used" not in schema["properties"]
    )
    assert "concrete task context" in request["json"]["instructions"]


def test_ungrounded_answers_cannot_invent_search_metadata(monkeypatch):
    data = {
        "status": "completed",
        "output": [
            message(
                json.dumps(
                    {
                        "reply": "Hello",
                        "tasks": [],
                        "web_search_used": True,
                        "sources": [{"url": "https://fake.example", "title": "Fake"}],
                    }
                )
            )
        ],
    }
    muse, _ = model(monkeypatch, data)
    result = muse.converse({"web_enabled": True}, "Hello")
    assert result.web_search_used is False and result.sources == []


@pytest.mark.parametrize(
    "payload,status",
    [
        ({"error": {"message": "fake-key provider secret"}}, 401),
        ({"status": "incomplete", "output": []}, 200),
        ({"status": "completed", "output": [message("invalid JSON fake-key")]}, 200),
        (
            {
                "status": "completed",
                "output": [{"type": "function_call", "name": "run_shell"}],
            },
            200,
        ),
        (
            {
                "status": "completed",
                "output": [
                    message(
                        json.dumps(
                            {"reply": "Bad", "tasks": [{"title": "Missing fields"}]}
                        )
                    )
                ],
            },
            200,
        ),
    ],
)
def test_web_failures_preserve_safe_errors(monkeypatch, payload, status):
    muse, _ = model(monkeypatch, payload, status)
    with pytest.raises(MuseFailure) as exc:
        muse.converse({"web_enabled": True}, "Question")
    assert "fake-key" not in str(exc.value)
