import sys
from pathlib import Path
from typing import Any, Dict

_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# from agents.integration_agent import IntegrationAgent  # type: ignore
from ..common_llm import call_llm_json


def integrated_analysis_basic(market_info: Dict[str, Any], product_info: Dict[str, Any], founder_info: Dict[str, Any]) -> Dict[str, Any]:
    system = (
        "You are the chief analyst combining team inputs. Return JSON with keys: "
        "overall_score (1-10), IntegratedAnalysis, recommendation, outcome."
    )
    user = (
        "Integrate the following inputs into a cohesive qualitative assessment with numeric overall_score and clear recommendation/outcome.\n\n"
        f"Market Info:\n{market_info}\n\nProduct Info:\n{product_info}\n\nFounder Info:\n{founder_info}"
    )
    return call_llm_json(system, user)


def integrated_analysis_pro(
    market_info: Dict[str, Any],
    product_info: Dict[str, Any],
    founder_info: Dict[str, Any],
    founder_idea_fit: Any,
    founder_segmentation: Any,
    rf_prediction: Any,
) -> Dict[str, Any]:
    system = (
        "You are the chief analyst. Return JSON with keys: overall_score (1-10), IntegratedAnalysis, "
        "recommendation, outcome. Consider all provided signals but don't over-index on any single one."
    )
    user = (
        "Integrate the following into a professional qualitative assessment including an overall_score and recommendation.\n\n"
        f"Market Info:\n{market_info}\n\nProduct Info:\n{product_info}\n\nFounder Info:\n{founder_info}\n\n"
        f"Founder-Idea Fit:\n{founder_idea_fit}\n\nFounder Segmentation:\n{founder_segmentation}\n\nModel Prediction:\n{rf_prediction}"
    )
    return call_llm_json(system, user)


def quantitative_decision(
    rf_prediction: Any,
    founder_idea_fit: Any,
    founder_segmentation: Any,
) -> Dict[str, Any]:
    system = (
        "Make a final qualitative decision based on the signals. Return JSON with keys: "
        "outcome (Successful/Unsuccessful), probability (0-1), reasoning."
    )
    user = (
        "Use these inputs to make a decision; be consistent and realistic about probability.\n\n"
        f"Model Prediction: {rf_prediction}\n"
        f"Founder-Idea Fit: {founder_idea_fit}\n"
        f"Founder Segmentation: {founder_segmentation}"
    )
    return call_llm_json(system, user)
