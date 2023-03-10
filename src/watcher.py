import logging
import time
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Assuming these modules exist and provide necessary functions
from src.organizer import FileOrganizer
from src.rules import load_rules
# Assuming a config module exists to load global configuration from config.yaml
# For the purpose of this file, we'll assume `config.py` provides a `load_config` function.
# In a real project, `src/main.py` might handle loading config and passing it down.
from config import load_config # This import assumes a `config.py` file exists at the project root or is importable.

# --- Logger Setup ---
# Configure a logger specifically for the watcher module.
# This allows for granular control over watcher-related logs.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Default log level for the watcher
# Add a stream handler if not already configured by a root logger
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# --- Custom Event Handler ---
class FileOrganizerEventHandler(FileSystemEventHandler):
    """
    Custom event handler for watchdog that triggers the FileOrganizer.
    Implements debouncing to prevent excessive organization calls during rapid file changes.
    When multiple file system events occur in quick succession (e.g., copying a large file),
    this handler ensures that the organization process is only triggered once after a
    period of inactivity, rather than for every single event.
    """
    def __init__(self, organizer: FileOrganizer, debounce_interval_seconds: float = 1.0):
        """
        Initializes the event handler.

        Args:
            organizer (FileOrganizer): An instance of the FileOrganizer to call.
            debounce_interval_seconds (float): The time in seconds to wait after the last
                                               event before triggering the organization.
        """
        super().__init__()
        self.organizer = organizer
        self.debounce_interval = debounce_interval_seconds
        self._timer: Optional[threading.Timer] = None
        logger.info(f"Initialized FileOrganizerEventHandler with debounce interval: {self.debounce_interval}s")

    def _schedule_organize(self):
        """
        Schedules the file organization process after a debounce interval.
        If an organization is already scheduled, it cancels the previous one