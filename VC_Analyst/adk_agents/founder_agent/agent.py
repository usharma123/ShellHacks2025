import os
from google.adk.agents import LlmAgent
from .tools import analyze_founders, segment_founder, calculate_idea_fit

root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-5"),
    name="FounderAgent",
    description="Analyzes founders; segmentation and idea-fit scoring.",
    instruction="Use tools to assess founders and compute fit metrics.",
    tools=[analyze_founders, segment_founder, calculate_idea_fit],
)
