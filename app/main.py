from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.audit import db as audit_db
from app.audit.db import create_escalation_ticket, decide_escalation_ticket, list_recent_queries, write_query_event
from app.pii.redact import redact_pii
from app.rag.answer import answer_with_rag, new_event_id
from app.rag.ingest import ingest_folder
from app.rag.risk import assess_risk
from app.security.auth import Principal, require_role

app = FastAPI(title="ComplianceRAG", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    audit_db.init_db()


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return FileResponse("rag-compliance-ui.html")


@app.get("/health")
def health():
    return {"ok": True}


class IngestRequest(BaseModel):
    folder_path: str = Field(..., description="Folder containing PDFs to ingest")


class IngestResponse(BaseModel):
    ingest_id: str
    file_count: int
    chunk_count: int


class QueryRequest(BaseModel):
    question: str
    top_k: int = 6


class QueryResponse(BaseModel):
    status: str
    event_id: str
    risk_level: str
    answer: str | None = None
    answer_redacted: str | None = None
    sources: list[dict] = []
    escalation_ticket_id: str | None = None
    escalation_reason: str | None = None


class ReviewApproveRequest(BaseModel):
    ticket_id: str
    top_k: int = 6


@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest, principal: Principal = Depends(require_role("admin"))):
    try:
        res = ingest_folder(folder_path=req.folder_path, actor_role=principal.role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return IngestResponse(ingest_id=res.ingest_id, file_count=res.file_count, chunk_count=res.chunk_count)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, principal: Principal = Depends(require_role("admin", "reviewer", "analyst"))):
    event_id = new_event_id()
    question_redacted = redact_pii(req.question)

    risk = assess_risk(req.question)
    if risk.level == "high" and principal.role == "analyst":
        ticket_id = new_event_id()
        create_escalation_ticket(
            ticket_id=ticket_id,
            actor_role=principal.role,
            question=req.question,
            question_redacted=question_redacted,
            risk_reason=risk.reason,
        )
        write_query_event(
            event_id=event_id,
            actor_role=principal.role,
            question=req.question,
            question_redacted=question_redacted,
            risk_level=risk.level,
            escalation_ticket_id=ticket_id,
            retrieved_k=req.top_k,
            sources=[],
            answer=None,
            answer_redacted=None,
        )
        return QueryResponse(
            status="escalated",
            event_id=event_id,
            risk_level=risk.level,
            escalation_ticket_id=ticket_id,
            escalation_reason=risk.reason,
        )

    try:
        rag = answer_with_rag(question=req.question, k=req.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    answer_redacted = redact_pii(rag.answer)
    write_query_event(
        event_id=event_id,
        actor_role=principal.role,
        question=req.question,
        question_redacted=question_redacted,
        risk_level=risk.level,
        escalation_ticket_id=None,
        retrieved_k=rag.retrieved_k,
        sources=rag.sources,
        answer=rag.answer,
        answer_redacted=answer_redacted,
    )
    return QueryResponse(
        status="answered",
        event_id=event_id,
        risk_level=risk.level,
        answer=rag.answer,
        answer_redacted=answer_redacted,
        sources=[s.__dict__ for s in rag.sources],
    )


@app.post("/review/approve", response_model=QueryResponse)
def review_approve(req: ReviewApproveRequest, principal: Principal = Depends(require_role("admin", "reviewer"))):
    decided = decide_escalation_ticket(ticket_id=req.ticket_id, reviewer_role=principal.role, decision="approved")
    if not decided:
        raise HTTPException(status_code=404, detail="Ticket not found")

    question = decided["question"]
    event_id = new_event_id()
    question_redacted = decided["question_redacted"]
    risk_level = "high"

    try:
        rag = answer_with_rag(question=question, k=req.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    answer_redacted = redact_pii(rag.answer)
    write_query_event(
        event_id=event_id,
        actor_role=principal.role,
        question=question,
        question_redacted=question_redacted,
        risk_level=risk_level,
        escalation_ticket_id=req.ticket_id,
        retrieved_k=rag.retrieved_k,
        sources=rag.sources,
        answer=rag.answer,
        answer_redacted=answer_redacted,
    )
    return QueryResponse(
        status="answered",
        event_id=event_id,
        risk_level=risk_level,
        answer=rag.answer,
        answer_redacted=answer_redacted,
        sources=[s.__dict__ for s in rag.sources],
        escalation_ticket_id=req.ticket_id,
    )


@app.get("/audit/queries")
def audit_queries(limit: int = 50, principal: Principal = Depends(require_role("admin"))):
    return {"queries": list_recent_queries(limit=limit)}