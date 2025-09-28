import importlib
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .framework import StartupFramework


class AnalyzeRequest(BaseModel):
    query: str = Field(
        ..., description="Company name/domain or description to ingest and analyze"
    )
    ingest_mode: Optional[str] = Field(
        default="default",
        description="Ingestion backend: default | exa | exa-attrs",
    )
    attributes: Optional[List[str]] = Field(
        default=None, description="Attributes to extract when using Exa ingestion"
    )


class AnalyzeResponse(BaseModel):
    ingestion: Dict[str, Any]
    analysis: Dict[str, Any]


app = FastAPI(title="VC Analyst API", version="1.0")

# CORS for local frontend development; override via env ADK_CORS_ORIGINS (comma-separated)
_origins_env = os.environ.get("ADK_CORS_ORIGINS")
_origins = [o.strip() for o in (_origins_env.split(",") if _origins_env else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "*",
])]  # keep permissive default for hackathon/dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        mod = importlib.import_module("VC_Analyst.ingestion_tools")
    except Exception as e:
        # Fallback import path when running from within package
        try:
            mod = importlib.import_module("ingestion_tools")
        except Exception:
            raise HTTPException(status_code=500, detail=f"Failed to load ingestion tools: {e}")

    # Resolve ingestion entrypoint
    ingest_mode = (req.ingest_mode or "default").lower()
    try:
        if ingest_mode == "exa":
            exa_company_search = getattr(mod, "exa_company_search", None)
            if exa_company_search:
                ingest_result = exa_company_search(req.query, attributes=req.attributes)
            else:
                exa_attribute_search_bundle = getattr(mod, "exa_attribute_search_bundle")
                ingest_result = exa_attribute_search_bundle(req.query, attributes=req.attributes)
        elif ingest_mode == "exa-attrs":
            exa_attribute_search_bundle = getattr(mod, "exa_attribute_search_bundle")
            ingest_result = exa_attribute_search_bundle(req.query, attributes=req.attributes)
        else:
            ingest_company = getattr(mod, "ingest_company")
            ingest_result = ingest_company(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    startup_info_str = ingest_result.get("startup_info_str") or req.query

    # Run analysis
    try:
        framework = StartupFramework(model=os.environ.get("ADK_MODEL", "gpt-5"))
        analysis = framework.analyze_startup_natural(startup_info_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return AnalyzeResponse(ingestion=ingest_result, analysis=analysis)


# Convenience for local dev: `uvicorn VC_Analyst.api:app --reload`

