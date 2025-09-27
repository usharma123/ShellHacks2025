import json
import os
from typing import Any, Dict

from openai import OpenAI


def call_llm_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Call OpenAI chat with JSON response_format and return parsed dict.

    Falls back to returning {"analysis": text} if JSON parse fails.
    Uses model from ADK_MODEL or OPENAI_MODEL env vars, defaults to gpt-4o-mini.
    """
    model = os.environ.get("ADK_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )
    text = resp.choices[0].message.content or "{}"
    try:
        return json.loads(text)
    except Exception:
        return {"analysis": text}
