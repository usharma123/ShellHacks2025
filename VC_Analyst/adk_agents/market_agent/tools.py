import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to import path
_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agents.market_agent import MarketAgent  # type: ignore
from ..common_llm import call_llm_json


def analyze_market(startup_info: Dict[str, Any], mode: str = "advanced") -> Dict[str, Any]:
    system = (
        "You are an experienced market analyst. Return JSON with keys: "
        "market_size, growth_rate, competition, market_trends, viability_score (1-10)."
    )
    user = (
        "Analyze the startup's market qualitatively based on this info. Be concise but specific.\n\n"
        f"Startup info:\n{startup_info}\n\nMode: {mode}"
    )
    return call_llm_json(system, user)
