import os

from langchain_community.vectorstores import Chroma

from app.rag.models import get_embeddings_model
from app.settings import settings


def ensure_dirs() -> None:
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)


def get_vectorstore() -> Chroma:
    ensure_dirs()
    return Chroma(
        collection_name="irish-regulatory-docs",
        persist_directory=settings.chroma_persist_dir,
        embedding_function=get_embeddings_model(),
    )

