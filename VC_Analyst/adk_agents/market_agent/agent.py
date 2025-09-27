import os
from google.adk.agents import LlmAgent
from .tools import analyze_market

root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-5"),
    name="MarketAgent",
    description="Analyzes market size, growth, competition, and trends.",
    instruction="Use tools to analyze market inputs and generate structured results.",
    tools=[analyze_market],
)
