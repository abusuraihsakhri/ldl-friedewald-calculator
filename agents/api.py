"""
FastAPI REST API Server for Ldl Friedewald Calculator.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from ldl_calc import calculate_ldl
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Ldl Friedewald Calculator API",
    description="Lipid estimate reference API with optional legacy audit endpoints",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    query: str


class LipidPanel(BaseModel):
    total_cholesterol: float = Field(ge=0, allow_inf_nan=False)
    hdl: float = Field(ge=0, allow_inf_nan=False)
    triglycerides: float = Field(ge=0, allow_inf_nan=False)
    method: str = "friedewald"


@app.get("/health")
def health():
    return {"status": "ok", "service": "ldl-friedewald-calculator"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "running"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


@app.post("/api/ldl")
def api_ldl(panel: LipidPanel):
    """Compute a lipid estimate; invalid clinical ranges return valid=false."""
    try:
        return calculate_ldl(panel.total_cholesterol, panel.hdl,
                             panel.triglycerides, panel.method)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# Register last so API and health routes retain precedence.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "web",
                           html=True), name="web")
