from typing import List, Dict, Any


def get_ingestion_system_prompt() -> str:
    return (
        "You are a meticulous VC research assistant. You will be given web-sourced snippets "
        "about a startup. Extract structured facts into JSON only.\n\n"
        "Return a single JSON object with these keys when known: \n"
        "- name (str)\n"
        "- description (str)\n"
        "- market_size (str)\n"
        "- growth_rate (str)\n"
        "- competition (str)\n"
        "- market_trends (str)\n"
        "- product_details (str)\n"
        "- technology_stack (str)\n"
        "- product_fit (str)\n"
        "- founder_backgrounds (str)\n"
        "- track_records (str)\n"
        "- leadership_skills (str)\n"
        "- vision_alignment (str)\n"
        "- citations (array of {title, url})\n\n"
        "Guidelines: Be concise, evidence-based, and attribute claims. If uncertain, write 'N/A'."
    )


def build_user_prompt(query: str, snippets: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("Research target (query):")
    lines.append(query)
    lines.append("")
    lines.append("Web snippets (title, url, content excerpt):")
    for idx, snip in enumerate(snippets, start=1):
        title = snip.get("title") or "Untitled"
        url = snip.get("url") or ""
        content = snip.get("content") or snip.get("text") or snip.get("summary") or ""
        if isinstance(content, dict):
            content = content.get("text") or content.get("value") or ""
        # Keep each snippet compact
        excerpt = (content or "").strip().replace("\n", " ")
        if len(excerpt) > 1200:
            excerpt = excerpt[:1200] + "..."
        lines.append(f"[{idx}] {title} | {url}\n{excerpt}")
        lines.append("")
    lines.append("\nExtract the JSON now.")
    return "\n".join(lines)


def build_startup_info_text(structured: Dict[str, Any]) -> str:
    """
    Compose a narrative text optimized for VC_Analyst.parse_record from structured fields.
    This becomes the `startup_info_str` fed into the VC_Analyst pipeline.
    """
    parts: List[str] = []
    name = structured.get("name") or "Unknown Startup"
    description = structured.get("description") or "N/A"
    parts.append(f"{name}: {description}")

    def add(label: str, key: str) -> None:
        val = structured.get(key)
        if val and str(val).strip() and str(val) != "N/A":
            parts.append(f"{label}: {val}")

    add("Market Size", "market_size")
    add("Growth Rate", "growth_rate")
    add("Competition", "competition")
    add("Market Trends", "market_trends")
    add("Product Details", "product_details")
    add("Technology Stack", "technology_stack")
    add("Product Fit", "product_fit")
    add("Founder Backgrounds", "founder_backgrounds")
    add("Track Records", "track_records")
    add("Leadership Skills", "leadership_skills")
    add("Vision Alignment", "vision_alignment")

    return "\n".join(parts)


