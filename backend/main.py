import sys
import os

# Ensure backend directory and repo root are in sys.path for robust module resolution
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
repo_root = os.path.dirname(backend_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Expose the FastAPI application instance
from backend.app.main import app

__all__ = ["app"]
