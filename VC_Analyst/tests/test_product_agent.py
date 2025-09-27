import os
import json

from refactor.adk_agents.product_agent.tools import analyze_product


def test_analyze_product_basic():
    payload = {
        "name": "EcoFresh",
        "product_details": "Smart fridge sensors",
        "technology_stack": "Vision + sensors",
        "product_fit": "Households reducing waste"
    }
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "features_analysis": "Strong sensor suite",
        "tech_stack_evaluation": "Feasible, off-the-shelf",
        "usp_assessment": "Waste reduction via AI",
        "potential_score": 8,
        "innovation_score": 7,
        "market_fit_score": 7
    })
    out = analyze_product(payload, mode="advanced")
    assert isinstance(out, dict)
    for key in [
        "features_analysis",
        "tech_stack_evaluation",
        "usp_assessment",
        "potential_score",
        "innovation_score",
        "market_fit_score",
    ]:
        assert key in out
