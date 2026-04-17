import uuid
from dataclasses import dataclass

from app.audit.db import SourceRef
from app.rag.models import get_chat_model
from app.rag.vectorstore import get_vectorstore


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[SourceRef]
    retrieved_k: int


SYSTEM_PROMPT = """You are a compliance support assistant for Irish insurance regulation.

Rules:
- Answer ONLY using the provided context.
- If the context is insufficient, say so and ask for the missing document or section.
- Provide a short, practical answer, then list citations as bullets in the form: source (page N).
- Do not provide legal advice. Use cautious language.
"""


def _format_context(chunks: list[tuple[str, dict]]) -> str:
    parts = []
    for i, (text, md) in enumerate(chunks, start=1):
        src = md.get("source", "unknown")
        page = md.get("page")
        parts.append(f"[{i}] source={src} page={page}\n{text}")
    return "\n\n".join(parts)


def answer_with_rag(*, question: str, k: int = 6) -> RAGAnswer:
    vs = get_vectorstore()
    results = vs.similarity_search_with_score(question, k=k)

    ctx = []
    sources: list[SourceRef] = []
    for doc, score in results:
        md = dict(doc.metadata or {})
        ctx.append((doc.page_content, md))
        sources.append(
            SourceRef(
                source=str(md.get("source", "unknown")),
                page=int(md["page"]) if "page" in md and md["page"] is not None else None,
                chunk_id=str(md.get("chunk_id")) if md.get("chunk_id") else None,
                score=float(score) if score is not None else None,
            )
        )

    llm = get_chat_model()
    user_prompt = f"""Question:
{question}

Context:
{_format_context(ctx)}
"""
    resp = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    text = getattr(resp, "content", None) or str(resp)
    return RAGAnswer(answer=text, sources=sources, retrieved_k=k)


def new_event_id() -> str:
    return str(uuid.uuid4())

