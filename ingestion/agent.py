import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from google.adk.agents import LlmAgent
from dotenv import load_dotenv

# Local imports
from .prompt import (
    get_ingestion_system_prompt,
    build_user_prompt,
    build_startup_info_text,
)

# Ensure project root on path for VC_Analyst imports, mirroring other agents
_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[1]  # repo root
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from VC_Analyst.adk_agents.common_llm import call_llm_json

# Load local ingestion .env (contains EXA_API_KEY) without affecting repo
_ENV_PATH = Path(__file__).resolve().parent / ".env"
try:
    load_dotenv(dotenv_path=str(_ENV_PATH))
except Exception:
    # Safe to ignore; the agent will fallback to environment
    pass


def _exa_search(query: str, num_results: int = 6) -> List[Dict[str, Any]]:
    """
    Fetch web results using Exa if available; otherwise, return an empty list.

    Env:
    - EXA_API_KEY: API key for Exa

    The implementation prefers the official exa client. We guard imports so the
    code runs even if the dependency is not installed.
    """
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        return []

    # Try both package names for broader compatibility
    try:
        # exa-py client
        from exa_py import Exa  # type: ignore

        client = Exa(api_key=api_key)
        # Preferred: search with content summaries
        resp = client.search_and_contents(
            query,
            type="neural",
            use_autoprompt=True,
            num_results=num_results,
            contents={"summary": "auto", "highlights": True},
        )
        items = []
        for r in resp.results or []:
            summary_text = None
            if r.contents:
                # Collect summary or first content block
                for c in r.contents:
                    summary_text = (
                        (c.get("summary") if isinstance(c, dict) else None)
                        or (c.get("text") if isinstance(c, dict) else None)
                    )
                    if summary_text:
                        break
            title_val = getattr(r, "title", None)
            url_val = getattr(r, "url", None)
            if title_val is None and isinstance(r, dict):
                title_val = r.get("title")
            if url_val is None and isinstance(r, dict):
                url_val = r.get("url")
            items.append({"title": title_val, "url": url_val, "content": summary_text})
        return items
    except Exception:
        pass

    try:
        # Alternate package name (future-proof)
        import exa  # type: ignore

        client = exa.Exa(api_key=api_key)
        resp = client.search_and_contents(
            query,
            type="neural",
            use_autoprompt=True,
            num_results=num_results,
            contents={"summary": "auto", "highlights": True},
        )
        items = []
        for r in getattr(resp, "results", []) or []:
            summary_text = None
            for c in getattr(r, "contents", []) or []:
                if isinstance(c, dict):
                    summary_text = c.get("summary") or c.get("text")
                if summary_text:
                    break
            items.append(
                {
                    "title": getattr(r, "title", None),
                    "url": getattr(r, "url", None),
                    "content": summary_text,
                }
            )
        return items
    except Exception:
        return []


def deep_research(query: str) -> Dict[str, Any]:
    """
    Perform deep research with Exa, then use an LLM to extract structured fields
    that the VC_Analyst expects. Returns both structured JSON and a synthesized
    `startup_info_str` suitable for downstream parse_record.
    """
    snippets = _exa_search(query)

    system_prompt = get_ingestion_system_prompt()
    user_prompt = build_user_prompt(query, snippets)
    structured = call_llm_json(system_prompt, user_prompt)

    # Normalize citations shape
    citations: List[Dict[str, str]] = []
    for sn in snippets:
        title = (sn.get("title") or "Source").strip()
        url = (sn.get("url") or "").strip()
        if url:
            citations.append({"title": title, "url": url})

    if isinstance(structured, dict):
        if "citations" not in structured or not structured.get("citations"):
            structured["citations"] = citations
    else:
        structured = {"analysis": structured, "citations": citations}

    startup_info_str = build_startup_info_text(structured)

    return {
        "query": query,
        "structured": structured,
        "startup_info_str": startup_info_str,
        "sources": citations,
    }


def ingest_for_vc_analyst(query: str) -> Dict[str, Any]:
    """ADK tool: Given a query (startup name, domain, or description),
    perform Exa-powered research and return the downstream-ready payload.

    Returns JSON with keys: startup_info_str, structured, sources.
    """
    return deep_research(query)


root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-5"),
    name="IngestionAgent",
    description="Deep-researches startups using Exa and prepares VC_Analyst-ready inputs.",
    instruction=(
        "Use the ingest_for_vc_analyst tool to gather web evidence and produce a "
        "concise, structured startup summary."
    ),
    tools=[ingest_for_vc_analyst],
)


