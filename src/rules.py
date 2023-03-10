import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# --- Configuration and Logger Setup ---
logger = logging.getLogger(__name__)

# Default rules file path (can be overridden)
DEFAULT_RULES_FILE = Path("rules.yaml")

# --- Helper Functions for Condition Evaluation ---

def _get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Retrieves common metadata for a given file path.
    Returns an empty dict if the file does not exist or an error occurs.
    """
    try:
        stat = file_path.stat()
        return {
            "name":