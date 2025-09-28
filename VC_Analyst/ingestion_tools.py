import os
import re
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

# LLM JSON helper
from adk_agents.common_llm import call_llm_json


# Load environment variables for EXA_API_KEY and OPENAI_API_KEY
try:
    load_dotenv()
except Exception:
    pass


def _exa_search_rich(query: str, num_results: int = 6, max_chars: int = 1800, summary_query: Optional[str] = None) -> List[Dict[str, Any]]:
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        return []
    try:
        from exa_py import Exa  # type: ignore

        client = Exa(api_key=api_key)
        kwargs: Dict[str, Any] = {
            "type": "auto",
            "use_autoprompt": True,
            "num_results": num_results,
            "text": {"max_characters": max_chars},
        }
        if summary_query:
            kwargs["summary"] = {"query": summary_query}
        resp = client.search_and_contents(query, **kwargs)
        items: List[Dict[str, Any]] = []
        for r in getattr(resp, "results", []) or []:
            title = getattr(r, "title", None)
            url = getattr(r, "url", None)
            text_val = None
            summary_val = None
            for c in getattr(r, "contents", []) or []:
                if isinstance(c, dict):
                    text_val = text_val or c.get("text")
                    summary_val = summary_val or c.get("summary")
                if text_val and summary_val:
                    break
            items.append({"title": title, "url": url, "text": text_val, "summary": summary_val})
        return items
    except Exception:
        return []


def _render_snippets(query: str, snippets: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("Research target (query):")
    lines.append(query)
    lines.append("")
    lines.append("Web snippets (title, url, excerpt):")
    for i, sn in enumerate(snippets, start=1):
        title = sn.get("title") or "Untitled"
        url = sn.get("url") or ""
        content = sn.get("summary") or sn.get("text") or ""
        if isinstance(content, dict):
            content = content.get("text") or content.get("value") or ""
        excerpt = (content or "").strip().replace("\n", " ")
        if len(excerpt) > 1500:
            excerpt = excerpt[:1500] + "..."
        lines.append(f"[{i}] {title} | {url}\n{excerpt}")
        lines.append("")
    lines.append("\nExtract the JSON now.")
    return "\n".join(lines)


def _citations_from(snippets: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    cites: List[Dict[str, str]] = []
    for sn in snippets:
        t = (sn.get("title") or "Source").strip()
        u = (sn.get("url") or "").strip()
        if u:
            cites.append({"title": t, "url": u})
    return cites


# ---------------- Attribute-specific Exa searches -----------------

def _exa_chat_text(user_prompt: str) -> Optional[str]:
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(base_url="https://api.exa.ai", api_key=api_key)
        resp = client.chat.completions.create(
            model="exa",
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = (getattr(resp.choices[0].message, "content", None) or "").strip()
        return text or None
    except Exception:
        return None

def _exa_chat_founder_names(company: str) -> Optional[List[str]]:
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(base_url="https://api.exa.ai", api_key=api_key)
        system = (
            "You extract only founder names. Return a comma-separated list with no extra words. "
            "If unknown, return an empty string."
        )
        prompt = f"Who are the founders of {company}?"
        resp = client.chat.completions.create(
            model="exa",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        text = (getattr(resp.choices[0].message, "content", None) or "").strip()
        if not text:
            return None
        # Normalize common formats: bullets, newlines, "and", colons
        cleaned = text
        cleaned = re.sub(r"(?i)^founders?:\s*", "", cleaned).strip()
        cleaned = cleaned.replace("•", ", ").replace("- ", "")
        cleaned = cleaned.replace("\n", ", ")
        cleaned = re.sub(r"\s+and\s+", ", ", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace(";", ",")
        # Split and filter
        parts = [t.strip() for t in cleaned.split(",")]
        tokens: List[str] = []
        for p in parts:
            if not p:
                continue
            # Drop trailing roles like (CEO) or descriptors after ' - '
            p = re.sub(r"\s*\([^)]*\)$", "", p).strip()
            p = p.split(" - ")[0].strip()
            # Basic sanity: should contain a letter and typically at least 2 tokens for a name
            if not re.search(r"[A-Za-z]", p):
                continue
            if len(p) < 2:
                continue
            tokens.append(p)
        names = [n for n in tokens if n.lower() not in ("unknown", "n/a", "none")]
        names = [p for p in parts if p.lower() not in ("unknown", "n/a", "none")]
        return names or None
    except Exception:
        return None

def exa_attr_name(query: str) -> Dict[str, Any]:
    snippets = _exa_search_rich(query, num_results=6, summary_query="One-line company name and identity.")
    system = "Return JSON { \"name\": string }. If unknown, 'N/A'."
    user = _render_snippets(query, snippets) + "\n\nFocus: Company legal/brand name only."
    obj = call_llm_json(system, user)
    return obj if isinstance(obj, dict) else {"name": "N/A"}


def exa_attr_description(query: str) -> Dict[str, Any]:
    snippets = _exa_search_rich(query, num_results=6, summary_query="One-sentence product/company description.")
    system = "Return JSON { \"description\": string }. If unknown, 'N/A'."
    user = _render_snippets(query, snippets) + "\n\nFocus: One concise what-they-do sentence."
    obj = call_llm_json(system, user)
    return obj if isinstance(obj, dict) else {"description": "N/A"}


def exa_attr_market_size(query: str) -> Dict[str, Any]:
    prompt = (
        f"Estimate the market size (TAM/SAM/SOM) for {query}? "
        f"Answer in <= 20 words with currency and timeframe if known."
    )
    text = _exa_chat_text(prompt)
    return {"market_size": text or "N/A"}


def exa_attr_growth_rate(query: str) -> Dict[str, Any]:
    prompt = (
        f"What is the typical CAGR/growth rate for {query}? "
        f"Answer in <= 15 words including timeframe if available."
    )
    text = _exa_chat_text(prompt)
    return {"growth_rate": text or "N/A"}


def exa_attr_competition(query: str) -> Dict[str, Any]:
    snippets = _exa_search_rich(f"{query} competitors alternatives", num_results=6, summary_query="Competitor list.")
    system = "Return JSON { \"competition\": string }. If unknown, 'N/A'."
    user = _render_snippets(query, snippets) + "\n\nFocus: Primary competitors/substitutes in one line."
    obj = call_llm_json(system, user)
    return obj if isinstance(obj, dict) else {"competition": "N/A"}


def exa_attr_market_trends(query: str) -> Dict[str, Any]:
    snippets = _exa_search_rich(f"{query} industry trends", num_results=6, summary_query="Key trends affecting the space.")
    system = "Return JSON { \"market_trends\": string }. If unknown, 'N/A'."
    user = _render_snippets(query, snippets) + "\n\nFocus: 1-2 concise trends most relevant."
    obj = call_llm_json(system, user)
    return obj if isinstance(obj, dict) else {"market_trends": "N/A"}


def exa_attr_product_details(query: str) -> Dict[str, Any]:
    snippets = _exa_search_rich(f"{query} features product capabilities", num_results=6, summary_query="Core features/workflows.")
    system = "Return JSON { \"product_details\": string }. If unknown, 'N/A'."
    user = _render_snippets(query, snippets) + "\n\nFocus: Key features and workflows in one line."
    obj = call_llm_json(system, user)
    return obj if isinstance(obj, dict) else {"product_details": "N/A"}


def exa_attr_technology_stack(query: str) -> Dict[str, Any]:
    prompt = (
        f"What public technologies/stack does {query} use? "
        f"Answer in <= 20 words, comma-separated key components."
    )
    text = _exa_chat_text(prompt)
    return {"technology_stack": text or "N/A"}


def exa_attr_product_fit(query: str) -> Dict[str, Any]:
    snippets = _exa_search_rich(f"{query} ICP customers use cases", num_results=6, summary_query="ICP/JTBD.")
    system = "Return JSON { \"product_fit\": string }. If unknown, 'N/A'."
    user = _render_snippets(query, snippets) + "\n\nFocus: Target customer and primary job-to-be-done."
    obj = call_llm_json(system, user)
    return obj if isinstance(obj, dict) else {"product_fit": "N/A"}


def exa_attr_founders(query: str) -> Dict[str, Any]:
    # Fast path: ask Exa chat directly for founder names
    chat_names = _exa_chat_founder_names(query) or []
    if chat_names:
        return {"founders": chat_names}

    # Fallback: snippet-grounded JSON extraction with normalization
    snippets = _exa_search_rich(f"{query} founders leadership team CEO CTO", num_results=6, summary_query="Founder names.")
    system = "Return JSON { \"founders\": array|string }. If unknown, return empty array."
    user = _render_snippets(query, snippets) + "\n\nFocus: Founder names only (array or comma-separated)."
    obj = call_llm_json(system, user)
    # Normalize founders to list[str]
    names: List[str] = []
    if isinstance(obj, dict):
        val = obj.get("founders")
        if isinstance(val, str):
            names = [t.strip() for t in val.replace(";", ",").split(",") if t.strip()]
        elif isinstance(val, list):
            for v in val:
                if isinstance(v, str) and v.strip():
                    names.append(v.strip())
                elif isinstance(v, dict):
                    n = v.get("name") or v.get("founder")
                    if isinstance(n, str) and n.strip():
                        names.append(n.strip())
    return {"founders": names}


def exa_founders_details(founder_names: List[str], num_results: int = 5) -> Dict[str, Any]:
    def _exa_chat_founder_background(name: str) -> Optional[str]:
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI  # Local import to avoid global dependency at import time

            client = OpenAI(base_url="https://api.exa.ai", api_key=api_key)
            prompt = (
                f"In one sentence (<= 25 words), summarize {name}'s professional background and notable roles."
            )
            resp = client.chat.completions.create(
                model="exa",
                messages=[{"role": "user", "content": prompt}],
            )
            text = (getattr(resp.choices[0].message, "content", None) or "").strip()
            return text or None
        except Exception:
            return None

    def _fetch_one(name: str) -> Dict[str, Any]:
        # Primary search
        snippets = _exa_search_rich(
            f"{name} founder biography achievements education",
            num_results=min(max(num_results, 3), 10),
            max_chars=1600,
            summary_query=f"Summarize notable roles, companies, achievements, education for {name}.",
        )
        # Fallback search if nothing returned
        if not snippets:
            snippets = _exa_search_rich(
                f"{name} LinkedIn OR Crunchbase OR Wikipedia founder CEO CTO bio profile",
                num_results=10,
                max_chars=1600,
                summary_query=f"Key roles, employers, education for {name}.",
            )
        sources: List[Dict[str, str]] = []
        for sn in snippets:
            title = (sn.get("title") or "Source").strip()
            url = (sn.get("url") or "").strip()
            summary = (sn.get("summary") or sn.get("text") or "").strip()
            if url:
                sources.append({"title": title, "url": url, "summary": summary})
        # Create a concise background using Exa chat only
        background = _exa_chat_founder_background(name) or "N/A"
        return {"name": name, "background": background, "sources": sources}

    results: List[Dict[str, Any]] = []
    if founder_names:
        max_workers = min(8, max(1, len(founder_names)))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for item in ex.map(_fetch_one, founder_names):
                results.append(item)
    return {"founder_details": results}


# --------------- Bundle and default entrypoint -------------------

def exa_attribute_search_bundle(query: str, attributes: Optional[List[str]] = None) -> Dict[str, Any]:
    keys = attributes or [
        "name",
        "description",
        "market_size",
        "growth_rate",
        "competition",
        "market_trends",
        "product_details",
        "technology_stack",
        "product_fit",
        "founders",
        "founder_details",
    ]
    structured: Dict[str, Any] = {}
    dispatch = {
        "name": exa_attr_name,
        "description": exa_attr_description,
        "market_size": exa_attr_market_size,
        "growth_rate": exa_attr_growth_rate,
        "competition": exa_attr_competition,
        "market_trends": exa_attr_market_trends,
        "product_details": exa_attr_product_details,
        "technology_stack": exa_attr_technology_stack,
        "product_fit": exa_attr_product_fit,
        "founders": exa_attr_founders,
    }
    # Run attribute-specific searches sequentially (can parallelize later)
    for k in keys:
        fn = dispatch.get(k)
        if k == "founder_details":
            try:
                names = structured.get("founders") or []
                name_list = [n for n in names if isinstance(n, str) and n.strip()]
                details = exa_founders_details(name_list)
                structured["founder_details"] = details.get("founder_details", [])
            except Exception:
                structured["founder_details"] = []
            continue
        if not fn:
            continue
        try:
            out = fn(query)
            if isinstance(out, dict) and k in out:
                structured[k] = out[k]
        except Exception:
            structured[k] = [] if k in ("founders", "founder_details") else "N/A"

    # Compose startup_info_str
    def _compose(struct: Dict[str, Any], keys_local: List[str]) -> str:
        name_val = struct.get("name") or "Unknown Startup"
        desc_val = struct.get("description") or "N/A"
        parts_local: List[str] = [f"{name_val}: {desc_val}"]
        for kk in keys_local:
            if kk in ("name", "description"):
                continue
            val = struct.get(kk)
            if val and str(val).strip() and str(val) != "N/A":
                label = kk.replace("_", " ").title()
                parts_local.append(f"{label}: {val}")
        return "\n".join(parts_local)

    startup_info_str = _compose(structured, keys)

    # Aggregate simple citations from a generic pass
    cite_snips = _exa_search_rich(query, num_results=6, max_chars=1200, summary_query="Overview")
    citations = _citations_from(cite_snips)

    return {
        "query": query,
        "structured": structured,
        "startup_info_str": startup_info_str,
        "sources": citations,
    }


def ingest_company(query: str) -> Dict[str, Any]:
    # Default entrypoint used by framework
    return exa_attribute_search_bundle(query)


def main():
    query = "Exa AI"
    ingest_company(query)
    print(ingest_company(query))

if __name__ == "__main__":
    main()