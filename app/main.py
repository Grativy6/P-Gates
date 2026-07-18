import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.mock_provider import EXAMPLE_TEXT
from app.config import Settings, has_openai_key
from app.provider_diagnostics import write_provider_failure
from app.providers import ProviderError, analyze_request
from openai import OpenAI
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


@app.get("/api/provider-status")
def provider_status() -> dict[str, bool | str]:
    client_constructed = False
    try:
        OpenAI(timeout=Settings().timeout_seconds, max_retries=0)
        client_constructed = True
    except Exception:
        pass
    return {
        "openai_api_key_exists": "OPENAI_API_KEY" in os.environ,
        "openai_api_key_nonempty": has_openai_key(),
        "openai_client_constructed": client_constructed,
        "environment_source": "process_environment",
    }


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze_route(request: AnalyzeRequest) -> AnalysisResult:
    if not request.source_text.strip():
        raise HTTPException(status_code=422, detail="Source text cannot be blank.")
    try:
        return analyze_request(request)
    except ProviderError as error:
        write_provider_failure(error)
        raise HTTPException(status_code=error.status_code, detail={"category": error.category, "message": error.public_message}) from error
