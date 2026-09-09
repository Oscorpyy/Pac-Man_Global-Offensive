import os
import json
from src.print_logs import print_error
from src.pydantic_models import Config
from pydantic import ValidationError
from typing import Any


def load_json_file(path: str) -> Any:
    """Load and parse a JSON file while stripping comments.

    Args:
        path: The file path to the JSON file to parse.

    Returns:
        The deserialized JSON data.

    Raises:
        ValueError: If an unterminated block comment is encountered.
    """
    with open(path, "r") as file:
        content = file.read()

    cleaned = []
    in_string = False
    escaped = False
    index = 0
    while index < len(content):
        char = content[index]
        next_char = content[index + 1] if index + 1 < len(content) else ""
        if in_string:
            cleaned.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
        elif char == '"':
            in_string = True
            cleaned.append(char)
            index += 1
        elif char == "/" and next_char == "/":
            index += 2
            while index < len(content) and content[index] not in "\r\n":
                index += 1
        elif char == "/" and next_char == "*":
            index += 2
            while (index + 1 < len(content)
                   and content[index:index + 2] != "*/"):
                index += 1
            if index + 1 >= len(content):
                raise ValueError("Unterminated JSON comment")
            index += 2
        else:
            cleaned.append(char)
            index += 1

    return json.loads("".join(cleaned))


def file_is_good(path: str) -> bool:
    """Check if a file exists and has a .json extension.

    Args:
        path: Path to the candidate file.

    Returns:
        True if the file exists and ends with .json, False otherwise.
    """
    if os.path.exists(path) is False:
        print_error("File can't be find")
        return False
    if not os.path.basename(path).endswith(".json"):
        print_error("File is not a json")
        return False
    return True


def check_file_content(path: str) -> bool | Any:
    """Validate JSON content against the Config schema.

    Args:
        path: Path to the JSON configuration file.

    Returns:
        Validated Config model instance, or False if invalid.
    """
    try:
        content = load_json_file(path)
    except (
            FileNotFoundError, PermissionError,
            ValueError, UnicodeDecodeError,
            TypeError
    ) as e:
        print_error(f"File can't be used: {e}")
        return False
    try:
        validate_content = Config.model_validate(content)
        if len(validate_content.level_array_multiple_levels) < 10:
            print_error("Not enough level to launch the game")
            return False
        highscore_path = validate_content.highscore_filename
        if (not os.path.isfile(highscore_path)
                or not os.access(highscore_path, os.R_OK)):
            print_error("Highscore file can't be found or read")
            return False
        return validate_content
    except (
            ValidationError, AttributeError,
            TypeError) as e:
        print_error(f"File content not good: {e}")
        return False


def check_config_file(argv: list[str]) -> bool:
    """Validate CLI arguments and configuration file suitability.

    Args:
        argv: Command-line arguments list.

    Returns:
        True if arguments and configuration file are valid, False otherwise.
    """
    if len(argv) != 2:
        print_error("with the number of args given")
        return False
    file_path: str = argv[1]
    if file_is_good(file_path) is False:
        return False
    if check_file_content(file_path) is False:
        return False
    return True
