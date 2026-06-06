# File: src/llm/targets.py
# Purpose: resolve a ModelTarget from the environment -- the ONE place the
# "Turbo if a key is set, else local Ollama" convention lives.
#
# Callers pass the model name(s) they want as defaults; this picks the backend
# (URL + auth) based on whether a Turbo key is present. An explicit per-job model
# is honored by passing the same name for both backends -- see turbo_or_local().

from __future__ import annotations

import os

from .client import ModelTarget


def turbo_or_local(model_turbo: str, model_local: str = "tinyllama:latest") -> ModelTarget:
    """Pick the backend by presence of BH_OLLAMA_KEY; use the given model on it.

    Turbo:  BH_OLLAMA_KEY set -> OLLAMA_TURBO_URL (default https://ollama.com), Bearer auth.
    Local:  no key            -> OLLAMA_URL       (default http://ollama:11434), no auth.

    Model selection is the CALLER'S to make (the recipe owns its default model):
      turbo_or_local(BIO_MODEL, LOCAL_MODEL)   # current default behavior
      turbo_or_local(override, override)        # explicit per-job model on either backend
    """
    key = os.getenv("BH_OLLAMA_KEY", "")
    if key:
        return ModelTarget(
            model=model_turbo,
            base_url=os.getenv("OLLAMA_TURBO_URL", "https://ollama.com"),
            api_key=key,
        )
    return ModelTarget(
        model=model_local,
        base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
    )
