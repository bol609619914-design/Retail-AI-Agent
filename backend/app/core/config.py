from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Retail-AI-Agent API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    allowed_origin_regex: str = r"https://.*\.vercel\.app"
    llm_provider: str = "openai_compatible"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
