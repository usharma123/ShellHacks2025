import os
import json

from refactor.adk_agents.founder_agent.tools import (
    analyze_founders,
    segment_founder,
    calculate_idea_fit,
)


def test_analyze_founders():
    payload = {"founder_backgrounds": "Ex-Google PM"}
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "competency_score": 8,
        "analysis": "Strong PM with leadership history"
    })
    out = analyze_founders(payload, mode="advanced")
    assert isinstance(out, dict)
    assert "competency_score" in out and "analysis" in out


def test_segment_founder():
    payload = {"founder_backgrounds": "Two exits"}
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({"segmentation": "L4"})
    out = segment_founder(payload)
    assert out.get("segmentation") in {"L1", "L2", "L3", "L4", "L5"}


def test_calculate_idea_fit():
    startup = {"description": "AI in healthcare"}
    founder = {"founder_backgrounds": "Healthcare data"}
    os.environ["TEST_LLM_RESPONSE"] = json.dumps({
        "idea_fit": 0.72,
        "cosine_similarity": 0.71,
        "rationale": "Aligned experience"
    })
    out = calculate_idea_fit(startup, founder)
    assert 0 <= out.get("idea_fit", 0) <= 1
    assert 0 <= out.get("cosine_similarity", 0) <= 1
