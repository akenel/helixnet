# src/llm -- the app's single LLM entry point.
# Import from here, not from .client / .targets directly.
from .client import LLMResult, ModelTarget, run_llm
from .targets import turbo_or_local

__all__ = ["run_llm", "ModelTarget", "LLMResult", "turbo_or_local"]
