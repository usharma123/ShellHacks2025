import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI


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
    if env_temp is not None:
        try:
            request_kwargs["temperature"] = float(env_temp)
        except Exception:
            # Ignore invalid temperature values
            pass

    try:
        resp = client.chat.completions.create(**request_kwargs)
    except Exception as e:
        err_text = str(e)
        if "temperature" in request_kwargs and "Unsupported value" in err_text:
            # Retry without temperature for models that don't support it
            request_kwargs.pop("temperature", None)
            resp = client.chat.completions.create(**request_kwargs)
        else:
            raise
    text = resp.choices[0].message.content or "{}"
    try:
        return json.loads(text)
    except Exception:
        return {"analysis": text}
