"""Pytest configuration and test fixtures."""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Use test sqlite database
os.environ["CODEMIND_ENV"] = "testing"
os.environ["LLM_PROVIDER"] = "local"
os.environ["EMBEDDING_PROVIDER"] = "local"
