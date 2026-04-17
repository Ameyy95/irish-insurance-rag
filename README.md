# Irish Insurance RAG Compliance Agent (from scratch)

End-to-end Retrieval-Augmented Generation (RAG) service for Irish insurance regulatory / compliance documents.

## What you get

- **Ingestion**: PDFs \(\*.pdf\) → text → semantic chunking → embeddings → **ChromaDB** (persistent on disk)
- **Querying**: FastAPI endpoint that does retrieval + grounded answer with citations
- **Governance**:
  - **PII redaction** using **spaCy NER** + a few regexes (email/phone)
  - **Audit trail** in SQLite (all queries + ingest events)
  - **Role-based access** via API keys (analyst/reviewer/admin)
  - **Human escalation gate** for high-risk query topics (AML breach reporting, capital adequacy, etc.)
- **Deployment**: Dockerfile + docker-compose

## Prereqs

- Docker (recommended) or Python 3.11+
- One provider mode:
  - **OpenAI mode**: OpenAI API key
  - **Local mode (offline)**: [Ollama](https://ollama.com/) installed and running locally

## Quickstart (Docker)

1. Create an env file:

```bash
copy .env.example .env
```

2. Edit `.env`:
   - OpenAI mode:
     - `MODEL_PROVIDER=openai`
     - set `OPENAI_API_KEY`
   - Local/offline mode:
     - `MODEL_PROVIDER=local`
     - keep `OLLAMA_BASE_URL=http://localhost:11434`
     - keep default models or change:
       - `OLLAMA_EMBEDDING_MODEL=nomic-embed-text`
       - `OLLAMA_CHAT_MODEL=llama3.2`

3. Start the API:

```bash
docker compose up --build
```

API will be at `http://localhost:8000`.

### Local/offline model pull (required once)

Before querying in `MODEL_PROVIDER=local`, pull local models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.2
```

## Quickstart (Local Python)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Using the API

### 1\) Ingest PDFs (admin only)

Put PDFs in a folder (example: `data/pdfs/`), then call:

```bash
curl -X POST "http://localhost:8000/ingest" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: admin-key-change-me" ^
  -d "{\"folder_path\":\"data/pdfs\"}"
```

### 2\) Ask a question (analyst/reviewer/admin)

```bash
curl -X POST "http://localhost:8000/query" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: analyst-key-change-me" ^
  -d "{\"question\":\"What are the reporting obligations for AML breaches?\"}"
```

If the query is high-risk, the service returns an escalation ticket ID. A reviewer can approve:

```bash
curl -X POST "http://localhost:8000/review/approve" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: reviewer-key-change-me" ^
  -d "{\"ticket_id\":\"...\"}"
```

## Project layout

- `app/main.py`: FastAPI routes
- `app/rag/`: ingestion + retrieval + LLM answering
- `app/pii/redact.py`: PII redaction
- `app/security/auth.py`: API key RBAC
- `app/audit/db.py`: SQLite audit trail
- `data/`: persisted Chroma + audit DB (created at runtime)

## Notes

- Chunking uses **tiktoken-aware** splitting: chunk size **512 tokens**, overlap **50 tokens**.
- This scaffold is designed to be easy to extend: add better risk policies, approvals workflow, and richer evaluation (RAGAS).
- In local mode, no OpenAI calls are made; embeddings + generation both go through Ollama on your machine.

