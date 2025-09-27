import logging
from typing import Dict, Any

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

# Set the model directly here, as per .env
MODEL = "gpt-5"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StartupFramework:
    def __init__(self, model: str = MODEL):
        # Model selection is handled in tool functions via env; kept for API parity
        self.model = model

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

        # Quick categorical screen and full evaluation
        quick_screen = side_evaluate(startup_info)
        full_eval = evaluate(startup_info, mode="advanced")

        # Core analyses
        market_analysis = analyze_market(startup_info, mode="advanced")
        product_analysis = analyze_product(startup_info, mode="advanced")
        founder_analysis = analyze_founders(startup_info, mode="advanced")

        # Founder-specific metrics
        founder_segmentation = segment_founder(startup_info.get("founder_backgrounds", {}))
        founder_idea_fit = calculate_idea_fit(startup_info, startup_info.get("founder_backgrounds", {}))

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

        quick_screen = side_evaluate(startup_info)
        full_eval = evaluate(startup_info, mode="natural_language_advanced")

        market_analysis = analyze_market(startup_info, mode="natural_language_advanced")
        product_analysis = analyze_product(startup_info, mode="natural_language_advanced")
        founder_analysis = analyze_founders(startup_info, mode="advanced")

        founder_segmentation = segment_founder(startup_info.get("founder_backgrounds", {}))
        founder_idea_fit = calculate_idea_fit(startup_info, startup_info.get("founder_backgrounds", {}))

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
    framework = StartupFramework(MODEL)

    startup_info_str = (
        "Turismocity is a travel search engine for Latin America that provides price "
        "comparison tools and travel deals. Eugenio Fage, the CTO and co-founder, "
        "has a background in software engineering and extensive experience in "
        "developing travel technology solutions."
    )

    output_lines = []
    output_lines.append("\n=== Testing Natural Language Analysis ===")
    output_lines.append("-" * 80)

    try:
        output_lines.append("\nStarting Natural Language Analysis...")
        natural_result = framework.analyze_startup_natural(startup_info_str)

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
