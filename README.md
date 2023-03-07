# File Organizer

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Watchdog](https://img.shields.io/badge/watchdog-enabled-orange.svg)

## Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
  - [config.yaml](#configyaml)
  - [rules.yaml](#rulesyaml)
- [Usage](#usage)
  - [One-time Scan](#one-time-scan)
  - [Watch Mode](#watch-mode)
  - [Dry Run](#dry-run)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## About

The File Organizer is a powerful and flexible Python-based tool designed to automatically organize files in a specified directory. It can sort files by type, creation/modification date, or according to custom rules defined by the user. With its real-time watch mode, it can continuously monitor a directory for new files and organize them as soon as they appear, keeping your workspace tidy effortlessly.

## Features

-   **Type-Based Organization**: Automatically moves files like documents, images, videos, audio, archives, and executables into designated subdirectories.
-   **Date-Based Organization**: Organizes files into year/month/day folders based on their creation or modification date.
-   **Customizable Rules**: Define your own rules using regular expressions or specific file names/extensions to move files to any desired location.
-   **Real-time Monitoring**: Utilizes `watchdog` to monitor a source directory and organize new files instantly.
-   **Flexible Configuration**: All settings are managed via `config.yaml` and `rules.yaml` files, allowing easy customization without code changes.
-   **Dry Run Mode**: Test your organization rules without actually moving any files, ensuring everything works as expected.
-   **Logging**: Detailed logging helps track file movements and troubleshoot issues.

## Tech Stack

-   **Python**: The core programming language.
-   **`pathlib`**: For object-oriented filesystem paths.
-   **`watchdog`**: For monitoring filesystem events in real-time.
-   **`PyYAML`**: For parsing configuration and rules files (`.yaml`).
-   **`logging`**: Python's standard logging library for robust output.

## Installation

Follow these steps to get the File Organizer up and running on your local machine.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/file-organizer.git
    cd file-organizer
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment**:
    -   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    -   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The File Organizer uses two YAML files for configuration: `config.yaml` for general settings and `rules.yaml` for defining organization logic.

### `config.yaml`

This file controls the core behavior of the organizer.

```yaml
# config.yaml
source_directory: "/path/to/your/source/folder" # The directory to monitor or scan for files.
destination_directory: "/path/to/your/organized/folder" # The base directory where files will be moved.
log_level: "INFO" # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
dry_run: false # If true, no files will be moved, only actions will be logged.
watch_mode: false # If true, the organizer will continuously monitor the source_directory.
```

**Parameters:**

-   `source_directory`: **Required**. The absolute path to the directory you want to organize.
-   `destination_directory`: **Required**. The absolute path to the base directory where organized files will be moved. Subdirectories will be created here.
-   `log_level`: Sets the verbosity of the logs. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
-   `dry_run`: A boolean flag. If `true`, the script will simulate file movements and log them without actually modifying the filesystem. Useful for testing rules.
-   `watch_mode`: A boolean flag. If `true`, the script will run in an infinite loop, monitoring `source_directory` for new files and organizing them as they appear. If `false`, it performs a one-time scan.

### `rules.yaml`

This file defines how files should be organized. Rules are processed in the order they appear.

```yaml
# rules.yaml
rules:
  - name: "Documents"
    type: "file_type"
    extensions: ["pdf", "doc", "docx", "txt", "odt", "rtf", "tex", "wpd"]
    destination: "Documents" # Relative to destination_directory

  - name: "Images"
    type: "file_type"
    extensions: ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "heic"]
    destination: "Images"

  - name: "Videos"
    type: "file_type"
    extensions: ["mp4", "mov", "avi", "mkv", "wmv", "flv", "webm"]
    destination: "Videos"

  - name: "Audio"
    type: "file_type"
    extensions: ["mp3", "wav", "aac", "flac", "ogg", "wma"]
    destination: "Audio"

  - name: "Archives"
    type: "file_type"
    extensions: ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"]
    destination: "Archives"

  - name: "Executables"
    type: "file_type"
    extensions: ["exe", "msi", "dmg", "app", "deb", "rpm"]
    destination: "Executables"

  - name: "Spreadsheets"
    type: "file_type"
    extensions: ["xls", "xlsx", "csv", "ods"]
    destination: "Documents/Spreadsheets"

  - name: "Presentations"
    type: "file_type"
    extensions: ["ppt", "pptx", "odp"]
    destination: "Documents/Presentations"

  - name: "Date-Based Organization (Creation Date)"
    type: "date"
    date_attribute: "creation" # or "modification"
    destination: "By_Date/Created" # Files will go into e.g., By_Date/Created/2023/10

  - name: "Custom Project Files"
    type: "regex"
    pattern: "^project_\\d{4}_.*\\.log$" # Matches files like project_2023_report.log
    destination: "Projects/Logs"

  - name: "Temporary Files"
    type: "regex"
    pattern: ".*\\.tmp$"
    destination: "Temp"
    delete_after_move: true # Optional: delete the file after moving it
```

**Rule Types:**

-   **`file_type`**: Organizes files based on their extensions.
    -   `extensions`: A list of file extensions (without the leading dot).
    -   `destination`: The subdirectory (relative to `destination_directory`) where these files will be moved.
-   **`date`**: Organizes files into `YYYY/MM` or `YYYY/MM/DD` subdirectories based on their creation or modification date.
    -   `date_attribute`: Can be `creation` or `modification`.
    -   `destination`: The base subdirectory for date-based organization.
-   **`regex`**: Organizes files based on a regular expression pattern matching their full filename.
    -   `pattern`: A valid regular expression string.
    -   `destination`: The subdirectory where matching files will be moved.
-   **`delete_after_move` (Optional)**: A boolean flag that can be added to any rule. If `true`, the file will be deleted from the `source_directory` after it has been successfully moved to its `destination`. Use with caution!

**Important Notes:**

-   Rules are processed from top to bottom. The first rule that matches a file will be applied.
-   Ensure `destination` paths are relative to your `destination_directory`. The script will create any necessary subdirectories.
-   If no rule matches a file, it will remain in the `source_directory`.

## Usage

After installation and configuration, you can run the File Organizer in two main modes: one-time scan or watch mode.

### One-time Scan

To perform a single scan of the `source_directory` and organize existing files:

```bash
python src/main.py --scan
```

This will read your `config.yaml` and `rules.yaml`, process all files in the `source_directory` once, and then exit.

### Watch Mode

To continuously monitor the `source_directory` for new files and organize them in real-time:

```bash
python src/main.py --watch
```

This will keep the script running in the background, listening for filesystem events. Any new files created or moved into the `source_directory` will be organized according to your rules. Press `Ctrl+C` to stop the watcher.

### Dry Run

To test your configuration and rules without actually moving any files, use the `--dry-run` flag:

```bash
python src/main.py --scan --dry-run
# Or for watch mode dry run:
python src/main.py --watch --dry-run
```

The script will log all the actions it *would* take, but no files will be moved or created. This is highly recommended when setting up new rules or changing directories.

## Project Structure

```
file-organizer/
├── README.md
├── .gitignore
├── requirements.txt
├── LICENSE
├── pyproject.toml
├── config.yaml             # Main configuration for source/destination, logging, etc.
├── rules.yaml              # Defines the file organization rules (types, dates, regex).
├── src/
│   ├── __init__.py
│   ├── main.py             # Entry point, handles CLI arguments and orchestrates components.
│   ├── organizer.py        # Core logic for moving and organizing files based on rules.
│   ├── rules.py            # Handles loading and applying rules from rules.yaml.
│   └── watcher.py          # Integrates watchdog for real-time directory monitoring.
└── tests/
    ├── __init__.py
    ├── test_organizer.py   # Unit tests for the organizer logic.
    └── test_rules.py       # Unit tests for rule parsing and application.
```

## Contributing

Contributions are welcome! If you have suggestions for improvements, bug reports, or want to add new features, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Write tests for your changes (if applicable).
5.  Ensure all tests pass (`pytest`).
6.  Commit your changes (`git commit -m 'Add new feature'`).
7.  Push to the branch (`git push origin feature/your-feature-name`).
8.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.