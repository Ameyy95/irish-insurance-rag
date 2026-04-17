from langchain_core.language_models import BaseChatModel

from app.settings import settings


def get_embeddings_model():
    provider = settings.model_provider.strip().lower()
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set. Create a .env file (see .env.example).")
        return OpenAIEmbeddings(model=settings.openai_embedding_model, api_key=settings.openai_api_key)
    if provider == "local":
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError as e:
            raise ValueError(
                "Local mode requires langchain-ollama. Install dependencies: pip install -r requirements.txt"
            ) from e
        return OllamaEmbeddings(model=settings.ollama_embedding_model, base_url=settings.ollama_base_url)
    raise ValueError("Invalid MODEL_PROVIDER. Use 'openai' or 'local'.")


def get_chat_model() -> BaseChatModel:
    provider = settings.model_provider.strip().lower()
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set. Create a .env file (see .env.example).")
        return ChatOpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key, temperature=0)
    if provider == "local":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as e:
            raise ValueError(
                "Local mode requires langchain-ollama. Install dependencies: pip install -r requirements.txt"
            ) from e
        return ChatOllama(model=settings.ollama_chat_model, base_url=settings.ollama_base_url, temperature=0)
    raise ValueError("Invalid MODEL_PROVIDER. Use 'openai' or 'local'.")

