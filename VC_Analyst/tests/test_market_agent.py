import os
import json

from refactor.adk_agents.market_agent.tools import analyze_market


def test_analyze_market_basic():
    payload = {
        "name": "EcoFresh",
        "market_size": "$10B TAM",
        "growth_rate": "15% CAGR",
        "competition": "Legacy fridge OEMs, startups",
        "market_trends": "AI in home appliances"
    }
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "market_size": "$10B TAM",
        "growth_rate": "15% CAGR",
        "competition": "Legacy fridge OEMs, startups",
        "market_trends": "AI in home appliances",
        "viability_score": 8
    })
    out = analyze_market(payload, mode="advanced")
    assert isinstance(out, dict)
    for key in ["market_size", "growth_rate", "competition", "market_trends", "viability_score"]:
        assert key in out
