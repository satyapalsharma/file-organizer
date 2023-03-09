import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Assuming Rule class is defined in src/rules.py
# We'll need to import it, but for a standalone file, we might mock or define a minimal version
# For production code, this would be a direct import:
from src.rules import Rule  # type: ignore # Mypy ignore for now, as rules.py is not in this file

# --- Logger Setup ---
logger = logging.getLogger(__name__)
# Basic configuration if this module is run directly, otherwise main.py should configure it
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Organizer:
    """
    The core class responsible for organizing files within a specified directory
    based on a set of predefined rules.
    """

    def __init__(self, source_dir: Path, rules: List[Rule], dry_run: bool = False):
        """
        Initializes the File Organizer.

        Args:
            source_dir (Path): The root directory to scan and organize files from.
            rules (List[Rule]): A list of Rule objects to apply for organizing files.
                                Rules are applied in the order they appear in the list.
            dry_run (bool): If True, no files will actually be moved or created.
                            Actions will only be logged. Defaults to False.
        """
        if not source_dir.is_dir():
            raise ValueError(f"Source directory does not exist or is not a directory: {source_dir}")

        self.source_dir = source_dir.resolve()  # Resolve to absolute path
        self.rules = rules
        self.dry_run = dry_run
        logger.info(f"Organizer initialized for '{self.source_dir}'. Dry run: {self.dry_run}")

    def _get_destination_path(self, file_path: Path) -> Optional[Path]:
        """
        Determines the target destination path for a given file based on the defined rules.

        Args:
            file_path (Path): The path to the file to be organized.

        Returns:
            Optional[Path]: The calculated destination path, or None if no rule matches.
        """
        if not file_path.is_file():
            logger.debug(f"Skipping non-file path: {file_path}")
            return None

        for rule in self.rules:
            if rule.matches(file_path):
                try:
                    # Extract file metadata for template placeholders
                    file_stat = file_path.stat()
                    creation_time = datetime.fromtimestamp(file_stat.st_ctime)
                    modification_time = datetime.fromtimestamp(file_stat.st_mtime)

                    # Prepare placeholders
                    placeholders = {
                        "name": file_path.stem,
                        "extension": file_path.suffix.lstrip('.'),
                        "full_extension": file_path.suffix,
                        "year": creation_time.strftime("%Y"),
                        "month": creation_time.strftime("%m"),
                        "day": creation_time.strftime("%d"),
                        "date": creation_time.strftime("%Y-%m-%d"),
                        "mod_year": modification_time.strftime("%Y"),
                        "mod_month": modification_time.strftime("%m"),
                        "mod_day": modification_time.strftime("%d"),
                        "mod_date": modification_time.strftime("%Y-%m-%d"),
                        # Add more as needed, e.g., file type from a mapping
                    }

                    # Add custom rule-specific placeholders if the rule provides them
                    if hasattr(rule, 'get_placeholders'):
                        placeholders.update(rule.get_placeholders(file_path))

                    # Format the destination path
                    relative_dest_str = rule.destination_template.format(**placeholders)
                    destination_dir = self.source_dir / relative_dest_str
                    destination_dir.mkdir(parents=True, exist_ok=True)

                    destination_path = destination_dir / file_path.name
                    logger.debug(f"Rule '{rule.name}' matched '{file_path}'. Destination: '{destination_path}'")
                    return destination_path
                except KeyError as e:
                    logger.error(f"Error formatting destination path for rule '{rule.name}' and file '{file_path}': "
                                 f"Missing placeholder '{e}'. Template: '{rule.destination_template}'")
                    return None
                except Exception as e:
                    logger.error(f"Unexpected error determining destination for rule '{rule.name}' and file '{file_path}': {e}")
                    return None
        logger.debug(f"No rule matched for file: {file_path}")
        return None

    def _move_file(self, source_path: Path, destination_path: Path) -> bool:
        """
        Moves a file from the source path to the destination path.
        Handles potential conflicts by renaming the file if it already exists at the destination.

        Args:
            source_path (Path): The current path of the file.
            destination_path (Path): The desired target path for the file.

        Returns:
            bool: True if the file was successfully moved (or would have been in dry run), False otherwise.
        """
        if source_path == destination_path:
            logger.info(f"File '{source_path}' is already in its correct location. Skipping.")
            return True

        final_destination = destination_path
        counter = 0
        while final_destination.exists():
            counter += 1
            # Append a counter to the filename to avoid overwriting
            final_destination = destination_path.parent / f"{destination_path.stem} ({counter}){destination_path.suffix}"
            if counter > 100:  # Prevent infinite loop for extreme cases
                logger.error(f"Too many existing files for '{destination_path}'. Skipping '{source_path}'.")
                return False

        if self.dry_run:
            logger.info(f"[DRY RUN] Would move '{source_path}' to '{final_destination}'")
            return True
        else:
            try:
                shutil.move(str(source_path), str(final_destination))
                logger.info(f"Moved '{source_path}' to '{final_destination}'")
                return True
            except shutil.Error as e:
                logger.error(f"Failed to move '{source_path}' to '{final_destination}': {e}")
                return False
            except OSError as e:
                logger.error(f"OS error moving '{source_path}' to '{final_destination}': {e}")
                return False
            except Exception as e:
                logger.error(f"An unexpected error occurred while moving '{source_path}': {e}")
                return False

    def organize_file(self, file_path: Path) -> bool:
        """
        Organizes a single file based on the configured rules.

        Args:
            file_path (Path): The path to the file to organize.

        Returns:
            bool: True if the file was successfully organized (or would be in dry run), False otherwise.
        """
        if not file_path.is_file():
            logger.warning(f"Path '{file_path}' is not a file or does not exist. Skipping.")
            return False

        if file_path.parent != self.source_dir:
            logger.warning(f"File '{file_path}' is not directly in the source directory '{self.source_dir}'. "
                           "Only files directly within the source directory are organized by this method.")
            # Depending on requirements, one might allow organizing files from subdirectories too.
            # For now, we'll stick to the immediate source_dir.
            return False

        destination_path = self._get_destination_path(file_path)
        if destination_path:
            return self._move_file(file_path, destination_path)
        else:
            logger.info(f"No rule matched for file '{file_path}'. It will remain in place.")
            return False

    def organize_directory(self) -> int:
        """
        Scans the source directory and organizes all files within it
        (excluding subdirectories themselves, but including files directly inside them if configured).

        Returns:
            int: The number of files successfully organized (or would be in dry run).
        """
        organized_count = 0
        logger.info(f"Starting organization of directory: '{self.source_dir}'")

        # Iterate through files directly in the source directory
        # Use rglob if you want to organize files in subdirectories too.
        # For simplicity, let's start with files directly in source_dir.
        # If rules are designed to handle subdirectories, then rglob is better.
        # For now, let's stick to immediate children of source_dir.
        for item in self.source_dir.iterdir():
            if item.is_file():
                if self.organize_file(item):
                    organized_count += 1
            elif item.is_dir():
                logger.debug(f"Skipping directory: {item}")
            else:
                logger.debug(f"Skipping non-file/non-directory item: {item}")

        logger.info(f"Finished organizing directory. {organized_count} files organized.")
        return organized_count


# --- Example Usage (for testing/demonstration) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Minimal Rule class for demonstration purposes
    class MockRule(Rule):
        def __init__(self, name: str, pattern: str, destination_template: str):
            self.name = name
            self.pattern = pattern
            self.destination_template = destination_template

        def matches(self, file_path: Path) -> bool:
            return file_path.suffix.lower() == self.pattern.lower()

    # Create a dummy source directory and some files
    test_source_dir = Path("./test_organizer_source")
    test_source_dir.mkdir(exist_ok=True)

    # Clean up previous test files
    for f in test_source_dir.iterdir():
        if f.is_file():
            f.unlink()
        elif f.is_dir():
            shutil.rmtree(f)

    (test_source_dir / "document.pdf").touch()
    (test_source_dir / "image.jpg").touch()
    (test_source_dir / "report.docx").touch()
    (test_source_dir / "archive.zip").touch()
    (test_source_dir / "another_image.JPG").touch()
    (test_source_dir / "config.txt").touch()
    (test_source_dir / "old_doc.pdf").touch() # To test conflict resolution

    # Create a subdirectory that should be ignored by default organize_directory
    (test_source_dir / "sub_dir").mkdir(exist_ok=True)
    (test_source_dir / "sub_dir" / "nested_file.txt").touch()

    # Define some mock rules
    mock_rules = [
        MockRule(name="PDFs", pattern=".pdf", destination_template="Documents/PDFs/{year}"),
        MockRule(name="Images", pattern=".jpg", destination_template="Pictures/{year}/{month}"),
        MockRule(name="Documents", pattern=".docx", destination_template="Documents/Word"),
        MockRule(name="Archives", pattern=".zip", destination_template="Archives"),
        # A catch-all rule could be added last
        MockRule(name="Others", pattern=".txt", destination_template="Others"),
    ]

    print("\n--- Running Dry Run ---")
    organizer_dry_run = Organizer(test_source_dir, mock_rules, dry_run=True)
    organizer_dry_run.organize_directory()

    print("\n--- Running Actual Organization ---")
    organizer_actual = Organizer(test_source_dir, mock_rules, dry_run=False)
    organized_count = organizer_actual.organize_directory()
    print(f"\nTotal files organized: {organized_count}")

    print("\n--- Files remaining in source directory ---")
    for item in test_source_dir.iterdir():
        print(f"- {item.name} ({'Dir' if item.is_dir() else 'File'})")

    # Clean up after demonstration
    # shutil.rmtree(test_source_dir)
    # print(f"\nCleaned up '{test_source_dir}'")