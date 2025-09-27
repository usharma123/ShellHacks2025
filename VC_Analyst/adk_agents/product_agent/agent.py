import os
from google.adk.agents import LlmAgent
from .tools import analyze_product

root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-5"),
    name="ProductAgent",
    description="Evaluates product features, tech, USP, and fit.",
    instruction="Use tools to analyze product inputs and generate structured results.",
    tools=[analyze_product],
)
