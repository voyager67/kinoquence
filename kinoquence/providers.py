from __future__ import annotations

import ipaddress
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class ProviderError(RuntimeError):
    """A safe, user-facing provider configuration or request error."""


@dataclass
class ProviderConfig:
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    timeout: int = 180
    max_tokens: int = 5000
    temperature: float = 0.35


DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "xai": "https://api.x.ai/v1",
    "ollama": "http://localhost:11434/v1",
    "lmstudio": "http://localhost:1234/v1",
    "vllm": "http://localhost:8000/v1",
    "llamacpp": "http://localhost:8080/v1",
}

KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    "lmstudio": "LMSTUDIO_API_KEY",
    "vllm": "VLLM_API_KEY",
    "llamacpp": "LLAMACPP_API_KEY",
    "openai-compatible": "OPENAI_API_KEY",
}

MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward credentials to a redirect target, even across hosts."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_config(config: ProviderConfig, provider: str) -> None:
    if provider not in {*DEFAULT_BASE_URLS, "openai-compatible", "anthropic", "gemini"}:
        supported = ", ".join([*DEFAULT_BASE_URLS.keys(), "openai-compatible", "anthropic", "gemini"])
        raise ProviderError(f"Unknown provider {provider!r}. Supported adapters: {supported}")
    if not isinstance(config.model, str) or not config.model.strip() or len(config.model) > 200:
        raise ProviderError("Model name must be a non-empty string no longer than 200 characters")
    if not isinstance(config.timeout, int) or isinstance(config.timeout, bool) or not 1 <= config.timeout <= 600:
        raise ProviderError("Timeout must be a whole number from 1 to 600 seconds")
    if not isinstance(config.max_tokens, int) or isinstance(config.max_tokens, bool) or not 1 <= config.max_tokens <= 1_000_000:
        raise ProviderError("Max tokens must be a whole number from 1 to 1,000,000")
    if not isinstance(config.temperature, (int, float)) or isinstance(config.temperature, bool) or not 0 <= config.temperature <= 2:
        raise ProviderError("Temperature must be between 0 and 2")
    if config.api_key is not None and not isinstance(config.api_key, str):
        raise ProviderError("API key must be supplied as a string")


def _safe_base_url(base_url: str, api_key: str | None) -> str:
    if not isinstance(base_url, str) or not base_url.strip():
        raise ProviderError("Provider base URL must be a non-empty URL string")
    if any(ord(char) <= 32 or ord(char) == 127 for char in base_url):
        raise ProviderError("Provider base URL must not contain whitespace or control characters")
    try:
        parsed = urllib.parse.urlsplit(base_url)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ProviderError("Provider base URL is malformed") from exc
    if parsed.scheme not in {"http", "https"} or not host or parsed.username is not None or parsed.password is not None:
        raise ProviderError("Provider base URL must be an http(s) URL without embedded credentials")
    if parsed.query or parsed.fragment:
        raise ProviderError("Provider base URL must not contain a query string or fragment")
    if port is not None and not 1 <= port <= 65535:
        raise ProviderError("Provider base URL contains an invalid port")
    if api_key and parsed.scheme != "https":
        is_loopback = host.lower() == "localhost" or host.lower().endswith(".localhost")
        if not is_loopback:
            try:
                is_loopback = ipaddress.ip_address(host).is_loopback
            except ValueError:
                is_loopback = False
        if not is_loopback:
            raise ProviderError("Refusing to send an API key over plain HTTP; use HTTPS or a loopback local server")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


def _request_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            raw_bytes = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Do not echo the response body: provider errors can contain prompt data or reflected credentials.
        raise ProviderError(f"Provider returned HTTP {exc.code}; response content was not logged") from None
    except urllib.error.URLError:
        # Do not echo exception reasons or request URLs; some APIs put credentials in URLs.
        raise ProviderError("Could not reach provider endpoint (network, DNS or TLS error)") from None
    except (TimeoutError, OSError):
        raise ProviderError(f"Provider request failed or timed out after {timeout}s") from None
    if len(raw_bytes) > MAX_RESPONSE_BYTES:
        raise ProviderError(f"Provider response exceeded the {MAX_RESPONSE_BYTES // (1024 * 1024)} MiB safety limit")
    try:
        raw = raw_bytes.decode("utf-8")
        result = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProviderError("Provider returned an invalid UTF-8 JSON response") from None
    if not isinstance(result, dict):
        raise ProviderError("Provider response was not a JSON object")
    return result


def _extract_openai(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("OpenAI-compatible response did not contain choices[0].message.content") from exc
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        text = "\n".join(part for part in parts if isinstance(part, str) and part)
        if text:
            return text
    raise ProviderError("Provider response content had an unsupported shape")


def _extract_anthropic(data: dict[str, Any]) -> str:
    blocks = data.get("content")
    if not isinstance(blocks, list):
        raise ProviderError("Anthropic response did not contain a content array")
    text = "\n".join(item.get("text", "") for item in blocks if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str))
    if not text:
        raise ProviderError("Anthropic returned no text content")
    return text


def _extract_gemini(data: dict[str, Any]) -> str:
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        # Provider error text is intentionally omitted to avoid accidental data disclosure.
        raise ProviderError("Gemini response did not contain candidates[0].content.parts") from None
    if not isinstance(parts, list):
        raise ProviderError("Gemini response parts were not an array")
    text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict) and isinstance(part.get("text"), str))
    if not text:
        raise ProviderError("Gemini returned no text content")
    return text


def generate_text(config: ProviderConfig, system_prompt: str, user_prompt: str) -> str:
    if not isinstance(config.provider, str):
        raise ProviderError("Provider name must be a string")
    provider = config.provider.lower().strip()
    _validate_config(config, provider)
    if not isinstance(system_prompt, str) or not isinstance(user_prompt, str):
        raise ProviderError("System and user prompts must be strings")

    api_key = (config.api_key or os.getenv(KEY_ENV.get(provider, ""), "")).strip()
    # Prevent header injection and avoid leaking malformed values through low-level HTTP errors.
    if len(api_key) > 4096 or any(ord(char) < 32 or ord(char) == 127 for char in api_key):
        raise ProviderError("API key contains unsupported control characters or exceeds the 4096-character safety limit")
    if provider in DEFAULT_BASE_URLS or provider == "openai-compatible":
        base = config.base_url or DEFAULT_BASE_URLS.get(provider) or os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")
        if not base:
            raise ProviderError("OpenAI-compatible provider requires --base-url or OPENAI_COMPATIBLE_BASE_URL")
        base = _safe_base_url(base, api_key)
        headers = {"User-Agent": "Kinoquence/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        response = _request_json(f"{base}/chat/completions", headers, payload, config.timeout)
        return _extract_openai(response)

    if provider == "anthropic":
        if not api_key:
            raise ProviderError("Set ANTHROPIC_API_KEY (or the environment variable selected by --api-key-env)")
        base = _safe_base_url(config.base_url or "https://api.anthropic.com", api_key)
        payload = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        response = _request_json(
            f"{base}/v1/messages",
            {"x-api-key": api_key, "anthropic-version": "2023-06-01", "User-Agent": "Kinoquence/1.0"},
            payload,
            config.timeout,
        )
        return _extract_anthropic(response)

    if provider == "gemini":
        if not api_key:
            raise ProviderError("Set GEMINI_API_KEY (or the environment variable selected by --api-key-env)")
        base = _safe_base_url(config.base_url or "https://generativelanguage.googleapis.com/v1beta", api_key)
        model = urllib.parse.quote(config.model, safe="-_.")
        url = f"{base}/models/{model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": config.temperature, "maxOutputTokens": config.max_tokens},
        }
        response = _request_json(url, {"x-goog-api-key": api_key, "User-Agent": "Kinoquence/1.0"}, payload, config.timeout)
        return _extract_gemini(response)

    # _validate_config rejects this branch; keep a defensive error for type checkers and future adapters.
    raise ProviderError(f"Provider adapter {provider!r} is not implemented")


def default_key_env(provider: str) -> str | None:
    return KEY_ENV.get(provider.lower())
