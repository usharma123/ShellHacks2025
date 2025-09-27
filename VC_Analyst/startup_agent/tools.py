import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure project root is on sys.path so we can import ssff_framework
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT_FILE.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ssff_framework import StartupFramework  # noqa: E402


def analyze_startup(description: str, mode: str = "advanced") -> Dict[str, Any]:
    """Analyze a startup description using the existing StartupFramework.

    Args:
        description: Freeform text describing the startup.
        mode: Either "advanced" (structured) or "natural" for natural language mode.

    Returns:
        A dictionary with the framework's results.
    """
    framework = StartupFramework()
    if mode == "natural":
        return framework.analyze_startup_natural(description)
    return framework.analyze_startup(description)
