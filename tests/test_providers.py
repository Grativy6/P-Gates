from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.config import Settings
from app.providers import ProviderError, _shape, analyze_openai
from app.schemas import AnalyzeRequest, ModelAnalysis


def test_usage_maps_safe_token_counts() -> None:
    from app.providers import _usage

    usage = _usage(SimpleNamespace(usage=SimpleNamespace(input_tokens=11, output_tokens=7, total_tokens=18)))
    assert usage is not None
    assert usage.total_tokens == 18


def test_openai_mode_without_key_has_safe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError) as error:
        analyze_openai("small test", Settings())
    assert error.value.category == "missing_api_key"


def test_request_defaults_to_mock() -> None:
    assert AnalyzeRequest(source_text="x").provider == "mock"


def test_schema_has_no_untyped_object_fields() -> None:
    schema = ModelAnalysis.model_json_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"pal", "pecan", "pea", "seed", "trace"}


def test_output_shape_withholds_json_values() -> None:
    assert _shape('{"pal":{"secret":"do not display"},"trace":[]}') == "JSON object keys: pal, trace"


def test_invalid_json_schema_preserves_safe_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "present-for-test-only")
    response = SimpleNamespace(id="resp_test", model="gpt-5.6", status="completed", output_text='{"pal":{}}', usage=SimpleNamespace(input_tokens=12, output_tokens=5, total_tokens=17), output=[])
    raw = SimpleNamespace(status_code=200, headers={"x-request-id": "req_test"}, parse=lambda: response)
    client = SimpleNamespace(responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=lambda **kwargs: raw)))
    with pytest.raises(ProviderError) as error:
        analyze_openai("small test", Settings(), client_factory=lambda **kwargs: client)
    assert error.value.category == "invalid_structured_output"
    assert error.value.diagnostic is not None
    assert error.value.diagnostic.http_status == 200
    assert error.value.diagnostic.request_id == "req_test"
    assert error.value.diagnostic.validation_errors


def test_incomplete_response_is_checked_before_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "present-for-test-only")
    response = SimpleNamespace(id="resp_test", model="gpt-5.6", status="incomplete", output_text="", usage=None, output=[], incomplete_details=SimpleNamespace(reason="max_output_tokens"))
    raw = SimpleNamespace(status_code=200, headers={}, parse=lambda: response)
    client = SimpleNamespace(responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=lambda **kwargs: raw)))
    with pytest.raises(ProviderError) as error:
        analyze_openai("small test", Settings(), client_factory=lambda **kwargs: client)
    assert error.value.category == "incomplete_response"
    assert error.value.diagnostic.incomplete_reason == "max_output_tokens"


@pytest.mark.parametrize(
    ("raised", "category", "exception_class"),
    [
        (APITimeoutError(request=httpx.Request("POST", "https://api.openai.com/v1/responses")), "timeout", "APITimeoutError"),
        (APIConnectionError(message="connection", request=httpx.Request("POST", "https://api.openai.com/v1/responses")), "network", "APIConnectionError"),
        (APIStatusError("status", response=httpx.Response(502, request=httpx.Request("POST", "https://api.openai.com/v1/responses")), body=None), "api_status", "APIStatusError"),
        (RuntimeError("unexpected"), "internal_error", "RuntimeError"),
    ],
)
def test_provider_error_categories_remain_distinct(monkeypatch: pytest.MonkeyPatch, raised: Exception, category: str, exception_class: str) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "present-for-test-only")

    def factory(**kwargs):
        raise raised

    with pytest.raises(ProviderError) as error:
        analyze_openai("small test", Settings(), client_factory=factory)
    assert error.value.category == category
    assert error.value.exception_class == exception_class
    assert error.value.diagnostic.provider_stage == "client_construction"
