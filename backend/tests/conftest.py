"""Test configuration for backend/tests."""

import os
import sys
from pathlib import Path

# Disable SQLAlchemy Cython C-extensions on Windows environments
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
