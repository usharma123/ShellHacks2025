import os
import sys
import json
from pathlib import Path

# Add the VC_Analyst directory to Python path
_CURRENT = Path(__file__).resolve()
_VC_ANALYST_ROOT = _CURRENT.parents[1]
if str(_VC_ANALYST_ROOT) not in sys.path:
    sys.path.insert(0, str(_VC_ANALYST_ROOT))

from adk_agents.vc_scout_agent.tools import (
    parse_record,
    evaluate,
    side_evaluate,
)


def test_parse_record():
    txt = "EcoFresh builds smart fridges reducing waste using AI."
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "name": "EcoFresh",
        "description": "Smart fridges reducing waste using AI"
    })
    out = parse_record(txt)
    assert isinstance(out, dict)
    assert "name" in out and "description" in out


def test_evaluate():
    info = {"name": "EcoFresh", "description": "Smart fridges"}
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "market_opportunity": "Large TAM",
        "product_innovation": "Strong",
        "founding_team": "Experienced",
        "potential_risks": "Hardware margins",
        "overall_potential": 8,
        "investment_recommendation": "Invest",
        "confidence": 0.7,
        "rationale": "Compelling market and team"
    })
    out = evaluate(info, mode="advanced")
    assert set(["overall_potential", "investment_recommendation", "confidence"]).issubset(out)


def test_side_evaluate():
    info = {"name": "EcoFresh", "description": "Smart fridges"}
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "industry_growth": "Yes",
        "market_size": "Large",
        "development_pace": "Faster",
        "market_adaptability": "Very Adaptable",
        "execution_capabilities": "Excellent",
        "funding_amount": "Above Average",
        "valuation_change": "Increased",
        "investor_backing": "Recognized",
        "reviews_testimonials": "Positive",
        "product_market_fit": "Strong",
        "sentiment_analysis": "Positive",
        "innovation_mentions": "Often",
        "cutting_edge_technology": "Mentioned",
        "timing": "Just Right",
        "prediction": "Successful"
    })
    out = side_evaluate(info)
    assert "prediction" in out
