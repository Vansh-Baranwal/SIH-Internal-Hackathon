import json
from typing import Dict, Any

def generate_uncertainty_report(metrics: Dict[str, Any], filepath: str) -> None:
    """
    Exports the uncertainty analysis metrics to a JSON report.
    """
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
