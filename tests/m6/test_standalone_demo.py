import os
import subprocess
from pathlib import Path
import json

def test_standalone_demo_execution():
    """
    Validates that the M6 standalone demo runs successfully without external dependencies
    and produces all expected artifact files.
    """
    # 1. Ensure output directory is clean
    output_dir = Path("results/m6_demo")
    
    # 2. Run the script as a subprocess to verify independent execution
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    
    import sys
    result = subprocess.run(
        [sys.executable, "scripts/run_m6_demo.py"],
        env=env,
        capture_output=True,
        text=True
    )
    
    # 3. Assert script exited successfully
    assert result.returncode == 0, f"Demo script failed with stderr: {result.stderr}"
    
    # 4. Verify all 5 expected output artifacts exist
    expected_files = [
        "selected_site.json",
        "trajectory.json",
        "replan_event.json",
        "replanned_trajectory.json",
        "uncertainty_report.json"
    ]
    
    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"Expected artifact {filename} was not generated."
        
        # Verify it's valid JSON
        with open(file_path, "r") as f:
            data = json.load(f)
            assert data is not None
