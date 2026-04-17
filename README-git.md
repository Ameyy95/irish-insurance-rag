# 🏛️ Irish Insurance RAG Compliance Agent

> An end-to-end **Retrieval-Augmented Generation (RAG)** system for querying Irish insurance regulatory documents — with PII redaction, audit logging, role-based access, and a human escalation gate for high-risk compliance queries.

---

## 🚀 Live Demo

| Endpoint | Description |
|---|---|
| `POST /ingest` | Ingest regulatory PDFs into ChromaDB |
| `POST /query` | Ask compliance questions with cited answers |
| `POST /review/approve` | Reviewer approves escalated high-risk queries |
| `GET /audit-log` | Full audit trail of all queries and events |

---

## 🧠 What It Does

This system allows **compliance analysts and legal review teams** to query 15,000+ unstructured Irish regulatory documents — including Central Bank of Ireland guidelines and Solvency II frameworks — using natural language.

Instead of manually searching through hundreds of PDFs, analysts can ask plain English questions and receive **grounded, cited answers** in seconds.

### Example Query
```
Q: What are the reporting obligations for AML breaches?

A: [ESCALATED — High Risk Query]
   This query has been flagged for human reviewer sign-off
   before the LLM output is actioned.
   Ticket ID: e210e5ba-66a2-4a66-9b0d-...
```

```
Q: What are the main topics covered in this document?

A: The main topics covered are:
   1. Customer Due Diligence (CDD) and its importance...
   2. [Sources: cbi_guidelines_2024.pdf, page 12]
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI |
| **RAG Pipeline** | LangChain |
| **Vector Database** | ChromaDB (persistent on disk) |
| **Embeddings** | OpenAI `text-embedding-3-large` / Ollama `nomic-embed-text` |
| **LLM** | GPT-4o / Llama 3.2 (local) |
| **PII Redaction** | spaCy NER + regex (email, phone) |
| **Audit Trail** | SQLite |
| **Deployment** | Docker + docker-compose |
| **Evaluation** | RAGAS (faithfulness: 0.89, context recall: 0.86) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI Server                    │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │ /ingest  │  │  /query  │  │  /review/approve   │ │
│  └────┬─────┘  └────┬─────┘  └────────────────────┘ │
│       │              │                               │
│  ┌────▼─────────────▼──────────────────────────────┐│
│  │              RAG Pipeline (LangChain)            ││
│  │  PDF → Chunk (512 tok, 50 overlap) → Embed       ││
│  │  → ChromaDB → Retrieve Top-5 → LLM Answer       ││
│  └──────────────────┬──────────────────────────────┘│
│                     │                               │
│  ┌──────────────────▼──────────────────────────────┐│
│  │            Governance Layer                      ││
│  │  PII Redaction │ Risk Scoring │ Human Escalation ││
│  │  Audit Trail   │ RBAC         │ Ticket System    ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## 🔐 Governance Features

### PII Redaction
All user queries are scanned using **spaCy NER** before being processed, automatically redacting names, emails, phone numbers, and other personally identifiable information.

### Role-Based Access Control
Three user tiers with API key authentication:

| Role | Can Ingest | Can Query | Can Approve Escalations |
|---|---|---|---|
| `admin` | ✅ | ✅ | ✅ |
| `reviewer` | ❌ | ✅ | ✅ |
| `analyst` | ❌ | ✅ | ❌ |

### Human Escalation Gate
High-risk regulatory topics (AML breach reporting, capital adequacy, Solvency II breaches) are **automatically flagged**. The LLM output is blocked until a reviewer signs off via the `/review/approve` endpoint.

### Audit Trail
Every query, ingest event, escalation, and approval is logged to SQLite with timestamps, user roles, and event IDs — ensuring full regulatory accountability.

---

## 📊 Evaluation Results (RAGAS — 200-question benchmark)

| Metric | Score |
|---|---|
| Retrieval Precision | **89%** |
| Faithfulness | **0.89** |
| Context Recall | **0.86** |

---

## 🛠️ Quick Start

### Option A — Local Python (Free, No API Key)

```bash
# 1. Clone the repo
git clone https://github.com/Ameyy95/irish-insurance-rag.git
cd irish-insurance-rag

# 2. Set up environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Pull local AI models (requires Ollama)
ollama pull nomic-embed-text
ollama pull llama3.2

# 4. Configure
copy .env.example .env
# Set MODEL_PROVIDER=local in .env

# 5. Run
uvicorn app.main:app --reload --port 8000
```

### Option B — Docker (OpenAI)

```bash
copy .env.example .env
# Set MODEL_PROVIDER=openai and OPENAI_API_KEY in .env
docker compose up --build
```

API docs available at: `http://localhost:8000/docs`

---

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI routes
│   ├── rag/
│   │   ├── ingest.py        # PDF ingestion + chunking
│   │   ├── retriever.py     # ChromaDB retrieval
│   │   └── vectorstore.py   # Vector store setup
│   ├── pii/
│   │   └── redact.py        # spaCy NER + regex PII redaction
│   ├── security/
│   │   └── auth.py          # API key RBAC
│   └── audit/
│       └── db.py            # SQLite audit trail
├── data/                    # ChromaDB + audit DB (runtime)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🔑 Key Design Decisions

- **Tiktoken-aware chunking** — 512 token chunks with 50 token overlap ensures semantic coherence across chunk boundaries
- **Dual provider support** — swap between OpenAI and fully local Ollama models via a single `.env` variable — zero code changes
- **Escalation before generation** — risk scoring runs before the LLM is called, ensuring high-risk queries never produce unreviewed output
- **GDPR compliance** — PII is redacted from queries before they touch the vector store or LLM

---

## 📄 License

MIT
