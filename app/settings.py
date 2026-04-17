from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    model_provider: str = "openai"

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-large"
    openai_chat_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llama3.2"

    chroma_persist_dir: str = "data/chroma"
    audit_db_path: str = "data/audit.db"

    api_key_admin: str = "admin-key-change-me"
    api_key_reviewer: str = "reviewer-key-change-me"
    api_key_analyst: str = "analyst-key-change-me"

    app_env: str = "dev"


settings = Settings()

