import os
from google.adk.agents import LlmAgent
from .tools import parse_record, evaluate, side_evaluate

root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-4o-mini"),
    name="VCScoutAgent",
    description="Parses startup text, evaluates, and provides side evaluation.",
    instruction="Use tools to parse and evaluate startups for VC scouting.",
    tools=[parse_record, evaluate, side_evaluate],
)
