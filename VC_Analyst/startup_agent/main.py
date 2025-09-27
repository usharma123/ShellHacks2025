import os
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Serve ADK UI and A2A endpoints. We point agents_dir to this package directory.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

app: FastAPI = get_fast_api_app(
    agents_dir=_THIS_DIR,
    allow_origins=["*"],
    web=True,
)
