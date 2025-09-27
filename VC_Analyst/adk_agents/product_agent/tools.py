import sys
from pathlib import Path
from typing import Any, Dict

_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# from agents.product_agent import ProductAgent  # type: ignore
from ..common_llm import call_llm_json


def analyze_product(startup_info: Dict[str, Any], mode: str = "advanced") -> Dict[str, Any]:
    system = (
        "You are a senior product analyst. Return JSON with keys: "
        "features_analysis, tech_stack_evaluation, usp_assessment, "
        "potential_score (1-10), innovation_score (1-10), market_fit_score (1-10)."
    )
    user = (
        "Analyze the startup's product qualitatively based on this info. Include concrete justifications.\n\n"
        f"Startup info:\n{startup_info}\n\nMode: {mode}"
    )
    return call_llm_json(system, user)
