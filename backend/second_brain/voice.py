"""Bounded, nonpersistent audio transcription through Meta's Voice API."""

import io
import json
import wave

import httpx

MAX_AUDIO_BYTES = 2_880_044  # One minute of mono 24 kHz PCM16 plus WAV header.
MAX_AUDIO_SECONDS = 60


class VoiceFailure(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def validate_audio(audio):
    if len(audio) > MAX_AUDIO_BYTES:
        raise VoiceFailure("Recording exceeds the one-minute audio limit", 413)
    try:
        with wave.open(io.BytesIO(audio), "rb") as recording:
            channels, width, rate, frames, compression, _ = recording.getparams()
            if (
                channels != 1
                or width != 2
                or rate not in {16000, 24000}
                or compression != "NONE"
                or not rate // 4 <= frames <= rate * MAX_AUDIO_SECONDS
                or len(recording.readframes(frames)) != frames * width
            ):
                raise ValueError
    except wave.Error, EOFError, ValueError:
        raise VoiceFailure(
            "Use a complete mono PCM16 WAV recording at 16 or 24 kHz, "
            "between a quarter second and one minute long",
            422,
        ) from None


class VoiceTranscriber:
    def __init__(self, settings):
        self.settings = settings

    def transcribe(self, audio):
        validate_audio(audio)
        key = self.settings.meta_api_key
        if not key or not key.get_secret_value():
            raise VoiceFailure(
                "Voice transcription requires the server's Meta API key", 503
            )
        try:
            with httpx.Client(
                timeout=httpx.Timeout(45, connect=10), follow_redirects=False
            ) as client:
                response = client.post(
                    self.settings.meta_base_url.rstrip("/") + "/asr/transcribe",
                    headers={"Authorization": "Bearer " + key.get_secret_value()},
                    files={
                        "request": (
                            None,
                            json.dumps(
                                {
                                    "model": self.settings.meta_voice_model,
                                    "mode": "PUSH_TO_TALK",
                                    "audioEncoding": "WAV",
                                }
                            ),
                            "application/json",
                        ),
                        "audio": ("recording.wav", audio, "audio/wav"),
                    },
                )
                if response.status_code in {401, 403, 404}:
                    raise VoiceFailure(
                        "Meta voice transcription is unavailable for the configured "
                        "key or endpoint. Check server configuration and model access.",
                        503,
                    )
                if response.status_code == 429:
                    raise VoiceFailure(
                        "Voice transcription is busy. Retry shortly.", 503
                    )
                response.raise_for_status()
                data = response.json()
                text = data["transcript"]
                if not isinstance(text, str) or len(text) > 10000:
                    raise ValueError
                text = text.strip()
                if not text:
                    raise VoiceFailure(
                        "No speech was transcribed. Try speaking closer to the microphone.",
                        422,
                    )
                return text
        except httpx.HTTPError, ValueError, KeyError, TypeError:
            raise VoiceFailure(
                "Meta voice transcription could not finish. Retry the recording "
                "or continue typing; your draft is kept."
            ) from None
