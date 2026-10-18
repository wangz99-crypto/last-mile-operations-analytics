"""Portfolio-only app, also mounted by the existing gateway. No model startup."""
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, ConfigDict

from domain.engine import CanonicalInputError
from domain.retrieval import RetrievalError
from src.triage_demo import CASES, analyze_case, case_catalog, exception_queue

UI = Path(__file__).resolve().parent / "ui"
router = APIRouter()


class DemoAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str


@router.get("/", include_in_schema=False)
def portfolio_home():
    return FileResponse(UI / "templates" / "portfolio.html")


@router.get("/engineering", include_in_schema=False)
def engineering_page():
    return FileResponse(UI / "templates" / "engineering.html")


@router.get("/zh", include_in_schema=False)
@router.get("/zh/engineering", include_in_schema=False)
def temporary_chinese_preview(request: Request):
    name = "engineering.html" if request.url.path.endswith("/engineering") else "portfolio.html"
    html = (UI / "templates" / name).read_text(encoding="utf-8")
    html = html.replace('lang="en"', 'lang="zh-CN"')
    html = html.replace('href="/engineering"', 'href="/zh/engineering"').replace('href="/#workspace"', 'href="/zh#workspace"').replace('href="/"', 'href="/zh"')
    html = html.replace('</head>', '<script src="/portfolio-assets/portfolio_zh.js?v=2" defer></script></head>')
    return HTMLResponse(html)


@router.get("/api/triage/queue")
def demo_queue():
    try:
        return exception_queue()
    except (RetrievalError, CanonicalInputError, OSError):
        raise HTTPException(503, "Verified queue is unavailable. No recommendations were issued.") from None


@router.get("/portfolio-assets/{name}", include_in_schema=False)
def portfolio_asset(name: str):
    if name not in {"portfolio.css", "portfolio.js", "portfolio_zh.js"}:
        raise HTTPException(404, "Asset not found")
    return FileResponse(UI / "static" / name)


@router.get("/api/triage/cases")
def demo_cases():
    return {"synthetic": True, "cases": case_catalog()}


@router.post("/api/triage/analyze")
def demo_analyze(request: DemoAnalysisRequest):
    if request.case_id not in {row[0] for row in CASES}:
        raise HTTPException(404, "Unknown demo case")
    try:
        return analyze_case(request.case_id)
    except (RetrievalError, CanonicalInputError, OSError):
        raise HTTPException(503, "Verified case or policy evidence is unavailable. No recommendation was issued.") from None


app = FastAPI(title="Last-Mile Exception Triage — Public Demo")
app.include_router(router)
