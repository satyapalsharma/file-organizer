import argparse
import logging
import sys
import time
from pathlib import Path

import yaml

# Project-specific imports
from src.organizer import Organizer
from src.rules import RuleSet
from src.watcher import Watcher

# --- Constants and Defaults ---
DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_RULES_PATH = Path("rules.yaml")
DEFAULT_LOG_LEVEL = "INFO"

# --- Logger Setup ---
# Configure a global logger for the application
logger = logging.getLogger(__name__)


def setup_logging(log_level: str) -> None:
    """
    Configures the logging for the application.

    Args:
        log_level: The desired logging level (e.g., "INFO", "DEBUG", "WARNING").
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger.info(f"Logging level set to {log_level.upper()}")


def load_yaml_config(file_path: Path) -> dict:
    """
    Loads configuration from a YAML file.

    Args:
        file_path: The path to the YAML configuration file.

    Returns:
        A dictionary containing the loaded configuration.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If there's an error parsing the YAML file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file '{file_path}': {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading '{file_path}': {e}")


def main() -> None:
    """
    Main function to parse arguments, load configurations, and run the file organizer.
    """
    parser = argparse.ArgumentParser(
        description="Automatically organizes files in a directory by type, date, or custom rules."
    )
    parser.add_argument(
        "directory",
        type=Path,
        nargs='?',  # Make directory optional, will be loaded from config if not provided
        help="The directory to organize or watch. Defaults to 'default_directory' in config.yaml."
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to the main configuration file (default: {DEFAULT_CONFIG_PATH})."
    )
    parser.add_argument(
        "-r", "--rules",
        type=Path,
        default=DEFAULT_RULES_PATH,
        help=f"Path to the rules definition file (default: {DEFAULT_RULES_PATH})."
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Run in watch mode, continuously monitoring the directory for new files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate file organization without actually moving or creating directories."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=DEFAULT_LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Set the logging level (default: {DEFAULT_LOG_LEVEL})."
    )

    args = parser.parse_args()

    # --- Load Configurations ---
    app_config = {}
    try:
        app_config = load_yaml_config(args.config)
        logger.debug(f"Loaded application config from {args.config}")
    except FileNotFoundError:
        logger.warning(f"Application config file not found at {args.config}. Using default settings.")
    except yaml.YAMLError as e:
        logger.error(f"Failed to load application config from {args.config}: {e}")
        sys.exit(1)

    rules_data = {}
    try:
        rules_data = load_yaml_config(args.rules)
        logger.debug(f"Loaded rules config from {args.rules}")
    except FileNotFoundError as e:
        logger.error(f"Rules config file not found at {args.rules}: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Failed to load rules config from {args.rules}: {e}")
        sys.exit(1)

    # --- Setup Logging ---
    # Use log level from CLI args, or config, or default
    log_level = args.log_level or app_config.get("log_level", DEFAULT_LOG_LEVEL)
    setup_logging(log_level)

    # --- Determine Target Directory ---
    target_directory = args.directory
    if not target_directory:
        default_dir_str = app_config.get("default_directory")
        if default_dir_str:
            target_directory = Path(default_dir_str).expanduser().resolve()
            logger.info(f"Using default directory from config: {target_directory}")
        else:
            logger.error("No directory specified via command line or 'default_directory' in config.yaml.")
            parser.print_help()
            sys.exit(1)

    if not target_directory.is_dir():
        logger.error(f"The specified directory does not exist or is not a directory: {target_directory}")
        sys.exit(1)

    # --- Initialize RuleSet and Organizer ---
    try:
        rule_set = RuleSet(rules_data.get("rules", []))
        logger.debug("RuleSet initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize RuleSet: {e}")
        sys.exit(1)

    organizer = Organizer(
        source_directory=target_directory,
        rule_set=rule_set,
        dry_run=args.dry_run
    )
    logger.info(f"Organizer initialized for directory: {target_directory}")
    if args.dry_run:
        logger.info("Running in DRY-RUN mode. No files will be moved or created.")

    # --- Run Modes ---
    if args.watch:
        logger.info(f"Starting watch mode for directory: {target_directory}")
        watcher = Watcher(target_directory, organizer)
        watcher.start()
        try:
            while True:
                time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            logger.info("Watch mode stopped by user (Ctrl+C).")
        finally:
            watcher.stop()
            logger.info("File watcher shut down.")
    else:
        logger.info(f"Starting one-time organization for directory: {target_directory}")
        try:
            organizer.organize_directory()
            logger.info("One-time organization complete.")
        except Exception as e:
            logger.error(f"An error occurred during one-time organization: {e}", exc_info=True)
            sys.exit(1)

    logger.info("File Organizer finished.")


if __name__ == "__main__":
    main()