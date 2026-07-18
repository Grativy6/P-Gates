from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.mock_provider import EXAMPLE_TEXT
from app.providers import ProviderError, analyze_request
from app.schemas import AnalyzeRequest, AnalysisResult

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="P-Gates", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/example")
def example() -> dict[str, str]:
    return {"source_text": EXAMPLE_TEXT}


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze_route(request: AnalyzeRequest) -> AnalysisResult:
    if not request.source_text.strip():
        raise HTTPException(status_code=422, detail="Source text cannot be blank.")
    try:
        return analyze_request(request)
    except ProviderError as error:
        raise HTTPException(status_code=error.status_code, detail={"category": error.category, "message": error.public_message}) from error
