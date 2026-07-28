import os
import json
from src.print_logs import print_error
from src.pydantic_models import Config
from pydantic import ValidationError
from typing import Any


def file_is_good(path: str) -> bool:
    if os.path.exists(path) is False:
        print_error("File can't be find")
        return False
    if not os.path.basename(path).endswith(".json"):
        print_error("File is not a json")
        return False
    return True


def check_file_content(path: str) -> bool | Any:
    try:
        with open(path, "r") as f:
            content = json.load(f)
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
        return validate_content
    except (
            ValidationError, AttributeError,
            TypeError) as e:
        print_error(f"File content not good: {e}")
        return False


def check_config_file(argv: list) -> bool:
    file_path: str = argv[1]
    if file_is_good(file_path) is False:
        return False
    if check_file_content(file_path) is False:
        return False
    return True
