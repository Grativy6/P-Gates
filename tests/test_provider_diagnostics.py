import json

from app.provider_diagnostics import write_provider_failure
from app.providers import ProviderError
from app.schemas import LiveDiagnostic


def test_provider_failure_record_contains_only_safe_fields(monkeypatch, tmp_path) -> None:
    target = tmp_path / "p-gates-provider-path-result.json"
    monkeypatch.setattr("app.provider_diagnostics.RESULT_PATH", target)
    error = ProviderError(
        "network",
        "Could not reach the OpenAI API. Check the network and try again.",
        503,
        LiveDiagnostic(requested_model="gpt-5.6", request_id="req_safe", provider_stage="request_dispatch"),
        exception_class="APIConnectionError",
    )
    write_provider_failure(error)
    record = json.loads(target.read_text(encoding="utf-8"))
    assert set(record) == {"exception_class", "safe_error_code", "safe_error_message", "http_status", "request_id", "provider_stage"}
    assert record["exception_class"] == "APIConnectionError"
    assert record["provider_stage"] == "request_dispatch"
