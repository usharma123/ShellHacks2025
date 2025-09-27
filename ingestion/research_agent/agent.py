import os
import sys
from pathlib import Path
from google.adk.agents import LlmAgent
from dotenv import load_dotenv

# Ensure repository root is on sys.path so we can import the top-level
# package `ingestion` even when ADK loads this module as `research_agent.*`.
_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Load this package's .env (e.g., ADK_MODEL, OPENAI_API_KEY)
_ENV_PATH = Path(__file__).resolve().parent / ".env"
try:
    load_dotenv(dotenv_path=str(_ENV_PATH))
except Exception:
    pass

# Reuse the implemented tool from the top-level ingestion package
from ingestion.agent import ingest_for_vc_analyst


root_agent: LlmAgent = LlmAgent(
    model=os.environ.get("ADK_MODEL", "gpt-5"),
    name="IngestionAgent",
    description="Deep-researches startups using Exa and prepares VC_Analyst-ready inputs.",
    instruction=(
        "Use the ingest_for_vc_analyst tool to gather web evidence and produce a "
        "concise, structured startup summary."
    ),
    tools=[ingest_for_vc_analyst],
)


