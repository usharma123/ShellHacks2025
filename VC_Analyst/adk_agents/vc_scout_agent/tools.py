import sys
from pathlib import Path
from typing import Any, Dict

_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# from agents.vc_scout_agent import VCScoutAgent, StartupInfo  # type: ignore
from ..common_llm import call_llm_json


def parse_record(startup_text: str) -> Dict[str, Any]:
    system = (
        "Parse freeform startup text into a JSON record. Return only fields you can infer: "
        "name, description, market_size, growth_rate, competition, market_trends, product_details, technology_stack, product_fit, founder_backgrounds, track_records, leadership_skills, vision_alignment."
    )
    user = f"Parse this startup description into JSON fields:\n{startup_text}"
    return call_llm_json(system, user)


def evaluate(startup_info: Dict[str, Any], mode: str = "advanced") -> Dict[str, Any]:
    system = (
        "You are a VC scout. Return JSON with keys: market_opportunity, product_innovation, "
        "founding_team, potential_risks, overall_potential (1-10), investment_recommendation (Invest/Pass), "
        "confidence (0-1), rationale."
    )
    user = (
        "Evaluate this startup qualitatively as a scout.\n\n"
        f"Startup info:\n{startup_info}\n\nMode: {mode}"
    )
    return call_llm_json(system, user)


def side_evaluate(startup_info: Dict[str, Any]) -> Dict[str, Any]:
    system = (
        "Produce a categorical assessment for quick screening. Return JSON with keys: "
        "industry_growth (Yes/No/N/A), market_size (Small/Medium/Large/N/A), development_pace (Slower/Same/Faster/N/A), "
        "market_adaptability (Not Adaptable/Somewhat Adaptable/Very Adaptable/N/A), execution_capabilities (Poor/Average/Excellent/N/A), "
        "funding_amount (Below Average/Average/Above Average/N/A), valuation_change (Decreased/Remained Stable/Increased/N/A), "
        "investor_backing (Unknown/Recognized/Highly Regarded/N/A), reviews_testimonials (Negative/Mixed/Positive/N/A), "
        "product_market_fit (Weak/Moderate/Strong/N/A), sentiment_analysis (Negative/Neutral/Positive/N/A), "
        "innovation_mentions (Rarely/Sometimes/Often/N/A), cutting_edge_technology (No/Mentioned/Emphasized/N/A), timing (Too Early/Just Right/Too Late/N/A), "
        "prediction (Successful/Unsuccessful)."
    )
    user = f"Categorize this startup quickly based on info:\n{startup_info}"
    return call_llm_json(system, user)
