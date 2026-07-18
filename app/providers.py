import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError
from pydantic import ValidationError

from app.config import Settings, has_openai_key
from app.mock_provider import analyze as mock_analyze
from app.schemas import AnalysisResult, AnalyzeRequest, LiveDiagnostic, ModelAnalysis, Usage, ValidationIssue

REFERENCE_DIR = Path(__file__).resolve().parents[1] / "framework" / "mvp"
DISCLAIMER = "P-Gates is an analysis and drafting aid. It does not make decisions, create legal or ethical authority, replace due process, or substitute for accountable human judgment."


class ProviderError(Exception):
    def __init__(self, category: str, public_message: str, status_code: int, diagnostic: LiveDiagnostic | None = None) -> None:
        super().__init__(public_message)
        self.category = category
        self.public_message = public_message
        self.status_code = status_code
        self.diagnostic = diagnostic


def _references() -> str:
    return "\n\n".join((REFERENCE_DIR / name).read_text(encoding="utf-8") for name in ("pal.md", "pecan.md", "pea.md", "seed.md"))


def _prompt(source_text: str) -> str:
    return f"""You are P-Gates, a bounded route-analysis and drafting aid. Use only the distilled MVP references below. Do not claim authority, legal conclusions, factual guilt, empirical validation, or an accountable human decision. Analyze the submitted text, not external facts. Keep findings concise and specific. Return all four panels and a phrase-level trace.

{_references()}

SOURCE TEXT:
{source_text}"""


def _usage(response: object) -> Usage | None:
    raw = getattr(response, "usage", None)
    if raw is None:
        return None
    return Usage(input_tokens=getattr(raw, "input_tokens", None), output_tokens=getattr(raw, "output_tokens", None), total_tokens=getattr(raw, "total_tokens", None))


def _refusal(response: object) -> str | None:
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            refusal = getattr(content, "refusal", None)
            if refusal:
                return "Model refusal returned; text withheld from diagnostics."
    return None


def _shape(output_text: str) -> str:
    try:
        value = json.loads(output_text)
    except json.JSONDecodeError:
        return f"non-JSON text ({len(output_text)} characters; content withheld)"
    if isinstance(value, dict):
        return "JSON object keys: " + ", ".join(sorted(str(key) for key in value.keys())[:12])
    if isinstance(value, list):
        return f"JSON list ({len(value)} items)"
    return f"JSON {type(value).__name__}"


def _diagnostic(response: object, raw_response: object | None, requested_model: str, output_text: str | None = None) -> LiveDiagnostic:
    usage = _usage(response)
    incomplete = getattr(response, "incomplete_details", None)
    return LiveDiagnostic(
        request_id=getattr(response, "_request_id", None) or getattr(raw_response, "headers", {}).get("x-request-id") if raw_response else getattr(response, "_request_id", None),
        response_id=getattr(response, "id", None),
        http_status=getattr(raw_response, "status_code", None),
        response_status=getattr(response, "status", None),
        requested_model=requested_model,
        returned_model=getattr(response, "model", None),
        output_shape=_shape(output_text) if output_text is not None else None,
        input_tokens=usage.input_tokens if usage else None,
        output_tokens=usage.output_tokens if usage else None,
        total_tokens=usage.total_tokens if usage else None,
        incomplete_reason=getattr(incomplete, "reason", None) if incomplete else None,
        refusal=_refusal(response),
    )


def _validation_issues(error: ValidationError) -> list[ValidationIssue]:
    return [ValidationIssue(location=".".join(str(part) for part in issue["loc"]), message=issue["msg"], error_type=issue["type"]) for issue in error.errors()]


def analyze_openai(source_text: str, settings: Settings | None = None, client_factory: Callable[..., OpenAI] = OpenAI) -> AnalysisResult:
    if not has_openai_key():
        raise ProviderError("missing_api_key", "Live mode needs OPENAI_API_KEY in the server environment.", 503)
    settings = settings or Settings()
    try:
        client = client_factory(timeout=settings.timeout_seconds, max_retries=0)
        raw_response = client.responses.with_raw_response.create(
            model=settings.openai_model,
            input=[{"role": "system", "content": "Return only the requested structured route analysis."}, {"role": "user", "content": _prompt(source_text)}],
            text={"format": {"type": "json_schema", "name": "p_gates_route_analysis", "schema": ModelAnalysis.model_json_schema(), "strict": True}},
            max_output_tokens=settings.max_output_tokens,
            store=False,
        )
        response = raw_response.parse()
        output_text = getattr(response, "output_text", "") or ""
        diagnostic = _diagnostic(response, raw_response, settings.openai_model, output_text)
        if getattr(response, "status", None) == "incomplete":
            raise ProviderError("incomplete_response", "The model response was incomplete; no analysis was accepted.", 502, diagnostic)
        if getattr(response, "status", None) == "failed":
            raise ProviderError("failed_response", "The model response failed; no analysis was accepted.", 502, diagnostic)
        if diagnostic.refusal:
            raise ProviderError("model_refusal", "The model declined the request; no analysis was accepted.", 422, diagnostic)
        try:
            parsed = ModelAnalysis.model_validate_json(output_text)
        except ValidationError as error:
            diagnostic.validation_errors = _validation_issues(error)
            raise ProviderError("invalid_structured_output", "The model response did not match the required route-analysis schema.", 502, diagnostic) from error
        return AnalysisResult(source_text=source_text, analysis_timestamp=datetime.now(UTC), provider="openai", model_identifier=diagnostic.returned_model or settings.openai_model, pal=parsed.pal, pecan=parsed.pecan, pea=parsed.pea, seed=parsed.seed, trace=parsed.trace, disclaimer=DISCLAIMER, usage=_usage(response), live_diagnostic=diagnostic)
    except ProviderError:
        raise
    except AuthenticationError as error:
        raise ProviderError("authentication", "OpenAI authentication was rejected. Check the server environment key.", 502) from error
    except RateLimitError as error:
        raise ProviderError("rate_limit_or_billing", "OpenAI rate limit or billing limit reached. Try again later.", 429) from error
    except APITimeoutError as error:
        raise ProviderError("timeout", "The OpenAI request timed out. Try again.", 504) from error
    except APIConnectionError as error:
        raise ProviderError("network", "Could not reach the OpenAI API. Check the network and try again.", 503) from error
    except APIStatusError as error:
        raise ProviderError("api_status", "The OpenAI API returned an unexpected error. Try again later.", 502) from error


def analyze_request(request: AnalyzeRequest) -> AnalysisResult:
    return mock_analyze(request.source_text) if request.provider == "mock" else analyze_openai(request.source_text)
