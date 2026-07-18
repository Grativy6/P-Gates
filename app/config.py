import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_model: str = os.getenv("P_GATES_OPENAI_MODEL", "gpt-5.6")
    timeout_seconds: float = float(os.getenv("P_GATES_OPENAI_TIMEOUT_SECONDS", "60"))
    max_output_tokens: int = int(os.getenv("P_GATES_OPENAI_MAX_OUTPUT_TOKENS", "1800"))


def has_openai_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())
