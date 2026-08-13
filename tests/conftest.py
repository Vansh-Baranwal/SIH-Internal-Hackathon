"""
tests/conftest.py

Standard workflow is `pip install -e .` before running tests. This conftest
keeps a compatibility fallback by adding src/ and repo root (for
`synthetic.terrain.*`) to sys.path when tests are executed in environments
where editable install is not configured yet.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)
