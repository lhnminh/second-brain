from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
        env_ignore_empty=True,
    )

    database_url: str = (
        f"sqlite:///{Path(__file__).resolve().parents[1] / 'second-brain.db'}"
    )
    mock_user_id: str = Field(default="demo-user", min_length=1, max_length=100)
    mock_auth_token: SecretStr | None = None
    meta_api_key: SecretStr | None = None
    meta_base_url: str = "https://api.meta.ai/v1"
    meta_model: str = "muse-spark-1.3"
    meta_voice_model: str = "muse-voice-transcribe-1.0"
    frontend_origin: str = "http://localhost:3000"
    vercel: str | None = None

    def validate_hosted(self):
        if self.vercel and (
            self.database_url.startswith("sqlite") or not self.mock_auth_token
        ):
            raise ValueError("Hosted demo requires Postgres and MOCK_AUTH_TOKEN")
