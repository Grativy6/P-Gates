import json
import os
from pathlib import Path

from app.providers import ProviderError


RESULT_PATH = Path(__file__).resolve().parents[1] / "diagnostics" / "p-gates-provider-path-result.json"


def write_provider_failure(error: ProviderError) -> None:
    diagnostic = error.diagnostic
    payload = {
        "exception_class": error.exception_class,
        "safe_error_code": error.safe_error_code or error.category,
        "safe_error_message": error.public_message,
        "http_status": diagnostic.http_status if diagnostic else None,
        "request_id": diagnostic.request_id if diagnostic else None,
        "provider_stage": diagnostic.provider_stage if diagnostic else None,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = RESULT_PATH.with_suffix(RESULT_PATH.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary_path, RESULT_PATH)
