import os
import sys
import json
from pathlib import Path

# Add the VC_Analyst directory to Python path
_CURRENT = Path(__file__).resolve()
_VC_ANALYST_ROOT = _CURRENT.parents[1]
if str(_VC_ANALYST_ROOT) not in sys.path:
    sys.path.insert(0, str(_VC_ANALYST_ROOT))

from adk_agents.integration_agent.tools import (
    integrated_analysis_basic,
    integrated_analysis_pro,
    quantitative_decision,
)


def test_integrated_analysis_basic():
    market = {"viability_score": 7}
    product = {"potential_score": 7}
    founders = {"competency_score": 8}
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "overall_score": 7.5,
        "IntegratedAnalysis": "Balanced strengths",
        "recommendation": "Invest",
        "outcome": "High potential"
    })
    out = integrated_analysis_basic(market, product, founders)
    assert set(["overall_score", "IntegratedAnalysis", "recommendation", "outcome"]).issubset(out)


def test_integrated_analysis_pro():
    market = {"viability_score": 8}
    product = {"potential_score": 8}
    founders = {"competency_score": 8}
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "overall_score": 8.2,
        "IntegratedAnalysis": "Strong alignment",
        "recommendation": "Invest",
        "outcome": "Promising"
    })
    out = integrated_analysis_pro(market, product, founders, 0.7, "L4", "Successful")
    assert out.get("recommendation") in {"Invest", "Hold", "Pass", "Proceed", "Reassess"}


def test_quantitative_decision():
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "outcome": "Successful",
        "probability": 0.65,
        "reasoning": "Strong signals"
    })
    out = quantitative_decision("Successful", 0.7, "L4")
    assert 0 <= out.get("probability", 0) <= 1
    assert out.get("outcome") in {"Successful", "Unsuccessful"}
