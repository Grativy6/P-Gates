"""One-shot browser-endpoint equivalent export helper; do not commit generated exports."""

import json
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "p-gates-first-live-report.json"
MARKDOWN_PATH = ROOT / "p-gates-first-live-report.md"
BASE_URL = "http://127.0.0.1:8000"


def markdown(report: dict[str, object]) -> str:
    lines = ["# P-Gates live route analysis", "", f"Provider: {report['provider']}", f"Model: {report['model_identifier']}", f"Timestamp: {report['analysis_timestamp']}", ""]
    for name in ("pal", "pecan", "pea", "seed"):
        panel = report[name]
        lines.extend([f"## {name.upper()}", "", panel["summary"], ""])
        for finding in panel["findings"]:
            lines.extend([f"- **{finding['category']}** — {finding['phrase']}", f"  - Issue: {finding['issue']}", f"  - Safer wording: {finding['safer_wording']}"])
        lines.append("")
    lines.extend(["## Phrase-level trace", ""])
    for item in report["trace"]:
        lines.extend([f"- **{item['layer']}** — {item['original_phrase']}", f"  - Problem: {item['detected_problem']}", f"  - Safer wording: {item['safer_wording']}"])
    lines.extend(["", f"> {report['disclaimer']}", ""])
    return "\n".join(lines)


def main() -> int:
    with httpx.Client(timeout=90.0) as client:
        example = client.get(f"{BASE_URL}/api/example")
        example.raise_for_status()
        response = client.post(f"{BASE_URL}/api/analyze", json={"source_text": example.json()["source_text"], "provider": "openai"})
    if response.status_code != 200:
        detail = response.json().get("detail", {})
        print(json.dumps({"http_status": response.status_code, "success": False, "safe_error_category": detail.get("category")}, indent=2))
        return 1
    report = response.json()
    JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    MARKDOWN_PATH.write_text(markdown(report), encoding="utf-8")
    diagnostic = report.get("live_diagnostic") or {}
    print(json.dumps({"http_status": 200, "success": True, "requested_model": diagnostic.get("requested_model"), "returned_model": diagnostic.get("returned_model"), "response_status": diagnostic.get("response_status"), "json_valid": diagnostic.get("output_shape") is not None and not diagnostic.get("output_shape", "").startswith("non-JSON"), "pydantic_validation": not diagnostic.get("validation_errors"), "token_usage": report.get("usage"), "panels": {name: bool(report.get(name)) for name in ("pal", "pecan", "pea", "seed")}, "trace_present": bool(report.get("trace"))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
