import os
from google.adk.agents import LlmAgent
from .tools import integrated_analysis_basic, integrated_analysis_pro, quantitative_decision

root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-5"),
    name="IntegrationAgent",
    description="Integrates analyses and makes a quantitative decision.",
    instruction="Use tools to integrate all signals and generate decisions.",
    tools=[integrated_analysis_basic, integrated_analysis_pro, quantitative_decision],
)
