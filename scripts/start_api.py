import uvicorn
from pathlib import Path
import sys

# Add src to PYTHONPATH
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(src_path))

if __name__ == "__main__":
    uvicorn.run("lunar_hazard_mapper.api.main:app", host="127.0.0.1", port=8000, reload=True)
