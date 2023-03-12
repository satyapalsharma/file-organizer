import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import shutil

# Assuming src.rules exists and defines Rule and RuleSet
# and that RuleAction and RuleCondition are internal logic or enums/constants
from src.rules import Rule, RuleSet

# --- Fixtures for common test data ---

@pytest.fixture
def mock_file_path():
    """
    Fixture to create a mock Path object for testing rule matching and actions.
    It simulates a file named 'document.pdf', 100KB in size, modified 2 days ago.
    """
    mock_path = MagicMock(spec=Path)
    mock_path.name = "document.pdf"