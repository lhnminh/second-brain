import io
import json
import wave
from email import policy
from email.parser import BytesParser

import httpx
import pytest
from fastapi.testclient import TestClient

from second_brain.api import create_app
from second_brain.config import Settings
from second_brain.voice import (
    MAX_AUDIO_BYTES,
    VoiceFailure,
    VoiceTranscriber,
    validate_audio,
)


def wav(*, rate=24000, channels=1, width=2, seconds=1):
    out = io.BytesIO()
    with wave.open(out, "wb") as recording:
        recording.setnchannels(channels)
        recording.setsampwidth(width)
        recording.setframerate(rate)
        recording.writeframes(b"\x00" * int(rate * channels * width * seconds))
    return out.getvalue()


def adapter(monkeypatch, handler, **kwargs):
    original = httpx.Client
    monkeypatch.setattr(
        "second_brain.voice.httpx.Client",
        lambda **kw: original(transport=httpx.MockTransport(handler), **kw),
    )
    return VoiceTranscriber(
        Settings(_env_file=None, meta_api_key="voice-secret", vercel=None, **kwargs)
    )


def test_meta_transcription_contract(monkeypatch):
    audio = wav()

    def handler(request):
        assert str(request.url) == "https://api.meta.ai/v1/asr/transcribe"
        assert request.headers["Authorization"] == "Bearer voice-secret"
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: "
            + request.headers["content-type"].encode()
            + b"\r\n\r\n"
            + request.content
        )
        parts = {
            part.get_param("name", header="content-disposition"): part
            for part in message.iter_parts()
        }
        assert json.loads(parts["request"].get_payload(decode=True)) == {
            "model": "muse-voice-transcribe-1.0",
            "mode": "PUSH_TO_TALK",
            "audioEncoding": "WAV",
        }
        assert parts["audio"].get_payload(decode=True) == audio
        return httpx.Response(200, json={"transcript": " Finish homework. "})

    assert adapter(monkeypatch, handler).transcribe(audio) == "Finish homework."


@pytest.mark.parametrize(
    "case",
    [
        "401",
        "403",
        "404",
        "429",
        "500",
        "302",
        "timeout",
        "invalid",
        "missing",
        "wrong_type",
        "long",
        "empty",
    ],
)
def test_provider_failures_are_safe(monkeypatch, case):
    def handler(request):
        if case.isdigit():
            return httpx.Response(int(case), text="voice-secret private-provider-body")
        if case == "timeout":
            raise httpx.ReadTimeout("voice-secret", request=request)
        if case == "invalid":
            return httpx.Response(200, text="voice-secret invalid json")
        payload = {
            "missing": {},
            "wrong_type": {"transcript": []},
            "long": {"transcript": "x" * 10001},
            "empty": {"transcript": "  "},
        }[case]
        return httpx.Response(200, json=payload)

    with pytest.raises(VoiceFailure) as exc:
        adapter(monkeypatch, handler).transcribe(wav())
    assert "voice-secret" not in str(exc.value)
    assert "private-provider-body" not in str(exc.value)


@pytest.mark.parametrize(
    "audio",
    [
        b"",
        b"not audio",
        wav(rate=48000),
        wav(channels=2),
        wav(width=1),
        wav(seconds=0.1),
        wav(seconds=61),
        wav()[:-100],
    ],
)
def test_invalid_audio_never_reaches_provider(monkeypatch, audio):
    def handler(request):
        pytest.fail("Invalid audio must not be forwarded")

    with pytest.raises(VoiceFailure):
        adapter(monkeypatch, handler).transcribe(audio)


def test_supported_rates_and_duration_boundary():
    validate_audio(wav(rate=16000))
    validate_audio(wav(seconds=60))


def test_missing_key_never_connects(monkeypatch):
    monkeypatch.delenv("META_API_KEY", raising=False)
    with pytest.raises(VoiceFailure) as exc:
        VoiceTranscriber(Settings(_env_file=None, meta_api_key=None)).transcribe(wav())
    assert exc.value.status == 503


def test_transcription_is_authenticated_and_does_not_save_or_plan(setup):
    _clients, muse, engine = setup
    settings = Settings(
        _env_file=None,
        mock_user_id="alice",
        mock_auth_token="demo",
        meta_api_key=None,
        vercel=None,
    )
    calls = []

    class Transcriber:
        def transcribe(self, audio):
            calls.append(audio)
            validate_audio(audio)
            return "Finish homework"

    client = TestClient(create_app(settings, engine, muse, Transcriber()))
    audio = wav()
    assert (
        client.post(
            "/api/voice/transcribe",
            content=audio,
            headers={"Content-Type": "audio/wav"},
        ).status_code
        == 401
    )
    assert calls == []
    client.post("/api/session", json={"token": "demo"})
    before = client.get("/api/dashboard").json()
    result = client.post(
        "/api/voice/transcribe", content=audio, headers={"Content-Type": "audio/wav"}
    )
    assert result.status_code == 200
    assert result.headers["cache-control"] == "no-store"
    assert result.json() == {
        "transcript": "Finish homework",
        "model": "muse-voice-transcribe-1.0",
    }
    assert client.get("/api/dashboard").json() == before
    assert muse.calls == 0
    assert (
        client.post(
            "/api/voice/transcribe",
            content=audio,
            headers={"Content-Type": "audio/wav", "Origin": "https://other.example"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/voice/transcribe",
            content=audio,
            headers={"Content-Type": "audio/webm"},
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/voice/transcribe",
            content=b"x" * (MAX_AUDIO_BYTES + 1),
            headers={"Content-Type": "audio/wav"},
        ).status_code
        == 413
    )
    assert len(calls) == 1


def test_endpoint_reports_transcription_failure(setup):
    _, muse, engine = setup

    class Transcriber:
        def transcribe(self, audio):
            raise VoiceFailure("Voice unavailable", 503)

    client = TestClient(
        create_app(
            Settings(
                _env_file=None, meta_api_key=None, mock_auth_token=None, vercel=None
            ),
            engine,
            muse,
            Transcriber(),
        )
    )
    response = client.post(
        "/api/voice/transcribe", content=wav(), headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 503
    assert response.json() == {"error": {"message": "Voice unavailable"}}
