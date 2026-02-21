import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path and is the working directory for all tests
PROJECT_ROOT = Path(__file__).parent.parent

@pytest.fixture(autouse=True)
def _project_cwd(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
