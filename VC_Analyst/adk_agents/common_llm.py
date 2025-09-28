import json
import os
import hashlib
import threading
from pathlib import Path
from time import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI


_memory_cache: Dict[str, Dict[str, Any]] = {}
_memory_cache_lock = threading.Lock()


def _get_env_float(name: str) -> Optional[float]:
    val = os.environ.get(name)
    if val is None:
        return None
    try:
        return float(val)
    except Exception:
        return None


def _cache_dir() -> Optional[Path]:
    """Return the cache directory if caching is enabled, else None.

    Controlled by env var ADK_CACHE_DIR. If not set, defaults to ".adk_cache" in CWD.
    Set ADK_DISABLE_CACHE=1 to disable on-disk caching.
    """
    if os.environ.get("ADK_DISABLE_CACHE") == "1":
        return None
    base = os.environ.get("ADK_CACHE_DIR")
    if base:
        return Path(base)
    # Fallback to current working directory .adk_cache
    return Path.cwd() / ".adk_cache"


def _make_cache_key(model: str, system_prompt: str, user_prompt: str, temperature: Optional[float]) -> str:
    temp_part = "" if temperature is None else f"|t={temperature:.4f}"
    payload = f"m={model}{temp_part}\nS:\n{system_prompt}\nU:\n{user_prompt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_read(key: str, ttl_seconds: float) -> Optional[Dict[str, Any]]:
    # Memory cache first
    with _memory_cache_lock:
        item = _memory_cache.get(key)
        if item is not None:
            return item

    cache_base = _cache_dir()
    if not cache_base:
        return None
    try:
        cache_base.mkdir(parents=True, exist_ok=True)
        path = cache_base / f"{key}.json"
        if not path.exists():
            return None
        # TTL via mtime
        if ttl_seconds > 0 and (time() - path.stat().st_mtime) > ttl_seconds:
            return None
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        # Populate memory cache for faster subsequent reads
        with _memory_cache_lock:
            _memory_cache[key] = data
        return data
    except Exception:
        return None


def _cache_write(key: str, data: Dict[str, Any]) -> None:
    with _memory_cache_lock:
        _memory_cache[key] = data
    cache_base = _cache_dir()
    if not cache_base:
        return
    try:
        cache_base.mkdir(parents=True, exist_ok=True)
        path = cache_base / f"{key}.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        # Best-effort cache; ignore failures
        pass


def call_llm_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Call OpenAI chat with JSON response_format and return parsed dict.

    Behavior:
    - If TEST_LLM_RESPONSE env var is set, return it (parsed) without network calls.
    - If no OPENAI_API_KEY is configured, return a minimal offline response.
    - Otherwise, call OpenAI with JSON response_format.
    """
    # Load .env only once per process
    load_dotenv()

    # Test/offline short-circuit for unit tests and local runs
    test_payload = os.environ.get("TEST_LLM_RESPONSE")
    if test_payload:
        try:
            return json.loads(test_payload)
        except Exception:
            return {"analysis": test_payload}

    model = os.environ.get("ADK_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-5"

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Offline fallback to keep demos from crashing in environments without keys
        return {
            "analysis": "LLM offline: set OPENAI_API_KEY or TEST_LLM_RESPONSE to enable full outputs.",
            "model": model,
        }

    client = OpenAI(api_key=api_key)
    # Build request with optional temperature (opt-in via env). Some models do not
    # support overriding temperature. We will retry without temperature if the API
    # rejects it.
    request_kwargs = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    # Respect env overrides for temperature, but do not set a default here
    # to maximize compatibility across models.
    env_temp = os.environ.get("ADK_TEMPERATURE") or os.environ.get("OPENAI_TEMPERATURE")
    temperature: Optional[float] = None
    if env_temp is not None:
        try:
            temperature = float(env_temp)
            request_kwargs["temperature"] = temperature
        except Exception:
            # Ignore invalid temperature values
            temperature = None

    # Caching
    ttl = _get_env_float("ADK_CACHE_TTL") or 24 * 3600.0
    cache_key = _make_cache_key(model, system_prompt, user_prompt, temperature)
    cached = _cache_read(cache_key, ttl)
    if cached is not None:
        return cached

    timeout = _get_env_float("ADK_HTTP_TIMEOUT") or 60.0

    # Retry with minimal backoff on transient errors
    max_retries = int(os.environ.get("ADK_LLM_MAX_RETRIES", "2"))
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(timeout=timeout, **request_kwargs)
            text = resp.choices[0].message.content or "{}"
            try:
                data = json.loads(text)
            except Exception:
                data = {"analysis": text}
            _cache_write(cache_key, data)
            return data
        except Exception as e:
            err_text = str(e)
            # Retry once without temperature if unsupported
            if attempt == 0 and "temperature" in request_kwargs and "Unsupported value" in err_text:
                request_kwargs.pop("temperature", None)
                temperature = None
                continue
            last_err = e
    # If all retries failed, re-raise last error
    if last_err:
        raise last_err
    # Fallback (should not reach here)
    return {"analysis": "Unknown error"}


def reduce_redundancy_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use an LLM to reduce repetition and verbosity in a JSON analysis object while
    preserving its structure, keys, and non-string values. This is a safe
    post-processing step intended to make narrative fields more concise.

    Controlled by env var ADK_DEDUP_JSON (set to "0" to disable). If the LLM is
    unavailable or returns an incompatible structure, the original data is
    returned unchanged.
    """
    try:
        if os.environ.get("ADK_DEDUP_JSON", "1") == "0":
            return data

        # Prepare prompts. Instruct the model to keep structure and only tighten strings.
        system = (
            "You are a meticulous JSON editor. Remove redundant phrases, repeated points, "
            "and verbosity ONLY inside string values. Rules:\n"
            "- Return a JSON object with IDENTICAL keys and structure as the input.\n"
            "- Do NOT add or remove keys.\n"
            "- Keep arrays and objects the same shape and order.\n"
            "- Keep numbers/booleans/null unchanged.\n"
            "- Preserve meaning and factual content; do not invent new content.\n"
            "- Respond with valid JSON only."
        )
        # Use a stable serialized snapshot for the user message
        user = (
            "Tighten and de-duplicate the following JSON while preserving exact structure:\n\n"
            f"{json.dumps(data, ensure_ascii=False)}"
        )

        cleaned = call_llm_json(system, user)

        # Basic sanity check: preserve top-level keys
        if isinstance(cleaned, dict) and set(cleaned.keys()) == set(data.keys()):
            return cleaned
    except Exception:
        # Best-effort; on any error, fall back to original
        pass
    return data
