from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    public_base_url: str = ""

    deepgram_api_key: str = ""

    llm_provider: str = "groq"
    groq_api_key: str = ""

    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""


settings = Settings()