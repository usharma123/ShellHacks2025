import os
from google.adk.agents import LlmAgent

from .tools import analyze_startup


_AGENT_INSTRUCTION = (
    "You are a startup evaluation agent. Use the provided tool to analyze "
    "a startup description and produce a structured assessment."
)


root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-4o-mini"),
    name="StartupEvaluator",
    description="Evaluates startups using market, product, and founder signals.",
    instruction=_AGENT_INSTRUCTION,
    tools=[analyze_startup],
)
