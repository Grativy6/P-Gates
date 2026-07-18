from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=20_000)
    provider: Literal["mock", "openai"] = "mock"


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: str
    phrase: str
    issue: str
    safer_wording: str


class Panel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    findings: list[Finding]


class TraceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original_phrase: str
    detected_problem: str
    safer_wording: str
    layer: str


class Usage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ModelAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pal: Panel
    pecan: Panel
    pea: Panel
    seed: Panel
    trace: list[TraceItem]


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: str
    message: str
    error_type: str


class LiveDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str | None = None
    response_id: str | None = None
    http_status: int | None = None
    response_status: str | None = None
    requested_model: str
    returned_model: str | None = None
    output_shape: str | None = None
    validation_errors: list[ValidationIssue] = Field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    incomplete_reason: str | None = None
    refusal: str | None = None
    provider_stage: str | None = None


class AnalysisResult(BaseModel):
    source_text: str
    analysis_timestamp: datetime
    provider: str = "mock"
    model_identifier: str = "deterministic-demo-rules-v0.1"
    framework_manifest_version: str = "0.1.0"
    pal: Panel
    pecan: Panel
    pea: Panel
    seed: Panel
    trace: list[TraceItem]
    disclaimer: str
    usage: Usage | None = None
    live_diagnostic: LiveDiagnostic | None = None
