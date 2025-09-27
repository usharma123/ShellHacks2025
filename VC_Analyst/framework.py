import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Ensure repository root on sys.path so we can import top-level packages
_CURRENT = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
# Also add this package directory to import local modules like `ingestion_tools`
_PKG_DIR = _CURRENT.parent
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

from adk_agents.vc_scout_agent.tools import parse_record, evaluate, side_evaluate
from adk_agents.market_agent.tools import analyze_market
from adk_agents.product_agent.tools import analyze_product
from adk_agents.founder_agent.tools import (
    analyze_founders,
    segment_founder,
    calculate_idea_fit,
)
from adk_agents.integration_agent.tools import (
    integrated_analysis_pro,
    quantitative_decision,
)

# Ingestion is imported dynamically in main() to avoid static import issues during linting

# Set the model directly here, as per .env
MODEL = "gpt-5"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StartupFramework:
    def __init__(self, model: str = MODEL):
        # Model selection is handled in tool functions via env; kept for API parity
        self.model = model
        # Allow tuning concurrency via env; default safe parallelism
        try:
            self.max_workers = int(os.environ.get("ADK_MAX_WORKERS", "4"))
            if self.max_workers < 1:
                self.max_workers = 1
        except Exception:
            self.max_workers = 4

    def _ensure_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        try:
            # Graceful degradation if upstream returns a Pydantic-like object
            return value.model_dump()  # type: ignore[attr-defined]
        except Exception:
            return {"value": value}

    def analyze_startup(self, startup_info_str: str) -> Dict[str, Any]:
        logger.info("Starting startup analysis in advanced mode")

        startup_info = parse_record(startup_info_str)
        logger.debug(f"Parsed record: {startup_info}")

        # Run independent LLM calls in parallel for performance
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            f_quick = ex.submit(side_evaluate, startup_info)
            f_full = ex.submit(evaluate, startup_info, mode="advanced")
            f_market = ex.submit(analyze_market, startup_info, mode="advanced")
            f_product = ex.submit(analyze_product, startup_info, mode="advanced")
            f_founder = ex.submit(analyze_founders, startup_info, mode="advanced")
            f_seg = ex.submit(segment_founder, startup_info.get("founder_backgrounds", {}))
            f_fit = ex.submit(
                calculate_idea_fit,
                startup_info,
                startup_info.get("founder_backgrounds", {}),
            )

            # Collect results (exceptions propagate to preserve existing behavior)
            quick_screen = f_quick.result()
            full_eval = f_full.result()
            market_analysis = f_market.result()
            product_analysis = f_product.result()
            founder_analysis = f_founder.result()
            founder_segmentation = f_seg.result()
            founder_idea_fit = f_fit.result()

        # Integrated analysis and quantitative decision
        integrated = integrated_analysis_pro(
            market_info=market_analysis,
            product_info=product_analysis,
            founder_info=founder_analysis,
            founder_idea_fit=founder_idea_fit,
            founder_segmentation=founder_segmentation,
            rf_prediction=quick_screen.get("prediction"),
        )

        quant_decision = quantitative_decision(
            rf_prediction=quick_screen.get("prediction"),
            founder_idea_fit=founder_idea_fit,
            founder_segmentation=founder_segmentation,
        )

        return {
            "Final Analysis": integrated,
            "Market Analysis": market_analysis,
            "Product Analysis": product_analysis,
            "Founder Analysis": founder_analysis,
            "Founder Segmentation": founder_segmentation,
            "Founder Idea Fit": founder_idea_fit.get("idea_fit"),
            "Categorical Prediction": quick_screen.get("prediction"),
            "Categorization": quick_screen,
            "Quantitative Decision": quant_decision,
            "Startup Info": startup_info,
            "Full Evaluation": full_eval,
        }

    def analyze_startup_natural(self, startup_info_str: str) -> Dict[str, Any]:
        logger.info("Starting startup analysis in natural language mode")

        startup_info = parse_record(startup_info_str)
        logger.debug(f"Parsed record: {startup_info}")

        # Parallelize independent calls in natural language mode
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            f_quick = ex.submit(side_evaluate, startup_info)
            f_full = ex.submit(evaluate, startup_info, mode="natural_language_advanced")
            f_market = ex.submit(analyze_market, startup_info, mode="natural_language_advanced")
            f_product = ex.submit(analyze_product, startup_info, mode="natural_language_advanced")
            # Preserve previous behavior: founders uses advanced mode here
            f_founder = ex.submit(analyze_founders, startup_info, mode="advanced")
            f_seg = ex.submit(segment_founder, startup_info.get("founder_backgrounds", {}))
            f_fit = ex.submit(
                calculate_idea_fit,
                startup_info,
                startup_info.get("founder_backgrounds", {}),
            )

            quick_screen = f_quick.result()
            full_eval = f_full.result()
            market_analysis = f_market.result()
            product_analysis = f_product.result()
            founder_analysis = f_founder.result()
            founder_segmentation = f_seg.result()
            founder_idea_fit = f_fit.result()

        integrated = integrated_analysis_pro(
            market_info=market_analysis,
            product_info=product_analysis,
            founder_info=founder_analysis,
            founder_idea_fit=founder_idea_fit,
            founder_segmentation=founder_segmentation,
            rf_prediction=quick_screen.get("prediction"),
        )

        quant_decision = quantitative_decision(
            rf_prediction=quick_screen.get("prediction"),
            founder_idea_fit=founder_idea_fit,
            founder_segmentation=founder_segmentation,
        )

        return {
            "Final Analysis": integrated,
            "Market Analysis": market_analysis,
            "Product Analysis": product_analysis,
            "Founder Analysis": founder_analysis,
            "Founder Segmentation": founder_segmentation,
            "Founder Idea Fit": founder_idea_fit.get("idea_fit"),
            "Categorical Prediction": quick_screen.get("prediction"),
            "Categorization": quick_screen,
            "Quantitative Decision": quant_decision,
            "Startup Info": startup_info,
            "Full Evaluation": full_eval,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run VC Analyst with optional ingestion. Provide a company name to research."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Company name/domain or brief description to research via ingestion",
    )
    parser.add_argument(
        "--ingest-mode",
        choices=["default", "exa", "exa-attrs"],
        default="default",
        help="Select ingestion backend: default (mixed), exa (single-pass), or exa-attrs (per-attribute)",
    )
    parser.add_argument(
        "--attrs",
        nargs="*",
        help="List of attributes to extract when using --ingest-mode exa (e.g., name description market_size)",
    )
    args = parser.parse_args()

    framework = StartupFramework(MODEL)

    output_lines = []
    output_lines.append("\n=== VC Analyst — Natural Language Analysis ===")
    output_lines.append("-" * 80)

    # If a query is provided, run ingestion to build startup_info_str; otherwise use sample text
    startup_info_str = None
    ingest_result = None
    if args.query:
        try:
            output_lines.append("\nStarting ingestion (web research)...")
            import importlib

            mod = importlib.import_module("ingestion_tools")
            if args.ingest_mode == "exa":
                exa_company_search = getattr(mod, "exa_company_search", None)
                if exa_company_search:
                    ingest_result = exa_company_search(args.query, attributes=args.attrs)
                else:
                    exa_attribute_search_bundle = getattr(mod, "exa_attribute_search_bundle")
                    ingest_result = exa_attribute_search_bundle(args.query, attributes=args.attrs)
            elif args.ingest_mode == "exa-attrs":
                exa_attribute_search_bundle = getattr(mod, "exa_attribute_search_bundle")
                ingest_result = exa_attribute_search_bundle(args.query, attributes=args.attrs)
            else:
                ingest_company = getattr(mod, "ingest_company")
                ingest_result = ingest_company(args.query)
            startup_info_str = ingest_result.get("startup_info_str") or args.query
            output_lines.append("Ingestion complete.")
        except Exception as e:
            output_lines.append(f"Ingestion failed, falling back to raw query: {str(e)}")
            startup_info_str = args.query
    else:
        # Default to ingestion by prompting the user for a company name
        try:
            company = input("Enter a company name to research: ").strip()
        except Exception:
            company = ""

        if not company:
            output_lines.append("No company provided; exiting without analysis.")
            with open("analysis_output.txt", "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(line)
                    if not line.endswith("\n"):
                        f.write("\n")
            return

        try:
            output_lines.append("\nStarting ingestion (web research)...")
            import importlib

            mod = importlib.import_module("ingestion_tools")
            if args.ingest_mode == "exa":
                exa_company_search = getattr(mod, "exa_company_search", None)
                if exa_company_search:
                    ingest_result = exa_company_search(company, attributes=args.attrs)
                else:
                    exa_attribute_search_bundle = getattr(mod, "exa_attribute_search_bundle")
                    ingest_result = exa_attribute_search_bundle(company, attributes=args.attrs)
            elif args.ingest_mode == "exa-attrs":
                exa_attribute_search_bundle = getattr(mod, "exa_attribute_search_bundle")
                ingest_result = exa_attribute_search_bundle(company, attributes=args.attrs)
            else:
                ingest_company = getattr(mod, "ingest_company")
                ingest_result = ingest_company(company)
            startup_info_str = ingest_result.get("startup_info_str") or company
            output_lines.append("Ingestion complete.")
        except Exception as e:
            output_lines.append(f"Ingestion failed: {str(e)}")
            with open("analysis_output.txt", "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(line)
                    if not line.endswith("\n"):
                        f.write("\n")
            return

    try:
        output_lines.append("\nStarting Natural Language Analysis...")
        natural_result = framework.analyze_startup_natural(startup_info_str)

        if ingest_result and isinstance(ingest_result, dict):
            # Show ingestion structured output
            output_lines.append("\nINGESTION STRUCTURED:")
            output_lines.append("-" * 20)
            try:
                output_lines.append(
                    json.dumps(ingest_result.get("structured"), indent=2, ensure_ascii=False)
                )
            except Exception:
                output_lines.append(str(ingest_result.get("structured")))

            # Show the composed narrative fed into the pipeline
            output_lines.append("\nINGESTION STARTUP_INFO_STR:")
            output_lines.append("-" * 20)
            output_lines.append(ingest_result.get("startup_info_str", ""))

            # Show sources
            sources = ingest_result.get("sources") or []
            if sources:
                output_lines.append("\nINGESTION SOURCES:")
                output_lines.append("-" * 20)
                for s in sources:
                    title = s.get("title") or "Source"
                    url = s.get("url") or ""
                    output_lines.append(f"- {title}: {url}")

        output_lines.append("\nNATURAL LANGUAGE ANALYSIS RESULTS:")
        output_lines.append("-" * 40)

        output_lines.append("\n1. MARKET ANALYSIS:")
        output_lines.append("-" * 20)
        output_lines.append(str(natural_result["Market Analysis"]))

        output_lines.append("\n2. PRODUCT ANALYSIS:")
        output_lines.append("-" * 20)
        output_lines.append(str(natural_result["Product Analysis"]))

        output_lines.append("\n3. FOUNDER ANALYSIS:")
        output_lines.append("-" * 20)
        output_lines.append(str(natural_result["Founder Analysis"]))

        output_lines.append("\n4. FINAL INTEGRATED ANALYSIS:")
        output_lines.append("-" * 20)
        output_lines.append(str(natural_result["Final Analysis"]))

        output_lines.append("\n5. QUANTITATIVE METRICS:")
        output_lines.append("-" * 20)
        output_lines.append(f"Founder Idea Fit: {natural_result['Founder Idea Fit']}")
        output_lines.append(f"Categorical Prediction: {natural_result['Categorical Prediction']}")
        output_lines.append(f"Quantitative Decision: {natural_result['Quantitative Decision']}")

    except Exception as e:
        output_lines.append(f"\nError during analysis: {str(e)}")
        import traceback
        import io
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        output_lines.append(buf.getvalue())

    with open("analysis_output.txt", "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line)
            if not line.endswith("\n"):
                f.write("\n")


if __name__ == "__main__":
    main()
