"""One-shot, sanitized diagnostic for the real P-Gates live provider path."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable
from types import SimpleNamespace

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI
from pydantic import ValidationError

from app.config import Settings
from app.mock_provider import EXAMPLE_TEXT
from app.providers import _diagnostic, _validation_issues
from app.schemas import ModelAnalysis


DIAGNOSTICS_DIR = REPOSITORY_ROOT / "diagnostics"
RESULT_PATH = DIAGNOSTICS_DIR / "p-gates-live-result.json"
PROGRESS_PATH = DIAGNOSTICS_DIR / "p-gates-live-progress.log"


def progress(marker: str, progress_path: Path) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{marker}\n")
        handle.flush()
        os.fsync(handle.fileno())


def base_result() -> dict[str, object]:
    return {
        "success": False,
        "exception_class": None,
        "safe_error_code": None,
        "safe_error_message": None,
        "http_status": None,
        "request_id": None,
        "response_id": None,
        "requested_model": "gpt-5.6",
        "returned_model": None,
        "response_status": None,
        "incomplete_reason": None,
        "refusal_marker": False,
        "output_text_valid_json": False,
        "pydantic_validation_passed": False,
        "validation_errors": [],
        "token_usage": None,
    }


def diagnostic_fields(diagnostic: Any) -> dict[str, object]:
    if diagnostic is None:
        return {}
    return {
        "http_status": diagnostic.http_status,
        "request_id": diagnostic.request_id,
        "response_id": diagnostic.response_id,
        "requested_model": diagnostic.requested_model,
        "returned_model": diagnostic.returned_model,
        "response_status": diagnostic.response_status,
        "incomplete_reason": diagnostic.incomplete_reason,
        "refusal_marker": bool(diagnostic.refusal),
        "output_text_valid_json": diagnostic.output_shape is not None and not diagnostic.output_shape.startswith("non-JSON"),
        "pydantic_validation_passed": not diagnostic.validation_errors,
        "validation_errors": [{"location": item.location, "message": item.message} for item in diagnostic.validation_errors],
        "token_usage": {"input_tokens": diagnostic.input_tokens, "output_tokens": diagnostic.output_tokens, "total_tokens": diagnostic.total_tokens},
    }


def write_atomic(result: dict[str, object], result_path: Path, progress_path: Path) -> None:
    progress("diagnostic_write_start", progress_path)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = result_path.with_suffix(result_path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary_path, result_path)
    progress("diagnostic_write_complete", progress_path)


def safe_exception(error: BaseException) -> tuple[str, str]:
    if isinstance(error, APITimeoutError):
        return "timeout", "The OpenAI request timed out."
    if isinstance(error, APIConnectionError):
        return "network", "Could not reach the OpenAI API."
    if isinstance(error, APIStatusError):
        return "api_status", "The OpenAI API returned an error response."
    if isinstance(error, ValidationError):
        if any(item["type"] == "json_invalid" for item in error.errors()):
            return "invalid_json", "The response output was not valid JSON."
        return "pydantic_validation", "The returned JSON did not match the required schema."
    if isinstance(error, json.JSONDecodeError):
        return "invalid_json", "The response output was not valid JSON."
    if isinstance(error, (KeyboardInterrupt, SystemExit)):
        return "interrupted", "The diagnostic process was interrupted."
    return "unexpected", "The diagnostic runner encountered an unexpected local error."


def run_once(
    client_factory: Callable[..., Any] = OpenAI,
    result_path: Path = RESULT_PATH,
    progress_path: Path = PROGRESS_PATH,
) -> tuple[int, dict[str, object]]:
    result = base_result()
    caught: BaseException | None = None
    try:
        progress("client_creation_start", progress_path)
        client = client_factory(timeout=60.0, max_retries=0)
        progress("client_creation_complete", progress_path)
        progress("request_start", progress_path)
        raw_response = client.responses.with_raw_response.create(
            model="gpt-5.6",
            input="Return exactly: API OK",
            text={"format": {"type": "json_schema", "name": "p_gates_route_analysis", "schema": ModelAnalysis.model_json_schema(), "strict": True}},
            max_output_tokens=1800,
            store=False,
        )
        progress("request_complete", progress_path)
        progress("response_receipt_start", progress_path)
        response = raw_response.parse()
        progress("response_receipt_complete", progress_path)
        progress("output_extraction_start", progress_path)
        output_text = getattr(response, "output_text", "") or ""
        diagnostic = _diagnostic(response, raw_response, "gpt-5.6", output_text)
        result.update(diagnostic_fields(diagnostic))
        progress("output_extraction_complete", progress_path)
        if getattr(response, "status", None) != "completed" or diagnostic.refusal or diagnostic.incomplete_reason:
            raise RuntimeError("Response was not eligible for local schema validation")
        progress("validation_start", progress_path)
        parsed = ModelAnalysis.model_validate_json(output_text)
        del parsed
        result["success"] = True
        result["pydantic_validation_passed"] = True
        progress("validation_complete", progress_path)
    except BaseException as error:
        caught = error
        safe_code, safe_message = safe_exception(error)
        result["exception_class"] = type(error).__name__
        result["safe_error_code"] = safe_code
        result["safe_error_message"] = safe_message
        if isinstance(error, ValidationError):
            result["validation_errors"] = [{"location": item.location, "message": item.message} for item in _validation_issues(error)]
        if isinstance(error, APIStatusError):
            result["http_status"] = error.status_code
            result["request_id"] = getattr(error, "request_id", None)
    finally:
        write_atomic(result, result_path, progress_path)
    if isinstance(caught, (SystemExit, KeyboardInterrupt)):
        raise caught
    return (0 if result["success"] else 1), result


def mock_success_client(**_: Any) -> Any:
    output = json.dumps({
        "pal": {"summary": "mock", "findings": []},
        "pecan": {"summary": "mock", "findings": []},
        "pea": {"summary": "mock", "findings": []},
        "seed": {"summary": "mock", "findings": []},
        "trace": [],
    })
    response = SimpleNamespace(id="resp_mock", model="gpt-5.6-sol", status="completed", output_text=output, usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15), output=[])
    raw = SimpleNamespace(status_code=200, headers={"x-request-id": "req_mock"}, parse=lambda: response)
    return SimpleNamespace(responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=lambda **__: raw)))


def main() -> int:
    factory = mock_success_client if "--mock-success" in sys.argv else OpenAI
    code, result = run_once(factory)
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
