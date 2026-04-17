import os
import uuid
from dataclasses import dataclass

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.audit.db import write_ingest_event
from app.rag.vectorstore import get_vectorstore


@dataclass(frozen=True)
class IngestResult:
    ingest_id: str
    file_count: int
    chunk_count: int


def ingest_folder(*, folder_path: str, actor_role: str) -> IngestResult:
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder not found: {folder_path}")

    pdf_paths: list[str] = []
    for root, _dirs, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_paths.append(os.path.join(root, f))

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=256, chunk_overlap=50)

    docs = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        loaded = loader.load()
        for d in loaded:
            d.metadata = dict(d.metadata or {})
            d.metadata["source"] = os.path.relpath(path, folder_path).replace("\\", "/")
        docs.extend(loaded)

    chunks = splitter.split_documents(docs)
    for c in chunks:
        c.metadata = dict(c.metadata or {})
        c.metadata["chunk_id"] = str(uuid.uuid4())

    vs = get_vectorstore()
    if chunks:
        vs.add_documents(chunks)

    ingest_id = str(uuid.uuid4())
    write_ingest_event(
        event_id=ingest_id,
        actor_role=actor_role,
        folder_path=folder_path,
        file_count=len(pdf_paths),
        chunk_count=len(chunks),
    )
    return IngestResult(ingest_id=ingest_id, file_count=len(pdf_paths), chunk_count=len(chunks))

