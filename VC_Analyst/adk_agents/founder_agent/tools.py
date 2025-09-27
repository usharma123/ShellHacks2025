import sys
from pathlib import Path
from typing import Any, Dict

_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ..common_llm import call_llm_json


def analyze_founders(startup_info: Dict[str, Any], mode: str = "advanced") -> Dict[str, Any]:
    system = (
        "You are a venture partner evaluating founders. Return JSON with keys: "
        "competency_score (1-10), analysis."
    )
    user = (
        "Assess the founding team qualitatively based on the info. Give a numeric competency_score and a detailed analysis.\n\n"
        f"Startup info:\n{startup_info}\n\nMode: {mode}"
    )
    return call_llm_json(system, user)


def segment_founder(founder_info: Dict[str, Any]) -> Dict[str, Any]:
    system = (
        "You categorize founders into L1-L5 based on track record and capabilities. "
        "Return JSON with key: segmentation (one of L1, L2, L3, L4, L5)."
    )
    user = f"Segment the founder/team based on the info:\n{founder_info}"
    return call_llm_json(system, user)


def calculate_idea_fit(startup_info: Dict[str, Any], founder_info: Dict[str, Any]) -> Dict[str, Any]:
    system = (
        "Estimate a qualitative founder-idea fit. Return JSON with keys: "
        "idea_fit (float between 0 and 1), cosine_similarity (float between 0 and 1). "
        "If you cannot compute exact similarity, produce a reasoned estimate."
    )
    user = (
        "Given the startup and founder info, estimate compatibility and include brief rationale inside a 'rationale' field.\n\n"
        f"Startup info:\n{startup_info}\n\nFounder info:\n{founder_info}"
    )
    result = call_llm_json(system, user)
    if "cosine_similarity" not in result:
        result["cosine_similarity"] = result.get("idea_fit", 0.5)
    return result
