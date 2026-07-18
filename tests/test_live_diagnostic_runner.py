import json
from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError

from diagnostics.run_live_provider_diagnostic import run_once


VALID_JSON = json.dumps({
    "pal": {"summary": "s", "findings": []},
    "pecan": {"summary": "s", "findings": []},
    "pea": {"summary": "s", "findings": []},
    "seed": {"summary": "s", "findings": []},
    "trace": [],
})


def client_for(response: object):
    raw = SimpleNamespace(status_code=200, headers={"x-request-id": "req_mock"}, parse=lambda: response)
    return lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=lambda **params: raw)))


def response_for(output_text: str, status: str = "completed"):
    return SimpleNamespace(id="resp_mock", model="gpt-5.6-sol", status=status, output_text=output_text, usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15), output=[])


@pytest.mark.parametrize(
    ("output_text", "success", "code"),
    [(VALID_JSON, True, None), ("not json", False, "invalid_json"), ("{}", False, "pydantic_validation")],
)
def test_runner_persists_mock_output(tmp_path, output_text, success, code) -> None:
    result_path = tmp_path / "nested" / "p-gates-live-result.json"
    progress_path = tmp_path / "nested" / "p-gates-live-progress.log"
    exit_code, result = run_once(client_for(response_for(output_text)), result_path, progress_path)
    assert result_path.resolve() == (tmp_path / "nested" / "p-gates-live-result.json").resolve()
    assert json.loads(result_path.read_text(encoding="utf-8")) == result
    assert progress_path.exists()
    assert "diagnostic_write_complete" in progress_path.read_text(encoding="utf-8")
    assert exit_code == (0 if success else 1)
    assert result["safe_error_code"] == code


@pytest.mark.parametrize("error", [
    APITimeoutError(request=httpx.Request("POST", "https://api.openai.com/v1/responses")),
    APIConnectionError(message="connection", request=httpx.Request("POST", "https://api.openai.com/v1/responses")),
    APIStatusError("status", response=httpx.Response(503, request=httpx.Request("POST", "https://api.openai.com/v1/responses")), body=None),
    RuntimeError("unexpected"),
])
def test_runner_persists_exception_cases(tmp_path, error) -> None:
    def factory(**kwargs):
        raise error

    result_path = tmp_path / "result.json"
    progress_path = tmp_path / "progress.log"
    exit_code, result = run_once(factory, result_path, progress_path)
    assert exit_code == 1
    assert result_path.exists()
    assert json.loads(result_path.read_text(encoding="utf-8"))["exception_class"] == type(error).__name__


def test_runner_persists_before_reraising_interrupt(tmp_path) -> None:
    result_path = tmp_path / "result.json"
    progress_path = tmp_path / "progress.log"

    def factory(**kwargs):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_once(factory, result_path, progress_path)
    assert result_path.exists()
    assert json.loads(result_path.read_text(encoding="utf-8"))["safe_error_code"] == "interrupted"
