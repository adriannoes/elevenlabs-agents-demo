"""Typed application settings loaded from environment variables and optional `.env` file."""

from functools import lru_cache
from typing import Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for ElevenLabs demos."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    elevenlabs_api_key: SecretStr = Field(
        ...,
        description="ElevenLabs API key (never log this value).",
    )
    openai_api_key: SecretStr | None = Field(
        default=None,
        description="Optional OpenAI API key for vendor TTS benchmark only.",
    )
    openai_tts_model_id: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "coral"
    openai_tts_response_format: str = "mp3"
    default_agent_voice_id: str | None = Field(
        default=None,
        description=("Voice Library id for ElevenAgents (English or multilingual for EN demos)."),
    )
    default_pt_voice_id: str | None = None
    default_en_voice_id: str | None = None
    demo_agent_id_telecom: str | None = None
    demo_agent_id_banking: str | None = None
    demo_agent_id_healthcare: str | None = None
    convai_demo_tool_webhook_url: str | None = Field(
        default=None,
        description="Public HTTPS base URL for Convai server-tool webhooks when provisioning.",
    )
    tts_model_id: str = "eleven_flash_v2_5"
    tts_output_format: str = "mp3_22050_32"
    stt_model_id: str = "scribe_v2"
    stt_realtime_model_id: str = "scribe_v2_realtime"
    log_level: str = "INFO"

    @field_validator(
        "default_agent_voice_id",
        "default_pt_voice_id",
        "default_en_voice_id",
        "demo_agent_id_telecom",
        "demo_agent_id_banking",
        "demo_agent_id_healthcare",
        "convai_demo_tool_webhook_url",
        mode="before",
    )
    @classmethod
    def empty_optional_str_to_none(cls, value: object) -> str | None:
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            msg = "Optional string settings expect a string"
            raise TypeError(msg)
        return value

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def empty_openai_key_to_none(cls, value: object) -> SecretStr | None:
        if value is None or value == "":
            return None
        if isinstance(value, SecretStr):
            return value
        if isinstance(value, str):
            return SecretStr(value)
        msg = "OPENAI_API_KEY must be a string when set"
        raise TypeError(msg)

    @model_validator(mode="after")
    def api_key_must_be_non_empty(self) -> Self:
        raw = self.elevenlabs_api_key.get_secret_value().strip()
        if not raw:
            msg = "ELEVENLABS_API_KEY is required"
            raise ValueError(msg)
        return self


def conversational_agent_voice_id(settings: Settings) -> str | None:
    """First non-empty of agent, English, then PT default voice id fields."""
    for raw in (
        settings.default_agent_voice_id,
        settings.default_en_voice_id,
        settings.default_pt_voice_id,
    ):
        if raw and raw.strip():
            return raw.strip()
    return None


def convai_demo_tool_webhook_fields(settings: Settings) -> dict[str, str]:
    """``tool_webhook_url`` for scenario kwargs when ``convai_demo_tool_webhook_url`` is set."""
    url = (settings.convai_demo_tool_webhook_url or "").strip()
    if not url:
        return {}
    return {"tool_webhook_url": url}


def resolve_conversational_agent_voice_id(settings: Settings) -> str:
    """Voice id for provisioning, or raise if none of the defaults are set."""
    resolved = conversational_agent_voice_id(settings)
    if resolved is None:
        msg = (
            "Set DEFAULT_AGENT_VOICE_ID, DEFAULT_EN_VOICE_ID, or DEFAULT_PT_VOICE_ID "
            "for agent provisioning."
        )
        raise ValueError(msg)
    return resolved


@lru_cache
def get_settings() -> Settings:
    """Return cached settings (singleton per process)."""
    return Settings()
