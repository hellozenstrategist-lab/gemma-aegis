"""Cerebras/Gemma provider wrapper and optional OpenAI-compatible baseline client."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .metrics import extract_metrics, redact_secrets

DEFAULT_MODEL = "gemma-4-31b"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_SYSTEM_PROMPT = """You are a fast enterprise security triage copilot.
Given screenshots, logs, stack traces, or repo snippets, return:
1. Situation summary
2. Likely severity / blast radius
3. Immediate action
4. Evidence to collect next
Keep answers demo-friendly and concise."""


def load_project_env(path: str | Path = DEFAULT_ENV_PATH, *, override: bool = False) -> dict[str, str]:
    """Load simple KEY=VALUE pairs from a local .env file without printing secrets."""
    env_path = Path(path)
    loaded: dict[str, str] = {}
    if not env_path.exists():
        return loaded
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return redact_secrets(loaded)


@dataclass
class ProviderResult:
    provider: str
    model: str
    output: str
    metrics: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return redact_secrets(
            {
                "provider": self.provider,
                "model": self.model,
                "output": self.output,
                "metrics": self.metrics,
                "error": self.error,
            }
        )


def build_messages(
    prompt: str,
    *,
    image_url: str | None = None,
    image_data_uri: str | None = None,
    system_prompt: str | None = None,
) -> list[dict[str, Any]]:
    """Build OpenAI-compatible chat messages with optional multimodal image content."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("prompt is required")
    if image_url and image_data_uri:
        raise ValueError("provide only one image source: image_url or image_data_uri")

    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    image_source = image_data_uri or image_url
    if image_source:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_source}},
                ],
            }
        )
    else:
        messages.append({"role": "user", "content": prompt})
    return messages


def _completion_text(completion: Any) -> str:
    choices = getattr(completion, "choices", None)
    if choices is None and isinstance(completion, dict):
        choices = completion.get("choices")
    if not choices:
        return ""
    first = choices[0]
    message = getattr(first, "message", None)
    if message is None and isinstance(first, dict):
        message = first.get("message")
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    return content or ""


def call_cerebras(
    prompt: str,
    *,
    image_url: str | None = None,
    image_data_uri: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    reasoning_effort: str = "none",
    max_completion_tokens: int = 768,
    temperature: float = 0.2,
    top_p: float = 1.0,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> ProviderResult:
    """Call Gemma 4 on Cerebras and return text plus timing/token metrics."""
    from cerebras.cloud.sdk import Cerebras

    load_project_env()
    key = api_key or os.environ.get("CEREBRAS_API_KEY")
    chosen_model = model or os.environ.get("CEREBRAS_MODEL", DEFAULT_MODEL)
    if not key:
        return ProviderResult("cerebras", chosen_model, "", {}, "CEREBRAS_API_KEY is not set")

    messages = build_messages(prompt, image_url=image_url, image_data_uri=image_data_uri, system_prompt=system_prompt)
    client = Cerebras(api_key=key)
    start = time.perf_counter()
    try:
        request: dict[str, Any] = {
            "messages": messages,
            "model": chosen_model,
            "max_completion_tokens": max_completion_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }
        if reasoning_effort != "none":
            request["reasoning_effort"] = reasoning_effort
        completion = client.chat.completions.create(**request)
        wall_ms = (time.perf_counter() - start) * 1000
        return ProviderResult("cerebras", chosen_model, _completion_text(completion), extract_metrics(completion, wall_ms=wall_ms))
    except Exception as exc:
        wall_ms = (time.perf_counter() - start) * 1000
        return ProviderResult("cerebras", chosen_model, "", {"wall_ms": round(wall_ms, 3)}, f"{type(exc).__name__}: {exc}")


def call_openai_compatible_baseline(
    prompt: str,
    *,
    image_url: str | None = None,
    image_data_uri: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    max_completion_tokens: int = 768,
    temperature: float = 0.2,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> ProviderResult:
    """Optional baseline for side-by-side speed proof using any OpenAI-compatible provider."""
    load_project_env()
    endpoint = (base_url or os.environ.get("BASELINE_OPENAI_BASE_URL") or "").rstrip("/")
    key = api_key or os.environ.get("BASELINE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    chosen_model = model or os.environ.get("BASELINE_MODEL") or "baseline-model"
    if not endpoint or not key or chosen_model == "baseline-model":
        return ProviderResult("baseline", chosen_model, "", {}, "Set BASELINE_OPENAI_BASE_URL, BASELINE_OPENAI_API_KEY, and BASELINE_MODEL to enable baseline comparison")

    messages = build_messages(prompt, image_url=image_url, image_data_uri=image_data_uri, system_prompt=system_prompt)
    body = {
        "model": chosen_model,
        "messages": messages,
        "max_tokens": max_completion_tokens,
        "temperature": temperature,
        "stream": False,
    }
    req = urllib.request.Request(
        f"{endpoint}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            parsed = json.loads(resp.read().decode("utf-8", "replace"))
        wall_ms = (time.perf_counter() - start) * 1000
        output = parsed.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ProviderResult("baseline", chosen_model, output, extract_metrics(parsed, wall_ms=wall_ms))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        wall_ms = (time.perf_counter() - start) * 1000
        return ProviderResult("baseline", chosen_model, "", {"wall_ms": round(wall_ms, 3)}, f"{type(exc).__name__}: {exc}")
