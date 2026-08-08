import sys
from pathlib import Path

# Add application/backend directory to sys.path so imports resolve cleanly
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "application" / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import app
